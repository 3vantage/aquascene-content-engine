"""
Audit and logging database models
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class AuditLog(Base, UUIDMixin):
    """Model for audit log tracking changes"""
    __tablename__ = "audit_log"
    
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    __table_args__ = (
        Index('idx_audit_log_table_record', 'table_name', 'record_id'),
        Index('idx_audit_log_changed_by', 'changed_by'),
        Index('idx_audit_log_changed_at', 'changed_at'),
    )


class SystemEvent(Base, UUIDMixin):
    """Model for system event log"""
    __tablename__ = "system_events"
    
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    severity: Mapped[str] = mapped_column(String(20), server_default=text("'info'"))
    service_name: Mapped[Optional[str]] = mapped_column(String(50))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    
    __table_args__ = (
        Index('idx_system_events_type', 'event_type'),
        Index('idx_system_events_occurred', 'occurred_at'),
        Index('idx_system_events_severity', 'severity', 'occurred_at'),
    )