"""
Orion ODA v4.0 - MCP Agent Tools (Phase 7.4.2)
===============================================

Exposes agent tools via MCP protocol for external clients:
- Tool definitions following MCP specification
- Handler registration for tool execution
- Integration with AgentExecutor and PermissionManager

MCP Tools Exposed:
- agent_execute: Execute an ODA action
- agent_plan: Generate an action plan for a goal
- agent_query: Query ontology objects
- agent_confirm: Request/check confirmation status
- agent_permissions: Check agent permissions
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from lib.oda.agent.executor import AgentExecutor, TaskResult, get_executor
from lib.oda.agent.confirmation import (
    ConfirmationManager,
    ConfirmationRequest,
    ConfirmationStatus,
    UrgencyLevel,
)
from lib.oda.agent.permissions import (
    PermissionCheckResult,
    PermissionLevel,
    PermissionManager,
    get_permission_manager,
)
from lib.oda.agent.planner import AgentPlanner, PlannedAction, PlannerConfig
from lib.oda.ontology.actions import action_registry, ActionContext

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

def get_agent_tools() -> List[Tool]:
    """
    Get all agent tool definitions for MCP registration.

    Returns:
        List of MCP Tool objects
    """
    return [
        # =================================================================
        # ACTION EXECUTION TOOLS
        # =================================================================
        Tool(
            name="agent_execute",
            description=(
                "Execute an ODA action through the agent executor. "
                "This is the primary method for running actions with governance checks."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "description": "The action API name (e.g., 'file.read', 'memory.save_insight')"
                    },
                    "params": {
                        "type": "object",
                        "description": "Action parameters"
                    },
                    "actor_id": {
                        "type": "string",
                        "description": "ID of the executing agent",
                        "default": "mcp-agent"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Priority for proposal if required",
                        "default": "medium"
                    }
                },
                "required": ["action_type", "params"]
            }
        ),
        Tool(
            name="agent_list_actions",
            description="List all available actions in the registry with their metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_type": {
                        "type": "string",
                        "enum": ["all", "safe", "hazardous"],
                        "description": "Filter actions by type",
                        "default": "all"
                    }
                }
            }
        ),
        Tool(
            name="agent_get_action_schema",
            description="Get the schema and required parameters for a specific action",
            inputSchema={
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "description": "The action API name"
                    }
                },
                "required": ["action_type"]
            }
        ),

        # =================================================================
        # PLANNING TOOLS
        # =================================================================
        Tool(
            name="agent_plan",
            description=(
                "Generate an action plan to achieve a goal. "
                "Returns a list of planned actions with rationale."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The goal to achieve"
                    },
                    "context": {
                        "type": "object",
                        "description": "Current context/state information",
                        "default": {}
                    },
                    "max_actions": {
                        "type": "integer",
                        "description": "Maximum number of actions to plan",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["goal"]
            }
        ),
        Tool(
            name="agent_execute_plan",
            description=(
                "Execute a list of planned actions in sequence. "
                "Stops on first failure unless continue_on_error is true."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action_type": {"type": "string"},
                                "params": {"type": "object"},
                                "rationale": {"type": "string"}
                            },
                            "required": ["action_type", "params"]
                        },
                        "description": "List of actions to execute"
                    },
                    "actor_id": {
                        "type": "string",
                        "default": "mcp-agent"
                    },
                    "continue_on_error": {
                        "type": "boolean",
                        "default": False,
                        "description": "Continue executing even if an action fails"
                    }
                },
                "required": ["actions"]
            }
        ),

        # =================================================================
        # CONFIRMATION TOOLS
        # =================================================================
        Tool(
            name="agent_request_confirmation",
            description=(
                "Request confirmation for a hazardous action. "
                "Creates a confirmation request that must be approved before execution."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "description": "Action requiring confirmation"
                    },
                    "params": {
                        "type": "object",
                        "description": "Action parameters"
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Why this action is needed"
                    },
                    "risks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Known risks of this action",
                        "default": []
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "critical"],
                        "default": "normal"
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "description": "Timeout for confirmation",
                        "default": 300
                    }
                },
                "required": ["action_type", "params"]
            }
        ),
        Tool(
            name="agent_check_confirmation",
            description="Check the status of a confirmation request",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "Confirmation request ID"
                    }
                },
                "required": ["request_id"]
            }
        ),
        Tool(
            name="agent_list_pending_confirmations",
            description="List all pending confirmation requests",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # =================================================================
        # PERMISSION TOOLS
        # =================================================================
        Tool(
            name="agent_check_permission",
            description="Check if an agent has permission for a specific action",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent ID to check"
                    },
                    "action_type": {
                        "type": "string",
                        "description": "Action to check permission for"
                    },
                    "params": {
                        "type": "object",
                        "description": "Optional action parameters for context",
                        "default": {}
                    }
                },
                "required": ["agent_id", "action_type"]
            }
        ),
        Tool(
            name="agent_register",
            description="Register a new agent with roles and permissions",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique agent identifier"
                    },
                    "name": {
                        "type": "string",
                        "description": "Human-readable name"
                    },
                    "roles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Role IDs to assign",
                        "default": ["agent"]
                    },
                    "trust_score": {
                        "type": "number",
                        "description": "Initial trust score (0-1)",
                        "default": 0.5
                    }
                },
                "required": ["agent_id"]
            }
        ),
        Tool(
            name="agent_list_roles",
            description="List all available roles with their permissions",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # =================================================================
        # QUERY TOOLS
        # =================================================================
        Tool(
            name="agent_query_objects",
            description=(
                "Query ontology objects by type. "
                "Returns objects matching the specified criteria."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "Type of objects to query (e.g., 'Task', 'Proposal')"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filter criteria",
                        "default": {}
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 50
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Pagination offset",
                        "default": 0
                    }
                },
                "required": ["object_type"]
            }
        ),
    ]


# =============================================================================
# TOOL HANDLERS
# =============================================================================

class AgentToolHandlers:
    """
    Handler implementations for agent MCP tools.

    This class provides the implementation logic for each tool,
    coordinating between AgentExecutor, PermissionManager, and ConfirmationManager.
    """

    def __init__(
        self,
        executor: Optional[AgentExecutor] = None,
        permission_manager: Optional[PermissionManager] = None,
        confirmation_manager: Optional[ConfirmationManager] = None,
    ):
        """
        Initialize handlers with optional custom managers.

        Args:
            executor: Agent executor instance
            permission_manager: Permission manager instance
            confirmation_manager: Confirmation manager instance
        """
        self._executor = executor
        self._permission_manager = permission_manager or get_permission_manager()
        self._confirmation_manager = confirmation_manager or ConfirmationManager()
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure executor is initialized."""
        if not self._initialized:
            if self._executor is None:
                self._executor = await get_executor()
            else:
                await self._executor.initialize()
            self._initialized = True

    # =========================================================================
    # ACTION EXECUTION HANDLERS
    # =========================================================================

    async def handle_agent_execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_execute tool call."""
        await self._ensure_initialized()

        action_type = arguments["action_type"]
        params = arguments["params"]
        actor_id = arguments.get("actor_id", "mcp-agent")
        priority = arguments.get("priority", "medium")

        # Check permissions first
        perm_result = self._permission_manager.check_with_governance(
            actor_id, action_type, params
        )

        if not perm_result.allowed and perm_result.level == PermissionLevel.DENY:
            return {
                "success": False,
                "error": "PERMISSION_DENIED",
                "reason": perm_result.reason,
            }

        # Execute through AgentExecutor
        result: TaskResult = await self._executor.execute_action(
            action_type=action_type,
            params=params,
            actor_id=actor_id,
            priority=priority,
        )

        return result.to_dict()

    async def handle_agent_list_actions(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_list_actions tool call."""
        await self._ensure_initialized()

        filter_type = arguments.get("filter_type", "all")
        result = self._executor.list_actions()

        if filter_type == "safe":
            actions = result.data.get("safe", [])
        elif filter_type == "hazardous":
            actions = result.data.get("hazardous", [])
        else:
            actions = result.data.get("actions", [])

        return {
            "success": True,
            "actions": actions,
            "count": len(actions),
            "filter": filter_type,
        }

    async def handle_agent_get_action_schema(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_get_action_schema tool call."""
        await self._ensure_initialized()

        action_type = arguments["action_type"]
        result = self._executor.get_action_schema(action_type)

        return result.to_dict()

    # =========================================================================
    # PLANNING HANDLERS
    # =========================================================================

    async def handle_agent_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_plan tool call."""
        goal = arguments["goal"]
        context = arguments.get("context", {})
        max_actions = arguments.get("max_actions", 5)

        # Build a simple plan based on available actions
        # In production, this would use LLM reasoning
        available_actions = action_registry.list_actions()

        # Simple keyword-based planning
        plan = []
        goal_lower = goal.lower()

        # Match actions to goal keywords
        action_keywords = {
            "file.read": ["read", "view", "check", "get"],
            "file.write": ["write", "create", "save", "output"],
            "file.modify": ["edit", "modify", "update", "change"],
            "file.delete": ["delete", "remove", "clean"],
            "memory.save_insight": ["remember", "insight", "learn", "note"],
            "memory.save_pattern": ["pattern", "template", "recurring"],
        }

        for action, keywords in action_keywords.items():
            if action in available_actions:
                if any(kw in goal_lower for kw in keywords):
                    plan.append({
                        "action_type": action,
                        "params": {},
                        "rationale": f"Matched goal keyword for {action}",
                    })
                    if len(plan) >= max_actions:
                        break

        return {
            "success": True,
            "goal": goal,
            "plan": plan,
            "action_count": len(plan),
            "note": "Simple keyword-based planning. Use LLM adapter for advanced planning.",
        }

    async def handle_agent_execute_plan(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_execute_plan tool call."""
        await self._ensure_initialized()

        actions = arguments["actions"]
        actor_id = arguments.get("actor_id", "mcp-agent")
        continue_on_error = arguments.get("continue_on_error", False)

        results = []
        for action in actions:
            result = await self._executor.execute_action(
                action_type=action["action_type"],
                params=action.get("params", {}),
                actor_id=actor_id,
            )

            results.append({
                "action_type": action["action_type"],
                "success": result.success,
                "message": result.message,
                "data": result.data,
            })

            if not result.success and not continue_on_error:
                break

        success_count = sum(1 for r in results if r["success"])

        return {
            "success": success_count == len(actions),
            "total_actions": len(actions),
            "executed": len(results),
            "successful": success_count,
            "failed": len(results) - success_count,
            "results": results,
        }

    # =========================================================================
    # CONFIRMATION HANDLERS
    # =========================================================================

    async def handle_agent_request_confirmation(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_request_confirmation tool call."""
        action_type = arguments["action_type"]
        params = arguments["params"]
        rationale = arguments.get("rationale", "")
        risks = arguments.get("risks", [])
        urgency = UrgencyLevel(arguments.get("urgency", "normal"))
        timeout = arguments.get("timeout_seconds", 300)

        # Create confirmation request (non-blocking)
        request = ConfirmationRequest(
            action_type=action_type,
            params=params,
            rationale=rationale,
            risks=risks,
            urgency=urgency,
            requester_id="mcp-agent",
        )

        # Store request for later checking
        self._confirmation_manager._pending_requests[request.id] = request

        return {
            "success": True,
            "request_id": request.id,
            "status": request.status.value,
            "action_type": action_type,
            "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            "message": "Confirmation request created. Check status with agent_check_confirmation.",
        }

    async def handle_agent_check_confirmation(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_check_confirmation tool call."""
        request_id = arguments["request_id"]

        request = self._confirmation_manager.get_request(request_id)
        if not request:
            # Check history
            for hist_req in self._confirmation_manager._request_history:
                if hist_req.id == request_id:
                    request = hist_req
                    break

        if not request:
            return {
                "success": False,
                "error": "REQUEST_NOT_FOUND",
                "request_id": request_id,
            }

        return {
            "success": True,
            "request_id": request.id,
            "status": request.status.value,
            "action_type": request.action_type,
            "is_pending": request.is_pending(),
            "is_expired": request.is_expired(),
            "created_at": request.created_at.isoformat(),
            "responded_at": request.responded_at.isoformat() if request.responded_at else None,
            "responder_id": request.responder_id,
            "response_comment": request.response_comment,
        }

    async def handle_agent_list_pending_confirmations(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_list_pending_confirmations tool call."""
        pending = self._confirmation_manager.get_pending_requests()

        return {
            "success": True,
            "count": len(pending),
            "requests": [req.to_display_dict() for req in pending],
        }

    # =========================================================================
    # PERMISSION HANDLERS
    # =========================================================================

    async def handle_agent_check_permission(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_check_permission tool call."""
        agent_id = arguments["agent_id"]
        action_type = arguments["action_type"]
        params = arguments.get("params", {})

        result = self._permission_manager.check_with_governance(
            agent_id, action_type, params
        )

        return {
            "success": True,
            "agent_id": agent_id,
            "action_type": action_type,
            "allowed": result.allowed,
            "permission_level": result.level.value,
            "reason": result.reason,
            "role": result.role,
        }

    async def handle_agent_register(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_register tool call."""
        agent_id = arguments["agent_id"]
        name = arguments.get("name", agent_id)
        roles = arguments.get("roles", ["agent"])
        trust_score = arguments.get("trust_score", 0.5)

        identity = self._permission_manager.register_agent(
            agent_id=agent_id,
            name=name,
            roles=roles,
            trust_score=trust_score,
        )

        return {
            "success": True,
            "agent_id": identity.id,
            "name": identity.name,
            "roles": identity.roles,
            "trust_score": identity.trust_score,
            "active": identity.is_active(),
        }

    async def handle_agent_list_roles(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_list_roles tool call."""
        roles = self._permission_manager.list_roles()

        return {
            "success": True,
            "count": len(roles),
            "roles": [
                {
                    "id": role.id,
                    "name": role.name,
                    "type": role.role_type.value,
                    "description": role.description,
                    "permission_count": len(role.permissions),
                }
                for role in roles
            ],
        }

    # =========================================================================
    # QUERY HANDLERS
    # =========================================================================

    async def handle_agent_query_objects(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent_query_objects tool call."""
        object_type = arguments["object_type"]
        filters = arguments.get("filters", {})
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        # This is a placeholder - actual implementation would query the ontology
        return {
            "success": True,
            "object_type": object_type,
            "filters": filters,
            "limit": limit,
            "offset": offset,
            "objects": [],
            "total": 0,
            "note": "Query functionality requires ontology repository integration",
        }


# =============================================================================
# MCP SERVER REGISTRATION
# =============================================================================

def register_agent_tools(server: Server, handlers: Optional[AgentToolHandlers] = None) -> None:
    """
    Register agent tools with an MCP server.

    Args:
        server: MCP Server instance
        handlers: Optional custom handlers (created if not provided)
    """
    if handlers is None:
        handlers = AgentToolHandlers()

    # Map tool names to handler methods
    tool_handlers = {
        "agent_execute": handlers.handle_agent_execute,
        "agent_list_actions": handlers.handle_agent_list_actions,
        "agent_get_action_schema": handlers.handle_agent_get_action_schema,
        "agent_plan": handlers.handle_agent_plan,
        "agent_execute_plan": handlers.handle_agent_execute_plan,
        "agent_request_confirmation": handlers.handle_agent_request_confirmation,
        "agent_check_confirmation": handlers.handle_agent_check_confirmation,
        "agent_list_pending_confirmations": handlers.handle_agent_list_pending_confirmations,
        "agent_check_permission": handlers.handle_agent_check_permission,
        "agent_register": handlers.handle_agent_register,
        "agent_list_roles": handlers.handle_agent_list_roles,
        "agent_query_objects": handlers.handle_agent_query_objects,
    }

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """Return agent tools."""
        return get_agent_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle agent tool calls."""
        handler = tool_handlers.get(name)

        if handler is None:
            return [TextContent(type="text", text=json.dumps({
                "error": "UNKNOWN_TOOL",
                "tool": name,
            }))]

        try:
            result = await handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        except Exception as e:
            logger.exception(f"Tool handler error: {name}")
            return [TextContent(type="text", text=json.dumps({
                "error": str(type(e).__name__),
                "message": str(e),
            }))]


__all__ = [
    "get_agent_tools",
    "AgentToolHandlers",
    "register_agent_tools",
]
