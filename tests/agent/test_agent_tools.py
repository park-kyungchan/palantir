"""
Agent Integration Tests for Phase 7.3-7.4

Tests for:
- ObjectQueryTool
- ActionExecutorTool
- FunctionCallTool
- OntologyContextBuilder
- AgentPlanner (models + SimplePlanner)
- PermissionManager
- ConfirmationManager
- ReasoningTrace

Run: pytest tests/agent/test_agent_tools.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
import pytest


# =============================================================================
# Test ObjectQueryTool
# =============================================================================

class TestObjectQueryTool:
    """Tests for ObjectQueryTool from Phase 7.1."""

    def test_import(self):
        """Test that ObjectQueryTool can be imported."""
        from lib.oda.agent.tools import ObjectQueryTool
        assert ObjectQueryTool is not None

    def test_get_object_input(self):
        """Test GetObjectInput model."""
        from lib.oda.agent.tools import GetObjectInput

        input_data = GetObjectInput(
            object_type="Task",
            object_id="task-123"
        )
        assert input_data.object_type == "Task"
        assert input_data.object_id == "task-123"

    def test_list_objects_input(self):
        """Test ListObjectsInput model."""
        from lib.oda.agent.tools import ListObjectsInput

        input_data = ListObjectsInput(
            object_type="Task",
            limit=10,
            offset=0
        )
        assert input_data.limit == 10

    def test_search_objects_input(self):
        """Test SearchObjectsInput model."""
        from lib.oda.agent.tools import SearchObjectsInput

        input_data = SearchObjectsInput(
            object_type="Task",
            query="status:pending"
        )
        assert input_data.query == "status:pending"


# =============================================================================
# Test ActionExecutorTool
# =============================================================================

class TestActionExecutorTool:
    """Tests for ActionExecutorTool from Phase 7.1."""

    def test_import(self):
        """Test that ActionExecutorTool can be imported."""
        from lib.oda.agent.tools import ActionExecutorTool
        assert ActionExecutorTool is not None

    def test_execute_action_input(self):
        """Test ExecuteActionInput model."""
        from lib.oda.agent.tools import ExecuteActionInput

        input_data = ExecuteActionInput(
            action_type="task.create",
            params={"title": "Test Task"}
        )
        assert input_data.action_type == "task.create"
        assert input_data.params["title"] == "Test Task"

    def test_get_action_schema_input(self):
        """Test GetActionSchemaInput model."""
        from lib.oda.agent.tools import GetActionSchemaInput

        input_data = GetActionSchemaInput(action_type="task.create")
        assert input_data.action_type == "task.create"

    def test_list_actions_input(self):
        """Test ListActionsInput model."""
        from lib.oda.agent.tools import ListActionsInput

        input_data = ListActionsInput(
            namespace="task",
            filter_hazardous=False,
        )
        assert input_data.namespace == "task"
        assert input_data.filter_hazardous is False


# =============================================================================
# Test FunctionCallTool
# =============================================================================

class TestFunctionCallTool:
    """Tests for FunctionCallTool from Phase 7.1."""

    def test_import(self):
        """Test that FunctionCallTool can be imported."""
        from lib.oda.agent.tools import FunctionCallTool
        assert FunctionCallTool is not None

    def test_function_definition(self):
        """Test FunctionDefinition model."""
        from lib.oda.agent.tools import FunctionDefinition

        func_def = FunctionDefinition(
            name="create_task",
            description="Create a new task",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string"}
                },
                "required": ["title"]
            }
        )
        assert func_def.name == "create_task"
        assert "title" in func_def.parameters["properties"]

    def test_function_call_request(self):
        """Test FunctionCallRequest model."""
        from lib.oda.agent.tools import FunctionCallRequest

        request = FunctionCallRequest(
            name="create_task",
            arguments={"title": "Test"}
        )
        assert request.name == "create_task"


# =============================================================================
# Test OntologyContextBuilder
# =============================================================================

class TestOntologyContextBuilder:
    """Tests for OntologyContextBuilder from Phase 7.2."""

    def test_import(self):
        """Test that OntologyContextBuilder can be imported."""
        from lib.oda.agent.context_builder import OntologyContextBuilder
        assert OntologyContextBuilder is not None

    def test_config(self):
        """Test ContextBuilderConfig model."""
        from lib.oda.agent.context_builder import (
            ContextBuilderConfig,
            ContextOutputFormat,
        )

        config = ContextBuilderConfig(
            include_object_types=True,
            include_actions=True,
            include_link_graph=False,
            output_format=ContextOutputFormat.JSON
        )
        assert config.include_object_types is True
        assert config.output_format == ContextOutputFormat.JSON


# =============================================================================
# Test AgentPlanner (Phase 7.3.1)
# =============================================================================

class TestAgentPlanner:
    """Tests for AgentPlanner with mocked LLM."""

    def test_import(self):
        """Test that AgentPlanner can be imported."""
        from lib.oda.agent.planner import AgentPlanner, SimplePlanner
        assert AgentPlanner is not None
        assert SimplePlanner is not None

    def test_planner_config(self):
        """Test PlannerConfig model."""
        from lib.oda.agent.planner import PlannerConfig

        config = PlannerConfig(
            max_iterations=10,
            enable_reflection=True,
            require_action_rationale=True,
        )
        assert config.max_iterations == 10
        assert config.enable_reflection is True

    def test_planned_action(self):
        """Test PlannedAction model."""
        from lib.oda.agent.planner import PlannedAction

        action = PlannedAction(
            action_type="task.create",
            params={"title": "Test"},
            rationale="Creating a task for testing"
        )
        assert action.action_type == "task.create"
        assert action.rationale is not None

    def test_observation(self):
        """Test Observation model."""
        from lib.oda.agent.planner import Observation

        obs = Observation(
            source="tool_result",
            content={"message": "Task created successfully"},
            timestamp=datetime.now()
        )
        assert obs.source == "tool_result"

    def test_thought(self):
        """Test Thought model."""
        from lib.oda.agent.planner import Thought, ThoughtType

        thought = Thought(
            content="I should create a task first",
            thought_type=ThoughtType.REASONING,
        )
        assert thought.thought_type == ThoughtType.REASONING

    @pytest.mark.asyncio
    async def test_simple_planner_execute_all(self):
        """Test SimplePlanner.execute_all() with empty actions."""
        from lib.oda.agent.planner import SimplePlanner, PlannerConfig

        config = PlannerConfig(max_iterations=5)
        planner = SimplePlanner(actions=[], config=config)
        results = await planner.execute_all()
        assert results == []


# =============================================================================
# Test ReasoningTrace (Phase 7.3.2)
# =============================================================================

class TestReasoningTrace:
    """Tests for ReasoningTrace logging."""

    def test_import(self):
        """Test that trace components can be imported."""
        from lib.oda.agent.trace import (
            ReasoningTrace,
            TraceLogger,
            TraceEvent,
            TraceLevel,
        )
        assert ReasoningTrace is not None
        assert TraceLogger is not None

    def test_trace_event(self):
        """Test TraceEvent model."""
        from lib.oda.agent.trace import TraceEvent, TraceEventType

        event = TraceEvent(
            event_type=TraceEventType.OBSERVATION,
            content={"message": "Observed file change"},
            metadata={"file": "test.py"}
        )
        assert event.event_type == TraceEventType.OBSERVATION
        assert event.metadata["file"] == "test.py"

    def test_reasoning_trace(self):
        """Test ReasoningTrace creation and event adding."""
        from lib.oda.agent.trace import ReasoningTrace, TraceEventType

        trace = ReasoningTrace(
            trace_id="trace-001",
            actor_id="test-agent",
            goal="Test task"
        )
        assert trace.trace_id == "trace-001"
        assert len(trace.events) == 0

        trace.add_event(
            event_type=TraceEventType.THOUGHT,
            content={"content": "Planning next step"},
        )
        assert len(trace.events) == 1

    def test_trace_logger(self):
        """Test TraceLogger functionality."""
        from lib.oda.agent.trace import TraceLogger, TraceLevel

        logger = TraceLogger(
            actor_id="test-agent",
            goal="Test task",
            level=TraceLevel.DETAILED
        )
        assert logger.trace.actor_id == "test-agent"
        assert logger.level == TraceLevel.DETAILED

    @pytest.mark.asyncio
    async def test_trace_logger_logging(self):
        """Test TraceLogger.log_* methods."""
        from lib.oda.agent.trace import TraceLogger, TraceLevel

        logger = TraceLogger(
            actor_id="test-agent",
            goal="Test task",
            level=TraceLevel.DEBUG
        )

        # Log various events
        logger.log_observation({"message": "File found", "path": "/test.py"}, source="tool_result")
        logger.log_thought("Should read the file")
        logger.log_action_planned("file.read", {"file_path": "/test.py"}, rationale="Need file content")
        logger.log_action_executed("file.read", {"success": True, "data": {"size": 1}})

        # End trace
        completed_trace = logger.complete("completed")
        assert completed_trace is not None
        assert len(completed_trace.events) >= 5  # includes session start/end


# =============================================================================
# Test ConfirmationManager (Phase 7.3.3)
# =============================================================================

class TestConfirmationManager:
    """Tests for ConfirmationManager workflow."""

    def test_import(self):
        """Test that confirmation components can be imported."""
        from lib.oda.agent.confirmation import (
            ConfirmationManager,
            ConfirmationRequest,
            ConfirmationResponse,
            ConfirmationStatus,
        )
        assert ConfirmationManager is not None
        assert ConfirmationRequest is not None

    def test_confirmation_request(self):
        """Test ConfirmationRequest model."""
        from lib.oda.agent.confirmation import ConfirmationRequest, UrgencyLevel

        request = ConfirmationRequest(
            id="req-001",
            action_type="file.delete",
            params={"file_path": "/test.py"},
            rationale="User requested file deletion",
            risks=["Deletes a file"],
            urgency=UrgencyLevel.HIGH,
        )
        assert request.id == "req-001"
        assert request.urgency == UrgencyLevel.HIGH

    def test_confirmation_response(self):
        """Test ConfirmationResponse model."""
        from lib.oda.agent.confirmation import ConfirmationResponse

        response = ConfirmationResponse(
            request_id="req-001",
            approved=True,
            responder_id="user-123",
            comment="Approved for deletion"
        )
        assert response.approved is True

    @pytest.mark.asyncio
    async def test_confirmation_manager_confirm_and_execute_default_deny(self):
        """Test ConfirmationManager.confirm_and_execute() default console auto-reject."""
        from lib.oda.agent.confirmation import ConfirmationManager

        manager = ConfirmationManager()

        result = await manager.confirm_and_execute(
            action_type="file.delete",
            params={"file_path": "/test.py"},
            rationale="Test deletion",
            actor_id="user-123",
            timeout_seconds=5,
        )
        assert result["confirmed"] is False
        assert result["request"].action_type == "file.delete"

    @pytest.mark.asyncio
    async def test_confirmation_manager_create_proposal(self):
        """Test ConfirmationManager.create_proposal()."""
        from lib.oda.agent.confirmation import (
            ConfirmationManager,
        )

        manager = ConfirmationManager()

        request = await manager.create_proposal(
            action_type="file.delete",
            params={"file_path": "/test.py"},
            rationale="Test deletion",
            actor_id="user-123",
        )
        assert request.proposal_id is not None


# =============================================================================
# Test PermissionManager (Phase 7.3.4)
# =============================================================================

class TestPermissionManager:
    """Tests for PermissionManager with RBAC."""

    def test_import(self):
        """Test that permission components can be imported."""
        from lib.oda.agent.permissions import (
            PermissionManager,
            AgentIdentity,
            RoleType,
            PermissionLevel,
        )
        assert PermissionManager is not None
        assert RoleType is not None

    def test_agent_identity(self):
        """Test AgentIdentity model."""
        from lib.oda.agent.permissions import AgentIdentity, RoleType

        identity = AgentIdentity(
            id="agent-001",
            name="Test Agent",
            roles=[RoleType.DEVELOPER.value]
        )
        assert identity.id == "agent-001"
        assert RoleType.DEVELOPER.value in identity.roles

    def test_permission_level_enum(self):
        """Test PermissionLevel enum values."""
        from lib.oda.agent.permissions import PermissionLevel

        assert PermissionLevel.EXECUTE.value == "execute"
        assert PermissionLevel.PROPOSE.value == "propose"
        assert PermissionLevel.VIEW.value == "view"
        assert PermissionLevel.DENY.value == "deny"

    def test_agent_role_permissions(self):
        """Test predefined role types exist."""
        from lib.oda.agent.permissions import RoleType

        # Verify all roles exist
        assert RoleType.ADMIN is not None
        assert RoleType.OPERATOR is not None
        assert RoleType.DEVELOPER is not None
        assert RoleType.AUDITOR is not None
        assert RoleType.AGENT is not None
        assert RoleType.GUEST is not None

    def test_permission_manager_check(self):
        """Test PermissionManager.check_permission()."""
        from lib.oda.agent.permissions import PermissionManager, PermissionLevel, RoleType

        manager = PermissionManager()
        manager.register_agent(agent_id="agent-001", name="Test Agent", roles=[RoleType.DEVELOPER.value])

        # Developer can execute safe read actions
        result = manager.check_permission(agent_id="agent-001", action_type="file.read")
        assert result.allowed is True
        assert result.level == PermissionLevel.EXECUTE

        # Developer can propose mutations
        result2 = manager.check_permission(agent_id="agent-001", action_type="file.write")
        assert result2.allowed is True
        assert result2.level == PermissionLevel.PROPOSE

    def test_permission_manager_deny_guest(self):
        """Test that guest role has limited permissions."""
        from lib.oda.agent.permissions import PermissionManager, PermissionLevel, RoleType

        manager = PermissionManager()
        manager.register_agent(agent_id="guest-001", name="Guest Agent", roles=[RoleType.GUEST.value])

        # Guest cannot execute delete
        result = manager.check_permission(agent_id="guest-001", action_type="file.delete")
        assert result.allowed is False
        assert result.level == PermissionLevel.DENY


# =============================================================================
# Test AgentLLMAdapter (Phase 7.4.1)
# =============================================================================

class TestAgentLLMAdapter:
    """Tests for AgentLLMAdapter integration."""

    def test_import(self):
        """Test that adapter components can be imported."""
        from lib.oda.llm.agent_adapter import (
            AgentLLMAdapter,
            OpenAIAgentAdapter,
            ClaudeCodeAgentAdapter,
            build_agent_adapter,
        )
        assert AgentLLMAdapter is not None
        assert build_agent_adapter is not None

    def test_agent_tool(self):
        """Test AgentTool model."""
        from lib.oda.llm.agent_adapter import AgentTool

        tool = AgentTool(
            name="create_task",
            description="Create a new task",
            parameters={
                "type": "object",
                "properties": {"title": {"type": "string"}}
            }
        )
        assert tool.name == "create_task"

    def test_tool_call_request(self):
        """Test ToolCallRequest model."""
        from lib.oda.llm.agent_adapter import ToolCallRequest

        request = ToolCallRequest(
            tool_name="create_task",
            arguments={"title": "Test"}
        )
        assert request.tool_name == "create_task"

    def test_build_adapter_openai(self, monkeypatch):
        """Test build_agent_adapter for OpenAI."""
        from lib.oda.llm.agent_adapter import build_agent_adapter, OpenAIAgentAdapter
        from lib.oda.llm.config import LLMProviderType

        # Provide minimal config so OPENAI adapter can be constructed deterministically.
        monkeypatch.setenv("ORION_LLM_BASE_URL", "http://localhost:9999/v1")
        monkeypatch.setenv("ORION_LLM_API_KEY", "test-key")
        monkeypatch.setenv("ORION_LLM_MODEL", "gpt-4o-mini")

        adapter = build_agent_adapter(provider_type=LLMProviderType.OPENAI)
        assert isinstance(adapter, OpenAIAgentAdapter)

    def test_build_adapter_claude(self):
        """Test build_agent_adapter for Claude."""
        from lib.oda.llm.agent_adapter import build_agent_adapter, ClaudeCodeAgentAdapter
        from lib.oda.llm.config import LLMProviderType

        adapter = build_agent_adapter(provider_type=LLMProviderType.CLAUDE_CODE)
        assert isinstance(adapter, ClaudeCodeAgentAdapter)


# =============================================================================
# Test MCP Agent Tools (Phase 7.4.2)
# =============================================================================

class TestMCPAgentTools:
    """Tests for MCP tool exposure."""

    def test_import(self):
        """Test that MCP tools can be imported."""
        from lib.oda.mcp.agent_tools import (
            get_agent_tools,
            register_agent_tools,
            AgentToolHandlers,
        )
        assert get_agent_tools is not None
        assert register_agent_tools is not None

    def test_get_agent_tools(self):
        """Test get_agent_tools returns tool definitions."""
        from lib.oda.mcp.agent_tools import get_agent_tools

        tools = get_agent_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure
        tool_names = [t.name for t in tools]
        assert "agent_execute" in tool_names
        assert "agent_list_actions" in tool_names
        assert "agent_plan" in tool_names

    def test_tool_handler_init(self):
        """Test AgentToolHandlers initialization."""
        from lib.oda.mcp.agent_tools import AgentToolHandlers

        handlers = AgentToolHandlers()
        assert handlers is not None

    @pytest.mark.asyncio
    async def test_handler_list_actions(self):
        """Test agent_list_actions handler."""
        from lib.oda.mcp.agent_tools import AgentToolHandlers

        mock_executor = MagicMock()
        mock_executor.initialize = AsyncMock()
        mock_executor.list_actions.return_value = MagicMock(
            data={"actions": [{"api_name": "file.read"}], "safe": [], "hazardous": []}
        )

        handlers = AgentToolHandlers(executor=mock_executor)
        result = await handlers.handle_agent_list_actions({})
        assert "actions" in result
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_handler_check_permission(self):
        """Test agent_check_permission handler."""
        from lib.oda.mcp.agent_tools import AgentToolHandlers
        from lib.oda.agent.permissions import PermissionCheckResult, PermissionLevel

        mock_perm = MagicMock()
        mock_perm.check_with_governance.return_value = PermissionCheckResult(
            allowed=True,
            level=PermissionLevel.EXECUTE,
            reason="Allowed",
        )
        handlers = AgentToolHandlers(permission_manager=mock_perm)

        result = await handlers.handle_agent_check_permission({
            "agent_id": "test-agent",
            "action_type": "file.read"
        })
        assert "allowed" in result


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_permission_manager_basic_integration(self):
        """Test permission manager works with default roles."""
        from lib.oda.agent.permissions import PermissionManager, RoleType

        manager = PermissionManager()
        manager.register_agent(agent_id="test-agent", roles=[RoleType.DEVELOPER.value])
        result = manager.check_permission("test-agent", "file.read")
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_trace_with_confirmation(self):
        """Test trace logging during confirmation workflow."""
        from lib.oda.agent.trace import TraceLogger, TraceLevel
        from lib.oda.agent.confirmation import (
            ConfirmationManager,
        )

        # Setup trace logger
        logger = TraceLogger(
            actor_id="test-agent",
            goal="Delete file with confirmation",
            level=TraceLevel.DETAILED
        )

        # Setup confirmation manager
        conf_manager = ConfirmationManager()

        # Log the confirmation request
        logger.log_action_planned("file.delete", {"file_path": "/test.py"}, rationale="Test deletion")
        request = await conf_manager.create_proposal(
            action_type="file.delete",
            params={"file_path": "/test.py"},
            rationale="Test deletion",
            actor_id="admin",
        )
        logger.log_observation({"confirmation_request_id": request.id, "proposal_id": request.proposal_id}, source="confirmation")

        completed_trace = logger.complete("completed")
        assert len(completed_trace.events) >= 3


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
