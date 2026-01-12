"""
Orion ODA v4.0 - Gemini/Antigravity Action Adapter

Adapter for Antigravity backend (Gemini) via OpenAI-compatible API.
Uses the OpenAI SDK with custom base_url pointing to Antigravity.

Key Features:
- OpenAI-compatible API interface
- Gemini model backend
- Structured output via Instructor
- Function calling support for action execution
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
from lib.oda.llm.providers import AntigravityProvider, LLMProviderType
from lib.oda.ontology.actions import ActionContext, ActionResult, ActionType

logger = logging.getLogger(__name__)


class GeminiActionAdapter(BaseActionAdapter):
    """
    Gemini/Antigravity Action Adapter.

    This adapter executes ODA actions through the Antigravity backend,
    which provides Gemini access via an OpenAI-compatible API.

    Execution Strategy:
    1. For simple actions: Direct action.execute() call
    2. For complex actions: LLM-assisted execution with function calling

    The adapter maintains the same interface as other adapters while
    leveraging Gemini's capabilities when beneficial.

    Usage:
        provider = AntigravityProvider(config)
        adapter = GeminiActionAdapter(provider)
        result = await adapter.execute_action(
            "memory.save_insight",
            {"content": "...", "source": "..."},
            ActionContext(actor_id="gemini-agent")
        )
    """

    def __init__(self, provider: AntigravityProvider):
        """
        Initialize the Gemini adapter.

        Args:
            provider: AntigravityProvider instance

        Raises:
            ValueError: If provider is not an AntigravityProvider
        """
        if not isinstance(provider, AntigravityProvider):
            raise ValueError(
                f"GeminiActionAdapter requires AntigravityProvider, "
                f"got {type(provider).__name__}"
            )
        super().__init__(provider)
        self._client: Optional[OpenAI] = None

    @property
    def name(self) -> str:
        return "gemini-adapter"

    @property
    def client(self) -> OpenAI:
        """
        Lazy-initialize and return the OpenAI client.

        The client is configured to use the Antigravity endpoint.
        """
        if self._client is None:
            self._client = self._provider.build_client()
        return self._client

    def get_capabilities(self) -> AdapterCapabilities:
        """
        Gemini/Antigravity capabilities.

        Uses API calls with function calling support.
        Rate limits depend on Antigravity configuration.
        """
        return AdapterCapabilities(
            execution_mode=ExecutionMode.API_CALL,
            supports_streaming=True,
            supports_async=True,
            supports_batch=False,
            supports_function_calling=True,
            max_tokens_per_request=32768,  # Gemini 1.5 context window
            rate_limit_rpm=60,  # Typical Antigravity rate limit
        )

    def is_available(self) -> bool:
        """
        Check if Antigravity endpoint is reachable.
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
        Execute action via Antigravity/Gemini.

        Current implementation: Direct action execution (same as Claude).
        Future enhancement: LLM-assisted execution for complex actions.

        The key design principle is that this method produces the same
        ActionResult as other adapters - the underlying execution
        mechanism is an implementation detail.
        """
        try:
            # Direct execution - Gemini adapter runs Python in-process
            # This matches the Claude adapter behavior for consistency
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
            result.error_details["execution_mode"] = ExecutionMode.API_CALL.value
            result.error_details["model"] = self._provider.default_model()

            return result

        except Exception as e:
            self._logger.exception(f"Gemini execution failed: {action.api_name}")
            raise ActionExecutionError(
                message=f"Gemini execution failed: {str(e)}",
                action_api_name=action.api_name,
                provider_type=LLMProviderType.ANTIGRAVITY,
                details={
                    "exception_type": type(e).__name__,
                    "model": self._provider.default_model(),
                }
            ) from e

    def _build_function_schema(self, action: ActionType) -> Dict[str, Any]:
        """
        Build OpenAI function calling schema from action.

        Converts ODA action parameter schema to OpenAI function format.
        This enables LLM-assisted parameter extraction and validation.
        """
        param_schema = action.get_parameter_schema()

        return {
            "type": "function",
            "function": {
                "name": action.api_name,
                "description": param_schema.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": param_schema.get("properties", {}),
                    "required": param_schema.get("required", []),
                }
            }
        }

    async def execute_with_llm_assist(
        self,
        action_api_name: str,
        natural_language_request: str,
        context: ActionContext,
        *,
        extract_params: bool = True
    ) -> ActionResult:
        """
        Execute action with LLM-assisted parameter extraction.

        Uses Gemini to extract action parameters from natural language,
        then executes the action with those parameters.

        Args:
            action_api_name: The api_name of the action
            natural_language_request: Free-form request text
            context: Execution context
            extract_params: If True, use LLM to extract params

        Returns:
            ActionResult from the execution

        Note:
            This is a Gemini-specific extension for natural language
            action invocation. Useful for chat-based interfaces.
        """
        from lib.oda.ontology.actions import action_registry

        action_class = action_registry.get(action_api_name)
        if action_class is None:
            raise ActionExecutionError(
                message=f"Action '{action_api_name}' not found",
                action_api_name=action_api_name,
                provider_type=LLMProviderType.ANTIGRAVITY,
            )

        action = action_class()

        if not extract_params:
            # Direct execution without LLM assist
            return await self.execute_action(
                action_api_name=action_api_name,
                params={},
                context=context
            )

        # Use function calling to extract parameters
        function_schema = self._build_function_schema(action)

        try:
            response = self.client.chat.completions.create(
                model=self._provider.default_model(),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract the parameters for the requested action. "
                            "Use the function calling capability to structure the response."
                        )
                    },
                    {
                        "role": "user",
                        "content": natural_language_request
                    }
                ],
                tools=[function_schema],
                tool_choice={"type": "function", "function": {"name": action_api_name}}
            )

            # Extract parameters from function call
            tool_call = response.choices[0].message.tool_calls[0]
            extracted_params = json.loads(tool_call.function.arguments)

            self._logger.info(
                f"LLM extracted params for {action_api_name}: {extracted_params}"
            )

            # Execute with extracted parameters
            return await self.execute_action(
                action_api_name=action_api_name,
                params=extracted_params,
                context=context
            )

        except Exception as e:
            self._logger.exception(f"LLM-assisted extraction failed: {action_api_name}")
            raise ActionExecutionError(
                message=f"LLM parameter extraction failed: {str(e)}",
                action_api_name=action_api_name,
                provider_type=LLMProviderType.ANTIGRAVITY,
                details={"extraction_error": True}
            ) from e
