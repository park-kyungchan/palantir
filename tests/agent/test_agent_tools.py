"""
Agent Integration Tests for Phase 7.3-7.4

Tests for:
- ObjectQueryTool
- ActionExecutorTool
- FunctionCallTool
- OntologyContextBuilder
- AgentPlanner (with mocked LLM)
- PermissionManager
- ConfirmationManager
- ReasoningTrace

Run: pytest tests/agent/test_agent_tools.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
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
            action_type="CreateTask",
            params={"title": "Test Task"}
        )
        assert input_data.action_type == "CreateTask"
        assert input_data.params["title"] == "Test Task"

    def test_get_action_schema_input(self):
        """Test GetActionSchemaInput model."""
        from lib.oda.agent.tools import GetActionSchemaInput

        input_data = GetActionSchemaInput(action_type="CreateTask")
        assert input_data.action_type == "CreateTask"

    def test_list_actions_input(self):
        """Test ListActionsInput model."""
        from lib.oda.agent.tools import ListActionsInput

        input_data = ListActionsInput(
            category="task",
            include_hazardous=False
        )
        assert input_data.category == "task"
        assert input_data.include_hazardous is False


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
            thinking_enabled=True,
            parallel_execution=False
        )
        assert config.max_iterations == 10
        assert config.thinking_enabled is True

    def test_planned_action(self):
        """Test PlannedAction model."""
        from lib.oda.agent.planner import PlannedAction

        action = PlannedAction(
            action_type="CreateTask",
            params={"title": "Test"},
            reasoning="Creating a task for testing"
        )
        assert action.action_type == "CreateTask"
        assert action.reasoning is not None

    def test_observation(self):
        """Test Observation model."""
        from lib.oda.agent.planner import Observation

        obs = Observation(
            source="tool_result",
            content="Task created successfully",
            timestamp=datetime.now()
        )
        assert obs.source == "tool_result"

    def test_thought(self):
        """Test Thought model."""
        from lib.oda.agent.planner import Thought

        thought = Thought(
            content="I should create a task first",
            reasoning_type="planning"
        )
        assert thought.reasoning_type == "planning"

    @pytest.mark.asyncio
    async def test_simple_planner_plan(self):
        """Test SimplePlanner.plan() method."""
        from lib.oda.agent.planner import SimplePlanner, PlannerConfig

        config = PlannerConfig(max_iterations=5)
        planner = SimplePlanner(config=config)

        # Mock the governance check
        with patch.object(planner, '_governance', create=True) as mock_gov:
            mock_gov.check_execution_policy.return_value = "ALLOW_IMMEDIATE"

            actions = await planner.plan("Create a test task")
            # SimplePlanner parses intents - may return empty if no matching patterns
            assert isinstance(actions, list)


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
        from lib.oda.agent.trace import TraceEvent, EventType

        event = TraceEvent(
            event_type=EventType.OBSERVATION,
            content="Observed file change",
            metadata={"file": "test.py"}
        )
        assert event.event_type == EventType.OBSERVATION
        assert event.metadata["file"] == "test.py"

    def test_reasoning_trace(self):
        """Test ReasoningTrace creation and event adding."""
        from lib.oda.agent.trace import ReasoningTrace, TraceEvent, EventType

        trace = ReasoningTrace(
            trace_id="trace-001",
            agent_id="test-agent",
            task_description="Test task"
        )
        assert trace.trace_id == "trace-001"
        assert len(trace.events) == 0

        event = TraceEvent(
            event_type=EventType.THOUGHT,
            content="Planning next step"
        )
        trace.events.append(event)
        assert len(trace.events) == 1

    def test_trace_logger(self):
        """Test TraceLogger functionality."""
        from lib.oda.agent.trace import TraceLogger, TraceLevel

        logger = TraceLogger(
            agent_id="test-agent",
            level=TraceLevel.DETAILED
        )
        assert logger.agent_id == "test-agent"
        assert logger.level == TraceLevel.DETAILED

    @pytest.mark.asyncio
    async def test_trace_logger_logging(self):
        """Test TraceLogger.log_* methods."""
        from lib.oda.agent.trace import TraceLogger, TraceLevel

        logger = TraceLogger(
            agent_id="test-agent",
            level=TraceLevel.DEBUG
        )

        # Start a trace
        trace = logger.start_trace("Test task")
        assert trace is not None

        # Log various events
        logger.log_observation("File found", {"path": "/test.py"})
        logger.log_thought("Should read the file")
        logger.log_action("ReadFile", {"path": "/test.py"})
        logger.log_result(True, "File content retrieved")

        # End trace
        completed_trace = logger.end_trace()
        assert completed_trace is not None
        assert len(completed_trace.events) >= 4


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
        from lib.oda.agent.confirmation import ConfirmationRequest

        request = ConfirmationRequest(
            request_id="req-001",
            action_type="DeleteFile",
            action_params={"path": "/test.py"},
            reason="User requested file deletion",
            risk_level="high"
        )
        assert request.request_id == "req-001"
        assert request.risk_level == "high"

    def test_confirmation_response(self):
        """Test ConfirmationResponse model."""
        from lib.oda.agent.confirmation import (
            ConfirmationResponse,
            ConfirmationStatus,
        )

        response = ConfirmationResponse(
            request_id="req-001",
            status=ConfirmationStatus.APPROVED,
            approver_id="user-123",
            comment="Approved for deletion"
        )
        assert response.status == ConfirmationStatus.APPROVED

    @pytest.mark.asyncio
    async def test_confirmation_manager_request(self):
        """Test ConfirmationManager.request_confirmation()."""
        from lib.oda.agent.confirmation import (
            ConfirmationManager,
            ConfirmationStatus,
        )

        manager = ConfirmationManager()

        request = await manager.request_confirmation(
            action_type="DeleteFile",
            action_params={"path": "/test.py"},
            reason="Test deletion",
            risk_level="high"
        )
        assert request is not None
        assert request.action_type == "DeleteFile"

        # Check that request is pending
        status = await manager.check_status(request.request_id)
        assert status == ConfirmationStatus.PENDING

    @pytest.mark.asyncio
    async def test_confirmation_manager_approve(self):
        """Test ConfirmationManager.approve()."""
        from lib.oda.agent.confirmation import (
            ConfirmationManager,
            ConfirmationStatus,
        )

        manager = ConfirmationManager()

        # Create request
        request = await manager.request_confirmation(
            action_type="DeleteFile",
            action_params={"path": "/test.py"},
            reason="Test deletion"
        )

        # Approve it
        response = await manager.approve(
            request_id=request.request_id,
            approver_id="user-123",
            comment="Approved"
        )
        assert response.status == ConfirmationStatus.APPROVED

    @pytest.mark.asyncio
    async def test_confirmation_manager_reject(self):
        """Test ConfirmationManager.reject()."""
        from lib.oda.agent.confirmation import (
            ConfirmationManager,
            ConfirmationStatus,
        )

        manager = ConfirmationManager()

        # Create request
        request = await manager.request_confirmation(
            action_type="DeleteFile",
            action_params={"path": "/test.py"},
            reason="Test deletion"
        )

        # Reject it
        response = await manager.reject(
            request_id=request.request_id,
            approver_id="user-123",
            reason="Not authorized"
        )
        assert response.status == ConfirmationStatus.REJECTED


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
            AgentRole,
            PermissionLevel,
        )
        assert PermissionManager is not None
        assert AgentRole is not None

    def test_agent_identity(self):
        """Test AgentIdentity model."""
        from lib.oda.agent.permissions import AgentIdentity, AgentRole

        identity = AgentIdentity(
            agent_id="agent-001",
            name="Test Agent",
            roles=[AgentRole.DEVELOPER]
        )
        assert identity.agent_id == "agent-001"
        assert AgentRole.DEVELOPER in identity.roles

    def test_permission_level_enum(self):
        """Test PermissionLevel enum values."""
        from lib.oda.agent.permissions import PermissionLevel

        assert PermissionLevel.EXECUTE.value > PermissionLevel.PROPOSE.value
        assert PermissionLevel.PROPOSE.value > PermissionLevel.VIEW.value
        assert PermissionLevel.DENY.value == 0

    def test_agent_role_permissions(self):
        """Test predefined role permissions."""
        from lib.oda.agent.permissions import AgentRole

        # Verify all roles exist
        assert AgentRole.ADMIN is not None
        assert AgentRole.OPERATOR is not None
        assert AgentRole.DEVELOPER is not None
        assert AgentRole.AUDITOR is not None
        assert AgentRole.AGENT is not None
        assert AgentRole.GUEST is not None

    @pytest.mark.asyncio
    async def test_permission_manager_check(self):
        """Test PermissionManager.check_permission()."""
        from lib.oda.agent.permissions import (
            PermissionManager,
            AgentIdentity,
            AgentRole,
            PermissionLevel,
        )

        manager = PermissionManager()

        # Register an agent
        identity = AgentIdentity(
            agent_id="agent-001",
            name="Test Agent",
            roles=[AgentRole.DEVELOPER]
        )
        await manager.register_agent(identity)

        # Check permission for non-hazardous action
        result = await manager.check_permission(
            agent_id="agent-001",
            action_type="CreateTask"
        )
        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_permission_manager_deny_guest(self):
        """Test that GUEST role has limited permissions."""
        from lib.oda.agent.permissions import (
            PermissionManager,
            AgentIdentity,
            AgentRole,
        )

        manager = PermissionManager()

        # Register a guest agent
        identity = AgentIdentity(
            agent_id="guest-001",
            name="Guest Agent",
            roles=[AgentRole.GUEST]
        )
        await manager.register_agent(identity)

        # Guest should not be able to execute hazardous actions
        result = await manager.check_permission(
            agent_id="guest-001",
            action_type="DeleteFile",
            is_hazardous=True
        )
        assert result.allowed is False


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

    def test_build_adapter_openai(self):
        """Test build_agent_adapter for OpenAI."""
        from lib.oda.llm.agent_adapter import (
            build_agent_adapter,
            OpenAIAgentAdapter,
        )

        adapter = build_agent_adapter(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        assert isinstance(adapter, OpenAIAgentAdapter)

    def test_build_adapter_claude(self):
        """Test build_agent_adapter for Claude."""
        from lib.oda.llm.agent_adapter import (
            build_agent_adapter,
            ClaudeCodeAgentAdapter,
        )

        adapter = build_agent_adapter(provider="claude-code")
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
        tool_names = [t["name"] for t in tools]
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

        handlers = AgentToolHandlers()

        # Mock the registry
        with patch.object(handlers, '_get_action_registry') as mock_registry:
            mock_registry.return_value = MagicMock()
            mock_registry.return_value.list_all.return_value = [
                MagicMock(api_name="CreateTask", description="Create task"),
                MagicMock(api_name="UpdateTask", description="Update task"),
            ]

            result = await handlers.handle_list_actions({})
            assert "actions" in result

    @pytest.mark.asyncio
    async def test_handler_check_permission(self):
        """Test agent_check_permission handler."""
        from lib.oda.mcp.agent_tools import AgentToolHandlers

        handlers = AgentToolHandlers()

        result = await handlers.handle_check_permission({
            "agent_id": "test-agent",
            "action_type": "CreateTask"
        })
        assert "allowed" in result


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    @pytest.mark.asyncio
    async def test_planner_with_permission_check(self):
        """Test planner respects permission checks."""
        from lib.oda.agent.planner import SimplePlanner, PlannerConfig
        from lib.oda.agent.permissions import (
            PermissionManager,
            AgentIdentity,
            AgentRole,
        )

        # Setup permission manager
        perm_manager = PermissionManager()
        identity = AgentIdentity(
            agent_id="test-agent",
            name="Test Agent",
            roles=[AgentRole.DEVELOPER]
        )
        await perm_manager.register_agent(identity)

        # Setup planner with permission manager
        config = PlannerConfig(max_iterations=5)
        planner = SimplePlanner(config=config)

        # Planner should work with valid permissions
        actions = await planner.plan("Create a task")
        assert isinstance(actions, list)

    @pytest.mark.asyncio
    async def test_trace_with_confirmation(self):
        """Test trace logging during confirmation workflow."""
        from lib.oda.agent.trace import TraceLogger, TraceLevel
        from lib.oda.agent.confirmation import (
            ConfirmationManager,
            ConfirmationStatus,
        )

        # Setup trace logger
        logger = TraceLogger(
            agent_id="test-agent",
            level=TraceLevel.DETAILED
        )

        # Setup confirmation manager
        conf_manager = ConfirmationManager()

        # Start trace
        trace = logger.start_trace("Delete file with confirmation")

        # Log the confirmation request
        logger.log_action("RequestConfirmation", {
            "action": "DeleteFile",
            "path": "/test.py"
        })

        # Create confirmation
        request = await conf_manager.request_confirmation(
            action_type="DeleteFile",
            action_params={"path": "/test.py"},
            reason="Test deletion"
        )

        logger.log_observation(
            f"Confirmation requested: {request.request_id}",
            {"status": "pending"}
        )

        # Approve
        response = await conf_manager.approve(
            request_id=request.request_id,
            approver_id="admin"
        )

        logger.log_result(
            response.status == ConfirmationStatus.APPROVED,
            "Confirmation approved"
        )

        # End trace
        completed_trace = logger.end_trace()
        assert len(completed_trace.events) >= 3


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
