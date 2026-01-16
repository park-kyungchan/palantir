"""
Orion ODA v3.0 - Observability Module
=====================================

Dashboard integration and observability events for the hook system.
Provides:
- ObservabilityEvent ObjectType for audit logging
- Dashboard metrics collection
- Real-time event streaming
- LogObservabilityAction for action-based logging

Reference: Palantir Workshop/Slate dashboard patterns
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import Field, ConfigDict

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type
from lib.oda.infrastructure.event_bus import DomainEvent, EventBus, get_event_bus

logger = logging.getLogger(__name__)


class ObservabilityEventType(str, Enum):
    """
    Types of observability events for dashboard and monitoring.
    """

    # Hook Events
    HOOK_REGISTERED = "hook.registered"
    HOOK_UNREGISTERED = "hook.unregistered"
    HOOK_TRIGGERED = "hook.triggered"
    HOOK_EXECUTED = "hook.executed"
    HOOK_FAILED = "hook.failed"
    HOOK_BLOCKED = "hook.blocked"

    # Session Events
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"

    # Security Events
    SECURITY_VIOLATION = "security.violation"
    SECURITY_WARNING = "security.warning"
    SECURITY_BLOCKED = "security.blocked"

    # Performance Events
    PERFORMANCE_SLOW = "performance.slow"
    PERFORMANCE_TIMEOUT = "performance.timeout"

    # System Events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"


class ObservabilitySeverity(str, Enum):
    """
    Severity levels for observability events.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@register_object_type
class ObservabilityEvent(OntologyObject):
    """
    Observability event for audit logging and dashboard display.

    Used to record significant events in the hook system for:
    - Audit compliance
    - Dashboard visualization
    - Alerting and monitoring
    - Performance analysis

    Attributes:
        event_type: Type of observability event
        severity: Event severity level
        source_app: Application/component that generated the event
        message: Human-readable event message
        timestamp: When the event occurred
        metadata: Additional structured data
        session_id: Claude session ID (if applicable)
        trace_id: Trace ID for distributed tracing
        span_id: Span ID for distributed tracing
        tags: Tags for filtering and categorization

    Example:
        ```python
        ObservabilityEvent(
            event_type=ObservabilityEventType.HOOK_BLOCKED,
            severity=ObservabilitySeverity.WARNING,
            source_app="security-validator",
            message="Blocked dangerous rm -rf command",
            metadata={"command": "rm -rf /", "rule": "NO_RECURSIVE_DELETE"},
        )
        ```
    """

    # Required fields
    event_type: ObservabilityEventType = Field(
        ...,
        description="Type of observability event",
    )
    source_app: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Application/component that generated the event",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Human-readable event message",
    )

    # Optional fields
    severity: ObservabilitySeverity = Field(
        default=ObservabilitySeverity.INFO,
        description="Event severity level",
    )
    event_timestamp: datetime = Field(
        default_factory=utc_now,
        description="When the event occurred",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured data",
    )

    # Context
    session_id: Optional[str] = Field(
        default=None,
        description="Claude session ID",
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for distributed tracing",
    )
    span_id: Optional[str] = Field(
        default=None,
        description="Span ID for distributed tracing",
    )

    # Categorization
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for filtering",
    )

    # Associated entity
    entity_type: Optional[str] = Field(
        default=None,
        description="Type of associated entity (e.g., 'HookDefinition')",
    )
    entity_id: Optional[str] = Field(
        default=None,
        description="ID of associated entity",
    )

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    @property
    def is_error(self) -> bool:
        """Returns True if severity is ERROR or CRITICAL."""
        return self.severity in (
            ObservabilitySeverity.ERROR,
            ObservabilitySeverity.CRITICAL,
        )

    @property
    def is_security_event(self) -> bool:
        """Returns True if this is a security-related event."""
        return self.event_type.value.startswith("security.")

    @classmethod
    def create_hook_event(
        cls,
        event_type: ObservabilityEventType,
        hook_name: str,
        message: str,
        severity: ObservabilitySeverity = ObservabilitySeverity.INFO,
        **kwargs: Any,
    ) -> ObservabilityEvent:
        """
        Factory method for hook-related events.

        Args:
            event_type: Type of hook event
            hook_name: Name of the hook
            message: Event message
            severity: Event severity
            **kwargs: Additional fields

        Returns:
            New ObservabilityEvent instance
        """
        metadata = kwargs.pop("metadata", {})
        metadata["hook_name"] = hook_name

        return cls(
            event_type=event_type,
            source_app=f"hook:{hook_name}",
            message=message,
            severity=severity,
            metadata=metadata,
            **kwargs,
        )

    @classmethod
    def create_security_event(
        cls,
        event_type: ObservabilityEventType,
        message: str,
        rule_name: str,
        severity: ObservabilitySeverity = ObservabilitySeverity.WARNING,
        **kwargs: Any,
    ) -> ObservabilityEvent:
        """
        Factory method for security-related events.

        Args:
            event_type: Type of security event
            message: Event message
            rule_name: Name of the security rule
            severity: Event severity
            **kwargs: Additional fields

        Returns:
            New ObservabilityEvent instance
        """
        metadata = kwargs.pop("metadata", {})
        metadata["rule_name"] = rule_name

        return cls(
            event_type=event_type,
            source_app="security-validator",
            message=message,
            severity=severity,
            metadata=metadata,
            tags=["security", rule_name],
            **kwargs,
        )


class ObservabilityCollector:
    """
    Singleton collector for observability events.

    Features:
    - Event buffering for batch writes
    - EventBus integration
    - Dashboard metrics aggregation
    - Real-time event streaming

    Usage:
        ```python
        collector = ObservabilityCollector.get_instance()

        # Log an event
        await collector.log(ObservabilityEvent(
            event_type=ObservabilityEventType.HOOK_EXECUTED,
            source_app="security-validator",
            message="Hook executed successfully",
        ))

        # Get recent events
        events = collector.get_recent_events(limit=10)

        # Get metrics
        metrics = collector.get_metrics()
        ```
    """

    _instance: Optional[ObservabilityCollector] = None

    def __init__(self) -> None:
        # Event buffer (bounded)
        self._events: List[ObservabilityEvent] = []
        self._max_buffer_size: int = 1000

        # Metrics
        self._event_counts: Dict[str, int] = {}
        self._severity_counts: Dict[str, int] = {}

        # Subscribers for real-time streaming
        self._subscribers: List[Callable[[ObservabilityEvent], None]] = []

    @classmethod
    def get_instance(cls) -> ObservabilityCollector:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("ObservabilityCollector singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    async def log(
        self,
        event: ObservabilityEvent,
        publish_to_event_bus: bool = True,
    ) -> None:
        """
        Log an observability event.

        Args:
            event: ObservabilityEvent to log
            publish_to_event_bus: Whether to publish to EventBus
        """
        # Add to buffer
        self._events.append(event)
        if len(self._events) > self._max_buffer_size:
            self._events.pop(0)

        # Update metrics
        self._event_counts[event.event_type.value] = (
            self._event_counts.get(event.event_type.value, 0) + 1
        )
        self._severity_counts[event.severity.value] = (
            self._severity_counts.get(event.severity.value, 0) + 1
        )

        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(event)
                else:
                    subscriber(event)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")

        # Publish to EventBus
        if publish_to_event_bus:
            event_bus = get_event_bus()
            await event_bus.publish(
                event_type=f"Observability.{event.event_type.value}",
                payload=event.model_dump(),
                metadata={
                    "severity": event.severity.value,
                    "source_app": event.source_app,
                },
            )

        # Log to standard logger based on severity
        log_method = getattr(logger, event.severity.value, logger.info)
        log_method(f"[{event.event_type.value}] {event.message}")

    def log_sync(
        self,
        event: ObservabilityEvent,
        publish_to_event_bus: bool = True,
    ) -> None:
        """Synchronous log method for non-async contexts."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.log(event, publish_to_event_bus))
        except RuntimeError:
            asyncio.run(self.log(event, publish_to_event_bus))

    def subscribe(
        self,
        callback: Callable[[ObservabilityEvent], None],
    ) -> Callable[[], None]:
        """
        Subscribe to real-time event stream.

        Args:
            callback: Function to call for each event

        Returns:
            Unsubscribe function
        """
        self._subscribers.append(callback)

        def unsubscribe():
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe

    def get_recent_events(
        self,
        limit: int = 100,
        event_type: Optional[ObservabilityEventType] = None,
        severity: Optional[ObservabilitySeverity] = None,
        source_app: Optional[str] = None,
    ) -> List[ObservabilityEvent]:
        """
        Get recent events with optional filtering.

        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            severity: Filter by severity
            source_app: Filter by source app

        Returns:
            List of ObservabilityEvent instances
        """
        events = list(reversed(self._events))

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if severity:
            events = [e for e in events if e.severity == severity]

        if source_app:
            events = [e for e in events if e.source_app == source_app]

        return events[:limit]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated metrics for dashboard.

        Returns:
            Dict with event counts, severity breakdown, etc.
        """
        return {
            "total_events": len(self._events),
            "event_counts": dict(self._event_counts),
            "severity_counts": dict(self._severity_counts),
            "recent_errors": len(
                [
                    e
                    for e in self._events[-100:]
                    if e.severity
                    in (ObservabilitySeverity.ERROR, ObservabilitySeverity.CRITICAL)
                ]
            ),
            "recent_security_events": len(
                [e for e in self._events[-100:] if e.is_security_event]
            ),
        }

    def clear(self) -> None:
        """Clear all events and metrics."""
        self._events.clear()
        self._event_counts.clear()
        self._severity_counts.clear()


class DashboardIntegration:
    """
    Integration layer for dashboard visualization.

    Provides formatted data for Workshop/Slate dashboard widgets.
    """

    def __init__(self, collector: Optional[ObservabilityCollector] = None) -> None:
        self._collector = collector or ObservabilityCollector.get_instance()

    def get_hook_execution_timeline(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get hook executions as timeline data for dashboard.

        Returns:
            List of timeline entries
        """
        events = self._collector.get_recent_events(
            limit=limit,
            event_type=ObservabilityEventType.HOOK_EXECUTED,
        )

        return [
            {
                "timestamp": e.event_timestamp.isoformat(),
                "hook_name": e.metadata.get("hook_name", "unknown"),
                "duration_ms": e.metadata.get("duration_ms", 0),
                "status": "success" if not e.is_error else "error",
                "message": e.message,
            }
            for e in events
        ]

    def get_security_alerts(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get security alerts for dashboard.

        Returns:
            List of security alert entries
        """
        events = [
            e for e in self._collector.get_recent_events(limit=limit * 2)
            if e.is_security_event
        ][:limit]

        return [
            {
                "timestamp": e.event_timestamp.isoformat(),
                "severity": e.severity.value,
                "rule_name": e.metadata.get("rule_name", "unknown"),
                "message": e.message,
                "blocked": e.event_type == ObservabilityEventType.SECURITY_BLOCKED,
            }
            for e in events
        ]

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary for dashboard.

        Returns:
            Performance metrics summary
        """
        events = self._collector.get_recent_events(
            limit=100,
            event_type=ObservabilityEventType.HOOK_EXECUTED,
        )

        durations = [
            e.metadata.get("duration_ms", 0)
            for e in events
            if "duration_ms" in e.metadata
        ]

        if not durations:
            return {
                "avg_duration_ms": 0,
                "max_duration_ms": 0,
                "min_duration_ms": 0,
                "total_executions": 0,
            }

        return {
            "avg_duration_ms": sum(durations) / len(durations),
            "max_duration_ms": max(durations),
            "min_duration_ms": min(durations),
            "total_executions": len(durations),
            "slow_executions": len([d for d in durations if d > 1000]),
        }


# Module-level convenience functions
def get_observability_collector() -> ObservabilityCollector:
    """Get the global ObservabilityCollector instance."""
    return ObservabilityCollector.get_instance()


async def log_observability_event(
    event_type: ObservabilityEventType,
    source_app: str,
    message: str,
    severity: ObservabilitySeverity = ObservabilitySeverity.INFO,
    **kwargs: Any,
) -> None:
    """
    Convenience function to log an observability event.

    Args:
        event_type: Type of event
        source_app: Source application/component
        message: Event message
        severity: Event severity
        **kwargs: Additional ObservabilityEvent fields
    """
    event = ObservabilityEvent(
        event_type=event_type,
        source_app=source_app,
        message=message,
        severity=severity,
        **kwargs,
    )
    await ObservabilityCollector.get_instance().log(event)
