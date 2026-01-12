from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

if TYPE_CHECKING:
    from . import ActionResult, ActionContext, ActionType

logger = logging.getLogger(__name__)

# =============================================================================
# SIDE EFFECT TYPES (Foundry-Aligned)
# =============================================================================

class SideEffectType(str, Enum):
    """
    Official side effect types aligned with Palantir Foundry.

    Reference: https://www.palantir.com/docs/foundry/action-types/overview
    """
    NOTIFICATION = "notification"       # Alert stakeholders
    WEBHOOK = "webhook"                 # External system integration
    LINK_CREATION = "link_creation"     # Automatic relationship establishment
    LOG = "log"                         # Audit logging
    EVENT_BUS = "event_bus"             # Internal event publication
    EMAIL = "email"                     # Email notification
    CACHE_INVALIDATION = "cache_invalidation"  # Cache update


class SideEffectPriority(str, Enum):
    """Execution priority for side effects."""
    HIGH = "high"       # Execute first (e.g., critical notifications)
    NORMAL = "normal"   # Default priority
    LOW = "low"         # Execute last (e.g., analytics)


# =============================================================================
# SIDE EFFECT MODEL
# =============================================================================

@dataclass
class SideEffectDeclaration:
    """
    Declarative side effect definition for ActionTypes.

    Foundry Pattern: Side effects are declared at ActionType definition time,
    not at execution time. This enables:
    - Governance validation before execution
    - Documentation generation
    - Impact analysis

    Example:
        @declares_side_effect(
            effect_type=SideEffectType.NOTIFICATION,
            description="Notify task assignee",
            target_roles=["assignee"],
            priority=SideEffectPriority.HIGH
        )
        class AssignTaskAction(ActionType):
            ...
    """
    effect_type: SideEffectType
    description: str
    target_roles: List[str] = field(default_factory=list)  # Who receives the effect
    priority: SideEffectPriority = SideEffectPriority.NORMAL
    is_optional: bool = False  # Can user opt-out?
    failure_policy: str = "continue"  # "continue" | "abort" | "retry"
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type.value,
            "description": self.description,
            "target_roles": self.target_roles,
            "priority": self.priority.value,
            "is_optional": self.is_optional,
            "failure_policy": self.failure_policy,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }


# =============================================================================
# SIDE EFFECT REGISTRY
# =============================================================================

class SideEffectRegistry:
    """
    Registry for declared side effects per ActionType.

    Foundry Pattern: All side effects must be declared upfront.
    This enables governance validation and impact analysis.
    """

    _declarations: ClassVar[Dict[str, List[SideEffectDeclaration]]] = {}

    @classmethod
    def register(cls, action_api_name: str, declaration: SideEffectDeclaration) -> None:
        """Register a side effect declaration for an action."""
        if action_api_name not in cls._declarations:
            cls._declarations[action_api_name] = []
        cls._declarations[action_api_name].append(declaration)
        logger.debug(
            f"Registered side effect {declaration.effect_type.value} "
            f"for action {action_api_name}"
        )

    @classmethod
    def get_declarations(cls, action_api_name: str) -> List[SideEffectDeclaration]:
        """Get all declared side effects for an action."""
        return cls._declarations.get(action_api_name, [])

    @classmethod
    def get_all_actions_with_effects(cls) -> Dict[str, List[SideEffectDeclaration]]:
        """Get all actions that have declared side effects."""
        return dict(cls._declarations)

    @classmethod
    def has_effect_type(cls, action_api_name: str, effect_type: SideEffectType) -> bool:
        """Check if an action declares a specific side effect type."""
        declarations = cls.get_declarations(action_api_name)
        return any(d.effect_type == effect_type for d in declarations)

    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (for testing)."""
        cls._declarations.clear()


# =============================================================================
# @declares_side_effect DECORATOR
# =============================================================================

T = TypeVar("T", bound="ActionType")


def declares_side_effect(
    effect_type: SideEffectType,
    description: str,
    target_roles: List[str] = None,
    priority: SideEffectPriority = SideEffectPriority.NORMAL,
    is_optional: bool = False,
    failure_policy: str = "continue",
    max_retries: int = 3,
    **metadata
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to declare side effects for an ActionType.

    Foundry Pattern: Side effects must be declared upfront for:
    - Governance validation
    - Documentation generation
    - Impact analysis

    Usage:
        @declares_side_effect(
            effect_type=SideEffectType.NOTIFICATION,
            description="Notify assigned agent when task is created",
            target_roles=["assignee"],
            priority=SideEffectPriority.HIGH
        )
        @declares_side_effect(
            effect_type=SideEffectType.WEBHOOK,
            description="Send task data to external CRM",
            priority=SideEffectPriority.LOW
        )
        @register_action
        class CreateTaskAction(ActionType[Task]):
            api_name = "task.create"
            ...

    Args:
        effect_type: Type of side effect (notification, webhook, etc.)
        description: Human-readable description
        target_roles: Who receives the effect (e.g., ["assignee", "manager"])
        priority: Execution priority (high/normal/low)
        is_optional: Can user opt-out of this effect?
        failure_policy: How to handle failures ("continue" | "abort" | "retry")
        max_retries: Max retry attempts if failure_policy is "retry"
        **metadata: Additional metadata for the side effect

    Returns:
        Decorated ActionType class with side effect declaration registered
    """
    def decorator(action_class: Type[T]) -> Type[T]:
        # Ensure api_name is set
        if not hasattr(action_class, "api_name"):
            raise ValueError(
                f"ActionType {action_class.__name__} must have api_name "
                f"before using @declares_side_effect"
            )

        declaration = SideEffectDeclaration(
            effect_type=effect_type,
            description=description,
            target_roles=target_roles or [],
            priority=priority,
            is_optional=is_optional,
            failure_policy=failure_policy,
            max_retries=max_retries,
            metadata=metadata,
        )

        SideEffectRegistry.register(action_class.api_name, declaration)

        # Store declarations on the class for introspection
        if not hasattr(action_class, "_declared_side_effects"):
            action_class._declared_side_effects = []
        action_class._declared_side_effects.append(declaration)

        return action_class

    return decorator


# =============================================================================
# SIDE EFFECTS PROTOCOL
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
    """Sends notification to a Slack channel via webhook."""

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
        if not self.webhook_url:
            logger.warning(
                f"SlackNotification: No webhook_url configured for channel {self.channel}"
            )
            return

        import httpx
        import time

        # Determine color based on success/failure
        color = "#36a64f" if action_result.success else "#dc3545"
        status_text = "SUCCESS" if action_result.success else "FAILED"

        # Build Slack attachment payload
        payload = {
            "channel": self.channel,
            "attachments": [
                {
                    "color": color,
                    "title": f"Action: {action_result.action_type}",
                    "fields": [
                        {
                            "title": "Status",
                            "value": status_text,
                            "short": True
                        },
                        {
                            "title": "Actor",
                            "value": context.actor_id,
                            "short": True
                        },
                        {
                            "title": "Correlation ID",
                            "value": context.correlation_id or "N/A",
                            "short": True
                        }
                    ],
                    "footer": "ODA Ontology",
                    "ts": int(time.time())
                }
            ]
        }

        # Add error message if failed
        if not action_result.success and action_result.error:
            payload["attachments"][0]["fields"].append({
                "title": "Error",
                "value": str(action_result.error)[:500],  # Truncate long errors
                "short": False
            })

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                response.raise_for_status()
                logger.debug(
                    f"Slack notification sent to {self.channel} for {action_result.action_type}"
                )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Slack webhook HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Slack webhook request failed: {self.webhook_url} - {e}")
        except Exception as e:
            logger.error(f"Slack notification failed unexpectedly: {e}")


class EmailNotification:
    """Sends email notification via SMTP using aiosmtplib."""

    def __init__(
        self,
        to_email: str,
        subject_template: str,
        smtp_host: str = "localhost",
        smtp_port: int = 587
    ):
        self.to_email = to_email
        self.subject_template = subject_template
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    @property
    def name(self) -> str:
        return f"EmailNotification({self.to_email})"

    async def execute(
        self,
        action_result: "ActionResult",
        context: "ActionContext"
    ) -> None:
        import aiosmtplib
        from email.message import EmailMessage

        # Format subject using template
        subject = self.subject_template.format(
            action_type=action_result.action_type,
            status="SUCCESS" if action_result.success else "FAILED",
            actor_id=context.actor_id
        )

        # Build email body
        status_text = "SUCCESS" if action_result.success else "FAILED"
        body_lines = [
            f"Action Notification",
            f"==================",
            f"",
            f"Action Type: {action_result.action_type}",
            f"Status: {status_text}",
            f"Actor: {context.actor_id}",
            f"Correlation ID: {context.correlation_id or 'N/A'}",
        ]

        if not action_result.success and action_result.error:
            body_lines.extend([
                f"",
                f"Error Details:",
                f"--------------",
                f"{str(action_result.error)[:1000]}"  # Truncate long errors
            ])

        body_lines.extend([
            f"",
            f"---",
            f"Sent by ODA Ontology"
        ])

        # Create email message
        message = EmailMessage()
        message["From"] = f"oda-ontology@{self.smtp_host}"
        message["To"] = self.to_email
        message["Subject"] = subject
        message.set_content("\n".join(body_lines))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                timeout=30.0
            )
            logger.debug(
                f"Email notification sent to {self.to_email} for {action_result.action_type}"
            )
        except aiosmtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed: {self.smtp_host}:{self.smtp_port} - {e}")
        except aiosmtplib.SMTPResponseException as e:
            logger.error(f"SMTP response error: {e.code} - {e.message}")
        except Exception as e:
            logger.error(f"Email notification failed unexpectedly: {e}")


class EventBusSideEffect:
    """
    Publishes an event to the global EventBus upon action success.
    """
    
    def __init__(self, event_type_template: str = "{action_type}.completed"):
        """
        Args:
            event_type_template: Template string for event type.
                                 Available placeholders: action_type, actor_id
        """
        self.event_type_template = event_type_template

    @property
    def name(self) -> str:
        return f"EventBusSideEffect({self.event_type_template})"
    
    async def execute(
        self,
        action_result: "ActionResult",
        context: "ActionContext"
    ) -> None:
        from lib.oda.infrastructure.event_bus import EventBus
        
        if not action_result.success:
            return

        event_type = self.event_type_template.format(
            action_type=action_result.action_type,
            actor_id=context.actor_id
        )
        
        # Publish
        await EventBus.get_instance().publish(
            event_type=event_type,
            payload=action_result.to_dict(),
            actor_id=context.actor_id,
            metadata={
                "correlation_id": context.correlation_id,
                "action_metadata": context.metadata
            }
        )


# =============================================================================
# SIDE EFFECT EXECUTION RESULT
# =============================================================================

class SideEffectStatus(str, Enum):
    """Status of side effect execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class SideEffectExecutionResult:
    """
    Result of a single side effect execution.

    Used for audit logging and debugging.
    """
    effect_name: str
    effect_type: SideEffectType
    status: SideEffectStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_name": self.effect_name,
            "effect_type": self.effect_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


# =============================================================================
# SIDE EFFECT AUDIT LOGGER
# =============================================================================

class SideEffectAuditLogger:
    """
    Audit logger for side effect executions.

    Foundry Pattern: All side effects must be auditable for:
    - Debugging failed notifications
    - Compliance tracking
    - Performance analysis
    """

    _instance: ClassVar[Optional["SideEffectAuditLogger"]] = None
    _log_history: ClassVar[List[Dict[str, Any]]] = []
    _max_history_size: ClassVar[int] = 1000

    @classmethod
    def get_instance(cls) -> "SideEffectAuditLogger":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log_execution(
        self,
        action_api_name: str,
        action_id: str,
        result: SideEffectExecutionResult,
        context_actor_id: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Log a side effect execution.

        Args:
            action_api_name: The API name of the action that triggered the effect
            action_id: Unique identifier for the action execution
            result: The execution result
            context_actor_id: Who triggered the action
            correlation_id: Optional trace ID
        """
        from datetime import timezone

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_api_name": action_api_name,
            "action_id": action_id,
            "actor_id": context_actor_id,
            "correlation_id": correlation_id,
            **result.to_dict(),
        }

        # Log to standard logger
        log_message = (
            f"[SideEffect] {result.effect_type.value}::{result.effect_name} "
            f"for {action_api_name} - {result.status.value}"
        )
        if result.status == SideEffectStatus.FAILED:
            logger.error(f"{log_message} - Error: {result.error}")
        elif result.status == SideEffectStatus.SUCCESS:
            logger.info(f"{log_message} ({result.duration_ms}ms)")
        else:
            logger.debug(log_message)

        # Store in memory for recent history
        self._log_history.append(log_entry)
        if len(self._log_history) > self._max_history_size:
            self._log_history.pop(0)

    def get_recent_logs(
        self,
        limit: int = 100,
        action_api_name: Optional[str] = None,
        effect_type: Optional[SideEffectType] = None,
        status: Optional[SideEffectStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent side effect logs with optional filtering.

        Args:
            limit: Maximum number of logs to return
            action_api_name: Filter by action type
            effect_type: Filter by side effect type
            status: Filter by execution status

        Returns:
            List of log entries (most recent first)
        """
        logs = list(reversed(self._log_history))

        if action_api_name:
            logs = [l for l in logs if l.get("action_api_name") == action_api_name]
        if effect_type:
            logs = [l for l in logs if l.get("effect_type") == effect_type.value]
        if status:
            logs = [l for l in logs if l.get("status") == status.value]

        return logs[:limit]

    def get_failure_summary(self) -> Dict[str, Any]:
        """
        Get summary of failed side effects.

        Returns:
            Dict with failure counts by effect type and action
        """
        failures = [
            l for l in self._log_history
            if l.get("status") == SideEffectStatus.FAILED.value
        ]

        by_effect_type: Dict[str, int] = {}
        by_action: Dict[str, int] = {}

        for f in failures:
            effect_type = f.get("effect_type", "unknown")
            action = f.get("action_api_name", "unknown")

            by_effect_type[effect_type] = by_effect_type.get(effect_type, 0) + 1
            by_action[action] = by_action.get(action, 0) + 1

        return {
            "total_failures": len(failures),
            "by_effect_type": by_effect_type,
            "by_action": by_action,
        }

    def clear_history(self) -> None:
        """Clear the log history (for testing)."""
        self._log_history.clear()


# =============================================================================
# SIDE EFFECT EXECUTOR
# =============================================================================

class SideEffectExecutor:
    """
    Executes side effects with retry logic and audit logging.

    Foundry Pattern: Side effects are executed in priority order
    with configurable retry and failure handling.
    """

    def __init__(
        self,
        audit_logger: Optional[SideEffectAuditLogger] = None,
    ):
        self.audit_logger = audit_logger or SideEffectAuditLogger.get_instance()

    async def execute_all(
        self,
        effects: List[SideEffect],
        action_result: "ActionResult",
        context: "ActionContext",
        declarations: Optional[List[SideEffectDeclaration]] = None,
    ) -> List[SideEffectExecutionResult]:
        """
        Execute all side effects in priority order.

        Args:
            effects: List of SideEffect instances to execute
            action_result: Result from the action execution
            context: Action execution context
            declarations: Optional declarations for audit enrichment

        Returns:
            List of execution results
        """
        from datetime import timezone
        import asyncio

        results: List[SideEffectExecutionResult] = []

        for i, effect in enumerate(effects):
            # Get declaration if available
            decl = declarations[i] if declarations and i < len(declarations) else None
            effect_type = decl.effect_type if decl else SideEffectType.LOG
            max_retries = decl.max_retries if decl else 3
            failure_policy = decl.failure_policy if decl else "continue"

            started_at = datetime.now(timezone.utc)
            result = SideEffectExecutionResult(
                effect_name=effect.name,
                effect_type=effect_type,
                status=SideEffectStatus.EXECUTING,
                started_at=started_at,
            )

            retry_count = 0
            last_error: Optional[str] = None

            while retry_count <= max_retries:
                try:
                    await effect.execute(action_result, context)
                    completed_at = datetime.now(timezone.utc)
                    result.status = SideEffectStatus.SUCCESS
                    result.completed_at = completed_at
                    result.duration_ms = int(
                        (completed_at - started_at).total_seconds() * 1000
                    )
                    break
                except Exception as e:
                    last_error = str(e)
                    retry_count += 1
                    if retry_count <= max_retries:
                        result.status = SideEffectStatus.RETRYING
                        await asyncio.sleep(0.5 * (2 ** (retry_count - 1)))
                    else:
                        result.status = SideEffectStatus.FAILED
                        result.error = last_error
                        result.completed_at = datetime.now(timezone.utc)
                        result.duration_ms = int(
                            (result.completed_at - started_at).total_seconds() * 1000
                        )

            result.retry_count = retry_count

            # Log execution
            self.audit_logger.log_execution(
                action_api_name=action_result.action_type,
                action_id=context.correlation_id or "unknown",
                result=result,
                context_actor_id=context.actor_id,
                correlation_id=context.correlation_id,
            )

            results.append(result)

            # Handle failure policy
            if result.status == SideEffectStatus.FAILED and failure_policy == "abort":
                logger.warning(
                    f"Side effect {effect.name} failed with abort policy, "
                    f"stopping remaining effects"
                )
                break

        return results


# =============================================================================
# GOVERNANCE VALIDATION FOR SIDE EFFECTS
# =============================================================================

class SideEffectGovernanceValidator:
    """
    Validates side effect declarations against governance rules.

    Foundry Pattern: Some side effects may require governance approval
    or have restrictions based on the action type.
    """

    # Side effect types that require explicit governance approval
    RESTRICTED_EFFECTS: ClassVar[List[SideEffectType]] = [
        SideEffectType.EMAIL,
        SideEffectType.WEBHOOK,
    ]

    @classmethod
    def validate_declarations(
        cls,
        action_api_name: str,
        declarations: List[SideEffectDeclaration],
        is_hazardous_action: bool = False,
    ) -> tuple[bool, List[str]]:
        """
        Validate side effect declarations for governance compliance.

        Args:
            action_api_name: The action being validated
            declarations: List of side effect declarations
            is_hazardous_action: Whether the action is marked hazardous

        Returns:
            Tuple of (is_valid, list_of_warnings_or_errors)
        """
        warnings: List[str] = []
        is_valid = True

        for decl in declarations:
            # Check if restricted effect type without proper policy
            if decl.effect_type in cls.RESTRICTED_EFFECTS:
                if decl.failure_policy == "abort":
                    warnings.append(
                        f"[{action_api_name}] Restricted effect type "
                        f"'{decl.effect_type.value}' should not use 'abort' failure policy"
                    )

            # Hazardous actions should have notification side effects
            if is_hazardous_action:
                has_notification = any(
                    d.effect_type == SideEffectType.NOTIFICATION
                    for d in declarations
                )
                if not has_notification:
                    warnings.append(
                        f"[{action_api_name}] Hazardous action should declare "
                        f"a NOTIFICATION side effect for audit purposes"
                    )

            # Non-optional external effects should have retry
            if (
                decl.effect_type in [SideEffectType.WEBHOOK, SideEffectType.EMAIL]
                and not decl.is_optional
                and decl.max_retries < 1
            ):
                warnings.append(
                    f"[{action_api_name}] Non-optional external effect "
                    f"'{decl.effect_type.value}' should have max_retries >= 1"
                )

        return is_valid, warnings

    @classmethod
    def get_required_effects_for_action_type(
        cls,
        action_api_name: str,
        is_hazardous: bool = False,
    ) -> List[SideEffectType]:
        """
        Get list of required side effect types for an action.

        Args:
            action_api_name: The action being checked
            is_hazardous: Whether the action is hazardous

        Returns:
            List of required side effect types
        """
        required: List[SideEffectType] = []

        # All actions should log
        required.append(SideEffectType.LOG)

        # Hazardous actions require notification
        if is_hazardous:
            required.append(SideEffectType.NOTIFICATION)

        return required
