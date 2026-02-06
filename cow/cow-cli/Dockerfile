# COW CLI - Multi-stage Docker Build
# Production-ready container for Layout/Content Separation Pipeline

# =============================================================================
# Stage 1: Build
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml README.md ./
COPY cow_cli/ ./cow_cli/

# Create virtual environment and install
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.12-slim AS production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash cow

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --from=builder /app/cow_cli /app/cow_cli

# Create directories for data
RUN mkdir -p /data/input /data/output /data/cache /data/review \
    && chown -R cow:cow /data /app

# Switch to non-root user
USER cow

# Environment variables
ENV COW_CONFIG_PATH=/data/config.yaml \
    COW_OUTPUT_DIR=/data/output \
    COW_CACHE_DIR=/data/cache \
    COW_REVIEW_DB_PATH=/data/review/review.db \
    COW_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD cow --help || exit 1

# Volumes for persistent data
VOLUME ["/data/input", "/data/output", "/data/cache", "/data/review"]

# Default command
ENTRYPOINT ["cow"]
CMD ["--help"]

# =============================================================================
# Stage 3: Development (optional)
# =============================================================================
FROM production AS development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    respx

USER cow

# Override entrypoint for development
ENTRYPOINT ["/bin/bash"]
