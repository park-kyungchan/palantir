"""
COW CLI - HITL Review Models

SQLAlchemy models for the Human-in-the-Loop review database.
"""
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    create_engine,
    event,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class ReviewStatus(str, Enum):
    """Review item status."""
    PENDING = "pending"
    CLAIMED = "claimed"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    SKIPPED = "skipped"


class ReviewDecision(str, Enum):
    """Review decision types."""
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    SKIPPED = "skipped"


class AuditAction(str, Enum):
    """Audit log action types."""
    CREATED = "created"
    CLAIMED = "claimed"
    REVIEWED = "reviewed"
    RELEASED = "released"
    PRIORITY_CHANGED = "priority_changed"
    EXPIRED = "expired"


class ReviewItem(Base):
    """
    Review item model.

    Represents an element that requires human review.
    """
    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    element_id: Mapped[str] = mapped_column(String(64), nullable=False)
    element_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Confidence scores
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Review metadata
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ReviewStatus.PENDING.value,
        nullable=False,
    )
    priority: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Review data
    reviewer: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    modifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Original element data (JSON serialized)
    element_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="review_item",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "image_path": self.image_path,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "confidence": self.confidence,
            "confidence_rate": self.confidence_rate,
            "reason": self.reason,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewer": self.reviewer,
            "decision": self.decision,
            "modifications": self.modifications,
            "comment": self.comment,
        }

    @property
    def is_pending(self) -> bool:
        """Check if item is pending."""
        return self.status == ReviewStatus.PENDING.value

    @property
    def is_claimed(self) -> bool:
        """Check if item is claimed."""
        return self.status == ReviewStatus.CLAIMED.value

    @property
    def is_reviewed(self) -> bool:
        """Check if item has been reviewed."""
        return self.status in [
            ReviewStatus.APPROVED.value,
            ReviewStatus.REJECTED.value,
            ReviewStatus.MODIFIED.value,
        ]


class AuditLog(Base):
    """
    Audit log model.

    Tracks all actions on review items.
    """
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
        DateTime,
        default=utc_now,
        nullable=False,
    )

    # Relationships
    review_item: Mapped[Optional["ReviewItem"]] = relationship(
        "ReviewItem",
        back_populates="audit_logs",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "review_item_id": self.review_item_id,
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class ReviewerStats(Base):
    """
    Reviewer statistics model.

    Tracks performance metrics for reviewers.
    """
    __tablename__ = "reviewer_stats"

    reviewer: Mapped[str] = mapped_column(String(64), primary_key=True)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    approved: Mapped[int] = mapped_column(Integer, default=0)
    rejected: Mapped[int] = mapped_column(Integer, default=0)
    modified: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    avg_review_time_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "reviewer": self.reviewer,
            "total_reviews": self.total_reviews,
            "approved": self.approved,
            "rejected": self.rejected,
            "modified": self.modified,
            "skipped": self.skipped,
            "avg_review_time_sec": self.avg_review_time_sec,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "approval_rate": self.approval_rate,
        }

    @property
    def approval_rate(self) -> float:
        """Calculate approval rate."""
        if self.total_reviews == 0:
            return 0.0
        return self.approved / self.total_reviews


__all__ = [
    "Base",
    "ReviewStatus",
    "ReviewDecision",
    "AuditAction",
    "ReviewItem",
    "AuditLog",
    "ReviewerStats",
]
