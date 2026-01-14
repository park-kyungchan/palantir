"""
Orion Infrastructure Layer
===========================
Cross-cutting concerns: Event Bus, Caching, Metrics, etc.
"""

from scripts.infrastructure.event_bus import EventBus, DomainEvent
from scripts.infrastructure.metrics import (
    MetricsCollector,
    instrument_action,
    instrument_side_effect,
    instrument_kernel_phase,
    record_concurrency_conflict,
    record_retry_attempt,
    get_metrics,
    get_metrics_content_type,
    log_metric,
    # Prometheus metrics for direct access
    ACTION_EXECUTION_DURATION,
    ACTION_EXECUTION_TOTAL,
    CONCURRENCY_CONFLICTS,
    PROPOSAL_STATUS_GAUGE,
    PROPOSAL_TRANSITIONS,
    SIDE_EFFECT_OUTCOMES,
    KERNEL_LOOP_ITERATIONS,
)

__all__ = [
    # Event Bus
    "EventBus",
    "DomainEvent",
    # Metrics
    "MetricsCollector",
    "instrument_action",
    "instrument_side_effect",
    "instrument_kernel_phase",
    "record_concurrency_conflict",
    "record_retry_attempt",
    "get_metrics",
    "get_metrics_content_type",
    "log_metric",
    # Raw metrics
    "ACTION_EXECUTION_DURATION",
    "ACTION_EXECUTION_TOTAL",
    "CONCURRENCY_CONFLICTS",
    "PROPOSAL_STATUS_GAUGE",
    "PROPOSAL_TRANSITIONS",
    "SIDE_EFFECT_OUTCOMES",
    "KERNEL_LOOP_ITERATIONS",
]
