"""
Orion ODA v4.0 - Branch ObjectType
Palantir Foundry Compliant Branch-Based Versioning

This module defines the Branch ObjectType for version control:
- Branch: Isolated workspace for changes
- BranchCheckpoint: Snapshot of branch state
- BranchCommit: Individual change within a branch

Design Principles:
1. Git-like branching semantics
2. Full audit trail of changes
3. Support for concurrent development
4. Merge and conflict resolution support
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field

from lib.oda.ontology.ontology_types import (
    Cardinality,
    Link,
    OntologyObject,
    utc_now,
)
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# ENUMS
# =============================================================================

class BranchStatus(str, Enum):
    """Branch lifecycle status."""
    ACTIVE = "active"           # Branch is active and accepting changes
    MERGED = "merged"           # Branch has been merged to target
    ABANDONED = "abandoned"     # Branch has been abandoned
    LOCKED = "locked"           # Branch is locked (no changes allowed)
    PENDING_MERGE = "pending_merge"  # Merge in progress


class CommitStatus(str, Enum):
    """Commit status within a branch."""
    PENDING = "pending"         # Commit not yet applied
    APPLIED = "applied"         # Commit applied to branch
    REVERTED = "reverted"       # Commit has been reverted
    CHERRY_PICKED = "cherry_picked"  # Commit cherry-picked from another branch


class CheckpointType(str, Enum):
    """Type of branch checkpoint."""
    AUTO = "auto"               # Automatic checkpoint (periodic)
    MANUAL = "manual"           # User-created checkpoint
    PRE_MERGE = "pre_merge"     # Checkpoint before merge
    POST_MERGE = "post_merge"   # Checkpoint after merge
    TAG = "tag"                 # Named tag/release


# =============================================================================
# BRANCH OBJECT TYPE
# =============================================================================

@register_object_type
class Branch(OntologyObject):
    """
    Represents an isolated workspace for changes.

    Branches allow parallel development and experimentation without
    affecting the main state. Changes can be merged or abandoned.

    Palantir Pattern:
    - Branches are first-class objects with full audit trail
    - Support for merge, rebase, and cherry-pick operations
    - Conflict detection and resolution during merge
    """
    # Required fields
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Branch name (e.g., 'feature/new-workflow')"
    )

    # Optional fields
    description: str = Field(
        default="",
        max_length=2000,
        description="Branch description/purpose"
    )

    # Status
    branch_status: BranchStatus = Field(
        default=BranchStatus.ACTIVE,
        description="Current branch status"
    )

    # Hierarchy
    parent_branch_id: Optional[str] = Field(
        default=None,
        description="ID of parent branch (null for main/trunk)"
    )
    base_commit_id: Optional[str] = Field(
        default=None,
        description="Commit ID this branch was created from"
    )

    # Merge tracking
    merged_to_branch_id: Optional[str] = Field(
        default=None,
        description="ID of branch this was merged into"
    )
    merged_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when branch was merged"
    )
    merged_by: Optional[str] = Field(
        default=None,
        description="Actor who performed the merge"
    )

    # Statistics
    commit_count: int = Field(
        default=0,
        ge=0,
        description="Number of commits in this branch"
    )
    ahead_count: int = Field(
        default=0,
        ge=0,
        description="Number of commits ahead of parent"
    )
    behind_count: int = Field(
        default=0,
        ge=0,
        description="Number of commits behind parent"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Tags/labels for the branch"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional branch metadata"
    )

    # Locking
    locked_at: Optional[datetime] = Field(
        default=None,
        description="When branch was locked"
    )
    locked_by: Optional[str] = Field(
        default=None,
        description="Who locked the branch"
    )
    lock_reason: Optional[str] = Field(
        default=None,
        description="Reason for locking"
    )

    # Link definitions
    parent_branch: ClassVar[Link["Branch"]] = Link(
        target="Branch",
        link_type_id="branch_parent",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="child_branches",
        description="Parent branch this was created from"
    )

    commits: ClassVar[Link["BranchCommit"]] = Link(
        target="BranchCommit",
        link_type_id="branch_commits",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="commit_branch",
        description="Commits in this branch"
    )

    checkpoints: ClassVar[Link["BranchCheckpoint"]] = Link(
        target="BranchCheckpoint",
        link_type_id="branch_checkpoints",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="checkpoint_branch",
        description="Checkpoints/snapshots of this branch"
    )

    @property
    def is_main(self) -> bool:
        """Check if this is the main/trunk branch."""
        return self.parent_branch_id is None

    @property
    def is_locked(self) -> bool:
        """Check if branch is locked."""
        return self.branch_status == BranchStatus.LOCKED

    @property
    def can_commit(self) -> bool:
        """Check if commits are allowed."""
        return self.branch_status == BranchStatus.ACTIVE

    @property
    def can_merge(self) -> bool:
        """Check if branch can be merged."""
        return self.branch_status in (BranchStatus.ACTIVE, BranchStatus.PENDING_MERGE)

    def lock(self, actor_id: str, reason: Optional[str] = None) -> None:
        """Lock the branch to prevent further changes."""
        self.branch_status = BranchStatus.LOCKED
        self.locked_at = utc_now()
        self.locked_by = actor_id
        self.lock_reason = reason
        self.touch(updated_by=actor_id)

    def unlock(self, actor_id: str) -> None:
        """Unlock the branch."""
        if self.branch_status == BranchStatus.LOCKED:
            self.branch_status = BranchStatus.ACTIVE
            self.locked_at = None
            self.locked_by = None
            self.lock_reason = None
            self.touch(updated_by=actor_id)


@register_object_type
class BranchCommit(OntologyObject):
    """
    Represents a single commit (change) within a branch.

    Commits capture:
    - What changed (object_type, object_id, operation)
    - Who made the change (author)
    - When (timestamp)
    - Previous and new state for undo capability
    """
    # Required fields
    branch_id: str = Field(
        ...,
        description="ID of the branch this commit belongs to"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Commit message describing the change"
    )

    # Author
    author_id: str = Field(
        ...,
        description="ID of the actor who made the commit"
    )

    # Status
    commit_status: CommitStatus = Field(
        default=CommitStatus.APPLIED,
        description="Current commit status"
    )

    # Change details
    object_type: str = Field(
        default="",
        description="Type of object modified"
    )
    object_id: Optional[str] = Field(
        default=None,
        description="ID of object modified"
    )
    operation: str = Field(
        default="update",
        description="Operation type: create, update, delete"
    )

    # State capture
    previous_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Object state before change"
    )
    new_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Object state after change"
    )
    diff: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Diff of changes (for large objects)"
    )

    # Sequence
    sequence_number: int = Field(
        default=0,
        ge=0,
        description="Commit sequence within branch"
    )
    parent_commit_id: Optional[str] = Field(
        default=None,
        description="ID of previous commit"
    )

    # Cherry-pick tracking
    source_commit_id: Optional[str] = Field(
        default=None,
        description="Original commit ID if cherry-picked"
    )
    source_branch_id: Optional[str] = Field(
        default=None,
        description="Original branch if cherry-picked"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Commit tags"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional commit metadata"
    )

    # Link to branch
    branch: ClassVar[Link[Branch]] = Link(
        target=Branch,
        link_type_id="commit_branch",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="branch_commits",
        description="Branch this commit belongs to"
    )

    @property
    def is_applied(self) -> bool:
        """Check if commit is applied."""
        return self.commit_status == CommitStatus.APPLIED

    @property
    def is_cherry_picked(self) -> bool:
        """Check if commit was cherry-picked."""
        return self.source_commit_id is not None


@register_object_type
class BranchCheckpoint(OntologyObject):
    """
    Represents a snapshot of branch state at a point in time.

    Checkpoints enable:
    - Rollback to previous state
    - Comparison between versions
    - Tagged releases

    Palantir Pattern:
    - Checkpoints are immutable once created
    - Store enough information to restore full state
    """
    # Required fields
    branch_id: str = Field(
        ...,
        description="ID of the branch this checkpoint belongs to"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Checkpoint name (e.g., 'v1.0.0', 'pre-merge-backup')"
    )

    # Type
    checkpoint_type: CheckpointType = Field(
        default=CheckpointType.MANUAL,
        description="Type of checkpoint"
    )

    # Optional fields
    description: str = Field(
        default="",
        max_length=2000,
        description="Checkpoint description"
    )

    # State
    commit_id: Optional[str] = Field(
        default=None,
        description="Commit ID at checkpoint"
    )
    commit_sequence: int = Field(
        default=0,
        ge=0,
        description="Commit sequence number at checkpoint"
    )

    # Full state snapshot (for critical checkpoints)
    state_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full state snapshot (for rollback)"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Checkpoint tags"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional checkpoint metadata"
    )

    # Link to branch
    branch: ClassVar[Link[Branch]] = Link(
        target=Branch,
        link_type_id="checkpoint_branch",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="branch_checkpoints",
        description="Branch this checkpoint belongs to"
    )

    @property
    def is_tag(self) -> bool:
        """Check if this is a named tag."""
        return self.checkpoint_type == CheckpointType.TAG

    @property
    def can_rollback(self) -> bool:
        """Check if rollback is possible."""
        return self.state_snapshot is not None or self.commit_id is not None
