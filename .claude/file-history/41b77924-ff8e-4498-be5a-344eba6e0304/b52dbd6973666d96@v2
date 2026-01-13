"""
Orion ODA PAI - Hooks Module

Event-driven hook system for Claude Code integration.

This module provides the infrastructure for the PAI hook system:
- HookEventType: Event type enum (PreToolUse, PostToolUse, etc.)
- HookDefinition: Hook configuration ObjectType
- HookRegistry: Dynamic hook registration and management
- Observability: Dashboard and telemetry integration
- SecurityValidator: Security validation hooks

Key Components:
- HookEventType: SESSION_START, SESSION_END, PRE_TOOL_USE, POST_TOOL_USE, etc.
- HookDefinition: event, matcher, command, priority
- HookExecution: Execution record for audit
- ObservabilityEvent: Telemetry payload
- SecurityValidator: Security check orchestration

Usage:
    ```python
    from lib.oda.pai.hooks import (
        HookEventType,
        HookDefinition,
        HookRegistry,
        HookExecution,
        SecurityValidator,
    )

    # Register a hook
    registry = HookRegistry()
    hook = HookDefinition(
        event=HookEventType.PRE_TOOL_USE,
        matcher={"tool_name": "Bash"},
        command="python validate_command.py",
        priority=100,
    )
    registry.register(hook)

    # Execute hooks for an event
    results = registry.execute_hooks(
        event_type=HookEventType.PRE_TOOL_USE,
        context={"tool_name": "Bash", "command": "rm -rf /"}
    )
    ```

Version: 1.0.0
"""

from lib.oda.pai.hooks.event_types import (
    HookEventType,
    get_event_bus_type,
    get_hook_event_type,
    HOOK_TO_EVENT_BUS_MAPPING,
)

from lib.oda.pai.hooks.hook_definition import (
    HookDefinition,
    HookExecution,
    HookMatcher,
    HookPriority,
)

from lib.oda.pai.hooks.hook_registry import (
    HookRegistry,
    RegisterHookAction,
    ExecuteHookAction,
)

from lib.oda.pai.hooks.observability import (
    ObservabilityEvent,
    ObservabilityConfig,
    ObservabilityClient,
    LogObservabilityAction,
)

from lib.oda.pai.hooks.security_validator import (
    SecurityValidator,
    SecurityCheckResult,
    SecurityRule,
    ValidateSecurityAction,
)


__all__ = [
    # Event Types
    "HookEventType",
    "get_event_bus_type",
    "get_hook_event_type",
    "HOOK_TO_EVENT_BUS_MAPPING",

    # Hook Definition
    "HookDefinition",
    "HookExecution",
    "HookMatcher",
    "HookPriority",

    # Hook Registry
    "HookRegistry",
    "RegisterHookAction",
    "ExecuteHookAction",

    # Observability
    "ObservabilityEvent",
    "ObservabilityConfig",
    "ObservabilityClient",
    "LogObservabilityAction",

    # Security
    "SecurityValidator",
    "SecurityCheckResult",
    "SecurityRule",
    "ValidateSecurityAction",
]


__version__ = "1.0.0"
