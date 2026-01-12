"""
Orion ODA v4.0 - Claude Code Action Adapter

CLI-native adapter for Claude Code integration.
This adapter does NOT use an API - it leverages direct CLI operations
within the Claude Code environment.

Key Features:
- No API key required (AIP-Free)
- CLI-native action execution
- Direct integration with Claude Code's native capabilities
- Supports Claude Code's Task delegation for complex operations
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from lib.oda.llm.adapters.base import (
    AdapterCapabilities,
    BaseActionAdapter,
    ExecutionMode,
    ActionExecutionError,
)
from lib.oda.llm.providers import ClaudeCodeProvider, LLMProviderType
from lib.oda.ontology.actions import ActionContext, ActionResult, ActionType

logger = logging.getLogger(__name__)


class ClaudeActionAdapter(BaseActionAdapter):
    """
    Claude Code CLI-native Action Adapter.

    This adapter executes ODA actions directly within the Claude Code
    CLI environment. No external API calls are made - all operations
    are performed through Claude Code's native capabilities.

    Execution Flow:
    1. Action lookup from registry (inherited)
    2. Parameter validation (inherited)
    3. Direct action.execute() call (CLI-native)
    4. Result packaging and return

    Usage:
        provider = ClaudeCodeProvider(config)
        adapter = ClaudeActionAdapter(provider)
        result = await adapter.execute_action(
            "memory.save_insight",
            {"content": "...", "source": "..."},
            ActionContext(actor_id="claude-agent")
        )
    """

    def __init__(self, provider: ClaudeCodeProvider):
        """
        Initialize the Claude Code adapter.

        Args:
            provider: ClaudeCodeProvider instance (must be CLI-native)

        Raises:
            ValueError: If provider is not a ClaudeCodeProvider
        """
        if not isinstance(provider, ClaudeCodeProvider):
            raise ValueError(
                f"ClaudeActionAdapter requires ClaudeCodeProvider, "
                f"got {type(provider).__name__}"
            )
        super().__init__(provider)
        self._cli_native = True

    @property
    def name(self) -> str:
        return "claude-code-adapter"

    def get_capabilities(self) -> AdapterCapabilities:
        """
        Claude Code capabilities.

        CLI-native mode with full async support.
        No rate limits since operations are local.
        """
        return AdapterCapabilities(
            execution_mode=ExecutionMode.CLI_NATIVE,
            supports_streaming=False,  # CLI operations are synchronous
            supports_async=True,
            supports_batch=False,
            supports_function_calling=True,  # Claude Code has native tool support
            max_tokens_per_request=None,  # No limit for CLI operations
            rate_limit_rpm=None,  # No rate limit for local execution
        )

    def is_available(self) -> bool:
        """
        Check if running in Claude Code environment.

        Verifies presence of Claude Code environment indicators.
        """
        # Check for Claude Code environment
        is_claude_env = bool(
            os.environ.get("CLAUDE_CODE") or
            os.environ.get("CLAUDE_CODE_SESSION") or
            os.environ.get("CLAUDE_SESSION_ID")
        )

        if not is_claude_env:
            # Fallback: Check if provider reports available
            is_claude_env = self._provider.is_available()

        return is_claude_env

    async def _execute_action_impl(
        self,
        action: ActionType,
        params: Dict[str, Any],
        context: ActionContext,
        validate_only: bool,
        return_edits: bool
    ) -> ActionResult:
        """
        CLI-native action execution.

        Directly calls action.execute() since we're running within
        the Claude Code environment. No API translation needed.

        This is the simplest adapter implementation since Claude Code
        has direct access to the Python runtime.
        """
        try:
            # Direct execution - Claude Code is in-process
            result = await action.execute(
                params=params,
                context=context,
                validate_only=validate_only,
                return_edits=return_edits
            )

            # Enrich result with adapter metadata
            if result.error_details is None:
                result.error_details = {}
            result.error_details["adapter"] = self.name
            result.error_details["execution_mode"] = ExecutionMode.CLI_NATIVE.value

            return result

        except Exception as e:
            self._logger.exception(f"CLI-native execution failed: {action.api_name}")
            raise ActionExecutionError(
                message=f"CLI-native execution failed: {str(e)}",
                action_api_name=action.api_name,
                provider_type=LLMProviderType.CLAUDE_CODE,
                details={
                    "exception_type": type(e).__name__,
                    "cli_native": True,
                }
            ) from e

    async def execute_with_task_delegation(
        self,
        action_api_name: str,
        params: Dict[str, Any],
        context: ActionContext,
        *,
        subagent_type: str = "general-purpose",
        run_in_background: bool = False
    ) -> ActionResult:
        """
        Execute action using Claude Code's Task delegation.

        This method leverages Claude Code's native Task capability
        for complex operations that benefit from subagent delegation.

        Args:
            action_api_name: The api_name of the action
            params: Action parameters
            context: Execution context
            subagent_type: Type of subagent to delegate to
            run_in_background: If True, run task in background

        Returns:
            ActionResult from the delegated execution

        Note:
            This is a Claude Code-specific extension. Other adapters
            do not have this capability.
        """
        # For now, fall back to direct execution
        # Task delegation would be implemented here when needed
        self._logger.info(
            f"Task delegation requested for {action_api_name} "
            f"[subagent={subagent_type}, background={run_in_background}]"
        )

        # Direct execution as baseline
        return await self.execute_action(
            action_api_name=action_api_name,
            params=params,
            context=context
        )
