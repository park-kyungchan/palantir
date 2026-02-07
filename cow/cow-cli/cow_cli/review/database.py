"""
COW CLI - HITL Review Database

Database operations for the Human-in-the-Loop review system.
"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import contextmanager
import json
import uuid
import logging

from sqlalchemy import create_engine, select, update, delete, func, and_, or_, text
from sqlalchemy.orm import Session, sessionmaker

from cow_cli.review.models import (
    Base,
    ReviewItem,
    AuditLog,
    ReviewerStats,
    ReviewStatus,
    ReviewDecision,
    AuditAction,
)

logger = logging.getLogger("cow-cli.review.database")


class ReviewDatabase:
    """
    HITL Review Database Manager.

    Provides CRUD operations for review items, audit logs, and reviewer stats.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        echo: bool = False,
    ):
        """
        Initialize the database.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/.cow/review.db
            echo: Enable SQL logging
        """
        if db_path is None:
            db_path = Path.home() / ".cow" / "review.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        # Create tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Initialized review database at {db_path}")

    @contextmanager
    def session(self) -> Session:
        """Get a database session."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # =========================================================================
    # Review Item Operations
    # =========================================================================

    def add_review_item(
        self,
        image_path: str,
        element_id: str,
        element_type: str,
        confidence: Optional[float] = None,
        confidence_rate: Optional[float] = None,
        reason: Optional[str] = None,
        priority: float = 0.0,
        element_data: Optional[dict] = None,
        reviewer: Optional[str] = None,
    ) -> ReviewItem:
        """
        Add a new review item.

        Args:
            image_path: Path to the source image
            element_id: Unique element identifier
            element_type: Type of element (e.g., 'equation', 'diagram')
            confidence: OCR confidence score (0-1)
            confidence_rate: Confidence rate from quality assessment
            reason: Reason for requiring review
            priority: Priority score (higher = more urgent)
            element_data: Original element data (dict)
            reviewer: Pre-assign to a reviewer

        Returns:
            Created ReviewItem
        """
        item_id = str(uuid.uuid4())[:8]

        with self.session() as session:
            item = ReviewItem(
                id=item_id,
                image_path=image_path,
                element_id=element_id,
                element_type=element_type,
                confidence=confidence,
                confidence_rate=confidence_rate,
                reason=reason,
                priority=priority,
                element_data=json.dumps(element_data) if element_data else None,
                reviewer=reviewer,
                status=ReviewStatus.CLAIMED.value if reviewer else ReviewStatus.PENDING.value,
                claimed_at=datetime.now(timezone.utc) if reviewer else None,
            )
            session.add(item)

            # Add audit log
            audit = AuditLog(
                review_item_id=item_id,
                action=AuditAction.CREATED.value,
                details=json.dumps({
                    "element_type": element_type,
                    "confidence": confidence,
                    "reason": reason,
                }),
            )
            session.add(audit)

            session.flush()
            logger.info(f"Added review item: {item_id}")

            return item

    def get_review_item(self, item_id: str) -> Optional[ReviewItem]:
        """Get a review item by ID."""
        with self.session() as session:
            result = session.execute(
                select(ReviewItem).where(ReviewItem.id == item_id)
            )
            return result.scalar_one_or_none()

    def list_review_items(
        self,
        status: Optional[str] = None,
        element_type: Optional[str] = None,
        reviewer: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by_priority: bool = True,
    ) -> List[ReviewItem]:
        """
        List review items with filters.

        Args:
            status: Filter by status
            element_type: Filter by element type
            reviewer: Filter by reviewer
            limit: Maximum items to return
            offset: Pagination offset
            order_by_priority: Order by priority descending

        Returns:
            List of ReviewItem
        """
        with self.session() as session:
            query = select(ReviewItem)

            conditions = []
            if status:
                conditions.append(ReviewItem.status == status)
            if element_type:
                conditions.append(ReviewItem.element_type == element_type)
            if reviewer:
                conditions.append(ReviewItem.reviewer == reviewer)

            if conditions:
                query = query.where(and_(*conditions))

            if order_by_priority:
                query = query.order_by(ReviewItem.priority.desc(), ReviewItem.created_at.asc())
            else:
                query = query.order_by(ReviewItem.created_at.asc())

            query = query.limit(limit).offset(offset)

            result = session.execute(query)
            return list(result.scalars().all())

    def get_pending_items(
        self,
        limit: int = 10,
        element_type: Optional[str] = None,
    ) -> List[ReviewItem]:
        """Get pending items for review."""
        return self.list_review_items(
            status=ReviewStatus.PENDING.value,
            element_type=element_type,
            limit=limit,
        )

    def claim_item(
        self,
        item_id: str,
        reviewer: str,
    ) -> Optional[ReviewItem]:
        """
        Claim a review item.

        Args:
            item_id: Item ID to claim
            reviewer: Reviewer name

        Returns:
            Updated ReviewItem or None if not found/already claimed
        """
        with self.session() as session:
            result = session.execute(
                select(ReviewItem).where(
                    and_(
                        ReviewItem.id == item_id,
                        ReviewItem.status == ReviewStatus.PENDING.value,
                    )
                )
            )
            item = result.scalar_one_or_none()

            if not item:
                return None

            item.status = ReviewStatus.CLAIMED.value
            item.reviewer = reviewer
            item.claimed_at = datetime.now(timezone.utc)

            # Audit log
            audit = AuditLog(
                review_item_id=item_id,
                action=AuditAction.CLAIMED.value,
                actor=reviewer,
            )
            session.add(audit)

            logger.info(f"Item {item_id} claimed by {reviewer}")
            return item

    def release_item(self, item_id: str) -> Optional[ReviewItem]:
        """Release a claimed item back to pending."""
        with self.session() as session:
            result = session.execute(
                select(ReviewItem).where(
                    and_(
                        ReviewItem.id == item_id,
                        ReviewItem.status == ReviewStatus.CLAIMED.value,
                    )
                )
            )
            item = result.scalar_one_or_none()

            if not item:
                return None

            old_reviewer = item.reviewer
            item.status = ReviewStatus.PENDING.value
            item.reviewer = None
            item.claimed_at = None

            # Audit log
            audit = AuditLog(
                review_item_id=item_id,
                action=AuditAction.RELEASED.value,
                actor=old_reviewer,
            )
            session.add(audit)

            logger.info(f"Item {item_id} released")
            return item

    def submit_review(
        self,
        item_id: str,
        decision: str,
        reviewer: str,
        modifications: Optional[dict] = None,
        comment: Optional[str] = None,
    ) -> Optional[ReviewItem]:
        """
        Submit a review decision.

        Args:
            item_id: Item ID
            decision: Decision (approved, rejected, modified, skipped)
            reviewer: Reviewer name
            modifications: Modified element data (for 'modified' decision)
            comment: Review comment

        Returns:
            Updated ReviewItem or None
        """
        with self.session() as session:
            result = session.execute(
                select(ReviewItem).where(ReviewItem.id == item_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                return None

            # Update item
            item.status = decision
            item.decision = decision
            item.reviewer = reviewer
            item.reviewed_at = datetime.now(timezone.utc)
            item.modifications = json.dumps(modifications) if modifications else None
            item.comment = comment

            # Audit log
            audit = AuditLog(
                review_item_id=item_id,
                action=AuditAction.REVIEWED.value,
                actor=reviewer,
                details=json.dumps({
                    "decision": decision,
                    "has_modifications": modifications is not None,
                }),
            )
            session.add(audit)

            # Update reviewer stats
            self._update_reviewer_stats(session, reviewer, decision, item.claimed_at)

            logger.info(f"Item {item_id} reviewed: {decision}")
            return item

    def update_priority(
        self,
        item_id: str,
        new_priority: float,
        actor: Optional[str] = None,
    ) -> Optional[ReviewItem]:
        """Update item priority."""
        with self.session() as session:
            result = session.execute(
                select(ReviewItem).where(ReviewItem.id == item_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                return None

            old_priority = item.priority
            item.priority = new_priority

            audit = AuditLog(
                review_item_id=item_id,
                action=AuditAction.PRIORITY_CHANGED.value,
                actor=actor,
                details=json.dumps({
                    "old_priority": old_priority,
                    "new_priority": new_priority,
                }),
            )
            session.add(audit)

            return item

    def delete_item(self, item_id: str) -> bool:
        """Delete a review item."""
        with self.session() as session:
            result = session.execute(
                delete(ReviewItem).where(ReviewItem.id == item_id)
            )
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted review item: {item_id}")
            return deleted

    # =========================================================================
    # Statistics & Metrics
    # =========================================================================

    def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        with self.session() as session:
            total = session.execute(
                select(func.count(ReviewItem.id))
            ).scalar_one()

            pending = session.execute(
                select(func.count(ReviewItem.id)).where(
                    ReviewItem.status == ReviewStatus.PENDING.value
                )
            ).scalar_one()

            claimed = session.execute(
                select(func.count(ReviewItem.id)).where(
                    ReviewItem.status == ReviewStatus.CLAIMED.value
                )
            ).scalar_one()

            approved = session.execute(
                select(func.count(ReviewItem.id)).where(
                    ReviewItem.status == ReviewStatus.APPROVED.value
                )
            ).scalar_one()

            rejected = session.execute(
                select(func.count(ReviewItem.id)).where(
                    ReviewItem.status == ReviewStatus.REJECTED.value
                )
            ).scalar_one()

            modified = session.execute(
                select(func.count(ReviewItem.id)).where(
                    ReviewItem.status == ReviewStatus.MODIFIED.value
                )
            ).scalar_one()

            avg_confidence = session.execute(
                select(func.avg(ReviewItem.confidence)).where(
                    ReviewItem.status == ReviewStatus.PENDING.value
                )
            ).scalar_one()

            return {
                "total": total,
                "pending": pending,
                "claimed": claimed,
                "reviewed": approved + rejected + modified,
                "approved": approved,
                "rejected": rejected,
                "modified": modified,
                "avg_pending_confidence": avg_confidence,
            }

    def get_reviewer_stats(self, reviewer: str) -> Optional[ReviewerStats]:
        """Get stats for a specific reviewer."""
        with self.session() as session:
            result = session.execute(
                select(ReviewerStats).where(ReviewerStats.reviewer == reviewer)
            )
            return result.scalar_one_or_none()

    def get_all_reviewer_stats(self) -> List[ReviewerStats]:
        """Get stats for all reviewers."""
        with self.session() as session:
            result = session.execute(
                select(ReviewerStats).order_by(ReviewerStats.total_reviews.desc())
            )
            return list(result.scalars().all())

    def _update_reviewer_stats(
        self,
        session: Session,
        reviewer: str,
        decision: str,
        claimed_at: Optional[datetime],
    ) -> None:
        """Update reviewer statistics after a review."""
        result = session.execute(
            select(ReviewerStats).where(ReviewerStats.reviewer == reviewer)
        )
        stats = result.scalar_one_or_none()

        if not stats:
            stats = ReviewerStats(
                reviewer=reviewer,
                total_reviews=0,
                approved=0,
                rejected=0,
                modified=0,
                skipped=0,
            )
            session.add(stats)

        stats.total_reviews += 1
        stats.last_active = datetime.now(timezone.utc)

        if decision == ReviewDecision.APPROVED.value:
            stats.approved += 1
        elif decision == ReviewDecision.REJECTED.value:
            stats.rejected += 1
        elif decision == ReviewDecision.MODIFIED.value:
            stats.modified += 1
        elif decision == ReviewDecision.SKIPPED.value:
            stats.skipped += 1

        # Calculate review time if claimed_at is available
        if claimed_at:
            # Make claimed_at timezone-aware if it's naive (SQLite stores naive datetimes)
            if claimed_at.tzinfo is None:
                claimed_at = claimed_at.replace(tzinfo=timezone.utc)
            review_time = (datetime.now(timezone.utc) - claimed_at).total_seconds()
            if stats.avg_review_time_sec is None:
                stats.avg_review_time_sec = review_time
            else:
                # Rolling average
                stats.avg_review_time_sec = (
                    stats.avg_review_time_sec * (stats.total_reviews - 1) + review_time
                ) / stats.total_reviews

    # =========================================================================
    # Audit Logs
    # =========================================================================

    def get_audit_logs(
        self,
        item_id: Optional[str] = None,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs with filters."""
        with self.session() as session:
            query = select(AuditLog)

            conditions = []
            if item_id:
                conditions.append(AuditLog.review_item_id == item_id)
            if action:
                conditions.append(AuditLog.action == action)
            if actor:
                conditions.append(AuditLog.actor == actor)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

            result = session.execute(query)
            return list(result.scalars().all())

    # =========================================================================
    # Maintenance
    # =========================================================================

    def expire_stale_claims(
        self,
        max_age_minutes: int = 60,
    ) -> int:
        """
        Release items that have been claimed for too long.

        Args:
            max_age_minutes: Maximum claim age before expiration

        Returns:
            Number of items released
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)

        with self.session() as session:
            result = session.execute(
                select(ReviewItem).where(
                    and_(
                        ReviewItem.status == ReviewStatus.CLAIMED.value,
                        ReviewItem.claimed_at < cutoff,
                    )
                )
            )
            stale_items = list(result.scalars().all())

            for item in stale_items:
                item.status = ReviewStatus.PENDING.value
                item.reviewer = None
                item.claimed_at = None

                audit = AuditLog(
                    review_item_id=item.id,
                    action=AuditAction.EXPIRED.value,
                    details=json.dumps({"max_age_minutes": max_age_minutes}),
                )
                session.add(audit)

            logger.info(f"Expired {len(stale_items)} stale claims")
            return len(stale_items)

    def vacuum(self) -> None:
        """Optimize the database."""
        with self.session() as session:
            session.execute(text("VACUUM"))
        logger.info("Database vacuumed")


# Global database instance
_database: Optional[ReviewDatabase] = None


def get_database(db_path: Optional[Path] = None) -> ReviewDatabase:
    """Get or create the global database instance."""
    global _database
    if _database is None:
        _database = ReviewDatabase(db_path=db_path)
    return _database


def configure_database(db_path: Path, echo: bool = False) -> ReviewDatabase:
    """Configure the global database instance."""
    global _database
    _database = ReviewDatabase(db_path=db_path, echo=echo)
    return _database


__all__ = [
    "ReviewDatabase",
    "get_database",
    "configure_database",
]
