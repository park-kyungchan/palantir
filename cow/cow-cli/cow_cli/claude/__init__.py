"""
COW CLI - Claude Agent SDK Integration Module

Provides MCP tool servers and stage agents for Claude Agent SDK integration.
"""
from cow_cli.claude.mcp_servers import (
    # Registry
    ToolRegistry,
    MCPTool,
    tool,
    get_registry,
    get_all_tools,
    get_tool_schema,
    get_tools_by_server,
    # cow-mathpix
    mathpix_request,
    mathpix_poll,
    # cow-separator
    separate_layout_content,
    get_layout_elements,
    # cow-validation
    validate_image,
    validate_schema,
    check_duplicates,
    # cow-hitl
    queue_for_review,
    get_review_status,
    submit_review,
    list_pending_reviews,
)
from cow_cli.claude.stage_agents import (
    # Types
    ModelType,
    StageType,
    AgentDefinition,
    # Agents
    INGESTION_AGENT,
    TEXT_PARSE_AGENT,
    SEPARATOR_AGENT,
    VISION_PARSE_AGENT,
    ALIGNMENT_AGENT,
    SEMANTIC_GRAPH_AGENT,
    REGENERATION_AGENT,
    HUMAN_REVIEW_AGENT,
    EXPORT_AGENT,
    # Registry
    STAGE_AGENTS,
    get_agent,
    get_agent_by_name,
    list_agents,
    get_agent_tools,
    get_pipeline_sequence,
)
from cow_cli.claude.orchestrator import (
    ProcessingStatus,
    StageExecution,
    SessionCheckpoint,
    PipelineResult,
    COWOrchestrator,
    process_document,
)
from cow_cli.claude.hooks import (
    HookAction,
    HookResult,
    ToolMetrics,
    QuotaManager,
    HookManager,
    get_hook_manager,
    configure_hooks,
    pre_tool_use,
    post_tool_use,
    post_tool_use_failure,
)

__all__ = [
    # MCP Tool Registry
    "ToolRegistry",
    "MCPTool",
    "tool",
    "get_registry",
    "get_all_tools",
    "get_tool_schema",
    "get_tools_by_server",
    # cow-mathpix
    "mathpix_request",
    "mathpix_poll",
    # cow-separator
    "separate_layout_content",
    "get_layout_elements",
    # cow-validation
    "validate_image",
    "validate_schema",
    "check_duplicates",
    # cow-hitl
    "queue_for_review",
    "get_review_status",
    "submit_review",
    "list_pending_reviews",
    # Stage Agent Types
    "ModelType",
    "StageType",
    "AgentDefinition",
    # Stage Agents
    "INGESTION_AGENT",
    "TEXT_PARSE_AGENT",
    "SEPARATOR_AGENT",
    "VISION_PARSE_AGENT",
    "ALIGNMENT_AGENT",
    "SEMANTIC_GRAPH_AGENT",
    "REGENERATION_AGENT",
    "HUMAN_REVIEW_AGENT",
    "EXPORT_AGENT",
    # Agent Registry
    "STAGE_AGENTS",
    "get_agent",
    "get_agent_by_name",
    "list_agents",
    "get_agent_tools",
    "get_pipeline_sequence",
    # Orchestrator
    "ProcessingStatus",
    "StageExecution",
    "SessionCheckpoint",
    "PipelineResult",
    "COWOrchestrator",
    "process_document",
    # Hooks
    "HookAction",
    "HookResult",
    "ToolMetrics",
    "QuotaManager",
    "HookManager",
    "get_hook_manager",
    "configure_hooks",
    "pre_tool_use",
    "post_tool_use",
    "post_tool_use_failure",
]
