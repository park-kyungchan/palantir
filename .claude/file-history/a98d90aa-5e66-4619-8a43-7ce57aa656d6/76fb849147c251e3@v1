# Plan 4: Production Readiness

> **Version:** 1.0 | **Status:** READY | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction
> **Execute:** `/execute plan_4_production_readiness.md`
> **Prerequisite:** Plans 1-3 completed

---

## Overview

| Item | Value |
|------|-------|
| Complexity | medium |
| Total Tasks | 7 |
| Files Affected | 15 |
| Estimated Time | 3-4 hours |

---

## Production Requirements

| Category | Requirement | Status |
|----------|-------------|--------|
| **Reliability** | 99.9% uptime target | pending |
| **Performance** | < 5s per image average | pending |
| **Scalability** | 100+ concurrent requests | pending |
| **Security** | API key encryption, input validation | pending |
| **Monitoring** | Metrics, tracing, alerting | pending |
| **Documentation** | Deployment guide, runbook | pending |

---

## Tasks

| # | Phase | Task | Status | File |
|---|-------|------|--------|------|
| 1 | Reliability | Add circuit breaker for external APIs | pending | `utils/circuit_breaker.py` |
| 2 | Performance | Implement caching layer | pending | `utils/cache.py` |
| 3 | Scalability | Add async queue for batch processing | pending | `utils/queue.py` |
| 4 | Security | Implement API key management | pending | `utils/secrets.py` |
| 5 | Monitoring | Add Prometheus metrics | pending | `utils/metrics.py` |
| 6 | Monitoring | Add OpenTelemetry tracing | pending | `utils/tracing.py` |
| 7 | Docs | Create deployment guide | pending | `docs/deployment/` |

---

## Implementation Details

### Task 1: Circuit Breaker

Prevent cascade failures when external APIs are down:

```python
# src/mathpix_pipeline/utils/circuit_breaker.py
"""Circuit breaker pattern for external API resilience."""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close
    timeout_seconds: float = 30.0       # Time before trying again
    half_open_max_calls: int = 3        # Max calls in half-open


class CircuitBreaker(Generic[T]):
    """Circuit breaker for external service calls.

    Usage:
        breaker = CircuitBreaker("mathpix_api")

        @breaker.protect
        async def call_mathpix():
            return await client.process(image)

        result = await call_mathpix()
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    def _should_attempt(self) -> bool:
        """Check if request should be attempted."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN")
                    return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.config.half_open_max_calls

        return False

    async def _record_success(self) -> None:
        """Record successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED")
            elif self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)

    async def _record_failure(self) -> None:
        """Record failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (failure)")

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(f"Circuit {self.name}: CLOSED -> OPEN (threshold)")

    def protect(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to protect a function with circuit breaker."""
        async def wrapper(*args, **kwargs) -> T:
            if not self._should_attempt():
                raise CircuitOpenError(
                    f"Circuit {self.name} is OPEN, rejecting request"
                )

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1

            try:
                result = await func(*args, **kwargs)
                await self._record_success()
                return result
            except Exception as e:
                await self._record_failure()
                raise

        return wrapper


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Global circuit breakers
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, config)
    return _breakers[name]
```

### Task 2: Caching Layer

```python
# src/mathpix_pipeline/utils/cache.py
"""Caching layer for pipeline results."""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheConfig:
    """Cache configuration."""
    cache_dir: Path = Path(".cache/mathpix")
    default_ttl_seconds: int = 3600  # 1 hour
    max_size_mb: int = 500


class ResultCache:
    """Cache for pipeline stage results.

    Caches expensive API calls (Mathpix, Claude) to:
    1. Reduce API costs
    2. Speed up repeated processing
    3. Enable offline development

    Usage:
        cache = ResultCache()

        # Try cache first
        cached = await cache.get("text_spec", image_hash)
        if cached:
            return cached

        # Call API
        result = await mathpix.process(image)

        # Store in cache
        await cache.set("text_spec", image_hash, result, ttl=3600)
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, tuple[Any, float]] = {}

    def _get_cache_key(self, namespace: str, key: str) -> str:
        """Generate cache key."""
        return f"{namespace}:{key}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache entry."""
        safe_key = hashlib.sha256(cache_key.encode()).hexdigest()[:32]
        return self.config.cache_dir / f"{safe_key}.json"

    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._get_cache_key(namespace, key)

        # Check memory cache first
        if cache_key in self._memory_cache:
            value, expiry = self._memory_cache[cache_key]
            if time.time() < expiry:
                logger.debug(f"Cache hit (memory): {cache_key}")
                return value
            else:
                del self._memory_cache[cache_key]

        # Check file cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text())
                if time.time() < data["expiry"]:
                    logger.debug(f"Cache hit (disk): {cache_key}")
                    # Promote to memory cache
                    self._memory_cache[cache_key] = (data["value"], data["expiry"])
                    return data["value"]
                else:
                    cache_path.unlink()  # Remove expired
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

        return None

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Store value in cache."""
        cache_key = self._get_cache_key(namespace, key)
        ttl = ttl or self.config.default_ttl_seconds
        expiry = time.time() + ttl

        # Store in memory
        self._memory_cache[cache_key] = (value, expiry)

        # Store on disk
        cache_path = self._get_cache_path(cache_key)
        try:
            cache_path.write_text(json.dumps({
                "value": value,
                "expiry": expiry,
                "created": time.time(),
            }))
            logger.debug(f"Cached: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def invalidate(self, namespace: str, key: str) -> None:
        """Remove entry from cache."""
        cache_key = self._get_cache_key(namespace, key)

        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            cache_path.unlink()

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all entries in namespace."""
        count = 0
        for key in list(self._memory_cache.keys()):
            if key.startswith(f"{namespace}:"):
                del self._memory_cache[key]
                count += 1

        # Note: File cleanup would need namespace tracking
        return count

    @staticmethod
    def compute_image_hash(image_bytes: bytes) -> str:
        """Compute hash for image content."""
        return hashlib.sha256(image_bytes).hexdigest()


# Global cache instance
_cache: Optional[ResultCache] = None


def get_cache(config: Optional[CacheConfig] = None) -> ResultCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = ResultCache(config)
    return _cache
```

### Task 3: Async Queue

```python
# src/mathpix_pipeline/utils/queue.py
"""Async processing queue for batch operations."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Processing job."""
    id: str
    payload: Any
    status: JobStatus = JobStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class ProcessingQueue:
    """Async queue for pipeline jobs.

    Features:
    - Priority queue support
    - Concurrent worker limit
    - Job status tracking
    - Failure recovery

    Usage:
        queue = ProcessingQueue(max_workers=4)

        # Add jobs
        job_id = await queue.enqueue(image_data, priority=1)

        # Process all
        results = await queue.process_all(pipeline.process)

        # Get specific result
        result = await queue.get_result(job_id)
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 1000,
    ):
        self.max_workers = max_workers
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._jobs: dict[str, Job] = {}
        self._processing = False
        self._workers: List[asyncio.Task] = []

    async def enqueue(
        self,
        payload: Any,
        priority: int = 5,  # 1=highest, 10=lowest
    ) -> str:
        """Add job to queue."""
        job_id = str(uuid4())
        job = Job(id=job_id, payload=payload)
        self._jobs[job_id] = job

        await self._queue.put((priority, job_id))
        logger.debug(f"Enqueued job {job_id} with priority {priority}")

        return job_id

    async def process_all(
        self,
        processor: Callable[[Any], Any],
    ) -> List[Job]:
        """Process all jobs in queue."""
        if self._processing:
            raise RuntimeError("Queue is already processing")

        self._processing = True

        # Start workers
        self._workers = [
            asyncio.create_task(self._worker(processor, i))
            for i in range(self.max_workers)
        ]

        # Wait for queue to empty
        await self._queue.join()

        # Stop workers
        for _ in self._workers:
            await self._queue.put((999, None))  # Sentinel

        await asyncio.gather(*self._workers)
        self._processing = False

        return list(self._jobs.values())

    async def _worker(self, processor: Callable, worker_id: int) -> None:
        """Worker coroutine."""
        while True:
            priority, job_id = await self._queue.get()

            if job_id is None:  # Sentinel
                self._queue.task_done()
                break

            job = self._jobs.get(job_id)
            if not job:
                self._queue.task_done()
                continue

            job.status = JobStatus.RUNNING
            logger.debug(f"Worker {worker_id} processing job {job_id}")

            try:
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(job.payload)
                else:
                    result = processor(job.payload)

                job.result = result
                job.status = JobStatus.COMPLETED
                logger.debug(f"Job {job_id} completed")

            except Exception as e:
                job.error = str(e)
                job.status = JobStatus.FAILED
                logger.error(f"Job {job_id} failed: {e}")

            finally:
                self._queue.task_done()

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    @property
    def pending_count(self) -> int:
        """Number of pending jobs."""
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)

    @property
    def completed_count(self) -> int:
        """Number of completed jobs."""
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.COMPLETED)
```

### Task 4: API Key Management

```python
# src/mathpix_pipeline/utils/secrets.py
"""Secure API key management."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class APICredentials:
    """API credentials container."""
    mathpix_app_id: Optional[str] = None
    mathpix_app_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None  # For Gemini


class SecretsManager:
    """Manage API keys securely.

    Priority order:
    1. Environment variables (production)
    2. .env file (development)
    3. Cloud secret managers (AWS, GCP, Azure)

    Never log or expose actual key values.
    """

    def __init__(self):
        self._credentials: Optional[APICredentials] = None

    def load(self) -> APICredentials:
        """Load credentials from available sources."""
        if self._credentials:
            return self._credentials

        credentials = APICredentials()

        # 1. Environment variables
        credentials.mathpix_app_id = os.getenv("MATHPIX_APP_ID")
        credentials.mathpix_app_key = os.getenv("MATHPIX_APP_KEY")
        credentials.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        credentials.google_api_key = os.getenv("GOOGLE_API_KEY")

        # 2. .env file (development only)
        env_path = Path(".env")
        if env_path.exists():
            self._load_env_file(env_path, credentials)

        # Log what was loaded (not the values!)
        self._log_credential_status(credentials)

        self._credentials = credentials
        return credentials

    def _load_env_file(self, path: Path, credentials: APICredentials) -> None:
        """Load from .env file."""
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key == "MATHPIX_APP_ID" and not credentials.mathpix_app_id:
                    credentials.mathpix_app_id = value
                elif key == "MATHPIX_APP_KEY" and not credentials.mathpix_app_key:
                    credentials.mathpix_app_key = value
                elif key == "ANTHROPIC_API_KEY" and not credentials.anthropic_api_key:
                    credentials.anthropic_api_key = value
                elif key == "GOOGLE_API_KEY" and not credentials.google_api_key:
                    credentials.google_api_key = value

    def _log_credential_status(self, credentials: APICredentials) -> None:
        """Log which credentials are available (not values)."""
        status = []
        if credentials.mathpix_app_id and credentials.mathpix_app_key:
            status.append("Mathpix: configured")
        else:
            status.append("Mathpix: MISSING")

        if credentials.anthropic_api_key:
            status.append("Anthropic: configured")
        else:
            status.append("Anthropic: MISSING")

        if credentials.google_api_key:
            status.append("Google: configured")
        else:
            status.append("Google: MISSING")

        logger.info(f"API Credentials: {', '.join(status)}")

    def validate(self) -> List[str]:
        """Validate credentials and return issues."""
        issues = []
        creds = self.load()

        if not creds.mathpix_app_id or not creds.mathpix_app_key:
            issues.append("Mathpix API credentials not configured")

        if not creds.anthropic_api_key and not creds.google_api_key:
            issues.append("No LLM API key configured (need Anthropic or Google)")

        return issues

    @staticmethod
    def mask_key(key: str) -> str:
        """Mask API key for safe logging."""
        if not key or len(key) < 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets() -> SecretsManager:
    """Get global secrets manager."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
```

### Task 5: Prometheus Metrics

```python
# src/mathpix_pipeline/utils/metrics.py
"""Prometheus metrics for monitoring."""

from typing import Optional
import time

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


# Define metrics
if PROMETHEUS_AVAILABLE:
    # Counters
    IMAGES_PROCESSED = Counter(
        "mathpix_images_processed_total",
        "Total images processed",
        ["status"]  # success, failure
    )

    API_CALLS = Counter(
        "mathpix_api_calls_total",
        "Total external API calls",
        ["service", "status"]  # mathpix/anthropic/google, success/failure
    )

    # Histograms
    PROCESSING_TIME = Histogram(
        "mathpix_processing_seconds",
        "Image processing time in seconds",
        ["stage"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    )

    API_LATENCY = Histogram(
        "mathpix_api_latency_seconds",
        "External API call latency",
        ["service"],
        buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )

    # Gauges
    QUEUE_SIZE = Gauge(
        "mathpix_queue_size",
        "Current processing queue size"
    )

    ACTIVE_WORKERS = Gauge(
        "mathpix_active_workers",
        "Number of active processing workers"
    )

    # Info
    PIPELINE_INFO = Info(
        "mathpix_pipeline",
        "Pipeline build information"
    )


class MetricsCollector:
    """Collect and export metrics.

    Usage:
        metrics = MetricsCollector()

        with metrics.time_stage("alignment"):
            result = engine.align(...)

        metrics.record_api_call("mathpix", success=True)
    """

    def __init__(self):
        self.enabled = PROMETHEUS_AVAILABLE

        if self.enabled:
            PIPELINE_INFO.info({
                "version": "2.0.0",
                "schema_version": "2.0.0",
            })

    def record_processed(self, success: bool) -> None:
        """Record image processing result."""
        if self.enabled:
            IMAGES_PROCESSED.labels(
                status="success" if success else "failure"
            ).inc()

    def record_api_call(self, service: str, success: bool) -> None:
        """Record API call."""
        if self.enabled:
            API_CALLS.labels(
                service=service,
                status="success" if success else "failure"
            ).inc()

    def time_stage(self, stage: str):
        """Context manager for timing a stage."""
        class Timer:
            def __init__(self, stage: str, enabled: bool):
                self.stage = stage
                self.enabled = enabled
                self.start: Optional[float] = None

            def __enter__(self):
                self.start = time.perf_counter()
                return self

            def __exit__(self, *args):
                if self.enabled and self.start:
                    duration = time.perf_counter() - self.start
                    PROCESSING_TIME.labels(stage=self.stage).observe(duration)

        return Timer(stage, self.enabled)

    def time_api(self, service: str):
        """Context manager for timing API calls."""
        class Timer:
            def __init__(self, service: str, enabled: bool):
                self.service = service
                self.enabled = enabled
                self.start: Optional[float] = None

            def __enter__(self):
                self.start = time.perf_counter()
                return self

            def __exit__(self, *args):
                if self.enabled and self.start:
                    duration = time.perf_counter() - self.start
                    API_LATENCY.labels(service=self.service).observe(duration)

        return Timer(service, self.enabled)

    def set_queue_size(self, size: int) -> None:
        """Set current queue size."""
        if self.enabled:
            QUEUE_SIZE.set(size)

    def set_active_workers(self, count: int) -> None:
        """Set active worker count."""
        if self.enabled:
            ACTIVE_WORKERS.set(count)


# Global instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
```

### Task 6: OpenTelemetry Tracing

```python
# src/mathpix_pipeline/utils/tracing.py
"""Distributed tracing with OpenTelemetry."""

from contextlib import contextmanager
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class Tracer:
    """Distributed tracing for pipeline operations.

    Usage:
        tracer = Tracer("mathpix-pipeline")

        with tracer.span("process_image", image_id=img_id) as span:
            result = pipeline.process(image)
            span.set_attribute("success", result.success)
    """

    def __init__(self, service_name: str = "mathpix-pipeline"):
        self.service_name = service_name
        self.enabled = OTEL_AVAILABLE

        if self.enabled:
            self._tracer = trace.get_tracer(service_name)
        else:
            self._tracer = None
            logger.warning("OpenTelemetry not available, tracing disabled")

    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        **attributes: Any,
    ):
        """Create a new span."""
        if not self.enabled:
            yield DummySpan()
            return

        with self._tracer.start_as_current_span(
            name,
            kind=kind,
            attributes=attributes,
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def create_span_for_stage(self, stage: str, image_id: str):
        """Create span for pipeline stage."""
        return self.span(
            f"stage_{stage}",
            image_id=image_id,
            stage=stage,
        )

    def create_span_for_api(self, service: str, operation: str):
        """Create span for external API call."""
        return self.span(
            f"api_{service}_{operation}",
            kind=SpanKind.CLIENT,
            service=service,
            operation=operation,
        )


class DummySpan:
    """Dummy span when tracing is disabled."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass


# Global instance
_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "mathpix-pipeline") -> Tracer:
    """Get global tracer."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer
```

### Task 7: Deployment Guide

Create `docs/deployment/README.md`:

```markdown
# MathpixPipeline Deployment Guide

## Quick Start (Docker)

```bash
# Build image
docker build -t mathpix-pipeline:latest .

# Run with environment variables
docker run -p 8000:8000 \
  -e MATHPIX_APP_ID="your-id" \
  -e MATHPIX_APP_KEY="your-key" \
  -e ANTHROPIC_API_KEY="your-key" \
  mathpix-pipeline:latest
```

## Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mathpix-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mathpix-pipeline
  template:
    metadata:
      labels:
        app: mathpix-pipeline
    spec:
      containers:
      - name: pipeline
        image: mathpix-pipeline:latest
        ports:
        - containerPort: 8000
        env:
        - name: MATHPIX_APP_ID
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: mathpix-app-id
        - name: MATHPIX_APP_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: mathpix-app-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MATHPIX_APP_ID` | Yes | Mathpix application ID |
| `MATHPIX_APP_KEY` | Yes | Mathpix API key |
| `ANTHROPIC_API_KEY` | No* | Claude API key |
| `GOOGLE_API_KEY` | No* | Gemini API key |
| `PIPELINE_LOG_LEVEL` | No | Log level (INFO) |
| `CACHE_DIR` | No | Cache directory |

*At least one LLM API key required

## Scaling Considerations

### Horizontal Scaling
- Stateless design allows easy horizontal scaling
- Use Redis for distributed caching
- Configure load balancer for batch endpoints

### Vertical Scaling
- YOLO detection benefits from GPU
- Allocate 2GB+ RAM for large images
- CPU-intensive stages: D, E

### Rate Limiting
- Mathpix: 100 requests/minute (default)
- Claude: Varies by plan
- Implement backpressure in queue

## Monitoring

### Prometheus Endpoints
```
GET /metrics
```

### Key Metrics
- `mathpix_images_processed_total`
- `mathpix_processing_seconds`
- `mathpix_api_calls_total`
- `mathpix_queue_size`

### Alerting Rules
```yaml
# prometheus/alerts.yaml
groups:
- name: mathpix-pipeline
  rules:
  - alert: HighErrorRate
    expr: rate(mathpix_images_processed_total{status="failure"}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate in pipeline"

  - alert: SlowProcessing
    expr: histogram_quantile(0.95, rate(mathpix_processing_seconds_bucket[5m])) > 30
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "P95 processing time > 30s"
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Check environment variables are set
   - Verify keys are valid (not expired)
   - Check rate limits

2. **Out of Memory**
   - Increase container memory limit
   - Enable image size limits in config
   - Reduce batch concurrency

3. **Slow Processing**
   - Check API latency metrics
   - Enable caching
   - Scale horizontally

### Debug Mode

```bash
PIPELINE_LOG_LEVEL=DEBUG python -m mathpix_pipeline.cli process image.png
```
```

---

## Verification Checklist

- [ ] Circuit breaker prevents cascade failures
- [ ] Caching reduces API calls for repeated images
- [ ] Queue handles batch processing efficiently
- [ ] API keys loaded securely
- [ ] Prometheus metrics exposed
- [ ] Tracing spans created correctly
- [ ] Deployment docs complete

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/plan_4_production_readiness.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence

---

## Completion

After completing Plan 4, the MathpixPipeline is production-ready:

- ✅ Full A→H pipeline flow
- ✅ API integrations (Mathpix, Claude/Gemini)
- ✅ Comprehensive testing
- ✅ Production infrastructure
- ✅ Monitoring and observability
