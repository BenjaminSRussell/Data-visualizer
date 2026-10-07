"""
REST API endpoints with comprehensive error handling and input validation.
All endpoints are protected against common vulnerabilities.
"""

import csv
import io
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.datasets import (
    MAX_LIMIT,
    Dataset,
    execute_dataset_query,
    get_all_datasets,
    get_dataset_count,
    list_datasets,
    refresh_datasets,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class DatasetInfo(BaseModel):
    """Dataset information response model."""

    name: str
    description: str
    table_name: str
    is_custom: bool = False

    class Config:
        from_attributes = True


class DatasetResponse(BaseModel):
    """Dataset query response with pagination info."""

    dataset: str
    total_count: int
    limit: int
    offset: int
    data: List[Dict[str, Any]]
    has_more: bool = False


class StatsResponse(BaseModel):
    """Database statistics response."""

    total_urls: int = 0
    total_classifications: int = 0
    total_patterns: int = 0
    total_sessions: int = 0
    domains_count: int = 0
    available_tables: List[str] = []


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: str
    detail: Optional[str] = None
    status_code: int


@router.get("/", tags=["root"])
async def root():
    """API root endpoint with version and description."""
    return {
        "name": "Data Visualizer API",
        "version": "2.0.0",
        "description": "PostgreSQL-backed data visualization and exploration platform",
        "endpoints": {
            "health": "/api/health",
            "datasets": "/api/datasets",
            "stats": "/api/stats",
            "docs": "/api/docs",
        },
    }


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint with database connectivity test.
    Returns detailed health status and database state.
    """
    try:
        result = db.execute(text("SELECT 1 as health_check"))
        result.fetchone()

        table_count = db.execute(
            text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        ).fetchone()[0]

        from app import cache as dv_cache

        details = {
            "tables_available": table_count,
            "connection_pool": "active",
            "cache": dv_cache.stats(),
            "redis_configured": bool(
                __import__("app.config", fromlist=["settings"]).settings.REDIS_URL
            ),
        }
        return HealthResponse(
            status="healthy",
            database="connected",
            details=details,
        )

    except SQLAlchemyError as db_error:
        logger.error(f"Database health check failed: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection failed"
        )
    except Exception as health_error:
        logger.error(f"Health check error: {health_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Health check failed"
        )


@router.get("/datasets", response_model=List[DatasetInfo], tags=["datasets"])
async def get_datasets_list(
    db: Session = Depends(get_db),
    refresh: bool = Query(False, description="Force refresh dataset cache"),
):
    """
    List all available datasets (both predefined and dynamically discovered).
    Use refresh=true to force refresh the dataset cache.
    """
    try:
        if refresh:
            refresh_datasets(db)

        all_datasets = get_all_datasets(db)

        return [
            DatasetInfo(
                name=dataset.name,
                description=dataset.description,
                table_name=dataset.table_name,
                is_custom=dataset.is_custom,
            )
            for dataset in all_datasets.values()
        ]

    except SQLAlchemyError as db_error:
        logger.error(f"Database error listing datasets: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve datasets from database",
        )
    except Exception as list_error:
        logger.error(f"Error listing datasets: {list_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list datasets"
        )


CSV_EXPORT_MAX = 50_000


@router.get("/datasets/{dataset_name}.csv", tags=["datasets"])
async def export_dataset_csv(
    dataset_name: str = Path(..., description="Name of the dataset to export as CSV"),
    limit: int = Query(CSV_EXPORT_MAX, ge=1, le=CSV_EXPORT_MAX, description="Max rows to export"),
    offset: int = Query(0, ge=0, description="Number of rows to skip"),
    db: Session = Depends(get_db),
):
    """Stream a dataset as CSV using the same query path as JSON query_dataset."""
    try:
        # Validate name exists (raises ValueError → 404)
        get_dataset_count(db, dataset_name)
        data_rows = execute_dataset_query(db, dataset_name, limit=limit, offset=offset)

        def generate():
            buf = io.StringIO()
            if not data_rows:
                # still emit an empty file with no header when unknown shape
                yield ""
                return
            writer = csv.DictWriter(
                buf, fieldnames=list(data_rows[0].keys()), extrasaction="ignore"
            )
            writer.writeheader()
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)
            for row in data_rows:
                writer.writerow(row)
                yield buf.getvalue()
                buf.seek(0)
                buf.truncate(0)

        filename = f"{dataset_name}.csv"
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as validation_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(validation_error))
    except SQLAlchemyError as db_error:
        logger.error(f"Database error exporting dataset {dataset_name}: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database query failed"
        )


@router.get("/datasets/{dataset_name}", response_model=DatasetResponse, tags=["datasets"])
async def query_dataset(
    dataset_name: str = Path(..., description="Name of the dataset to query"),
    limit: int = Query(100, ge=1, le=MAX_LIMIT, description="Maximum rows to return"),
    offset: int = Query(0, ge=0, description="Number of rows to skip"),
    db: Session = Depends(get_db),
):
    """
    Query a specific dataset with pagination.
    Supports all dynamically discovered datasets and predefined aggregations.
    """
    try:
        total_count = get_dataset_count(db, dataset_name)

        data_rows = execute_dataset_query(db, dataset_name, limit=limit, offset=offset)

        has_more_data = (offset + limit) < total_count

        return DatasetResponse(
            dataset=dataset_name,
            total_count=total_count,
            limit=limit,
            offset=offset,
            data=data_rows,
            has_more=has_more_data,
        )

    except ValueError as validation_error:
        logger.warning(f"Dataset not found: {dataset_name}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(validation_error))
    except SQLAlchemyError as db_error:
        logger.error(f"Database error querying dataset {dataset_name}: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database query failed"
        )
    except Exception as query_error:
        logger.error(f"Error querying dataset {dataset_name}: {query_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Query execution failed"
        )


@router.get("/stats", response_model=StatsResponse, tags=["statistics"])
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get comprehensive database statistics.
    Returns counts for all major tables and available tables list.
    """
    try:
        stats = StatsResponse()

        try:
            stats.total_urls = db.query(func.count(models.URL.id)).scalar() or 0
        except Exception:
            logger.warning("Failed to count URLs")

        try:
            stats.total_classifications = (
                db.query(func.count(models.Classification.id)).scalar() or 0
            )
        except Exception:
            logger.warning("Failed to count classifications")

        try:
            stats.total_patterns = db.query(func.count(models.Pattern.id)).scalar() or 0
        except Exception:
            logger.warning("Failed to count patterns")

        try:
            stats.total_sessions = db.query(func.count(models.CrawlSession.id)).scalar() or 0
        except Exception:
            logger.warning("Failed to count sessions")

        try:
            stats.domains_count = (
                db.query(func.count(func.distinct(models.URL.domain))).scalar() or 0
            )
        except Exception:
            logger.warning("Failed to count domains")

        try:
            table_query = text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
            result = db.execute(table_query)
            stats.available_tables = [row[0] for row in result]
        except Exception:
            logger.warning("Failed to list tables")

        return stats

    except Exception as stats_error:
        logger.error(f"Error getting statistics: {stats_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


@router.get("/urls", tags=["urls"])
async def list_urls(
    limit: int = Query(50, ge=1, le=500, description="Maximum URLs to return"),
    offset: int = Query(0, ge=0, description="Number of URLs to skip"),
    domain: Optional[str] = Query(None, max_length=255, description="Filter by domain"),
    status_code: Optional[int] = Query(None, ge=100, le=599, description="Filter by HTTP status"),
    db: Session = Depends(get_db),
):
    """
    List URLs with optional filtering and pagination.
    Supports filtering by domain and HTTP status code.
    """
    try:
        query = db.query(models.URL)

        if domain:
            query = query.filter(models.URL.domain == domain)

        if status_code:
            query = query.filter(models.URL.status_code == status_code)

        total_count = query.count()

        urls = query.offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
            "data": [
                {
                    "id": url.id,
                    "url": url.url,
                    "domain": url.domain,
                    "status_code": url.status_code,
                    "content_type": url.content_type,
                    "last_crawled": url.last_crawled.isoformat() if url.last_crawled else None,
                }
                for url in urls
            ],
        }

    except SQLAlchemyError as db_error:
        logger.error(f"Database error listing URLs: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to retrieve URLs"
        )
    except Exception as url_error:
        logger.error(f"Error listing URLs: {url_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list URLs"
        )


@router.get("/urls/{url_id}", tags=["urls"])
async def get_url_details(
    url_id: int = Path(..., gt=0, description="URL ID"), db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific URL including related data.
    Returns URL metadata, classifications, and page metadata if available.
    """
    try:
        url = db.query(models.URL).filter(models.URL.id == url_id).first()

        if not url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"URL with ID {url_id} not found"
            )

        response = {
            "id": url.id,
            "url": url.url,
            "domain": url.domain,
            "path": url.path,
            "status_code": url.status_code,
            "content_type": url.content_type,
            "file_extension": url.file_extension,
            "last_crawled": url.last_crawled.isoformat() if url.last_crawled else None,
            "created_at": url.created_at.isoformat() if url.created_at else None,
            "updated_at": url.updated_at.isoformat() if url.updated_at else None,
            "classifications": [],
            "page_metadata": None,
        }

        if url.classifications:
            response["classifications"] = [
                {
                    "category": classification.category,
                    "confidence": classification.confidence,
                    "model_version": classification.model_version,
                    "created_at": (
                        classification.created_at.isoformat() if classification.created_at else None
                    ),
                }
                for classification in url.classifications
            ]

        if url.page_metadata:
            pm = url.page_metadata
            response["page_metadata"] = {
                "title": pm.title,
                "description": pm.description,
                "keywords": pm.keywords,
                "language": pm.language,
                "word_count": pm.word_count,
                "has_images": pm.has_images,
                "has_videos": pm.has_videos,
                "has_forms": pm.has_forms,
                "extracted_at": pm.extracted_at.isoformat() if pm.extracted_at else None,
            }

        return response

    except HTTPException:
        raise
    except SQLAlchemyError as db_error:
        logger.error(f"Database error getting URL details: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to retrieve URL details"
        )
    except Exception as details_error:
        logger.error(f"Error getting URL details: {details_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get URL details"
        )


@router.get("/domains", tags=["domains"])
async def list_domains(
    limit: int = Query(50, ge=1, le=500, description="Maximum domains to return"),
    offset: int = Query(0, ge=0, description="Number of domains to skip"),
    db: Session = Depends(get_db),
):
    """
    List all domains with URL counts.
    Returns domains sorted by URL count in descending order.
    """
    try:
        query = (
            db.query(models.URL.domain, func.count(models.URL.id).label("url_count"))
            .filter(models.URL.domain.isnot(None))
            .group_by(models.URL.domain)
            .order_by(func.count(models.URL.id).desc())
        )

        total_count = query.count()
        results = query.offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
            "data": [{"domain": domain, "url_count": count} for domain, count in results],
        }

    except SQLAlchemyError as db_error:
        logger.error(f"Database error listing domains: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to retrieve domains"
        )
    except Exception as domain_error:
        logger.error(f"Error listing domains: {domain_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list domains"
        )


@router.get("/pattern-types", tags=["patterns"])
async def list_pattern_types(db: Session = Depends(get_db)):
    """Distinct pattern types for filter dropdown (#3)."""
    try:
        rows = (
            db.query(models.Pattern.pattern_type)
            .filter(models.Pattern.pattern_type.isnot(None))
            .distinct()
            .order_by(models.Pattern.pattern_type)
            .all()
        )
        return {"types": [r[0] for r in rows if r[0]]}
    except Exception as exc:
        logger.warning("Failed to list pattern types: %s", exc)
        return {"types": []}


@router.get("/patterns", tags=["patterns"])
async def list_patterns(
    pattern_type: Optional[str] = Query(None, max_length=50, description="Filter by pattern type"),
    limit: int = Query(50, ge=1, le=500, description="Maximum patterns to return"),
    offset: int = Query(0, ge=0, description="Number of patterns to skip"),
    db: Session = Depends(get_db),
):
    """
    List discovered patterns with optional filtering.
    Supports filtering by pattern type.
    """
    try:
        query = db.query(models.Pattern)

        if pattern_type:
            query = query.filter(models.Pattern.pattern_type == pattern_type)

        query = query.order_by(models.Pattern.frequency.desc())

        total_count = query.count()
        patterns = query.offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
            "data": [
                {
                    "id": pattern.id,
                    "pattern_type": pattern.pattern_type,
                    "pattern_value": pattern.pattern_value,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "discovered_at": (
                        pattern.discovered_at.isoformat() if pattern.discovered_at else None
                    ),
                }
                for pattern in patterns
            ],
        }

    except SQLAlchemyError as db_error:
        logger.error(f"Database error listing patterns: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to retrieve patterns"
        )
    except Exception as pattern_error:
        logger.error(f"Error listing patterns: {pattern_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list patterns"
        )


@router.get("/sessions", tags=["sessions"])
async def list_sessions(
    status_filter: Optional[str] = Query(
        None, max_length=50, description="Filter by session status", alias="status"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    db: Session = Depends(get_db),
):
    """
    List crawl sessions with optional status filtering.
    Returns sessions sorted by start time in descending order.
    """
    try:
        query = db.query(models.CrawlSession)

        if status_filter:
            query = query.filter(models.CrawlSession.status == status_filter)

        query = query.order_by(models.CrawlSession.started_at.desc())

        total_count = query.count()
        sessions = query.offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
            "data": [
                {
                    "id": session.id,
                    "session_id": session.session_id,
                    "total_urls": session.total_urls,
                    "processed_urls": session.processed_urls,
                    "failed_urls": session.failed_urls,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": (
                        session.completed_at.isoformat() if session.completed_at else None
                    ),
                    "status": session.status,
                }
                for session in sessions
            ],
        }

    except SQLAlchemyError as db_error:
        logger.error(f"Database error listing sessions: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to retrieve sessions"
        )
    except Exception as session_error:
        logger.error(f"Error listing sessions: {session_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list sessions"
        )


# --- Registry / dashboards / queries / freshness (#28–#31) ---
from datetime import datetime, timedelta, timezone

from fastapi import Body
from pydantic import BaseModel, Field
from sqlalchemy import text

from app import cache as dv_cache
from app.config import settings as app_settings


class DashboardIn(BaseModel):
    name: str
    layout_json: dict = Field(default_factory=dict)
    owner: str = "local"


class SavedQueryIn(BaseModel):
    name: str
    sql: str
    owner: str = "local"


@router.get("/registry", tags=["registry"])
async def list_registry(db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text(
                "SELECT name, source_uri, ingested_at, row_count, schema_hash, sla_hours FROM dataset_registry ORDER BY name"
            )
        ).fetchall()
    except Exception:
        return {"datasets": []}
    now = datetime.now(timezone.utc)
    out = []
    for r in rows:
        ingested = r[2]
        sla = r[5] or 168
        stale = False
        if ingested is not None:
            if getattr(ingested, "tzinfo", None) is None:
                ingested = ingested.replace(tzinfo=timezone.utc)
            stale = (now - ingested) > timedelta(hours=sla)
        out.append(
            {
                "name": r[0],
                "source_uri": r[1],
                "ingested_at": ingested.isoformat() if ingested else None,
                "row_count": r[3],
                "schema_hash": r[4],
                "sla_hours": sla,
                "freshness": "stale" if stale else "fresh",
            }
        )
    return {"datasets": out}


@router.post("/registry/register", tags=["registry"])
async def register_dataset(payload: dict = Body(...), db: Session = Depends(get_db)):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    db.execute(
        text("""INSERT INTO dataset_registry (name, source_uri, row_count, schema_hash, sla_hours)
               VALUES (:n, :u, :c, :h, :s)
               ON CONFLICT (name) DO UPDATE SET
                 source_uri=EXCLUDED.source_uri,
                 row_count=EXCLUDED.row_count,
                 schema_hash=EXCLUDED.schema_hash,
                 sla_hours=EXCLUDED.sla_hours,
                 ingested_at=now()"""),
        {
            "n": name,
            "u": payload.get("source_uri"),
            "c": int(payload.get("row_count") or 0),
            "h": payload.get("schema_hash"),
            "s": int(payload.get("sla_hours") or 168),
        },
    )
    db.commit()
    return {"ok": True, "name": name}


@router.get("/dashboards", tags=["dashboards"])
async def list_dashboards(db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text(
                "SELECT id, name, layout_json, owner, updated_at FROM dashboards ORDER BY updated_at DESC"
            )
        ).fetchall()
    except Exception:
        return {"dashboards": []}
    if not rows:
        return {"dashboards": [], "empty": True}
    return {
        "dashboards": [
            {
                "id": r[0],
                "name": r[1],
                "layout_json": r[2],
                "owner": r[3],
                "updated_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    }


@router.post("/dashboards", tags=["dashboards"])
async def save_dashboard(payload: DashboardIn, db: Session = Depends(get_db)):
    row = db.execute(
        text("""INSERT INTO dashboards (name, layout_json, owner)
               VALUES (:n, CAST(:l AS jsonb), :o) RETURNING id"""),
        {"n": payload.name, "l": __import__("json").dumps(payload.layout_json), "o": payload.owner},
    ).fetchone()
    db.commit()
    return {"id": row[0], "name": payload.name}


@router.get("/saved-queries", tags=["queries"])
async def list_saved_queries(db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text("SELECT id, name, sql, owner, created_at FROM saved_queries ORDER BY id DESC")
        ).fetchall()
    except Exception:
        return {"queries": []}
    return {
        "queries": [
            {
                "id": r[0],
                "name": r[1],
                "sql": r[2],
                "owner": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    }


@router.post("/saved-queries", tags=["queries"])
async def create_saved_query(payload: SavedQueryIn, db: Session = Depends(get_db)):
    sql = (payload.sql or "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="sql required")
    # cheap lint: reject multiple statements / dangerous keywords for library safety
    lowered = sql.lower()
    if any(
        x in lowered
        for x in (";--", " drop ", " delete ", " truncate ", " alter ", " insert ", " update ")
    ):
        raise HTTPException(status_code=400, detail="mutating SQL rejected")
    if ";" in sql.rstrip(";"):
        raise HTTPException(status_code=400, detail="multiple statements rejected")
    try:
        import sqlparse

        parsed = sqlparse.parse(sql)
        if not parsed:
            raise HTTPException(status_code=400, detail="invalid SQL")
    except ImportError:
        if not lowered.startswith("select"):
            raise HTTPException(status_code=400, detail="only SELECT allowed without sqlparse")
    row = db.execute(
        text("INSERT INTO saved_queries (name, sql, owner) VALUES (:n, :s, :o) RETURNING id"),
        {"n": payload.name, "s": sql, "o": payload.owner},
    ).fetchone()
    db.commit()
    return {"id": row[0]}


@router.post("/saved-queries/{query_id}/run", tags=["queries"])
async def run_saved_query(query_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT sql FROM saved_queries WHERE id=:i"), {"i": query_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="query not found")
    sql = row[0]
    if not sql.lower().lstrip().startswith("select"):
        raise HTTPException(status_code=400, detail="only SELECT runnable")
    result = db.execute(text(sql))
    cols = list(result.keys())
    data = [dict(zip(cols, r)) for r in result.fetchmany(200)]
    return {"columns": cols, "rows": data}


@router.post("/freshness/check", tags=["freshness"])
async def freshness_check(db: Session = Depends(get_db)):
    """Fire webhook once per open window when dataset SLA breached (#31)."""
    import json
    import urllib.request

    reg = await list_registry(db)
    fired = []
    for ds in reg.get("datasets", []):
        if ds.get("freshness") != "stale":
            # clear open alert if recovered
            db.execute(
                text(
                    "UPDATE freshness_alerts SET cleared_at=now() WHERE dataset_name=:n AND cleared_at IS NULL"
                ),
                {"n": ds["name"]},
            )
            continue
        open_alert = db.execute(
            text("SELECT id FROM freshness_alerts WHERE dataset_name=:n AND cleared_at IS NULL"),
            {"n": ds["name"]},
        ).fetchone()
        if open_alert:
            continue
        payload = {"text": f"Dataset {ds['name']} is stale", "dataset": ds}
        db.execute(
            text(
                "INSERT INTO freshness_alerts (dataset_name, payload_json) VALUES (:n, CAST(:p AS jsonb))"
            ),
            {"n": ds["name"], "p": json.dumps(payload)},
        )
        if app_settings.FRESHNESS_WEBHOOK:
            req = urllib.request.Request(
                app_settings.FRESHNESS_WEBHOOK,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                urllib.request.urlopen(req, timeout=5).read()
            except Exception:
                pass
        fired.append(ds["name"])
    db.commit()
    return {"fired": fired}
