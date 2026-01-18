"""
ReviewQueueManager for Human Review system.

Manages the review task queue with:
- Task enqueueing with priority
- Fair task distribution
- Stale task detection and reassignment
- Queue statistics

Module Version: 1.0.0
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field

from ..schemas.common import MathpixBaseModel, PipelineStage

from .models.task import (
    ReviewTask,
    ReviewStatus,
    ReviewPriority,
    ReviewDecision,
)
from .models.reviewer import Reviewer
from .exceptions import QueueError, TaskNotFoundError
from .priority_scorer import PriorityScorer, PriorityScorerConfig


logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class QueueConfig:
    """Configuration for ReviewQueueManager."""
    # Storage
    db_path: Optional[Path] = None
    use_memory_store: bool = True

    # Queue settings
    default_queue_name: str = "default"
    max_queue_size: int = 10000

    # Task lifecycle
    task_expiry_hours: int = 48
    stale_threshold_hours: int = 24
    max_assignment_attempts: int = 3

    # Processing
    batch_size: int = 100
    enable_auto_reassign: bool = True
    enable_priority_scoring: bool = True


# =============================================================================
# Queue Statistics
# =============================================================================

class QueueStats(MathpixBaseModel):
    """Statistics for a review queue."""
    queue_name: str
    total_tasks: int = 0
    pending_tasks: int = 0
    assigned_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    expired_tasks: int = 0

    # Priority distribution
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Time metrics
    avg_wait_time_ms: float = 0.0
    avg_review_time_ms: float = 0.0
    oldest_pending_age_ms: float = 0.0

    # Throughput
    tasks_per_hour: float = 0.0
    tasks_per_day: float = 0.0

    # Health
    stale_task_count: int = 0
    error_count: int = 0

    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# ReviewQueueManager
# =============================================================================

class ReviewQueueManager:
    """Manages the human review task queue.

    Provides:
    - Enqueueing tasks with automatic priority scoring
    - Dequeueing tasks for reviewers (with fair distribution)
    - Task lifecycle management
    - Stale task detection and reassignment
    - Queue statistics and monitoring

    Usage:
        config = QueueConfig()
        manager = ReviewQueueManager(config)

        # Enqueue a task
        task_id = await manager.enqueue(task)

        # Dequeue for a reviewer
        task = await manager.dequeue("reviewer-123")

        # Get stats
        stats = await manager.get_queue_stats()
    """

    def __init__(
        self,
        config: Optional[QueueConfig] = None,
    ):
        """Initialize queue manager.

        Args:
            config: Queue configuration
        """
        self.config = config or QueueConfig()

        # In-memory storage (for demo; use proper DB in production)
        self._tasks: Dict[str, ReviewTask] = {}
        self._queues: Dict[str, List[str]] = {self.config.default_queue_name: []}

        # Priority scorer
        self._priority_scorer = PriorityScorer(PriorityScorerConfig())

        # Statistics
        self._stats_cache: Dict[str, QueueStats] = {}
        self._error_count = 0

        # Locks for thread safety
        self._lock = asyncio.Lock()

        logger.info(f"ReviewQueueManager initialized with config: {self.config}")

    # =========================================================================
    # Enqueue Operations
    # =========================================================================

    async def enqueue(
        self,
        task: ReviewTask,
        queue_name: Optional[str] = None,
    ) -> str:
        """Enqueue a task for review.

        Args:
            task: ReviewTask to enqueue
            queue_name: Optional queue name (uses default if not specified)

        Returns:
            Task ID

        Raises:
            QueueError: If queue is full or other error
        """
        async with self._lock:
            queue = queue_name or self.config.default_queue_name

            # Ensure queue exists
            if queue not in self._queues:
                self._queues[queue] = []

            # Check queue size
            if len(self._queues[queue]) >= self.config.max_queue_size:
                raise QueueError(
                    message=f"Queue {queue} is full",
                    queue_name=queue,
                    operation="enqueue",
                )

            # Apply priority scoring if enabled
            if self.config.enable_priority_scoring:
                scored_priority = self._priority_scorer.score(task)
                task.priority = scored_priority

            # Set task metadata
            task.assigned_queue = queue
            task.status = ReviewStatus.PENDING

            # Store task
            self._tasks[task.task_id] = task

            # Add to queue in priority order
            self._insert_by_priority(queue, task.task_id)

            logger.info(
                f"Task {task.task_id} enqueued to {queue} "
                f"with priority {task.priority.value}"
            )

            return task.task_id

    def _insert_by_priority(self, queue_name: str, task_id: str) -> None:
        """Insert task ID into queue maintaining priority order."""
        queue = self._queues[queue_name]
        task = self._tasks[task_id]

        # Priority order: CRITICAL > HIGH > MEDIUM > LOW
        priority_order = {
            ReviewPriority.CRITICAL: 0,
            ReviewPriority.HIGH: 1,
            ReviewPriority.MEDIUM: 2,
            ReviewPriority.LOW: 3,
        }

        task_priority = priority_order.get(task.priority, 2)

        # Find insertion point
        for i, existing_id in enumerate(queue):
            existing_task = self._tasks.get(existing_id)
            if existing_task:
                existing_priority = priority_order.get(existing_task.priority, 2)
                if task_priority < existing_priority:
                    queue.insert(i, task_id)
                    return

        # Append at end
        queue.append(task_id)

    async def enqueue_batch(
        self,
        tasks: List[ReviewTask],
        queue_name: Optional[str] = None,
    ) -> List[str]:
        """Enqueue multiple tasks.

        Args:
            tasks: List of tasks to enqueue
            queue_name: Optional queue name

        Returns:
            List of task IDs
        """
        task_ids = []
        for task in tasks:
            task_id = await self.enqueue(task, queue_name)
            task_ids.append(task_id)
        return task_ids

    # =========================================================================
    # Dequeue Operations
    # =========================================================================

    async def dequeue(
        self,
        reviewer_id: str,
        queue_name: Optional[str] = None,
        stage_filter: Optional[PipelineStage] = None,
    ) -> Optional[ReviewTask]:
        """Dequeue a task for a reviewer.

        Args:
            reviewer_id: ID of the reviewer
            queue_name: Optional queue name
            stage_filter: Optional filter by pipeline stage

        Returns:
            ReviewTask or None if queue is empty
        """
        async with self._lock:
            queue = queue_name or self.config.default_queue_name

            if queue not in self._queues:
                return None

            # Find first suitable task
            for task_id in list(self._queues[queue]):
                task = self._tasks.get(task_id)
                if not task:
                    # Clean up orphaned reference
                    self._queues[queue].remove(task_id)
                    continue

                if task.status != ReviewStatus.PENDING:
                    continue

                # Apply stage filter if specified
                if stage_filter and task.context.pipeline_stage != stage_filter:
                    continue

                # Assign task
                self._queues[queue].remove(task_id)
                task.assign(reviewer_id)
                self._tasks[task_id] = task

                logger.info(f"Task {task_id} dequeued for reviewer {reviewer_id}")
                return task

            return None

    async def peek(
        self,
        queue_name: Optional[str] = None,
        count: int = 1,
    ) -> List[ReviewTask]:
        """Peek at tasks without removing them.

        Args:
            queue_name: Optional queue name
            count: Number of tasks to peek

        Returns:
            List of tasks (up to count)
        """
        queue = queue_name or self.config.default_queue_name

        if queue not in self._queues:
            return []

        tasks = []
        for task_id in self._queues[queue][:count]:
            task = self._tasks.get(task_id)
            if task:
                tasks.append(task)

        return tasks

    # =========================================================================
    # Task Management
    # =========================================================================

    async def get_task(self, task_id: str) -> Optional[ReviewTask]:
        """Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            ReviewTask or None
        """
        return self._tasks.get(task_id)

    async def update_task(self, task: ReviewTask) -> None:
        """Update a task.

        Args:
            task: Updated task
        """
        async with self._lock:
            if task.task_id not in self._tasks:
                raise TaskNotFoundError(
                    message=f"Task not found: {task.task_id}",
                    task_id=task.task_id,
                )
            self._tasks[task.task_id] = task

    async def complete_task(
        self,
        task_id: str,
        decision: ReviewDecision,
        reason: Optional[str] = None,
    ) -> ReviewTask:
        """Mark a task as completed.

        Args:
            task_id: Task identifier
            decision: Review decision
            reason: Optional reason for decision

        Returns:
            Updated task
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise TaskNotFoundError(
                    message=f"Task not found: {task_id}",
                    task_id=task_id,
                )

            task.complete(decision, reason)
            self._tasks[task_id] = task

            logger.info(
                f"Task {task_id} completed with decision {decision.value}"
            )

            return task

    async def escalate_task(
        self,
        task_id: str,
        reason: str,
    ) -> ReviewTask:
        """Escalate a task.

        Args:
            task_id: Task identifier
            reason: Reason for escalation

        Returns:
            Updated task
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise TaskNotFoundError(
                    message=f"Task not found: {task_id}",
                    task_id=task_id,
                )

            task.escalate(reason)

            # Re-enqueue with higher priority
            task.priority = ReviewPriority.HIGH
            queue = task.assigned_queue or self.config.default_queue_name
            self._insert_by_priority(queue, task_id)

            self._tasks[task_id] = task

            logger.info(f"Task {task_id} escalated: {reason}")

            return task

    # =========================================================================
    # Stale Task Management
    # =========================================================================

    async def reassign_stale_tasks(
        self,
        timeout_hours: Optional[int] = None,
    ) -> int:
        """Reassign tasks that have been stale for too long.

        Args:
            timeout_hours: Hours before task is considered stale

        Returns:
            Number of tasks reassigned
        """
        if not self.config.enable_auto_reassign:
            return 0

        timeout = timeout_hours or self.config.stale_threshold_hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=timeout)

        reassigned = 0

        async with self._lock:
            for task_id, task in list(self._tasks.items()):
                if task.status not in (ReviewStatus.ASSIGNED, ReviewStatus.IN_PROGRESS):
                    continue

                # Check if stale
                if task.metrics.assigned_at and task.metrics.assigned_at < cutoff:
                    # Check max attempts
                    if task.metrics.assignment_count >= self.config.max_assignment_attempts:
                        task.expire()
                        logger.warning(
                            f"Task {task_id} expired after "
                            f"{task.metrics.assignment_count} attempts"
                        )
                    else:
                        # Reassign
                        task.status = ReviewStatus.PENDING
                        task.assigned_to = None
                        queue = task.assigned_queue or self.config.default_queue_name
                        self._insert_by_priority(queue, task_id)
                        reassigned += 1
                        logger.info(
                            f"Task {task_id} reassigned (attempt "
                            f"{task.metrics.assignment_count})"
                        )

                    self._tasks[task_id] = task

        return reassigned

    async def expire_old_tasks(
        self,
        expiry_hours: Optional[int] = None,
    ) -> int:
        """Expire tasks that are too old.

        Args:
            expiry_hours: Hours before task expires

        Returns:
            Number of tasks expired
        """
        expiry = expiry_hours or self.config.task_expiry_hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=expiry)

        expired_count = 0

        async with self._lock:
            for task_id, task in list(self._tasks.items()):
                if task.status in (ReviewStatus.COMPLETED, ReviewStatus.EXPIRED):
                    continue

                if task.created_at < cutoff:
                    task.expire()
                    self._tasks[task_id] = task

                    # Remove from queue if present
                    queue = task.assigned_queue or self.config.default_queue_name
                    if queue in self._queues and task_id in self._queues[queue]:
                        self._queues[queue].remove(task_id)

                    expired_count += 1
                    logger.info(f"Task {task_id} expired due to age")

        return expired_count

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_queue_stats(
        self,
        queue_name: Optional[str] = None,
    ) -> QueueStats:
        """Get statistics for a queue.

        Args:
            queue_name: Optional queue name

        Returns:
            QueueStats
        """
        queue = queue_name or self.config.default_queue_name

        stats = QueueStats(queue_name=queue)

        # Count by status
        now = datetime.now(timezone.utc)
        oldest_pending_time: Optional[datetime] = None
        total_wait_time_ms = 0.0
        total_review_time_ms = 0.0
        wait_count = 0
        review_count = 0

        for task_id, task in self._tasks.items():
            if task.assigned_queue != queue:
                continue

            stats.total_tasks += 1

            # Status counts
            if task.status == ReviewStatus.PENDING:
                stats.pending_tasks += 1
                if oldest_pending_time is None or task.created_at < oldest_pending_time:
                    oldest_pending_time = task.created_at
            elif task.status == ReviewStatus.ASSIGNED:
                stats.assigned_tasks += 1
            elif task.status == ReviewStatus.IN_PROGRESS:
                stats.in_progress_tasks += 1
            elif task.status == ReviewStatus.COMPLETED:
                stats.completed_tasks += 1
            elif task.status == ReviewStatus.EXPIRED:
                stats.expired_tasks += 1

            # Priority counts
            if task.priority == ReviewPriority.CRITICAL:
                stats.critical_count += 1
            elif task.priority == ReviewPriority.HIGH:
                stats.high_count += 1
            elif task.priority == ReviewPriority.MEDIUM:
                stats.medium_count += 1
            elif task.priority == ReviewPriority.LOW:
                stats.low_count += 1

            # Time metrics
            if task.metrics.queue_time_ms:
                total_wait_time_ms += task.metrics.queue_time_ms
                wait_count += 1
            if task.metrics.review_time_ms:
                total_review_time_ms += task.metrics.review_time_ms
                review_count += 1

        # Calculate averages
        if wait_count > 0:
            stats.avg_wait_time_ms = total_wait_time_ms / wait_count
        if review_count > 0:
            stats.avg_review_time_ms = total_review_time_ms / review_count

        # Oldest pending
        if oldest_pending_time:
            stats.oldest_pending_age_ms = (now - oldest_pending_time).total_seconds() * 1000

        # Stale count
        stale_cutoff = now - timedelta(hours=self.config.stale_threshold_hours)
        stats.stale_task_count = sum(
            1 for t in self._tasks.values()
            if t.assigned_queue == queue
            and t.status in (ReviewStatus.ASSIGNED, ReviewStatus.IN_PROGRESS)
            and t.metrics.assigned_at
            and t.metrics.assigned_at < stale_cutoff
        )

        stats.error_count = self._error_count
        stats.last_updated = now

        return stats

    async def get_all_queue_stats(self) -> Dict[str, QueueStats]:
        """Get statistics for all queues.

        Returns:
            Dict mapping queue names to stats
        """
        stats = {}
        for queue_name in self._queues.keys():
            stats[queue_name] = await self.get_queue_stats(queue_name)
        return stats

    # =========================================================================
    # Queue Management
    # =========================================================================

    async def create_queue(self, queue_name: str) -> bool:
        """Create a new queue.

        Args:
            queue_name: Name for the new queue

        Returns:
            True if created, False if already exists
        """
        if queue_name in self._queues:
            return False
        self._queues[queue_name] = []
        logger.info(f"Created queue: {queue_name}")
        return True

    async def delete_queue(
        self,
        queue_name: str,
        force: bool = False,
    ) -> bool:
        """Delete a queue.

        Args:
            queue_name: Queue to delete
            force: Delete even if not empty

        Returns:
            True if deleted
        """
        if queue_name not in self._queues:
            return False

        if queue_name == self.config.default_queue_name:
            raise QueueError(
                message="Cannot delete default queue",
                queue_name=queue_name,
                operation="delete",
            )

        if not force and self._queues[queue_name]:
            raise QueueError(
                message="Queue not empty",
                queue_name=queue_name,
                operation="delete",
            )

        del self._queues[queue_name]
        logger.info(f"Deleted queue: {queue_name}")
        return True

    async def list_queues(self) -> List[str]:
        """List all queue names.

        Returns:
            List of queue names
        """
        return list(self._queues.keys())


# =============================================================================
# Factory Function
# =============================================================================

def create_queue_manager(
    config: Optional[QueueConfig] = None,
) -> ReviewQueueManager:
    """Create a ReviewQueueManager instance.

    Args:
        config: Optional configuration

    Returns:
        ReviewQueueManager instance
    """
    return ReviewQueueManager(config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "QueueConfig",
    "QueueStats",
    "ReviewQueueManager",
    "create_queue_manager",
]
