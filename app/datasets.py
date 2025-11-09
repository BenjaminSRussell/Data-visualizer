"""
Dynamic dataset management with SQL injection prevention and automatic schema discovery.
"""
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

MAX_LIMIT = 10000
DEFAULT_LIMIT = 100
SAFE_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


@dataclass
class Dataset:
    """Represents a queryable dataset."""
    name: str
    description: str
    table_name: str
    sql_query: Optional[str] = None
    columns: Optional[List[str]] = None
    is_custom: bool = False
    params: Dict[str, Any] = field(default_factory=dict)


def validate_identifier(identifier: str) -> bool:
    """Validate that an identifier is safe for SQL (prevents injection)."""
    if not identifier or not isinstance(identifier, str):
        return False
    return SAFE_IDENTIFIER_PATTERN.match(identifier) is not None


def validate_limit(limit: int, max_limit: int = MAX_LIMIT) -> int:
    """Validate and sanitize limit parameter."""
    try:
        limit_value = int(limit)
        if limit_value < 1:
            return DEFAULT_LIMIT
        if limit_value > max_limit:
            return max_limit
        return limit_value
    except (ValueError, TypeError):
        return DEFAULT_LIMIT


def validate_offset(offset: int) -> int:
    """Validate and sanitize offset parameter."""
    try:
        offset_value = int(offset)
        return max(0, offset_value)
    except (ValueError, TypeError):
        return 0


def discover_tables(session: Session) -> List[str]:
    """Discover all table names in the database dynamically."""
    try:
        engine = session.get_bind()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Discovered {len(tables)} tables")
        return tables
    except Exception as discovery_error:
        logger.error(f"Failed to discover tables: {discovery_error}")
        return []


def discover_columns(session: Session, table_name: str) -> List[Dict[str, Any]]:
    """Discover columns for a table dynamically."""
    if not validate_identifier(table_name):
        logger.warning(f"Invalid table name: {table_name}")
        return []

    try:
        engine = session.get_bind()
        inspector = inspect(engine)

        if not inspector.has_table(table_name):
            logger.warning(f"Table does not exist: {table_name}")
            return []

        columns = inspector.get_columns(table_name)
        logger.info(f"Discovered {len(columns)} columns for table {table_name}")
        return columns

    except Exception as column_error:
        logger.error(f"Failed to discover columns for {table_name}: {column_error}")
        return []


def create_dynamic_datasets(session: Session) -> Dict[str, Dataset]:
    """Create datasets dynamically based on database schema."""
    datasets = {}

    tables = discover_tables(session)

    for table_name in tables:
        columns_info = discover_columns(session, table_name)

        if not columns_info:
            continue

        column_names = [col['name'] for col in columns_info]

        dataset_key = table_name.lower()
        datasets[dataset_key] = Dataset(
            name=table_name.replace('_', ' ').title(),
            description=f"All data from {table_name} table",
            table_name=table_name,
            columns=column_names,
            is_custom=False
        )

    logger.info(f"Created {len(datasets)} dynamic datasets")
    return datasets


PREDEFINED_DATASETS = {
    "urls_by_domain": Dataset(
        name="URLs by Domain",
        description="URLs grouped by domain with counts",
        table_name="urls",
        is_custom=True,
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
    "classifications_with_urls": Dataset(
        name="URL Classifications",
        description="Classified URLs with categories and confidence scores",
        table_name="classifications",
        is_custom=True,
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
    "page_metadata_with_urls": Dataset(
        name="Page Metadata",
        description="Detailed page metadata including content analysis",
        table_name="page_metadata",
        is_custom=True,
        sql_query="""
            SELECT
                pm.id,
                pm.title,
                pm.description,
                pm.language,
                pm.word_count,
                pm.has_images,
                pm.has_videos,
                pm.has_forms,
                u.url,
                u.domain,
                pm.extracted_at
            FROM page_metadata pm
            JOIN urls u ON pm.url_id = u.id
            ORDER BY pm.extracted_at DESC
        """
    ),
    "domain_statistics": Dataset(
        name="Domain Statistics",
        description="Comprehensive domain-level statistics",
        table_name="urls",
        is_custom=True,
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
    "content_types_distribution": Dataset(
        name="Content Types Distribution",
        description="Distribution of content types across all URLs",
        table_name="urls",
        is_custom=True,
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
    "status_codes_distribution": Dataset(
        name="HTTP Status Codes",
        description="Distribution of HTTP status codes",
        table_name="urls",
        is_custom=True,
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

_cached_datasets: Optional[Dict[str, Dataset]] = None


def get_all_datasets(session: Session, force_refresh: bool = False) -> Dict[str, Dataset]:
    """
    Get all datasets (predefined + dynamically discovered).

    Args:
        session: Database session
        force_refresh: Force refresh of cached datasets

    Returns:
        Dictionary of all available datasets
    """
    global _cached_datasets

    if _cached_datasets is not None and not force_refresh:
        return _cached_datasets

    try:
        dynamic_datasets = create_dynamic_datasets(session)
        all_datasets = {**dynamic_datasets, **PREDEFINED_DATASETS}
        _cached_datasets = all_datasets
        return all_datasets

    except Exception as dataset_error:
        logger.error(f"Failed to get all datasets: {dataset_error}")
        return PREDEFINED_DATASETS


def get_dataset(dataset_name: str, session: Optional[Session] = None) -> Optional[Dataset]:
    """Get a dataset by name."""
    if session:
        datasets = get_all_datasets(session)
        return datasets.get(dataset_name)
    else:
        return PREDEFINED_DATASETS.get(dataset_name)


def list_datasets(session: Optional[Session] = None) -> List[Dataset]:
    """List all available datasets."""
    if session:
        datasets = get_all_datasets(session)
        return list(datasets.values())
    else:
        return list(PREDEFINED_DATASETS.values())


def build_safe_where_clause(filters: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """
    Build a safe WHERE clause using parameterized queries.

    Returns:
        Tuple of (where_clause_string, parameters_dict)
    """
    if not filters:
        return "", {}

    where_parts = []
    params = {}

    for column_name, value in filters.items():
        if not validate_identifier(column_name):
            logger.warning(f"Skipping invalid column name in filter: {column_name}")
            continue

        param_name = f"filter_{column_name}"
        where_parts.append(f"{column_name} = :{param_name}")
        params[param_name] = value

    if not where_parts:
        return "", {}

    return " AND ".join(where_parts), params


def execute_dataset_query(
    db: Session,
    dataset_name: str,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute a dataset query with SQL injection prevention.

    Args:
        db: Database session
        dataset_name: Name of the dataset to query
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        filters: Optional filters to apply (dict of column: value)

    Returns:
        List of dictionaries representing rows

    Raises:
        ValueError: If dataset not found or invalid parameters
        SQLAlchemyError: If database query fails
    """
    datasets = get_all_datasets(db)
    dataset = datasets.get(dataset_name)

    if not dataset:
        raise ValueError(f"Dataset '{dataset_name}' not found")

    limit = validate_limit(limit)
    offset = validate_offset(offset)

    try:
        if dataset.sql_query:
            base_query = dataset.sql_query
            where_clause, params = "", {}
        else:
            if not validate_identifier(dataset.table_name):
                raise ValueError(f"Invalid table name: {dataset.table_name}")

            column_list = ", ".join(dataset.columns) if dataset.columns else "*"
            base_query = f"SELECT {column_list} FROM {dataset.table_name}"
            where_clause, params = build_safe_where_clause(filters or {})

        if where_clause:
            if "WHERE" in base_query.upper():
                full_query = f"{base_query} AND {where_clause}"
            else:
                full_query = f"{base_query} WHERE {where_clause}"
        else:
            full_query = base_query

        full_query += f" LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset

        result = db.execute(text(full_query), params)
        column_names = result.keys()
        rows = [dict(zip(column_names, row)) for row in result]

        logger.info(f"Query executed successfully: {dataset_name}, {len(rows)} rows returned")
        return rows

    except SQLAlchemyError as db_error:
        logger.error(f"Database error executing query for {dataset_name}: {db_error}")
        raise
    except Exception as query_error:
        logger.error(f"Error executing query for {dataset_name}: {query_error}")
        raise


def get_dataset_count(
    db: Session,
    dataset_name: str,
    filters: Optional[Dict[str, Any]] = None
) -> int:
    """
    Get total count for a dataset with SQL injection prevention.

    Args:
        db: Database session
        dataset_name: Name of the dataset
        filters: Optional filters to apply

    Returns:
        Total row count

    Raises:
        ValueError: If dataset not found
        SQLAlchemyError: If database query fails
    """
    datasets = get_all_datasets(db)
    dataset = datasets.get(dataset_name)

    if not dataset:
        raise ValueError(f"Dataset '{dataset_name}' not found")

    try:
        if dataset.sql_query:
            base_query = f"SELECT COUNT(*) as count FROM ({dataset.sql_query}) as subquery"
            params = {}
        else:
            if not validate_identifier(dataset.table_name):
                raise ValueError(f"Invalid table name: {dataset.table_name}")

            base_query = f"SELECT COUNT(*) as count FROM {dataset.table_name}"
            where_clause, params = build_safe_where_clause(filters or {})

            if where_clause:
                base_query += f" WHERE {where_clause}"

        result = db.execute(text(base_query), params)
        count = result.fetchone()[0]

        logger.info(f"Count query executed successfully: {dataset_name}, count={count}")
        return count

    except SQLAlchemyError as db_error:
        logger.error(f"Database error getting count for {dataset_name}: {db_error}")
        raise
    except Exception as count_error:
        logger.error(f"Error getting count for {dataset_name}: {count_error}")
        raise


def refresh_datasets(session: Session) -> int:
    """Force refresh of dataset cache and return number of datasets."""
    global _cached_datasets
    _cached_datasets = None
    datasets = get_all_datasets(session, force_refresh=True)
    logger.info(f"Refreshed datasets cache: {len(datasets)} datasets available")
    return len(datasets)
