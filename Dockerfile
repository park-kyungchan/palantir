# Multi-Stage Build: Frontend (Node) + Backend (Python)
# Result: Slim Production Image (~200MB)
# Security: Boris Cherny Pattern 3 - Permission Bypass via Sandbox

# ==========================================
# STAGE 1: Frontend Builder
# ==========================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
# Note: In a real repo, we would copy package.json and run install
# COPY frontend/package.json .
# RUN npm ci
# COPY frontend/ .
# RUN npm run build
# For this prototype, we assume artifacts are pre-generated or we mock them.
# We create a dummy dist folder to simulate the build output.
RUN mkdir -p dist/static && \
    echo "<html><body><h1>Orion ODA</h1></body></html>" > dist/index.html

# ==========================================
# STAGE 2: Backend Runtime (Hardened)
# ==========================================
FROM python:3.11-slim AS runtime

# Security: Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    # Security: Disable pip version check for reproducibility
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Security: Create non-root user and group
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/false --create-home appuser

# Install System Deps (if needed for sqlite extensions)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python Deps (as root, before switching user)
COPY pyproject.toml .
RUN pip install "fastapi" "uvicorn" "pydantic>=2.0" "sqlalchemy[asyncio]>=2.0" "aiosqlite" "instructor" "tenacity" "uuid6"

# Copy Backend Code (lib/ is required for core ODA functionality)
COPY --chown=appuser:appgroup lib/ lib/
COPY --chown=appuser:appgroup scripts/ scripts/
COPY --chown=appuser:appgroup data/ data/

# Copy Frontend Artifacts (optional - only if frontend/dist exists)
# Use multi-stage build or conditionally copy in CI/CD pipeline
# COPY --chown=appuser:appgroup frontend/dist /app/frontend/dist

# Environment: Centralized path configuration
ENV ORION_WORKSPACE_ROOT=/app \
    ORION_DB_PATH=/app/.agent/tmp/ontology.db \
    ORION_AGENT_ROOT=/app/.agent

# Security: Create necessary directories with proper permissions
RUN mkdir -p /app/.agent/tmp /app/.agent/memory /app/logs && \
    chown -R appuser:appgroup /app/.agent /app/logs

# Security: Switch to non-root user
USER appuser

# Expose Port
EXPOSE 8000

# Security: Use exec form to avoid shell injection
# Security: Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Entrypoint
CMD ["uvicorn", "scripts.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
