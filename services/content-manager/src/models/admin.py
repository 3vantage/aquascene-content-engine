"""
Admin user management database models
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey,
    text, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class AdminUser(Base, UUIDMixin, TimestampMixin):
    """Model for admin users"""
    __tablename__ = "admin_users"
    
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30), server_default=text("'editor'"))
    permissions: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    is_superuser: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("NOW()")
    )
    
    # Relationships
    sessions = relationship("AdminSession", back_populates="user")


class AdminSession(Base, UUIDMixin):
    """Model for admin user sessions"""
    __tablename__ = "admin_sessions"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('admin_users.id', ondelete='CASCADE'),
        nullable=False
    )
    session_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"))
    
    # Relationships
    user = relationship("AdminUser", back_populates="sessions")