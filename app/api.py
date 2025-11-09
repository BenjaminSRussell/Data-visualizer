"""REST API endpoints for data retrieval and exploration."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.datasets import (
    list_datasets, get_dataset, execute_dataset_query,
    get_dataset_count, Dataset
)
from app import models


router = APIRouter()


# Pydantic models for API responses
class DatasetInfo(BaseModel):
    """Dataset information."""
    name: str
    description: str
    table_name: str


class DatasetResponse(BaseModel):
    """Dataset query response."""
    dataset: str
    total_count: int
    limit: int
    offset: int
    data: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    """Database statistics response."""
    total_urls: int
    total_classifications: int
    total_patterns: int
    total_sessions: int
    domains_count: int


# API Endpoints

@router.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Data Visualizer API",
        "version": "2.0.0",
        "description": "PostgreSQL-backed data visualization and exploration"
    }


@router.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")


@router.get("/datasets", response_model=List[DatasetInfo], tags=["datasets"])
async def get_datasets():
    """List all available datasets."""
    datasets = list_datasets()
    return [
        DatasetInfo(
            name=ds.name,
            description=ds.description,
            table_name=ds.table_name
        )
        for ds in datasets
    ]


@router.get("/datasets/{dataset_name}", response_model=DatasetResponse, tags=["datasets"])
async def query_dataset(
    dataset_name: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum rows to return"),
    offset: int = Query(0, ge=0, description="Number of rows to skip"),
    db: Session = Depends(get_db)
):
    """Query a dataset with pagination."""
    try:
        # Get total count
        total = get_dataset_count(db, dataset_name)

        # Get data
        data = execute_dataset_query(db, dataset_name, limit=limit, offset=offset)

        return DatasetResponse(
            dataset=dataset_name,
            total_count=total,
            limit=limit,
            offset=offset,
            data=data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/stats", response_model=StatsResponse, tags=["statistics"])
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall database statistics."""
    try:
        total_urls = db.query(models.URL).count()
        total_classifications = db.query(models.Classification).count()
        total_patterns = db.query(models.Pattern).count()
        total_sessions = db.query(models.CrawlSession).count()

        # Count distinct domains
        from sqlalchemy import func
        domains_count = db.query(func.count(func.distinct(models.URL.domain))).scalar()

        return StatsResponse(
            total_urls=total_urls,
            total_classifications=total_classifications,
            total_patterns=total_patterns,
            total_sessions=total_sessions,
            domains_count=domains_count or 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/urls", tags=["urls"])
async def list_urls(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    domain: Optional[str] = None,
    status_code: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List URLs with optional filtering."""
    query = db.query(models.URL)

    # Apply filters
    if domain:
        query = query.filter(models.URL.domain == domain)
    if status_code:
        query = query.filter(models.URL.status_code == status_code)

    # Get total count
    total = query.count()

    # Apply pagination
    urls = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": url.id,
                "url": url.url,
                "domain": url.domain,
                "status_code": url.status_code,
                "content_type": url.content_type,
                "last_crawled": url.last_crawled
            }
            for url in urls
        ]
    }


@router.get("/urls/{url_id}", tags=["urls"])
async def get_url_details(url_id: int, db: Session = Depends(get_db)):
    """Get detailed information for a specific URL."""
    url = db.query(models.URL).filter(models.URL.id == url_id).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    # Build response with related data
    response = {
        "id": url.id,
        "url": url.url,
        "domain": url.domain,
        "path": url.path,
        "status_code": url.status_code,
        "content_type": url.content_type,
        "file_extension": url.file_extension,
        "last_crawled": url.last_crawled,
        "created_at": url.created_at,
        "updated_at": url.updated_at,
        "classifications": [],
        "metadata": None
    }

    # Add classifications
    if url.classifications:
        response["classifications"] = [
            {
                "category": c.category,
                "confidence": c.confidence,
                "model_version": c.model_version,
                "created_at": c.created_at
            }
            for c in url.classifications
        ]

    # Add metadata
    if url.metadata:
        response["metadata"] = {
            "title": url.metadata.title,
            "description": url.metadata.description,
            "keywords": url.metadata.keywords,
            "language": url.metadata.language,
            "word_count": url.metadata.word_count,
            "has_images": url.metadata.has_images,
            "has_videos": url.metadata.has_videos,
            "has_forms": url.metadata.has_forms,
            "extracted_at": url.metadata.extracted_at
        }

    return response


@router.get("/domains", tags=["domains"])
async def list_domains(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List all domains with URL counts."""
    from sqlalchemy import func

    query = db.query(
        models.URL.domain,
        func.count(models.URL.id).label("url_count")
    ).filter(
        models.URL.domain.isnot(None)
    ).group_by(
        models.URL.domain
    ).order_by(
        func.count(models.URL.id).desc()
    )

    total = query.count()
    results = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {"domain": domain, "url_count": count}
            for domain, count in results
        ]
    }


@router.get("/patterns", tags=["patterns"])
async def list_patterns(
    pattern_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List discovered patterns."""
    query = db.query(models.Pattern)

    if pattern_type:
        query = query.filter(models.Pattern.pattern_type == pattern_type)

    query = query.order_by(models.Pattern.frequency.desc())

    total = query.count()
    patterns = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": p.id,
                "pattern_type": p.pattern_type,
                "pattern_value": p.pattern_value,
                "frequency": p.frequency,
                "confidence": p.confidence,
                "discovered_at": p.discovered_at
            }
            for p in patterns
        ]
    }


@router.get("/sessions", tags=["sessions"])
async def list_sessions(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List crawl sessions."""
    query = db.query(models.CrawlSession)

    if status:
        query = query.filter(models.CrawlSession.status == status)

    query = query.order_by(models.CrawlSession.started_at.desc())

    total = query.count()
    sessions = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": s.id,
                "session_id": s.session_id,
                "total_urls": s.total_urls,
                "processed_urls": s.processed_urls,
                "failed_urls": s.failed_urls,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
                "status": s.status
            }
            for s in sessions
        ]
    }
