"""
Orion ODA v4.0 - Merge Strategy
Palantir Foundry Compliant Three-Way Merge

This module provides:
- MergeStrategy: Three-way merge implementation
- MergeResult: Merge operation result
- MergeExecutor: Merge execution coordination

Design Principles:
1. Three-way merge with common ancestor detection
2. Conflict detection before merge
3. Multiple merge strategies (fast-forward, recursive, squash)
4. Full audit trail of merge operations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from lib.oda.ontology.objects.branch import Branch, BranchCommit

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class MergeStatus(str, Enum):
    """Merge operation status."""
    PENDING = "pending"           # Merge not started
    IN_PROGRESS = "in_progress"   # Merge in progress
    COMPLETED = "completed"       # Merge completed successfully
    FAILED = "failed"             # Merge failed
    CONFLICTS = "conflicts"       # Merge has conflicts requiring resolution
    CANCELLED = "cancelled"       # Merge was cancelled


class MergeMode(str, Enum):
    """Merge strategy mode."""
    FAST_FORWARD = "fast_forward"  # Move pointer if linear history
    RECURSIVE = "recursive"        # Standard three-way merge
    SQUASH = "squash"             # Combine all commits into one
    REBASE = "rebase"             # Replay commits on top of target
    NO_FAST_FORWARD = "no_ff"     # Always create merge commit


# =============================================================================
# DATA CLASSES
# =============================================================================

def _utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def _generate_id() -> str:
    """Generate unique identifier."""
    return uuid.uuid4().hex[:16]


@dataclass
class MergeCommit:
    """Represents a merge commit."""
    id: str = field(default_factory=_generate_id)
    message: str = ""
    source_branch_id: str = ""
    target_branch_id: str = ""
    source_commit_id: Optional[str] = None
    target_commit_id: Optional[str] = None
    common_ancestor_id: Optional[str] = None
    merged_commits: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    author_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message": self.message,
            "source_branch_id": self.source_branch_id,
            "target_branch_id": self.target_branch_id,
            "source_commit_id": self.source_commit_id,
            "target_commit_id": self.target_commit_id,
            "common_ancestor_id": self.common_ancestor_id,
            "merged_commits": self.merged_commits,
            "created_at": self.created_at.isoformat(),
            "author_id": self.author_id,
        }


@dataclass
class MergeResult:
    """Result of a merge operation."""
    success: bool
    status: MergeStatus = MergeStatus.PENDING
    source_branch_id: Optional[str] = None
    target_branch_id: Optional[str] = None
    merge_commit_id: Optional[str] = None
    merged_commit_count: int = 0
    conflicts: List["MergeConflict"] = field(default_factory=list)
    error: Optional[str] = None
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None
    merge_mode: MergeMode = MergeMode.RECURSIVE
    is_fast_forward: bool = False

    @property
    def has_conflicts(self) -> bool:
        """Check if merge has conflicts."""
        return len(self.conflicts) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "source_branch_id": self.source_branch_id,
            "target_branch_id": self.target_branch_id,
            "merge_commit_id": self.merge_commit_id,
            "merged_commit_count": self.merged_commit_count,
            "conflict_count": len(self.conflicts),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "merge_mode": self.merge_mode.value,
            "is_fast_forward": self.is_fast_forward,
        }


@dataclass
class MergeConflict:
    """Represents a merge conflict."""
    id: str = field(default_factory=_generate_id)
    object_type: str = ""
    object_id: str = ""
    field_name: str = ""
    source_value: Any = None
    target_value: Any = None
    base_value: Any = None
    source_commit_id: Optional[str] = None
    target_commit_id: Optional[str] = None
    resolved: bool = False
    resolution_value: Any = None
    resolution_mode: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "field_name": self.field_name,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "base_value": self.base_value,
            "source_commit_id": self.source_commit_id,
            "target_commit_id": self.target_commit_id,
            "resolved": self.resolved,
            "resolution_value": self.resolution_value,
            "resolution_mode": self.resolution_mode,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


# =============================================================================
# MERGE STRATEGY
# =============================================================================

class MergeStrategy:
    """
    Three-way merge strategy implementation.

    Supports:
    - Fast-forward merges (linear history)
    - Recursive three-way merge
    - Squash merge (combine commits)
    - Rebase (replay commits)

    Usage:
        ```python
        strategy = MergeStrategy(branch_manager)

        # Check if merge is possible
        can_merge, conflicts = await strategy.preview_merge(
            source_branch_id="feature-branch",
            target_branch_id="main"
        )

        # Execute merge
        if can_merge:
            result = await strategy.merge(
                source_branch_id="feature-branch",
                target_branch_id="main",
                mode=MergeMode.RECURSIVE,
                author_id="user-123"
            )
        ```
    """

    def __init__(
        self,
        branch_manager: Any = None,  # BranchManager
    ):
        """
        Initialize MergeStrategy.

        Args:
            branch_manager: Branch manager for branch operations
        """
        self._branch_manager = branch_manager

    async def preview_merge(
        self,
        source_branch_id: str,
        target_branch_id: str,
        mode: MergeMode = MergeMode.RECURSIVE,
    ) -> tuple[bool, List[MergeConflict]]:
        """
        Preview merge without executing.

        Args:
            source_branch_id: Branch to merge from
            target_branch_id: Branch to merge into
            mode: Merge mode to use

        Returns:
            Tuple of (can_merge, conflicts)
        """
        # Get branches
        if not self._branch_manager:
            return False, []

        source = await self._branch_manager.get_branch(source_branch_id)
        target = await self._branch_manager.get_branch(target_branch_id)

        if not source or not target:
            return False, []

        # Check if fast-forward is possible
        if mode == MergeMode.FAST_FORWARD:
            is_ff = await self._can_fast_forward(source_branch_id, target_branch_id)
            if is_ff:
                return True, []
            return False, []

        # Detect conflicts for three-way merge
        conflicts = await self._detect_conflicts(
            source_branch_id, target_branch_id
        )

        return len(conflicts) == 0, conflicts

    async def merge(
        self,
        source_branch_id: str,
        target_branch_id: str,
        mode: MergeMode = MergeMode.RECURSIVE,
        author_id: Optional[str] = None,
        message: Optional[str] = None,
        auto_resolve: bool = False,
    ) -> MergeResult:
        """
        Execute merge operation.

        Args:
            source_branch_id: Branch to merge from
            target_branch_id: Branch to merge into
            mode: Merge strategy mode
            author_id: Author of the merge
            message: Custom merge message
            auto_resolve: Auto-resolve conflicts using THEIRS strategy

        Returns:
            MergeResult with outcome details
        """
        result = MergeResult(
            success=False,
            source_branch_id=source_branch_id,
            target_branch_id=target_branch_id,
            merge_mode=mode,
        )

        try:
            # Validate branches
            if not self._branch_manager:
                result.error = "Branch manager not configured"
                result.status = MergeStatus.FAILED
                return result

            source = await self._branch_manager.get_branch(source_branch_id)
            target = await self._branch_manager.get_branch(target_branch_id)

            if not source:
                result.error = f"Source branch not found: {source_branch_id}"
                result.status = MergeStatus.FAILED
                return result

            if not target:
                result.error = f"Target branch not found: {target_branch_id}"
                result.status = MergeStatus.FAILED
                return result

            if not source.can_merge:
                result.error = f"Source branch cannot be merged: {source.branch_status.value}"
                result.status = MergeStatus.FAILED
                return result

            result.status = MergeStatus.IN_PROGRESS

            # Execute based on mode
            if mode == MergeMode.FAST_FORWARD:
                return await self._fast_forward_merge(
                    source, target, author_id, result
                )
            elif mode == MergeMode.SQUASH:
                return await self._squash_merge(
                    source, target, author_id, message, result
                )
            elif mode == MergeMode.REBASE:
                return await self._rebase_merge(
                    source, target, author_id, result
                )
            else:
                # Recursive three-way merge
                return await self._three_way_merge(
                    source, target, author_id, message, auto_resolve, result
                )

        except Exception as e:
            logger.error(f"Merge failed: {e}")
            result.success = False
            result.status = MergeStatus.FAILED
            result.error = str(e)
            return result

    async def _can_fast_forward(
        self,
        source_branch_id: str,
        target_branch_id: str,
    ) -> bool:
        """
        Check if fast-forward merge is possible.

        Fast-forward is possible when target hasn't diverged from source.
        """
        if not self._branch_manager:
            return False

        source = await self._branch_manager.get_branch(source_branch_id)
        target = await self._branch_manager.get_branch(target_branch_id)

        if not source or not target:
            return False

        # Check if source is a descendant of target
        # (target hasn't had any new commits since source was created)
        target_commits = await self._branch_manager.get_commits(target_branch_id)
        source_commits = await self._branch_manager.get_commits(source_branch_id)

        if not source_commits:
            return True  # Nothing to merge

        # Find if source base commit is in target
        base_commit_id = source.base_commit_id
        for commit in target_commits:
            if commit.id == base_commit_id:
                # Check if target has any commits after base
                idx = target_commits.index(commit)
                return idx == 0  # Base is latest commit

        return False

    async def _find_common_ancestor(
        self,
        source_branch_id: str,
        target_branch_id: str,
    ) -> Optional[str]:
        """Find the common ancestor commit between two branches."""
        if not self._branch_manager:
            return None

        source = await self._branch_manager.get_branch(source_branch_id)

        if source and source.base_commit_id:
            return source.base_commit_id

        return None

    async def _detect_conflicts(
        self,
        source_branch_id: str,
        target_branch_id: str,
    ) -> List[MergeConflict]:
        """
        Detect conflicts between two branches.

        Compares changes in both branches since common ancestor
        to find overlapping modifications.
        """
        conflicts = []

        if not self._branch_manager:
            return conflicts

        # Get commits from both branches
        source_commits = await self._branch_manager.get_commits(source_branch_id)
        target_commits = await self._branch_manager.get_commits(target_branch_id)

        # Find common ancestor
        ancestor_id = await self._find_common_ancestor(source_branch_id, target_branch_id)

        # Build change sets
        source_changes = self._build_change_set(source_commits, ancestor_id)
        target_changes = self._build_change_set(target_commits, ancestor_id)

        # Find overlapping changes
        for obj_key, source_change in source_changes.items():
            if obj_key in target_changes:
                target_change = target_changes[obj_key]

                # Check for field-level conflicts
                field_conflicts = self._detect_field_conflicts(
                    source_change, target_change
                )
                conflicts.extend(field_conflicts)

        return conflicts

    def _build_change_set(
        self,
        commits: List["BranchCommit"],
        since_ancestor_id: Optional[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a set of changes from commits.

        Returns dict mapping (object_type, object_id) -> latest changes
        """
        changes: Dict[str, Dict[str, Any]] = {}

        include = since_ancestor_id is None

        for commit in reversed(commits):  # Process in order
            if not include:
                if commit.id == since_ancestor_id:
                    include = True
                continue

            if commit.object_id:
                key = f"{commit.object_type}:{commit.object_id}"
                changes[key] = {
                    "commit_id": commit.id,
                    "object_type": commit.object_type,
                    "object_id": commit.object_id,
                    "operation": commit.operation,
                    "previous_state": commit.previous_state,
                    "new_state": commit.new_state,
                }

        return changes

    def _detect_field_conflicts(
        self,
        source_change: Dict[str, Any],
        target_change: Dict[str, Any],
    ) -> List[MergeConflict]:
        """Detect field-level conflicts between two changes."""
        conflicts = []

        source_state = source_change.get("new_state") or {}
        target_state = target_change.get("new_state") or {}

        # Compare fields
        all_fields = set(source_state.keys()) | set(target_state.keys())

        for field_name in all_fields:
            source_value = source_state.get(field_name)
            target_value = target_state.get(field_name)

            if source_value != target_value:
                # Conflict detected
                conflict = MergeConflict(
                    object_type=source_change.get("object_type", ""),
                    object_id=source_change.get("object_id", ""),
                    field_name=field_name,
                    source_value=source_value,
                    target_value=target_value,
                    source_commit_id=source_change.get("commit_id"),
                    target_commit_id=target_change.get("commit_id"),
                )
                conflicts.append(conflict)

        return conflicts

    async def _fast_forward_merge(
        self,
        source: "Branch",
        target: "Branch",
        author_id: Optional[str],
        result: MergeResult,
    ) -> MergeResult:
        """Execute fast-forward merge."""
        can_ff = await self._can_fast_forward(source.id, target.id)

        if not can_ff:
            result.success = False
            result.status = MergeStatus.FAILED
            result.error = "Fast-forward not possible - branches have diverged"
            return result

        # Get source commits to apply
        source_commits = await self._branch_manager.get_commits(source.id)

        # Update target branch
        for commit in source_commits:
            await self._branch_manager.commit(
                branch_id=target.id,
                message=commit.message,
                author_id=commit.author_id,
                object_type=commit.object_type,
                object_id=commit.object_id,
                operation=commit.operation,
                previous_state=commit.previous_state,
                new_state=commit.new_state,
                metadata={"cherry_picked_from": commit.id},
            )

        # Update source branch status
        from lib.oda.ontology.objects.branch import BranchStatus
        source.branch_status = BranchStatus.MERGED
        source.merged_to_branch_id = target.id
        source.merged_at = _utc_now()
        source.merged_by = author_id

        result.success = True
        result.status = MergeStatus.COMPLETED
        result.is_fast_forward = True
        result.merged_commit_count = len(source_commits)
        result.completed_at = _utc_now()

        logger.info(
            f"Fast-forward merge completed: {source.id} -> {target.id}, "
            f"commits={len(source_commits)}"
        )

        return result

    async def _squash_merge(
        self,
        source: "Branch",
        target: "Branch",
        author_id: Optional[str],
        message: Optional[str],
        result: MergeResult,
    ) -> MergeResult:
        """Execute squash merge - combine all commits into one."""
        source_commits = await self._branch_manager.get_commits(source.id)

        if not source_commits:
            result.success = True
            result.status = MergeStatus.COMPLETED
            result.merged_commit_count = 0
            result.completed_at = _utc_now()
            return result

        # Create single squashed commit
        combined_message = message or f"Squash merge from {source.name}\n\n"
        if not message:
            for commit in source_commits:
                combined_message += f"- {commit.message}\n"

        # Combine state changes
        combined_state: Dict[str, Any] = {}
        for commit in source_commits:
            if commit.new_state:
                combined_state.update(commit.new_state)

        commit_result = await self._branch_manager.commit(
            branch_id=target.id,
            message=combined_message,
            author_id=author_id or "system",
            operation="merge",
            new_state=combined_state,
            metadata={
                "squash_merge": True,
                "squashed_commits": [c.id for c in source_commits],
                "source_branch": source.id,
            },
        )

        if not commit_result.success:
            result.success = False
            result.status = MergeStatus.FAILED
            result.error = commit_result.error
            return result

        # Update source branch
        from lib.oda.ontology.objects.branch import BranchStatus
        source.branch_status = BranchStatus.MERGED
        source.merged_to_branch_id = target.id
        source.merged_at = _utc_now()
        source.merged_by = author_id

        result.success = True
        result.status = MergeStatus.COMPLETED
        result.merge_commit_id = commit_result.commit_id
        result.merged_commit_count = len(source_commits)
        result.completed_at = _utc_now()

        logger.info(
            f"Squash merge completed: {source.id} -> {target.id}, "
            f"commits={len(source_commits)}"
        )

        return result

    async def _rebase_merge(
        self,
        source: "Branch",
        target: "Branch",
        author_id: Optional[str],
        result: MergeResult,
    ) -> MergeResult:
        """Execute rebase merge - replay commits on top of target."""
        source_commits = await self._branch_manager.get_commits(source.id)

        if not source_commits:
            result.success = True
            result.status = MergeStatus.COMPLETED
            result.merged_commit_count = 0
            result.completed_at = _utc_now()
            return result

        # Get latest target commit
        target_commits = await self._branch_manager.get_commits(target.id, limit=1)
        new_base = target_commits[0].id if target_commits else None

        # Replay each commit
        for commit in reversed(source_commits):
            commit_result = await self._branch_manager.commit(
                branch_id=target.id,
                message=commit.message,
                author_id=commit.author_id,
                object_type=commit.object_type,
                object_id=commit.object_id,
                operation=commit.operation,
                previous_state=commit.previous_state,
                new_state=commit.new_state,
                metadata={
                    "rebased_from": commit.id,
                    "original_branch": source.id,
                },
            )

            if not commit_result.success:
                result.success = False
                result.status = MergeStatus.FAILED
                result.error = f"Rebase failed at commit {commit.id}: {commit_result.error}"
                return result

        # Update source branch
        from lib.oda.ontology.objects.branch import BranchStatus
        source.branch_status = BranchStatus.MERGED
        source.merged_to_branch_id = target.id
        source.merged_at = _utc_now()
        source.merged_by = author_id

        result.success = True
        result.status = MergeStatus.COMPLETED
        result.merged_commit_count = len(source_commits)
        result.completed_at = _utc_now()

        logger.info(
            f"Rebase merge completed: {source.id} -> {target.id}, "
            f"commits={len(source_commits)}"
        )

        return result

    async def _three_way_merge(
        self,
        source: "Branch",
        target: "Branch",
        author_id: Optional[str],
        message: Optional[str],
        auto_resolve: bool,
        result: MergeResult,
    ) -> MergeResult:
        """Execute three-way recursive merge."""
        # Detect conflicts
        conflicts = await self._detect_conflicts(source.id, target.id)

        if conflicts and not auto_resolve:
            result.success = False
            result.status = MergeStatus.CONFLICTS
            result.conflicts = conflicts
            result.error = f"Merge has {len(conflicts)} conflict(s) requiring resolution"
            return result

        if conflicts and auto_resolve:
            # Auto-resolve using THEIRS (target) strategy
            for conflict in conflicts:
                conflict.resolved = True
                conflict.resolution_value = conflict.target_value
                conflict.resolution_mode = "theirs"
                conflict.resolved_by = "auto"
                conflict.resolved_at = _utc_now()
            result.conflicts = conflicts

        # Get source commits
        source_commits = await self._branch_manager.get_commits(source.id)

        # Find common ancestor
        ancestor_id = await self._find_common_ancestor(source.id, target.id)

        # Create merge commit
        merge_message = message or f"Merge branch '{source.name}' into '{target.name}'"

        merge_commit = MergeCommit(
            message=merge_message,
            source_branch_id=source.id,
            target_branch_id=target.id,
            common_ancestor_id=ancestor_id,
            merged_commits=[c.id for c in source_commits],
            author_id=author_id,
        )

        # Record merge commit
        commit_result = await self._branch_manager.commit(
            branch_id=target.id,
            message=merge_message,
            author_id=author_id or "system",
            operation="merge",
            metadata={
                "merge_commit": merge_commit.to_dict(),
                "source_branch": source.id,
                "conflicts_resolved": len([c for c in conflicts if c.resolved]),
            },
        )

        if not commit_result.success:
            result.success = False
            result.status = MergeStatus.FAILED
            result.error = commit_result.error
            return result

        # Update source branch
        from lib.oda.ontology.objects.branch import BranchStatus
        source.branch_status = BranchStatus.MERGED
        source.merged_to_branch_id = target.id
        source.merged_at = _utc_now()
        source.merged_by = author_id

        result.success = True
        result.status = MergeStatus.COMPLETED
        result.merge_commit_id = merge_commit.id
        result.merged_commit_count = len(source_commits)
        result.completed_at = _utc_now()

        logger.info(
            f"Three-way merge completed: {source.id} -> {target.id}, "
            f"commits={len(source_commits)}, conflicts_resolved={len(conflicts)}"
        )

        return result
