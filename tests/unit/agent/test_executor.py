"""
Unit tests for AgentExecutor

Run: pytest tests/unit/agent/test_executor.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio

from lib.oda.agent.executor import (
    AgentExecutor,
    TaskResult,
    ExecutionPolicy,
)
from lib.oda.ontology.actions import ActionResult, ActionType


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
        """Test that governance DENY policy returns failure."""
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
        """Test that hazardous actions create proposals."""
        class HazardousAction(ActionType):
            api_name = "hazardous"
            requires_proposal = True
            async def apply_edits(self, p, c): return None, []

        mock_proposal = MagicMock()
        mock_proposal.id = "prop-123"
        
        with patch.object(executor._governance.registry, 'get', return_value=HazardousAction), \
             patch.object(executor._governance, 'check_execution_policy', return_value="REQUIRE_PROPOSAL"), \
             patch.object(executor, '_create_proposal', return_value=TaskResult(
                 success=True,
                 action_type="hazardous",
                 message="Proposal created",
                 proposal_id="prop-123",
                 data={"requires_approval": True}
             )):
            result = await executor.execute_action("hazardous", {}, "agent")
            assert result.success is True
            assert result.proposal_id is not None
            assert result.data.get("requires_approval") is True

    @pytest.mark.asyncio
    async def test_execute_immediate_success(self, executor):
        """Test successful immediate execution."""
        class SafeAction(ActionType):
            api_name = "safe"
            submission_criteria = []
            
            async def apply_edits(self, p, c): 
                mock_obj = MagicMock()
                mock_obj.id = "obj-1"
                return mock_obj, []

        mock_result = ActionResult(action_type="safe", success=True, created_ids=["obj-1"])

        with patch.object(executor._governance.registry, 'get', return_value=SafeAction), \
             patch.object(executor._governance, 'check_execution_policy', return_value="ALLOW_IMMEDIATE"), \
             patch.object(executor, '_execute_immediate', return_value=TaskResult(
                 success=True,
                 action_type="safe",
                 message="Action executed",
                 data={"created_ids": ["obj-1"]}
             )):
            result = await executor.execute_action("safe", {}, "agent")
            assert result.success is True


class TestConvenienceFunctions:
    """Tests for module-level functions."""

    @pytest.mark.asyncio
    async def test_get_executor_singleton(self):
        import lib.oda.agent.executor as module
        module._executor = None

        with patch('scripts.agent.executor.initialize_database') as mock_init, \
             patch('scripts.agent.executor.ProposalRepository'):
            mock_init.return_value = MagicMock()

            from lib.oda.agent.executor import get_executor
            exec1 = await get_executor()
            exec2 = await get_executor()
            assert exec1 is exec2
