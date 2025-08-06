"""
Social media integration database models
"""
from datetime import datetime
from typing import List, Optional
import uuid
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime,
    ForeignKey, ARRAY, text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class InstagramPost(Base, UUIDMixin, TimestampMixin):
    """Model for Instagram posts and scheduling"""
    __tablename__ = "instagram_posts"
    
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('generated_content.id')
    )
    post_type: Mapped[str] = mapped_column(String(20), server_default=text("'feed'"))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(String))
    media_urls: Mapped[List[str]] = mapped_column(ARRAY(String))
    instagram_media_ids: Mapped[List[str]] = mapped_column(ARRAY(String))
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    instagram_post_id: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'scheduled'"))
    metrics: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    engagement_data: Mapped[dict] = mapped_column(
        JSONB, 
        server_default=text("'{}'::jsonb")
    )
    
    __table_args__ = (
        Index('idx_instagram_posts_status', 'status'),
        Index('idx_instagram_posts_scheduled', 'scheduled_for'),
        Index('idx_instagram_posts_posted', 'posted_at'),
    )


class SocialAccount(Base, TimestampMixin):
    """Model for social media accounts configuration"""
    __tablename__ = "social_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_id: Mapped[Optional[str]] = mapped_column(String(100))
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    configuration: Mapped[dict] = mapped_column(
        JSONB, 
        server_default=text("'{}'::jsonb")
    )
    
    __table_args__ = (
        UniqueConstraint('platform', 'account_id', name='uq_social_account'),
    )