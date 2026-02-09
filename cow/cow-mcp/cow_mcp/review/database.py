"""Async SQLite database for the HITL review queue.

Full async rewrite of cow-cli/review/database.py (CH-1.2).
Uses aiosqlite + SQLAlchemy async engine/session pattern.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager
import json
import uuid
import logging

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from cow_mcp.review.models import (
    Base,
    ReviewItem,
    AuditLog,
    ReviewStatus,
    ReviewDecision,
    AuditAction,
)

logger = logging.getLogger("cow-mcp.review.database")


class AsyncReviewDatabase:
    """Async HITL review database.

    Provides 3 MCP-facing operations: queue_review, get_queue, submit_review.
    Uses aiosqlite backend via SQLAlchemy async engine.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".cow" / "review.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

        self._engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine, expire_on_commit=False
        )

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Initialized review database at {self.db_path}")

    @asynccontextmanager
    async def _session(self):
        """Get an async database session with auto-commit/rollback."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def queue_review(
        self,
        session_id: str,
        items: list[dict],
    ) -> list[dict]:
        """Add verification findings to the review queue.

        Args:
            session_id: Pipeline session ID.
            items: List of review items, each with:
                - element_id: str
                - element_type: str (e.g., 'ocr_correction', 'math_error', 'logic_issue')
                - confidence: Optional[float]
                - reason: Optional[str]
                - priority: Optional[float]
                - original_content: Optional[str] (JSON)

        Returns:
            List of created item dicts with IDs.
        """
        created = []

        async with self._session() as session:
            for item_data in items:
                item_id = str(uuid.uuid4())[:8]

                item = ReviewItem(
                    id=item_id,
                    session_id=session_id,
                    element_id=item_data.get("element_id", ""),
                    element_type=item_data.get("element_type", "unknown"),
                    confidence=item_data.get("confidence"),
                    reason=item_data.get("reason"),
                    priority=item_data.get("priority", 0.0),
                    original_content=item_data.get("original_content"),
                    status=ReviewStatus.PENDING.value,
                )
                session.add(item)

                audit = AuditLog(
                    review_item_id=item_id,
                    action=AuditAction.CREATED.value,
                    details=json.dumps({
                        "element_type": item.element_type,
                        "confidence": item.confidence,
                        "reason": item.reason,
                    }),
                )
                session.add(audit)

                await session.flush()
                created.append(item.to_dict())

            logger.info(f"Queued {len(created)} review items for session {session_id}")

        return created

    async def get_queue(
        self,
        session_id: str,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get review items for a session, optionally filtered by status.

        Args:
            session_id: Pipeline session ID.
            status: Filter by status (pending, claimed, approved, rejected, modified).
            limit: Maximum items to return.

        Returns:
            List of review item dicts.
        """
        async with self._session() as session:
            conditions = [ReviewItem.session_id == session_id]
            if status:
                conditions.append(ReviewItem.status == status)

            query = (
                select(ReviewItem)
                .where(and_(*conditions))
                .order_by(ReviewItem.priority.desc(), ReviewItem.created_at.asc())
                .limit(limit)
            )

            result = await session.execute(query)
            items = list(result.scalars().all())
            return [item.to_dict() for item in items]

    async def submit_review(
        self,
        item_id: str,
        decision: str,
        modified_content: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Optional[dict]:
        """Record a review decision for an item.

        Args:
            item_id: Review item ID.
            decision: One of: approved, rejected, modified, skipped.
            modified_content: Modified content (for 'modified' decisions).
            comment: Optional review comment.

        Returns:
            Updated item dict, or None if not found.
        """
        if decision not in [d.value for d in ReviewDecision]:
            raise ValueError(f"Invalid decision: {decision}. Must be one of: {[d.value for d in ReviewDecision]}")

        async with self._session() as session:
            result = await session.execute(
                select(ReviewItem).where(ReviewItem.id == item_id)
            )
            item = result.scalar_one_or_none()

            if not item:
                return None

            item.status = decision
            item.decision = decision
            item.reviewed_at = datetime.now(timezone.utc)
            item.modified_content = modified_content
            item.comment = comment

            audit = AuditLog(
                review_item_id=item_id,
                action=AuditAction.REVIEWED.value,
                details=json.dumps({
                    "decision": decision,
                    "has_modifications": modified_content is not None,
                }),
            )
            session.add(audit)

            logger.info(f"Item {item_id} reviewed: {decision}")
            return item.to_dict()

    async def get_queue_stats(self, session_id: str) -> dict:
        """Get queue statistics for a session."""
        async with self._session() as session:
            conditions = [ReviewItem.session_id == session_id]

            total = (await session.execute(
                select(func.count(ReviewItem.id)).where(and_(*conditions))
            )).scalar_one()

            pending = (await session.execute(
                select(func.count(ReviewItem.id)).where(
                    and_(*conditions, ReviewItem.status == ReviewStatus.PENDING.value)
                )
            )).scalar_one()

            reviewed = (await session.execute(
                select(func.count(ReviewItem.id)).where(
                    and_(
                        *conditions,
                        ReviewItem.status.in_([
                            ReviewStatus.APPROVED.value,
                            ReviewStatus.REJECTED.value,
                            ReviewStatus.MODIFIED.value,
                        ]),
                    )
                )
            )).scalar_one()

            return {
                "session_id": session_id,
                "total": total,
                "pending": pending,
                "reviewed": reviewed,
            }


# Module-level singleton
_database: Optional[AsyncReviewDatabase] = None


async def get_database(db_path: Optional[Path] = None) -> AsyncReviewDatabase:
    """Get or create the global async database instance."""
    global _database
    if _database is None:
        _database = AsyncReviewDatabase(db_path=db_path)
        await _database.initialize()
    return _database


__all__ = [
    "AsyncReviewDatabase",
    "get_database",
]
