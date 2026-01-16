"""
Orion ODA v3.0 - Hook Registry
==============================

Dynamic hook registration and management system.
Provides:
- Hook registration and lookup
- Event-based hook triggering
- EventBus integration
- Priority-based execution ordering

Reference: PAI/Packs/pai-hook-system/config/settings-hooks.json
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from lib.oda.infrastructure.event_bus import DomainEvent, EventBus, get_event_bus
from lib.oda.pai.hooks.event_types import (
    EVENT_BUS_TO_HOOK_MAPPING,
    HOOK_TO_EVENT_BUS_MAPPING,
    HookEventType,
    get_hook_event_type,
)
from lib.oda.pai.hooks.hook_definition import (
    HookDefinition,
    HookExecution,
    HookExecutionStatus,
    HookPriority,
)

logger = logging.getLogger(__name__)


@dataclass
class HookExecutionResult:
    """
    Result of executing a single hook.

    Attributes:
        hook_id: ID of the executed hook
        hook_name: Name of the executed hook
        status: Execution status
        output: Output data from the hook
        duration_ms: Execution time in milliseconds
        blocked: Whether the hook blocked the operation
        block_reason: Reason for blocking (if blocked)
        error: Error message if execution failed
    """

    hook_id: str
    hook_name: str
    status: HookExecutionStatus
    output: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    blocked: bool = False
    block_reason: Optional[str] = None
    error: Optional[str] = None


@dataclass
class HookTriggerResult:
    """
    Result of triggering all hooks for an event.

    Attributes:
        event_type: The event type that was triggered
        results: List of individual hook execution results
        total_duration_ms: Total time to execute all hooks
        any_blocked: True if any hook blocked the operation
        block_reasons: Combined block reasons if blocked
    """

    event_type: HookEventType
    results: List[HookExecutionResult] = field(default_factory=list)
    total_duration_ms: int = 0
    any_blocked: bool = False
    block_reasons: List[str] = field(default_factory=list)

    @property
    def all_successful(self) -> bool:
        """Returns True if all hooks executed successfully."""
        return all(r.status == HookExecutionStatus.SUCCESS for r in self.results)

    @property
    def hook_count(self) -> int:
        """Number of hooks that were executed."""
        return len(self.results)


class HookRegistry:
    """
    Singleton registry for managing hook definitions.

    Features:
    - Dynamic hook registration
    - Event-based lookup with matcher support
    - Priority-based execution ordering
    - EventBus integration for ODA domain events

    Usage:
        ```python
        registry = HookRegistry.get_instance()

        # Register a hook
        hook = HookDefinition(
            name="security-validator",
            event=HookEventType.PRE_TOOL_USE,
            matcher="Bash",
            command="python security_check.py",
        )
        registry.register(hook)

        # Get hooks for an event
        hooks = registry.get_hooks(HookEventType.PRE_TOOL_USE, tool_name="Bash")

        # Trigger all matching hooks
        result = await registry.trigger(
            HookEventType.PRE_TOOL_USE,
            input_data={"tool": "Bash", "command": "ls -la"},
            tool_name="Bash",
        )
        ```
    """

    _instance: Optional[HookRegistry] = None

    def __init__(self) -> None:
        # Hook ID -> HookDefinition
        self._hooks: Dict[str, HookDefinition] = {}
        # Event type -> Set of hook IDs
        self._event_index: Dict[HookEventType, Set[str]] = {}
        # EventBus subscriptions (pattern -> unsubscribe callable)
        self._subscriptions: Dict[str, Callable[[], None]] = {}
        # Hook executors (command_type -> executor callable)
        self._executors: Dict[str, Callable] = {}

    @classmethod
    def get_instance(cls) -> HookRegistry:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("HookRegistry singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        if cls._instance:
            cls._instance._unsubscribe_all()
        cls._instance = None

    def register(self, hook: HookDefinition) -> None:
        """
        Register a hook definition.

        Args:
            hook: HookDefinition to register

        Raises:
            ValueError: If a hook with the same ID is already registered
        """
        if hook.id in self._hooks:
            raise ValueError(f"Hook with ID {hook.id} is already registered")

        self._hooks[hook.id] = hook

        # Update event index
        if hook.event not in self._event_index:
            self._event_index[hook.event] = set()
        self._event_index[hook.event].add(hook.id)

        logger.info(f"Registered hook: {hook.name} (event={hook.event.value})")

    def unregister(self, hook_id: str) -> bool:
        """
        Unregister a hook by ID.

        Args:
            hook_id: ID of the hook to unregister

        Returns:
            True if hook was found and unregistered, False otherwise
        """
        if hook_id not in self._hooks:
            return False

        hook = self._hooks.pop(hook_id)

        # Update event index
        if hook.event in self._event_index:
            self._event_index[hook.event].discard(hook_id)

        logger.info(f"Unregistered hook: {hook.name}")
        return True

    def get_hook(self, hook_id: str) -> Optional[HookDefinition]:
        """Get a hook by ID."""
        return self._hooks.get(hook_id)

    def get_hook_by_name(self, name: str) -> Optional[HookDefinition]:
        """Get a hook by name (first match)."""
        for hook in self._hooks.values():
            if hook.name == name:
                return hook
        return None

    def list_hooks(
        self,
        event_type: Optional[HookEventType] = None,
        enabled_only: bool = True,
    ) -> List[HookDefinition]:
        """
        List all registered hooks.

        Args:
            event_type: Filter by event type (None for all)
            enabled_only: Only return enabled hooks

        Returns:
            List of HookDefinition instances
        """
        hooks = list(self._hooks.values())

        if event_type:
            hooks = [h for h in hooks if h.event == event_type]

        if enabled_only:
            hooks = [h for h in hooks if h.enabled]

        # Sort by priority
        return sorted(hooks, key=lambda h: h.priority.value)

    def get_hooks(
        self,
        event_type: HookEventType,
        tool_name: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[HookDefinition]:
        """
        Get all hooks matching an event and optional tool name.

        Args:
            event_type: Event type to match
            tool_name: Tool name to match against hook matchers
            enabled_only: Only return enabled hooks

        Returns:
            List of matching HookDefinition instances, sorted by priority
        """
        hook_ids = self._event_index.get(event_type, set())
        hooks: List[HookDefinition] = []

        for hook_id in hook_ids:
            hook = self._hooks.get(hook_id)
            if not hook:
                continue

            if enabled_only and not hook.enabled:
                continue

            # Check matcher
            if tool_name:
                if not self._matches(hook.matcher, tool_name):
                    continue

            hooks.append(hook)

        # Sort by priority (lower value = higher priority)
        return sorted(hooks, key=lambda h: h.priority.value)

    async def trigger(
        self,
        event_type: HookEventType,
        input_data: Dict[str, Any],
        tool_name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> HookTriggerResult:
        """
        Trigger all matching hooks for an event.

        Args:
            event_type: Event type to trigger
            input_data: Input data to pass to hooks
            tool_name: Tool name for matcher filtering
            session_id: Claude session ID

        Returns:
            HookTriggerResult with all execution results
        """
        start_time = time.time()
        hooks = self.get_hooks(event_type, tool_name)

        result = HookTriggerResult(event_type=event_type)

        for hook in hooks:
            exec_result = await self._execute_hook(
                hook,
                input_data,
                session_id=session_id,
                tool_name=tool_name,
            )
            result.results.append(exec_result)

            # Track blocking
            if exec_result.blocked:
                result.any_blocked = True
                if exec_result.block_reason:
                    result.block_reasons.append(exec_result.block_reason)

                # For blocking events, stop execution on first block
                if event_type.is_blocking:
                    break

        result.total_duration_ms = int((time.time() - start_time) * 1000)

        # Publish to EventBus
        await self._publish_trigger_event(event_type, result, input_data)

        return result

    async def _execute_hook(
        self,
        hook: HookDefinition,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> HookExecutionResult:
        """
        Execute a single hook.

        Args:
            hook: HookDefinition to execute
            input_data: Input data for the hook
            session_id: Claude session ID
            tool_name: Tool name (for context)

        Returns:
            HookExecutionResult with execution details
        """
        start_time = time.time()

        try:
            # Get executor for command type
            executor = self._get_executor(hook.command_type.value)
            if not executor:
                return HookExecutionResult(
                    hook_id=hook.id,
                    hook_name=hook.name,
                    status=HookExecutionStatus.FAILURE,
                    error=f"No executor for command type: {hook.command_type.value}",
                )

            # Execute with timeout
            try:
                output = await asyncio.wait_for(
                    executor(hook, input_data),
                    timeout=hook.timeout_ms / 1000,
                )
            except asyncio.TimeoutError:
                duration_ms = int((time.time() - start_time) * 1000)
                return HookExecutionResult(
                    hook_id=hook.id,
                    hook_name=hook.name,
                    status=HookExecutionStatus.TIMEOUT,
                    duration_ms=duration_ms,
                    error=f"Hook timed out after {hook.timeout_ms}ms",
                )

            duration_ms = int((time.time() - start_time) * 1000)

            # Parse output for blocking result
            blocked = output.get("blocked", False) if isinstance(output, dict) else False
            block_reason = (
                output.get("block_reason") if isinstance(output, dict) else None
            )

            # Create execution record
            execution = HookExecution.create_from_hook(
                hook=hook,
                status=HookExecutionStatus.SUCCESS,
                input_data=input_data,
                output_data=output if isinstance(output, dict) else {"result": output},
                duration_ms=duration_ms,
                blocked_operation=blocked,
                block_reason=block_reason,
                session_id=session_id,
                tool_name=tool_name,
            )

            # Store execution record (in production, persist to DB)
            logger.debug(f"Hook executed: {hook.name} (duration={duration_ms}ms)")

            return HookExecutionResult(
                hook_id=hook.id,
                hook_name=hook.name,
                status=HookExecutionStatus.SUCCESS,
                output=output if isinstance(output, dict) else {"result": output},
                duration_ms=duration_ms,
                blocked=blocked,
                block_reason=block_reason,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Hook execution failed: {hook.name} - {e}", exc_info=True)

            return HookExecutionResult(
                hook_id=hook.id,
                hook_name=hook.name,
                status=HookExecutionStatus.FAILURE,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _get_executor(self, command_type: str) -> Optional[Callable]:
        """Get executor for a command type."""
        # Return registered executor or default
        if command_type in self._executors:
            return self._executors[command_type]

        # Default executors
        if command_type == "command":
            return self._execute_shell_command
        elif command_type == "python":
            return self._execute_python_callable
        elif command_type == "webhook":
            return self._execute_webhook

        return None

    def register_executor(
        self,
        command_type: str,
        executor: Callable,
    ) -> None:
        """
        Register a custom executor for a command type.

        Args:
            command_type: Command type (e.g., "custom")
            executor: Async callable that takes (hook, input_data) and returns output
        """
        self._executors[command_type] = executor
        logger.info(f"Registered executor for command type: {command_type}")

    async def _execute_shell_command(
        self,
        hook: HookDefinition,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a shell command hook.

        Args:
            hook: HookDefinition with command
            input_data: Input data (passed as env vars)

        Returns:
            Command output as dict
        """
        import json
        import os

        # Prepare environment
        env = os.environ.copy()
        env.update(hook.environment)
        env["HOOK_INPUT"] = json.dumps(input_data)
        env["HOOK_NAME"] = hook.name
        env["HOOK_EVENT"] = hook.event.value

        # Execute command
        proc = await asyncio.create_subprocess_shell(
            hook.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return {
                "success": False,
                "error": stderr.decode() if stderr else "Command failed",
                "return_code": proc.returncode,
            }

        # Try to parse JSON output
        output_text = stdout.decode().strip()
        try:
            return json.loads(output_text)
        except json.JSONDecodeError:
            return {"success": True, "output": output_text}

    async def _execute_python_callable(
        self,
        hook: HookDefinition,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a Python callable hook.

        Args:
            hook: HookDefinition with python callable path
            input_data: Input data to pass to callable

        Returns:
            Callable result as dict
        """
        import importlib

        # Parse callable path (e.g., "module.submodule:function_name")
        if ":" not in hook.command:
            raise ValueError(f"Invalid python callable format: {hook.command}")

        module_path, func_name = hook.command.rsplit(":", 1)

        # Import module and get function
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)

        # Execute
        if asyncio.iscoroutinefunction(func):
            result = await func(input_data, hook=hook)
        else:
            result = func(input_data, hook=hook)

        if isinstance(result, dict):
            return result
        return {"result": result}

    async def _execute_webhook(
        self,
        hook: HookDefinition,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a webhook hook.

        Args:
            hook: HookDefinition with webhook URL
            input_data: Input data to POST

        Returns:
            Webhook response as dict
        """
        try:
            import aiohttp
        except ImportError:
            return {"error": "aiohttp not installed for webhook support"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                hook.command,
                json=input_data,
                timeout=aiohttp.ClientTimeout(total=hook.timeout_ms / 1000),
            ) as response:
                return await response.json()

    async def _publish_trigger_event(
        self,
        event_type: HookEventType,
        result: HookTriggerResult,
        input_data: Dict[str, Any],
    ) -> None:
        """Publish hook trigger event to EventBus."""
        event_bus = get_event_bus()
        await event_bus.publish(
            event_type=f"Hook.triggered",
            payload={
                "hook_event_type": event_type.value,
                "hook_count": result.hook_count,
                "any_blocked": result.any_blocked,
                "total_duration_ms": result.total_duration_ms,
            },
            metadata={
                "input_data_keys": list(input_data.keys()),
                "results": [
                    {
                        "hook_name": r.hook_name,
                        "status": r.status.value,
                        "blocked": r.blocked,
                    }
                    for r in result.results
                ],
            },
        )

    def subscribe_to_event_bus(self) -> None:
        """
        Subscribe to ODA EventBus events and trigger corresponding hooks.

        This enables automatic hook triggering from EventBus events.
        """
        event_bus = get_event_bus()

        for hook_event, event_bus_type in HOOK_TO_EVENT_BUS_MAPPING.items():
            if event_bus_type not in self._subscriptions:
                unsubscribe = event_bus.subscribe(
                    event_bus_type,
                    lambda evt, he=hook_event: asyncio.create_task(
                        self._on_event_bus_event(evt, he)
                    ),
                )
                self._subscriptions[event_bus_type] = unsubscribe
                logger.debug(f"Subscribed to EventBus: {event_bus_type} -> {hook_event.value}")

    def _unsubscribe_all(self) -> None:
        """Unsubscribe from all EventBus events."""
        for unsubscribe in self._subscriptions.values():
            unsubscribe()
        self._subscriptions.clear()

    async def _on_event_bus_event(
        self,
        event: DomainEvent,
        hook_event: HookEventType,
    ) -> None:
        """Handle EventBus event and trigger corresponding hooks."""
        input_data = {
            "event_type": event.event_type,
            "payload": event.payload,
            "actor_id": event.actor_id,
            "metadata": event.metadata,
        }

        await self.trigger(
            event_type=hook_event,
            input_data=input_data,
        )

    @staticmethod
    def _matches(pattern: str, value: str) -> bool:
        """Check if a value matches a pattern (supports wildcards)."""
        if pattern == "*":
            return True
        return fnmatch.fnmatch(value, pattern)


# Module-level convenience functions
def get_hook_registry() -> HookRegistry:
    """Get the global HookRegistry instance."""
    return HookRegistry.get_instance()


def register_hook(hook: HookDefinition) -> None:
    """Register a hook with the global registry."""
    HookRegistry.get_instance().register(hook)


async def trigger_hooks(
    event_type: HookEventType,
    input_data: Dict[str, Any],
    tool_name: Optional[str] = None,
) -> HookTriggerResult:
    """Trigger hooks with the global registry."""
    return await HookRegistry.get_instance().trigger(
        event_type=event_type,
        input_data=input_data,
        tool_name=tool_name,
    )
