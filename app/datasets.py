"""Dataset management for defining queryable data sources."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class Dataset:
    """Represents a queryable dataset."""
    name: str
    description: str
    table_name: str
    sql_query: Optional[str] = None
    columns: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


# Predefined datasets based on the schema
DATASETS = {
    "urls": Dataset(
        name="URLs",
        description="All crawled URLs with basic metadata",
        table_name="urls",
        columns=["id", "url", "domain", "path", "status_code", "content_type",
                 "file_extension", "last_crawled", "created_at"]
    ),
    "urls_by_domain": Dataset(
        name="URLs by Domain",
        description="URLs grouped by domain with counts",
        table_name="urls",
        sql_query="""
            SELECT
                domain,
                COUNT(*) as url_count,
                COUNT(DISTINCT file_extension) as file_types,
                MAX(last_crawled) as last_crawl,
                AVG(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) * 100 as success_rate
            FROM urls
            WHERE domain IS NOT NULL
            GROUP BY domain
            ORDER BY url_count DESC
        """
    ),
    "classifications": Dataset(
        name="URL Classifications",
        description="Classified URLs with categories and confidence scores",
        table_name="classifications",
        sql_query="""
            SELECT
                c.id,
                c.category,
                c.confidence,
                c.model_version,
                u.url,
                u.domain,
                c.created_at
            FROM classifications c
            JOIN urls u ON c.url_id = u.id
            ORDER BY c.created_at DESC
        """
    ),
    "page_metadata": Dataset(
        name="Page Metadata",
        description="Detailed page metadata including content analysis",
        table_name="page_metadata",
        sql_query="""
            SELECT
                pm.*,
                u.url,
                u.domain
            FROM page_metadata pm
            JOIN urls u ON pm.url_id = u.id
            ORDER BY pm.extracted_at DESC
        """
    ),
    "patterns": Dataset(
        name="Discovered Patterns",
        description="Pattern analysis results",
        table_name="patterns",
        columns=["id", "pattern_type", "pattern_value", "frequency",
                 "confidence", "discovered_at"]
    ),
    "crawl_sessions": Dataset(
        name="Crawl Sessions",
        description="Crawl session tracking and statistics",
        table_name="crawl_sessions",
        columns=["id", "session_id", "total_urls", "processed_urls",
                 "failed_urls", "started_at", "completed_at", "status"]
    ),
    "domain_statistics": Dataset(
        name="Domain Statistics",
        description="Comprehensive domain-level statistics",
        table_name="urls",
        sql_query="""
            SELECT
                domain,
                COUNT(*) as total_urls,
                COUNT(CASE WHEN status_code = 200 THEN 1 END) as successful_urls,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_urls,
                COUNT(DISTINCT file_extension) as unique_extensions,
                MIN(last_crawled) as first_crawl,
                MAX(last_crawled) as last_crawl,
                AVG(CASE WHEN content_type LIKE 'text/html%' THEN 1 ELSE 0 END) * 100 as html_percentage
            FROM urls
            WHERE domain IS NOT NULL
            GROUP BY domain
            HAVING COUNT(*) > 0
            ORDER BY total_urls DESC
        """
    ),
    "content_types": Dataset(
        name="Content Types Distribution",
        description="Distribution of content types across all URLs",
        table_name="urls",
        sql_query="""
            SELECT
                content_type,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
            FROM urls
            WHERE content_type IS NOT NULL
            GROUP BY content_type
            ORDER BY count DESC
        """
    ),
    "status_codes": Dataset(
        name="HTTP Status Codes",
        description="Distribution of HTTP status codes",
        table_name="urls",
        sql_query="""
            SELECT
                status_code,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
            FROM urls
            WHERE status_code IS NOT NULL
            GROUP BY status_code
            ORDER BY status_code
        """
    )
}


def get_dataset(name: str) -> Optional[Dataset]:
    """Get a dataset by name."""
    return DATASETS.get(name)


def list_datasets() -> List[Dataset]:
    """List all available datasets."""
    return list(DATASETS.values())


def execute_dataset_query(db: Session, dataset_name: str,
                          limit: int = 100, offset: int = 0,
                          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a dataset query and return results.

    Args:
        db: Database session
        dataset_name: Name of the dataset to query
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        filters: Optional filters to apply (dict of column: value)

    Returns:
        List of dictionaries representing rows
    """
    dataset = get_dataset(dataset_name)
    if not dataset:
        raise ValueError(f"Dataset '{dataset_name}' not found")

    # Use custom SQL query if provided, otherwise build simple SELECT
    if dataset.sql_query:
        query = dataset.sql_query
    else:
        columns = ", ".join(dataset.columns) if dataset.columns else "*"
        query = f"SELECT {columns} FROM {dataset.table_name}"

    # Add filters if provided
    if filters:
        where_clauses = []
        for col, val in filters.items():
            if isinstance(val, str):
                where_clauses.append(f"{col} = '{val}'")
            else:
                where_clauses.append(f"{col} = {val}")

        if where_clauses:
            if "WHERE" in query.upper():
                query += " AND " + " AND ".join(where_clauses)
            else:
                query += " WHERE " + " AND ".join(where_clauses)

    # Add pagination
    query += f" LIMIT {limit} OFFSET {offset}"

    # Execute query
    result = db.execute(text(query))

    # Convert to list of dicts
    columns = result.keys()
    rows = []
    for row in result:
        rows.append(dict(zip(columns, row)))

    return rows


def get_dataset_count(db: Session, dataset_name: str,
                      filters: Optional[Dict[str, Any]] = None) -> int:
    """Get total count for a dataset."""
    dataset = get_dataset(dataset_name)
    if not dataset:
        raise ValueError(f"Dataset '{dataset_name}' not found")

    # Build count query
    if dataset.sql_query:
        # Wrap custom query in subquery
        query = f"SELECT COUNT(*) as count FROM ({dataset.sql_query}) as subq"
    else:
        query = f"SELECT COUNT(*) as count FROM {dataset.table_name}"

    # Add filters if provided
    if filters and not dataset.sql_query:
        where_clauses = []
        for col, val in filters.items():
            if isinstance(val, str):
                where_clauses.append(f"{col} = '{val}'")
            else:
                where_clauses.append(f"{col} = {val}")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

    result = db.execute(text(query))
    return result.fetchone()[0]
