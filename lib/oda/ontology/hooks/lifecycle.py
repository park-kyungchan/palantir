"""
Orion ODA v4.0 - Lifecycle Hooks Implementation
================================================

Implements async lifecycle hooks for OntologyObjects:
- pre_save: Runs before persisting object (can modify or abort)
- post_save: Runs after persisting object (for side effects)
- pre_delete: Runs before deletion (can abort)
- validation: Custom validation beyond Pydantic

Features:
- Async protocol for flexibility
- Priority-based execution ordering
- Object type filtering
- Hook chaining with abort capability
- Comprehensive error handling

Schema Version: 4.0.0
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
)

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class LifecycleHookType(str, Enum):
    """
    Types of lifecycle hooks.

    - PRE_SAVE: Runs before object is saved (can modify or abort)
    - POST_SAVE: Runs after object is saved (for side effects)
    - PRE_DELETE: Runs before deletion (can abort)
    - POST_DELETE: Runs after deletion (cleanup)
    - VALIDATION: Custom validation (can abort with validation errors)
    """

    PRE_SAVE = "pre_save"
    POST_SAVE = "post_save"
    PRE_DELETE = "pre_delete"
    POST_DELETE = "post_delete"
    VALIDATION = "validation"


class LifecycleHookPriority(IntEnum):
    """
    Hook execution priority.

    Lower values execute first.
    Use CRITICAL for security/validation that must run first.
    """

    CRITICAL = 0  # Security validation, schema checks
    HIGH = 10  # Pre-processing, normalization
    NORMAL = 50  # Default priority
    LOW = 90  # Post-processing
    DEFERRED = 100  # Cleanup, logging, analytics


# =============================================================================
# CONTEXT AND RESULT TYPES
# =============================================================================


@dataclass
class LifecycleContext:
    """
    Context passed to lifecycle hooks.

    Attributes:
        object_type: Name of the ObjectType being operated on
        object_id: ID of the object (if existing)
        operation: The lifecycle operation (save, delete)
        actor_id: ID of the user/agent performing the operation
        is_create: True if this is a new object
        is_update: True if this is an update
        original: Original object state (for updates)
        current: Current object state
        metadata: Additional context data
    """

    object_type: str
    object_id: Optional[str] = None
    operation: str = "save"
    actor_id: Optional[str] = None
    is_create: bool = False
    is_update: bool = False
    original: Optional[OntologyObject] = None
    current: Optional[OntologyObject] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def for_save(
        cls,
        obj: OntologyObject,
        original: Optional[OntologyObject] = None,
        actor_id: Optional[str] = None,
        **metadata: Any,
    ) -> LifecycleContext:
        """Create context for a save operation."""
        is_create = original is None
        return cls(
            object_type=obj.__class__.__name__,
            object_id=obj.id,
            operation="save",
            actor_id=actor_id,
            is_create=is_create,
            is_update=not is_create,
            original=original,
            current=obj,
            metadata=metadata,
        )

    @classmethod
    def for_delete(
        cls,
        obj: OntologyObject,
        actor_id: Optional[str] = None,
        **metadata: Any,
    ) -> LifecycleContext:
        """Create context for a delete operation."""
        return cls(
            object_type=obj.__class__.__name__,
            object_id=obj.id,
            operation="delete",
            actor_id=actor_id,
            is_create=False,
            is_update=False,
            original=obj,
            current=obj,
            metadata=metadata,
        )


@dataclass
class HookResult:
    """
    Result of a lifecycle hook execution.

    Attributes:
        success: Whether the hook executed successfully
        abort: Whether to abort the operation
        abort_reason: Reason for aborting (if abort=True)
        modified_object: Modified object (for pre_save hooks)
        validation_errors: List of validation errors (for validation hooks)
        duration_ms: Execution time in milliseconds
        metadata: Additional result data
    """

    success: bool = True
    abort: bool = False
    abort_reason: Optional[str] = None
    modified_object: Optional[OntologyObject] = None
    validation_errors: List[str] = field(default_factory=list)
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, modified_object: Optional[OntologyObject] = None, **metadata: Any) -> HookResult:
        """Create a successful result."""
        return cls(success=True, modified_object=modified_object, metadata=metadata)

    @classmethod
    def abort_operation(cls, reason: str) -> HookResult:
        """Create an abort result."""
        return cls(success=True, abort=True, abort_reason=reason)

    @classmethod
    def validation_failed(cls, errors: List[str]) -> HookResult:
        """Create a validation failure result."""
        return cls(success=True, abort=True, validation_errors=errors)

    @classmethod
    def error(cls, message: str) -> HookResult:
        """Create an error result."""
        return cls(success=False, abort=True, abort_reason=message)


@dataclass
class HookChainResult:
    """
    Result of running a chain of hooks.

    Attributes:
        success: Whether all hooks executed successfully
        aborted: Whether any hook aborted the operation
        abort_reason: Combined abort reasons
        final_object: Final object after all modifications
        validation_errors: All validation errors
        hook_results: Individual hook results
        total_duration_ms: Total execution time
    """

    success: bool = True
    aborted: bool = False
    abort_reason: Optional[str] = None
    final_object: Optional[OntologyObject] = None
    validation_errors: List[str] = field(default_factory=list)
    hook_results: List[HookResult] = field(default_factory=list)
    total_duration_ms: int = 0

    @property
    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        return len(self.validation_errors) > 0


# =============================================================================
# HOOK PROTOCOL AND BASE CLASS
# =============================================================================


@runtime_checkable
class LifecycleHookProtocol(Protocol):
    """
    Protocol for lifecycle hooks.

    Hooks can be either classes implementing this protocol or
    async callables matching the signature.
    """

    async def __call__(
        self,
        obj: OntologyObject,
        context: LifecycleContext,
    ) -> HookResult:
        """Execute the hook."""
        ...


T = TypeVar("T", bound=OntologyObject)


class LifecycleHook(ABC, Generic[T]):
    """
    Base class for lifecycle hooks.

    Extend this class to create custom hooks with type safety.

    Example:
        ```python
        class AuditLogHook(LifecycleHook[Task]):
            hook_type = LifecycleHookType.POST_SAVE
            object_types = {"Task"}
            priority = LifecycleHookPriority.LOW

            async def execute(self, obj: Task, context: LifecycleContext) -> HookResult:
                logger.info(f"Task saved: {obj.id}")
                return HookResult.ok()
        ```
    """

    # Class attributes to override
    hook_type: LifecycleHookType = LifecycleHookType.PRE_SAVE
    object_types: Set[str] = set()  # Empty = all types
    priority: LifecycleHookPriority = LifecycleHookPriority.NORMAL
    enabled: bool = True
    name: Optional[str] = None
    description: Optional[str] = None

    @abstractmethod
    async def execute(
        self,
        obj: T,
        context: LifecycleContext,
    ) -> HookResult:
        """
        Execute the hook logic.

        Args:
            obj: The object being operated on
            context: Lifecycle context with operation details

        Returns:
            HookResult indicating success/failure and any modifications
        """
        ...

    async def __call__(
        self,
        obj: OntologyObject,
        context: LifecycleContext,
    ) -> HookResult:
        """Make the hook callable."""
        return await self.execute(obj, context)  # type: ignore

    def should_run(self, object_type: str) -> bool:
        """Check if this hook should run for the given object type."""
        if not self.enabled:
            return False
        if not self.object_types:
            return True
        return object_type in self.object_types

    @property
    def hook_name(self) -> str:
        """Get the hook name."""
        return self.name or self.__class__.__name__


# =============================================================================
# HOOK DEFINITION MODEL
# =============================================================================


class LifecycleHookDefinition(BaseModel):
    """
    Pydantic model for persisted hook definitions.

    Used for dynamic hook registration and serialization.
    """

    id: str = Field(..., description="Unique hook identifier")
    name: str = Field(..., min_length=1, max_length=128)
    hook_type: LifecycleHookType
    object_types: List[str] = Field(default_factory=list)
    priority: LifecycleHookPriority = LifecycleHookPriority.NORMAL
    enabled: bool = True
    description: Optional[str] = None
    handler_path: Optional[str] = Field(
        default=None,
        description="Python import path for handler (e.g., 'module.path:handler_func')",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# HOOK REGISTRY
# =============================================================================


class LifecycleHookRegistry:
    """
    Registry for lifecycle hooks.

    Features:
    - Hook registration by type
    - Priority-based ordering
    - Object type filtering
    - Hook chain execution

    Usage:
        ```python
        registry = get_lifecycle_registry()

        # Register a hook
        registry.register(AuditLogHook())

        # Run hooks
        result = await registry.run_hooks(
            LifecycleHookType.PRE_SAVE,
            obj=task,
            context=context,
        )
        ```
    """

    _instance: Optional[LifecycleHookRegistry] = None

    def __init__(self) -> None:
        # hook_type -> list of (priority, hook)
        self._hooks: Dict[LifecycleHookType, List[tuple[int, Union[LifecycleHook, Callable]]]] = {
            hook_type: [] for hook_type in LifecycleHookType
        }
        self._hook_definitions: Dict[str, LifecycleHookDefinition] = {}

    @classmethod
    def get_instance(cls) -> LifecycleHookRegistry:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("LifecycleHookRegistry singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    def register(
        self,
        hook: Union[LifecycleHook, Callable],
        hook_type: Optional[LifecycleHookType] = None,
        priority: Optional[LifecycleHookPriority] = None,
        object_types: Optional[Set[str]] = None,
    ) -> None:
        """
        Register a lifecycle hook.

        Args:
            hook: Hook instance or async callable
            hook_type: Override hook type (for callables)
            priority: Override priority
            object_types: Override object type filter
        """
        # Get hook metadata
        if isinstance(hook, LifecycleHook):
            h_type = hook_type or hook.hook_type
            h_priority = priority or hook.priority
            hook_name = hook.hook_name
        else:
            if hook_type is None:
                raise ValueError("hook_type required for callable hooks")
            h_type = hook_type
            h_priority = priority or LifecycleHookPriority.NORMAL
            hook_name = getattr(hook, "__name__", str(hook))

        # Store with priority for sorting
        self._hooks[h_type].append((h_priority, hook))
        # Re-sort by priority
        self._hooks[h_type].sort(key=lambda x: x[0])

        logger.info(f"Registered lifecycle hook: {hook_name} (type={h_type.value}, priority={h_priority})")

    def unregister(
        self,
        hook: Union[LifecycleHook, Callable],
        hook_type: Optional[LifecycleHookType] = None,
    ) -> bool:
        """
        Unregister a hook.

        Args:
            hook: The hook to unregister
            hook_type: Hook type (required for callables)

        Returns:
            True if hook was found and removed
        """
        if isinstance(hook, LifecycleHook):
            h_type = hook_type or hook.hook_type
        else:
            if hook_type is None:
                raise ValueError("hook_type required for callable hooks")
            h_type = hook_type

        original_len = len(self._hooks[h_type])
        self._hooks[h_type] = [(p, h) for p, h in self._hooks[h_type] if h is not hook]

        return len(self._hooks[h_type]) < original_len

    def get_hooks(
        self,
        hook_type: LifecycleHookType,
        object_type: Optional[str] = None,
    ) -> List[Union[LifecycleHook, Callable]]:
        """
        Get all hooks for a type, optionally filtered by object type.

        Args:
            hook_type: Type of hooks to retrieve
            object_type: Filter by object type

        Returns:
            List of hooks, sorted by priority
        """
        hooks = []
        for _, hook in self._hooks[hook_type]:
            if object_type and isinstance(hook, LifecycleHook):
                if not hook.should_run(object_type):
                    continue
            hooks.append(hook)
        return hooks

    async def run_hooks(
        self,
        hook_type: LifecycleHookType,
        obj: OntologyObject,
        context: LifecycleContext,
    ) -> HookChainResult:
        """
        Run all hooks of a type in priority order.

        For PRE_SAVE hooks, the object may be modified.
        Any hook can abort the chain by returning abort=True.

        Args:
            hook_type: Type of hooks to run
            obj: Object being operated on
            context: Lifecycle context

        Returns:
            HookChainResult with combined results
        """
        import time

        start_time = time.time()
        chain_result = HookChainResult(final_object=obj)

        hooks = self.get_hooks(hook_type, context.object_type)

        current_obj = obj
        for hook in hooks:
            try:
                hook_start = time.time()

                # Update context with current object
                context.current = current_obj

                # Execute hook
                if asyncio.iscoroutinefunction(hook):
                    result = await hook(current_obj, context)
                elif isinstance(hook, LifecycleHook):
                    result = await hook(current_obj, context)
                else:
                    # Sync callable
                    result = hook(current_obj, context)
                    if asyncio.iscoroutine(result):
                        result = await result

                result.duration_ms = int((time.time() - hook_start) * 1000)
                chain_result.hook_results.append(result)

                # Handle abort
                if result.abort:
                    chain_result.aborted = True
                    chain_result.abort_reason = result.abort_reason
                    chain_result.validation_errors.extend(result.validation_errors)
                    break

                # Handle modification
                if result.modified_object is not None:
                    current_obj = result.modified_object

                # Collect validation errors
                chain_result.validation_errors.extend(result.validation_errors)

                if not result.success:
                    chain_result.success = False
                    break

            except Exception as e:
                logger.error(f"Hook execution failed: {e}", exc_info=True)
                error_result = HookResult.error(str(e))
                chain_result.hook_results.append(error_result)
                chain_result.success = False
                chain_result.aborted = True
                chain_result.abort_reason = f"Hook error: {e}"
                break

        chain_result.final_object = current_obj
        chain_result.total_duration_ms = int((time.time() - start_time) * 1000)

        return chain_result

    def list_hooks(self) -> Dict[LifecycleHookType, List[str]]:
        """List all registered hooks by type."""
        result = {}
        for hook_type, hooks in self._hooks.items():
            result[hook_type] = [
                getattr(h, "hook_name", getattr(h, "__name__", str(h)))
                for _, h in hooks
            ]
        return result


# =============================================================================
# DECORATOR AND CONVENIENCE FUNCTIONS
# =============================================================================


def lifecycle_hook(
    hook_type: LifecycleHookType,
    priority: LifecycleHookPriority = LifecycleHookPriority.NORMAL,
    object_types: Optional[Set[str]] = None,
    auto_register: bool = True,
) -> Callable:
    """
    Decorator to register a function as a lifecycle hook.

    Example:
        ```python
        @lifecycle_hook(LifecycleHookType.PRE_SAVE, priority=LifecycleHookPriority.HIGH)
        async def normalize_task_title(obj: Task, context: LifecycleContext) -> HookResult:
            obj.title = obj.title.strip()
            return HookResult.ok(modified_object=obj)
        ```
    """

    def decorator(func: Callable) -> Callable:
        # Store metadata on the function
        func._hook_type = hook_type  # type: ignore
        func._hook_priority = priority  # type: ignore
        func._hook_object_types = object_types or set()  # type: ignore

        if auto_register:
            registry = get_lifecycle_registry()
            registry.register(func, hook_type=hook_type, priority=priority)

        return func

    return decorator


def get_lifecycle_registry() -> LifecycleHookRegistry:
    """Get the global LifecycleHookRegistry instance."""
    return LifecycleHookRegistry.get_instance()


def register_lifecycle_hook(
    hook: Union[LifecycleHook, Callable],
    hook_type: Optional[LifecycleHookType] = None,
    priority: Optional[LifecycleHookPriority] = None,
) -> None:
    """Register a hook with the global registry."""
    get_lifecycle_registry().register(hook, hook_type=hook_type, priority=priority)


async def run_hooks(
    hook_type: LifecycleHookType,
    obj: OntologyObject,
    context: LifecycleContext,
) -> HookChainResult:
    """Run hooks using the global registry."""
    return await get_lifecycle_registry().run_hooks(hook_type, obj, context)


# =============================================================================
# BUILT-IN HOOKS
# =============================================================================


class TimestampUpdateHook(LifecycleHook):
    """
    Built-in hook to update timestamps on save.

    Automatically updates updated_at and version.
    """

    hook_type = LifecycleHookType.PRE_SAVE
    priority = LifecycleHookPriority.CRITICAL
    name = "timestamp_update"
    description = "Updates timestamps and version on save"

    async def execute(
        self,
        obj: OntologyObject,
        context: LifecycleContext,
    ) -> HookResult:
        if context.is_update:
            obj.touch(updated_by=context.actor_id)
        return HookResult.ok(modified_object=obj)


class ValidationHook(LifecycleHook):
    """
    Built-in hook for Pydantic validation.

    Runs model_validate to ensure object is valid.
    """

    hook_type = LifecycleHookType.VALIDATION
    priority = LifecycleHookPriority.CRITICAL
    name = "pydantic_validation"
    description = "Validates object with Pydantic"

    async def execute(
        self,
        obj: OntologyObject,
        context: LifecycleContext,
    ) -> HookResult:
        try:
            # Pydantic validation
            obj.__class__.model_validate(obj.model_dump())
            return HookResult.ok()
        except Exception as e:
            return HookResult.validation_failed([str(e)])


# Register built-in hooks when module loads
def _register_builtin_hooks() -> None:
    """Register built-in hooks."""
    registry = get_lifecycle_registry()
    registry.register(TimestampUpdateHook())
    registry.register(ValidationHook())


# Lazy registration - call explicitly if needed
# _register_builtin_hooks()
