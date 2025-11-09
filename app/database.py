"""Database connection and session management with robust error handling."""
import os
import logging
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool, Pool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def _validate_database_url(url: str) -> bool:
    """Validate database URL format."""
    if not url or not isinstance(url, str):
        return False

    valid_prefixes = ('postgresql://', 'postgresql+psycopg2://', 'sqlite://')
    return any(url.startswith(prefix) for prefix in valid_prefixes)


def get_database_url() -> str:
    """Get database URL from environment with validation."""
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/data_visualizer"
    )

    if not _validate_database_url(url):
        raise ValueError(f"Invalid DATABASE_URL format: {url}")

    return url


def get_pool_config(database_url: str) -> dict:
    """Get database pool configuration from environment."""
    config = {
        'poolclass': QueuePool,
        'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
        'pool_pre_ping': True,
        'echo': os.getenv('DB_ECHO', 'false').lower() == 'true'
    }

    if database_url.startswith('postgresql'):
        config['connect_args'] = {
            'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10'))
        }
    elif database_url.startswith('sqlite'):
        config['connect_args'] = {
            'check_same_thread': False
        }

    return config


def get_engine() -> Engine:
    """Get or create database engine with error handling."""
    global _engine

    if _engine is not None:
        return _engine

    try:
        database_url = get_database_url()
        pool_config = get_pool_config(database_url)

        _engine = create_engine(database_url, **pool_config)

        logger.info("Database engine created successfully")
        return _engine

    except ValueError as validation_error:
        logger.error(f"Database URL validation failed: {validation_error}")
        raise
    except Exception as engine_error:
        logger.error(f"Failed to create database engine: {engine_error}")
        raise RuntimeError(f"Database engine creation failed: {engine_error}") from engine_error


def get_session_factory() -> sessionmaker:
    """Get or create session factory with error handling."""
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    try:
        engine = get_engine()
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False
        )
        logger.info("Session factory created successfully")
        return _session_factory

    except Exception as factory_error:
        logger.error(f"Failed to create session factory: {factory_error}")
        raise RuntimeError(f"Session factory creation failed: {factory_error}") from factory_error


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions in FastAPI.
    Provides automatic session management with proper cleanup.
    """
    factory = get_session_factory()
    session = factory()

    try:
        yield session
        session.commit()
    except Exception as session_error:
        session.rollback()
        logger.error(f"Database session error: {session_error}")
        raise
    finally:
        try:
            session.close()
        except Exception as close_error:
            logger.warning(f"Error closing session: {close_error}")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for getting database sessions outside FastAPI."""
    factory = get_session_factory()
    session = factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> bool:
    """Initialize database tables with error handling."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
        return True

    except SQLAlchemyError as db_error:
        logger.error(f"Failed to initialize database tables: {db_error}")
        return False
    except Exception as init_error:
        logger.error(f"Unexpected error during database initialization: {init_error}")
        return False


def test_connection(max_retries: int = 3) -> bool:
    """
    Test database connection with retry logic.

    Args:
        max_retries: Maximum number of connection attempts

    Returns:
        True if connection successful, False otherwise
    """
    for attempt in range(1, max_retries + 1):
        try:
            factory = get_session_factory()
            session = factory()

            try:
                result = session.execute(text("SELECT 1"))
                result.fetchone()
                session.commit()
                logger.info("Database connection test successful")
                return True

            finally:
                session.close()

        except OperationalError as op_error:
            logger.warning(f"Connection attempt {attempt}/{max_retries} failed: {op_error}")
            if attempt == max_retries:
                logger.error("Database connection test failed after all retries")
                return False

        except Exception as test_error:
            logger.error(f"Database connection test failed: {test_error}")
            return False

    return False


def get_table_names() -> list[str]:
    """Get list of all table names in the database."""
    try:
        engine = get_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return tables

    except Exception as inspect_error:
        logger.error(f"Failed to get table names: {inspect_error}")
        return []


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        engine = get_engine()
        inspector = inspect(engine)
        return inspector.has_table(table_name)

    except Exception as check_error:
        logger.error(f"Failed to check if table exists: {check_error}")
        return False


def get_table_columns(table_name: str) -> list[dict]:
    """
    Get column information for a table.

    Returns list of dicts with: name, type, nullable, default
    """
    try:
        engine = get_engine()
        inspector = inspect(engine)

        if not inspector.has_table(table_name):
            return []

        columns = inspector.get_columns(table_name)
        return columns

    except Exception as column_error:
        logger.error(f"Failed to get columns for table {table_name}: {column_error}")
        return []


def reset_connection() -> None:
    """Reset database connection (useful for testing or connection issues)."""
    global _engine, _session_factory

    if _session_factory:
        _session_factory.close_all()

    if _engine:
        _engine.dispose()

    _engine = None
    _session_factory = None
    logger.info("Database connection reset")
