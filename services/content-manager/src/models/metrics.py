"""
Analytics and metrics database models
"""
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, Integer, DateTime, Date, DECIMAL,
    ForeignKey, text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin


class ContentMetric(Base, UUIDMixin):
    """Model for content performance metrics"""
    __tablename__ = "content_metrics"
    
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('generated_content.id', ondelete='CASCADE'),
        nullable=False
    )
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    metric_data: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    date_bucket: Mapped[date] = mapped_column(
        Date,
        server_default=text("CURRENT_DATE")
    )
    
    # Relationships
    content = relationship("GeneratedContent", back_populates="metrics")
    
    __table_args__ = (
        UniqueConstraint(
            'content_id', 'metric_type', 'metric_name', 'date_bucket',
            name='uq_content_metric'
        ),
        Index('idx_content_metrics_content_date', 'content_id', 'date_bucket'),
        Index('idx_content_metrics_type', 'metric_type', 'date_bucket'),
    )


class NewsletterMetric(Base, UUIDMixin):
    """Model for newsletter campaign metrics"""
    __tablename__ = "newsletter_metrics"
    
    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('newsletter_issues.id', ondelete='CASCADE'),
        nullable=False
    )
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    delivered_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    open_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    click_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    unsubscribe_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    bounce_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    complaint_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    unique_opens: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    unique_clicks: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    open_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4))
    click_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4))
    unsubscribe_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4))
    bounce_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    
    # Relationships
    issue = relationship("NewsletterIssue", back_populates="newsletter_metrics")
    
    __table_args__ = (
        Index('idx_newsletter_metrics_issue', 'issue_id'),
    )


class SystemMetric(Base, UUIDMixin):
    """Model for system analytics and monitoring"""
    __tablename__ = "system_metrics"
    
    service_name: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    metric_unit: Mapped[Optional[str]] = mapped_column(String(20))
    tags: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    date_bucket: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("DATE_TRUNC('minute', NOW())")
    )
    
    __table_args__ = (
        Index('idx_system_metrics_service_date', 'service_name', 'date_bucket'),
    )