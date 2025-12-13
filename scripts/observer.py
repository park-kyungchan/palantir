from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List


class _ObserverBus:
    """
    Central observability bus.

    The underlying bus remains string-keyed (`event_type` -> listeners) so it can
    support both "raw" emits and structured Event objects.
    """

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        self._listeners.setdefault(event_type, []).append(callback)

    def emit(self, event_type: str, payload: Any) -> None:
        for callback in self._listeners.get(event_type, []):
            try:
                callback(payload)
            except Exception:
                logging.exception("Observer callback error")


def _coerce_event_type(event: Any) -> str:
    event_type = getattr(event, "event_type", None)
    if event_type is None:
        return "UNKNOWN"
    if hasattr(event_type, "value"):
        return str(event_type.value)
    return str(event_type)


# Global instance for lightweight usage and backwards-compatibility.
global_observer = _ObserverBus()


class Observer:
    """
    Public facade used by the rest of the codebase.

    Supports:
    - `Observer.subscribe("ACTION_START", cb)`
    - `Observer.emit(Event(...))`
    - `Observer.emit("ACTION_START", payload)` (legacy)
    """

    @staticmethod
    def subscribe(event_type: str, callback: Callable[[Any], None]) -> None:
        global_observer.subscribe(event_type, callback)

    @staticmethod
    def emit(*args: Any) -> None:
        if len(args) == 1:
            event = args[0]
            global_observer.emit(_coerce_event_type(event), event)
            return
        if len(args) == 2:
            event_type, payload = args
            global_observer.emit(str(event_type), payload)
            return
        raise TypeError("Observer.emit expects (event) or (event_type, payload)")
