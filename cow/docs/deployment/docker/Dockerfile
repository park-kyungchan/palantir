# =============================================================================
# MathpixPipeline Production Dockerfile
# Multi-stage build for optimal size and security
# =============================================================================
#
# Build: docker build -t mathpix-pipeline:latest -f docs/deployment/docker/Dockerfile .
# Run:   docker run -d --env-file .env -p 8080:8080 mathpix-pipeline:latest
#
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# Installs dependencies and builds the application
# -----------------------------------------------------------------------------
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
# Copy only requirements first to leverage Docker cache
WORKDIR /build

# If you have a requirements.txt, copy and install
COPY requirements*.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt 2>/dev/null || \
    pip install \
        aiohttp>=3.9.0 \
        pydantic>=2.0.0 \
        httpx>=0.25.0 \
        pillow>=10.0.0 \
        numpy>=1.24.0 \
        prometheus-client>=0.19.0 \
        opentelemetry-api>=1.21.0 \
        opentelemetry-sdk>=1.21.0 \
        opentelemetry-exporter-otlp>=1.21.0 \
        python-dotenv>=1.0.0 \
        structlog>=23.2.0 \
        uvicorn>=0.24.0 \
        gunicorn>=21.2.0

# Copy source code and install package
COPY src/ ./src/
COPY setup.py pyproject.toml* ./
RUN pip install -e . 2>/dev/null || pip install ./src/

# -----------------------------------------------------------------------------
# Stage 2: Production
# Minimal runtime image with only necessary files
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS production

# Labels for image metadata
LABEL org.opencontainers.image.title="MathpixPipeline" \
      org.opencontainers.image.description="Math image parsing pipeline with 8-stage processing" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.vendor="MathpixPipeline" \
      org.opencontainers.image.source="https://github.com/your-org/mathpix-pipeline"

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Application settings
    PIPELINE_WORKERS=4 \
    PIPELINE_LOG_LEVEL=INFO \
    PIPELINE_CACHE_DIR=/app/.cache/mathpix_pipeline \
    PIPELINE_CACHE_TTL=3600 \
    PIPELINE_CACHE_MAX_SIZE_MB=500 \
    PIPELINE_MEMORY_CACHE_ITEMS=1000 \
    # Server settings
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8080 \
    SERVER_REQUEST_TIMEOUT=300 \
    # Circuit breaker defaults
    CB_FAILURE_THRESHOLD=5 \
    CB_SUCCESS_THRESHOLD=2 \
    CB_TIMEOUT_SECONDS=60 \
    CB_HALF_OPEN_MAX_CALLS=1 \
    # Prometheus metrics
    PROMETHEUS_ENABLED=true

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For image processing
    libgl1-mesa-glx \
    libglib2.0-0 \
    # For curl health checks
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 pipeline && \
    useradd --uid 1000 --gid pipeline --shell /bin/bash --create-home pipeline

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application source
COPY --from=builder /build/src/ ./src/
COPY --chown=pipeline:pipeline scripts/ ./scripts/
COPY --chown=pipeline:pipeline config/ ./config/

# Create cache directory with correct permissions
RUN mkdir -p /app/.cache/mathpix_pipeline && \
    chown -R pipeline:pipeline /app/.cache

# Create log directory
RUN mkdir -p /app/logs && \
    chown -R pipeline:pipeline /app/logs

# Switch to non-root user
USER pipeline

# Expose application port
EXPOSE 8080

# Health check configuration
# Checks /health endpoint every 30 seconds
# Allows 5 seconds for startup, 5 second timeout per check
# Marks unhealthy after 3 consecutive failures
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/health || exit 1

# Volume for persistent cache
VOLUME ["/app/.cache"]

# Default command - using gunicorn with uvicorn workers for production
# Override this if you have a custom entrypoint
CMD ["python", "-m", "uvicorn", "mathpix_pipeline.server:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--access-log"]

# Alternative: Use gunicorn for more control
# CMD ["gunicorn", "mathpix_pipeline.server:app", \
#      "--bind", "0.0.0.0:8080", \
#      "--workers", "4", \
#      "--worker-class", "uvicorn.workers.UvicornWorker", \
#      "--timeout", "300", \
#      "--access-logfile", "-", \
#      "--error-logfile", "-"]
