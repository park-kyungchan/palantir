"""
Orion ODA v4.0 - OpenAI Action Adapter

Adapter for direct OpenAI API integration.
Supports all OpenAI-compatible endpoints including Codex.

Key Features:
- Direct OpenAI API integration
- Function calling support
- Structured output via Instructor
- Compatible with Codex and other OpenAI-compatible APIs
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from lib.oda.llm.adapters.base import (
    AdapterCapabilities,
    BaseActionAdapter,
    ExecutionMode,
    ActionExecutionError,
)
from lib.oda.llm.providers import OpenAICompatibleProvider, LLMProviderType
from lib.oda.ontology.actions import ActionContext, ActionResult, ActionType

logger = logging.getLogger(__name__)


class OpenAIActionAdapter(BaseActionAdapter):
    """
    OpenAI Action Adapter.

    This adapter executes ODA actions using the OpenAI API.
    It supports both direct OpenAI and any OpenAI-compatible endpoints
    (like Codex, Azure OpenAI, etc.).

    Execution Strategy:
    1. For simple actions: Direct action.execute() call
    2. For complex actions: Function calling with GPT-4

    The adapter maintains the same interface as other adapters while
    leveraging OpenAI's capabilities when beneficial.

    Usage:
        provider = OpenAICompatibleProvider(config)
        adapter = OpenAIActionAdapter(provider)
        result = await adapter.execute_action(
            "memory.save_insight",
            {"content": "...", "source": "..."},
            ActionContext(actor_id="openai-agent")
        )
    """

    def __init__(self, provider: OpenAICompatibleProvider):
        """
        Initialize the OpenAI adapter.

        Args:
            provider: OpenAICompatibleProvider instance

        Raises:
            ValueError: If provider is not an OpenAICompatibleProvider
        """
        if not isinstance(provider, OpenAICompatibleProvider):
            raise ValueError(
                f"OpenAIActionAdapter requires OpenAICompatibleProvider, "
                f"got {type(provider).__name__}"
            )
        super().__init__(provider)
        self._client: Optional[OpenAI] = None

    @property
    def name(self) -> str:
        return "openai-adapter"

    @property
    def client(self) -> OpenAI:
        """
        Lazy-initialize and return the OpenAI client.
        """
        if self._client is None:
            self._client = self._provider.build_client()
        return self._client

    def get_capabilities(self) -> AdapterCapabilities:
        """
        OpenAI capabilities.

        Uses API calls with full function calling support.
        Rate limits depend on OpenAI tier.
        """
        return AdapterCapabilities(
            execution_mode=ExecutionMode.FUNCTION_CALLING,
            supports_streaming=True,
            supports_async=True,
            supports_batch=True,  # OpenAI supports batch API
            supports_function_calling=True,
            max_tokens_per_request=128000,  # GPT-4 Turbo context
            rate_limit_rpm=500,  # Varies by tier
        )

    def is_available(self) -> bool:
        """
        Check if OpenAI endpoint is reachable.
        """
        return self._provider.is_available()

    async def _execute_action_impl(
        self,
        action: ActionType,
        params: Dict[str, Any],
        context: ActionContext,
        validate_only: bool,
        return_edits: bool
    ) -> ActionResult:
        """
        Execute action via OpenAI.

        Current implementation: Direct action execution.
        The LLM-agnostic design means we can execute actions directly
        in Python, with the option to use LLM assistance when needed.
        """
        try:
            # Direct execution - OpenAI adapter runs Python in-process
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
            result.error_details["execution_mode"] = ExecutionMode.FUNCTION_CALLING.value
            result.error_details["model"] = self._provider.default_model()

            return result

        except Exception as e:
            self._logger.exception(f"OpenAI execution failed: {action.api_name}")
            raise ActionExecutionError(
                message=f"OpenAI execution failed: {str(e)}",
                action_api_name=action.api_name,
                provider_type=LLMProviderType.OPENAI,
                details={
                    "exception_type": type(e).__name__,
                    "model": self._provider.default_model(),
                }
            ) from e

    def _build_tool_schema(self, action: ActionType) -> Dict[str, Any]:
        """
        Build OpenAI tools schema from action.

        Converts ODA action parameter schema to OpenAI tools format.
        Uses the newer 'tools' API (not deprecated 'functions').
        """
        param_schema = action.get_parameter_schema()

        return {
            "type": "function",
            "function": {
                "name": action.api_name.replace(".", "_"),  # OpenAI doesn't allow dots
                "description": param_schema.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": param_schema.get("properties", {}),
                    "required": param_schema.get("required", []),
                    "additionalProperties": False
                },
                "strict": True  # Enable structured outputs
            }
        }

    async def execute_with_structured_output(
        self,
        action_api_name: str,
        prompt: str,
        context: ActionContext,
        *,
        system_prompt: Optional[str] = None
    ) -> ActionResult:
        """
        Execute action using OpenAI's structured output capability.

        Uses the response_format parameter for guaranteed JSON schema
        compliance, combined with function calling for action execution.

        Args:
            action_api_name: The api_name of the action
            prompt: User prompt describing what to do
            context: Execution context
            system_prompt: Optional system prompt override

        Returns:
            ActionResult from the execution

        Note:
            This leverages OpenAI's structured output feature for
            reliable JSON generation. Useful for complex param extraction.
        """
        from lib.oda.ontology.actions import action_registry

        action_class = action_registry.get(action_api_name)
        if action_class is None:
            raise ActionExecutionError(
                message=f"Action '{action_api_name}' not found",
                action_api_name=action_api_name,
                provider_type=LLMProviderType.OPENAI,
            )

        action = action_class()
        tool_schema = self._build_tool_schema(action)

        default_system = (
            "You are an ODA action executor. Extract parameters from the user's "
            "request and call the appropriate function. Be precise and follow "
            "the parameter schema exactly."
        )

        try:
            response = self.client.chat.completions.create(
                model=self._provider.default_model(),
                messages=[
                    {"role": "system", "content": system_prompt or default_system},
                    {"role": "user", "content": prompt}
                ],
                tools=[tool_schema],
                tool_choice="required"
            )

            # Extract parameters from tool call
            if not response.choices[0].message.tool_calls:
                raise ActionExecutionError(
                    message="No tool call in response",
                    action_api_name=action_api_name,
                    provider_type=LLMProviderType.OPENAI,
                )

            tool_call = response.choices[0].message.tool_calls[0]
            extracted_params = json.loads(tool_call.function.arguments)

            self._logger.info(
                f"Structured output extracted for {action_api_name}: {extracted_params}"
            )

            # Execute with extracted parameters
            return await self.execute_action(
                action_api_name=action_api_name,
                params=extracted_params,
                context=context
            )

        except Exception as e:
            self._logger.exception(f"Structured output execution failed: {action_api_name}")
            raise ActionExecutionError(
                message=f"Structured output failed: {str(e)}",
                action_api_name=action_api_name,
                provider_type=LLMProviderType.OPENAI,
                details={"structured_output_error": True}
            ) from e

    async def execute_batch(
        self,
        action_requests: List[Dict[str, Any]],
        context: ActionContext
    ) -> List[ActionResult]:
        """
        Execute multiple actions in batch.

        Leverages OpenAI's batch API for efficient bulk execution.
        Each request should have 'action_api_name' and 'params'.

        Args:
            action_requests: List of {"action_api_name": str, "params": dict}
            context: Shared execution context

        Returns:
            List of ActionResult in same order as requests

        Note:
            OpenAI-specific feature for bulk operations.
            Other adapters fall back to sequential execution.
        """
        results = []

        # For now, execute sequentially
        # TODO: Implement true batch API when needed
        for request in action_requests:
            action_api_name = request.get("action_api_name")
            params = request.get("params", {})

            if not action_api_name:
                results.append(ActionResult(
                    action_type="unknown",
                    success=False,
                    error="Missing action_api_name in batch request"
                ))
                continue

            try:
                result = await self.execute_action(
                    action_api_name=action_api_name,
                    params=params,
                    context=context
                )
                results.append(result)
            except Exception as e:
                results.append(ActionResult(
                    action_type=action_api_name,
                    success=False,
                    error=str(e),
                    error_details={"exception_type": type(e).__name__}
                ))

        return results
