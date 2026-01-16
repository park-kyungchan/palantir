"""
Orion ODA v3.0 - Hook Definition ObjectTypes
=============================================

Defines ODA ObjectTypes for the hook system:
- HookDefinition: Configuration for a hook (what to run, when)
- HookExecution: Execution record for audit trail

Reference: PAI/Packs/pai-hook-system/config/settings-hooks.json
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, ConfigDict

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type
from lib.oda.pai.hooks.event_types import HookEventType


class HookPriority(int, Enum):
    """
    Hook execution priority.

    Lower values execute first.
    Security hooks should use CRITICAL to run before other hooks.
    """

    CRITICAL = 0  # Security validation
    HIGH = 10  # Pre-processing
    NORMAL = 50  # Default
    LOW = 90  # Post-processing
    DEFERRED = 100  # Cleanup/logging


class HookCommandType(str, Enum):
    """
    Type of command a hook executes.

    - COMMAND: Shell command execution
    - PYTHON: Python function call
    - WEBHOOK: HTTP webhook call
    """

    COMMAND = "command"
    PYTHON = "python"
    WEBHOOK = "webhook"


class HookExecutionStatus(str, Enum):
    """
    Status of a hook execution.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    BLOCKED = "blocked"  # Blocked by security validator


@register_object_type
class HookDefinition(OntologyObject):
    """
    Definition of a hook that can be triggered by Claude Code events.

    This ObjectType represents a configured hook in the ODA system.
    Hooks are executed when matching events occur.

    Attributes:
        name: Human-readable hook name
        event: The event type that triggers this hook
        matcher: Pattern to match against (e.g., "Bash", "*" for all)
        command: Command or callable to execute
        command_type: Type of command (shell, python, webhook)
        description: Human-readable description
        priority: Execution priority (lower runs first)
        enabled: Whether the hook is active
        timeout_ms: Maximum execution time in milliseconds
        environment: Environment variables to set

    Example:
        ```python
        HookDefinition(
            name="security-validator",
            event=HookEventType.PRE_TOOL_USE,
            matcher="Bash",
            command="python -m lib.oda.pai.hooks.security_validator",
            description="Validate bash commands for security",
            priority=HookPriority.CRITICAL,
        )
        ```
    """

    # Required fields
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Human-readable hook name",
    )
    event: HookEventType = Field(
        ...,
        description="Event type that triggers this hook",
    )
    matcher: str = Field(
        default="*",
        description="Pattern to match against (tool name, '*' for all)",
    )
    command: str = Field(
        ...,
        min_length=1,
        description="Command to execute (shell command, python callable, or URL)",
    )

    # Optional fields
    command_type: HookCommandType = Field(
        default=HookCommandType.COMMAND,
        description="Type of command to execute",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Human-readable description of what this hook does",
    )
    priority: HookPriority = Field(
        default=HookPriority.NORMAL,
        description="Execution priority (lower runs first)",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this hook is active",
    )
    timeout_ms: int = Field(
        default=30000,
        ge=100,
        le=300000,
        description="Maximum execution time in milliseconds",
    )
    environment: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables to set for hook execution",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering",
    )

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate hook name format (alphanumeric, hyphens, underscores)."""
        import re

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", v):
            raise ValueError(
                "Hook name must start with a letter and contain only "
                "alphanumeric characters, hyphens, and underscores"
            )
        return v

    @property
    def is_blocking(self) -> bool:
        """Returns True if this hook can block execution."""
        return self.event.is_blocking

    @property
    def event_bus_type(self) -> str:
        """Get the ODA EventBus event type for this hook."""
        return self.event.to_event_bus_type()


@register_object_type
class HookExecution(OntologyObject):
    """
    Record of a hook execution for audit and observability.

    Created each time a hook is executed, regardless of outcome.
    Used for:
    - Audit trail of hook executions
    - Performance monitoring
    - Debugging failed hooks
    - Observability dashboard

    Attributes:
        hook_id: ID of the HookDefinition that was executed
        hook_name: Name of the hook (denormalized for queries)
        event_type: The event type that triggered execution
        input_data: Input data passed to the hook
        output_data: Output from the hook execution
        duration_ms: Execution time in milliseconds
        status: Execution status (success, failure, etc.)
        error_message: Error message if execution failed
        blocked_operation: True if hook blocked the operation (PreToolUse)
        session_id: Claude session ID
        tool_name: Name of the tool (for tool events)

    Example:
        ```python
        HookExecution(
            hook_id="abc-123",
            hook_name="security-validator",
            event_type=HookEventType.PRE_TOOL_USE,
            input_data={"tool": "Bash", "command": "rm -rf /"},
            status=HookExecutionStatus.SUCCESS,
            blocked_operation=True,
            duration_ms=15,
        )
        ```
    """

    # Required fields
    hook_id: str = Field(
        ...,
        description="ID of the HookDefinition that was executed",
    )
    hook_name: str = Field(
        ...,
        description="Name of the hook (denormalized)",
    )
    event_type: HookEventType = Field(
        ...,
        description="Event type that triggered execution",
    )
    status: HookExecutionStatus = Field(
        ...,
        description="Execution status",
    )

    # Execution data
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input data passed to the hook",
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Output from hook execution",
    )
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Execution time in milliseconds",
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if execution failed",
    )
    error_traceback: Optional[str] = Field(
        default=None,
        description="Full traceback if execution failed",
    )

    # Blocking result
    blocked_operation: bool = Field(
        default=False,
        description="True if hook blocked the operation",
    )
    block_reason: Optional[str] = Field(
        default=None,
        description="Reason for blocking (if blocked)",
    )

    # Context
    session_id: Optional[str] = Field(
        default=None,
        description="Claude session ID",
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Name of the tool (for tool events)",
    )
    execution_timestamp: datetime = Field(
        default_factory=utc_now,
        description="When the hook was executed",
    )

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    @property
    def is_successful(self) -> bool:
        """Returns True if execution was successful."""
        return self.status == HookExecutionStatus.SUCCESS

    @property
    def is_blocking_success(self) -> bool:
        """Returns True if hook successfully blocked an operation."""
        return self.blocked_operation and self.status == HookExecutionStatus.SUCCESS

    @classmethod
    def create_from_hook(
        cls,
        hook: HookDefinition,
        status: HookExecutionStatus,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0,
        **kwargs: Any,
    ) -> HookExecution:
        """
        Factory method to create HookExecution from a HookDefinition.

        Args:
            hook: The HookDefinition that was executed
            status: Execution status
            input_data: Input data passed to hook
            output_data: Output from hook
            duration_ms: Execution time
            **kwargs: Additional fields

        Returns:
            New HookExecution instance
        """
        return cls(
            hook_id=hook.id,
            hook_name=hook.name,
            event_type=hook.event,
            status=status,
            input_data=input_data or {},
            output_data=output_data or {},
            duration_ms=duration_ms,
            **kwargs,
        )
