# Refactoring Task A3: `scripts/ontology/objects/proposal.py`

> **Priority**: 🔴 High
> **Estimated Time**: 1 hour
> **Dependencies**: `ontology_types.py` (A5 must be applied first)

---

## Instruction

Replace the existing `proposal.py` with the following implementation.
This refactoring adds:
1. `ProposalStatus` Enum with all valid states
2. `VALID_TRANSITIONS` map enforcing state machine rules
3. `InvalidTransitionError` custom exception
4. `approve()`, `reject()`, `execute()` methods with validation
5. Full audit trail support

---

## Complete Implementation

```python
"""
Orion ODA v3.0 - Proposal Governance Object
Palantir AIP/Foundry Compliant Governance Workflow

This module implements the Proposal object for human-in-the-loop governance.
High-stakes actions require explicit approval before execution.

State Machine:
    DRAFT → PENDING → APPROVED → EXECUTED
                   ↘ REJECTED (terminal)

All state transitions are validated and audited.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import Field, field_validator, model_validator

# Import from refactored ontology_types (A5)
from scripts.ontology.ontology_types import OntologyObject, utc_now


# =============================================================================
# EXCEPTIONS
# =============================================================================

class ProposalError(Exception):
    """Base exception for Proposal-related errors."""
    pass


class InvalidTransitionError(ProposalError):
    """Raised when an invalid state transition is attempted."""
    
    def __init__(self, current_status: str, target_status: str, allowed: List[str]):
        self.current_status = current_status
        self.target_status = target_status
        self.allowed = allowed
        super().__init__(
            f"Invalid transition: {current_status} → {target_status}. "
            f"Allowed transitions: {allowed}"
        )


class ProposalAlreadyProcessedError(ProposalError):
    """Raised when trying to modify an already-processed proposal."""
    pass


# =============================================================================
# ENUMS
# =============================================================================

class ProposalStatus(str, Enum):
    """
    Proposal lifecycle states.
    
    - DRAFT: Initial state, can be edited
    - PENDING: Submitted for review, awaiting approval
    - APPROVED: Approved by reviewer, ready for execution
    - REJECTED: Rejected by reviewer (terminal state)
    - EXECUTED: Successfully executed (terminal state)
    - CANCELLED: Cancelled by creator before review (terminal state)
    """
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class ProposalPriority(str, Enum):
    """Priority levels for proposal review ordering."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# STATE MACHINE
# =============================================================================

# Valid state transitions map
# Key: Current state, Value: Set of allowed target states
VALID_TRANSITIONS: Dict[ProposalStatus, Set[ProposalStatus]] = {
    ProposalStatus.DRAFT: {
        ProposalStatus.PENDING,
        ProposalStatus.CANCELLED,
    },
    ProposalStatus.PENDING: {
        ProposalStatus.APPROVED,
        ProposalStatus.REJECTED,
        ProposalStatus.CANCELLED,
    },
    ProposalStatus.APPROVED: {
        ProposalStatus.EXECUTED,
        ProposalStatus.CANCELLED,  # Can cancel before execution
    },
    ProposalStatus.REJECTED: set(),  # Terminal state
    ProposalStatus.EXECUTED: set(),  # Terminal state
    ProposalStatus.CANCELLED: set(),  # Terminal state
}

# Terminal states (no further transitions allowed)
TERMINAL_STATES: Set[ProposalStatus] = {
    ProposalStatus.REJECTED,
    ProposalStatus.EXECUTED,
    ProposalStatus.CANCELLED,
}


# =============================================================================
# PROPOSAL OBJECT
# =============================================================================

class Proposal(OntologyObject):
    """
    Represents a staged Action awaiting Human Review.
    
    A Proposal encapsulates:
    - The action to be performed (action_type + payload)
    - The creator (created_by from OntologyObject)
    - The reviewer (reviewed_by)
    - Full audit trail (timestamps, comments)
    
    Usage:
        ```python
        # Create a proposal
        proposal = Proposal(
            action_type="deploy_to_production",
            payload={"service": "checkout", "version": "2.1.0"},
            created_by="agent-001",
            priority=ProposalPriority.HIGH
        )
        
        # Submit for review
        proposal.submit()
        
        # Approve (by human reviewer)
        proposal.approve(reviewer_id="admin-001", comment="LGTM")
        
        # Execute
        proposal.execute()
        ```
    
    Attributes:
        action_type: The ActionType API name to execute
        payload: Parameters for the action
        status: Current lifecycle state
        priority: Review priority
        reviewed_by: ID of the reviewer
        reviewed_at: Timestamp of review decision
        review_comment: Reviewer's comment
        executed_at: Timestamp of execution
        execution_result: Result of execution (success/error details)
    """
    
    # Action Definition
    action_type: str = Field(
        ...,
        description="The ActionType API name to execute (e.g., 'deploy_to_production')",
        min_length=1,
        max_length=255
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the action"
    )
    
    # Lifecycle State
    status: ProposalStatus = Field(
        default=ProposalStatus.DRAFT,
        description="Current lifecycle state"
    )
    priority: ProposalPriority = Field(
        default=ProposalPriority.MEDIUM,
        description="Review priority"
    )
    
    # Review Fields
    reviewed_by: Optional[str] = Field(
        default=None,
        description="ID of the reviewer who approved/rejected"
    )
    reviewed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of review decision"
    )
    review_comment: Optional[str] = Field(
        default=None,
        description="Reviewer's comment or reason",
        max_length=2000
    )
    
    # Execution Fields
    executed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of execution"
    )
    execution_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Result of execution (success/error details)"
    )
    
    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )
    
    # ==========================================================================
    # VALIDATORS
    # ==========================================================================
    
    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Ensure action_type follows snake_case convention."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                f"action_type must be snake_case alphanumeric: {v}"
            )
        return v.lower()
    
    # ==========================================================================
    # STATE MACHINE METHODS
    # ==========================================================================
    
    def _validate_transition(self, target_status: ProposalStatus) -> None:
        """
        Validate that the transition to target_status is allowed.
        
        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if target_status not in allowed:
            raise InvalidTransitionError(
                current_status=self.status.value,
                target_status=target_status.value,
                allowed=[s.value for s in allowed]
            )
    
    def _transition_to(
        self,
        target_status: ProposalStatus,
        actor_id: Optional[str] = None
    ) -> None:
        """
        Execute a state transition with validation and audit.
        
        Args:
            target_status: The target state
            actor_id: ID of the user/agent performing the transition
        """
        self._validate_transition(target_status)
        self.status = target_status
        self.touch(updated_by=actor_id)
    
    @property
    def is_terminal(self) -> bool:
        """Check if the proposal is in a terminal state."""
        return self.status in TERMINAL_STATES
    
    @property
    def is_pending_review(self) -> bool:
        """Check if the proposal is awaiting review."""
        return self.status == ProposalStatus.PENDING
    
    @property
    def can_execute(self) -> bool:
        """Check if the proposal can be executed."""
        return self.status == ProposalStatus.APPROVED
    
    # ==========================================================================
    # LIFECYCLE METHODS
    # ==========================================================================
    
    def submit(self, submitter_id: Optional[str] = None) -> "Proposal":
        """
        Submit the proposal for review.
        
        Transitions: DRAFT → PENDING
        
        Args:
            submitter_id: ID of the submitter (defaults to created_by)
        
        Returns:
            self for method chaining
        
        Raises:
            InvalidTransitionError: If not in DRAFT state
        """
        self._transition_to(
            ProposalStatus.PENDING,
            actor_id=submitter_id or self.created_by
        )
        return self
    
    def approve(
        self,
        reviewer_id: str,
        comment: Optional[str] = None
    ) -> "Proposal":
        """
        Approve the proposal.
        
        Transitions: PENDING → APPROVED
        
        Args:
            reviewer_id: ID of the reviewer (required)
            comment: Optional approval comment
        
        Returns:
            self for method chaining
        
        Raises:
            InvalidTransitionError: If not in PENDING state
            ValueError: If reviewer_id is not provided
        """
        if not reviewer_id:
            raise ValueError("reviewer_id is required for approval")
        
        self._transition_to(ProposalStatus.APPROVED, actor_id=reviewer_id)
        self.reviewed_by = reviewer_id
        self.reviewed_at = utc_now()
        self.review_comment = comment
        return self
    
    def reject(
        self,
        reviewer_id: str,
        reason: str
    ) -> "Proposal":
        """
        Reject the proposal.
        
        Transitions: PENDING → REJECTED (terminal)
        
        Args:
            reviewer_id: ID of the reviewer (required)
            reason: Rejection reason (required)
        
        Returns:
            self for method chaining
        
        Raises:
            InvalidTransitionError: If not in PENDING state
            ValueError: If reviewer_id or reason is not provided
        """
        if not reviewer_id:
            raise ValueError("reviewer_id is required for rejection")
        if not reason:
            raise ValueError("reason is required for rejection")
        
        self._transition_to(ProposalStatus.REJECTED, actor_id=reviewer_id)
        self.reviewed_by = reviewer_id
        self.reviewed_at = utc_now()
        self.review_comment = reason
        return self
    
    def execute(
        self,
        executor_id: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> "Proposal":
        """
        Mark the proposal as executed.
        
        Transitions: APPROVED → EXECUTED (terminal)
        
        Note: This method only marks the status. Actual action execution
        should be handled by the ActionService.
        
        Args:
            executor_id: ID of the executor (defaults to created_by)
            result: Execution result details
        
        Returns:
            self for method chaining
        
        Raises:
            InvalidTransitionError: If not in APPROVED state
        """
        self._transition_to(
            ProposalStatus.EXECUTED,
            actor_id=executor_id or self.created_by
        )
        self.executed_at = utc_now()
        self.execution_result = result
        return self
    
    def cancel(
        self,
        canceller_id: str,
        reason: Optional[str] = None
    ) -> "Proposal":
        """
        Cancel the proposal.
        
        Transitions: DRAFT/PENDING/APPROVED → CANCELLED (terminal)
        
        Args:
            canceller_id: ID of the person cancelling
            reason: Optional cancellation reason
        
        Returns:
            self for method chaining
        
        Raises:
            InvalidTransitionError: If in terminal state
        """
        if not canceller_id:
            raise ValueError("canceller_id is required for cancellation")
        
        self._transition_to(ProposalStatus.CANCELLED, actor_id=canceller_id)
        self.review_comment = f"[CANCELLED] {reason}" if reason else "[CANCELLED]"
        return self
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def to_audit_log(self) -> Dict[str, Any]:
        """
        Generate an audit log entry for this proposal.
        
        Returns:
            Dictionary suitable for logging/storage
        """
        return {
            "proposal_id": self.id,
            "action_type": self.action_type,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_comment": self.review_comment,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "version": self.version,
        }
    
    def __repr__(self) -> str:
        return (
            f"Proposal(id={self.id[:8]}..., "
            f"action={self.action_type}, "
            f"status={self.status.value}, "
            f"priority={self.priority.value})"
        )
```

---

## Verification Checklist

After applying this refactoring, verify:

- [ ] `ProposalStatus.PENDING.value` returns `"pending"`
- [ ] `submit()` transitions DRAFT → PENDING
- [ ] `approve()` requires `reviewer_id`
- [ ] `reject()` requires both `reviewer_id` and `reason`
- [ ] Invalid transitions raise `InvalidTransitionError`
- [ ] Terminal states (REJECTED, EXECUTED, CANCELLED) block further transitions

---

## Test Command

```bash
python -c "
from scripts.ontology.objects.proposal import *

# Test State Machine
p = Proposal(action_type='deploy_service', created_by='agent-001')
assert p.status == ProposalStatus.DRAFT

# DRAFT → PENDING
p.submit()
assert p.status == ProposalStatus.PENDING

# PENDING → APPROVED
p.approve(reviewer_id='admin-001', comment='Looks good')
assert p.status == ProposalStatus.APPROVED
assert p.reviewed_by == 'admin-001'

# APPROVED → EXECUTED
p.execute(result={'success': True})
assert p.status == ProposalStatus.EXECUTED
assert p.is_terminal == True

# Verify invalid transition is blocked
p2 = Proposal(action_type='test', created_by='x')
try:
    p2.approve(reviewer_id='y')  # Can't approve from DRAFT
    assert False, 'Should have raised InvalidTransitionError'
except InvalidTransitionError as e:
    assert 'draft' in str(e).lower()

print('✅ proposal.py verification passed')
"
```
