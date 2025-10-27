"""
Database Connection Manager
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from .models import Base


class DatabaseManager:
    """Manage database connections and sessions"""

    def __init__(self, database_url=None):
        """
        Initialize database manager.

        Args:
            database_url: PostgreSQL connection string
                         Format: postgresql://user:password@localhost:5432/dbname
                         If None, will look for DATABASE_URL env variable
                         If env variable not found, will use local SQLite for development
        """
        if database_url is None:
            database_url = os.getenv(
                'DATABASE_URL',
                'sqlite:///analysis/data/url_analysis.db'  # fallback to sqlite for development
            )

        self.database_url = database_url
        self.engine = None
        self.session_factory = None

    def initialize(self):
        """Initialize database engine and create tables"""

        # create engine
        if self.database_url.startswith('postgresql'):
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
        else:
            # sqlite for development
            self.engine = create_engine(
                self.database_url,
                poolclass=NullPool,
                echo=False
            )

        # create session factory
        self.session_factory = scoped_session(
            sessionmaker(bind=self.engine, expire_on_commit=False)
        )

        # create all tables
        Base.metadata.create_all(self.engine)

        print(f"Database initialized: {self.database_url.split('@')[-1] if '@' in self.database_url else 'SQLite'}")

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_session(self):
        """Get a new session"""
        return self.session_factory()

    def close(self):
        """Close all connections"""
        if self.session_factory:
            self.session_factory.remove()
        if self.engine:
            self.engine.dispose()

    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(self.engine)
        print("All tables dropped!")

    def get_stats(self):
        """Get database statistics"""
        with self.session_scope() as session:
            from .models import URL, Domain, Subdomain, URLBatch, AnalysisResult

            stats = {
                'total_urls': session.query(URL).count(),
                'total_domains': session.query(Domain).count(),
                'total_subdomains': session.query(Subdomain).count(),
                'total_batches': session.query(URLBatch).count(),
                'total_analyses': session.query(AnalysisResult).count()
            }

            return stats


# global database manager instance
db_manager = None


def get_db_manager(database_url=None):
    """Get or create global database manager"""
    global db_manager

    if db_manager is None:
        db_manager = DatabaseManager(database_url)
        db_manager.initialize()

    return db_manager


def init_database(database_url=None):
    """Initialize database - convenience function"""
    manager = get_db_manager(database_url)
    return manager
