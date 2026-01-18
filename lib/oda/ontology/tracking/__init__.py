"""
Orion ODA v4.0 - Change Tracking

This package provides change tracking for OntologyObjects:
- changes.py: Property change tracking and diff generation
- status_history.py: Status lifecycle transition history

Schema Version: 4.0.0
"""

from lib.oda.ontology.tracking.changes import (
    PropertyChange,
    ChangeSet,
    ChangeTracker,
    ChangeTrackingMixin,
    get_changes,
    has_changes,
)

from lib.oda.ontology.tracking.status_history import (
    StatusHistoryEntry,
    StatusHistoryTracker,
    get_default_tracker,
    set_default_tracker,
)

__all__ = [
    # Property Change Tracking
    "PropertyChange",
    "ChangeSet",
    "ChangeTracker",
    "ChangeTrackingMixin",
    "get_changes",
    "has_changes",
    # Status History Tracking
    "StatusHistoryEntry",
    "StatusHistoryTracker",
    "get_default_tracker",
    "set_default_tracker",
]
