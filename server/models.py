"""
Database models and configuration.
"""

import os
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator

from dotenv import load_dotenv
from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

logger = logging.getLogger(__name__)
load_dotenv()

# Database Configuration

DEFAULT_DB_URL = "sqlite:///./url_analyzer.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=SQL_ECHO, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session() -> Session:
    """Create a plain SQLAlchemy session."""
    return SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency helper that yields a session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope for operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize all database tables."""
    Base.metadata.create_all(bind=engine)


# Database Models


class Category(Base):
    """Dynamic classification category."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_type = Column(String(100), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_category_type_active", "category_type", "is_active"),
        Index("idx_category_type_label", "category_type", "label", unique=True),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category_type": self.category_type,
            "label": self.label,
            "description": self.description,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }


class URL(Base):
    """URL metadata."""

    __tablename__ = "urls"

    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False, index=True)
    domain = Column(String(255), index=True)
    path = Column(Text)
    session_id = Column(String(100), index=True)
    status_code = Column(Integer)
    content_type = Column(String(255))
    file_extension = Column(String(50))
    last_crawled = Column(DateTime, default=datetime.utcnow)

    # Relationships
    metadata = relationship("PageMetadata", back_populates="url", uselist=False, cascade="all, delete-orphan")
    classifications = relationship("Classification", back_populates="url", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_url_domain", "domain"),
        Index("idx_url_session", "session_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "domain": self.domain,
            "path": self.path,
            "session_id": self.session_id,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "file_extension": self.file_extension,
            "last_crawled": self.last_crawled.isoformat() if self.last_crawled else None,
        }


class PageMetadata(Base):
    """Page metadata extracted from HTML."""

    __tablename__ = "page_metadata"

    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), unique=True, nullable=False)
    title = Column(Text)
    description = Column(Text)
    keywords = Column(ARRAY(String), default=[])
    language = Column(String(10))
    author = Column(String(255))
    word_count = Column(Integer)
    has_images = Column(Boolean, default=False)
    has_videos = Column(Boolean, default=False)
    has_forms = Column(Boolean, default=False)

    # Relationship
    url = relationship("URL", back_populates="metadata")

    __table_args__ = (Index("idx_metadata_url", "url_id"),)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url_id": self.url_id,
            "title": self.title,
            "description": self.description,
            "keywords": self.keywords,
            "language": self.language,
            "author": self.author,
            "word_count": self.word_count,
            "has_images": self.has_images,
            "has_videos": self.has_videos,
            "has_forms": self.has_forms,
        }


class Classification(Base):
    """ML classification results."""

    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(100))
    classified_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    url = relationship("URL", back_populates="classifications")

    __table_args__ = (Index("idx_classification_url", "url_id"),)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url_id": self.url_id,
            "category": self.category,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "classified_at": self.classified_at.isoformat() if self.classified_at else None,
        }


class Pattern(Base):
    """Detected URL patterns."""

    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), index=True)
    pattern_type = Column(String(100), nullable=False)
    pattern_value = Column(String(500), nullable=False)
    frequency = Column(Integer, default=1)
    confidence = Column(Float, default=1.0)
    example = Column(Text)
    detected_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_pattern_type", "pattern_type"),
        Index("idx_pattern_session", "session_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "pattern_type": self.pattern_type,
            "pattern_value": self.pattern_value,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "example": self.example,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class CrawlSession(Base):
    """Tracking for sitemap processing sessions."""

    __tablename__ = "crawl_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    session_name = Column(String(255))
    total_urls = Column(Integer, default=0)
    processed_urls = Column(Integer, default=0)
    failed_urls = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    __table_args__ = (Index("idx_session_status", "status"),)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "session_name": self.session_name,
            "total_urls": self.total_urls,
            "processed_urls": self.processed_urls,
            "failed_urls": self.failed_urls,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
