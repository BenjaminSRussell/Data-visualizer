"""SQLAlchemy models matching the PostgreSQL schema."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    TIMESTAMP, ForeignKey, ARRAY
)
from sqlalchemy.orm import relationship
from app.database import Base


class URL(Base):
    """URLs table - main URL storage."""
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, unique=True, nullable=False, index=True)
    domain = Column(String(255), index=True)
    path = Column(Text)
    last_crawled = Column(TIMESTAMP)
    status_code = Column(Integer)
    content_type = Column(String(100))
    file_extension = Column(String(50), index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classifications = relationship("Classification", back_populates="url", cascade="all, delete-orphan")
    metadata = relationship("PageMetadata", back_populates="url", uselist=False, cascade="all, delete-orphan")


class Classification(Base):
    """Classifications table - URL classifications."""
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), index=True)
    category = Column(String(100), index=True)
    confidence = Column(Float, index=True)
    model_version = Column(String(50))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    url = relationship("URL", back_populates="classifications")


class PageMetadata(Base):
    """Page metadata table - page-level data."""
    __tablename__ = "page_metadata"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), unique=True, index=True)
    title = Column(Text)
    description = Column(Text)
    keywords = Column(ARRAY(Text))
    language = Column(String(10))
    word_count = Column(Integer)
    has_images = Column(Boolean)
    has_videos = Column(Boolean)
    has_forms = Column(Boolean)
    extracted_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    url = relationship("URL", back_populates="metadata")


class Pattern(Base):
    """Patterns table - discovered patterns."""
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String(50), index=True)
    pattern_value = Column(Text)
    frequency = Column(Integer)
    confidence = Column(Float)
    discovered_at = Column(TIMESTAMP, default=datetime.utcnow)


class CrawlSession(Base):
    """Crawl sessions table - crawl tracking."""
    __tablename__ = "crawl_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    total_urls = Column(Integer)
    processed_urls = Column(Integer, default=0)
    failed_urls = Column(Integer, default=0)
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(50), default="processing", index=True)


class URLAnalysis(Base):
    """Legacy URL analyses table."""
    __tablename__ = "url_analyses"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    path = Column(Text)
    classifications = Column(Text)  # JSON as text
    sitemap_url = Column(Text)
    priority = Column(Float)
    change_freq = Column(String(50))
    last_modified = Column(TIMESTAMP, index=True)
    analyzed_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    analysis_version = Column(String(50))
    status = Column(String(50), default="pending", nullable=False)
    error_message = Column(Text)


class SitemapSource(Base):
    """Sitemap sources table."""
    __tablename__ = "sitemap_sources"

    id = Column(Integer, primary_key=True, index=True)
    sitemap_url = Column(Text, unique=True, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    total_urls = Column(Integer, default=0)
    analyzed_urls = Column(Integer, default=0)
    failed_urls = Column(Integer, default=0)
    first_crawled_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    last_crawled_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    crawl_frequency = Column(String(50))


class Category(Base):
    """Categories table - classification categories."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_type = Column(String(100), nullable=False, index=True)
    label = Column(String(200), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
