"""
Orion ODA v4.0 - Property Change Tracking
==========================================

Provides change tracking for OntologyObjects with:
- Individual property change records
- ChangeSets for grouped changes
- Automatic tracking via mixin
- Diff generation between object states

Palantir Pattern:
- All changes to ObjectTypes are tracked
- ChangeSets group related changes into atomic units
- Audit trail for compliance and debugging

Example:
    ```python
    class User(OntologyObject, ChangeTrackingMixin):
        name: str
        email: str

    user = User(name="John", email="john@example.com")
    user.start_tracking()

    user.name = "Jane"
    user.email = "jane@example.com"

    changes = user.get_pending_changes()
    # [PropertyChange(property="name", old="John", new="Jane"), ...]
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


# =============================================================================
# ENUMS
# =============================================================================


class ChangeType(str, Enum):
    """Type of property change."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ChangeStatus(str, Enum):
    """Status of a change in the tracking lifecycle."""
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"


# =============================================================================
# PROPERTY CHANGE
# =============================================================================


@dataclass
class PropertyChange:
    """
    Represents a single property change.

    Attributes:
        property_name: Name of the changed property
        old_value: Previous value (None for create)
        new_value: New value (None for delete)
        change_type: Type of change (create, update, delete)
        timestamp: When the change occurred
        changed_by: ID of actor who made the change
    """
    property_name: str
    old_value: Any
    new_value: Any
    change_type: ChangeType = ChangeType.UPDATE
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    changed_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "property_name": self.property_name,
            "old_value": self._serialize_value(self.old_value),
            "new_value": self._serialize_value(self.new_value),
            "change_type": self.change_type.value,
            "timestamp": self.timestamp.isoformat(),
            "changed_by": self.changed_by,
        }

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize a value for JSON storage."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, (list, tuple)):
            return [PropertyChange._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: PropertyChange._serialize_value(v) for k, v in value.items()}
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return value

    @property
    def is_significant(self) -> bool:
        """Check if this is a significant (non-trivial) change."""
        if self.change_type == ChangeType.CREATE:
            return self.new_value is not None
        if self.change_type == ChangeType.DELETE:
            return self.old_value is not None
        return self.old_value != self.new_value


# =============================================================================
# CHANGE SET
# =============================================================================


class ChangeSet(BaseModel):
    """
    Groups related property changes into an atomic unit.

    Palantir Pattern:
    - ChangeSets represent a single logical operation
    - All changes in a ChangeSet succeed or fail together
    - ChangeSets are immutable after commit

    Example:
        ```python
        change_set = ChangeSet(
            object_id="user-123",
            object_type="User",
            changes=[
                PropertyChange("name", "John", "Jane"),
                PropertyChange("email", "john@ex.com", "jane@ex.com"),
            ]
        )
        ```
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    # Identity
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this ChangeSet"
    )

    # Target object
    object_id: str = Field(
        ...,
        description="ID of the object being changed"
    )
    object_type: str = Field(
        ...,
        description="Type name of the object being changed"
    )

    # Changes
    changes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of property changes (serialized)"
    )

    # Status
    status: ChangeStatus = Field(
        default=ChangeStatus.PENDING,
        description="Current status of this ChangeSet"
    )

    # Audit
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    created_by: Optional[str] = Field(default=None)
    committed_at: Optional[datetime] = Field(default=None)
    committed_by: Optional[str] = Field(default=None)

    # Metadata
    description: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)

    def add_change(self, change: PropertyChange) -> None:
        """Add a property change to this ChangeSet."""
        if self.status != ChangeStatus.PENDING:
            raise ValueError("Cannot modify a committed or rolled-back ChangeSet")
        self.changes.append(change.to_dict())

    def commit(self, committed_by: Optional[str] = None) -> None:
        """Mark this ChangeSet as committed."""
        self.status = ChangeStatus.COMMITTED
        self.committed_at = datetime.now(timezone.utc)
        self.committed_by = committed_by

    def rollback(self) -> None:
        """Mark this ChangeSet as rolled back."""
        self.status = ChangeStatus.ROLLED_BACK

    @property
    def change_count(self) -> int:
        """Get the number of changes in this ChangeSet."""
        return len(self.changes)

    @property
    def changed_properties(self) -> Set[str]:
        """Get the set of property names that were changed."""
        return {c["property_name"] for c in self.changes}

    def to_json(self) -> str:
        """Serialize ChangeSet to JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ChangeSet":
        """Deserialize ChangeSet from JSON string."""
        return cls.model_validate_json(json_str)


# =============================================================================
# CHANGE TRACKER
# =============================================================================


class ChangeTracker(Generic[T]):
    """
    Tracks changes to an object by comparing snapshots.

    The tracker maintains:
    - Original snapshot (state at start of tracking)
    - Current state (live object reference)
    - Pending changes (uncommitted modifications)

    Example:
        ```python
        user = User(name="John", email="john@example.com")
        tracker = ChangeTracker(user)

        user.name = "Jane"

        changes = tracker.get_changes()
        # [PropertyChange(property="name", old="John", new="Jane")]

        tracker.commit()  # Accept changes, update snapshot
        ```
    """

    def __init__(
        self,
        obj: T,
        tracked_properties: Optional[Set[str]] = None,
        ignore_properties: Optional[Set[str]] = None,
    ) -> None:
        """
        Initialize the change tracker.

        Args:
            obj: Object to track changes for
            tracked_properties: Only track these properties (None = all)
            ignore_properties: Never track these properties
        """
        self._obj = obj
        self._tracked = tracked_properties
        self._ignored = ignore_properties or {"updated_at", "version"}

        # Take initial snapshot
        self._snapshot = self._take_snapshot()
        self._pending_changes: List[PropertyChange] = []
        self._tracking_enabled = True

    def _take_snapshot(self) -> Dict[str, Any]:
        """Take a snapshot of the current object state."""
        if hasattr(self._obj, "model_dump"):
            data = self._obj.model_dump()
        elif hasattr(self._obj, "__dict__"):
            data = copy.deepcopy(self._obj.__dict__)
        else:
            data = {}

        # Filter to tracked properties
        if self._tracked:
            data = {k: v for k, v in data.items() if k in self._tracked}

        # Remove ignored properties
        for prop in self._ignored:
            data.pop(prop, None)

        return data

    def get_changes(self) -> List[PropertyChange]:
        """
        Get all changes since the last snapshot/commit.

        Returns:
            List of PropertyChange objects for modified properties
        """
        if not self._tracking_enabled:
            return []

        current = self._take_snapshot()
        changes: List[PropertyChange] = []

        # Check for updated and deleted properties
        for prop_name, old_value in self._snapshot.items():
            if prop_name not in current:
                changes.append(PropertyChange(
                    property_name=prop_name,
                    old_value=old_value,
                    new_value=None,
                    change_type=ChangeType.DELETE,
                ))
            elif current[prop_name] != old_value:
                changes.append(PropertyChange(
                    property_name=prop_name,
                    old_value=old_value,
                    new_value=current[prop_name],
                    change_type=ChangeType.UPDATE,
                ))

        # Check for new properties
        for prop_name, new_value in current.items():
            if prop_name not in self._snapshot:
                changes.append(PropertyChange(
                    property_name=prop_name,
                    old_value=None,
                    new_value=new_value,
                    change_type=ChangeType.CREATE,
                ))

        return changes

    def has_changes(self) -> bool:
        """Check if there are any uncommitted changes."""
        return len(self.get_changes()) > 0

    def commit(self, changed_by: Optional[str] = None) -> ChangeSet:
        """
        Commit current changes and update snapshot.

        Args:
            changed_by: ID of actor committing the changes

        Returns:
            ChangeSet containing the committed changes
        """
        changes = self.get_changes()

        # Create ChangeSet
        object_id = getattr(self._obj, "id", str(id(self._obj)))
        object_type = self._obj.__class__.__name__

        change_set = ChangeSet(
            object_id=object_id,
            object_type=object_type,
            created_by=changed_by,
        )

        for change in changes:
            change.changed_by = changed_by
            change_set.add_change(change)

        change_set.commit(committed_by=changed_by)

        # Update snapshot
        self._snapshot = self._take_snapshot()

        return change_set

    def rollback(self) -> None:
        """
        Rollback to the last snapshot state.

        Note: This only works if the object supports __setattr__ for all properties.
        """
        for prop_name, old_value in self._snapshot.items():
            if hasattr(self._obj, prop_name):
                setattr(self._obj, prop_name, old_value)

    def reset(self) -> None:
        """Reset the tracker by taking a new snapshot."""
        self._snapshot = self._take_snapshot()

    def pause_tracking(self) -> None:
        """Temporarily pause change tracking."""
        self._tracking_enabled = False

    def resume_tracking(self) -> None:
        """Resume change tracking."""
        self._tracking_enabled = True

    @property
    def is_tracking(self) -> bool:
        """Check if tracking is enabled."""
        return self._tracking_enabled


# =============================================================================
# CHANGE TRACKING MIXIN
# =============================================================================


class ChangeTrackingMixin:
    """
    Mixin that adds change tracking capabilities to OntologyObjects.

    Provides automatic change tracking through __setattr__ interception.

    Example:
        ```python
        class User(OntologyObject, ChangeTrackingMixin):
            name: str
            email: str

        user = User(name="John", email="john@example.com")
        user.start_tracking()

        user.name = "Jane"

        if user.has_pending_changes():
            changes = user.get_pending_changes()
            user.commit_changes()
        ```
    """

    _change_tracker: Optional[ChangeTracker] = None
    _tracking_started: bool = False

    def start_tracking(
        self,
        tracked_properties: Optional[Set[str]] = None,
        ignore_properties: Optional[Set[str]] = None,
    ) -> None:
        """
        Start tracking changes to this object.

        Args:
            tracked_properties: Only track these properties (None = all)
            ignore_properties: Never track these properties
        """
        default_ignored = {"updated_at", "version", "_change_tracker", "_tracking_started"}
        ignore = (ignore_properties or set()) | default_ignored

        self._change_tracker = ChangeTracker(
            self,
            tracked_properties=tracked_properties,
            ignore_properties=ignore,
        )
        self._tracking_started = True

    def stop_tracking(self) -> None:
        """Stop tracking changes to this object."""
        self._change_tracker = None
        self._tracking_started = False

    def get_pending_changes(self) -> List[PropertyChange]:
        """Get all pending (uncommitted) changes."""
        if self._change_tracker:
            return self._change_tracker.get_changes()
        return []

    def has_pending_changes(self) -> bool:
        """Check if there are any pending changes."""
        if self._change_tracker:
            return self._change_tracker.has_changes()
        return False

    def commit_changes(self, changed_by: Optional[str] = None) -> Optional[ChangeSet]:
        """
        Commit all pending changes.

        Args:
            changed_by: ID of actor committing the changes

        Returns:
            ChangeSet if there were changes to commit, None otherwise
        """
        if self._change_tracker and self._change_tracker.has_changes():
            return self._change_tracker.commit(changed_by=changed_by)
        return None

    def rollback_changes(self) -> None:
        """Rollback all pending changes to the last committed state."""
        if self._change_tracker:
            self._change_tracker.rollback()

    def reset_tracking(self) -> None:
        """Reset the tracker by taking a new snapshot (discards pending changes)."""
        if self._change_tracker:
            self._change_tracker.reset()

    @property
    def is_tracking(self) -> bool:
        """Check if change tracking is enabled."""
        return self._tracking_started and self._change_tracker is not None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_changes(obj: Any) -> List[PropertyChange]:
    """
    Get changes for an object (works with mixin or standalone tracker).

    Args:
        obj: Object to get changes for

    Returns:
        List of PropertyChange objects
    """
    if isinstance(obj, ChangeTrackingMixin):
        return obj.get_pending_changes()
    if hasattr(obj, "_change_tracker") and obj._change_tracker:
        return obj._change_tracker.get_changes()
    return []


def has_changes(obj: Any) -> bool:
    """
    Check if an object has pending changes.

    Args:
        obj: Object to check

    Returns:
        True if there are pending changes
    """
    return len(get_changes(obj)) > 0


def diff_objects(old_obj: Any, new_obj: Any) -> List[PropertyChange]:
    """
    Generate a diff between two objects of the same type.

    Args:
        old_obj: Original object state
        new_obj: New object state

    Returns:
        List of PropertyChange objects representing the differences
    """
    changes: List[PropertyChange] = []

    # Get property values
    if hasattr(old_obj, "model_dump"):
        old_data = old_obj.model_dump()
        new_data = new_obj.model_dump()
    elif hasattr(old_obj, "__dict__"):
        old_data = old_obj.__dict__.copy()
        new_data = new_obj.__dict__.copy()
    else:
        return changes

    # Ignore internal properties
    ignored = {"updated_at", "version", "_change_tracker", "_tracking_started"}
    for prop in ignored:
        old_data.pop(prop, None)
        new_data.pop(prop, None)

    all_props = set(old_data.keys()) | set(new_data.keys())

    for prop_name in all_props:
        old_value = old_data.get(prop_name)
        new_value = new_data.get(prop_name)

        if prop_name not in old_data:
            changes.append(PropertyChange(
                property_name=prop_name,
                old_value=None,
                new_value=new_value,
                change_type=ChangeType.CREATE,
            ))
        elif prop_name not in new_data:
            changes.append(PropertyChange(
                property_name=prop_name,
                old_value=old_value,
                new_value=None,
                change_type=ChangeType.DELETE,
            ))
        elif old_value != new_value:
            changes.append(PropertyChange(
                property_name=prop_name,
                old_value=old_value,
                new_value=new_value,
                change_type=ChangeType.UPDATE,
            ))

    return changes


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "ChangeType",
    "ChangeStatus",
    # Data classes
    "PropertyChange",
    "ChangeSet",
    # Tracker
    "ChangeTracker",
    # Mixin
    "ChangeTrackingMixin",
    # Utilities
    "get_changes",
    "has_changes",
    "diff_objects",
]
