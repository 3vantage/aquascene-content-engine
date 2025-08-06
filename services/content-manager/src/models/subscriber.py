"""
Subscriber management database models
"""
import uuid
from datetime import datetime, time
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Time,
    ForeignKey, ARRAY, text, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Subscriber(Base, UUIDMixin, TimestampMixin):
    """Model for subscriber information"""
    __tablename__ = "subscribers"
    
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(50), server_default=text("'UTC'"))
    language: Mapped[str] = mapped_column(String(10), server_default=text("'en'"))
    source: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'active'"))
    subscription_date: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("NOW()")
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    bounce_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    complaint_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("NOW()")
    )
    preferences: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    custom_fields: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))
    
    # Relationships
    subscription_preferences = relationship(
        "SubscriptionPreference", 
        back_populates="subscriber",
        uselist=False
    )
    segment_memberships = relationship(
        "SubscriberSegmentMembership",
        back_populates="subscriber"
    )
    
    __table_args__ = (
        Index('idx_subscribers_email', 'email'),
        Index('idx_subscribers_status', 'status'),
        Index('idx_subscribers_source', 'source'),
        Index('idx_subscribers_tags', 'tags'),
        Index('idx_subscribers_subscription_date', 'subscription_date'),
    )


class SubscriberSegment(Base, TimestampMixin):
    """Model for subscriber segments"""
    __tablename__ = "subscriber_segments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    segment_type: Mapped[str] = mapped_column(String(30), server_default=text("'manual'"))
    filter_criteria: Mapped[dict] = mapped_column(
        JSONB, 
        server_default=text("'{}'::jsonb")
    )
    subscriber_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    
    # Relationships
    memberships = relationship(
        "SubscriberSegmentMembership",
        back_populates="segment"
    )


class SubscriberSegmentMembership(Base):
    """Model for linking subscribers to segments"""
    __tablename__ = "subscriber_segment_memberships"
    
    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('subscribers.id', ondelete='CASCADE'),
        primary_key=True
    )
    segment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('subscriber_segments.id', ondelete='CASCADE'),
        primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    added_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relationships
    subscriber = relationship("Subscriber", back_populates="segment_memberships")
    segment = relationship("SubscriberSegment", back_populates="memberships")


class SubscriptionPreference(Base, UUIDMixin):
    """Model for subscription preferences and consent"""
    __tablename__ = "subscription_preferences"
    
    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('subscribers.id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )
    newsletter_frequency: Mapped[str] = mapped_column(
        String(20), 
        server_default=text("'weekly'")
    )
    content_types: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        server_default=text("ARRAY['all']")
    )
    preferred_send_time: Mapped[time] = mapped_column(
        Time,
        server_default=text("'09:00:00'")
    )
    preferred_send_days: Mapped[List[int]] = mapped_column(
        ARRAY(Integer),
        server_default=text("ARRAY[1,2,3,4,5]")
    )
    email_format: Mapped[str] = mapped_column(String(10), server_default=text("'html'"))
    double_opt_in: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    marketing_consent: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    analytics_consent: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    third_party_sharing: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    gdpr_consent_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("NOW()"),
        onupdate=text("NOW()")
    )
    
    # Relationships
    subscriber = relationship("Subscriber", back_populates="subscription_preferences")