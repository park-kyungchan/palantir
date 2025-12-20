
# Multi-Stage Build: Frontend (Node) + Backend (Python)
# Result: Slim Production Image (~200MB)

# ==========================================
# STAGE 1: Frontend Builder
# ==========================================
FROM node:18-alpine as frontend-builder
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
# STAGE 2: Backend Runtime
# ==========================================
FROM python:3.11-slim as runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

# Install System Deps (if needed for sqlite extensions)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python Deps
COPY pyproject.toml .
RUN pip install "fastapi" "uvicorn" "pydantic>=2.0" "sqlalchemy[asyncio]>=2.0" "aiosqlite" "instructor" "tenacity" "uuid6"

# Copy Backend Code
COPY scripts/ scripts/
COPY data/ data/

# Copy Frontend Artifacts from Stage 1
# In real usage: COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
# Since we created the file locally in the IDE, we copy from context
COPY frontend/dist /app/frontend/dist

# Expose Port
EXPOSE 8000

# Entrypoint
CMD ["uvicorn", "scripts.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
