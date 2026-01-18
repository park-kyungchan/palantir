# MathpixPipeline Deployment Guide

Production deployment documentation for the MathpixPipeline - a comprehensive math image parsing system that processes images through 8 pipeline stages (A-H) to extract, align, and regenerate mathematical content.

## Table of Contents

- [Quick Start (Docker)](#quick-start-docker)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Scaling Considerations](#scaling-considerations)
- [Monitoring Endpoints](#monitoring-endpoints)
- [Troubleshooting Guide](#troubleshooting-guide)

---

## Quick Start (Docker)

### Prerequisites

- Docker 24.0+ and Docker Compose v2
- API keys for external services (Mathpix, Anthropic, Gemini)
- Minimum 2GB RAM, 2 CPU cores

### Build and Run

```bash
# Clone repository
git clone <repository-url>
cd mathpix-pipeline

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# MATHPIX_APP_ID=your_app_id
# MATHPIX_APP_KEY=your_app_key
# ANTHROPIC_API_KEY=your_anthropic_key
# GEMINI_API_KEY=your_gemini_key

# Build Docker image
docker build -t mathpix-pipeline:latest -f docs/deployment/docker/Dockerfile .

# Run with docker-compose (recommended)
cd docs/deployment/docker
docker-compose up -d

# Or run directly
docker run -d \
  --name mathpix-pipeline \
  --env-file .env \
  -p 8080:8080 \
  -v $(pwd)/cache:/app/.cache \
  mathpix-pipeline:latest
```

### Verify Deployment

```bash
# Health check
curl http://localhost:8080/health

# Readiness check
curl http://localhost:8080/ready

# Metrics endpoint
curl http://localhost:8080/metrics
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MATHPIX_APP_ID` | Mathpix API application ID for OCR | `app_abc123...` |
| `MATHPIX_APP_KEY` | Mathpix API application key for OCR | `key_xyz789...` |

### Optional Variables (Feature Enhancement)

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude vision analysis | None |
| `GEMINI_API_KEY` | Google Gemini API key for vision fallback | None |

### Pipeline Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PIPELINE_WORKERS` | Number of concurrent processing workers | `4` |
| `PIPELINE_LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `PIPELINE_CACHE_DIR` | Directory for result caching | `.cache/mathpix_pipeline` |
| `PIPELINE_CACHE_TTL` | Cache TTL in seconds (0 = infinite) | `3600` |
| `PIPELINE_CACHE_MAX_SIZE_MB` | Maximum disk cache size in MB | `500` |
| `PIPELINE_MEMORY_CACHE_ITEMS` | Maximum items in memory cache | `1000` |

### Circuit Breaker Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CB_FAILURE_THRESHOLD` | Failures before circuit opens | `5` |
| `CB_SUCCESS_THRESHOLD` | Successes to close circuit | `2` |
| `CB_TIMEOUT_SECONDS` | Time circuit stays open | `60` |
| `CB_HALF_OPEN_MAX_CALLS` | Concurrent calls in half-open state | `1` |

### Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_HOST` | Server bind address | `0.0.0.0` |
| `SERVER_PORT` | Server port | `8080` |
| `SERVER_REQUEST_TIMEOUT` | Request timeout in seconds | `300` |
| `SERVER_MAX_REQUEST_SIZE_MB` | Maximum request body size | `50` |

### Observability Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint | None |
| `OTEL_SERVICE_NAME` | Service name for tracing | `mathpix-pipeline` |
| `PROMETHEUS_ENABLED` | Enable Prometheus metrics | `true` |

---

## Docker Deployment

### Production Dockerfile

The production Dockerfile uses multi-stage builds for optimal image size and security:

```bash
# Build production image
docker build -t mathpix-pipeline:latest -f docs/deployment/docker/Dockerfile .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.12 -t mathpix-pipeline:latest .
```

### Docker Compose

For local development and testing:

```bash
cd docs/deployment/docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See `docker/docker-compose.yml` for the complete configuration.

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.28+
- kubectl configured
- Namespace created: `kubectl create namespace mathpix-pipeline`

### Deploy to Kubernetes

```bash
# Create secrets (do this first!)
kubectl create secret generic mathpix-api-credentials \
  --from-literal=MATHPIX_APP_ID='your_app_id' \
  --from-literal=MATHPIX_APP_KEY='your_app_key' \
  --from-literal=ANTHROPIC_API_KEY='your_anthropic_key' \
  --from-literal=GEMINI_API_KEY='your_gemini_key' \
  -n mathpix-pipeline

# Apply configuration
kubectl apply -f docs/deployment/k8s/configmap.yaml -n mathpix-pipeline

# Deploy application
kubectl apply -f docs/deployment/k8s/deployment.yaml -n mathpix-pipeline

# Expose service
kubectl apply -f docs/deployment/k8s/service.yaml -n mathpix-pipeline

# Verify deployment
kubectl get pods -n mathpix-pipeline
kubectl get svc -n mathpix-pipeline
```

### Configuration Files

| File | Purpose |
|------|---------|
| `k8s/deployment.yaml` | Deployment with 3 replicas, resource limits, probes |
| `k8s/service.yaml` | ClusterIP and LoadBalancer service definitions |
| `k8s/configmap.yaml` | Non-sensitive configuration |
| `k8s/secret.yaml.example` | Template for secrets (do not commit with real values) |

### Horizontal Pod Autoscaler (Optional)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mathpix-pipeline-hpa
  namespace: mathpix-pipeline
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mathpix-pipeline
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Scaling Considerations

### Worker Pool Sizing

The pipeline processes images through 8 stages (A-H). Worker pool sizing affects throughput:

| Workload | Recommended Workers | Notes |
|----------|---------------------|-------|
| Light (< 100 images/hour) | 2-4 | Single pod sufficient |
| Medium (100-1000 images/hour) | 4-8 | 2-3 replicas recommended |
| Heavy (1000+ images/hour) | 8-16 | 3+ replicas with HPA |

**Configuration:**

```yaml
# Environment variable
PIPELINE_WORKERS=4

# Or in Python
from mathpix_pipeline.utils.queue import ProcessingQueue
queue = ProcessingQueue(max_workers=4)
```

### Cache Configuration

Two-tier caching (memory + disk) reduces API calls and improves latency:

| Setting | Light Load | Medium Load | Heavy Load |
|---------|------------|-------------|------------|
| `memory_max_items` | 500 | 1000 | 2000 |
| `max_size_mb` | 250 | 500 | 1000 |
| `default_ttl_seconds` | 7200 | 3600 | 1800 |

**Cache Invalidation:**

```python
from mathpix_pipeline.utils.cache import get_cache

cache = await get_cache()

# Clear all cache
await cache.clear()

# Clear specific namespace (e.g., stage_a results)
await cache.invalidate_namespace("stage_a")

# Cleanup expired entries
await cache.cleanup_expired()
```

### Circuit Breaker Tuning

The circuit breaker protects against cascading failures from external APIs:

| Scenario | failure_threshold | timeout | success_threshold |
|----------|-------------------|---------|-------------------|
| Stable APIs | 5 | 60s | 2 |
| Flaky APIs | 3 | 30s | 3 |
| Critical path | 10 | 120s | 5 |

**Configuration:**

```python
from mathpix_pipeline.utils.circuit_breaker import CircuitBreakerConfig, get_breaker

config = CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=2,
    timeout=60.0,
    half_open_max_calls=1,
)
breaker = get_breaker("mathpix_api", config)
```

### Resource Limits

Recommended Kubernetes resource limits per pod:

| Resource | Request | Limit | Notes |
|----------|---------|-------|-------|
| CPU | 250m | 500m | Scales linearly with workers |
| Memory | 256Mi | 512Mi | Increase for large image batches |
| Ephemeral Storage | 1Gi | 2Gi | For cache directory |

**For high-throughput deployments:**

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1Gi"
```

---

## Monitoring Endpoints

### Health Check Endpoint

**Endpoint:** `GET /health`

Returns basic health status of the service.

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-01-18T10:30:00Z"
}
```

**HTTP Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is unhealthy

### Readiness Check Endpoint

**Endpoint:** `GET /ready`

Checks if the service is ready to accept traffic (API connectivity, cache initialized).

```json
{
  "status": "ready",
  "checks": {
    "mathpix_api": "connected",
    "cache": "initialized",
    "workers": "running"
  }
}
```

**HTTP Status Codes:**
- `200 OK` - Ready to accept traffic
- `503 Service Unavailable` - Not ready

### Prometheus Metrics Endpoint

**Endpoint:** `GET /metrics`

Exposes Prometheus-compatible metrics:

```
# HELP mathpix_images_processed_total Total number of images processed
# TYPE mathpix_images_processed_total counter
mathpix_images_processed_total{status="success"} 1234
mathpix_images_processed_total{status="failure"} 56

# HELP mathpix_api_calls_total Total number of external API calls
# TYPE mathpix_api_calls_total counter
mathpix_api_calls_total{service="mathpix",status="success"} 5678
mathpix_api_calls_total{service="anthropic",status="success"} 1234

# HELP mathpix_processing_seconds Image processing time in seconds by stage
# TYPE mathpix_processing_seconds histogram
mathpix_processing_seconds_bucket{stage="alignment",le="1.0"} 890
mathpix_processing_seconds_bucket{stage="alignment",le="5.0"} 1200

# HELP mathpix_api_latency_seconds External API call latency in seconds
# TYPE mathpix_api_latency_seconds histogram
mathpix_api_latency_seconds_bucket{service="mathpix",le="1.0"} 4500

# HELP mathpix_queue_size Current number of items in the processing queue
# TYPE mathpix_queue_size gauge
mathpix_queue_size 12

# HELP mathpix_active_workers Number of currently active processing workers
# TYPE mathpix_active_workers gauge
mathpix_active_workers 4

# HELP mathpix_pipeline_info Pipeline build and version information
# TYPE mathpix_pipeline_info gauge
mathpix_pipeline_info{version="2.0.0",schema_version="2.0.0"} 1
```

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mathpix-pipeline
  namespace: mathpix-pipeline
spec:
  selector:
    matchLabels:
      app: mathpix-pipeline
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

---

## Troubleshooting Guide

### Common Errors and Solutions

#### 1. "Circuit breaker is OPEN"

**Symptom:** API calls fail immediately with `CircuitOpenError`

**Cause:** Too many consecutive failures to external API

**Solutions:**
1. Check external API status (Mathpix, Anthropic, Gemini)
2. Verify API credentials are valid
3. Check network connectivity
4. Wait for circuit timeout (default: 60s) to reset

```python
# Check circuit breaker status
from mathpix_pipeline.utils.circuit_breaker import get_breaker

breaker = get_breaker("mathpix_api")
stats = breaker.get_stats()
print(f"State: {stats['state']}, Failures: {stats['failure_count']}")

# Manual reset (use with caution)
await breaker.reset()
```

#### 2. "MATHPIX_APP_ID not set"

**Symptom:** Startup fails or Stage B returns empty results

**Cause:** Required environment variables not configured

**Solutions:**
1. Verify `.env` file exists and contains credentials
2. Check environment variable names (case-sensitive)
3. For Kubernetes, verify Secret is correctly mounted

```bash
# Check environment
env | grep MATHPIX

# Kubernetes secret verification
kubectl get secret mathpix-api-credentials -n mathpix-pipeline -o yaml
```

#### 3. "Image validation failed"

**Symptom:** Stage A rejects images

**Cause:** Image doesn't meet validation requirements

**Solutions:**
1. Check image format (PNG, JPEG, WebP supported)
2. Verify image dimensions (min: 50x50, max: 4096x4096)
3. Ensure file is not corrupted
4. Check file size (max: 50MB default)

```python
# Debug validation
from mathpix_pipeline.ingestion import ImageValidator, ImageLoader

loader = ImageLoader()
validator = ImageValidator()

image = await loader.load_from_path("problematic_image.png")
result = validator.validate(image)
print(f"Valid: {result.is_valid}, Issues: {result.checks_failed}")
```

#### 4. "Out of memory" or OOMKilled

**Symptom:** Pod restarts or process crashes

**Cause:** Memory limits too low or memory leak

**Solutions:**
1. Increase memory limits in deployment
2. Reduce `memory_max_items` in cache config
3. Process images in smaller batches
4. Enable disk-only caching

```yaml
# Increase memory limit
resources:
  limits:
    memory: "1Gi"  # Increase from 512Mi
```

```python
# Reduce memory cache
from mathpix_pipeline.utils.cache import CacheConfig, ResultCache

config = CacheConfig(
    memory_max_items=100,  # Reduce from 1000
    enable_disk_cache=True,
    enable_memory_cache=False,  # Disable memory cache
)
cache = ResultCache(config)
```

#### 5. "Timeout exceeded"

**Symptom:** Pipeline processing times out

**Cause:** Complex images or slow API responses

**Solutions:**
1. Increase request timeout
2. Skip unnecessary stages with `PipelineOptions`
3. Process simpler images first (priority queue)

```python
from mathpix_pipeline.schemas.pipeline import PipelineOptions
from mathpix_pipeline.schemas.common import PipelineStage

# Skip human review stage
options = PipelineOptions(
    skip_stages=[PipelineStage.HUMAN_REVIEW],
    export_formats=["json"],
)
result = await pipeline.process(image, options)
```

#### 6. "Alignment confidence too low"

**Symptom:** Stage D produces poor results

**Cause:** Text and vision outputs don't correlate well

**Solutions:**
1. Improve image quality
2. Adjust alignment thresholds
3. Enable human review for low-confidence results

```python
from mathpix_pipeline.alignment import AlignmentEngineConfig

config = AlignmentEngineConfig(
    base_alignment_threshold=0.60,  # Lower threshold
    position_weight=0.4,
    semantic_weight=0.6,
)
```

### Logging Configuration

Enable debug logging for detailed diagnostics:

```bash
# Environment variable
PIPELINE_LOG_LEVEL=DEBUG

# Or in Python
import logging
logging.getLogger("mathpix_pipeline").setLevel(logging.DEBUG)
```

### Support

For additional support:
1. Check logs: `kubectl logs -f deployment/mathpix-pipeline -n mathpix-pipeline`
2. Review metrics dashboard
3. Open an issue with logs, metrics, and reproduction steps

---

## Quick Reference

| Component | Default | Env Variable |
|-----------|---------|--------------|
| Workers | 4 | `PIPELINE_WORKERS` |
| Cache TTL | 3600s | `PIPELINE_CACHE_TTL` |
| Cache Size | 500MB | `PIPELINE_CACHE_MAX_SIZE_MB` |
| Memory Items | 1000 | `PIPELINE_MEMORY_CACHE_ITEMS` |
| Circuit Timeout | 60s | `CB_TIMEOUT_SECONDS` |
| Request Timeout | 300s | `SERVER_REQUEST_TIMEOUT` |
| Health Endpoint | `/health` | - |
| Metrics Endpoint | `/metrics` | - |
