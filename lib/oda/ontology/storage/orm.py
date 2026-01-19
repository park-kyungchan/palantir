"""
ODA Storage - ORM Base Types
===========================

Some parts of the codebase (e.g. the transaction checkpoint system) expect a
shared SQLAlchemy Declarative Base and a common ORM base class that provides
audit/versioning columns.

The primary schema is defined in `lib.oda.ontology.storage.models`; this module
re-exports the same `Base` to ensure all tables share one metadata registry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from lib.oda.ontology.storage.models import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AsyncOntologyObject(Base):
    """
    Common ORM base for persisted ontology objects.

    This is intentionally minimal and primarily exists to support the
    transaction subsystem's SQLAlchemy models.
    """

    __abstract__ = True

    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


__all__ = ["AsyncOntologyObject", "Base"]

