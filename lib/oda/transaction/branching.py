"""
Orion ODA v4.0 - Branch Manager
Palantir Foundry Compliant Branch Operations

This module provides:
- BranchManager: Branch lifecycle management
- Branch creation, deletion, and status updates
- Checkpoint creation and management
- Commit tracking within branches

Design Principles:
1. Full audit trail for all branch operations
2. Transaction-safe branch modifications
3. Support for hierarchical branch structure
4. Integration with merge and conflict resolution
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from lib.oda.ontology.objects.branch import (
        Branch,
        BranchCommit,
        BranchCheckpoint,
    )

logger = logging.getLogger(__name__)


# Re-export BranchStatus for convenience
from lib.oda.ontology.objects.branch import (
    BranchStatus,
    CommitStatus,
    CheckpointType,
)

__all__ = [
    "BranchManager",
    "BranchStatus",
    "BranchCreateResult",
    "BranchCommitResult",
]


# =============================================================================
# RESULT TYPES
# =============================================================================

def _utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def _generate_id() -> str:
    """Generate unique identifier."""
    return uuid.uuid4().hex[:16]


@dataclass
class BranchCreateResult:
    """Result of branch creation."""
    success: bool
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    parent_branch_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "branch_id": self.branch_id,
            "branch_name": self.branch_name,
            "parent_branch_id": self.parent_branch_id,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class BranchCommitResult:
    """Result of commit operation."""
    success: bool
    commit_id: Optional[str] = None
    branch_id: Optional[str] = None
    sequence_number: int = 0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "commit_id": self.commit_id,
            "branch_id": self.branch_id,
            "sequence_number": self.sequence_number,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CheckpointResult:
    """Result of checkpoint creation."""
    success: bool
    checkpoint_id: Optional[str] = None
    branch_id: Optional[str] = None
    checkpoint_name: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "checkpoint_id": self.checkpoint_id,
            "branch_id": self.branch_id,
            "checkpoint_name": self.checkpoint_name,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# BRANCH MANAGER
# =============================================================================

class BranchManager:
    """
    Branch lifecycle management.

    Provides operations for:
    - Creating and deleting branches
    - Managing branch status
    - Recording commits
    - Creating checkpoints

    Usage:
        ```python
        manager = BranchManager(repository)

        # Create branch from parent
        result = await manager.create_branch(
            name="feature/new-api",
            parent_branch_id="main-branch-id",
            created_by="user-123"
        )

        # Record a commit
        commit = await manager.commit(
            branch_id=result.branch_id,
            message="Add new endpoint",
            author_id="user-123",
            object_type="APIEndpoint",
            object_id="endpoint-456",
            operation="create",
            new_state={"path": "/api/v2/users"}
        )

        # Create checkpoint before merge
        checkpoint = await manager.create_checkpoint(
            branch_id=result.branch_id,
            name="pre-merge-v1.0",
            checkpoint_type=CheckpointType.PRE_MERGE
        )
        ```
    """

    def __init__(
        self,
        repository: Any = None,  # BranchRepository - to be implemented
        default_main_branch_name: str = "main",
    ):
        """
        Initialize BranchManager.

        Args:
            repository: Optional repository for persistence
            default_main_branch_name: Name for the default main branch
        """
        self._repository = repository
        self._default_main_name = default_main_branch_name
        self._branches: Dict[str, "Branch"] = {}  # In-memory cache
        self._commits: Dict[str, List["BranchCommit"]] = {}  # branch_id -> commits
        self._checkpoints: Dict[str, List["BranchCheckpoint"]] = {}

    # =========================================================================
    # BRANCH OPERATIONS
    # =========================================================================

    async def create_branch(
        self,
        name: str,
        parent_branch_id: Optional[str] = None,
        description: str = "",
        created_by: Optional[str] = None,
        base_commit_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BranchCreateResult:
        """
        Create a new branch.

        Args:
            name: Branch name
            parent_branch_id: ID of parent branch (None for main)
            description: Branch description
            created_by: Actor creating the branch
            base_commit_id: Specific commit to branch from
            tags: Initial tags
            metadata: Additional metadata

        Returns:
            BranchCreateResult with success status
        """
        from lib.oda.ontology.objects.branch import Branch

        try:
            # Validate parent if specified
            if parent_branch_id and parent_branch_id not in self._branches:
                # Try to load from repository
                if self._repository:
                    parent = await self._repository.get(parent_branch_id)
                    if not parent:
                        return BranchCreateResult(
                            success=False,
                            error=f"Parent branch not found: {parent_branch_id}"
                        )
                    self._branches[parent_branch_id] = parent
                else:
                    return BranchCreateResult(
                        success=False,
                        error=f"Parent branch not found: {parent_branch_id}"
                    )

            # Determine base commit
            if not base_commit_id and parent_branch_id:
                # Get latest commit from parent
                parent_commits = self._commits.get(parent_branch_id, [])
                if parent_commits:
                    base_commit_id = parent_commits[-1].id

            # Create branch
            branch = Branch(
                name=name,
                description=description,
                parent_branch_id=parent_branch_id,
                base_commit_id=base_commit_id,
                created_by=created_by,
                tags=tags or [],
                metadata=metadata or {},
            )

            # Store in cache
            self._branches[branch.id] = branch
            self._commits[branch.id] = []
            self._checkpoints[branch.id] = []

            # Persist if repository available
            if self._repository:
                await self._repository.save(branch)

            logger.info(
                f"Branch created: id={branch.id}, name={name}, "
                f"parent={parent_branch_id}"
            )

            return BranchCreateResult(
                success=True,
                branch_id=branch.id,
                branch_name=name,
                parent_branch_id=parent_branch_id,
            )

        except Exception as e:
            logger.error(f"Branch creation failed: {e}")
            return BranchCreateResult(
                success=False,
                error=str(e)
            )

    async def get_branch(self, branch_id: str) -> Optional["Branch"]:
        """
        Get branch by ID.

        Args:
            branch_id: Branch identifier

        Returns:
            Branch or None if not found
        """
        if branch_id in self._branches:
            return self._branches[branch_id]

        if self._repository:
            branch = await self._repository.get(branch_id)
            if branch:
                self._branches[branch_id] = branch
            return branch

        return None

    async def get_branch_by_name(self, name: str) -> Optional["Branch"]:
        """
        Get branch by name.

        Args:
            name: Branch name

        Returns:
            Branch or None if not found
        """
        for branch in self._branches.values():
            if branch.name == name:
                return branch

        if self._repository:
            branch = await self._repository.get_by_name(name)
            if branch:
                self._branches[branch.id] = branch
            return branch

        return None

    async def list_branches(
        self,
        status: Optional[BranchStatus] = None,
        parent_branch_id: Optional[str] = None,
    ) -> List["Branch"]:
        """
        List branches with optional filters.

        Args:
            status: Filter by status
            parent_branch_id: Filter by parent

        Returns:
            List of matching branches
        """
        branches = list(self._branches.values())

        if status:
            branches = [b for b in branches if b.branch_status == status]

        if parent_branch_id:
            branches = [b for b in branches if b.parent_branch_id == parent_branch_id]

        return branches

    async def update_status(
        self,
        branch_id: str,
        new_status: BranchStatus,
        updated_by: Optional[str] = None,
    ) -> bool:
        """
        Update branch status.

        Args:
            branch_id: Branch to update
            new_status: New status
            updated_by: Actor performing update

        Returns:
            True if successful
        """
        branch = await self.get_branch(branch_id)
        if not branch:
            return False

        branch.branch_status = new_status
        branch.touch(updated_by=updated_by)

        if self._repository:
            await self._repository.save(branch)

        logger.info(f"Branch status updated: id={branch_id}, status={new_status.value}")
        return True

    async def delete_branch(
        self,
        branch_id: str,
        deleted_by: Optional[str] = None,
        force: bool = False,
    ) -> bool:
        """
        Delete (or soft-delete) a branch.

        Args:
            branch_id: Branch to delete
            deleted_by: Actor performing deletion
            force: Force delete even if not merged

        Returns:
            True if successful
        """
        branch = await self.get_branch(branch_id)
        if not branch:
            return False

        # Check if branch can be deleted
        if not force and branch.branch_status == BranchStatus.ACTIVE:
            # Check if there are unmerged commits
            commits = self._commits.get(branch_id, [])
            if commits:
                logger.warning(
                    f"Cannot delete branch with unmerged commits: {branch_id}"
                )
                return False

        # Soft delete
        branch.branch_status = BranchStatus.ABANDONED
        branch.soft_delete(deleted_by=deleted_by)

        if self._repository:
            await self._repository.save(branch)

        logger.info(f"Branch deleted: id={branch_id}")
        return True

    # =========================================================================
    # COMMIT OPERATIONS
    # =========================================================================

    async def commit(
        self,
        branch_id: str,
        message: str,
        author_id: str,
        object_type: str = "",
        object_id: Optional[str] = None,
        operation: str = "update",
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        diff: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BranchCommitResult:
        """
        Record a commit in the branch.

        Args:
            branch_id: Target branch
            message: Commit message
            author_id: Commit author
            object_type: Type of object modified
            object_id: ID of object modified
            operation: Operation type (create/update/delete)
            previous_state: State before change
            new_state: State after change
            diff: Computed diff
            tags: Commit tags
            metadata: Additional metadata

        Returns:
            BranchCommitResult with commit details
        """
        from lib.oda.ontology.objects.branch import BranchCommit

        try:
            branch = await self.get_branch(branch_id)
            if not branch:
                return BranchCommitResult(
                    success=False,
                    error=f"Branch not found: {branch_id}"
                )

            if not branch.can_commit:
                return BranchCommitResult(
                    success=False,
                    error=f"Branch is not accepting commits: {branch.branch_status.value}"
                )

            # Get commit sequence
            branch_commits = self._commits.get(branch_id, [])
            sequence_number = len(branch_commits) + 1
            parent_commit_id = branch_commits[-1].id if branch_commits else None

            # Create commit
            commit = BranchCommit(
                branch_id=branch_id,
                message=message,
                author_id=author_id,
                object_type=object_type,
                object_id=object_id,
                operation=operation,
                previous_state=previous_state,
                new_state=new_state,
                diff=diff,
                sequence_number=sequence_number,
                parent_commit_id=parent_commit_id,
                tags=tags or [],
                metadata=metadata or {},
            )

            # Store commit
            if branch_id not in self._commits:
                self._commits[branch_id] = []
            self._commits[branch_id].append(commit)

            # Update branch statistics
            branch.commit_count += 1
            branch.ahead_count += 1
            branch.touch(updated_by=author_id)

            if self._repository:
                await self._repository.save_commit(commit)
                await self._repository.save(branch)

            logger.debug(
                f"Commit recorded: id={commit.id}, branch={branch_id}, "
                f"seq={sequence_number}"
            )

            return BranchCommitResult(
                success=True,
                commit_id=commit.id,
                branch_id=branch_id,
                sequence_number=sequence_number,
            )

        except Exception as e:
            logger.error(f"Commit failed: {e}")
            return BranchCommitResult(
                success=False,
                error=str(e)
            )

    async def get_commits(
        self,
        branch_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List["BranchCommit"]:
        """
        Get commits for a branch.

        Args:
            branch_id: Target branch
            limit: Max commits to return
            offset: Skip first N commits

        Returns:
            List of commits (newest first)
        """
        commits = self._commits.get(branch_id, [])
        # Return in reverse order (newest first)
        commits = list(reversed(commits))
        return commits[offset:offset + limit]

    async def get_commit(self, commit_id: str) -> Optional["BranchCommit"]:
        """Get commit by ID."""
        for commits in self._commits.values():
            for commit in commits:
                if commit.id == commit_id:
                    return commit
        return None

    # =========================================================================
    # CHECKPOINT OPERATIONS
    # =========================================================================

    async def create_checkpoint(
        self,
        branch_id: str,
        name: str,
        checkpoint_type: CheckpointType = CheckpointType.MANUAL,
        description: str = "",
        state_snapshot: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckpointResult:
        """
        Create a checkpoint for the branch.

        Args:
            branch_id: Target branch
            name: Checkpoint name
            checkpoint_type: Type of checkpoint
            description: Checkpoint description
            state_snapshot: Optional full state snapshot
            created_by: Creator
            tags: Checkpoint tags
            metadata: Additional metadata

        Returns:
            CheckpointResult with checkpoint details
        """
        from lib.oda.ontology.objects.branch import BranchCheckpoint

        try:
            branch = await self.get_branch(branch_id)
            if not branch:
                return CheckpointResult(
                    success=False,
                    error=f"Branch not found: {branch_id}"
                )

            # Get current commit
            branch_commits = self._commits.get(branch_id, [])
            commit_id = branch_commits[-1].id if branch_commits else None
            commit_sequence = len(branch_commits)

            # Create checkpoint
            checkpoint = BranchCheckpoint(
                branch_id=branch_id,
                name=name,
                checkpoint_type=checkpoint_type,
                description=description,
                commit_id=commit_id,
                commit_sequence=commit_sequence,
                state_snapshot=state_snapshot,
                created_by=created_by,
                tags=tags or [],
                metadata=metadata or {},
            )

            # Store checkpoint
            if branch_id not in self._checkpoints:
                self._checkpoints[branch_id] = []
            self._checkpoints[branch_id].append(checkpoint)

            if self._repository:
                await self._repository.save_checkpoint(checkpoint)

            logger.info(
                f"Checkpoint created: id={checkpoint.id}, name={name}, "
                f"branch={branch_id}"
            )

            return CheckpointResult(
                success=True,
                checkpoint_id=checkpoint.id,
                branch_id=branch_id,
                checkpoint_name=name,
            )

        except Exception as e:
            logger.error(f"Checkpoint creation failed: {e}")
            return CheckpointResult(
                success=False,
                error=str(e)
            )

    async def get_checkpoints(
        self,
        branch_id: str,
        checkpoint_type: Optional[CheckpointType] = None,
    ) -> List["BranchCheckpoint"]:
        """
        Get checkpoints for a branch.

        Args:
            branch_id: Target branch
            checkpoint_type: Optional type filter

        Returns:
            List of checkpoints
        """
        checkpoints = self._checkpoints.get(branch_id, [])

        if checkpoint_type:
            checkpoints = [
                cp for cp in checkpoints
                if cp.checkpoint_type == checkpoint_type
            ]

        return checkpoints

    async def rollback_to_checkpoint(
        self,
        branch_id: str,
        checkpoint_id: str,
        actor_id: Optional[str] = None,
    ) -> bool:
        """
        Rollback branch to a checkpoint.

        Args:
            branch_id: Target branch
            checkpoint_id: Checkpoint to rollback to
            actor_id: Actor performing rollback

        Returns:
            True if successful
        """
        branch = await self.get_branch(branch_id)
        if not branch:
            return False

        checkpoints = self._checkpoints.get(branch_id, [])
        checkpoint = None
        for cp in checkpoints:
            if cp.id == checkpoint_id:
                checkpoint = cp
                break

        if not checkpoint:
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return False

        if not checkpoint.can_rollback:
            logger.error(f"Checkpoint cannot be rolled back: {checkpoint_id}")
            return False

        # Remove commits after checkpoint
        commits = self._commits.get(branch_id, [])
        rollback_index = checkpoint.commit_sequence
        removed_commits = commits[rollback_index:]
        self._commits[branch_id] = commits[:rollback_index]

        # Update branch
        branch.commit_count = rollback_index
        branch.touch(updated_by=actor_id)

        if self._repository:
            await self._repository.save(branch)

        logger.info(
            f"Branch rolled back: id={branch_id}, "
            f"checkpoint={checkpoint_id}, "
            f"commits_removed={len(removed_commits)}"
        )

        return True

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def get_main_branch(self) -> Optional["Branch"]:
        """Get the main/trunk branch."""
        return await self.get_branch_by_name(self._default_main_name)

    async def ensure_main_branch(
        self,
        created_by: Optional[str] = None,
    ) -> "Branch":
        """
        Ensure main branch exists, create if not.

        Args:
            created_by: Creator if creating

        Returns:
            Main branch
        """
        main = await self.get_main_branch()
        if main:
            return main

        result = await self.create_branch(
            name=self._default_main_name,
            description="Main/trunk branch",
            created_by=created_by,
        )

        if result.success and result.branch_id:
            return await self.get_branch(result.branch_id)

        raise RuntimeError(f"Failed to create main branch: {result.error}")

    async def get_branch_tree(
        self,
        root_branch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get branch hierarchy tree.

        Args:
            root_branch_id: Starting branch (None for main)

        Returns:
            Tree structure with branches
        """
        if root_branch_id is None:
            main = await self.get_main_branch()
            if not main:
                return {}
            root_branch_id = main.id

        root = await self.get_branch(root_branch_id)
        if not root:
            return {}

        children = await self.list_branches(parent_branch_id=root_branch_id)

        return {
            "id": root.id,
            "name": root.name,
            "status": root.branch_status.value,
            "commit_count": root.commit_count,
            "children": [
                await self.get_branch_tree(child.id)
                for child in children
            ],
        }
