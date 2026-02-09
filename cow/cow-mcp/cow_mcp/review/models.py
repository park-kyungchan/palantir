"""SQLAlchemy ORM models for the HITL review database.

Adapted from cow-cli/review/models.py. Same table schema, updated imports.
"""

from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from sqlalchemy import (
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReviewStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    SKIPPED = "skipped"


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    SKIPPED = "skipped"


class AuditAction(str, Enum):
    CREATED = "created"
    CLAIMED = "claimed"
    REVIEWED = "reviewed"
    RELEASED = "released"
    PRIORITY_CHANGED = "priority_changed"
    EXPIRED = "expired"


class ReviewItem(Base):
    """Review item — an element requiring human review."""

    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    element_id: Mapped[str] = mapped_column(String(64), nullable=False)
    element_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Confidence scores
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Review metadata
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=ReviewStatus.PENDING.value, nullable=False
    )
    priority: Mapped[float] = mapped_column(Float, default=0.0)

    # Original content (JSON serialized)
    original_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Review decision data
    reviewer: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    modified_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="review_item", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "confidence": self.confidence,
            "reason": self.reason,
            "status": self.status,
            "priority": self.priority,
            "original_content": self.original_content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewer": self.reviewer,
            "decision": self.decision,
            "modified_content": self.modified_content,
            "comment": self.comment,
        }

    @property
    def is_pending(self) -> bool:
        return self.status == ReviewStatus.PENDING.value

    @property
    def is_reviewed(self) -> bool:
        return self.status in [
            ReviewStatus.APPROVED.value,
            ReviewStatus.REJECTED.value,
            ReviewStatus.MODIFIED.value,
        ]


class AuditLog(Base):
    """Audit log — tracks all actions on review items."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_item_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("review_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )

    review_item: Mapped[Optional["ReviewItem"]] = relationship(
        "ReviewItem", back_populates="audit_logs"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "review_item_id": self.review_item_id,
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


__all__ = [
    "Base",
    "ReviewStatus",
    "ReviewDecision",
    "AuditAction",
    "ReviewItem",
    "AuditLog",
]
