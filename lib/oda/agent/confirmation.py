"""
Orion ODA v4.0 - Confirmation Workflow (Phase 7.3.3)
====================================================

Confirmation workflow for hazardous action execution:
- ConfirmationRequest model for tracking confirmation state
- Hazardous action confirmation before execution
- User approval integration with timeout handling
- Async callback support for UI integration

Flow:
    1. Agent requests hazardous action
    2. ConfirmationManager creates ConfirmationRequest
    3. Request is sent to approval handler (UI/CLI/API)
    4. User approves/rejects within timeout
    5. Action executed or denied based on response
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import ActionContext, ActionResult, GovernanceEngine, action_registry
from lib.oda.ontology.objects.proposal import Proposal, ProposalPriority, ProposalStatus
from lib.oda.ontology.ontology_types import utc_now

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ConfirmationStatus(str, Enum):
    """Status of a confirmation request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ConfirmationMode(str, Enum):
    """Mode of confirmation handling."""
    BLOCKING = "blocking"       # Wait synchronously for response
    ASYNC = "async"             # Fire-and-forget with callback
    PROPOSAL = "proposal"       # Create proposal for later review


class UrgencyLevel(str, Enum):
    """Urgency level for confirmation requests."""
    LOW = "low"           # Can wait indefinitely
    NORMAL = "normal"     # Standard timeout
    HIGH = "high"         # Expedited review
    CRITICAL = "critical" # Immediate attention required


# =============================================================================
# DATA MODELS
# =============================================================================

class ConfirmationRequest(BaseModel):
    """
    Represents a request for user confirmation.

    Created when an agent attempts a hazardous action that
    requires explicit user approval before execution.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: str = Field(..., description="Action API name requiring confirmation")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    rationale: str = Field(default="", description="Why this action is being requested")
    risks: List[str] = Field(default_factory=list, description="Identified risks")

    # Request metadata
    requester_id: str = Field(default="agent", description="ID of the requesting agent")
    session_id: str = Field(default="", description="Session context")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.NORMAL)

    # State tracking
    status: ConfirmationStatus = Field(default=ConfirmationStatus.PENDING)
    created_at: datetime = Field(default_factory=utc_now)
    responded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Response
    responder_id: Optional[str] = None
    response_comment: Optional[str] = None

    # Linked proposal (if using proposal mode)
    proposal_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def is_pending(self) -> bool:
        """Check if request is still pending."""
        return self.status == ConfirmationStatus.PENDING

    def is_expired(self) -> bool:
        """Check if request has expired."""
        if self.expires_at and utc_now() > self.expires_at:
            return True
        return self.status == ConfirmationStatus.EXPIRED

    def approve(self, responder_id: str, comment: str = "") -> None:
        """Mark request as approved."""
        self.status = ConfirmationStatus.APPROVED
        self.responder_id = responder_id
        self.response_comment = comment
        self.responded_at = utc_now()

    def reject(self, responder_id: str, reason: str = "") -> None:
        """Mark request as rejected."""
        self.status = ConfirmationStatus.REJECTED
        self.responder_id = responder_id
        self.response_comment = reason
        self.responded_at = utc_now()

    def timeout(self) -> None:
        """Mark request as timed out."""
        self.status = ConfirmationStatus.TIMEOUT
        self.responded_at = utc_now()

    def cancel(self, reason: str = "") -> None:
        """Cancel the request."""
        self.status = ConfirmationStatus.CANCELLED
        self.response_comment = reason
        self.responded_at = utc_now()

    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to user-friendly display format."""
        return {
            "id": self.id,
            "action": self.action_type,
            "params_preview": str(self.params)[:200],
            "rationale": self.rationale,
            "risks": self.risks,
            "urgency": self.urgency.value,
            "status": self.status.value,
            "requester": self.requester_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class ConfirmationResponse(BaseModel):
    """Response to a confirmation request."""
    request_id: str
    approved: bool
    responder_id: str
    comment: str = ""
    timestamp: datetime = Field(default_factory=utc_now)

    class Config:
        arbitrary_types_allowed = True


@dataclass
class ConfirmationConfig:
    """Configuration for the confirmation workflow."""
    default_timeout_seconds: float = 300.0  # 5 minutes
    mode: ConfirmationMode = ConfirmationMode.BLOCKING
    auto_reject_on_timeout: bool = True
    require_comment_on_reject: bool = False
    max_pending_requests: int = 100


# =============================================================================
# PROTOCOLS
# =============================================================================

class ConfirmationHandler(Protocol):
    """Protocol for confirmation UI/API handlers."""

    async def request_confirmation(
        self,
        request: ConfirmationRequest,
    ) -> ConfirmationResponse:
        """
        Request user confirmation and wait for response.

        Args:
            request: The confirmation request

        Returns:
            ConfirmationResponse with user's decision
        """
        ...

    async def notify_result(
        self,
        request: ConfirmationRequest,
        result: Optional[Dict[str, Any]],
    ) -> None:
        """
        Notify handler of action execution result.

        Called after approved action is executed.

        Args:
            request: The original confirmation request
            result: Action execution result (or None if not executed)
        """
        ...


# =============================================================================
# DEFAULT HANDLERS
# =============================================================================

class ConsoleConfirmationHandler:
    """
    Console-based confirmation handler for CLI usage.

    Prints confirmation request and waits for user input.
    Useful for testing and CLI-based agents.
    """

    async def request_confirmation(
        self,
        request: ConfirmationRequest,
    ) -> ConfirmationResponse:
        """Request confirmation via console input."""
        print("\n" + "=" * 60)
        print("CONFIRMATION REQUIRED")
        print("=" * 60)
        print(f"Action: {request.action_type}")
        print(f"Urgency: {request.urgency.value}")
        print(f"Rationale: {request.rationale}")
        if request.risks:
            print(f"Risks: {', '.join(request.risks)}")
        print(f"Parameters: {str(request.params)[:500]}")
        print("=" * 60)

        # In actual async context, this would use asyncio-friendly input
        # For now, return auto-reject for safety in production
        logger.warning("Console handler - auto-rejecting for safety")

        return ConfirmationResponse(
            request_id=request.id,
            approved=False,
            responder_id="console-auto",
            comment="Auto-rejected by console handler (interactive input not available)",
        )

    async def notify_result(
        self,
        request: ConfirmationRequest,
        result: Optional[Dict[str, Any]],
    ) -> None:
        """Notify console of result."""
        if result and result.get("success"):
            print(f"\n[OK] Action {request.action_type} executed successfully")
        elif result:
            print(f"\n[FAIL] Action {request.action_type} failed: {result.get('error')}")
        else:
            print(f"\n[SKIP] Action {request.action_type} was not executed")


class CallbackConfirmationHandler:
    """
    Callback-based confirmation handler.

    Uses provided async callbacks for request/response handling.
    Useful for integration with external UIs or APIs.
    """

    def __init__(
        self,
        on_request: Callable[[ConfirmationRequest], Any],
        on_response: Optional[Callable[[ConfirmationRequest, Dict[str, Any]], Any]] = None,
    ):
        """
        Initialize with callbacks.

        Args:
            on_request: Called when confirmation is needed
            on_response: Called when action completes (optional)
        """
        self._on_request = on_request
        self._on_response = on_response
        self._pending_responses: Dict[str, asyncio.Future] = {}

    async def request_confirmation(
        self,
        request: ConfirmationRequest,
    ) -> ConfirmationResponse:
        """Request confirmation via callback."""
        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_responses[request.id] = future

        # Call request handler
        if asyncio.iscoroutinefunction(self._on_request):
            await self._on_request(request)
        else:
            self._on_request(request)

        # Wait for response
        response = await future
        del self._pending_responses[request.id]

        return response

    async def notify_result(
        self,
        request: ConfirmationRequest,
        result: Optional[Dict[str, Any]],
    ) -> None:
        """Notify result via callback."""
        if self._on_response:
            if asyncio.iscoroutinefunction(self._on_response):
                await self._on_response(request, result)
            else:
                self._on_response(request, result)

    def submit_response(self, response: ConfirmationResponse) -> bool:
        """
        Submit a response to a pending confirmation.

        Called by external handler when user responds.

        Returns:
            True if response was accepted, False if request not found
        """
        future = self._pending_responses.get(response.request_id)
        if future and not future.done():
            future.set_result(response)
            return True
        return False


# =============================================================================
# CONFIRMATION MANAGER
# =============================================================================

class ConfirmationManager:
    """
    Manages the confirmation workflow for hazardous actions.

    Provides:
    - Request creation and tracking
    - Timeout handling
    - Integration with GovernanceEngine
    - Action execution after approval

    Usage:
        ```python
        manager = ConfirmationManager(
            handler=ConsoleConfirmationHandler(),
            config=ConfirmationConfig(default_timeout_seconds=60),
        )

        # Request confirmation
        result = await manager.confirm_and_execute(
            action_type="file.delete",
            params={"path": "/important/file"},
            rationale="Cleanup obsolete files",
            actor_id="agent-001",
        )

        if result["confirmed"]:
            print(f"Action executed: {result['action_result']}")
        else:
            print(f"Action denied: {result['reason']}")
        ```
    """

    def __init__(
        self,
        handler: Optional[ConfirmationHandler] = None,
        config: Optional[ConfirmationConfig] = None,
        governance: Optional[GovernanceEngine] = None,
    ):
        """
        Initialize the confirmation manager.

        Args:
            handler: Handler for confirmation UI/API
            config: Configuration options
            governance: GovernanceEngine for policy checks
        """
        self.handler = handler or ConsoleConfirmationHandler()
        self.config = config or ConfirmationConfig()
        self.governance = governance or GovernanceEngine(action_registry)

        self._pending_requests: Dict[str, ConfirmationRequest] = {}
        self._request_history: List[ConfirmationRequest] = []

    @property
    def pending_count(self) -> int:
        """Number of pending confirmation requests."""
        return len(self._pending_requests)

    async def confirm_and_execute(
        self,
        action_type: str,
        params: Dict[str, Any],
        rationale: str = "",
        risks: Optional[List[str]] = None,
        actor_id: str = "agent",
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Request confirmation and execute action if approved.

        This is the main entry point for confirmed action execution.

        Args:
            action_type: Action API name
            params: Action parameters
            rationale: Why this action is needed
            risks: Known risks of this action
            actor_id: ID of requesting agent
            urgency: Urgency level
            timeout_seconds: Custom timeout (overrides config)

        Returns:
            Dict with:
            - confirmed: bool - Whether action was confirmed
            - request: ConfirmationRequest - The request object
            - action_result: Optional action execution result
            - reason: Explanation if not confirmed
        """
        # Create request
        timeout = timeout_seconds or self.config.default_timeout_seconds
        request = ConfirmationRequest(
            action_type=action_type,
            params=params,
            rationale=rationale,
            risks=risks or [],
            requester_id=actor_id,
            urgency=urgency,
            expires_at=utc_now() + timedelta(seconds=timeout),
        )

        # Check if we're at max pending
        if len(self._pending_requests) >= self.config.max_pending_requests:
            request.status = ConfirmationStatus.REJECTED
            return {
                "confirmed": False,
                "request": request,
                "action_result": None,
                "reason": "Max pending requests exceeded",
            }

        # Track request
        self._pending_requests[request.id] = request

        try:
            # Request confirmation with timeout
            response = await asyncio.wait_for(
                self.handler.request_confirmation(request),
                timeout=timeout,
            )

            # Update request status
            if response.approved:
                request.approve(response.responder_id, response.comment)
            else:
                request.reject(response.responder_id, response.comment)

        except asyncio.TimeoutError:
            request.timeout()
            if self.config.auto_reject_on_timeout:
                return {
                    "confirmed": False,
                    "request": request,
                    "action_result": None,
                    "reason": f"Confirmation timed out after {timeout}s",
                }

        finally:
            # Remove from pending
            self._pending_requests.pop(request.id, None)
            self._request_history.append(request)

        # Execute if approved
        if request.status == ConfirmationStatus.APPROVED:
            action_result = await self._execute_action(action_type, params, actor_id)

            # Notify handler of result
            await self.handler.notify_result(request, action_result)

            return {
                "confirmed": True,
                "request": request,
                "action_result": action_result,
                "reason": None,
            }

        return {
            "confirmed": False,
            "request": request,
            "action_result": None,
            "reason": request.response_comment or f"Status: {request.status.value}",
        }

    async def _execute_action(
        self,
        action_type: str,
        params: Dict[str, Any],
        actor_id: str,
    ) -> Dict[str, Any]:
        """Execute the confirmed action."""
        action_cls = action_registry.get(action_type)
        if not action_cls:
            return {
                "success": False,
                "error": "ACTION_NOT_FOUND",
                "action_type": action_type,
            }

        try:
            action = action_cls()
            context = ActionContext(actor_id=actor_id)
            result: ActionResult = await action.execute(params, context)
            return result.to_dict()

        except Exception as e:
            logger.exception(f"Action execution failed: {action_type}")
            return {
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__,
            }

    async def create_proposal(
        self,
        action_type: str,
        params: Dict[str, Any],
        rationale: str = "",
        actor_id: str = "agent",
        priority: ProposalPriority = ProposalPriority.MEDIUM,
    ) -> ConfirmationRequest:
        """
        Create a proposal for later review (proposal mode).

        Instead of blocking for confirmation, creates a Proposal
        object that can be reviewed asynchronously.

        Args:
            action_type: Action API name
            params: Action parameters
            rationale: Why this action is needed
            actor_id: ID of requesting agent
            priority: Proposal priority

        Returns:
            ConfirmationRequest linked to created Proposal
        """
        request = ConfirmationRequest(
            action_type=action_type,
            params=params,
            rationale=rationale,
            requester_id=actor_id,
        )

        # Create linked proposal
        proposal = Proposal(
            action_type=action_type,
            payload=params,
            priority=priority,
            created_by=actor_id,
        )
        proposal.submit(submitter_id=actor_id)

        request.proposal_id = proposal.id
        self._request_history.append(request)

        return request

    def get_pending_requests(self) -> List[ConfirmationRequest]:
        """Get all pending confirmation requests."""
        return list(self._pending_requests.values())

    def get_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """Get a specific request by ID."""
        return self._pending_requests.get(request_id)

    def cancel_request(self, request_id: str, reason: str = "") -> bool:
        """
        Cancel a pending confirmation request.

        Returns:
            True if request was cancelled, False if not found
        """
        request = self._pending_requests.get(request_id)
        if request and request.is_pending():
            request.cancel(reason)
            self._pending_requests.pop(request_id, None)
            self._request_history.append(request)
            return True
        return False

    def get_history(self, limit: int = 100) -> List[ConfirmationRequest]:
        """Get recent confirmation request history."""
        return self._request_history[-limit:]

    def clear_expired(self) -> int:
        """
        Clear expired requests from pending.

        Returns:
            Number of requests cleared
        """
        expired = [
            req_id for req_id, req in self._pending_requests.items()
            if req.is_expired()
        ]

        for req_id in expired:
            request = self._pending_requests.pop(req_id)
            request.status = ConfirmationStatus.EXPIRED
            self._request_history.append(request)

        return len(expired)


__all__ = [
    "ConfirmationStatus",
    "ConfirmationMode",
    "UrgencyLevel",
    "ConfirmationRequest",
    "ConfirmationResponse",
    "ConfirmationConfig",
    "ConfirmationHandler",
    "ConsoleConfirmationHandler",
    "CallbackConfirmationHandler",
    "ConfirmationManager",
]
