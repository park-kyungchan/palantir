"""
Math Image Parsing Pipeline - Utility Functions
"""

from .geometry import (
    contour_to_bbox,
    position_to_bbox,
    normalize_bbox,
    calculate_iou,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    get_breaker,
    get_all_breakers,
    reset_all_breakers,
    clear_breakers,
    MATHPIX_API_CONFIG,
    EXTERNAL_SERVICE_CONFIG,
)
from .metrics import (
    MetricsCollector,
    get_metrics,
    reset_metrics,
    is_prometheus_available,
    PROMETHEUS_AVAILABLE,
)
from .secrets import (
    SecretsManager,
    APICredentials,
    SecretsError,
    MissingCredentialError,
    get_secrets,
    reset_secrets,
    mask_key,
)
from .tracing import (
    Tracer,
    TracerConfig,
    DummySpan,
    get_tracer,
    reset_tracer,
    is_tracing_available,
    SpanKindEnum,
    SPAN_KIND_INTERNAL,
    SPAN_KIND_CLIENT,
    OTEL_AVAILABLE,
)
from .queue import (
    JobStatus,
    Job,
    QueueStats,
    ProcessingQueue,
    ProcessorFunc,
)
from .cache import (
    CacheConfig,
    CacheEntry,
    ResultCache,
    get_cache,
    get_cache_sync,
    reset_global_cache,
)

__all__ = [
    # Geometry utilities
    "contour_to_bbox",
    "position_to_bbox",
    "normalize_bbox",
    "calculate_iou",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitOpenError",
    "CircuitState",
    "get_breaker",
    "get_all_breakers",
    "reset_all_breakers",
    "clear_breakers",
    "MATHPIX_API_CONFIG",
    "EXTERNAL_SERVICE_CONFIG",
    # Metrics utilities
    "MetricsCollector",
    "get_metrics",
    "reset_metrics",
    "is_prometheus_available",
    "PROMETHEUS_AVAILABLE",
    # Secrets management
    "SecretsManager",
    "APICredentials",
    "SecretsError",
    "MissingCredentialError",
    "get_secrets",
    "reset_secrets",
    "mask_key",
    # Tracing utilities
    "Tracer",
    "TracerConfig",
    "DummySpan",
    "get_tracer",
    "reset_tracer",
    "is_tracing_available",
    "SpanKindEnum",
    "SPAN_KIND_INTERNAL",
    "SPAN_KIND_CLIENT",
    "OTEL_AVAILABLE",
    # Queue utilities
    "JobStatus",
    "Job",
    "QueueStats",
    "ProcessingQueue",
    "ProcessorFunc",
    # Cache utilities
    "CacheConfig",
    "CacheEntry",
    "ResultCache",
    "get_cache",
    "get_cache_sync",
    "reset_global_cache",
]
