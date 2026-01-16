"""
Orion ODA v4.0 - Conflict Resolution
Palantir Foundry Compliant Merge Conflict Handling

This module provides:
- ConflictDetector: Detect conflicts between changes
- ConflictResolver: Resolve conflicts using various strategies
- ConflictResolution: Record of how conflicts were resolved

Design Principles:
1. Multiple resolution strategies (ours, theirs, manual)
2. Field-level conflict granularity
3. Full audit trail of resolutions
4. Interactive and automatic resolution modes
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from lib.oda.ontology.objects.branch import BranchCommit
    from lib.oda.transaction.merge import MergeConflict

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ConflictResolutionMode(str, Enum):
    """Conflict resolution strategy."""
    OURS = "ours"           # Use source branch value
    THEIRS = "theirs"       # Use target branch value
    MANUAL = "manual"       # Manually specified value
    MERGE = "merge"         # Attempt to merge values (for compatible types)
    NEWER = "newer"         # Use more recently modified value
    OLDER = "older"         # Use less recently modified value
    SKIP = "skip"           # Skip this conflict (leave unresolved)


class ConflictType(str, Enum):
    """Type of conflict."""
    VALUE = "value"             # Same field, different values
    DELETE_UPDATE = "delete_update"  # One deleted, other updated
    CREATE_CREATE = "create_create"  # Both created same object
    SCHEMA = "schema"           # Incompatible schema changes


class ConflictSeverity(str, Enum):
    """Severity of conflict."""
    LOW = "low"             # Can be auto-resolved
    MEDIUM = "medium"       # Requires attention but non-breaking
    HIGH = "high"           # Requires manual resolution
    CRITICAL = "critical"   # Blocking, must resolve


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
class Conflict:
    """
    Represents a merge conflict.

    Captures:
    - What conflicted (object, field)
    - Values from both sides and base
    - Resolution status and outcome
    """
    id: str = field(default_factory=_generate_id)

    # Location
    object_type: str = ""
    object_id: str = ""
    field_name: str = ""

    # Conflict type
    conflict_type: ConflictType = ConflictType.VALUE
    severity: ConflictSeverity = ConflictSeverity.MEDIUM

    # Values
    source_value: Any = None      # Value from source branch (ours)
    target_value: Any = None      # Value from target branch (theirs)
    base_value: Any = None        # Value from common ancestor
    resolved_value: Any = None    # Final resolved value

    # Context
    source_commit_id: Optional[str] = None
    target_commit_id: Optional[str] = None
    source_timestamp: Optional[datetime] = None
    target_timestamp: Optional[datetime] = None

    # Resolution
    resolved: bool = False
    resolution_mode: Optional[ConflictResolutionMode] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""

    # Metadata
    detected_at: datetime = field(default_factory=_utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_auto_resolvable(self) -> bool:
        """Check if conflict can be auto-resolved."""
        return self.severity in (ConflictSeverity.LOW,)

    @property
    def key(self) -> str:
        """Unique key for this conflict."""
        return f"{self.object_type}:{self.object_id}:{self.field_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "field_name": self.field_name,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "base_value": self.base_value,
            "resolved_value": self.resolved_value,
            "source_commit_id": self.source_commit_id,
            "target_commit_id": self.target_commit_id,
            "resolved": self.resolved,
            "resolution_mode": self.resolution_mode.value if self.resolution_mode else None,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class ConflictResolution:
    """
    Record of how a conflict was resolved.

    Used for audit and replay purposes.
    """
    id: str = field(default_factory=_generate_id)
    conflict_id: str = ""
    conflict_key: str = ""

    # Resolution details
    mode: ConflictResolutionMode = ConflictResolutionMode.MANUAL
    original_source_value: Any = None
    original_target_value: Any = None
    resolved_value: Any = None

    # Actor
    resolved_by: Optional[str] = None
    resolved_at: datetime = field(default_factory=_utc_now)
    notes: str = ""

    # Context
    merge_id: Optional[str] = None
    branch_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conflict_id": self.conflict_id,
            "conflict_key": self.conflict_key,
            "mode": self.mode.value,
            "original_source_value": self.original_source_value,
            "original_target_value": self.original_target_value,
            "resolved_value": self.resolved_value,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat(),
            "notes": self.notes,
            "merge_id": self.merge_id,
            "branch_id": self.branch_id,
        }


@dataclass
class ConflictBatch:
    """A batch of conflicts from a merge operation."""
    id: str = field(default_factory=_generate_id)
    merge_id: Optional[str] = None
    source_branch_id: Optional[str] = None
    target_branch_id: Optional[str] = None
    conflicts: List[Conflict] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)

    @property
    def total_count(self) -> int:
        return len(self.conflicts)

    @property
    def resolved_count(self) -> int:
        return len([c for c in self.conflicts if c.resolved])

    @property
    def unresolved_count(self) -> int:
        return self.total_count - self.resolved_count

    @property
    def all_resolved(self) -> bool:
        return self.unresolved_count == 0

    def get_by_severity(self, severity: ConflictSeverity) -> List[Conflict]:
        return [c for c in self.conflicts if c.severity == severity]


# =============================================================================
# CONFLICT DETECTOR
# =============================================================================

class ConflictDetector:
    """
    Detect conflicts between changes.

    Analyzes commits from two branches to find:
    - Value conflicts (same field, different values)
    - Delete/Update conflicts
    - Create/Create conflicts
    - Schema conflicts

    Usage:
        ```python
        detector = ConflictDetector()

        # Detect conflicts between commit sets
        conflicts = detector.detect_conflicts(
            source_commits=source_commits,
            target_commits=target_commits,
            common_ancestor_state=ancestor_state
        )

        # Classify severity
        for conflict in conflicts:
            detector.classify_severity(conflict)
        ```
    """

    def __init__(
        self,
        auto_resolve_low: bool = True,
        custom_resolvers: Optional[Dict[str, Callable]] = None,
    ):
        """
        Initialize ConflictDetector.

        Args:
            auto_resolve_low: Auto-resolve LOW severity conflicts
            custom_resolvers: Custom resolution functions by field pattern
        """
        self._auto_resolve_low = auto_resolve_low
        self._custom_resolvers = custom_resolvers or {}

    def detect_conflicts(
        self,
        source_commits: List["BranchCommit"],
        target_commits: List["BranchCommit"],
        common_ancestor_state: Optional[Dict[str, Any]] = None,
    ) -> List[Conflict]:
        """
        Detect conflicts between two sets of commits.

        Args:
            source_commits: Commits from source branch
            target_commits: Commits from target branch
            common_ancestor_state: State at common ancestor (for three-way)

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Build change maps
        source_changes = self._build_change_map(source_commits)
        target_changes = self._build_change_map(target_commits)

        # Find overlapping changes
        overlapping_keys = set(source_changes.keys()) & set(target_changes.keys())

        for key in overlapping_keys:
            source_change = source_changes[key]
            target_change = target_changes[key]

            # Detect field-level conflicts
            field_conflicts = self._detect_field_conflicts(
                source_change, target_change, common_ancestor_state
            )
            conflicts.extend(field_conflicts)

        # Detect delete/update conflicts
        delete_conflicts = self._detect_delete_update_conflicts(
            source_changes, target_changes
        )
        conflicts.extend(delete_conflicts)

        # Classify severity for each conflict
        for conflict in conflicts:
            self._classify_severity(conflict)

        return conflicts

    def _build_change_map(
        self,
        commits: List["BranchCommit"],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a map of changes from commits.

        Key: "object_type:object_id"
        Value: Change details including field changes
        """
        changes: Dict[str, Dict[str, Any]] = {}

        for commit in commits:
            if not commit.object_id:
                continue

            key = f"{commit.object_type}:{commit.object_id}"

            if key not in changes:
                changes[key] = {
                    "object_type": commit.object_type,
                    "object_id": commit.object_id,
                    "operations": [],
                    "field_changes": {},
                    "latest_commit_id": commit.id,
                    "latest_timestamp": commit.created_at,
                }

            # Track operations
            changes[key]["operations"].append(commit.operation)
            changes[key]["latest_commit_id"] = commit.id
            changes[key]["latest_timestamp"] = commit.created_at

            # Track field changes
            if commit.new_state:
                for field_name, value in commit.new_state.items():
                    changes[key]["field_changes"][field_name] = {
                        "value": value,
                        "commit_id": commit.id,
                        "timestamp": commit.created_at,
                    }

        return changes

    def _detect_field_conflicts(
        self,
        source_change: Dict[str, Any],
        target_change: Dict[str, Any],
        ancestor_state: Optional[Dict[str, Any]],
    ) -> List[Conflict]:
        """Detect field-level conflicts between two changes."""
        conflicts = []

        source_fields = source_change.get("field_changes", {})
        target_fields = target_change.get("field_changes", {})

        # Check overlapping field changes
        overlapping_fields = set(source_fields.keys()) & set(target_fields.keys())

        for field_name in overlapping_fields:
            source_data = source_fields[field_name]
            target_data = target_fields[field_name]

            source_value = source_data.get("value")
            target_value = target_data.get("value")

            # Check if values differ
            if source_value != target_value:
                # Get base value if available
                base_value = None
                if ancestor_state:
                    obj_key = f"{source_change['object_type']}:{source_change['object_id']}"
                    obj_state = ancestor_state.get(obj_key, {})
                    base_value = obj_state.get(field_name)

                conflict = Conflict(
                    object_type=source_change["object_type"],
                    object_id=source_change["object_id"],
                    field_name=field_name,
                    conflict_type=ConflictType.VALUE,
                    source_value=source_value,
                    target_value=target_value,
                    base_value=base_value,
                    source_commit_id=source_data.get("commit_id"),
                    target_commit_id=target_data.get("commit_id"),
                    source_timestamp=source_data.get("timestamp"),
                    target_timestamp=target_data.get("timestamp"),
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_delete_update_conflicts(
        self,
        source_changes: Dict[str, Dict[str, Any]],
        target_changes: Dict[str, Dict[str, Any]],
    ) -> List[Conflict]:
        """Detect delete/update conflicts."""
        conflicts = []

        for key, source_change in source_changes.items():
            if key not in target_changes:
                continue

            target_change = target_changes[key]
            source_ops = source_change.get("operations", [])
            target_ops = target_change.get("operations", [])

            # Check for delete/update conflict
            source_deleted = "delete" in source_ops
            target_deleted = "delete" in target_ops
            source_updated = "update" in source_ops or "create" in source_ops
            target_updated = "update" in target_ops or "create" in target_ops

            if (source_deleted and target_updated) or (source_updated and target_deleted):
                conflict = Conflict(
                    object_type=source_change["object_type"],
                    object_id=source_change["object_id"],
                    field_name="__object__",
                    conflict_type=ConflictType.DELETE_UPDATE,
                    severity=ConflictSeverity.HIGH,
                    source_commit_id=source_change.get("latest_commit_id"),
                    target_commit_id=target_change.get("latest_commit_id"),
                    metadata={
                        "source_deleted": source_deleted,
                        "target_deleted": target_deleted,
                    },
                )
                conflicts.append(conflict)

        return conflicts

    def _classify_severity(self, conflict: Conflict) -> None:
        """Classify conflict severity based on type and field."""
        # Delete/Update conflicts are always HIGH
        if conflict.conflict_type == ConflictType.DELETE_UPDATE:
            conflict.severity = ConflictSeverity.HIGH
            return

        # Schema conflicts are CRITICAL
        if conflict.conflict_type == ConflictType.SCHEMA:
            conflict.severity = ConflictSeverity.CRITICAL
            return

        # Value conflicts - check if auto-resolvable
        if conflict.conflict_type == ConflictType.VALUE:
            # If base value matches one side, it's auto-resolvable
            if conflict.base_value is not None:
                if conflict.base_value == conflict.source_value:
                    # Only target changed - use target (THEIRS)
                    conflict.severity = ConflictSeverity.LOW
                    return
                if conflict.base_value == conflict.target_value:
                    # Only source changed - use source (OURS)
                    conflict.severity = ConflictSeverity.LOW
                    return

            # Both changed - requires attention
            conflict.severity = ConflictSeverity.MEDIUM


# =============================================================================
# CONFLICT RESOLVER
# =============================================================================

class ConflictResolver:
    """
    Resolve conflicts using various strategies.

    Supports:
    - Automatic resolution (ours, theirs, newer, older)
    - Manual resolution with custom values
    - Batch resolution
    - Custom resolution functions

    Usage:
        ```python
        resolver = ConflictResolver()

        # Resolve single conflict
        resolution = resolver.resolve(
            conflict=conflict,
            mode=ConflictResolutionMode.THEIRS,
            resolved_by="user-123"
        )

        # Batch resolve with same strategy
        resolutions = resolver.resolve_batch(
            conflicts=conflicts,
            mode=ConflictResolutionMode.OURS,
            resolved_by="user-123"
        )

        # Auto-resolve where possible
        auto_resolved, remaining = resolver.auto_resolve(conflicts)
        ```
    """

    def __init__(
        self,
        custom_resolvers: Optional[Dict[str, Callable]] = None,
    ):
        """
        Initialize ConflictResolver.

        Args:
            custom_resolvers: Custom resolution functions by pattern
                             e.g., {"*.timestamp": lambda c: c.target_value}
        """
        self._custom_resolvers = custom_resolvers or {}
        self._resolutions: List[ConflictResolution] = []

    def resolve(
        self,
        conflict: Conflict,
        mode: ConflictResolutionMode,
        resolved_by: Optional[str] = None,
        custom_value: Any = None,
        notes: str = "",
    ) -> ConflictResolution:
        """
        Resolve a single conflict.

        Args:
            conflict: Conflict to resolve
            mode: Resolution strategy
            resolved_by: Actor resolving
            custom_value: Custom value for MANUAL mode
            notes: Resolution notes

        Returns:
            ConflictResolution record
        """
        # Determine resolved value based on mode
        if mode == ConflictResolutionMode.OURS:
            resolved_value = conflict.source_value
        elif mode == ConflictResolutionMode.THEIRS:
            resolved_value = conflict.target_value
        elif mode == ConflictResolutionMode.MANUAL:
            if custom_value is None:
                raise ValueError("custom_value required for MANUAL resolution")
            resolved_value = custom_value
        elif mode == ConflictResolutionMode.NEWER:
            resolved_value = self._resolve_newer(conflict)
        elif mode == ConflictResolutionMode.OLDER:
            resolved_value = self._resolve_older(conflict)
        elif mode == ConflictResolutionMode.MERGE:
            resolved_value = self._resolve_merge(conflict)
        elif mode == ConflictResolutionMode.SKIP:
            resolved_value = None
        else:
            raise ValueError(f"Unknown resolution mode: {mode}")

        # Update conflict
        conflict.resolved = True
        conflict.resolution_mode = mode
        conflict.resolved_value = resolved_value
        conflict.resolved_by = resolved_by
        conflict.resolved_at = _utc_now()
        conflict.resolution_notes = notes

        # Create resolution record
        resolution = ConflictResolution(
            conflict_id=conflict.id,
            conflict_key=conflict.key,
            mode=mode,
            original_source_value=conflict.source_value,
            original_target_value=conflict.target_value,
            resolved_value=resolved_value,
            resolved_by=resolved_by,
            notes=notes,
        )

        self._resolutions.append(resolution)

        logger.debug(
            f"Conflict resolved: {conflict.key}, mode={mode.value}, "
            f"by={resolved_by}"
        )

        return resolution

    def resolve_batch(
        self,
        conflicts: List[Conflict],
        mode: ConflictResolutionMode,
        resolved_by: Optional[str] = None,
        notes: str = "",
    ) -> List[ConflictResolution]:
        """
        Resolve multiple conflicts with same strategy.

        Args:
            conflicts: Conflicts to resolve
            mode: Resolution strategy for all
            resolved_by: Actor resolving
            notes: Resolution notes

        Returns:
            List of resolution records
        """
        resolutions = []

        for conflict in conflicts:
            if not conflict.resolved:
                resolution = self.resolve(
                    conflict=conflict,
                    mode=mode,
                    resolved_by=resolved_by,
                    notes=notes,
                )
                resolutions.append(resolution)

        logger.info(
            f"Batch resolved {len(resolutions)} conflicts with {mode.value}"
        )

        return resolutions

    def auto_resolve(
        self,
        conflicts: List[Conflict],
        resolved_by: str = "auto",
    ) -> tuple[List[Conflict], List[Conflict]]:
        """
        Automatically resolve conflicts where possible.

        Uses heuristics:
        - LOW severity: resolve based on base value comparison
        - Custom resolvers: apply matching patterns

        Args:
            conflicts: Conflicts to process
            resolved_by: Attribution for auto resolutions

        Returns:
            Tuple of (resolved_conflicts, remaining_conflicts)
        """
        resolved = []
        remaining = []

        for conflict in conflicts:
            if conflict.resolved:
                resolved.append(conflict)
                continue

            # Try auto-resolution
            auto_resolved = self._try_auto_resolve(conflict, resolved_by)

            if auto_resolved:
                resolved.append(conflict)
            else:
                remaining.append(conflict)

        logger.info(
            f"Auto-resolve: {len(resolved)} resolved, {len(remaining)} remaining"
        )

        return resolved, remaining

    def _try_auto_resolve(
        self,
        conflict: Conflict,
        resolved_by: str,
    ) -> bool:
        """
        Try to auto-resolve a single conflict.

        Returns True if resolved.
        """
        # Check custom resolvers first
        for pattern, resolver_fn in self._custom_resolvers.items():
            if self._matches_pattern(conflict, pattern):
                try:
                    value = resolver_fn(conflict)
                    self.resolve(
                        conflict=conflict,
                        mode=ConflictResolutionMode.MANUAL,
                        custom_value=value,
                        resolved_by=resolved_by,
                        notes=f"Auto-resolved by custom resolver: {pattern}",
                    )
                    return True
                except Exception as e:
                    logger.warning(f"Custom resolver failed: {e}")

        # Check if base-value based resolution is possible
        if conflict.base_value is not None:
            if conflict.base_value == conflict.source_value:
                # Only target changed - use THEIRS
                self.resolve(
                    conflict=conflict,
                    mode=ConflictResolutionMode.THEIRS,
                    resolved_by=resolved_by,
                    notes="Auto-resolved: only target branch changed",
                )
                return True

            if conflict.base_value == conflict.target_value:
                # Only source changed - use OURS
                self.resolve(
                    conflict=conflict,
                    mode=ConflictResolutionMode.OURS,
                    resolved_by=resolved_by,
                    notes="Auto-resolved: only source branch changed",
                )
                return True

        # LOW severity conflicts can be resolved with NEWER
        if conflict.severity == ConflictSeverity.LOW:
            self.resolve(
                conflict=conflict,
                mode=ConflictResolutionMode.NEWER,
                resolved_by=resolved_by,
                notes="Auto-resolved: using newer value",
            )
            return True

        return False

    def _matches_pattern(self, conflict: Conflict, pattern: str) -> bool:
        """Check if conflict matches a pattern."""
        import fnmatch

        # Pattern can match object_type, field_name, or combination
        key = f"{conflict.object_type}.{conflict.field_name}"
        return fnmatch.fnmatch(key, pattern) or fnmatch.fnmatch(conflict.field_name, pattern)

    def _resolve_newer(self, conflict: Conflict) -> Any:
        """Resolve by using more recent value."""
        source_ts = conflict.source_timestamp
        target_ts = conflict.target_timestamp

        if source_ts and target_ts:
            return conflict.source_value if source_ts > target_ts else conflict.target_value
        elif source_ts:
            return conflict.source_value
        elif target_ts:
            return conflict.target_value
        else:
            # Default to target if no timestamps
            return conflict.target_value

    def _resolve_older(self, conflict: Conflict) -> Any:
        """Resolve by using older value."""
        source_ts = conflict.source_timestamp
        target_ts = conflict.target_timestamp

        if source_ts and target_ts:
            return conflict.source_value if source_ts < target_ts else conflict.target_value
        elif source_ts:
            return conflict.target_value
        elif target_ts:
            return conflict.source_value
        else:
            # Default to source if no timestamps
            return conflict.source_value

    def _resolve_merge(self, conflict: Conflict) -> Any:
        """
        Attempt to merge values (for compatible types).

        Works for:
        - Lists: combine unique elements
        - Dicts: merge keys
        - Sets: union
        """
        source = conflict.source_value
        target = conflict.target_value

        # Lists - combine unique
        if isinstance(source, list) and isinstance(target, list):
            merged = list(source)
            for item in target:
                if item not in merged:
                    merged.append(item)
            return merged

        # Dicts - merge
        if isinstance(source, dict) and isinstance(target, dict):
            merged = dict(source)
            merged.update(target)  # Target wins for overlapping keys
            return merged

        # Sets - union
        if isinstance(source, set) and isinstance(target, set):
            return source | target

        # Can't merge - return target
        return target

    def get_resolutions(self) -> List[ConflictResolution]:
        """Get all resolution records."""
        return list(self._resolutions)

    def clear_resolutions(self) -> None:
        """Clear resolution history."""
        self._resolutions.clear()
