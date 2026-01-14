"""
Orion ODA V3 - Prometheus Metrics Layer
========================================
Non-invasive metrics collection for observability.

Design Principles:
1. Zero Business Logic Modification: Uses decorators and context managers
2. EventBus Integration: Subscribes to domain events for reactive metrics
3. Prometheus Native: Uses prometheus_client for standard exposition
4. Structlog Compatible: Optional structured logging for metrics events

Metrics Exposed:
- orion_action_execution_duration_seconds (Histogram)
- orion_action_concurrency_conflicts_total (Counter)
- orion_proposal_status (Gauge)
- orion_side_effect_outcomes_total (Counter)
- orion_kernel_loop_iterations_total (Counter)
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.oda.ontology.storage.proposal_repository import ProposalRepository

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Try to import prometheus_client, provide stubs if not available
try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Info,
        REGISTRY,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed. Metrics will be no-ops.")

    # Stub implementations
    class StubMetric:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def info(self, *args, **kwargs):
            pass

    Counter = Gauge = Histogram = Info = StubMetric
    REGISTRY = None

    def generate_latest(registry=None):
        return b"# Prometheus not available\n"

    CONTENT_TYPE_LATEST = "text/plain"


# =============================================================================
# METRIC DEFINITIONS
# =============================================================================

# Action Execution Metrics
ACTION_EXECUTION_DURATION = Histogram(
    "orion_action_execution_duration_seconds",
    "Time spent executing an action",
    labelnames=["action_type", "status"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
) if PROMETHEUS_AVAILABLE else StubMetric()

ACTION_EXECUTION_TOTAL = Counter(
    "orion_action_executions_total",
    "Total number of action executions",
    labelnames=["action_type", "status"],
) if PROMETHEUS_AVAILABLE else StubMetric()

ACTION_RETRY_TOTAL = Counter(
    "orion_action_retries_total",
    "Total number of action retry attempts",
    labelnames=["action_type", "attempt"],
) if PROMETHEUS_AVAILABLE else StubMetric()

# Concurrency Metrics
CONCURRENCY_CONFLICTS = Counter(
    "orion_concurrency_conflicts_total",
    "Total number of optimistic locking conflicts",
    labelnames=["operation", "entity_type"],
) if PROMETHEUS_AVAILABLE else StubMetric()

# Proposal Metrics
PROPOSAL_STATUS_GAUGE = Gauge(
    "orion_proposal_status_count",
    "Current count of proposals by status",
    labelnames=["status"],
) if PROMETHEUS_AVAILABLE else StubMetric()

PROPOSAL_TRANSITIONS = Counter(
    "orion_proposal_transitions_total",
    "Total proposal state transitions",
    labelnames=["from_status", "to_status", "action_type"],
) if PROMETHEUS_AVAILABLE else StubMetric()

PROPOSAL_APPROVAL_RATE = Gauge(
    "orion_proposal_approval_rate",
    "Rolling approval rate (approved / (approved + rejected))",
) if PROMETHEUS_AVAILABLE else StubMetric()

# Side Effect Metrics
SIDE_EFFECT_OUTCOMES = Counter(
    "orion_side_effect_outcomes_total",
    "Outcomes of side effect executions",
    labelnames=["side_effect_name", "outcome"],
) if PROMETHEUS_AVAILABLE else StubMetric()

SIDE_EFFECT_DURATION = Histogram(
    "orion_side_effect_duration_seconds",
    "Time spent executing side effects",
    labelnames=["side_effect_name"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
) if PROMETHEUS_AVAILABLE else StubMetric()

# Kernel Loop Metrics
KERNEL_LOOP_ITERATIONS = Counter(
    "orion_kernel_loop_iterations_total",
    "Total kernel loop iterations",
    labelnames=["phase"],
) if PROMETHEUS_AVAILABLE else StubMetric()

KERNEL_LOOP_DURATION = Histogram(
    "orion_kernel_loop_duration_seconds",
    "Duration of kernel loop phases",
    labelnames=["phase"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
) if PROMETHEUS_AVAILABLE else StubMetric()

KERNEL_QUEUE_DEPTH = Gauge(
    "orion_kernel_queue_depth",
    "Current depth of processing queues",
    labelnames=["queue_name"],
) if PROMETHEUS_AVAILABLE else StubMetric()

# System Info
ORION_INFO = Info(
    "orion_system",
    "Orion Orchestrator system information",
) if PROMETHEUS_AVAILABLE else StubMetric()


# =============================================================================
# METRICS COLLECTOR (Singleton)
# =============================================================================

class MetricsCollector:
    """
    Central metrics collection service.

    Subscribes to EventBus events and updates Prometheus metrics.
    """

    _instance: Optional["MetricsCollector"] = None

    def __init__(self):
        self._initialized = False
        self._unsubscribers: List[Callable] = []
        self._approval_count = 0
        self._rejection_count = 0

    @classmethod
    def get_instance(cls) -> "MetricsCollector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset for testing."""
        if cls._instance:
            cls._instance.shutdown()
        cls._instance = None

    async def initialize(self) -> None:
        """Initialize metrics collection and subscribe to EventBus."""
        if self._initialized:
            return

        try:
            from lib.oda.infrastructure.event_bus import EventBus

            bus = EventBus.get_instance()

            self._unsubscribers.append(
                bus.subscribe("Proposal.*", self._on_proposal_event)
            )

            self._unsubscribers.append(
                bus.subscribe("*.completed", self._on_action_completed)
            )
        except ImportError:
            logger.warning("EventBus not available, skipping event subscriptions")

        # Set system info
        if PROMETHEUS_AVAILABLE:
            ORION_INFO.info({
                "version": "3.0.0",
                "mode": "enterprise_async",
                "persistence": "sqlalchemy_async",
            })

        self._initialized = True
        logger.info("MetricsCollector initialized")

    def shutdown(self) -> None:
        """Unsubscribe from all events."""
        for unsub in self._unsubscribers:
            try:
                unsub()
            except Exception:
                pass
        self._unsubscribers.clear()
        self._initialized = False

    async def _on_proposal_event(self, event) -> None:
        """Handle proposal lifecycle events."""
        payload = event.payload if hasattr(event, 'payload') else {}

        if isinstance(payload, dict):
            action_type = payload.get("action_type", "unknown")
            from_status = payload.get("previous_status", "unknown")
            to_status = payload.get("new_status", payload.get("status", "unknown"))
        else:
            action_type = getattr(payload, "action_type", "unknown")
            from_status = "unknown"
            to_status = getattr(payload, "status", "unknown")
            if hasattr(to_status, "value"):
                to_status = to_status.value

        PROPOSAL_TRANSITIONS.labels(
            from_status=from_status,
            to_status=to_status,
            action_type=action_type,
        ).inc()

        if to_status == "approved":
            self._approval_count += 1
        elif to_status == "rejected":
            self._rejection_count += 1

        total = self._approval_count + self._rejection_count
        if total > 0:
            PROPOSAL_APPROVAL_RATE.set(self._approval_count / total)

    async def _on_action_completed(self, event) -> None:
        """Handle action completion events."""
        payload = event.payload if hasattr(event, 'payload') else {}

        if isinstance(payload, dict):
            action_type = payload.get("action_type", "unknown")
            success = payload.get("success", False)
        else:
            action_type = getattr(payload, "action_type", "unknown")
            success = getattr(payload, "success", False)

        status = "success" if success else "failure"
        ACTION_EXECUTION_TOTAL.labels(action_type=action_type, status=status).inc()

    async def refresh_proposal_gauges(self, repo: "ProposalRepository") -> None:
        """Refresh proposal status gauges from database."""
        try:
            counts = await repo.count_by_status()
            for status, count in counts.items():
                PROPOSAL_STATUS_GAUGE.labels(status=status).set(count)
        except Exception as e:
            logger.warning(f"Failed to refresh proposal gauges: {e}")


# =============================================================================
# DECORATORS FOR NON-INVASIVE INSTRUMENTATION
# =============================================================================

def instrument_action(func: Callable) -> Callable:
    """
    Decorator to instrument action execution.

    Records execution duration and count by status.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        self_arg = args[0] if args else None
        action_type = getattr(self_arg, "api_name", "unknown")

        start_time = time.perf_counter()
        status = "success"

        try:
            result = await func(*args, **kwargs)
            if hasattr(result, "success") and not result.success:
                status = "failure"
            return result
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.perf_counter() - start_time
            ACTION_EXECUTION_DURATION.labels(
                action_type=action_type,
                status=status,
            ).observe(duration)
            ACTION_EXECUTION_TOTAL.labels(
                action_type=action_type,
                status=status,
            ).inc()

    return wrapper


def instrument_side_effect(func: Callable) -> Callable:
    """Decorator to instrument side effect execution."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        self_arg = args[0] if args else None
        effect_name = getattr(self_arg, "name", "unknown")

        start_time = time.perf_counter()
        outcome = "success"

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception:
            outcome = "failure"
            raise
        finally:
            duration = time.perf_counter() - start_time
            SIDE_EFFECT_DURATION.labels(side_effect_name=effect_name).observe(duration)
            SIDE_EFFECT_OUTCOMES.labels(
                side_effect_name=effect_name,
                outcome=outcome,
            ).inc()

    return wrapper


@asynccontextmanager
async def instrument_kernel_phase(phase: str):
    """Context manager for kernel loop phase instrumentation."""
    start_time = time.perf_counter()
    KERNEL_LOOP_ITERATIONS.labels(phase=phase).inc()

    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        KERNEL_LOOP_DURATION.labels(phase=phase).observe(duration)


def record_concurrency_conflict(operation: str, entity_type: str) -> None:
    """Record a concurrency conflict event."""
    CONCURRENCY_CONFLICTS.labels(
        operation=operation,
        entity_type=entity_type,
    ).inc()


def record_retry_attempt(action_type: str, attempt: int) -> None:
    """Record a retry attempt for action execution."""
    ACTION_RETRY_TOTAL.labels(
        action_type=action_type,
        attempt=str(attempt),
    ).inc()


# =============================================================================
# HTTP EXPOSITION
# =============================================================================

async def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    if PROMETHEUS_AVAILABLE:
        return generate_latest(REGISTRY)
    return b"# Prometheus not available\n"


def get_metrics_content_type() -> str:
    """Get the correct content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST


# =============================================================================
# STRUCTLOG INTEGRATION
# =============================================================================

@dataclass
class MetricEvent:
    """Structured metric event for logging."""
    metric_name: str
    metric_type: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
        }


def log_metric(
    metric_name: str,
    metric_type: str,
    value: float,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """Log a metric event with structlog format."""
    event = MetricEvent(
        metric_name=metric_name,
        metric_type=metric_type,
        value=value,
        labels=labels or {},
    )
    logger.info(
        "metric_recorded",
        extra=event.to_dict(),
    )
