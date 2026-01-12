"""
Orion ODA v4.0 - Transaction Framework
Palantir Foundry Compliant Transaction Management

This module provides:
- TransactionManager: ACID-compliant transaction management
- IsolationLevel: Configurable isolation levels
- @transactional: Decorator for automatic transaction handling
- BranchManager: Branch-based versioning system
- MergeStrategy: Three-way merge with conflict detection
- ConflictResolver: Automated and manual conflict resolution
- Checkpoint: Immutable state snapshots
- DiffEngine: Checkpoint comparison and diff application

Schema Version: 4.0.0
"""

# Transaction Manager
from lib.oda.transaction.manager import (
    TransactionManager,
    IsolationLevel,
    TransactionState,
    TransactionContext,
    Savepoint,
    get_transaction_manager,
    initialize_transaction_manager,
)

# Decorators
from lib.oda.transaction.decorators import (
    transactional,
    PropagationMode,
    TransactionOptions,
    requires_transaction,
    new_transaction,
    read_only,
    nested_transaction,
)

# Branching
from lib.oda.transaction.branching import (
    BranchManager,
    BranchStatus,
    BranchCreateResult,
    BranchCommitResult,
    CheckpointResult,
)

# Merge
from lib.oda.transaction.merge import (
    MergeStrategy,
    MergeResult,
    MergeStatus,
    MergeMode,
    MergeCommit,
    MergeConflict,
)

# Conflicts
from lib.oda.transaction.conflicts import (
    ConflictDetector,
    ConflictResolver,
    ConflictResolutionMode,
    ConflictType,
    ConflictSeverity,
    Conflict,
    ConflictResolution,
    ConflictBatch,
)

# Checkpoint (existing)
from lib.oda.transaction.checkpoint import (
    Checkpoint,
    CheckpointMetadata,
    CheckpointManager,
    CheckpointModel,
    ObjectSnapshot,
    SnapshotType,
)

# Diff (existing)
from lib.oda.transaction.diff import (
    ChangedObject,
    ChangeType,
    CheckpointDiff,
    DiffEngine,
    DiffMode,
    FieldChange,
)

__all__ = [
    # Manager
    "TransactionManager",
    "IsolationLevel",
    "TransactionState",
    "TransactionContext",
    "Savepoint",
    "get_transaction_manager",
    "initialize_transaction_manager",
    # Decorators
    "transactional",
    "PropagationMode",
    "TransactionOptions",
    "requires_transaction",
    "new_transaction",
    "read_only",
    "nested_transaction",
    # Branching
    "BranchManager",
    "BranchStatus",
    "BranchCreateResult",
    "BranchCommitResult",
    "CheckpointResult",
    # Merge
    "MergeStrategy",
    "MergeResult",
    "MergeStatus",
    "MergeMode",
    "MergeCommit",
    "MergeConflict",
    # Conflicts
    "ConflictDetector",
    "ConflictResolver",
    "ConflictResolutionMode",
    "ConflictType",
    "ConflictSeverity",
    "Conflict",
    "ConflictResolution",
    "ConflictBatch",
    # Checkpoint
    "Checkpoint",
    "CheckpointMetadata",
    "CheckpointManager",
    "CheckpointModel",
    "ObjectSnapshot",
    "SnapshotType",
    # Diff
    "ChangedObject",
    "ChangeType",
    "CheckpointDiff",
    "DiffEngine",
    "DiffMode",
    "FieldChange",
]
