"""
Web scraping system database models
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, 
    ForeignKey, ARRAY, Interval, text, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class ScraperTarget(Base, TimestampMixin):
    """Model for scraping targets configuration"""
    __tablename__ = "scraper_targets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    domains: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    categories: Mapped[List[str]] = mapped_column(ARRAY(String))
    scraping_rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    rate_limit_delay: Mapped[int] = mapped_column(Integer, server_default=text("2"))
    max_pages: Mapped[int] = mapped_column(Integer, server_default=text("100"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_scrape_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scrape_frequency: Mapped[timedelta] = mapped_column(
        Interval,
        server_default=text("INTERVAL '1 day'")
    )
    success_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    error_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    
    # Relationships
    scraping_jobs = relationship("ScrapingJob", back_populates="target")
    
    __table_args__ = (
        Index('idx_scraper_targets_active', 'is_active'),
        Index('idx_scraper_targets_next_scrape', 'next_scrape_at'),
    )


class ScrapingJob(Base, UUIDMixin, TimestampMixin):
    """Model for scraping jobs and status"""
    __tablename__ = "scraping_jobs"
    
    target_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('scraper_targets.id')
    )
    job_type: Mapped[str] = mapped_column(String(30), server_default=text("'scheduled'"))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    pages_scraped: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    content_found: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    errors_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    error_details: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    configuration: Mapped[dict] = mapped_column(
        JSONB, 
        server_default=text("'{}'::jsonb")
    )
    
    # Relationships
    target = relationship("ScraperTarget", back_populates="scraping_jobs")
    
    __table_args__ = (
        Index('idx_scraping_jobs_status', 'status'),
        Index('idx_scraping_jobs_target', 'target_id', 'created_at'),
    )