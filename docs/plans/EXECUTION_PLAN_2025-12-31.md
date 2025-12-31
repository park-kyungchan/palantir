# LLM-Independent Execution Plan: Orion Orchestrator V2 Improvements

**Document ID**: EXEC-2025-12-31
**Created**: 2025-12-31
**Author**: Claude 4.5 Opus (Logic Core)
**Source Audit**: DEEP_DIVE_AUDIT_2025-12-31.md

---

## LLM Independence Declaration

This execution plan is designed to be **platform-agnostic** and executable by:
- Claude Code CLI (any model: Opus, Sonnet, Haiku)
- Antigravity IDE (Claude Opus 4.5, Gemini 3 Pro)
- Claude Agent SDK implementations

**Constraint**: Uses only file operations (Read/Write/Edit) and shell commands (Bash/run_command) that work on ALL platforms. Does NOT use platform-specific features like Task/dispatch_agent (Claude Code only) or browser_subagent (Antigravity only).

---

## Executive Summary

| Phase | Task | Effort | Priority | Risk |
|-------|------|--------|----------|------|
| **0** | Remove Deprecated Modules (R3) | 1h | HIGH | LOW |
| **1** | ActionType Unit Tests (R1) | 4h | HIGH | LOW |
| **2** | AgentExecutor Unit Tests (R2) | 3h | HIGH | MEDIUM |
| **3** | Observability Metrics (R4) | 6h | MEDIUM | LOW |
| **4** | Type Stub Generation (R5) | 2h | LOW | LOW |
| **5** | Action Development Guide (R6) | 3h | LOW | LOW |

**Total Estimated Effort**: 19 hours

---

## Prerequisites

### Environment Requirements

```bash
# Verify Python version
python --version  # Must be 3.11+

# Verify pytest installation
pip show pytest pytest-asyncio pytest-cov

# If not installed:
pip install pytest pytest-asyncio pytest-cov prometheus-client
```

### Repository State Verification

```bash
cd /home/palantir/orion-orchestrator-v2

# Verify no uncommitted changes
git status

# Verify tests pass before changes
pytest tests/ -v --asyncio-mode=auto
```

---

## Phase 0: Remove Deprecated Modules (R3)

**Duration**: 1 hour
**Risk**: LOW (no production dependencies)
**Prerequisite**: None

### Step 0.1: Verify No Production Imports

**Command** (Validation):
```bash
cd /home/palantir/orion-orchestrator-v2
grep -r "from scripts.ontology.db import\|from scripts.ontology.manager import" \
  --include="*.py" --exclude-dir=__pycache__ --exclude-dir=tests
```

**Expected Output**: Empty (no matches) or only test files

**If production imports found**: STOP. Update those files first using migration patterns below.

### Step 0.2: Review Deprecated Files

**Files to Delete**:
```
/home/palantir/orion-orchestrator-v2/scripts/ontology/db.py
/home/palantir/orion-orchestrator-v2/scripts/ontology/manager.py
```

### Step 0.3: Update Test Files (if needed)

**Migration Pattern** - Replace sync ObjectManager with async Repository:

```python
# BEFORE (deprecated)
from scripts.ontology.manager import ObjectManager
manager = ObjectManager()
manager.save(obj)

# AFTER (new pattern)
from scripts.ontology.storage import initialize_database, ActionLogRepository
db = await initialize_database()
repo = ActionLogRepository(db)
await repo.save(obj, actor_id="system")
```

### Step 0.4: Delete Deprecated Files

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Backup first (optional)
mkdir -p .deprecated_backup
cp scripts/ontology/db.py .deprecated_backup/
cp scripts/ontology/manager.py .deprecated_backup/

# Delete files
rm scripts/ontology/db.py
rm scripts/ontology/manager.py
```

### Step 0.5: Validate Removal

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Verify no import errors
python -c "from scripts.ontology import *"

# Run existing tests
pytest tests/e2e/ -v --asyncio-mode=auto
```

**Expected**: All imports succeed, all tests pass

### Phase 0 Quality Gate

- [ ] `grep` returns no production imports of deprecated modules
- [ ] `python -c "from scripts.ontology import *"` succeeds
- [ ] `pytest tests/e2e/` passes
- [ ] Files `db.py` and `manager.py` no longer exist

---

## Phase 1: ActionType Unit Tests (R1)

**Duration**: 4 hours
**Risk**: LOW
**Prerequisite**: Phase 0 complete

### Step 1.1: Create Directory Structure

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

mkdir -p tests/unit/actions
touch tests/unit/__init__.py
touch tests/unit/actions/__init__.py
```

### Step 1.2: Create Shared Fixtures (conftest.py)

**File**: `/home/palantir/orion-orchestrator-v2/tests/conftest.py`

**Content**:
```python
"""
Shared pytest fixtures for Orion Orchestrator V2 tests.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from scripts.ontology.actions import ActionContext, ActionRegistry
from scripts.ontology.storage.database import Database


# =============================================================================
# ACTION CONTEXT FIXTURES
# =============================================================================

@pytest.fixture
def system_context() -> ActionContext:
    """Create a system-level action context."""
    return ActionContext.system()


@pytest.fixture
def user_context() -> ActionContext:
    """Create a user action context."""
    return ActionContext(
        actor_id="user-001",
        correlation_id="test-correlation-123",
        metadata={"source": "pytest"}
    )


@pytest.fixture
def admin_context() -> ActionContext:
    """Create an admin action context."""
    return ActionContext(
        actor_id="admin-001",
        metadata={"role": "administrator"}
    )


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def temp_db() -> AsyncGenerator[Database, None]:
    """Create a temporary in-memory database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_ontology.db"
        database = Database(db_path)
        await database.initialize()
        yield database


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_instructor_client():
    """Mock InstructorClient for LLM action tests."""
    mock_client = MagicMock()
    mock_client.generate = MagicMock()
    mock_client.client = MagicMock()
    mock_client.client.chat.completions.create = MagicMock()
    return mock_client


@pytest.fixture
def clean_registry() -> ActionRegistry:
    """Create a fresh ActionRegistry for isolated tests."""
    return ActionRegistry()
```

### Step 1.3: Create Memory Actions Tests

**File**: `/home/palantir/orion-orchestrator-v2/tests/unit/actions/test_memory_actions.py`

**Content**:
```python
"""
Unit tests for Memory ActionTypes: SaveInsightAction, SavePatternAction

Run: pytest tests/unit/actions/test_memory_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from scripts.ontology.actions import ActionContext, ActionResult
from scripts.ontology.actions.memory_actions import SaveInsightAction, SavePatternAction


class TestSaveInsightAction:
    """Tests for SaveInsightAction."""

    @pytest.fixture
    def action(self):
        return SaveInsightAction()

    @pytest.fixture
    def valid_insight_params(self):
        return {
            "content": {
                "summary": "Test insight summary",
                "domain": "testing",
                "tags": ["unit-test"]
            },
            "provenance": {
                "source_episodic_ids": ["ep-001"],
                "method": "automated"
            }
        }

    def test_submission_criteria_defined(self, action):
        """Verify submission criteria includes RequiredField for content and provenance."""
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(content)" in criteria_names
        assert "RequiredField(provenance)" in criteria_names

    def test_validate_missing_content_fails(self, action, user_context):
        """Verify validation fails when content is missing."""
        errors = action.validate({"provenance": {}}, user_context)
        assert len(errors) > 0

    def test_validate_valid_params_passes(self, action, user_context, valid_insight_params):
        """Verify validation passes for valid parameters."""
        errors = action.validate(valid_insight_params, user_context)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_apply_edits_creates_insight(self, action, user_context, valid_insight_params):
        """Verify apply_edits creates an insight."""
        with patch('scripts.ontology.actions.memory_actions.get_database') as mock_get_db, \
             patch('scripts.ontology.actions.memory_actions.InsightRepository') as MockRepo:
            mock_get_db.return_value = MagicMock()
            MockRepo.return_value = AsyncMock()

            result = await action.apply_edits(valid_insight_params, user_context)
            assert isinstance(result, ActionResult)
            assert result.success is True


class TestSavePatternAction:
    """Tests for SavePatternAction."""

    @pytest.fixture
    def action(self):
        return SavePatternAction()

    def test_submission_criteria_defined(self, action):
        """Verify submission criteria includes RequiredField for structure."""
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(structure)" in criteria_names
```

### Step 1.4: Create LLM Actions Tests

**File**: `/home/palantir/orion-orchestrator-v2/tests/unit/actions/test_llm_actions.py`

**Content**:
```python
"""
Unit tests for LLM ActionTypes: GeneratePlanAction, RouteTaskAction

Run: pytest tests/unit/actions/test_llm_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from scripts.ontology.actions import ActionContext, EditType
from scripts.ontology.actions.llm_actions import GeneratePlanAction, RouteTaskAction


class TestGeneratePlanAction:
    """Tests for GeneratePlanAction."""

    @pytest.fixture
    def action(self):
        return GeneratePlanAction()

    def test_api_name_correct(self, action):
        assert action.api_name == "llm.generate_plan"

    def test_submission_criteria_requires_goal(self, action):
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(goal)" in criteria_names

    def test_validate_missing_goal_fails(self, action, user_context):
        errors = action.validate({}, user_context)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_apply_edits_returns_plan(self, action, user_context):
        """Verify apply_edits returns a Plan and EditOperation."""
        mock_plan = MagicMock()
        mock_plan.id = "plan-123"
        mock_plan.model_dump.return_value = {"id": "plan-123"}

        with patch('scripts.ontology.actions.llm_actions.InstructorClient') as MockClient:
            MockClient.return_value.generate.return_value = mock_plan

            plan, edits = await action.apply_edits({"goal": "Test"}, user_context)

            assert plan.id == "plan-123"
            assert len(edits) == 1
            assert edits[0].edit_type == EditType.CREATE


class TestRouteTaskAction:
    """Tests for RouteTaskAction."""

    @pytest.fixture
    def action(self):
        return RouteTaskAction()

    def test_api_name_correct(self, action):
        assert action.api_name == "llm.route_task"

    def test_submission_criteria_requires_request(self, action):
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(request)" in criteria_names
```

### Step 1.5: Create Learning Actions Tests

**File**: `/home/palantir/orion-orchestrator-v2/tests/unit/actions/test_learning_actions.py`

**Content**:
```python
"""
Unit tests for Learning ActionTypes: SaveLearnerStateAction

Run: pytest tests/unit/actions/test_learning_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from scripts.ontology.actions import ActionContext
from scripts.ontology.actions.learning_actions import SaveLearnerStateAction


class TestSaveLearnerStateAction:
    """Tests for SaveLearnerStateAction."""

    @pytest.fixture
    def action(self):
        return SaveLearnerStateAction()

    @pytest.fixture
    def valid_params(self):
        return {
            "user_id": "learner-001",
            "theta": 1.5,
            "knowledge_state": {"algebra": {"p_know": 0.8}}
        }

    def test_api_name_correct(self, action):
        assert action.api_name == "learning.save_state"

    def test_submission_criteria_defined(self, action):
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(user_id)" in criteria_names
        assert "RequiredField(theta)" in criteria_names

    def test_validate_missing_fields_fails(self, action, user_context):
        errors = action.validate({}, user_context)
        assert len(errors) >= 2

    @pytest.mark.asyncio
    async def test_apply_edits_saves_learner(self, action, user_context, valid_params):
        with patch('scripts.ontology.actions.learning_actions.get_database') as mock_get_db, \
             patch('scripts.ontology.actions.learning_actions.LearnerRepository') as MockRepo:
            mock_get_db.return_value = MagicMock()
            mock_repo = AsyncMock()
            mock_repo.save.return_value = MagicMock(id="learner-db-id")
            MockRepo.return_value = mock_repo

            result = await action.apply_edits(valid_params, user_context)
            assert result.success is True
```

### Step 1.6: Create Logic Actions Tests

**File**: `/home/palantir/orion-orchestrator-v2/tests/unit/actions/test_logic_actions.py`

**Content**:
```python
"""
Unit tests for Logic ActionTypes: ExecuteLogicAction

Run: pytest tests/unit/actions/test_logic_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import patch
import pytest

from scripts.ontology.actions import ActionContext
from scripts.ontology.actions.logic_actions import ExecuteLogicAction


class TestExecuteLogicAction:
    """Tests for ExecuteLogicAction."""

    @pytest.fixture
    def action(self):
        with patch('scripts.ontology.actions.logic_actions.InstructorClient'), \
             patch('scripts.ontology.actions.logic_actions.LogicEngine'):
            return ExecuteLogicAction()

    def test_api_name_correct(self, action):
        assert action.api_name == "execute_logic"

    def test_requires_proposal_false(self, action):
        assert action.requires_proposal is False

    @pytest.mark.asyncio
    async def test_apply_edits_returns_result(self, action, user_context):
        params = {"function_name": "TestFunc", "input_data": {}}
        result, edits = await action.apply_edits(params, user_context)

        assert isinstance(result, dict)
        assert result["function"] == "TestFunc"
        assert len(edits) == 0
```

### Step 1.7: Run Phase 1 Validation

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Run all unit tests
pytest tests/unit/actions/ -v --asyncio-mode=auto

# Run with coverage
pytest tests/unit/actions/ -v --asyncio-mode=auto \
  --cov=scripts.ontology.actions --cov-report=term-missing
```

**Expected**: All tests pass, coverage >60%

### Phase 1 Quality Gate

- [ ] Directory `tests/unit/actions/` exists with 4 test files
- [ ] `conftest.py` exists with shared fixtures
- [ ] `pytest tests/unit/actions/ -v` shows all tests passing
- [ ] No import errors in test files

---

## Phase 2: AgentExecutor Unit Tests (R2)

**Duration**: 3 hours
**Risk**: MEDIUM
**Prerequisite**: Phase 1 complete

### Step 2.1: Create Agent Test Directory

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2
mkdir -p tests/unit/agent
touch tests/unit/agent/__init__.py
```

### Step 2.2: Create AgentExecutor Tests

**File**: `/home/palantir/orion-orchestrator-v2/tests/unit/agent/test_executor.py`

**Content**:
```python
"""
Unit tests for AgentExecutor

Run: pytest tests/unit/agent/test_executor.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio

from scripts.agent.executor import (
    AgentExecutor,
    TaskResult,
    ExecutionPolicy,
)
from scripts.ontology.actions import ActionResult, ActionType
from scripts.ontology.objects.proposal import Proposal


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_creation(self):
        result = TaskResult(success=True, action_type="test", message="OK")
        assert result.success is True
        assert result.data == {}

    def test_to_dict(self):
        result = TaskResult(
            success=True,
            action_type="test",
            message="OK",
            data={"key": "value"}
        )
        d = result.to_dict()
        assert "timestamp" in d
        assert d["data"]["key"] == "value"


class TestAgentExecutorInit:
    """Tests for initialization."""

    def test_not_initialized_by_default(self):
        executor = AgentExecutor()
        assert executor._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        with patch('scripts.agent.executor.initialize_database') as mock_init, \
             patch('scripts.agent.executor.ProposalRepository'):
            mock_init.return_value = MagicMock()

            executor = AgentExecutor()
            result = await executor.initialize()

            assert result.success is True
            assert executor._initialized is True


class TestAgentExecutorExecution:
    """Tests for action execution."""

    @pytest_asyncio.fixture
    async def executor(self):
        with patch('scripts.agent.executor.initialize_database') as mock_init, \
             patch('scripts.agent.executor.ProposalRepository') as MockRepo:
            mock_init.return_value = MagicMock()
            MockRepo.return_value = AsyncMock()

            exec = AgentExecutor()
            await exec.initialize()
            yield exec

    @pytest.mark.asyncio
    async def test_execute_not_initialized(self):
        executor = AgentExecutor()
        result = await executor.execute_action("test", {}, "user")
        assert result.success is False
        assert result.error_code == "NOT_INITIALIZED"

    @pytest.mark.asyncio
    async def test_execute_action_not_found(self, executor):
        with patch.object(executor._governance.registry, 'get', return_value=None):
            result = await executor.execute_action("unknown", {}, "user")
            assert result.success is False
            assert result.error_code == "ACTION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_execute_governance_deny(self, executor):
        class MockAction(ActionType):
            api_name = "denied"
            async def apply_edits(self, p, c): return None, []

        with patch.object(executor._governance.registry, 'get', return_value=MockAction), \
             patch.object(executor._governance, 'check_execution_policy', return_value="DENY"):
            result = await executor.execute_action("denied", {}, "user")
            assert result.success is False
            assert result.error_code == "GOVERNANCE_DENIED"

    @pytest.mark.asyncio
    async def test_execute_require_proposal(self, executor):
        class HazardousAction(ActionType):
            api_name = "hazardous"
            requires_proposal = True
            async def apply_edits(self, p, c): return None, []

        with patch.object(executor._governance.registry, 'get', return_value=HazardousAction), \
             patch.object(executor._governance, 'check_execution_policy', return_value="REQUIRE_PROPOSAL"):
            result = await executor.execute_action("hazardous", {}, "agent")
            assert result.success is True
            assert result.proposal_id is not None
            assert result.data["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_execute_immediate_success(self, executor):
        class SafeAction(ActionType):
            api_name = "safe"
            async def apply_edits(self, p, c): return MagicMock(id="obj-1"), []

        mock_result = ActionResult(action_type="safe", success=True, created_ids=["obj-1"])

        with patch.object(executor._governance.registry, 'get', return_value=SafeAction), \
             patch.object(executor._governance, 'check_execution_policy', return_value="ALLOW_IMMEDIATE"), \
             patch.object(SafeAction, 'execute', return_value=mock_result):
            result = await executor.execute_action("safe", {}, "agent")
            assert result.success is True


class TestConvenienceFunctions:
    """Tests for module-level functions."""

    @pytest.mark.asyncio
    async def test_get_executor_singleton(self):
        import scripts.agent.executor as module
        module._executor = None

        with patch('scripts.agent.executor.initialize_database') as mock_init, \
             patch('scripts.agent.executor.ProposalRepository'):
            mock_init.return_value = MagicMock()

            from scripts.agent.executor import get_executor
            exec1 = await get_executor()
            exec2 = await get_executor()
            assert exec1 is exec2
```

### Step 2.3: Run Phase 2 Validation

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Run executor tests
pytest tests/unit/agent/test_executor.py -v --asyncio-mode=auto

# Run all unit tests together
pytest tests/unit/ -v --asyncio-mode=auto
```

### Phase 2 Quality Gate

- [ ] `tests/unit/agent/test_executor.py` exists
- [ ] All executor tests pass
- [ ] Test coverage for executor >70%

---

## Phase 3: Observability Metrics (R4)

**Duration**: 6 hours
**Risk**: LOW
**Prerequisite**: Phase 2 complete

### Step 3.1: Verify Existing Metrics Infrastructure

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Check existing metrics module
cat scripts/infrastructure/metrics.py | head -100

# Verify Prometheus dependency
pip show prometheus-client
```

### Step 3.2: Create Enhanced Concurrency Metrics

**File**: `/home/palantir/orion-orchestrator-v2/scripts/infrastructure/concurrency_metrics.py`

**Content**:
```python
"""
Enhanced Concurrency Metrics for OCC Tracking

Tracks:
- Backoff duration distribution
- Retry exhaustion events
- Version conflict deltas
"""

from prometheus_client import Counter, Histogram, Gauge

# Backoff behavior
CONCURRENCY_BACKOFF_DURATION = Histogram(
    "orion_concurrency_backoff_duration_seconds",
    "Time spent in exponential backoff",
    labelnames=["attempt", "entity_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 4.0, 8.0]
)

# Retry exhaustion
RETRY_EXHAUSTION_TOTAL = Counter(
    "orion_retry_exhaustion_total",
    "Actions that exhausted all retries",
    labelnames=["action_type"]
)

# Version conflict analysis
VERSION_CONFLICT_DELTA = Histogram(
    "orion_version_conflict_delta",
    "Distance between expected and actual versions",
    labelnames=["entity_type"],
    buckets=[1, 2, 5, 10, 50, 100]
)


def record_backoff(attempt: int, entity_type: str, duration: float) -> None:
    """Record a backoff event."""
    CONCURRENCY_BACKOFF_DURATION.labels(
        attempt=str(attempt),
        entity_type=entity_type
    ).observe(duration)


def record_retry_exhaustion(action_type: str) -> None:
    """Record when an action exhausts all retries."""
    RETRY_EXHAUSTION_TOTAL.labels(action_type=action_type).inc()


def record_version_delta(entity_type: str, expected: int, actual: int) -> None:
    """Record the version difference in a conflict."""
    delta = abs(actual - expected)
    VERSION_CONFLICT_DELTA.labels(entity_type=entity_type).observe(delta)
```

### Step 3.3: Integrate Metrics into ActionType.execute()

**Modification**: Edit `/home/palantir/orion-orchestrator-v2/scripts/ontology/actions/__init__.py`

**Location**: Lines 404-434 (ConcurrencyError handling in execute())

**Add imports at top**:
```python
from scripts.infrastructure.concurrency_metrics import (
    record_backoff,
    record_retry_exhaustion,
    record_version_delta
)
```

**Modify ConcurrencyError handling**:
```python
except ConcurrencyError as e:
    last_error = e

    # Record metrics
    if hasattr(e, 'expected_version') and hasattr(e, 'actual_version'):
        record_version_delta(
            self.object_type.__name__,
            e.expected_version,
            e.actual_version
        )

    if attempt < MAX_RETRIES - 1:
        wait_time = BACKOFF_BASE * (2 ** attempt)

        # Record backoff duration
        record_backoff(attempt, self.object_type.__name__, wait_time)

        logger.warning(f"ConcurrencyError on {self.api_name}, retry {attempt+1}/{MAX_RETRIES}")
        await asyncio.sleep(wait_time)
    else:
        # Record exhaustion
        record_retry_exhaustion(self.api_name)

        logger.error(f"All retries exhausted for {self.api_name}")
        return ActionResult(...)
```

### Step 3.4: Run Phase 3 Validation

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Verify imports work
python -c "from scripts.infrastructure.concurrency_metrics import *"

# Run tests to ensure no regressions
pytest tests/ -v --asyncio-mode=auto
```

### Phase 3 Quality Gate

- [ ] `scripts/infrastructure/concurrency_metrics.py` exists
- [ ] Metrics integration compiles without errors
- [ ] All existing tests still pass

---

## Phase 4: Type Stub Generation (R5)

**Duration**: 2 hours
**Risk**: LOW
**Prerequisite**: Phase 3 complete

### Step 4.1: Generate Stubs

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Install stubgen if needed
pip install mypy

# Generate stubs for OSDK
stubgen scripts/osdk -o stubs/

# Generate stubs for ontology
stubgen scripts/ontology -o stubs/
```

### Step 4.2: Add py.typed Marker

**Commands**:
```bash
cd /home/palantir/orion-orchestrator-v2

# Add typed package marker
touch scripts/py.typed
touch scripts/ontology/py.typed
touch scripts/osdk/py.typed
```

### Phase 4 Quality Gate

- [ ] `stubs/` directory exists with `.pyi` files
- [ ] `py.typed` markers exist in package roots

---

## Phase 5: Action Development Guide (R6)

**Duration**: 3 hours
**Risk**: LOW
**Prerequisite**: Phase 4 complete

### Step 5.1: Create Documentation File

**File**: `/home/palantir/orion-orchestrator-v2/docs/guides/ACTION_DEVELOPMENT.md`

**Content**:
```markdown
# Action Development Guide

## Overview

Actions are the ONLY way to mutate the Ontology in Orion Orchestrator V2.
This guide explains how to create, test, and deploy new ActionType classes.

## ActionType Structure

```python
from scripts.ontology.actions import (
    ActionType,
    ActionContext,
    ActionResult,
    RequiredField,
    EditOperation,
    EditType,
    register_action
)

@register_action
class MyAction(ActionType[MyEntity]):
    """Docstring explains what this action does."""

    api_name = "my_domain.my_action"
    object_type = MyEntity
    submission_criteria = [
        RequiredField("title"),
        MaxLength("title", 200),
    ]
    side_effects = []
    requires_proposal = False  # Set True for hazardous actions

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[MyEntity], List[EditOperation]]:
        # 1. Create/modify entity
        entity = MyEntity(**params)

        # 2. Persist via repository
        repo = MyEntityRepository(get_database())
        await repo.save(entity, actor_id=context.actor_id)

        # 3. Return entity and edit operations
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="MyEntity",
            object_id=entity.id,
            changes=params
        )
        return entity, [edit]
```

## Validation with SubmissionCriteria

Available validators:
- `RequiredField(field_name)` - Field must be present and non-empty
- `AllowedValues(field_name, [values])` - Field must be in allowed list
- `MaxLength(field_name, max)` - String field max length
- `CustomValidator(name, fn, error_msg)` - Custom validation function

## Testing Your Action

```python
@pytest.mark.asyncio
async def test_my_action_validates():
    action = MyAction()
    context = ActionContext(actor_id="test")

    # Should fail without required fields
    errors = action.validate({}, context)
    assert len(errors) > 0

    # Should pass with valid params
    errors = action.validate({"title": "Test"}, context)
    assert len(errors) == 0
```

## Governance

Actions with `requires_proposal = True` will:
1. Create a Proposal instead of executing immediately
2. Require human approval before execution
3. Track in governance audit trail

## Side Effects

Side effects run AFTER successful commit:

```python
from scripts.ontology.actions.side_effects import LogSideEffect, WebhookSideEffect

class MyAction(ActionType):
    side_effects = [
        LogSideEffect(),
        WebhookSideEffect(url="https://hooks.example.com/notify")
    ]
```
```

### Phase 5 Quality Gate

- [ ] `docs/guides/ACTION_DEVELOPMENT.md` exists
- [ ] Guide includes code examples
- [ ] Guide covers testing patterns

---

## Rollback Procedures

### Git-Based Rollback

```bash
cd /home/palantir/orion-orchestrator-v2

# View recent commits
git log --oneline -10

# Rollback to specific commit
git revert <commit-hash>

# Or reset (destructive)
git reset --hard <commit-hash>
```

### Phase-Specific Rollbacks

**Phase 0 (Deprecated Removal)**:
```bash
# Restore from backup
cp .deprecated_backup/db.py scripts/ontology/
cp .deprecated_backup/manager.py scripts/ontology/
```

**Phase 1-2 (Tests)**:
```bash
# Simply delete test files
rm -rf tests/unit/
```

**Phase 3 (Metrics)**:
```bash
# Revert the concurrency_metrics.py
git checkout HEAD -- scripts/infrastructure/concurrency_metrics.py
# Revert ActionType changes
git checkout HEAD -- scripts/ontology/actions/__init__.py
```

---

## Final Validation

After all phases complete:

```bash
cd /home/palantir/orion-orchestrator-v2

# Run complete test suite
pytest tests/ -v --asyncio-mode=auto

# Run with coverage
pytest tests/ --cov=scripts --cov-report=html

# Verify imports
python -c "from scripts.ontology import *; from scripts.agent.executor import *"

# Verify metrics
python -c "from scripts.infrastructure.concurrency_metrics import *"
```

**All validation must pass before considering execution complete.**

---

## Completion Checklist

- [ ] **Phase 0**: Deprecated modules removed
- [ ] **Phase 1**: ActionType unit tests created and passing
- [ ] **Phase 2**: AgentExecutor unit tests created and passing
- [ ] **Phase 3**: Observability metrics integrated
- [ ] **Phase 4**: Type stubs generated
- [ ] **Phase 5**: Action development guide written
- [ ] **Final**: All tests pass, no import errors

---

*Document generated by Claude 4.5 Opus (Logic Core)*
*Based on Deep-Dive Audit 2025-12-31*
*LLM-Independent: Works on Claude Code CLI, Antigravity IDE, Agent SDK*
