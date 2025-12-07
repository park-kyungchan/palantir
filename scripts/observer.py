
import logging
from typing import Dict, Any, Callable

# Standard Interface for Observability
# This allows 'AutomationLayer' (Phase 3) to subscribe to system events.

class Observer:
    """
    Central Observability Bus.
    """
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def emit(self, event_type: str, payload: Any):
        """
        Standard Interface: Emits a full Event object.
        """
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(payload)
                except Exception as e:
                    logging.error(f"Observer Error: {e}")

# Global instance for lightweight usage
global_observer = Observer()
