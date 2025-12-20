"""
Orion ODA V3 - Async ORM Foundation
====================================
Implements SQLAlchemy 2.0 Declarative Base with Optimistic Locking.

Design Principles:
1.  **Async First**: Inherits from `AsyncAttrs` to support `await object.awaitable_attrs.relationship`.
2.  **Concurrency Safety**: Enforces `version_id_col` for hardware-level atomic CAS (Compare-And-Swap) logic via SQL WHERE clauses.
3.  **Identity Unifiction**: Replaces the Pydantic-only `OntologyObject` for persistence scenarios, while maintaining compatibility via DTOs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)

def generate_uuid() -> str:
    """Generate UUIDv4 string."""
    return str(uuid.uuid4())

class Base(AsyncAttrs, DeclarativeBase):
    """
    SQLAlchemy 2.0 Async Base Class.
    """
    pass

class AsyncOntologyObject(Base):
    """
    Base Persistence Model for all ODA Objects.
    
    Features:
    - UUIDv4 Primary Key
    - Audit Timestamps (created_at, updated_at)
    - Optimistic Locking (version)
    """
    __abstract__ = True
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String, 
        primary_key=True, 
        default=generate_uuid
    )
    
    # Optimistic Locking
    # SQLAlchemy will automatically check 'version' on UPDATE
    # and raise StaleDataError if it doesn't match.
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=utc_now, 
        onupdate=utc_now, 
        nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Object Status (as String enum for storage simplicity)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)

    __mapper_args__ = {
        "version_id_col": version
    }
    
    def touch(self):
        """
        Manually trigger update timestamp.
        Note: version increment is handled automatically by SQLAlchemy.
        """
        self.updated_at = utc_now()
