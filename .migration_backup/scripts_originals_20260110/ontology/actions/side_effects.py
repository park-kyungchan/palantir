from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Protocol, runtime_checkable

if TYPE_CHECKING:
    from . import ActionResult, ActionContext

logger = logging.getLogger(__name__)

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
