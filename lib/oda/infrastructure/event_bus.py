"""
Orion ODA V3 - Async Event Bus
===============================
Decoupled event publishing for Repository → Observers communication.

Replaces ObjectManager._notify() with a standalone, async-first event system.
Follows Palantir AIP pattern: Side effects should be triggered via events, not callbacks.

Usage:
    # Publisher (in Repository)
    await EventBus.get_instance().publish("OrionActionLog.created", action_log)

    # Subscriber (in SimulationEngine)
    EventBus.get_instance().subscribe("OrionActionLog.*", self.on_action_log_event)
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Union
from weakref import WeakSet

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """
    Structured event payload for type safety.

    Attributes:
        event_type: Dot-notation event type (e.g., "Proposal.approved")
        payload: The domain object or data associated with the event
        timestamp: When the event occurred
        actor_id: Who triggered the event
        metadata: Optional additional context
    """
    event_type: str
    payload: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def entity_type(self) -> str:
        """Extract entity type from event_type (e.g., 'Proposal' from 'Proposal.approved')."""
        return self.event_type.split(".")[0] if "." in self.event_type else self.event_type

    @property
    def action(self) -> str:
        """Extract action from event_type (e.g., 'approved' from 'Proposal.approved')."""
        parts = self.event_type.split(".")
        return parts[1] if len(parts) > 1 else "unknown"


# Type alias for event handlers
EventHandler = Callable[[DomainEvent], Union[None, Coroutine[Any, Any, None]]]


class EventBus:
    """
    Singleton Async Event Bus for domain events.

    Features:
    - Pattern-based subscription (supports wildcards: "Proposal.*", "*")
    - Async and sync handler support
    - Weak references to prevent memory leaks (optional)
    - Error isolation: one handler failure doesn't affect others

    Thread Safety:
    - Uses asyncio for concurrency
    - Safe for use in async context
    """

    _instance: Optional[EventBus] = None

    def __init__(self):
        # Pattern -> List of handlers
        self._handlers: Dict[str, List[EventHandler]] = {}
        # Track active subscriptions for debugging
        self._subscription_count: int = 0
        # Event history for debugging/replay (bounded)
        self._event_history: List[DomainEvent] = []
        self._max_history_size: int = 100

    @classmethod
    def get_instance(cls) -> EventBus:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("EventBus singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    def subscribe(
        self,
        event_pattern: str,
        handler: EventHandler
    ) -> Callable[[], None]:
        """
        Subscribe to events matching a pattern.

        Args:
            event_pattern: Event type pattern (supports wildcards)
                - "Proposal.created": Exact match
                - "Proposal.*": All Proposal events
                - "*": All events
            handler: Async or sync callable that receives DomainEvent

        Returns:
            Unsubscribe function for cleanup

        Example:
            unsubscribe = bus.subscribe("Proposal.*", self.handle_proposal)
            # Later:
            unsubscribe()
        """
        if event_pattern not in self._handlers:
            self._handlers[event_pattern] = []

        self._handlers[event_pattern].append(handler)
        self._subscription_count += 1

        logger.debug(f"EventBus: Subscribed to '{event_pattern}' (total: {self._subscription_count})")

        # Return unsubscribe function
        def unsubscribe():
            self._unsubscribe(event_pattern, handler)

        return unsubscribe

    def _unsubscribe(self, event_pattern: str, handler: EventHandler) -> None:
        """Remove a specific handler from a pattern."""
        if event_pattern in self._handlers:
            try:
                self._handlers[event_pattern].remove(handler)
                self._subscription_count -= 1
                logger.debug(f"EventBus: Unsubscribed from '{event_pattern}'")
            except ValueError:
                pass  # Handler not found, ignore

    def unsubscribe_all(self, handler: EventHandler) -> int:
        """
        Remove a handler from all patterns.

        Returns:
            Number of subscriptions removed
        """
        removed = 0
        for pattern, handlers in list(self._handlers.items()):
            while handler in handlers:
                handlers.remove(handler)
                removed += 1
                self._subscription_count -= 1
        return removed

    async def publish(
        self,
        event_type: str,
        payload: Any,
        actor_id: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Publish an event to all matching subscribers.

        Args:
            event_type: Dot-notation event type (e.g., "Proposal.approved")
            payload: The domain object or data
            actor_id: Who triggered the event
            metadata: Optional additional context

        Returns:
            Number of handlers notified

        Example:
            await bus.publish("Proposal.approved", proposal, actor_id="user-123")
        """
        event = DomainEvent(
            event_type=event_type,
            payload=payload,
            actor_id=actor_id,
            metadata=metadata or {}
        )

        # Store in history (bounded)
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)

        # Find matching handlers
        matching_handlers: List[EventHandler] = []
        for pattern, handlers in self._handlers.items():
            if self._matches_pattern(event_type, pattern):
                matching_handlers.extend(handlers)

        if not matching_handlers:
            logger.debug(f"EventBus: No handlers for '{event_type}'")
            return 0

        # Execute handlers with error isolation
        notified = 0
        for handler in matching_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                notified += 1
            except Exception as e:
                logger.error(
                    f"EventBus: Handler error for '{event_type}': {e}",
                    exc_info=True
                )
                # Continue to next handler - don't let one failure stop others

        logger.debug(f"EventBus: Published '{event_type}' to {notified} handlers")
        return notified

    def publish_sync(
        self,
        event_type: str,
        payload: Any,
        actor_id: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Synchronous publish for non-async contexts.
        Creates event loop if needed.
        """
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - schedule the coroutine
            future = asyncio.ensure_future(
                self.publish(event_type, payload, actor_id, metadata)
            )
            return 0  # Can't wait for result in sync context
        except RuntimeError:
            # No running loop - create one
            return asyncio.run(
                self.publish(event_type, payload, actor_id, metadata)
            )

    @staticmethod
    def _matches_pattern(event_type: str, pattern: str) -> bool:
        """
        Check if event_type matches a subscription pattern.

        Supports:
        - Exact match: "Proposal.created" matches "Proposal.created"
        - Wildcard suffix: "Proposal.*" matches "Proposal.created", "Proposal.approved"
        - Global wildcard: "*" matches everything
        """
        if pattern == "*":
            return True
        return fnmatch.fnmatch(event_type, pattern)

    def get_handler_count(self, pattern: Optional[str] = None) -> int:
        """Get count of registered handlers."""
        if pattern:
            return len(self._handlers.get(pattern, []))
        return self._subscription_count

    def get_recent_events(self, limit: int = 10) -> List[DomainEvent]:
        """Get recent events for debugging."""
        return self._event_history[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Convenience functions for module-level access
def get_event_bus() -> EventBus:
    """Get the global EventBus instance."""
    return EventBus.get_instance()


async def publish_event(
    event_type: str,
    payload: Any,
    actor_id: str = "system",
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Convenience function to publish an event."""
    return await EventBus.get_instance().publish(
        event_type, payload, actor_id, metadata
    )
