"""
Base model configuration for SQLAlchemy
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class TimestampMixin:
    """Mixin for models that need created_at and updated_at timestamps"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("NOW()"),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
        nullable=False
    )


class UUIDMixin:
    """Mixin for models that use UUID primary keys"""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )