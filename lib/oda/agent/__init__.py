"""
Orion ODA v4.0 - Agent Infrastructure
=====================================

This module provides standardized entry points and protocols for LLM agents
to interact with the Orion Ontology-Driven Architecture.

Components:
- executor: AgentExecutor for running actions
- protocols: Standardized execution protocols
- validators: Input validation utilities
- tools: Agent tool wrappers for LLM integration
- context_builder: Ontology context builder for prompts
- schema_prompt: Schema-to-prompt conversion utilities

Phase 7 Additions (v4.0):
- ObjectQueryTool: Query ObjectTypes from ontology
- ActionExecutorTool: Execute actions with validation
- FunctionCallTool: OpenAI/Claude function calling format
- OntologyContextBuilder: Build system prompts from ontology
"""

from lib.oda.agent.executor import AgentExecutor
from lib.oda.agent.protocols import ExecutionProtocol, TaskResult

# Phase 7.1: Agent Tool Framework
from lib.oda.agent.tools import (
    # Registry
    ToolRegistry,
    ToolMetadata,
    get_registry as get_tool_registry,
    get_tool,
    get_all_tools,
    list_tools,
    register_tool,
    # Tool definitions export
    export_tool_definitions,
    get_openai_tools,
    get_claude_tools,
    # Unified interface
    UnifiedToolInterface,
    # ObjectQueryTool
    ObjectQueryTool,
    GetObjectInput,
    ListObjectsInput,
    SearchObjectsInput,
    ObjectQueryResult,
    SchemaQueryResult,
    # ActionExecutorTool
    ActionExecutorTool,
    ExecuteActionInput,
    GetActionSchemaInput,
    ListActionsInput,
    ActionExecutionResult,
    ActionSchemaResult,
    ActionListResult,
    # FunctionCallTool
    FunctionCallTool,
    FunctionDefinition,
    ToolDefinition,
    FunctionCallRequest,
    FunctionCallResponse,
    ActionToFunctionConverter,
    ClaudeToolAdapter,
)

# Phase 7.2: Ontology Context Builder
from lib.oda.agent.context_builder import (
    OntologyContextBuilder,
    ContextBuilderConfig,
    ContextOutputFormat,
    BuiltContext,
    ObjectTypeContext,
    ActionContext as ContextActionContext,  # Alias to avoid conflict
    LinkGraphContext,
    build_agent_context,
    get_context_json,
)

# Phase 7.2: Schema to Prompt Conversion
from lib.oda.agent.schema_prompt import (
    PydanticToNaturalLanguage,
    ObjectTypeDocumenter,
    ActionDocumenter,
    describe_model,
    document_object_type,
    document_action,
    generate_schema_prompt,
)

# Phase 7.3: Agent Execution
from lib.oda.agent.planner import (
    AgentPlanner,
    SimplePlanner,
    PlannerConfig,
    PlannerIteration,
    PlannedAction,
    Observation,
    Thought,
)

from lib.oda.agent.trace import (
    ReasoningTrace,
    TraceLogger,
    TraceStore,
    TraceEvent,
    TraceEventType,
    TraceLevel,
)

# Backward compatibility alias
EventType = TraceEventType

from lib.oda.agent.confirmation import (
    ConfirmationManager,
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationStatus,
    ConfirmationHandler,
    CallbackConfirmationHandler,
    ConsoleConfirmationHandler,
)

from lib.oda.agent.permissions import (
    PermissionManager,
    AgentIdentity,
    AgentRole,
    ActionPermission,
    PermissionLevel,
    PermissionCheckResult,
)

__all__ = [
    # Core executor
    "AgentExecutor",
    "ExecutionProtocol",
    "TaskResult",
    # Tool registry
    "ToolRegistry",
    "ToolMetadata",
    "get_tool_registry",
    "get_tool",
    "get_all_tools",
    "list_tools",
    "register_tool",
    "export_tool_definitions",
    "get_openai_tools",
    "get_claude_tools",
    "UnifiedToolInterface",
    # ObjectQueryTool
    "ObjectQueryTool",
    "GetObjectInput",
    "ListObjectsInput",
    "SearchObjectsInput",
    "ObjectQueryResult",
    "SchemaQueryResult",
    # ActionExecutorTool
    "ActionExecutorTool",
    "ExecuteActionInput",
    "GetActionSchemaInput",
    "ListActionsInput",
    "ActionExecutionResult",
    "ActionSchemaResult",
    "ActionListResult",
    # FunctionCallTool
    "FunctionCallTool",
    "FunctionDefinition",
    "ToolDefinition",
    "FunctionCallRequest",
    "FunctionCallResponse",
    "ActionToFunctionConverter",
    "ClaudeToolAdapter",
    # Context builder
    "OntologyContextBuilder",
    "ContextBuilderConfig",
    "ContextOutputFormat",
    "BuiltContext",
    "ObjectTypeContext",
    "ContextActionContext",
    "LinkGraphContext",
    "build_agent_context",
    "get_context_json",
    # Schema prompt
    "PydanticToNaturalLanguage",
    "ObjectTypeDocumenter",
    "ActionDocumenter",
    "describe_model",
    "document_object_type",
    "document_action",
    "generate_schema_prompt",
    # Phase 7.3: Planner
    "AgentPlanner",
    "SimplePlanner",
    "PlannerConfig",
    "PlannerIteration",
    "PlannedAction",
    "Observation",
    "Thought",
    # Phase 7.3: Trace
    "ReasoningTrace",
    "TraceLogger",
    "TraceStore",
    "TraceEvent",
    "TraceEventType",
    "EventType",  # Backward compatibility alias
    "TraceLevel",
    # Phase 7.3: Confirmation
    "ConfirmationManager",
    "ConfirmationRequest",
    "ConfirmationResponse",
    "ConfirmationStatus",
    "ConfirmationHandler",
    "CallbackConfirmationHandler",
    "ConsoleConfirmationHandler",
    # Phase 7.3: Permissions
    "PermissionManager",
    "AgentIdentity",
    "AgentRole",
    "ActionPermission",
    "PermissionLevel",
    "PermissionCheckResult",
]
