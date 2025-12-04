# Implementation Plan - Phase 4: Observability Integration

## 1. Objective
Integrate OpenTelemetry (OTel) into the Backend to provide tracing and logging capabilities. This ensures visibility into system health and performance, fulfilling the "Production-Ready" requirement.

## 2. Proposed Changes

### A. Backend Integration (`/home/palantir/math/backend`)
- **Dependencies**: Add `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`.
- **Middleware**: Implement `ObservabilityMiddleware` in `app/core/observability.py`.
    - Trace ID generation.
    - Request/Response logging.
    - Error tracking.
- **Main**: Ensure middleware is registered in `main.py` (already done, verify config).

### B. Infrastructure (Optional but Recommended)
- **Jaeger/Zipkin**: Add a tracing backend to `docker-compose.yml` if full visualization is needed.
    - *Decision*: For now, we will log traces to **Console (Stdout)** to keep it lightweight, as requested in "Cleanup" phase.

## 3. Verification Strategy (Turbo Mode)

### Automated Checks (`03_verify.md`)
1.  **Trace Check**:
    - Call `curl http://localhost:8000/api/v1/health`.
    - Check `docker compose logs backend`.
    - Verify logs contain `trace_id` and `span_id`.

## 4. Rollback Plan
- Disable middleware in `main.py` if performance degrades or errors occur.
