"""
Distributed tracing with OpenTelemetry.

Provides tracing capabilities for the MathpixPipeline with graceful degradation
when OpenTelemetry is not installed. Supports both pipeline stages (INTERNAL spans)
and external API calls (CLIENT spans).

Schema Version: 2.0.0

Usage:
    from mathpix_pipeline.utils.tracing import get_tracer

    tracer = get_tracer()

    # Trace a pipeline stage
    with tracer.create_span_for_stage("alignment", image_id="img_123") as span:
        result = engine.align(...)
        span.set_attribute("success", result.success)
        span.add_event("alignment_complete", {"elements_aligned": 42})

    # Trace an API call
    with tracer.create_span_for_api("mathpix", "process_image") as span:
        response = await client.process(image)
        span.set_attribute("response_size", len(response))
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

# Attempt to import OpenTelemetry with graceful degradation
try:
    from opentelemetry import trace
    from opentelemetry.trace import (
        Span,
        SpanKind,
        Status,
        StatusCode,
        Tracer as OTelTracer,
    )
    from opentelemetry.trace.propagation import set_span_in_context
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Define placeholder types for type hints when OTEL not available
    if TYPE_CHECKING:
        from opentelemetry.trace import Span, SpanKind, Status, StatusCode


# SpanKind constants for use when OTEL is not available
class SpanKindEnum:
    """Span kinds for tracing (mirrors OpenTelemetry SpanKind)."""
    INTERNAL = 0  # Default, internal operation
    SERVER = 1    # Server-side handling of an RPC
    CLIENT = 2    # Client-side of an RPC
    PRODUCER = 3  # Producer sending a message
    CONSUMER = 4  # Consumer receiving a message


@dataclass
class DummyStatus:
    """Dummy status class for when OTEL is not available."""
    code: int = 0
    description: str = ""


class DummySpan:
    """Dummy span implementation when OpenTelemetry is not available.

    Provides no-op implementations of all span methods to allow code
    to run without modification when tracing is disabled.

    Example:
        # This code works whether OTEL is available or not:
        with tracer.span("operation") as span:
            span.set_attribute("key", "value")
            span.add_event("something_happened")
    """

    def set_attribute(self, key: str, value: Any) -> "DummySpan":
        """No-op attribute setter.

        Args:
            key: Attribute name
            value: Attribute value

        Returns:
            Self for method chaining
        """
        return self

    def set_attributes(self, attributes: Dict[str, Any]) -> "DummySpan":
        """No-op bulk attribute setter.

        Args:
            attributes: Dictionary of attributes

        Returns:
            Self for method chaining
        """
        return self

    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
    ) -> "DummySpan":
        """No-op event adder.

        Args:
            name: Event name
            attributes: Optional event attributes
            timestamp: Optional event timestamp (nanoseconds since epoch)

        Returns:
            Self for method chaining
        """
        return self

    def set_status(
        self,
        status: Any,
        description: Optional[str] = None,
    ) -> "DummySpan":
        """No-op status setter.

        Args:
            status: Status object or status code
            description: Optional status description

        Returns:
            Self for method chaining
        """
        return self

    def record_exception(
        self,
        exception: BaseException,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
        escaped: bool = False,
    ) -> "DummySpan":
        """No-op exception recorder.

        Args:
            exception: The exception to record
            attributes: Optional additional attributes
            timestamp: Optional timestamp (nanoseconds since epoch)
            escaped: Whether the exception escaped the span's scope

        Returns:
            Self for method chaining
        """
        return self

    def update_name(self, name: str) -> "DummySpan":
        """No-op name updater.

        Args:
            name: New span name

        Returns:
            Self for method chaining
        """
        return self

    def is_recording(self) -> bool:
        """Check if span is recording.

        Returns:
            Always False for dummy spans
        """
        return False

    def end(self, end_time: Optional[int] = None) -> None:
        """No-op span end.

        Args:
            end_time: Optional end timestamp (nanoseconds since epoch)
        """
        pass

    def get_span_context(self) -> None:
        """Get span context (no-op).

        Returns:
            None for dummy spans
        """
        return None

    def __enter__(self) -> "DummySpan":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        pass


@dataclass
class TracerConfig:
    """Configuration for the Tracer.

    Attributes:
        service_name: Name of the service for tracing
        enabled: Whether tracing is enabled (auto-detected if None)
        default_attributes: Attributes to add to all spans
    """
    service_name: str = "mathpix-pipeline"
    enabled: Optional[bool] = None  # None = auto-detect based on OTEL availability
    default_attributes: Dict[str, Any] = field(default_factory=dict)


class Tracer:
    """Distributed tracing for pipeline operations.

    Provides a unified interface for creating spans that works whether
    OpenTelemetry is installed or not. When OTEL is not available, all
    operations become no-ops via DummySpan.

    Attributes:
        service_name: Name of the service being traced
        enabled: Whether tracing is actually enabled
        config: Tracer configuration

    Example:
        tracer = Tracer("mathpix-pipeline")

        # Basic span
        with tracer.span("process_image", image_id="img_123") as span:
            result = pipeline.process(image)
            span.set_attribute("success", result.success)

        # Pipeline stage span
        with tracer.create_span_for_stage("alignment", "img_123") as span:
            aligned = alignment_engine.align(elements)

        # External API span
        with tracer.create_span_for_api("mathpix", "extract_text") as span:
            response = await mathpix_client.process(image)
            span.set_attribute("response_size", len(response.text))
    """

    def __init__(
        self,
        service_name: str = "mathpix-pipeline",
        config: Optional[TracerConfig] = None,
    ):
        """Initialize the tracer.

        Args:
            service_name: Name of the service for tracing
            config: Optional tracer configuration (overrides service_name if provided)
        """
        self.config = config or TracerConfig(service_name=service_name)
        self.service_name = self.config.service_name

        # Determine if tracing should be enabled
        if self.config.enabled is not None:
            self.enabled = self.config.enabled and OTEL_AVAILABLE
        else:
            self.enabled = OTEL_AVAILABLE

        # Initialize OpenTelemetry tracer if available
        if self.enabled:
            self._tracer: Optional[OTelTracer] = trace.get_tracer(
                self.service_name,
                tracer_provider=trace.get_tracer_provider(),
            )
            logger.info(f"OpenTelemetry tracing enabled for service: {self.service_name}")
        else:
            self._tracer = None
            if not OTEL_AVAILABLE:
                logger.debug(
                    "OpenTelemetry not available, tracing disabled. "
                    "Install with: pip install opentelemetry-api opentelemetry-sdk"
                )

    @contextmanager
    def span(
        self,
        name: str,
        kind: Optional[int] = None,
        attributes: Optional[Dict[str, Any]] = None,
        **extra_attributes: Any,
    ) -> Generator[Any, None, None]:
        """Create a new span as a context manager.

        This is the primary method for creating spans. It automatically
        handles span lifecycle and exception recording.

        Args:
            name: Name of the span
            kind: Span kind (INTERNAL, CLIENT, etc.). Defaults to INTERNAL.
            attributes: Dictionary of span attributes
            **extra_attributes: Additional attributes as keyword arguments

        Yields:
            The span object (real Span or DummySpan)

        Example:
            with tracer.span("process", image_id="123", size=1024) as span:
                result = process_image(image)
                span.set_attribute("result_type", result.type)
        """
        if not self.enabled or self._tracer is None:
            yield DummySpan()
            return

        # Merge attributes
        all_attributes = {**self.config.default_attributes}
        if attributes:
            all_attributes.update(attributes)
        all_attributes.update(extra_attributes)

        # Convert kind to OpenTelemetry SpanKind
        otel_kind = self._convert_span_kind(kind)

        with self._tracer.start_as_current_span(
            name,
            kind=otel_kind,
            attributes=all_attributes if all_attributes else None,
        ) as span:
            try:
                yield span
            except Exception as e:
                # Record exception and set error status
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def _convert_span_kind(self, kind: Optional[int]) -> "SpanKind":
        """Convert kind constant to OpenTelemetry SpanKind.

        Args:
            kind: Span kind constant or None

        Returns:
            OpenTelemetry SpanKind enum value
        """
        if kind is None:
            return SpanKind.INTERNAL

        kind_map = {
            SpanKindEnum.INTERNAL: SpanKind.INTERNAL,
            SpanKindEnum.SERVER: SpanKind.SERVER,
            SpanKindEnum.CLIENT: SpanKind.CLIENT,
            SpanKindEnum.PRODUCER: SpanKind.PRODUCER,
            SpanKindEnum.CONSUMER: SpanKind.CONSUMER,
        }
        return kind_map.get(kind, SpanKind.INTERNAL)

    @contextmanager
    def create_span_for_stage(
        self,
        stage: str,
        image_id: Optional[str] = None,
        **attributes: Any,
    ) -> Generator[Any, None, None]:
        """Create a span for a pipeline stage.

        Pipeline stages (A through H) are internal operations with consistent
        naming and attributes.

        Args:
            stage: Stage identifier (e.g., "alignment", "semantic_graph", "A", "B")
            image_id: Optional image identifier for correlation
            **attributes: Additional attributes for the span

        Yields:
            The span object

        Example:
            with tracer.create_span_for_stage("D", image_id="img_123") as span:
                result = alignment_engine.align(elements)
                span.set_attribute("elements_aligned", len(result))
                span.add_event("alignment_complete")
        """
        span_name = f"pipeline.stage.{stage}"

        span_attributes = {
            "pipeline.stage": stage,
            "pipeline.component": "mathpix-pipeline",
        }

        if image_id:
            span_attributes["pipeline.image_id"] = image_id

        span_attributes.update(attributes)

        with self.span(
            name=span_name,
            kind=SpanKindEnum.INTERNAL,
            attributes=span_attributes,
        ) as span:
            yield span

    @contextmanager
    def create_span_for_api(
        self,
        service: str,
        operation: str,
        **attributes: Any,
    ) -> Generator[Any, None, None]:
        """Create a span for an external API call.

        External API calls (Mathpix, Claude, Gemini) use CLIENT span kind
        to properly represent the outbound request.

        Args:
            service: External service name (e.g., "mathpix", "anthropic", "google")
            operation: Operation being performed (e.g., "process_image", "extract")
            **attributes: Additional attributes for the span

        Yields:
            The span object

        Example:
            with tracer.create_span_for_api("mathpix", "process_image") as span:
                span.set_attribute("request.image_size", len(image_bytes))
                response = await mathpix_client.process(image)
                span.set_attribute("response.text_length", len(response.text))
        """
        span_name = f"api.{service}.{operation}"

        span_attributes = {
            "api.service": service,
            "api.operation": operation,
            "span.kind": "client",
        }
        span_attributes.update(attributes)

        with self.span(
            name=span_name,
            kind=SpanKindEnum.CLIENT,
            attributes=span_attributes,
        ) as span:
            yield span

    @contextmanager
    def create_span_for_batch(
        self,
        batch_id: str,
        total_items: int,
        **attributes: Any,
    ) -> Generator[Any, None, None]:
        """Create a span for batch processing.

        Args:
            batch_id: Unique batch identifier
            total_items: Total number of items in the batch
            **attributes: Additional attributes

        Yields:
            The span object
        """
        span_name = "pipeline.batch"

        span_attributes = {
            "batch.id": batch_id,
            "batch.total_items": total_items,
            "pipeline.component": "mathpix-pipeline",
        }
        span_attributes.update(attributes)

        with self.span(
            name=span_name,
            kind=SpanKindEnum.INTERNAL,
            attributes=span_attributes,
        ) as span:
            yield span

    def get_current_span(self) -> Any:
        """Get the current active span.

        Returns:
            Current span or DummySpan if no span is active or tracing disabled
        """
        if not self.enabled:
            return DummySpan()

        current = trace.get_current_span()
        if current is None:
            return DummySpan()
        return current

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """Inject trace context into a carrier for propagation.

        Useful for passing trace context to external services or
        across process boundaries.

        Args:
            carrier: Dictionary to inject context into (modified in-place)
        """
        if not self.enabled:
            return

        from opentelemetry import propagate
        propagate.inject(carrier)

    def extract_context(self, carrier: Dict[str, str]) -> Any:
        """Extract trace context from a carrier.

        Args:
            carrier: Dictionary containing trace context headers

        Returns:
            Extracted context or None
        """
        if not self.enabled:
            return None

        from opentelemetry import propagate
        return propagate.extract(carrier)


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer(
    service_name: str = "mathpix-pipeline",
    config: Optional[TracerConfig] = None,
) -> Tracer:
    """Get or create the global tracer instance.

    This is the recommended way to access the tracer. It ensures
    a single tracer instance is used throughout the application.

    Args:
        service_name: Name of the service (used on first call)
        config: Optional tracer configuration (used on first call)

    Returns:
        The global Tracer instance

    Example:
        from mathpix_pipeline.utils.tracing import get_tracer

        tracer = get_tracer()
        with tracer.span("my_operation") as span:
            # do work
            pass
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name=service_name, config=config)
    return _tracer


def reset_tracer() -> None:
    """Reset the global tracer instance.

    Primarily useful for testing to ensure a fresh tracer state.
    """
    global _tracer
    _tracer = None


def is_tracing_available() -> bool:
    """Check if OpenTelemetry tracing is available.

    Returns:
        True if OpenTelemetry is installed and importable
    """
    return OTEL_AVAILABLE


# Convenience exports for span kinds
SPAN_KIND_INTERNAL = SpanKindEnum.INTERNAL
SPAN_KIND_CLIENT = SpanKindEnum.CLIENT
SPAN_KIND_SERVER = SpanKindEnum.SERVER
SPAN_KIND_PRODUCER = SpanKindEnum.PRODUCER
SPAN_KIND_CONSUMER = SpanKindEnum.CONSUMER


__all__ = [
    # Main classes
    "Tracer",
    "TracerConfig",
    "DummySpan",
    "DummyStatus",
    # Factory functions
    "get_tracer",
    "reset_tracer",
    "is_tracing_available",
    # Span kinds
    "SpanKindEnum",
    "SPAN_KIND_INTERNAL",
    "SPAN_KIND_CLIENT",
    "SPAN_KIND_SERVER",
    "SPAN_KIND_PRODUCER",
    "SPAN_KIND_CONSUMER",
    # Availability flag
    "OTEL_AVAILABLE",
]
