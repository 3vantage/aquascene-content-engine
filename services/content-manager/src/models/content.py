"""
Content-related database models
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, DECIMAL, 
    ForeignKey, ARRAY, text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class RawContent(Base, UUIDMixin, TimestampMixin):
    """Model for raw scraped content storage"""
    __tablename__ = "raw_content"
    
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    html_content: Mapped[Optional[str]] = mapped_column(Text)
    images: Mapped[dict] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    processed: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    processing_status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))
    processing_error: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(10), server_default=text("'en'"))
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    __table_args__ = (
        UniqueConstraint('content_hash', name='uq_raw_content_hash'),
        Index('idx_raw_content_source_domain', 'source_domain'),
        Index('idx_raw_content_processed', 'processed', 'scraped_at'),
        Index('idx_raw_content_type', 'content_type'),
        Index('idx_raw_content_hash', 'content_hash'),
    )


class GeneratedContent(Base, UUIDMixin, TimestampMixin):
    """Model for AI-generated content"""
    __tablename__ = "generated_content"
    
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)
    template_used: Mapped[Optional[str]] = mapped_column(String(100))
    source_materials: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    quality_score: Mapped[Optional[float]] = mapped_column(DECIMAL(3, 2))
    readability_score: Mapped[Optional[int]] = mapped_column(Integer)
    seo_score: Mapped[Optional[float]] = mapped_column(DECIMAL(3, 2))
    engagement_prediction: Mapped[Optional[float]] = mapped_column(DECIMAL(3, 2))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"))
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))
    categories: Mapped[List[str]] = mapped_column(ARRAY(String))
    target_audience: Mapped[Optional[str]] = mapped_column(String(50))
    tone: Mapped[Optional[str]] = mapped_column(String(30))
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_reading_time: Mapped[Optional[int]] = mapped_column(Integer)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    assets = relationship("ContentAssetRelation", back_populates="content")
    metrics = relationship("ContentMetric", back_populates="content")
    
    __table_args__ = (
        Index('idx_generated_content_status', 'status'),
        Index('idx_generated_content_type', 'content_type', 'status'),
        Index('idx_generated_content_published', 'published_at'),
        Index('idx_generated_content_scheduled', 'scheduled_for'),
        Index('idx_generated_content_tags', 'tags'),
        Index('idx_generated_content_categories', 'categories'),
    )


class ContentCategory(Base, TimestampMixin):
    """Model for content categories and taxonomy"""
    __tablename__ = "content_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('content_categories.id'))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    
    # Self-referential relationship
    parent = relationship("ContentCategory", remote_side=[id], back_populates="children")
    children = relationship("ContentCategory", back_populates="parent")


class ContentTag(Base, TimestampMixin):
    """Model for content tags"""
    __tablename__ = "content_tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    usage_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class ContentAsset(Base, UUIDMixin):
    """Model for content assets (images, videos, documents)"""
    __tablename__ = "content_assets"
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    file_type: Mapped[Optional[str]] = mapped_column(String(20))
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    alt_text: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    
    # Relationships
    content_relations = relationship("ContentAssetRelation", back_populates="asset")


class ContentAssetRelation(Base):
    """Model for linking content to assets"""
    __tablename__ = "content_asset_relations"
    
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey('generated_content.id', ondelete='CASCADE'),
        primary_key=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('content_assets.id', ondelete='CASCADE'),
        primary_key=True
    )
    relation_type: Mapped[str] = mapped_column(String(30), server_default=text("'attachment'"))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    
    # Relationships
    content = relationship("GeneratedContent", back_populates="assets")
    asset = relationship("ContentAsset", back_populates="content_relations")