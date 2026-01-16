"""
Orion ODA v4.0 - ActionExecutorTool
===================================

Tool wrapper around AgentExecutor for LLM-based action execution.
Provides structured interfaces for action discovery, execution, and dry-run.

Key Features:
- LLM-friendly action schemas
- Dry-run capability for safe exploration
- Proper error handling with actionable messages
- Parameter validation via Pydantic models
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, field_validator

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    ActionMetadata,
    ActionRegistry,
    action_registry,
    GovernanceEngine,
)

logger = logging.getLogger(__name__)


# =============================================================================
# INPUT MODELS
# =============================================================================


class ExecuteActionInput(BaseModel):
    """Input schema for execute_action operation."""

    action_type: str = Field(
        ...,
        description="The API name of the action (e.g., 'file.read', 'llm.generate_plan')",
        min_length=1,
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action parameters as key-value pairs",
    )
    actor_id: str = Field(
        default="agent",
        description="ID of the agent executing the action",
    )
    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
        description="Priority level for proposal creation",
    )
    dry_run: bool = Field(
        default=False,
        description="If True, validate without executing (safe exploration)",
    )

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Validate action type format."""
        # Action names should be lowercase with dots/underscores
        if v and v[0].isupper():
            raise ValueError(
                "action_type should be lowercase (e.g., 'file.read', not 'FileRead')"
            )
        return v


class GetActionSchemaInput(BaseModel):
    """Input schema for get_action_schema operation."""

    action_type: str = Field(
        ...,
        description="The API name of the action",
        min_length=1,
    )


class ListActionsInput(BaseModel):
    """Input schema for list_actions operation."""

    filter_hazardous: Optional[bool] = Field(
        default=None,
        description="Filter to only hazardous (True) or safe (False) actions",
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Filter by namespace prefix (e.g., 'file', 'llm')",
    )


# =============================================================================
# OUTPUT MODELS
# =============================================================================


class ActionExecutionResult(BaseModel):
    """Result of an action execution."""

    success: bool = Field(description="Whether the action succeeded")
    action_type: str = Field(description="The executed action type")
    message: str = Field(description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Action output data",
    )
    proposal_id: Optional[str] = Field(
        default=None,
        description="Proposal ID if action requires approval",
    )
    was_dry_run: bool = Field(
        default=False,
        description="True if this was a dry-run (no changes made)",
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code",
    )
    validation_errors: Optional[List[str]] = Field(
        default=None,
        description="List of validation errors if any",
    )
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggestions for fixing errors",
    )


class ActionSchemaResult(BaseModel):
    """Result of get_action_schema operation."""

    success: bool
    action_type: str
    schema: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ActionListResult(BaseModel):
    """Result of list_actions operation."""

    success: bool
    total_count: int
    actions: List[Dict[str, Any]]
    hazardous_count: int
    safe_count: int


# =============================================================================
# ACTION EXECUTOR TOOL
# =============================================================================


class ActionExecutorTool:
    """
    Tool wrapper for executing ODA actions from LLM agents.

    This tool provides:
    1. Action discovery - list and inspect available actions
    2. Safe execution - dry-run mode for exploration
    3. Proper error handling - actionable error messages
    4. Governance compliance - automatic proposal creation

    Example Usage:
        ```python
        tool = ActionExecutorTool()

        # List available actions
        result = tool.list_actions(ListActionsInput(namespace="file"))

        # Get action schema
        schema = tool.get_action_schema(GetActionSchemaInput(
            action_type="file.read"
        ))

        # Execute with dry-run first
        result = await tool.execute_action(ExecuteActionInput(
            action_type="file.read",
            params={"path": "/etc/config.yaml"},
            dry_run=True
        ))

        # Execute for real
        result = await tool.execute_action(ExecuteActionInput(
            action_type="file.read",
            params={"path": "/etc/config.yaml"},
            dry_run=False
        ))
        ```
    """

    TOOL_NAME = "action_executor"
    TOOL_DESCRIPTION = (
        "Execute ODA actions with validation and governance. "
        "Supports dry-run mode for safe exploration before execution."
    )

    def __init__(
        self,
        registry: Optional[ActionRegistry] = None,
        governance: Optional[GovernanceEngine] = None,
    ) -> None:
        """
        Initialize the ActionExecutorTool.

        Args:
            registry: ActionRegistry instance (defaults to global registry)
            governance: GovernanceEngine instance (defaults to new instance)
        """
        self._registry = registry or action_registry
        self._governance = governance or GovernanceEngine(self._registry)

    # =========================================================================
    # ACTION DISCOVERY
    # =========================================================================

    def list_actions(self, input_data: Optional[ListActionsInput] = None) -> ActionListResult:
        """
        List all available actions in the registry.

        Args:
            input_data: Optional filters for the list

        Returns:
            ActionListResult with action metadata
        """
        input_data = input_data or ListActionsInput()

        all_actions = self._registry.list_actions()
        hazardous_actions = set(self._registry.get_hazardous_actions())

        actions = []
        for action_name in all_actions:
            # Apply namespace filter
            if input_data.namespace:
                if not action_name.startswith(input_data.namespace):
                    continue

            is_hazardous = action_name in hazardous_actions

            # Apply hazardous filter
            if input_data.filter_hazardous is not None:
                if input_data.filter_hazardous != is_hazardous:
                    continue

            metadata = self._registry.get_metadata(action_name)

            actions.append({
                "api_name": action_name,
                "requires_proposal": is_hazardous,
                "description": metadata.description if metadata else "",
                "namespace": action_name.split(".")[0] if "." in action_name else "",
            })

        return ActionListResult(
            success=True,
            total_count=len(actions),
            actions=sorted(actions, key=lambda x: x["api_name"]),
            hazardous_count=sum(1 for a in actions if a["requires_proposal"]),
            safe_count=sum(1 for a in actions if not a["requires_proposal"]),
        )

    def get_action_schema(self, input_data: GetActionSchemaInput) -> ActionSchemaResult:
        """
        Get the schema (parameters, constraints) for an action.

        Args:
            input_data: Input with action_type

        Returns:
            ActionSchemaResult with schema definition
        """
        action_cls = self._registry.get(input_data.action_type)
        if not action_cls:
            available = self._registry.list_actions()
            suggestions = self._suggest_similar_actions(
                input_data.action_type, available
            )

            return ActionSchemaResult(
                success=False,
                action_type=input_data.action_type,
                error=f"Action '{input_data.action_type}' not found. "
                f"Did you mean: {suggestions}" if suggestions else "",
            )

        # Get schema from action class
        schema = action_cls.get_parameter_schema()
        metadata = self._registry.get_metadata(input_data.action_type)

        # Enhance with governance info
        schema["requires_proposal"] = metadata.requires_proposal if metadata else False
        schema["is_hazardous"] = metadata.is_dangerous if metadata else False

        return ActionSchemaResult(
            success=True,
            action_type=input_data.action_type,
            schema=schema,
        )

    # =========================================================================
    # ACTION EXECUTION
    # =========================================================================

    async def execute_action(
        self, input_data: ExecuteActionInput
    ) -> ActionExecutionResult:
        """
        Execute an action with validation and governance.

        Args:
            input_data: Validated execution input

        Returns:
            ActionExecutionResult with outcome
        """
        # 1. Validate action exists
        action_cls = self._registry.get(input_data.action_type)
        if not action_cls:
            suggestions = self._suggest_similar_actions(
                input_data.action_type,
                self._registry.list_actions(),
            )
            return ActionExecutionResult(
                success=False,
                action_type=input_data.action_type,
                message=f"Action '{input_data.action_type}' not found",
                error_code="ACTION_NOT_FOUND",
                suggestions=suggestions,
            )

        # 2. Check governance policy
        policy = self._governance.check_execution_policy(
            input_data.action_type,
            input_data.params,
        )

        if policy.is_blocked():
            return ActionExecutionResult(
                success=False,
                action_type=input_data.action_type,
                message=policy.reason,
                error_code="GOVERNANCE_BLOCKED",
                suggestions=[
                    "Check if the parameters contain dangerous patterns",
                    "Consider using a safer alternative action",
                ],
            )

        # 3. Instantiate action and validate
        try:
            action = action_cls()
            context = ActionContext(actor_id=input_data.actor_id)

            # Pre-validate parameters
            validation_errors = action.validate(input_data.params, context)
            if validation_errors:
                return ActionExecutionResult(
                    success=False,
                    action_type=input_data.action_type,
                    message="Parameter validation failed",
                    error_code="VALIDATION_FAILED",
                    validation_errors=validation_errors,
                    suggestions=self._generate_validation_suggestions(
                        input_data.action_type, validation_errors
                    ),
                )

            # 4. Handle dry-run mode
            if input_data.dry_run:
                return ActionExecutionResult(
                    success=True,
                    action_type=input_data.action_type,
                    message="Dry-run passed. Action is valid and would execute successfully.",
                    was_dry_run=True,
                    data={
                        "policy": policy.decision,
                        "would_create_proposal": policy.decision == "REQUIRE_PROPOSAL",
                    },
                )

            # 5. Execute the action
            result = await action.execute(
                params=input_data.params,
                context=context,
                validate_only=False,
            )

            if result.success:
                return ActionExecutionResult(
                    success=True,
                    action_type=input_data.action_type,
                    message=result.message or "Action executed successfully",
                    data=result.to_dict(),
                )
            else:
                return ActionExecutionResult(
                    success=False,
                    action_type=input_data.action_type,
                    message=result.error or "Action execution failed",
                    error_code="EXECUTION_FAILED",
                    data=result.error_details,
                )

        except Exception as e:
            logger.exception(f"Action execution error: {input_data.action_type}")
            return ActionExecutionResult(
                success=False,
                action_type=input_data.action_type,
                message=f"Execution error: {str(e)}",
                error_code="EXECUTION_ERROR",
                suggestions=[
                    "Check the action parameters for correct types",
                    "Ensure all required fields are provided",
                ],
            )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _suggest_similar_actions(
        self, action_type: str, available: List[str], max_suggestions: int = 3
    ) -> List[str]:
        """Suggest similar action names using simple string matching."""
        action_lower = action_type.lower()
        parts = action_lower.replace(".", " ").replace("_", " ").split()

        scored = []
        for name in available:
            name_lower = name.lower()
            score = 0

            # Exact prefix match
            if name_lower.startswith(action_lower[:3]):
                score += 10

            # Part matching
            name_parts = name_lower.replace(".", " ").replace("_", " ").split()
            for part in parts:
                if part in name_parts:
                    score += 5
                elif any(part in np for np in name_parts):
                    score += 2

            if score > 0:
                scored.append((name, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored[:max_suggestions]]

    def _generate_validation_suggestions(
        self, action_type: str, errors: List[str]
    ) -> List[str]:
        """Generate helpful suggestions based on validation errors."""
        suggestions = []

        for error in errors:
            error_lower = error.lower()

            if "required" in error_lower:
                # Extract field name if possible
                suggestions.append("Ensure all required fields are provided")

            elif "length" in error_lower or "max" in error_lower:
                suggestions.append("Check field length constraints")

            elif "allowed" in error_lower or "enum" in error_lower:
                suggestions.append("Use one of the allowed values for this field")

            elif "type" in error_lower:
                suggestions.append("Check parameter types match expected schema")

        # Add generic suggestion
        suggestions.append(
            f"Use get_action_schema('{action_type}') to see required parameters"
        )

        return list(set(suggestions))


# =============================================================================
# TOOL EXPORT (for LLM function calling)
# =============================================================================


def get_tool_definition() -> Dict[str, Any]:
    """
    Get the OpenAI-compatible tool definition for ActionExecutorTool.

    Returns:
        Tool definition dict for function calling
    """
    return {
        "type": "function",
        "function": {
            "name": "action_executor",
            "description": ActionExecutorTool.TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["execute", "list", "schema"],
                        "description": "The operation to perform",
                    },
                    "action_type": {
                        "type": "string",
                        "description": "The action API name (required for 'execute' and 'schema')",
                    },
                    "params": {
                        "type": "object",
                        "description": "Action parameters (for 'execute' operation)",
                    },
                    "actor_id": {
                        "type": "string",
                        "description": "ID of the executing agent",
                        "default": "agent",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, validate without executing",
                        "default": False,
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Filter actions by namespace (for 'list' operation)",
                    },
                    "filter_hazardous": {
                        "type": "boolean",
                        "description": "Filter to hazardous actions only (for 'list' operation)",
                    },
                },
                "required": ["operation"],
            },
        },
    }
