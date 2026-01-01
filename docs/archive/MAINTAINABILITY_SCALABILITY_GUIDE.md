# Orion Orchestrator: Maintainability & Scalability Guide

> **For**: Solo Developer Implementation
> **Version**: 1.0
> **Date**: 2025-12-27

---

## 1. MAINTAINABILITY PRINCIPLES

### 1.1 Current Architecture Strengths

```
┌─────────────────────────────────────────────────────────────────┐
│                      ORION ORCHESTRATOR V2                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   API       │   │   Kernel    │   │   LLM       │           │
│  │  (FastAPI)  │◄──│  (Runtime)  │──►│ (Instructor)│           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│         │                │                                      │
│         ▼                ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ONTOLOGY LAYER                              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Actions  │  │ Objects  │  │ Proposals│  │  Links   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              STORAGE LAYER                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │  Repository  │  │   Database   │  │   EventBus   │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Maintainability Features**:
1. **Layered Architecture**: Clean separation between API, Business Logic, and Storage
2. **Repository Pattern**: Data access abstracted behind interfaces
3. **Action-Based Mutations**: All changes go through validated, audited actions
4. **Pydantic Everywhere**: Runtime validation prevents invalid states

---

## 2. CODE ORGANIZATION RECOMMENDATIONS

### 2.1 Current Structure (Good)

```
scripts/
├── ontology/           # Domain Layer (THE CORE)
│   ├── ontology_types.py
│   ├── actions.py
│   ├── objects/
│   └── storage/
├── runtime/            # Application Layer
│   ├── kernel.py
│   └── marshaler.py
├── api/                # Presentation Layer
│   ├── main.py
│   ├── routes.py
│   └── dtos.py
├── llm/                # External Integration
│   └── instructor_client.py
└── infrastructure/     # Cross-Cutting
    └── event_bus.py
```

### 2.2 Recommended Additions

```
scripts/
├── ontology/
│   ├── interfaces/         # NEW: Interface definitions
│   │   └── __init__.py
│   ├── value_types/        # NEW: Semantic type wrappers
│   │   └── __init__.py
│   └── queries/            # NEW: OSDK query builders
│       └── __init__.py
├── security/               # NEW: Auth & authorization
│   ├── auth.py
│   ├── roles.py
│   └── permissions.py
├── data/                   # NEW: Data integration
│   ├── connectors/
│   │   ├── base.py
│   │   ├── sqlite.py
│   │   └── postgres.py
│   └── lineage.py
└── config/                 # NEW: Configuration management
    ├── settings.py
    └── logging.py
```

---

## 3. TESTING STRATEGY

### 3.1 Current State

- Test files exist in `scripts/ontology/tests/`, `scripts/action/tests/`
- Coverage is estimated at **30-40%**

### 3.2 Target Test Structure

```
tests/
├── unit/
│   ├── ontology/
│   │   ├── test_ontology_types.py
│   │   ├── test_actions.py
│   │   └── test_proposal.py
│   ├── storage/
│   │   ├── test_repository.py
│   │   └── test_database.py
│   └── runtime/
│       ├── test_kernel.py
│       └── test_marshaler.py
├── integration/
│   ├── test_api_proposals.py
│   ├── test_action_execution.py
│   └── test_full_workflow.py
├── e2e/
│   └── test_scenarios.py
└── conftest.py             # Shared fixtures
```

### 3.3 Key Test Fixtures

```python
# tests/conftest.py

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from scripts.ontology.storage.database import Database
from scripts.ontology.storage.models import Base

@pytest.fixture
async def test_db():
    """In-memory SQLite for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db = Database()
    db._engine = engine
    yield db

    await engine.dispose()

@pytest.fixture
async def proposal_repo(test_db):
    """Pre-configured repository for testing."""
    from scripts.ontology.storage.proposal_repository import ProposalRepository
    return ProposalRepository(test_db)

@pytest.fixture
def action_context():
    """Standard test context."""
    from scripts.ontology.actions import ActionContext
    return ActionContext(actor_id="test-user")
```

### 3.4 Critical Test Cases to Add

```python
# tests/unit/ontology/test_proposal.py

import pytest
from scripts.ontology.objects.proposal import (
    Proposal, ProposalStatus, InvalidTransitionError
)

class TestProposalStateMachine:
    def test_valid_transition_draft_to_pending(self):
        proposal = Proposal(action_type="test_action")
        proposal.submit()
        assert proposal.status == ProposalStatus.PENDING

    def test_invalid_transition_draft_to_executed(self):
        proposal = Proposal(action_type="test_action")
        with pytest.raises(InvalidTransitionError):
            proposal.execute()

    def test_approve_requires_reviewer(self):
        proposal = Proposal(action_type="test_action")
        proposal.submit()
        with pytest.raises(ValueError, match="reviewer_id is required"):
            proposal.approve(reviewer_id=None)

# tests/unit/ontology/test_actions.py

import pytest
from scripts.ontology.actions import (
    ActionType, ActionContext, RequiredField, ValidationError
)

class TestSubmissionCriteria:
    def test_required_field_passes(self):
        criterion = RequiredField("title")
        context = ActionContext(actor_id="test")
        assert criterion.validate({"title": "Test"}, context) is True

    def test_required_field_fails_on_empty(self):
        criterion = RequiredField("title")
        context = ActionContext(actor_id="test")
        with pytest.raises(ValidationError):
            criterion.validate({"title": ""}, context)
```

---

## 4. ERROR HANDLING PATTERNS

### 4.1 Exception Hierarchy

```python
# scripts/exceptions.py

class OrionError(Exception):
    """Base exception for all Orion errors."""
    def __init__(self, message: str, code: str = "ORION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class OntologyError(OrionError):
    """Errors in the ontology layer."""
    pass

class ActionError(OntologyError):
    """Errors during action execution."""
    pass

class ValidationError(ActionError):
    """Submission criteria validation failed."""
    def __init__(self, criterion: str, message: str, details: dict = None):
        self.criterion = criterion
        self.details = details or {}
        super().__init__(f"[{criterion}] {message}", code="VALIDATION_ERROR")

class GovernanceError(OntologyError):
    """Governance policy violations."""
    pass

class ProposalError(OntologyError):
    """Proposal lifecycle errors."""
    pass

class StorageError(OrionError):
    """Persistence layer errors."""
    pass

class ConcurrencyError(StorageError):
    """Optimistic locking failures."""
    def __init__(self, message: str, expected_version: int, actual_version: int):
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(message, code="CONCURRENCY_CONFLICT")
```

### 4.2 API Error Responses

```python
# scripts/api/error_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse
from scripts.exceptions import OrionError, ValidationError, ConcurrencyError

async def orion_exception_handler(request: Request, exc: OrionError):
    """Global handler for Orion exceptions."""
    status_codes = {
        "VALIDATION_ERROR": 400,
        "CONCURRENCY_CONFLICT": 409,
        "NOT_FOUND": 404,
        "FORBIDDEN": 403,
    }

    return JSONResponse(
        status_code=status_codes.get(exc.code, 500),
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": getattr(exc, "details", {})
            }
        }
    )

# Register in main.py
app.add_exception_handler(OrionError, orion_exception_handler)
```

---

## 5. LOGGING STRATEGY

### 5.1 Current State

Basic Python logging with `[%(name)s] %(message)s` format.

### 5.2 Recommended: Structured Logging with structlog

```python
# scripts/config/logging.py

import structlog
import logging.config

def configure_logging(json_output: bool = False):
    """Configure structured logging."""

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Usage in code
logger = structlog.get_logger()

async def execute_action(action_type: str, params: dict):
    log = logger.bind(action_type=action_type)
    log.info("action_started", params=params)

    try:
        result = await _do_execute(action_type, params)
        log.info("action_completed", success=True, duration_ms=result.duration_ms)
        return result
    except Exception as e:
        log.error("action_failed", error=str(e), exc_info=True)
        raise
```

### 5.3 Log Levels by Component

| Component | Level | What to Log |
|-----------|-------|-------------|
| API | INFO | Request/response, status codes |
| Kernel | INFO | Task processing, proposal execution |
| Actions | DEBUG | Parameter validation, edit operations |
| Storage | DEBUG | SQL queries (dev only), transaction boundaries |
| LLM | INFO | Prompt summaries, token counts |

---

## 6. CONFIGURATION MANAGEMENT

### 6.1 Recommended: Pydantic Settings

```python
# scripts/config/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    url: str = "sqlite+aiosqlite:///./data/ontology.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 60

class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseSettings = DatabaseSettings()
    llm: LLMSettings = LLMSettings()
    api: APISettings = APISettings()

# Singleton
settings = Settings()
```

### 6.2 Environment File Template

```bash
# .env.template

# Environment
ENVIRONMENT=development

# Database
DB_URL=sqlite+aiosqlite:///./data/ontology.db
DB_ECHO=false

# LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-...

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
API_CORS_ORIGINS=["http://localhost:3000"]
```

---

## 7. SCALABILITY PATTERNS

### 7.1 Database Scaling Path

```
Phase 1: SQLite (Current)
├── Single-file database
├── Good for development
└── Limit: ~1000 concurrent reads

Phase 2: PostgreSQL
├── Connection pooling via asyncpg
├── JSONB for payload storage
└── Full-text search with pg_trgm

Phase 3: Read Replicas
├── Write to primary
├── Read from replicas
└── Async replication
```

**Migration Example**:

```python
# scripts/ontology/storage/database.py

async def get_database_url() -> str:
    """Get database URL based on environment."""
    from scripts.config.settings import settings

    if settings.environment == Environment.PRODUCTION:
        return settings.database.url  # PostgreSQL in prod
    return "sqlite+aiosqlite:///./data/ontology.db"
```

### 7.2 EventBus Scaling

```python
# scripts/infrastructure/redis_bus.py

import redis.asyncio as redis
import json
from typing import Callable, Awaitable
from scripts.infrastructure.event_bus import DomainEvent

class RedisEventBus:
    """Distributed event bus using Redis Pub/Sub."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis = redis.from_url(redis_url)
        self._handlers: dict[str, list[Callable]] = {}

    async def publish(self, event: DomainEvent):
        """Publish event to Redis channel."""
        channel = f"orion:events:{event.event_type}"
        await self._redis.publish(channel, event.json())

    async def subscribe(self, pattern: str, handler: Callable[[DomainEvent], Awaitable[None]]):
        """Subscribe to event pattern."""
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe(f"orion:events:{pattern}")

        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                event_data = json.loads(message["data"])
                event = DomainEvent(**event_data)
                await handler(event)
```

### 7.3 Kernel Worker Scaling

```python
# scripts/runtime/distributed_kernel.py

import asyncio
from typing import Optional
from scripts.ontology.objects.proposal import ProposalStatus

class DistributedKernel:
    """
    Kernel that can run as multiple workers.
    Uses proposal ID partitioning for distribution.
    """

    def __init__(self, worker_id: str, total_workers: int = 1):
        self.worker_id = worker_id
        self.total_workers = total_workers
        self.worker_index = int(worker_id.split("-")[-1])

    def _should_process(self, proposal_id: str) -> bool:
        """Check if this worker should handle the proposal."""
        # Simple hash-based partitioning
        hash_value = hash(proposal_id) % self.total_workers
        return hash_value == self.worker_index

    async def _process_approved_proposals(self):
        """Only process proposals assigned to this worker."""
        approved = await self.repo.find_by_status(ProposalStatus.APPROVED)

        for proposal in approved:
            if self._should_process(proposal.id):
                await self._execute_proposal(proposal)

# Usage: Run multiple workers
# python -m scripts.runtime.distributed_kernel --worker-id=worker-0 --total-workers=3
# python -m scripts.runtime.distributed_kernel --worker-id=worker-1 --total-workers=3
# python -m scripts.runtime.distributed_kernel --worker-id=worker-2 --total-workers=3
```

---

## 8. DEPLOYMENT CONFIGURATIONS

### 8.1 Development: Docker Compose

```yaml
# docker-compose.yml

version: "3.8"

services:
  orion-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DB_URL=sqlite+aiosqlite:///./data/ontology.db
      - LLM_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./scripts:/app/scripts
    command: uvicorn scripts.api.main:app --host 0.0.0.0 --port 8000 --reload

  orion-kernel:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=development
      - DB_URL=sqlite+aiosqlite:///./data/ontology.db
      - LLM_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./scripts:/app/scripts
    command: python -m scripts.runtime.kernel
    depends_on:
      - orion-api
```

### 8.2 Production: Kubernetes

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: orion-orchestrator
  namespace: orion
spec:
  replicas: 1
  selector:
    matchLabels:
      app: orion
  template:
    metadata:
      labels:
        app: orion
    spec:
      containers:
        - name: api
          image: ghcr.io/yourusername/orion-orchestrator:latest
          ports:
            - containerPort: 8000
          env:
            - name: ENVIRONMENT
              value: production
            - name: DB_URL
              valueFrom:
                secretKeyRef:
                  name: orion-secrets
                  key: database-url
            - name: LLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: orion-secrets
                  key: openai-api-key
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 30

        - name: kernel
          image: ghcr.io/yourusername/orion-orchestrator:latest
          command: ["python", "-m", "scripts.runtime.kernel"]
          env:
            - name: ENVIRONMENT
              value: production
            - name: DB_URL
              valueFrom:
                secretKeyRef:
                  name: orion-secrets
                  key: database-url
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: orion-api
  namespace: orion
spec:
  selector:
    app: orion
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

### 8.3 Dockerfile

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY scripts/ ./scripts/
COPY config/ ./config/

# Create data directory
RUN mkdir -p /app/data

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default command
CMD ["uvicorn", "scripts.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. MONITORING & OBSERVABILITY

### 9.1 Health Check Endpoint

```python
# scripts/api/routes.py

from fastapi import APIRouter
from scripts.ontology.storage.database import get_database

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    db = get_database()

    try:
        async with db.transaction() as session:
            await session.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "checks": {
            "database": db_status,
            "version": "v3.0.0"
        }
    }
```

### 9.2 Metrics with Prometheus

```python
# scripts/infrastructure/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Action metrics
ACTIONS_TOTAL = Counter(
    "orion_actions_total",
    "Total number of action executions",
    ["action_type", "status"]
)

ACTION_DURATION = Histogram(
    "orion_action_duration_seconds",
    "Action execution duration",
    ["action_type"]
)

# Proposal metrics
PROPOSALS_PENDING = Gauge(
    "orion_proposals_pending",
    "Number of pending proposals"
)

PROPOSALS_TOTAL = Counter(
    "orion_proposals_total",
    "Total proposals by status transition",
    ["from_status", "to_status"]
)

# Usage
async def execute_action(action_type: str, params: dict):
    with ACTION_DURATION.labels(action_type=action_type).time():
        result = await _do_execute(action_type, params)
        ACTIONS_TOTAL.labels(
            action_type=action_type,
            status="success" if result.success else "failure"
        ).inc()
        return result
```

---

## 10. DEPENDENCY MANAGEMENT

### 10.1 Current Dependencies (Inferred)

```txt
# requirements.txt (Current)
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
httpx>=0.24.0
instructor>=0.3.0
openai>=1.0.0
```

### 10.2 Recommended Additional Dependencies

```txt
# requirements.txt (Extended)

# Core
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Database
sqlalchemy>=2.0.0
aiosqlite>=0.19.0              # SQLite async
asyncpg>=0.28.0                # PostgreSQL async

# HTTP
httpx>=0.24.0

# LLM
instructor>=0.3.0
openai>=1.0.0

# Logging
structlog>=23.1.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Monitoring (optional)
prometheus-client>=0.17.0

# Development
black>=23.0.0
ruff>=0.0.280
mypy>=1.4.0
```

### 10.3 Lock File Strategy

```bash
# Use pip-tools for deterministic builds
pip install pip-tools

# Generate locked requirements
pip-compile requirements.in -o requirements.txt
pip-compile requirements-dev.in -o requirements-dev.txt

# Install locked versions
pip-sync requirements.txt requirements-dev.txt
```

---

## 11. SUMMARY CHECKLIST

### Immediate Actions (This Week)

- [ ] Add `scripts/config/settings.py` with Pydantic Settings
- [ ] Add `scripts/config/logging.py` with structlog
- [ ] Add `/health` endpoint to API
- [ ] Create `tests/conftest.py` with shared fixtures
- [ ] Add 5 critical unit tests for Proposal and Actions

### Short-term (This Month)

- [ ] Increase test coverage to 60%
- [ ] Add Dockerfile and docker-compose.yml
- [ ] Implement exception hierarchy in `scripts/exceptions.py`
- [ ] Add structured logging throughout codebase
- [ ] Create `.env.template` for configuration

### Medium-term (Next Quarter)

- [ ] Add PostgreSQL connector for production
- [ ] Implement Redis EventBus for distributed events
- [ ] Add Prometheus metrics
- [ ] Create Kubernetes manifests
- [ ] Reach 80% test coverage

---

**Document End**

*For Solo Developer Excellence*
