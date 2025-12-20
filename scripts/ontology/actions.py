"""
Orion ODA v3.0 - Semantic Action System
Palantir AIP/Foundry Compliant Action Definitions

This module implements the Action layer of the Ontology-Driven Architecture.
Actions are the ONLY way to mutate the Ontology, ensuring:
- All changes are validated (SubmissionCriteria)
- All changes are audited (EditOperations)
- Side effects are decoupled (post-commit execution)

Design Principles:
1. Actions are declarative (class-based, not instance-based)
2. Validation before mutation (fail-fast)
3. Side effects after commit (eventual consistency)
4. Full audit trail (who, what, when)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
)

from pydantic import BaseModel, Field

from scripts.ontology.ontology_types import OntologyObject, utc_now

logger = logging.getLogger(__name__)


# =============================================================================
# EDIT OPERATIONS
# =============================================================================

class EditType(str, Enum):
    """Types of edit operations on the Ontology."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    LINK = "link"
    UNLINK = "unlink"


@dataclass
class EditOperation:
    """
    Represents a single edit operation on the Ontology.
    
    Used for:
    - Audit logging
    - Transaction rollback
    - Change data capture
    """
    edit_type: EditType
    object_type: str
    object_id: str
    changes: Dict[str, Any] = field(default_factory=dict)
    # Using default_factory for timestamp to ensure it's generated at instantiation
    timestamp: datetime = field(default_factory=utc_now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "edit_type": self.edit_type.value,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "changes": self.changes,
            "timestamp": self.timestamp.isoformat(),
        }



# =============================================================================
# SUBMISSION CRITERIA
# =============================================================================

class ValidationError(Exception):
    """Raised when SubmissionCriteria validation fails."""
    
    def __init__(self, criterion: str, message: str, details: Dict[str, Any] = None):
        self.criterion = criterion
        self.message = message
        self.details = details or {}
        super().__init__(f"[{criterion}] {message}")


@runtime_checkable
class SubmissionCriterion(Protocol):
    """
    Protocol for SubmissionCriteria validators.
    
    Implement this protocol to create custom validation rules.
    Each criterion is evaluated before action execution.
    """
    
    @property
    def name(self) -> str:
        """Human-readable name of this criterion."""
        ...
    
    def validate(self, params: Dict[str, Any], context: "ActionContext") -> bool:
        """
        Validate the action parameters.
        
        Args:
            params: Action parameters
            context: Execution context (user, timestamp, etc.)
        
        Returns:
            True if validation passes
        
        Raises:
            ValidationError: If validation fails
        """
        ...


class RequiredField(SubmissionCriterion):
    """Validates that a required field is present and non-empty."""
    
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    @property
    def name(self) -> str:
        return f"RequiredField({self.field_name})"
    
    def validate(self, params: Dict[str, Any], context: "ActionContext") -> bool:
        value = params.get(self.field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(
                criterion=self.name,
                message=f"Field '{self.field_name}' is required",
                details={"field": self.field_name, "value": value}
            )
        return True


class AllowedValues(SubmissionCriterion):
    """Validates that a field value is in an allowed set."""
    
    def __init__(self, field_name: str, allowed: List[Any]):
        self.field_name = field_name
        self.allowed = allowed
    
    @property
    def name(self) -> str:
        return f"AllowedValues({self.field_name})"
    
    def validate(self, params: Dict[str, Any], context: "ActionContext") -> bool:
        value = params.get(self.field_name)
        if value is not None and value not in self.allowed:
            raise ValidationError(
                criterion=self.name,
                message=f"Value '{value}' not in allowed values: {self.allowed}",
                details={"field": self.field_name, "value": value, "allowed": self.allowed}
            )
        return True


class MaxLength(SubmissionCriterion):
    """Validates that a string field doesn't exceed max length."""
    
    def __init__(self, field_name: str, max_length: int):
        self.field_name = field_name
        self.max_length = max_length
    
    @property
    def name(self) -> str:
        return f"MaxLength({self.field_name}, {self.max_length})"
    
    def validate(self, params: Dict[str, Any], context: "ActionContext") -> bool:
        value = params.get(self.field_name, "")
        if isinstance(value, str) and len(value) > self.max_length:
            raise ValidationError(
                criterion=self.name,
                message=f"Field '{self.field_name}' exceeds max length {self.max_length}",
                details={"field": self.field_name, "length": len(value), "max": self.max_length}
            )
        return True


class CustomValidator(SubmissionCriterion):
    """Wraps a custom validation function."""
    
    def __init__(
        self,
        name: str,
        validator_fn: Callable[[Dict[str, Any], "ActionContext"], bool],
        error_message: str = "Custom validation failed"
    ):
        self._name = name
        self.validator_fn = validator_fn
        self.error_message = error_message
    
    @property
    def name(self) -> str:
        return self._name
    
    def validate(self, params: Dict[str, Any], context: "ActionContext") -> bool:
        if not self.validator_fn(params, context):
            raise ValidationError(
                criterion=self.name,
                message=self.error_message,
                details={"params": params}
            )
        return True


# =============================================================================
# SIDE EFFECTS
# =============================================================================

@runtime_checkable
class SideEffect(Protocol):
    """
    Protocol for post-commit side effects.
    
    Side effects are executed AFTER the Ontology commit succeeds.
    They should be idempotent and handle failures gracefully.
    
    Examples:
    - Send Slack notification
    - Trigger webhook
    - Update external cache
    - Emit analytics event
    """
    
    @property
    def name(self) -> str:
        """Human-readable name of this side effect."""
        ...
    
    async def execute(
        self,
        action_result: "ActionResult",
        context: "ActionContext"
    ) -> None:
        """
        Execute the side effect.
        
        Args:
            action_result: Result of the action execution
            context: Execution context
        
        Note: Exceptions should be logged but not re-raised
        to avoid breaking other side effects.
        """
        ...


class LogSideEffect:
    """Logs action execution to the standard logger."""
    
    def __init__(self, log_level: int = logging.INFO):
        self.log_level = log_level
    
    @property
    def name(self) -> str:
        return "LogSideEffect"
    
    async def execute(
        self,
        action_result: "ActionResult",
        context: "ActionContext"
    ) -> None:
        logger.log(
            self.log_level,
            f"Action executed: {action_result.action_type} "
            f"by {context.actor_id} - "
            f"{'SUCCESS' if action_result.success else 'FAILED'}"
        )


class WebhookSideEffect:
    """Sends action result to a webhook URL."""
    
    def __init__(self, url: str, headers: Dict[str, str] = None):
        self.url = url
        self.headers = headers or {}
    
    @property
    def name(self) -> str:
        return f"WebhookSideEffect({self.url})"
    
    async def execute(
        self,
        action_result: "ActionResult",
        context: "ActionContext"
    ) -> None:
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.url,
                    json=action_result.to_dict(),
                    headers=self.headers,
                    timeout=10.0
                )
        except Exception as e:
            logger.error(f"Webhook failed: {self.url} - {e}")


class SlackNotification:
    """Sends notification to a Slack channel."""
    
    def __init__(self, channel: str, webhook_url: str = None):
        self.channel = channel
        self.webhook_url = webhook_url  # From config if not provided
    
    @property
    def name(self) -> str:
        return f"SlackNotification({self.channel})"
    
    async def execute(
        self,
        action_result: "ActionResult",
        context: "ActionContext"
    ) -> None:
        # Implementation depends on Slack integration
        logger.info(
            f"[Slack:{self.channel}] Action {action_result.action_type} "
            f"completed by {context.actor_id}"
        )


# =============================================================================
# ACTION CONTEXT & RESULT
# =============================================================================

@dataclass
class ActionContext:
    """
    Execution context for an action.
    
    Contains information about WHO is executing the action,
    WHEN it's being executed, and any relevant metadata.
    """
    actor_id: str  # User or Agent ID
    timestamp: datetime = field(default_factory=utc_now)
    correlation_id: Optional[str] = None  # For distributed tracing
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def system(cls) -> "ActionContext":
        """Create a system-level context (for automated actions)."""
        return cls(actor_id="system", metadata={"automated": True})


@dataclass
class ActionResult:
    """
    Result of an action execution.
    
    Contains success/failure status, created/modified objects,
    and any error information.
    """
    action_type: str
    success: bool
    edits: List[EditOperation] = field(default_factory=list)
    created_ids: List[str] = field(default_factory=list)
    modified_ids: List[str] = field(default_factory=list)
    deleted_ids: List[str] = field(default_factory=list)
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=utc_now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "success": self.success,
            "edits": [e.to_dict() for e in self.edits],
            "created_ids": self.created_ids,
            "modified_ids": self.modified_ids,
            "deleted_ids": self.deleted_ids,
            "error": self.error,
            "error_details": self.error_details,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# BASE ACTION TYPE
# =============================================================================

T = TypeVar("T", bound=OntologyObject)


class ActionType(ABC, Generic[T]):
    """
    Base class for all ActionTypes.
    
    To define a new action, subclass ActionType and implement:
    1. Class attributes: api_name, object_type, submission_criteria, side_effects
    2. apply_edits() method: the actual mutation logic
    
    Example:
        ```python
        class CreateTaskAction(ActionType[Task]):
            api_name = "create_task"
            object_type = Task
            
            submission_criteria = [
                RequiredField("title"),
                AllowedValues("priority", ["low", "medium", "high"]),
                MaxLength("title", 255),
            ]
            
            side_effects = [
                LogSideEffect(),
                SlackNotification(channel="#tasks"),
            ]
            
            async def apply_edits(
                self,
                params: Dict[str, Any],
                context: ActionContext
            ) -> Tuple[T, List[EditOperation]]:
                task = Task(
                    title=params["title"],
                    priority=params.get("priority", "medium"),
                    created_by=context.actor_id,
                )
                edit = EditOperation(
                    edit_type=EditType.CREATE,
                    object_type="Task",
                    object_id=task.id,
                    changes=params,
                )
                return task, [edit]
        ```
    """
    
    # Class attributes to be overridden by subclasses
    api_name: ClassVar[str]
    object_type: ClassVar[Type[T]]
    submission_criteria: ClassVar[List[SubmissionCriterion]] = []
    side_effects: ClassVar[List[SideEffect]] = []
    requires_proposal: ClassVar[bool] = False  # True for hazardous actions
    
    def __init__(self):
        """Initialize the action. Override for custom initialization."""
        pass
    
    def validate(self, params: Dict[str, Any], context: ActionContext) -> List[str]:
        """
        Run all submission criteria validators.
        
        Args:
            params: Action parameters
            context: Execution context
        
        Returns:
            List of validation error messages (empty if all pass)
        """
        errors = []
        for criterion in self.submission_criteria:
            try:
                criterion.validate(params, context)
            except ValidationError as e:
                errors.append(str(e))
        return errors
    
    @abstractmethod
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[T], List[EditOperation]]:
        """
        Apply the action's edits to the Ontology.
        
        This is where the actual mutation logic lives.
        
        Args:
            params: Action parameters
            context: Execution context
        
        Returns:
            Tuple of (created/modified object or None, list of edit operations)
        """
        ...
    
    async def execute(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """
        Execute the action with full validation and side effects.
        
        Execution flow:
        1. Validate submission criteria
        2. Apply edits (transactional)
        3. Execute side effects (post-commit)
        
        Args:
            params: Action parameters
            context: Execution context
        
        Returns:
            ActionResult with success/failure status
        """
        # 1. Validation
        errors = self.validate(params, context)
        if errors:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error="Submission criteria failed",
                error_details={"validation_errors": errors},
            )
        
        # 2. Apply Edits
        try:
            obj, edits = await self.apply_edits(params, context)
            
            result = ActionResult(
                action_type=self.api_name,
                success=True,
                edits=edits,
                created_ids=[obj.id] if obj and any(
                    e.edit_type == EditType.CREATE for e in edits
                ) else [],
                modified_ids=[obj.id] if obj and any(
                    e.edit_type == EditType.MODIFY for e in edits
                ) else [],
            )
        except Exception as e:
            logger.exception(f"Action {self.api_name} failed")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )
        
        # 3. Side Effects (fire-and-forget, errors logged but not raised)
        for effect in self.side_effects:
            try:
                await effect.execute(result, context)
            except Exception as e:
                logger.error(f"Side effect {effect.name} failed: {e}")
        
        return result
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(api_name='{self.api_name}')"


# =============================================================================
# ACTION REGISTRY
# =============================================================================

# =============================================================================
# ACTION REGISTRY & GOVERNANCE
# =============================================================================

@dataclass
class ActionMetadata:
    """Metadata for governance and execution policy."""
    requires_proposal: bool = False
    is_dangerous: bool = False
    description: str = ""

class ActionRegistry:
    """
    Registry for ActionType discovery and lookup with Metadata.
    
    Stores not just the class, but also its governance metadata.
    """
    
    def __init__(self):
        # Mapping: api_name -> (ActionClass, Metadata)
        self._actions: Dict[str, tuple[Type[ActionType], ActionMetadata]] = {}
    
    def register(self, action_class: Type[ActionType], **metadata_overrides) -> None:
        """Register an ActionType class with extracted or overridden metadata."""
        if not hasattr(action_class, "api_name"):
            raise ValueError(f"{action_class.__name__} missing api_name")
        
        api_name = action_class.api_name
        
        # Extract metadata from class attributes (Source of Truth)
        # Priorities: 1. Overrides (Decorator param) -> 2. Class Attribute -> 3. Default False
        requires_proposal = metadata_overrides.get(
            "requires_proposal", 
            getattr(action_class, "requires_proposal", False)
        )
        is_dangerous = metadata_overrides.get("is_dangerous", False) # Default for now if not on class
        
        metadata = ActionMetadata(
            requires_proposal=requires_proposal,
            is_dangerous=is_dangerous,
            description=action_class.__doc__ or ""
        )

        if api_name in self._actions:
            logger.warning(f"Overwriting action: {api_name}")
        
        self._actions[api_name] = (action_class, metadata)
        logger.debug(f"Registered action: {api_name} [Proposal:{requires_proposal}]")
    
    def get(self, api_name: str) -> Optional[Type[ActionType]]:
        """Get an ActionType class by api_name."""
        entry = self._actions.get(api_name)
        return entry[0] if entry else None

    def get_metadata(self, api_name: str) -> Optional[ActionMetadata]:
        """Get governance metadata for an action."""
        entry = self._actions.get(api_name)
        return entry[1] if entry else None
    
    def list_actions(self) -> List[str]:
        """List all registered action api_names."""
        return list(self._actions.keys())


# Global registry instance
action_registry = ActionRegistry()


def register_action(cls: Type[ActionType] = None, *, requires_proposal: bool = None):
    """
    Decorator to register an ActionType with the global registry.
    
    Can be used as:
    1. Bare decorator: @register_action
    2. With args: @register_action(requires_proposal=True)
    """
    def _register(action_cls):
        overrides = {}
        if requires_proposal is not None:
            overrides["requires_proposal"] = requires_proposal
            
        action_registry.register(action_cls, **overrides)
        return action_cls

    if cls is None:
        return _register
    return _register(cls)


class GovernanceEngine:
    """
    Enforces policies based on ActionMetadata.
    
    Centralizes the logic for "Should this run immediately or wait for approval?".
    """
    def __init__(self, registry: ActionRegistry):
        self.registry = registry
    
    def check_execution_policy(self, action_name: str) -> str:
        """
        Determines execution policy.
        Returns:
            "DENY": Action unknown
            "REQUIRE_PROPOSAL": Needs HITL review
            "ALLOW_IMMEDIATE": Can run now
        """
        meta = self.registry.get_metadata(action_name)
        if not meta:
            return "DENY"
        
        if meta.requires_proposal:
            return "REQUIRE_PROPOSAL"
        
        return "ALLOW_IMMEDIATE"

