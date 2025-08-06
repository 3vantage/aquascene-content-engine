"""
Newsletter-related database models
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, 
    ARRAY, text, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class NewsletterIssue(Base, UUIDMixin, TimestampMixin):
    """Model for newsletter issues/campaigns"""
    __tablename__ = "newsletter_issues"
    
    issue_number: Mapped[Optional[int]] = mapped_column(Integer)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_line: Mapped[str] = mapped_column(Text, nullable=False)
    preview_text: Mapped[Optional[str]] = mapped_column(Text)
    content_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), 
        nullable=False
    )
    personalization_data: Mapped[dict] = mapped_column(
        JSONB, 
        server_default=text("'{}'::jsonb")
    )
    design_template: Mapped[Optional[str]] = mapped_column(String(100))
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"))
    recipient_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    metrics: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relationships
    newsletter_metrics = relationship("NewsletterMetric", back_populates="issue")
    
    __table_args__ = (
        Index('idx_newsletter_issues_status', 'status'),
        Index('idx_newsletter_issues_scheduled', 'scheduled_for'),
        Index('idx_newsletter_issues_sent', 'sent_at'),
    )


class NewsletterTemplate(Base, TimestampMixin):
    """Model for newsletter templates"""
    __tablename__ = "newsletter_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    html_template: Mapped[str] = mapped_column(Text, nullable=False)
    text_template: Mapped[Optional[str]] = mapped_column(Text)
    default_subject: Mapped[Optional[str]] = mapped_column(String(255))
    variables: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))