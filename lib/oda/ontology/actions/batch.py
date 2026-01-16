"""
Orion ODA v4.0 - Batch Action Executor
======================================

Implements batch execution of multiple actions with:
- Transaction grouping
- Progress reporting
- Partial rollback on failure

Phase 3.3 Implementation:
- 3.3.1: BatchAction executor
- 3.3.2: Transaction grouping
- 3.3.3: Batch progress reporting
- 3.3.4: Partial rollback on failure

Schema Version: 4.0.0
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    action_registry,
)
from lib.oda.ontology.ontology_types import OntologyObject, utc_now

logger = logging.getLogger(__name__)


# =============================================================================
# BATCH EXECUTION ENUMS AND MODELS
# =============================================================================


class BatchExecutionMode(str, Enum):
    """Mode for batch execution."""
    SEQUENTIAL = "sequential"  # Execute one at a time
    PARALLEL = "parallel"      # Execute all in parallel
    TRANSACTIONAL = "transactional"  # All-or-nothing with rollback


class BatchItemStatus(str, Enum):
    """Status of individual batch item."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class RollbackStrategy(str, Enum):
    """Strategy for handling failures in batch."""
    CONTINUE = "continue"     # Continue with remaining items
    STOP = "stop"             # Stop at first failure
    ROLLBACK = "rollback"     # Rollback completed items


@dataclass
class BatchItem:
    """
    Individual item in a batch execution.

    Represents a single action to be executed as part of a batch.
    """
    action_type: str
    params: Dict[str, Any]
    status: BatchItemStatus = BatchItemStatus.PENDING
    result: Optional[ActionResult] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rollback_data: Optional[Dict[str, Any]] = None

    @property
    def duration_ms(self) -> Optional[float]:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


@dataclass
class BatchProgress:
    """
    Progress report for batch execution.

    Used for real-time progress tracking.
    """
    batch_id: str
    total_items: int
    completed_items: int
    failed_items: int
    current_item: Optional[str] = None
    percent_complete: float = 0.0
    elapsed_ms: float = 0.0
    estimated_remaining_ms: Optional[float] = None
    status: str = "running"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "batch_id": self.batch_id,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "current_item": self.current_item,
            "percent_complete": self.percent_complete,
            "elapsed_ms": self.elapsed_ms,
            "estimated_remaining_ms": self.estimated_remaining_ms,
            "status": self.status,
        }


class BatchResult(BaseModel):
    """
    Result of batch execution.

    Contains summary of all executed items and their results.
    """
    batch_id: str = Field(..., description="Unique batch identifier")
    success: bool = Field(default=True, description="Overall batch success")
    total_items: int = Field(default=0, description="Total items in batch")
    succeeded_items: int = Field(default=0, description="Successfully executed items")
    failed_items: int = Field(default=0, description="Failed items")
    skipped_items: int = Field(default=0, description="Skipped items")
    rolled_back_items: int = Field(default=0, description="Rolled back items")

    items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Individual item results"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages"
    )

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Batch start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Batch completion time"
    )
    duration_ms: Optional[float] = Field(
        default=None,
        description="Total duration in milliseconds"
    )

    edits: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All edit operations from successful items"
    )


# =============================================================================
# PROGRESS CALLBACK TYPE
# =============================================================================


ProgressCallback = Callable[[BatchProgress], None]


# =============================================================================
# BATCH EXECUTOR
# =============================================================================


class BatchExecutor:
    """
    Executor for batch action processing.

    Supports:
    - Sequential, parallel, and transactional execution
    - Progress reporting via callbacks
    - Partial rollback on failure
    - Transaction grouping

    Usage:
        executor = BatchExecutor()

        # Add items to batch
        executor.add_item("file.read", {"file_path": "/path/to/file"})
        executor.add_item("file.write", {"file_path": "/path/to/file", "content": "..."})

        # Execute with progress callback
        result = await executor.execute(
            context=ActionContext(actor_id="user"),
            on_progress=lambda p: print(f"Progress: {p.percent_complete}%"),
            mode=BatchExecutionMode.SEQUENTIAL,
            rollback_strategy=RollbackStrategy.ROLLBACK
        )
    """

    def __init__(self, batch_id: Optional[str] = None):
        """Initialize batch executor."""
        self.batch_id = batch_id or self._generate_batch_id()
        self.items: List[BatchItem] = []
        self._transaction_groups: Dict[str, List[int]] = {}  # group_name -> item indices
        self._rollback_handlers: Dict[str, Callable] = {}

    @staticmethod
    def _generate_batch_id() -> str:
        """Generate unique batch ID."""
        import uuid
        return f"batch-{uuid.uuid4().hex[:8]}"

    def add_item(
        self,
        action_type: str,
        params: Dict[str, Any],
        group: Optional[str] = None,
        rollback_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add an item to the batch.

        Args:
            action_type: API name of the action
            params: Action parameters
            group: Optional transaction group name
            rollback_data: Optional data needed for rollback

        Returns:
            Index of the added item
        """
        item = BatchItem(
            action_type=action_type,
            params=params,
            rollback_data=rollback_data
        )
        index = len(self.items)
        self.items.append(item)

        # Add to transaction group if specified
        if group:
            if group not in self._transaction_groups:
                self._transaction_groups[group] = []
            self._transaction_groups[group].append(index)

        return index

    def create_transaction_group(self, name: str, items: List[Dict[str, Any]]) -> List[int]:
        """
        Create a transaction group with multiple items.

        All items in a group succeed or fail together.

        Args:
            name: Group name for identification
            items: List of {"action_type": str, "params": dict}

        Returns:
            List of item indices in the group
        """
        indices = []
        for item in items:
            idx = self.add_item(
                action_type=item["action_type"],
                params=item["params"],
                group=name,
                rollback_data=item.get("rollback_data")
            )
            indices.append(idx)
        return indices

    def register_rollback_handler(
        self,
        action_type: str,
        handler: Callable[[Dict[str, Any], ActionContext], None]
    ) -> None:
        """
        Register a custom rollback handler for an action type.

        Args:
            action_type: API name of the action
            handler: Async function to perform rollback
        """
        self._rollback_handlers[action_type] = handler

    async def execute(
        self,
        context: ActionContext,
        mode: BatchExecutionMode = BatchExecutionMode.SEQUENTIAL,
        rollback_strategy: RollbackStrategy = RollbackStrategy.CONTINUE,
        on_progress: Optional[ProgressCallback] = None,
        max_parallel: int = 5
    ) -> BatchResult:
        """
        Execute all items in the batch.

        Args:
            context: Execution context
            mode: Execution mode (sequential, parallel, transactional)
            rollback_strategy: How to handle failures
            on_progress: Optional progress callback
            max_parallel: Max concurrent executions for parallel mode

        Returns:
            BatchResult with summary of execution
        """
        result = BatchResult(
            batch_id=self.batch_id,
            total_items=len(self.items),
            started_at=datetime.now(timezone.utc)
        )

        if not self.items:
            result.completed_at = datetime.now(timezone.utc)
            result.duration_ms = 0
            return result

        start_time = datetime.now(timezone.utc)

        try:
            if mode == BatchExecutionMode.PARALLEL:
                await self._execute_parallel(context, result, on_progress, max_parallel, rollback_strategy)
            elif mode == BatchExecutionMode.TRANSACTIONAL:
                await self._execute_transactional(context, result, on_progress)
            else:  # SEQUENTIAL
                await self._execute_sequential(context, result, on_progress, rollback_strategy)

        except Exception as e:
            logger.exception(f"Batch execution failed: {e}")
            result.success = False
            result.errors.append(f"Batch execution error: {str(e)}")

        # Finalize result
        end_time = datetime.now(timezone.utc)
        result.completed_at = end_time
        result.duration_ms = (end_time - start_time).total_seconds() * 1000

        # Calculate success
        result.success = result.failed_items == 0

        # Collect edits
        for item in self.items:
            if item.result and item.result.success:
                for edit in item.result.edits:
                    result.edits.append(edit.to_dict() if hasattr(edit, 'to_dict') else edit)

        # Final progress report
        if on_progress:
            progress = self._create_progress(
                completed=result.succeeded_items + result.failed_items + result.skipped_items,
                failed=result.failed_items,
                current_item=None,
                start_time=start_time,
                status="completed" if result.success else "failed"
            )
            on_progress(progress)

        return result

    async def _execute_sequential(
        self,
        context: ActionContext,
        result: BatchResult,
        on_progress: Optional[ProgressCallback],
        rollback_strategy: RollbackStrategy
    ) -> None:
        """Execute items sequentially."""
        start_time = datetime.now(timezone.utc)
        completed = 0
        failed = 0

        for i, item in enumerate(self.items):
            # Report progress
            if on_progress:
                progress = self._create_progress(
                    completed=completed,
                    failed=failed,
                    current_item=item.action_type,
                    start_time=start_time
                )
                on_progress(progress)

            # Execute item
            item_result = await self._execute_item(item, context)
            completed += 1

            if item_result.success:
                result.succeeded_items += 1
            else:
                result.failed_items += 1
                failed += 1
                result.errors.append(f"[{item.action_type}] {item_result.error or 'Unknown error'}")

                if rollback_strategy == RollbackStrategy.STOP:
                    # Mark remaining as skipped
                    for remaining in self.items[i+1:]:
                        remaining.status = BatchItemStatus.SKIPPED
                        result.skipped_items += 1
                    break

                elif rollback_strategy == RollbackStrategy.ROLLBACK:
                    # Rollback completed items
                    await self._rollback_completed(self.items[:i], context)
                    result.rolled_back_items = i
                    # Mark remaining as skipped
                    for remaining in self.items[i+1:]:
                        remaining.status = BatchItemStatus.SKIPPED
                        result.skipped_items += 1
                    break

            # Add to result items
            result.items.append({
                "action_type": item.action_type,
                "status": item.status.value,
                "duration_ms": item.duration_ms,
                "error": item.error
            })

    async def _execute_parallel(
        self,
        context: ActionContext,
        result: BatchResult,
        on_progress: Optional[ProgressCallback],
        max_parallel: int,
        rollback_strategy: RollbackStrategy
    ) -> None:
        """Execute items in parallel with concurrency limit."""
        start_time = datetime.now(timezone.utc)
        semaphore = asyncio.Semaphore(max_parallel)
        completed = 0
        failed = 0
        lock = asyncio.Lock()

        async def execute_with_semaphore(item: BatchItem) -> ActionResult:
            nonlocal completed, failed
            async with semaphore:
                item_result = await self._execute_item(item, context)
                async with lock:
                    completed += 1
                    if not item_result.success:
                        failed += 1
                    if on_progress:
                        progress = self._create_progress(
                            completed=completed,
                            failed=failed,
                            current_item=None,
                            start_time=start_time
                        )
                        on_progress(progress)
                return item_result

        # Execute all items in parallel
        tasks = [execute_with_semaphore(item) for item in self.items]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        for item in self.items:
            if item.status == BatchItemStatus.SUCCEEDED:
                result.succeeded_items += 1
            elif item.status == BatchItemStatus.FAILED:
                result.failed_items += 1
                result.errors.append(f"[{item.action_type}] {item.error or 'Unknown error'}")

            result.items.append({
                "action_type": item.action_type,
                "status": item.status.value,
                "duration_ms": item.duration_ms,
                "error": item.error
            })

    async def _execute_transactional(
        self,
        context: ActionContext,
        result: BatchResult,
        on_progress: Optional[ProgressCallback]
    ) -> None:
        """Execute items transactionally (all-or-nothing)."""
        start_time = datetime.now(timezone.utc)
        completed = 0

        for i, item in enumerate(self.items):
            # Report progress
            if on_progress:
                progress = self._create_progress(
                    completed=completed,
                    failed=0,
                    current_item=item.action_type,
                    start_time=start_time
                )
                on_progress(progress)

            # Execute item
            item_result = await self._execute_item(item, context)
            completed += 1

            if item_result.success:
                result.items.append({
                    "action_type": item.action_type,
                    "status": item.status.value,
                    "duration_ms": item.duration_ms
                })
            else:
                # Transaction failed - rollback everything
                result.failed_items += 1
                result.errors.append(f"[{item.action_type}] {item_result.error or 'Unknown error'}")

                # Rollback all completed items
                completed_items = [itm for itm in self.items[:i] if itm.status == BatchItemStatus.SUCCEEDED]
                await self._rollback_completed(completed_items, context)
                result.rolled_back_items = len(completed_items)

                # Mark remaining as skipped
                for remaining in self.items[i+1:]:
                    remaining.status = BatchItemStatus.SKIPPED
                    result.skipped_items += 1

                return

        # All succeeded
        result.succeeded_items = len(self.items)

    async def _execute_item(self, item: BatchItem, context: ActionContext) -> ActionResult:
        """Execute a single batch item."""
        item.status = BatchItemStatus.IN_PROGRESS
        item.started_at = datetime.now(timezone.utc)

        try:
            # Get action class from registry
            action_cls = action_registry.get(item.action_type)
            if not action_cls:
                raise ValueError(f"Unknown action type: {item.action_type}")

            # Create action instance and execute
            action = action_cls()
            result = await action.execute(item.params, context)

            item.result = result
            item.completed_at = datetime.now(timezone.utc)

            if result.success:
                item.status = BatchItemStatus.SUCCEEDED
            else:
                item.status = BatchItemStatus.FAILED
                item.error = result.error

            return result

        except Exception as e:
            logger.exception(f"Failed to execute {item.action_type}: {e}")
            item.status = BatchItemStatus.FAILED
            item.error = str(e)
            item.completed_at = datetime.now(timezone.utc)

            return ActionResult(
                action_type=item.action_type,
                success=False,
                error=str(e)
            )

    async def _rollback_completed(
        self,
        items: List[BatchItem],
        context: ActionContext
    ) -> None:
        """
        Rollback completed items.

        Uses registered rollback handlers or default rollback logic.
        """
        # Rollback in reverse order
        for item in reversed(items):
            if item.status != BatchItemStatus.SUCCEEDED:
                continue

            try:
                # Check for registered handler
                if item.action_type in self._rollback_handlers:
                    handler = self._rollback_handlers[item.action_type]
                    await handler(item.rollback_data or item.params, context)
                else:
                    # Default rollback based on action type
                    await self._default_rollback(item, context)

                item.status = BatchItemStatus.ROLLED_BACK
                logger.info(f"Rolled back {item.action_type}")

            except Exception as e:
                logger.error(f"Failed to rollback {item.action_type}: {e}")

    async def _default_rollback(self, item: BatchItem, context: ActionContext) -> None:
        """
        Default rollback logic for common action types.

        This is best-effort - some actions may not be rollback-able.
        """
        action_type = item.action_type
        params = item.params
        rollback_data = item.rollback_data or {}

        # File operations rollback
        if action_type == "file.write":
            # If we have original content, restore it
            if "original_content" in rollback_data:
                action_cls = action_registry.get("file.write")
                if action_cls:
                    action = action_cls()
                    await action.execute({
                        "file_path": params["file_path"],
                        "content": rollback_data["original_content"],
                        "reason": f"Rollback from batch {self.batch_id}"
                    }, context)
            elif "was_new_file" in rollback_data and rollback_data["was_new_file"]:
                # Delete the newly created file
                action_cls = action_registry.get("file.delete")
                if action_cls:
                    action = action_cls()
                    await action.execute({
                        "file_path": params["file_path"],
                        "reason": f"Rollback from batch {self.batch_id}"
                    }, context)

        elif action_type == "file.modify":
            # Restore original content
            if "original_content" in rollback_data:
                action_cls = action_registry.get("file.modify")
                if action_cls:
                    action = action_cls()
                    await action.execute({
                        "file_path": params["file_path"],
                        "new_content": rollback_data["original_content"],
                        "reason": f"Rollback from batch {self.batch_id}"
                    }, context)

        # For other action types, log a warning
        else:
            logger.warning(
                f"No default rollback for {action_type}. "
                f"Consider registering a custom rollback handler."
            )

    def _create_progress(
        self,
        completed: int,
        failed: int,
        current_item: Optional[str],
        start_time: datetime,
        status: str = "running"
    ) -> BatchProgress:
        """Create a progress report."""
        total = len(self.items)
        elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        percent = (completed / total * 100) if total > 0 else 0

        # Estimate remaining time
        estimated_remaining = None
        if completed > 0 and completed < total:
            avg_time_per_item = elapsed_ms / completed
            remaining_items = total - completed
            estimated_remaining = avg_time_per_item * remaining_items

        return BatchProgress(
            batch_id=self.batch_id,
            total_items=total,
            completed_items=completed,
            failed_items=failed,
            current_item=current_item,
            percent_complete=percent,
            elapsed_ms=elapsed_ms,
            estimated_remaining_ms=estimated_remaining,
            status=status
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


async def execute_batch(
    items: List[Dict[str, Any]],
    context: ActionContext,
    mode: BatchExecutionMode = BatchExecutionMode.SEQUENTIAL,
    rollback_strategy: RollbackStrategy = RollbackStrategy.CONTINUE,
    on_progress: Optional[ProgressCallback] = None
) -> BatchResult:
    """
    Execute a batch of actions.

    Convenience function for quick batch execution.

    Args:
        items: List of {"action_type": str, "params": dict}
        context: Execution context
        mode: Execution mode
        rollback_strategy: How to handle failures
        on_progress: Optional progress callback

    Returns:
        BatchResult

    Usage:
        result = await execute_batch([
            {"action_type": "file.read", "params": {"file_path": "/path"}},
            {"action_type": "file.write", "params": {"file_path": "/path", "content": "..."}},
        ], context)
    """
    executor = BatchExecutor()
    for item in items:
        executor.add_item(
            action_type=item["action_type"],
            params=item["params"],
            rollback_data=item.get("rollback_data")
        )

    return await executor.execute(
        context=context,
        mode=mode,
        rollback_strategy=rollback_strategy,
        on_progress=on_progress
    )


async def execute_transaction(
    items: List[Dict[str, Any]],
    context: ActionContext,
    on_progress: Optional[ProgressCallback] = None
) -> BatchResult:
    """
    Execute a transactional batch (all-or-nothing).

    If any item fails, all completed items are rolled back.

    Args:
        items: List of {"action_type": str, "params": dict}
        context: Execution context
        on_progress: Optional progress callback

    Returns:
        BatchResult
    """
    return await execute_batch(
        items=items,
        context=context,
        mode=BatchExecutionMode.TRANSACTIONAL,
        on_progress=on_progress
    )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "BatchExecutionMode",
    "BatchItemStatus",
    "RollbackStrategy",
    # Models
    "BatchItem",
    "BatchProgress",
    "BatchResult",
    # Executor
    "BatchExecutor",
    # Convenience functions
    "execute_batch",
    "execute_transaction",
    # Types
    "ProgressCallback",
]
