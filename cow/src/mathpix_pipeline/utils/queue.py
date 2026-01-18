"""
Async Processing Queue for Batch Operations.

Provides a high-performance async job queue with:
- Priority queue support for job ordering
- Concurrent worker management
- Job status tracking and error handling
- Graceful shutdown and cancellation

Schema Version: 2.0.0
Module Version: 1.0.0

Usage:
    from mathpix_pipeline.utils.queue import ProcessingQueue, Job

    async def process_item(payload: dict) -> dict:
        # Processing logic
        return {"result": payload["id"]}

    queue = ProcessingQueue(max_workers=4)

    # Enqueue jobs
    job1 = await queue.enqueue({"id": 1}, priority=1)
    job2 = await queue.enqueue({"id": 2}, priority=0)  # Higher priority

    # Process all jobs
    results = await queue.process_all(process_item)

    # Check status
    print(f"Completed: {queue.completed_count}")
    print(f"Failed: {queue.failed_count}")
"""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Generic, List, Optional, TypeVar
from uuid import uuid4


logger = logging.getLogger(__name__)


# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")  # Payload type
R = TypeVar("R")  # Result type


# =============================================================================
# Job Status Enum
# =============================================================================

class JobStatus(Enum):
    """Status of a job in the processing queue.

    Lifecycle:
        PENDING -> RUNNING -> COMPLETED
                          -> FAILED
                -> CANCELLED
    """

    PENDING = "pending"
    """Job is waiting in the queue."""

    RUNNING = "running"
    """Job is currently being processed."""

    COMPLETED = "completed"
    """Job has been successfully processed."""

    FAILED = "failed"
    """Job processing failed with an error."""

    CANCELLED = "cancelled"
    """Job was cancelled before processing."""


# =============================================================================
# Job Dataclass
# =============================================================================

@dataclass
class Job(Generic[T, R]):
    """Represents a job in the processing queue.

    Attributes:
        id: Unique job identifier (auto-generated if not provided).
        payload: The data to be processed.
        status: Current job status.
        priority: Job priority (lower = higher priority, default 10).
        result: Processing result (set after completion).
        error: Error message if job failed.
        error_traceback: Full traceback if job failed.
        created_at: Timestamp when job was created.
        started_at: Timestamp when job started processing.
        completed_at: Timestamp when job finished (success or failure).
        retries: Number of retry attempts made.
        max_retries: Maximum number of retries allowed.
        metadata: Optional metadata dictionary.

    Comparison:
        Jobs are compared by (priority, created_at) for priority queue ordering.
        Lower priority value = higher priority in queue.
    """

    payload: T
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.PENDING
    priority: int = 10
    result: Optional[R] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "Job") -> bool:
        """Compare jobs for priority queue ordering.

        Lower priority value = higher priority.
        If priorities are equal, earlier created jobs have priority.
        """
        if not isinstance(other, Job):
            return NotImplemented
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

    def __le__(self, other: "Job") -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, Job):
            return NotImplemented
        return self < other or self == other

    def __gt__(self, other: "Job") -> bool:
        """Greater than comparison."""
        if not isinstance(other, Job):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: "Job") -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, Job):
            return NotImplemented
        return not self < other

    @property
    def duration_ms(self) -> Optional[float]:
        """Get job processing duration in milliseconds.

        Returns:
            Duration in ms if job has completed, None otherwise.
        """
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state (completed, failed, or cancelled)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

    def mark_running(self) -> None:
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, result: R) -> None:
        """Mark job as completed with result.

        Args:
            result: The processing result.
        """
        self.status = JobStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str, traceback_str: Optional[str] = None) -> None:
        """Mark job as failed with error.

        Args:
            error: Error message.
            traceback_str: Optional full traceback.
        """
        self.status = JobStatus.FAILED
        self.error = error
        self.error_traceback = traceback_str
        self.completed_at = datetime.now(timezone.utc)

    def mark_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)

    def can_retry(self) -> bool:
        """Check if job can be retried.

        Returns:
            True if retries < max_retries.
        """
        return self.retries < self.max_retries

    def reset_for_retry(self) -> None:
        """Reset job state for retry attempt."""
        self.retries += 1
        self.status = JobStatus.PENDING
        self.error = None
        self.error_traceback = None
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary representation.

        Returns:
            Dictionary with job data.
        """
        return {
            "id": self.id,
            "status": self.status.value,
            "priority": self.priority,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }


# =============================================================================
# Queue Statistics
# =============================================================================

@dataclass
class QueueStats:
    """Statistics for the processing queue.

    Attributes:
        total_jobs: Total number of jobs submitted.
        pending_jobs: Number of jobs waiting in queue.
        running_jobs: Number of jobs currently processing.
        completed_jobs: Number of successfully completed jobs.
        failed_jobs: Number of failed jobs.
        cancelled_jobs: Number of cancelled jobs.
        total_processing_time_ms: Total time spent processing (all jobs).
        average_processing_time_ms: Average processing time per job.
    """

    total_jobs: int = 0
    pending_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    total_processing_time_ms: float = 0.0

    @property
    def average_processing_time_ms(self) -> float:
        """Calculate average processing time.

        Returns:
            Average processing time in ms, or 0 if no jobs completed.
        """
        processed = self.completed_jobs + self.failed_jobs
        if processed == 0:
            return 0.0
        return self.total_processing_time_ms / processed

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "total_jobs": self.total_jobs,
            "pending_jobs": self.pending_jobs,
            "running_jobs": self.running_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "cancelled_jobs": self.cancelled_jobs,
            "total_processing_time_ms": self.total_processing_time_ms,
            "average_processing_time_ms": self.average_processing_time_ms,
        }


# =============================================================================
# Processing Queue
# =============================================================================

# Type alias for processor function
ProcessorFunc = Callable[[T], Coroutine[Any, Any, R]]


class ProcessingQueue(Generic[T, R]):
    """Async processing queue with priority support and concurrent workers.

    Features:
    - Priority-based job ordering (lower priority value = higher priority)
    - Configurable number of concurrent workers
    - Job status tracking and error handling
    - Graceful shutdown and cancellation
    - Automatic retry support
    - Event-based notifications

    Usage:
        # Create queue with 4 workers
        queue = ProcessingQueue(max_workers=4)

        # Define processor function
        async def process(payload: dict) -> dict:
            await asyncio.sleep(1)  # Simulate work
            return {"processed": payload["id"]}

        # Enqueue jobs
        job1 = await queue.enqueue({"id": 1}, priority=1)
        job2 = await queue.enqueue({"id": 2}, priority=0)  # Higher priority

        # Process all jobs
        results = await queue.process_all(process)

        # Or start workers manually
        await queue.start(process)
        # ... enqueue more jobs ...
        await queue.shutdown()

    Attributes:
        max_workers: Maximum number of concurrent workers.
        retry_failed: Whether to automatically retry failed jobs.
        max_retries: Maximum retry attempts per job.
    """

    def __init__(
        self,
        max_workers: int = 4,
        retry_failed: bool = False,
        max_retries: int = 3,
    ):
        """Initialize the processing queue.

        Args:
            max_workers: Maximum concurrent workers (default: 4).
            retry_failed: Auto-retry failed jobs (default: False).
            max_retries: Max retries per job (default: 3).

        Raises:
            ValueError: If max_workers < 1.
        """
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")

        self.max_workers = max_workers
        self.retry_failed = retry_failed
        self.max_retries = max_retries

        # Priority queue for jobs
        self._queue: asyncio.PriorityQueue[Job[T, R]] = asyncio.PriorityQueue()

        # Job tracking
        self._jobs: Dict[str, Job[T, R]] = {}
        self._lock = asyncio.Lock()

        # Worker management
        self._workers: List[asyncio.Task] = []
        self._processor: Optional[ProcessorFunc] = None
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Statistics
        self._stats = QueueStats()

        # Event callbacks
        self._on_job_complete: Optional[Callable[[Job[T, R]], None]] = None
        self._on_job_failed: Optional[Callable[[Job[T, R]], None]] = None

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def pending_count(self) -> int:
        """Get number of pending jobs in the queue."""
        return self._queue.qsize()

    @property
    def completed_count(self) -> int:
        """Get number of completed jobs."""
        return self._stats.completed_jobs

    @property
    def failed_count(self) -> int:
        """Get number of failed jobs."""
        return self._stats.failed_jobs

    @property
    def running_count(self) -> int:
        """Get number of currently running jobs."""
        return self._stats.running_jobs

    @property
    def is_running(self) -> bool:
        """Check if queue is actively processing."""
        return self._running

    @property
    def is_empty(self) -> bool:
        """Check if queue has no pending jobs."""
        return self._queue.empty()

    # -------------------------------------------------------------------------
    # Job Management
    # -------------------------------------------------------------------------

    async def enqueue(
        self,
        payload: T,
        priority: int = 10,
        job_id: Optional[str] = None,
        max_retries: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Job[T, R]:
        """Add a job to the queue.

        Args:
            payload: Data to be processed.
            priority: Job priority (lower = higher priority, default: 10).
            job_id: Optional custom job ID.
            max_retries: Max retries for this job (overrides queue default).
            metadata: Optional metadata dictionary.

        Returns:
            The created Job instance.

        Raises:
            RuntimeError: If queue is shutting down.
        """
        if self._shutdown_event.is_set():
            raise RuntimeError("Cannot enqueue jobs during shutdown")

        job: Job[T, R] = Job(
            id=job_id or str(uuid4()),
            payload=payload,
            priority=priority,
            max_retries=max_retries if max_retries is not None else self.max_retries,
            metadata=metadata or {},
        )

        async with self._lock:
            self._jobs[job.id] = job
            self._stats.total_jobs += 1
            self._stats.pending_jobs += 1

        await self._queue.put(job)
        logger.debug(f"Enqueued job {job.id} with priority {priority}")

        return job

    async def enqueue_many(
        self,
        payloads: List[T],
        priority: int = 10,
        max_retries: Optional[int] = None,
    ) -> List[Job[T, R]]:
        """Add multiple jobs to the queue.

        Args:
            payloads: List of payloads to enqueue.
            priority: Priority for all jobs (default: 10).
            max_retries: Max retries per job.

        Returns:
            List of created Job instances.
        """
        jobs = []
        for payload in payloads:
            job = await self.enqueue(
                payload=payload,
                priority=priority,
                max_retries=max_retries,
            )
            jobs.append(job)
        return jobs

    def get_job(self, job_id: str) -> Optional[Job[T, R]]:
        """Get a job by ID.

        Args:
            job_id: The job identifier.

        Returns:
            Job instance or None if not found.
        """
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> List[Job[T, R]]:
        """Get all jobs.

        Returns:
            List of all job instances.
        """
        return list(self._jobs.values())

    def get_jobs_by_status(self, status: JobStatus) -> List[Job[T, R]]:
        """Get jobs filtered by status.

        Args:
            status: The job status to filter by.

        Returns:
            List of jobs with the specified status.
        """
        return [job for job in self._jobs.values() if job.status == status]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job.

        Args:
            job_id: The job identifier.

        Returns:
            True if job was cancelled, False if not found or not cancellable.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status != JobStatus.PENDING:
            return False

        async with self._lock:
            job.mark_cancelled()
            self._stats.pending_jobs -= 1
            self._stats.cancelled_jobs += 1

        logger.info(f"Cancelled job {job_id}")
        return True

    async def cancel_all_pending(self) -> int:
        """Cancel all pending jobs.

        Returns:
            Number of jobs cancelled.
        """
        cancelled = 0
        for job in self._jobs.values():
            if job.status == JobStatus.PENDING:
                async with self._lock:
                    job.mark_cancelled()
                    self._stats.pending_jobs -= 1
                    self._stats.cancelled_jobs += 1
                cancelled += 1

        logger.info(f"Cancelled {cancelled} pending jobs")
        return cancelled

    # -------------------------------------------------------------------------
    # Worker Management
    # -------------------------------------------------------------------------

    async def _worker(self, worker_id: int) -> None:
        """Worker coroutine that processes jobs from the queue.

        Args:
            worker_id: Worker identifier for logging.
        """
        logger.debug(f"Worker {worker_id} started")

        while self._running:
            try:
                # Wait for a job with timeout to allow shutdown check
                try:
                    job = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=0.5,
                    )
                except asyncio.TimeoutError:
                    continue

                # Skip cancelled jobs
                if job.status == JobStatus.CANCELLED:
                    self._queue.task_done()
                    continue

                # Process the job
                await self._process_job(job, worker_id)
                self._queue.task_done()

            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.exception(f"Worker {worker_id} error: {e}")

        logger.debug(f"Worker {worker_id} stopped")

    async def _process_job(self, job: Job[T, R], worker_id: int) -> None:
        """Process a single job.

        Args:
            job: The job to process.
            worker_id: Worker identifier for logging.
        """
        if not self._processor:
            logger.error(f"No processor set for job {job.id}")
            return

        logger.debug(f"Worker {worker_id} processing job {job.id}")

        # Update status
        async with self._lock:
            job.mark_running()
            self._stats.pending_jobs -= 1
            self._stats.running_jobs += 1

        start_time = time.time()

        try:
            # Execute processor
            result = await self._processor(job.payload)

            # Mark completed
            async with self._lock:
                job.mark_completed(result)
                self._stats.running_jobs -= 1
                self._stats.completed_jobs += 1
                duration = (time.time() - start_time) * 1000
                self._stats.total_processing_time_ms += duration

            logger.debug(f"Job {job.id} completed in {duration:.2f}ms")

            # Trigger callback
            if self._on_job_complete:
                try:
                    self._on_job_complete(job)
                except Exception as e:
                    logger.warning(f"Job complete callback error: {e}")

        except Exception as e:
            error_msg = str(e)
            tb_str = traceback.format_exc()

            # Check for retry
            if self.retry_failed and job.can_retry():
                logger.warning(
                    f"Job {job.id} failed (attempt {job.retries + 1}/{job.max_retries}), "
                    f"retrying: {error_msg}"
                )
                async with self._lock:
                    job.reset_for_retry()
                    self._stats.running_jobs -= 1
                    self._stats.pending_jobs += 1
                await self._queue.put(job)
            else:
                # Mark as failed
                async with self._lock:
                    job.mark_failed(error_msg, tb_str)
                    self._stats.running_jobs -= 1
                    self._stats.failed_jobs += 1
                    duration = (time.time() - start_time) * 1000
                    self._stats.total_processing_time_ms += duration

                logger.error(f"Job {job.id} failed: {error_msg}")

                # Trigger callback
                if self._on_job_failed:
                    try:
                        self._on_job_failed(job)
                    except Exception as cb_err:
                        logger.warning(f"Job failed callback error: {cb_err}")

    async def start(self, processor: ProcessorFunc) -> None:
        """Start the queue workers.

        Args:
            processor: Async function to process job payloads.

        Raises:
            RuntimeError: If queue is already running.
        """
        if self._running:
            raise RuntimeError("Queue is already running")

        self._processor = processor
        self._running = True
        self._shutdown_event.clear()

        # Start workers
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]

        logger.info(f"Started {self.max_workers} queue workers")

    async def stop(self) -> None:
        """Stop the queue workers gracefully.

        Waits for currently processing jobs to complete.
        """
        if not self._running:
            return

        logger.info("Stopping queue workers...")
        self._running = False
        self._shutdown_event.set()

        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers.clear()

        logger.info("Queue workers stopped")

    async def shutdown(self, wait_for_completion: bool = True) -> None:
        """Shutdown the queue.

        Args:
            wait_for_completion: If True, wait for pending jobs to complete.
        """
        logger.info("Shutting down queue...")
        self._shutdown_event.set()

        if wait_for_completion and not self._queue.empty():
            logger.info(f"Waiting for {self._queue.qsize()} pending jobs...")
            await self._queue.join()

        await self.stop()
        logger.info("Queue shutdown complete")

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    async def process_all(
        self,
        processor: ProcessorFunc,
        timeout: Optional[float] = None,
    ) -> List[Job[T, R]]:
        """Process all jobs in the queue and return results.

        This is a convenience method that:
        1. Starts workers
        2. Waits for all jobs to complete
        3. Stops workers
        4. Returns all jobs

        Args:
            processor: Async function to process job payloads.
            timeout: Optional timeout in seconds.

        Returns:
            List of all jobs with their results/errors.

        Raises:
            asyncio.TimeoutError: If timeout is reached.
        """
        if self._queue.empty():
            return list(self._jobs.values())

        await self.start(processor)

        try:
            if timeout:
                await asyncio.wait_for(self._queue.join(), timeout=timeout)
            else:
                await self._queue.join()
        finally:
            await self.stop()

        return list(self._jobs.values())

    async def process_batch(
        self,
        payloads: List[T],
        processor: ProcessorFunc,
        priority: int = 10,
        timeout: Optional[float] = None,
    ) -> List[Job[T, R]]:
        """Enqueue and process a batch of payloads.

        Convenience method combining enqueue_many and process_all.

        Args:
            payloads: List of payloads to process.
            processor: Async function to process each payload.
            priority: Priority for all jobs (default: 10).
            timeout: Optional timeout in seconds.

        Returns:
            List of all jobs with results.
        """
        await self.enqueue_many(payloads, priority=priority)
        return await self.process_all(processor, timeout=timeout)

    # -------------------------------------------------------------------------
    # Event Callbacks
    # -------------------------------------------------------------------------

    def on_job_complete(self, callback: Callable[[Job[T, R]], None]) -> None:
        """Set callback for job completion.

        Args:
            callback: Function to call when a job completes successfully.
        """
        self._on_job_complete = callback

    def on_job_failed(self, callback: Callable[[Job[T, R]], None]) -> None:
        """Set callback for job failure.

        Args:
            callback: Function to call when a job fails.
        """
        self._on_job_failed = callback

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> QueueStats:
        """Get queue statistics.

        Returns:
            QueueStats instance with current statistics.
        """
        return self._stats

    def reset_stats(self) -> None:
        """Reset queue statistics."""
        self._stats = QueueStats()

    def clear(self) -> None:
        """Clear all jobs and reset the queue.

        Warning: This does not stop running workers.
        """
        self._jobs.clear()
        self._queue = asyncio.PriorityQueue()
        self._stats = QueueStats()
        logger.info("Queue cleared")


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "JobStatus",
    # Dataclasses
    "Job",
    "QueueStats",
    # Main class
    "ProcessingQueue",
    # Type alias
    "ProcessorFunc",
]
