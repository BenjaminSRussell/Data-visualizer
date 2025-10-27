"""
SQLAlchemy Models for URL Analysis Database
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Domain(Base):
    """Top-level domain analysis"""
    __tablename__ = 'domains'

    id = Column(Integer, primary_key=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    tld = Column(String(50))  # top-level domain (.edu, .com, etc.)
    registered_domain = Column(String(255))  # e.g., hartford.edu

    # statistics
    total_urls = Column(Integer, default=0)
    total_subdomains = Column(Integer, default=0)
    avg_depth = Column(Float)
    avg_path_length = Column(Float)

    # temporal
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    subdomains = relationship("Subdomain", back_populates="domain", cascade="all, delete-orphan")
    urls = relationship("URL", back_populates="domain", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Domain(domain='{self.domain}', urls={self.total_urls})>"


class Subdomain(Base):
    """Subdomain analysis"""
    __tablename__ = 'subdomains'

    id = Column(Integer, primary_key=True)
    subdomain = Column(String(255), nullable=False, index=True)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False)
    full_subdomain = Column(String(512))  # e.g., www.hartford.edu

    # statistics
    total_urls = Column(Integer, default=0)
    avg_depth = Column(Float)
    avg_path_length = Column(Float)

    # temporal
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    domain = relationship("Domain", back_populates="subdomains")
    urls = relationship("URL", back_populates="subdomain", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('subdomain', 'domain_id', name='unique_subdomain_per_domain'),
        Index('idx_subdomain_domain', 'subdomain', 'domain_id'),
    )

    def __repr__(self):
        return f"<Subdomain(subdomain='{self.subdomain}', urls={self.total_urls})>"


class URLBatch(Base):
    """URL Batch - Groups of URLs with similar characteristics"""
    __tablename__ = 'url_batches'

    id = Column(Integer, primary_key=True)
    batch_name = Column(String(255), nullable=False)
    batch_type = Column(String(100))  # 'domain', 'path_pattern', 'temporal', 'semantic'

    # batch characteristics
    pattern = Column(String(512))  # the pattern that defines this batch
    category = Column(String(100))  # category of urls in batch

    # statistics
    total_urls = Column(Integer, default=0)
    avg_depth = Column(Float)
    avg_quality_score = Column(Float)

    # contextual information
    context = Column(JSON)  # what led to this batch (parent urls, discovery method, etc.)
    metadata = Column(JSON)  # additional metadata

    # temporal
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    urls = relationship("URL", back_populates="batch", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<URLBatch(name='{self.batch_name}', type='{self.batch_type}', urls={self.total_urls})>"


class URL(Base):
    """Individual URL with comprehensive analysis"""
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False, index=True)
    url_hash = Column(String(64), unique=True, nullable=False, index=True)  # sha256 hash

    # url components
    scheme = Column(String(10))  # http, https
    netloc = Column(String(512))  # full network location
    path = Column(Text)
    query = Column(Text)
    fragment = Column(String(255))

    # foreign keys
    domain_id = Column(Integer, ForeignKey('domains.id'))
    subdomain_id = Column(Integer, ForeignKey('subdomains.id'))
    batch_id = Column(Integer, ForeignKey('url_batches.id'))

    # basic metrics
    depth = Column(Integer)
    path_length = Column(Integer)
    query_param_count = Column(Integer, default=0)

    # content metadata
    status_code = Column(Integer)
    content_type = Column(String(100))
    title = Column(Text)

    # link analysis
    parent_url = Column(Text)
    outbound_links_count = Column(Integer, default=0)
    inbound_links_count = Column(Integer, default=0)

    # quality metrics
    quality_score = Column(Float)
    health_score = Column(Float)
    seo_score = Column(Float)

    # categorization
    category = Column(String(100))
    semantic_category = Column(String(100))
    is_dead_end = Column(Boolean, default=False)

    # temporal
    discovered_at = Column(DateTime)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # rich metadata
    metadata = Column(JSON)  # store additional analysis data

    # relationships
    domain = relationship("Domain", back_populates="urls")
    subdomain = relationship("Subdomain", back_populates="urls")
    batch = relationship("URLBatch", back_populates="urls")
    path_components = relationship("PathComponent", back_populates="url", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="url", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_url_hash', 'url_hash'),
        Index('idx_url_domain', 'domain_id'),
        Index('idx_url_batch', 'batch_id'),
        Index('idx_url_category', 'category'),
    )

    def __repr__(self):
        return f"<URL(id={self.id}, depth={self.depth}, quality={self.quality_score})>"


class PathComponent(Base):
    """Individual components of URL path for deep analysis"""
    __tablename__ = 'path_components'

    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('urls.id'), nullable=False)

    component = Column(String(512), nullable=False)
    position = Column(Integer, nullable=False)  # position in path (0-indexed)
    component_type = Column(String(50))  # 'directory', 'file', 'parameter', etc.

    # semantic analysis
    semantic_meaning = Column(String(100))  # inferred meaning
    is_numeric = Column(Boolean, default=False)
    is_date = Column(Boolean, default=False)
    is_id = Column(Boolean, default=False)

    # relationships
    url = relationship("URL", back_populates="path_components")

    __table_args__ = (
        Index('idx_component_url', 'url_id'),
        Index('idx_component_value', 'component'),
    )

    def __repr__(self):
        return f"<PathComponent(component='{self.component}', position={self.position})>"


class AnalysisResult(Base):
    """Store results from different analysis modules"""
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('urls.id'), nullable=False)

    # analysis metadata
    analysis_type = Column(String(100), nullable=False)  # 'statistical', 'network', 'semantic', etc.
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)

    # results
    results = Column(JSON, nullable=False)  # store analysis results as json

    # scores
    score = Column(Float)
    confidence = Column(Float)

    # relationships
    url = relationship("URL", back_populates="analysis_results")

    __table_args__ = (
        Index('idx_analysis_url_type', 'url_id', 'analysis_type'),
    )

    def __repr__(self):
        return f"<AnalysisResult(type='{self.analysis_type}', score={self.score})>"
