"""
Orion ODA v4.0 - LLM Action Adapter Base Protocol

Defines the LLMActionAdapter Protocol that all LLM adapters must implement.
This ensures LLM-agnostic action execution across the ODA system.

Protocol Requirements:
1. execute_action(): Execute an ODA action with full context
2. validate_action(): Validate action parameters before execution
3. get_capabilities(): Report adapter capabilities
4. is_available(): Check if the adapter is ready for use
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Type, runtime_checkable

from lib.oda.ontology.actions import ActionContext, ActionResult, ActionType, action_registry
from lib.oda.llm.providers import LLMProvider, LLMProviderType

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class ActionExecutionError(Exception):
    """Raised when action execution fails at the adapter level."""

    def __init__(
        self,
        message: str,
        action_api_name: str,
        provider_type: LLMProviderType,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.action_api_name = action_api_name
        self.provider_type = provider_type
        self.details = details or {}
        super().__init__(f"[{provider_type.value}] {action_api_name}: {message}")


class ActionValidationError(Exception):
    """Raised when action validation fails at the adapter level."""

    def __init__(
        self,
        message: str,
        action_api_name: str,
        validation_errors: List[str]
    ):
        self.message = message
        self.action_api_name = action_api_name
        self.validation_errors = validation_errors
        super().__init__(f"{action_api_name}: {message}")


# =============================================================================
# CAPABILITIES
# =============================================================================

class ExecutionMode(str, Enum):
    """How the adapter executes actions."""
    CLI_NATIVE = "cli_native"      # Direct CLI integration (Claude Code)
    API_CALL = "api_call"          # REST API calls
    FUNCTION_CALLING = "function_calling"  # LLM function/tool calling


@dataclass(frozen=True)
class AdapterCapabilities:
    """
    Describes the capabilities of an LLM adapter.

    Used for runtime capability checking and adapter selection.
    """
    execution_mode: ExecutionMode
    supports_streaming: bool = False
    supports_async: bool = True
    supports_batch: bool = False
    supports_function_calling: bool = False
    max_tokens_per_request: Optional[int] = None
    rate_limit_rpm: Optional[int] = None  # Requests per minute

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_mode": self.execution_mode.value,
            "supports_streaming": self.supports_streaming,
            "supports_async": self.supports_async,
            "supports_batch": self.supports_batch,
            "supports_function_calling": self.supports_function_calling,
            "max_tokens_per_request": self.max_tokens_per_request,
            "rate_limit_rpm": self.rate_limit_rpm,
        }


# =============================================================================
# LLM ACTION ADAPTER PROTOCOL
# =============================================================================

@runtime_checkable
class LLMActionAdapter(Protocol):
    """
    Protocol for LLM Action Adapters.

    All LLM adapters must implement this protocol to ensure consistent
    action execution behavior across different LLM backends.

    This is the core abstraction for LLM-Agnostic Governance in ODA.
    """

    @property
    def name(self) -> str:
        """Human-readable name of this adapter."""
        ...

    @property
    def provider_type(self) -> LLMProviderType:
        """The LLM provider type this adapter wraps."""
        ...

    def get_capabilities(self) -> AdapterCapabilities:
        """
        Return the capabilities of this adapter.

        Used for runtime capability checking and adapter selection.
        """
        ...

    def is_available(self) -> bool:
        """
        Check if this adapter is ready for use.

        Should verify that the underlying provider is available
        and properly configured.
        """
        ...

    async def execute_action(
        self,
        action_api_name: str,
        params: Dict[str, Any],
        context: ActionContext,
        *,
        validate_only: bool = False,
        return_edits: bool = True
    ) -> ActionResult:
        """
        Execute an ODA action through this LLM adapter.

        This is the primary method for action execution. All adapters
        must implement this method to provide consistent behavior.

        Args:
            action_api_name: The api_name of the action to execute
            params: Action parameters
            context: Execution context (actor, timestamp, metadata)
            validate_only: If True, only validate without execution
            return_edits: If True, include EditOperations in result

        Returns:
            ActionResult with success/error status and affected objects

        Raises:
            ActionExecutionError: If action execution fails
            ActionValidationError: If action validation fails
        """
        ...

    def validate_action(
        self,
        action_api_name: str,
        params: Dict[str, Any],
        context: ActionContext
    ) -> List[str]:
        """
        Validate action parameters without executing.

        Args:
            action_api_name: The api_name of the action to validate
            params: Action parameters to validate
            context: Execution context

        Returns:
            List of validation error messages (empty if valid)
        """
        ...


# =============================================================================
# BASE ADAPTER IMPLEMENTATION
# =============================================================================

class BaseActionAdapter(ABC):
    """
    Abstract base class for LLM Action Adapters.

    Provides common functionality for all adapter implementations:
    - Action registry lookup
    - Validation orchestration
    - Logging and error handling

    Subclasses must implement:
    - _execute_action_impl(): Provider-specific execution logic
    """

    def __init__(self, provider: LLMProvider):
        """
        Initialize the adapter with an LLM provider.

        Args:
            provider: The underlying LLM provider instance
        """
        self._provider = provider
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def name(self) -> str:
        """Human-readable name derived from provider."""
        return f"{self._provider.name}-adapter"

    @property
    def provider_type(self) -> LLMProviderType:
        """Delegate to underlying provider."""
        return self._provider.provider_type()

    @property
    def provider(self) -> LLMProvider:
        """Access the underlying provider."""
        return self._provider

    def is_available(self) -> bool:
        """Delegate availability check to provider."""
        return self._provider.is_available()

    @abstractmethod
    def get_capabilities(self) -> AdapterCapabilities:
        """Subclasses must declare their capabilities."""
        ...

    @abstractmethod
    async def _execute_action_impl(
        self,
        action: ActionType,
        params: Dict[str, Any],
        context: ActionContext,
        validate_only: bool,
        return_edits: bool
    ) -> ActionResult:
        """
        Provider-specific action execution implementation.

        This method is called after action lookup and validation.
        Subclasses implement their specific execution logic here.
        """
        ...

    def _get_action_class(self, action_api_name: str) -> Type[ActionType]:
        """
        Lookup action class from registry.

        Raises:
            ActionExecutionError: If action not found
        """
        action_class = action_registry.get(action_api_name)
        if action_class is None:
            raise ActionExecutionError(
                message=f"Action '{action_api_name}' not found in registry",
                action_api_name=action_api_name,
                provider_type=self.provider_type,
                details={"available_actions": action_registry.list_actions()}
            )
        return action_class

    def validate_action(
        self,
        action_api_name: str,
        params: Dict[str, Any],
        context: ActionContext
    ) -> List[str]:
        """
        Validate action parameters using the action's submission criteria.
        """
        try:
            action_class = self._get_action_class(action_api_name)
            action = action_class()
            return action.validate(params, context)
        except ActionExecutionError:
            return [f"Action '{action_api_name}' not found in registry"]
        except Exception as e:
            return [f"Validation error: {str(e)}"]

    async def execute_action(
        self,
        action_api_name: str,
        params: Dict[str, Any],
        context: ActionContext,
        *,
        validate_only: bool = False,
        return_edits: bool = True
    ) -> ActionResult:
        """
        Execute an ODA action with full validation and error handling.

        This method orchestrates:
        1. Action lookup from registry
        2. Pre-execution logging
        3. Delegation to provider-specific implementation
        4. Post-execution logging and error handling
        """
        self._logger.info(
            f"Executing action: {action_api_name} "
            f"[actor={context.actor_id}, validate_only={validate_only}]"
        )

        try:
            # 1. Lookup action class
            action_class = self._get_action_class(action_api_name)
            action = action_class()

            # 2. Pre-validation (fail fast)
            validation_errors = action.validate(params, context)
            if validation_errors:
                self._logger.warning(
                    f"Action validation failed: {action_api_name} - {validation_errors}"
                )
                raise ActionValidationError(
                    message="Submission criteria failed",
                    action_api_name=action_api_name,
                    validation_errors=validation_errors
                )

            # 3. Delegate to provider-specific implementation
            result = await self._execute_action_impl(
                action=action,
                params=params,
                context=context,
                validate_only=validate_only,
                return_edits=return_edits
            )

            # 4. Log result
            if result.success:
                self._logger.info(
                    f"Action succeeded: {action_api_name} "
                    f"[created={len(result.created_ids)}, modified={len(result.modified_ids)}]"
                )
            else:
                self._logger.warning(
                    f"Action failed: {action_api_name} - {result.error}"
                )

            return result

        except ActionValidationError:
            # Re-raise validation errors
            raise
        except ActionExecutionError:
            # Re-raise execution errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            self._logger.exception(f"Unexpected error executing {action_api_name}")
            raise ActionExecutionError(
                message=str(e),
                action_api_name=action_api_name,
                provider_type=self.provider_type,
                details={"exception_type": type(e).__name__}
            ) from e
