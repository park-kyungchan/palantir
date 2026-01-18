"""Prometheus metrics for monitoring.

This module provides Prometheus metrics for observability of the MathpixPipeline.
It includes graceful degradation when prometheus_client is not installed.

Metrics exported:
    - mathpix_images_processed_total: Counter of processed images by status
    - mathpix_api_calls_total: Counter of external API calls by service/status
    - mathpix_processing_seconds: Histogram of processing time by stage
    - mathpix_api_latency_seconds: Histogram of API call latency
    - mathpix_queue_size: Gauge of current queue size
    - mathpix_active_workers: Gauge of active processing workers
    - mathpix_pipeline: Info about pipeline build

Usage:
    from mathpix_pipeline.utils.metrics import get_metrics

    metrics = get_metrics()

    # Record processing result
    metrics.record_processed(success=True)

    # Time a pipeline stage
    with metrics.time_stage("alignment"):
        result = engine.align(...)

    # Time an API call
    with metrics.time_api("mathpix"):
        response = await client.process(image)

    # Update gauges
    metrics.set_queue_size(10)
    metrics.set_active_workers(4)
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)

# Try to import prometheus_client, gracefully degrade if not available
try:
    from prometheus_client import Counter, Gauge, Histogram, Info

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info(
        "prometheus_client not installed, metrics collection disabled. "
        "Install with: pip install prometheus-client"
    )


# Define metrics if prometheus_client is available
if PROMETHEUS_AVAILABLE:
    # Counters - track total occurrences
    IMAGES_PROCESSED = Counter(
        "mathpix_images_processed_total",
        "Total number of images processed",
        ["status"],  # Labels: success, failure
    )

    API_CALLS = Counter(
        "mathpix_api_calls_total",
        "Total number of external API calls",
        ["service", "status"],  # Labels: mathpix/anthropic/google, success/failure
    )

    # Histograms - track distribution of values
    PROCESSING_TIME = Histogram(
        "mathpix_processing_seconds",
        "Image processing time in seconds by stage",
        ["stage"],  # Labels: ingestion, text_parse, vision_parse, alignment, etc.
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    )

    API_LATENCY = Histogram(
        "mathpix_api_latency_seconds",
        "External API call latency in seconds",
        ["service"],  # Labels: mathpix, anthropic, google
        buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # Gauges - track current values
    QUEUE_SIZE = Gauge(
        "mathpix_queue_size",
        "Current number of items in the processing queue",
    )

    ACTIVE_WORKERS = Gauge(
        "mathpix_active_workers",
        "Number of currently active processing workers",
    )

    # Info - static metadata
    PIPELINE_INFO = Info(
        "mathpix_pipeline",
        "Pipeline build and version information",
    )
else:
    # Placeholder variables when prometheus is not available
    IMAGES_PROCESSED = None
    API_CALLS = None
    PROCESSING_TIME = None
    API_LATENCY = None
    QUEUE_SIZE = None
    ACTIVE_WORKERS = None
    PIPELINE_INFO = None


class _TimerContext:
    """Context manager for timing operations."""

    def __init__(self, label_name: str, label_value: str, histogram: Any, enabled: bool):
        self.label_name = label_name
        self.label_value = label_value
        self.histogram = histogram
        self.enabled = enabled
        self._start_time: Optional[float] = None
        self.duration: Optional[float] = None

    def __enter__(self) -> "_TimerContext":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._start_time is not None:
            self.duration = time.perf_counter() - self._start_time
            if self.enabled and self.histogram is not None:
                self.histogram.labels(**{self.label_name: self.label_value}).observe(
                    self.duration
                )


class MetricsCollector:
    """Collect and export Prometheus metrics.

    This class provides methods to record various metrics about the pipeline's
    operation. If prometheus_client is not installed, all methods become no-ops.

    Attributes:
        enabled: Whether metrics collection is enabled (prometheus available).

    Example:
        metrics = MetricsCollector()

        # Record image processing result
        metrics.record_processed(success=True)

        # Time a processing stage
        with metrics.time_stage("alignment") as timer:
            result = engine.align(...)
        print(f"Alignment took {timer.duration:.2f}s")

        # Time an API call
        with metrics.time_api("mathpix") as timer:
            response = await client.process(image)

        # Update gauges
        metrics.set_queue_size(10)
        metrics.set_active_workers(4)
    """

    def __init__(self, version: str = "2.0.0", schema_version: str = "2.0.0") -> None:
        """Initialize the metrics collector.

        Args:
            version: Pipeline version to report in info metric.
            schema_version: Schema version to report in info metric.
        """
        self.enabled = PROMETHEUS_AVAILABLE
        self._version = version
        self._schema_version = schema_version

        if self.enabled and PIPELINE_INFO is not None:
            PIPELINE_INFO.info(
                {
                    "version": version,
                    "schema_version": schema_version,
                }
            )
            logger.debug("Prometheus metrics initialized")

    def record_processed(self, success: bool) -> None:
        """Record an image processing result.

        Args:
            success: True if processing succeeded, False if it failed.
        """
        if self.enabled and IMAGES_PROCESSED is not None:
            status = "success" if success else "failure"
            IMAGES_PROCESSED.labels(status=status).inc()

    def record_api_call(self, service: str, success: bool) -> None:
        """Record an external API call.

        Args:
            service: The service called (e.g., "mathpix", "anthropic", "google").
            success: True if the call succeeded, False if it failed.
        """
        if self.enabled and API_CALLS is not None:
            status = "success" if success else "failure"
            API_CALLS.labels(service=service, status=status).inc()

    def time_stage(self, stage: str) -> _TimerContext:
        """Create a context manager for timing a pipeline stage.

        Args:
            stage: The stage name (e.g., "ingestion", "alignment", "export").

        Returns:
            A context manager that times the enclosed code block.

        Example:
            with metrics.time_stage("alignment") as timer:
                result = engine.align(data)
            print(f"Took {timer.duration:.2f}s")
        """
        return _TimerContext(
            label_name="stage",
            label_value=stage,
            histogram=PROCESSING_TIME,
            enabled=self.enabled,
        )

    def time_api(self, service: str) -> _TimerContext:
        """Create a context manager for timing an API call.

        Args:
            service: The service name (e.g., "mathpix", "anthropic").

        Returns:
            A context manager that times the enclosed code block.

        Example:
            with metrics.time_api("mathpix") as timer:
                response = await client.process(image)
            print(f"API call took {timer.duration:.2f}s")
        """
        return _TimerContext(
            label_name="service",
            label_value=service,
            histogram=API_LATENCY,
            enabled=self.enabled,
        )

    @contextmanager
    def track_worker(self) -> Generator[None, None, None]:
        """Context manager to track active workers.

        Increments the active worker count on entry and decrements on exit.

        Example:
            async def process_job(job):
                with metrics.track_worker():
                    return await pipeline.process(job.payload)
        """
        if self.enabled and ACTIVE_WORKERS is not None:
            ACTIVE_WORKERS.inc()
        try:
            yield
        finally:
            if self.enabled and ACTIVE_WORKERS is not None:
                ACTIVE_WORKERS.dec()

    def set_queue_size(self, size: int) -> None:
        """Set the current queue size.

        Args:
            size: The number of items currently in the queue.
        """
        if self.enabled and QUEUE_SIZE is not None:
            QUEUE_SIZE.set(size)

    def set_active_workers(self, count: int) -> None:
        """Set the number of active workers.

        Args:
            count: The number of currently active workers.
        """
        if self.enabled and ACTIVE_WORKERS is not None:
            ACTIVE_WORKERS.set(count)

    def increment_active_workers(self) -> None:
        """Increment the active worker count by 1."""
        if self.enabled and ACTIVE_WORKERS is not None:
            ACTIVE_WORKERS.inc()

    def decrement_active_workers(self) -> None:
        """Decrement the active worker count by 1."""
        if self.enabled and ACTIVE_WORKERS is not None:
            ACTIVE_WORKERS.dec()

    @property
    def version(self) -> str:
        """Get the pipeline version."""
        return self._version

    @property
    def schema_version(self) -> str:
        """Get the schema version."""
        return self._schema_version


# Global singleton instance
_metrics: Optional[MetricsCollector] = None


def get_metrics(
    version: str = "2.0.0", schema_version: str = "2.0.0"
) -> MetricsCollector:
    """Get the global MetricsCollector instance.

    Creates a new instance if one doesn't exist. Subsequent calls return
    the same instance (singleton pattern).

    Args:
        version: Pipeline version (only used on first call).
        schema_version: Schema version (only used on first call).

    Returns:
        The global MetricsCollector instance.

    Example:
        metrics = get_metrics()
        metrics.record_processed(success=True)
    """
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector(version=version, schema_version=schema_version)
    return _metrics


def reset_metrics() -> None:
    """Reset the global metrics instance.

    This is primarily useful for testing. In production, you typically
    want to keep the same metrics instance throughout the application lifecycle.
    """
    global _metrics
    _metrics = None


def is_prometheus_available() -> bool:
    """Check if Prometheus client is available.

    Returns:
        True if prometheus_client is installed, False otherwise.
    """
    return PROMETHEUS_AVAILABLE


__all__ = [
    "MetricsCollector",
    "get_metrics",
    "reset_metrics",
    "is_prometheus_available",
    "PROMETHEUS_AVAILABLE",
    # Raw metrics (for advanced usage)
    "IMAGES_PROCESSED",
    "API_CALLS",
    "PROCESSING_TIME",
    "API_LATENCY",
    "QUEUE_SIZE",
    "ACTIVE_WORKERS",
    "PIPELINE_INFO",
]
