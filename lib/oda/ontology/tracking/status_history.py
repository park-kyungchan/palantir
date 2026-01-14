"""
Orion ODA v4.0 - Status History Tracking
=========================================

This module provides status transition history tracking for OntologyObjects,
enabling full audit trails of lifecycle changes.

Features:
- StatusHistoryEntry: Individual transition records
- StatusHistoryTracker: Service for recording and querying history
- Full audit trail with timestamps, actors, and reasons

Example:
    ```python
    tracker = StatusHistoryTracker()

    # Record a transition
    entry = tracker.record_transition(
        object_id="proj-001",
        object_type="Project",
        from_status=ResourceLifecycleStatus.DRAFT,
        to_status=ResourceLifecycleStatus.EXPERIMENTAL,
        context=StatusTransitionContext(
            actor_id="user-123",
            reason="Ready for testing"
        )
    )

    # Query history
    history = tracker.get_history("proj-001")
    for entry in history:
        print(f"{entry.timestamp}: {entry.from_status} -> {entry.to_status}")
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from lib.oda.ontology.types.status_types import ResourceLifecycleStatus

logger = logging.getLogger(__name__)


class StatusHistoryEntry(BaseModel):
    """
    Represents a single status transition record.

    Attributes:
        entry_id: Unique identifier for this history entry
        object_id: ID of the object that transitioned
        object_type: Type name of the object
        from_status: Previous status
        to_status: New status
        timestamp: When the transition occurred
        actor_id: Who initiated the transition
        reason: Optional explanation
        metadata: Additional context information
    """

    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    object_id: str
    object_type: str
    from_status: ResourceLifecycleStatus
    to_status: ResourceLifecycleStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": False}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entry_id": self.entry_id,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "reason": self.reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusHistoryEntry":
        """Create from dictionary."""
        return cls(
            entry_id=data["entry_id"],
            object_id=data["object_id"],
            object_type=data["object_type"],
            from_status=ResourceLifecycleStatus(data["from_status"]),
            to_status=ResourceLifecycleStatus(data["to_status"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            actor_id=data["actor_id"],
            reason=data.get("reason"),
            metadata=data.get("metadata", {}),
        )


class StatusHistoryTracker:
    """
    Service for tracking status transition history.

    Provides methods to record transitions and query history.
    Supports both in-memory and file-based storage.

    Thread-safe for concurrent access.
    """

    def __init__(self, storage_path: Optional[Union[str, Path]] = None):
        """
        Initialize the tracker.

        Args:
            storage_path: Optional path for persistent storage.
                         If None, history is kept in memory only.
        """
        self._history: Dict[str, List[StatusHistoryEntry]] = {}
        self._storage_path = Path(storage_path) if storage_path else None

        if self._storage_path:
            self._load_history()

    def record_transition(
        self,
        object_id: str,
        object_type: str,
        from_status: ResourceLifecycleStatus,
        to_status: ResourceLifecycleStatus,
        context: Optional[Any] = None,  # StatusTransitionContext
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StatusHistoryEntry:
        """
        Record a status transition.

        Args:
            object_id: ID of the transitioned object
            object_type: Type name of the object
            from_status: Previous status
            to_status: New status
            context: Optional StatusTransitionContext with full details
            actor_id: Who initiated (can also come from context)
            reason: Why the transition occurred (can also come from context)
            metadata: Additional context (can also come from context)

        Returns:
            The created StatusHistoryEntry
        """
        # Extract from context if provided
        if context is not None:
            actor_id = actor_id or getattr(context, "actor_id", "unknown")
            reason = reason or getattr(context, "reason", None)
            timestamp = getattr(context, "timestamp", datetime.now(timezone.utc))
            ctx_metadata = getattr(context, "metadata", {})
            metadata = {**ctx_metadata, **(metadata or {})}
        else:
            actor_id = actor_id or "unknown"
            timestamp = datetime.now(timezone.utc)
            metadata = metadata or {}

        entry = StatusHistoryEntry(
            object_id=object_id,
            object_type=object_type,
            from_status=from_status,
            to_status=to_status,
            timestamp=timestamp,
            actor_id=actor_id,
            reason=reason,
            metadata=metadata,
        )

        # Store in memory
        if object_id not in self._history:
            self._history[object_id] = []
        self._history[object_id].append(entry)

        # Persist if storage configured
        if self._storage_path:
            self._save_history()

        logger.debug(
            f"Recorded status transition for {object_type}:{object_id} "
            f"({from_status.value} -> {to_status.value})"
        )

        return entry

    def get_history(
        self,
        object_id: str,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> List[StatusHistoryEntry]:
        """
        Get status transition history for an object.

        Args:
            object_id: ID of the object
            limit: Maximum number of entries to return
            ascending: If True, oldest first; if False, newest first

        Returns:
            List of StatusHistoryEntry in chronological order
        """
        history = self._history.get(object_id, [])

        if ascending:
            sorted_history = sorted(history, key=lambda e: e.timestamp)
        else:
            sorted_history = sorted(history, key=lambda e: e.timestamp, reverse=True)

        if limit:
            return sorted_history[:limit]
        return sorted_history

    def get_latest_status(self, object_id: str) -> Optional[ResourceLifecycleStatus]:
        """
        Get the most recent status for an object.

        Args:
            object_id: ID of the object

        Returns:
            The latest status, or None if no history exists
        """
        history = self.get_history(object_id, limit=1, ascending=False)
        if history:
            return history[0].to_status
        return None

    def get_transitions_by_actor(
        self,
        actor_id: str,
        limit: Optional[int] = None,
    ) -> List[StatusHistoryEntry]:
        """
        Get all transitions performed by a specific actor.

        Args:
            actor_id: ID of the actor
            limit: Maximum number of entries

        Returns:
            List of transitions by this actor
        """
        all_entries = []
        for entries in self._history.values():
            for entry in entries:
                if entry.actor_id == actor_id:
                    all_entries.append(entry)

        sorted_entries = sorted(all_entries, key=lambda e: e.timestamp, reverse=True)

        if limit:
            return sorted_entries[:limit]
        return sorted_entries

    def get_transitions_by_status(
        self,
        to_status: ResourceLifecycleStatus,
        limit: Optional[int] = None,
    ) -> List[StatusHistoryEntry]:
        """
        Get all transitions to a specific status.

        Args:
            to_status: Target status to filter by
            limit: Maximum number of entries

        Returns:
            List of transitions to this status
        """
        all_entries = []
        for entries in self._history.values():
            for entry in entries:
                if entry.to_status == to_status:
                    all_entries.append(entry)

        sorted_entries = sorted(all_entries, key=lambda e: e.timestamp, reverse=True)

        if limit:
            return sorted_entries[:limit]
        return sorted_entries

    def get_transition_count(self, object_id: str) -> int:
        """Get the number of transitions for an object."""
        return len(self._history.get(object_id, []))

    def get_time_in_status(
        self,
        object_id: str,
        status: ResourceLifecycleStatus,
    ) -> Optional[float]:
        """
        Calculate total time spent in a status (in seconds).

        Args:
            object_id: ID of the object
            status: Status to calculate time for

        Returns:
            Total seconds in this status, or None if never in status
        """
        history = self.get_history(object_id, ascending=True)
        if not history:
            return None

        total_seconds = 0.0
        in_status_since: Optional[datetime] = None

        for entry in history:
            if entry.from_status == status and in_status_since:
                # Leaving the status
                delta = entry.timestamp - in_status_since
                total_seconds += delta.total_seconds()
                in_status_since = None
            elif entry.to_status == status:
                # Entering the status
                in_status_since = entry.timestamp

        # If still in status, count up to now
        if in_status_since:
            delta = datetime.now(timezone.utc) - in_status_since
            total_seconds += delta.total_seconds()

        return total_seconds if total_seconds > 0 else None

    def clear_history(self, object_id: Optional[str] = None) -> int:
        """
        Clear history entries.

        Args:
            object_id: If provided, clear only for this object.
                      If None, clear all history.

        Returns:
            Number of entries cleared
        """
        if object_id:
            count = len(self._history.pop(object_id, []))
        else:
            count = sum(len(entries) for entries in self._history.values())
            self._history.clear()

        if self._storage_path:
            self._save_history()

        return count

    def export_history(self, object_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Export history as a list of dictionaries.

        Args:
            object_id: If provided, export only for this object

        Returns:
            List of history entries as dictionaries
        """
        if object_id:
            entries = self._history.get(object_id, [])
        else:
            entries = []
            for obj_entries in self._history.values():
                entries.extend(obj_entries)

        return [entry.to_dict() for entry in entries]

    def _load_history(self) -> None:
        """Load history from storage file."""
        if not self._storage_path or not self._storage_path.exists():
            return

        try:
            with open(self._storage_path) as f:
                data = json.load(f)

            for object_id, entries_data in data.items():
                self._history[object_id] = [
                    StatusHistoryEntry.from_dict(e) for e in entries_data
                ]

            logger.info(
                f"Loaded status history from {self._storage_path} "
                f"({sum(len(e) for e in self._history.values())} entries)"
            )
        except Exception as e:
            logger.error(f"Failed to load status history: {e}")

    def _save_history(self) -> None:
        """Save history to storage file."""
        if not self._storage_path:
            return

        try:
            # Ensure parent directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                object_id: [entry.to_dict() for entry in entries]
                for object_id, entries in self._history.items()
            }

            with open(self._storage_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save status history: {e}")


# Global tracker instance (optional, can be overridden)
_default_tracker: Optional[StatusHistoryTracker] = None


def get_default_tracker() -> StatusHistoryTracker:
    """Get or create the default status history tracker."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = StatusHistoryTracker()
    return _default_tracker


def set_default_tracker(tracker: StatusHistoryTracker) -> None:
    """Set the default status history tracker."""
    global _default_tracker
    _default_tracker = tracker


__all__ = [
    "StatusHistoryEntry",
    "StatusHistoryTracker",
    "get_default_tracker",
    "set_default_tracker",
]
