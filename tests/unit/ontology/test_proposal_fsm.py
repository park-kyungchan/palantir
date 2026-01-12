"""
Unit tests for Proposal State Machine (FSM) transitions.

Run: pytest tests/unit/ontology/test_proposal_fsm.py -v

This module tests:
1. Valid state transitions through the proposal lifecycle
2. Invalid transitions that should raise errors
3. Terminal state behavior
4. Version increment on transitions
5. Required parameters for approve/reject actions
"""

from __future__ import annotations

import pytest

from lib.oda.ontology.objects.proposal import (
    Proposal,
    ProposalStatus,
    ProposalPriority,
    InvalidTransitionError,
    VALID_TRANSITIONS,
    TERMINAL_STATES,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def draft_proposal() -> Proposal:
    """Create a proposal in DRAFT state."""
    return Proposal(
        action_type="deploy_to_production",
        payload={"service": "checkout", "version": "2.1.0"},
        created_by="agent-001",
        priority=ProposalPriority.HIGH,
    )


@pytest.fixture
def pending_proposal(draft_proposal: Proposal) -> Proposal:
    """Create a proposal in PENDING state."""
    draft_proposal.submit()
    return draft_proposal


@pytest.fixture
def approved_proposal(pending_proposal: Proposal) -> Proposal:
    """Create a proposal in APPROVED state."""
    pending_proposal.approve(reviewer_id="admin-001", comment="LGTM")
    return pending_proposal


@pytest.fixture
def rejected_proposal() -> Proposal:
    """Create a proposal in REJECTED state."""
    proposal = Proposal(
        action_type="risky_action",
        payload={"danger": "high"},
        created_by="agent-001",
        priority=ProposalPriority.HIGH,
    )
    proposal.submit()
    proposal.reject(reviewer_id="admin-001", reason="Not safe for production")
    return proposal


@pytest.fixture
def executed_proposal(approved_proposal: Proposal) -> Proposal:
    """Create a proposal in EXECUTED state."""
    approved_proposal.execute(executor_id="system-001", result={"status": "success"})
    return approved_proposal


@pytest.fixture
def cancelled_proposal(draft_proposal: Proposal) -> Proposal:
    """Create a proposal in CANCELLED state."""
    draft_proposal.cancel(canceller_id="user-001", reason="Changed my mind")
    return draft_proposal


# =============================================================================
# TEST CLASS: PROPOSAL FSM
# =============================================================================

class TestProposalFSM:
    """Test Proposal State Machine transitions."""

    # =========================================================================
    # TEST: VALID TRANSITIONS
    # =========================================================================

    @pytest.mark.parametrize("start_state,action,expected,extra_kwargs", [
        (
            ProposalStatus.DRAFT,
            "submit",
            ProposalStatus.PENDING,
            {},
        ),
        (
            ProposalStatus.PENDING,
            "approve",
            ProposalStatus.APPROVED,
            {"reviewer_id": "admin-001"},
        ),
        (
            ProposalStatus.PENDING,
            "reject",
            ProposalStatus.REJECTED,
            {"reviewer_id": "admin-001", "reason": "Not approved"},
        ),
        (
            ProposalStatus.APPROVED,
            "execute",
            ProposalStatus.EXECUTED,
            {},
        ),
        (
            ProposalStatus.DRAFT,
            "cancel",
            ProposalStatus.CANCELLED,
            {"canceller_id": "user-001"},
        ),
        (
            ProposalStatus.PENDING,
            "cancel",
            ProposalStatus.CANCELLED,
            {"canceller_id": "user-001"},
        ),
        (
            ProposalStatus.APPROVED,
            "cancel",
            ProposalStatus.CANCELLED,
            {"canceller_id": "user-001"},
        ),
    ])
    def test_valid_transitions(
        self,
        start_state: ProposalStatus,
        action: str,
        expected: ProposalStatus,
        extra_kwargs: dict,
    ) -> None:
        """Test all valid state transitions through the FSM."""
        # Setup: Create proposal and transition to start_state
        proposal = Proposal(
            action_type="test_action",
            payload={"key": "value"},
            created_by="agent-001",
        )

        # Move to the starting state if not DRAFT
        if start_state == ProposalStatus.PENDING:
            proposal.submit()
        elif start_state == ProposalStatus.APPROVED:
            proposal.submit()
            proposal.approve(reviewer_id="admin-001")

        # Verify we're in the expected start state
        assert proposal.status == start_state, (
            f"Setup failed: expected {start_state}, got {proposal.status}"
        )

        # Execute the transition
        method = getattr(proposal, action)
        method(**extra_kwargs)

        # Assert the transition succeeded
        assert proposal.status == expected, (
            f"Transition {start_state} -> {action}() should result in {expected}, "
            f"but got {proposal.status}"
        )


def test_proposal_action_type_accepts_dotted_api_names() -> None:
    proposal = Proposal(
        action_type="learning.update_kb",
        payload={"kb_id": "01", "section": "Practice Exercise", "content": "x"},
        created_by="agent-001",
    )
    assert proposal.action_type == "learning.update_kb"

    # =========================================================================
    # TEST: INVALID TRANSITIONS
    # =========================================================================

    @pytest.mark.parametrize("initial_state,action,extra_kwargs,error_message", [
        (
            ProposalStatus.REJECTED,
            "approve",
            {"reviewer_id": "admin-001"},
            "Cannot approve a rejected proposal",
        ),
        (
            ProposalStatus.EXECUTED,
            "reject",
            {"reviewer_id": "admin-001", "reason": "Too late"},
            "Cannot reject an executed proposal",
        ),
        (
            ProposalStatus.DRAFT,
            "execute",
            {},
            "Cannot execute a draft proposal",
        ),
        (
            ProposalStatus.CANCELLED,
            "submit",
            {},
            "Cannot submit a cancelled proposal",
        ),
        (
            ProposalStatus.REJECTED,
            "execute",
            {},
            "Cannot execute a rejected proposal",
        ),
        (
            ProposalStatus.EXECUTED,
            "approve",
            {"reviewer_id": "admin-001"},
            "Cannot approve an executed proposal",
        ),
        (
            ProposalStatus.DRAFT,
            "approve",
            {"reviewer_id": "admin-001"},
            "Cannot approve a draft proposal (must submit first)",
        ),
        (
            ProposalStatus.APPROVED,
            "approve",
            {"reviewer_id": "admin-002"},
            "Cannot approve an already approved proposal",
        ),
    ])
    def test_invalid_transitions_raise_error(
        self,
        initial_state: ProposalStatus,
        action: str,
        extra_kwargs: dict,
        error_message: str,
    ) -> None:
        """Test that invalid state transitions raise InvalidTransitionError."""
        # Setup: Create proposal and move to initial state
        proposal = Proposal(
            action_type="test_action",
            payload={"key": "value"},
            created_by="agent-001",
        )

        # Transition to the initial state
        if initial_state == ProposalStatus.PENDING:
            proposal.submit()
        elif initial_state == ProposalStatus.APPROVED:
            proposal.submit()
            proposal.approve(reviewer_id="admin-001")
        elif initial_state == ProposalStatus.REJECTED:
            proposal.submit()
            proposal.reject(reviewer_id="admin-001", reason="Initial rejection")
        elif initial_state == ProposalStatus.EXECUTED:
            proposal.submit()
            proposal.approve(reviewer_id="admin-001")
            proposal.execute()
        elif initial_state == ProposalStatus.CANCELLED:
            proposal.cancel(canceller_id="user-001")

        # Verify we're in the expected initial state
        assert proposal.status == initial_state

        # Execute and expect InvalidTransitionError
        method = getattr(proposal, action)
        with pytest.raises(InvalidTransitionError) as exc_info:
            method(**extra_kwargs)

        # Verify exception contains useful information
        error = exc_info.value
        assert error.current_status == initial_state.value
        assert isinstance(error.allowed, list)

    # =========================================================================
    # TEST: TERMINAL STATES BLOCK TRANSITIONS
    # =========================================================================

    @pytest.mark.parametrize("terminal_state_fixture,blocked_actions", [
        ("rejected_proposal", ["submit", "approve", "execute"]),
        ("executed_proposal", ["submit", "approve", "reject"]),
        ("cancelled_proposal", ["submit", "approve", "reject", "execute"]),
    ])
    def test_terminal_states_block_transitions(
        self,
        terminal_state_fixture: str,
        blocked_actions: list,
        request: pytest.FixtureRequest,
    ) -> None:
        """Test that terminal states block most transitions."""
        proposal = request.getfixturevalue(terminal_state_fixture)

        for action in blocked_actions:
            method = getattr(proposal, action)

            # Build appropriate kwargs for each action
            kwargs = {}
            if action == "approve":
                kwargs = {"reviewer_id": "admin-001"}
            elif action == "reject":
                kwargs = {"reviewer_id": "admin-001", "reason": "Too late"}
            elif action == "cancel":
                kwargs = {"canceller_id": "user-001"}

            with pytest.raises(InvalidTransitionError):
                method(**kwargs)

    def test_rejected_is_terminal(self, rejected_proposal: Proposal) -> None:
        """Explicitly test REJECTED is a terminal state."""
        assert rejected_proposal.is_terminal is True
        assert rejected_proposal.status in TERMINAL_STATES

    def test_executed_is_terminal(self, executed_proposal: Proposal) -> None:
        """Explicitly test EXECUTED is a terminal state."""
        assert executed_proposal.is_terminal is True
        assert executed_proposal.status in TERMINAL_STATES

    def test_cancelled_is_terminal(self, cancelled_proposal: Proposal) -> None:
        """Explicitly test CANCELLED is a terminal state."""
        assert cancelled_proposal.is_terminal is True
        assert cancelled_proposal.status in TERMINAL_STATES

    # =========================================================================
    # TEST: VERSION INCREMENTS
    # =========================================================================

    def test_version_increments_on_transition(self, draft_proposal: Proposal) -> None:
        """Test that version increments on each state transition."""
        initial_version = draft_proposal.version

        # Transition: DRAFT -> PENDING
        draft_proposal.submit()
        assert draft_proposal.version == initial_version + 1

        # Transition: PENDING -> APPROVED
        draft_proposal.approve(reviewer_id="admin-001")
        assert draft_proposal.version == initial_version + 2

        # Transition: APPROVED -> EXECUTED
        draft_proposal.execute()
        assert draft_proposal.version == initial_version + 3

    def test_version_increments_on_reject(self) -> None:
        """Test version increments when rejecting a proposal."""
        proposal = Proposal(
            action_type="risky_action",
            payload={},
            created_by="agent-001",
        )
        initial_version = proposal.version

        proposal.submit()
        assert proposal.version == initial_version + 1

        proposal.reject(reviewer_id="admin-001", reason="Too risky")
        assert proposal.version == initial_version + 2

    def test_version_increments_on_cancel(self) -> None:
        """Test version increments when cancelling a proposal."""
        proposal = Proposal(
            action_type="maybe_action",
            payload={},
            created_by="agent-001",
        )
        initial_version = proposal.version

        proposal.cancel(canceller_id="user-001")
        assert proposal.version == initial_version + 1

    # =========================================================================
    # TEST: REQUIRED PARAMETERS
    # =========================================================================

    def test_approve_requires_reviewer_id(self, pending_proposal: Proposal) -> None:
        """Test that approve() without reviewer_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            pending_proposal.approve(reviewer_id="")

        assert "reviewer_id is required" in str(exc_info.value)

    def test_approve_with_none_reviewer_id_raises(self, pending_proposal: Proposal) -> None:
        """Test that approve() with None reviewer_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            pending_proposal.approve(reviewer_id=None)  # type: ignore

        assert "reviewer_id is required" in str(exc_info.value)

    def test_reject_requires_reason(self, pending_proposal: Proposal) -> None:
        """Test that reject() without reason raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            pending_proposal.reject(reviewer_id="admin-001", reason="")

        assert "reason is required" in str(exc_info.value)

    def test_reject_requires_reviewer_id(self, pending_proposal: Proposal) -> None:
        """Test that reject() without reviewer_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            pending_proposal.reject(reviewer_id="", reason="Some reason")

        assert "reviewer_id is required" in str(exc_info.value)

    def test_cancel_requires_canceller_id(self, draft_proposal: Proposal) -> None:
        """Test that cancel() without canceller_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            draft_proposal.cancel(canceller_id="")

        assert "canceller_id is required" in str(exc_info.value)

    # =========================================================================
    # TEST: HELPER PROPERTIES
    # =========================================================================

    def test_is_pending_review_property(self, pending_proposal: Proposal) -> None:
        """Test is_pending_review property."""
        assert pending_proposal.is_pending_review is True

    def test_is_pending_review_false_for_other_states(
        self,
        draft_proposal: Proposal,
        approved_proposal: Proposal,
    ) -> None:
        """Test is_pending_review is False for non-PENDING states."""
        assert draft_proposal.is_pending_review is False
        assert approved_proposal.is_pending_review is False

    def test_can_execute_property(self, approved_proposal: Proposal) -> None:
        """Test can_execute property for APPROVED state."""
        assert approved_proposal.can_execute is True

    def test_can_execute_false_for_other_states(
        self,
        draft_proposal: Proposal,
        pending_proposal: Proposal,
        rejected_proposal: Proposal,
    ) -> None:
        """Test can_execute is False for non-APPROVED states."""
        assert draft_proposal.can_execute is False
        assert pending_proposal.can_execute is False
        assert rejected_proposal.can_execute is False

    # =========================================================================
    # TEST: REVIEW FIELDS
    # =========================================================================

    def test_approve_sets_review_fields(self, pending_proposal: Proposal) -> None:
        """Test that approve() sets reviewer fields correctly."""
        pending_proposal.approve(reviewer_id="admin-001", comment="Looks good!")

        assert pending_proposal.reviewed_by == "admin-001"
        assert pending_proposal.reviewed_at is not None
        assert pending_proposal.review_comment == "Looks good!"

    def test_reject_sets_review_fields(self, pending_proposal: Proposal) -> None:
        """Test that reject() sets reviewer fields correctly."""
        pending_proposal.reject(reviewer_id="admin-002", reason="Security concerns")

        assert pending_proposal.reviewed_by == "admin-002"
        assert pending_proposal.reviewed_at is not None
        assert pending_proposal.review_comment == "Security concerns"

    def test_execute_sets_execution_fields(self, approved_proposal: Proposal) -> None:
        """Test that execute() sets execution fields correctly."""
        result = {"status": "success", "deployed_version": "2.1.0"}
        approved_proposal.execute(executor_id="system-001", result=result)

        assert approved_proposal.executed_at is not None
        assert approved_proposal.execution_result == result

    # =========================================================================
    # TEST: METHOD CHAINING
    # =========================================================================

    def test_submit_returns_self_for_chaining(self, draft_proposal: Proposal) -> None:
        """Test that submit() returns self for method chaining."""
        result = draft_proposal.submit()
        assert result is draft_proposal

    def test_approve_returns_self_for_chaining(self, pending_proposal: Proposal) -> None:
        """Test that approve() returns self for method chaining."""
        result = pending_proposal.approve(reviewer_id="admin-001")
        assert result is pending_proposal

    def test_reject_returns_self_for_chaining(self, pending_proposal: Proposal) -> None:
        """Test that reject() returns self for method chaining."""
        result = pending_proposal.reject(reviewer_id="admin-001", reason="Rejected")
        assert result is pending_proposal

    def test_execute_returns_self_for_chaining(self, approved_proposal: Proposal) -> None:
        """Test that execute() returns self for method chaining."""
        result = approved_proposal.execute()
        assert result is approved_proposal

    def test_cancel_returns_self_for_chaining(self, draft_proposal: Proposal) -> None:
        """Test that cancel() returns self for method chaining."""
        result = draft_proposal.cancel(canceller_id="user-001")
        assert result is draft_proposal

    # =========================================================================
    # TEST: VALID TRANSITIONS MAP COMPLETENESS
    # =========================================================================

    def test_all_states_have_transition_map_entry(self) -> None:
        """Ensure every ProposalStatus has an entry in VALID_TRANSITIONS."""
        for status in ProposalStatus:
            assert status in VALID_TRANSITIONS, (
                f"ProposalStatus.{status.name} missing from VALID_TRANSITIONS map"
            )

    def test_terminal_states_match_config(self) -> None:
        """Verify TERMINAL_STATES matches expected terminal states."""
        expected_terminal = {
            ProposalStatus.REJECTED,
            ProposalStatus.EXECUTED,
            ProposalStatus.CANCELLED,
            ProposalStatus.DELETED,
        }
        assert TERMINAL_STATES == expected_terminal

    # =========================================================================
    # TEST: AUDIT LOG
    # =========================================================================

    def test_to_audit_log_contains_all_fields(self, executed_proposal: Proposal) -> None:
        """Test that to_audit_log() returns comprehensive audit data."""
        audit_log = executed_proposal.to_audit_log()

        required_fields = [
            "proposal_id",
            "action_type",
            "status",
            "priority",
            "created_by",
            "created_at",
            "reviewed_by",
            "reviewed_at",
            "review_comment",
            "executed_at",
            "version",
        ]

        for field in required_fields:
            assert field in audit_log, f"Audit log missing required field: {field}"


class TestProposalCreation:
    """Test Proposal creation and initialization."""

    def test_default_status_is_draft(self) -> None:
        """Test that new proposals start in DRAFT status."""
        proposal = Proposal(
            action_type="test_action",
            payload={},
            created_by="agent-001",
        )
        assert proposal.status == ProposalStatus.DRAFT

    def test_default_priority_is_medium(self) -> None:
        """Test that default priority is MEDIUM."""
        proposal = Proposal(
            action_type="test_action",
            payload={},
            created_by="agent-001",
        )
        assert proposal.priority == ProposalPriority.MEDIUM

    def test_action_type_normalized_to_lowercase(self) -> None:
        """Test that action_type is normalized to lowercase."""
        proposal = Proposal(
            action_type="DEPLOY_TO_PRODUCTION",
            payload={},
            created_by="agent-001",
        )
        assert proposal.action_type == "deploy_to_production"

    def test_invalid_action_type_raises_error(self) -> None:
        """Test that invalid action_type raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Proposal(
                action_type="invalid-action-name!",  # Contains invalid chars
                payload={},
                created_by="agent-001",
            )

    def test_id_is_generated_automatically(self) -> None:
        """Test that id is auto-generated if not provided."""
        proposal = Proposal(
            action_type="test_action",
            payload={},
            created_by="agent-001",
        )
        assert proposal.id is not None
        assert len(proposal.id) == 36  # UUID format

    def test_initial_version_is_one(self) -> None:
        """Test that initial version is 1."""
        proposal = Proposal(
            action_type="test_action",
            payload={},
            created_by="agent-001",
        )
        assert proposal.version == 1


class TestInvalidTransitionError:
    """Test InvalidTransitionError exception behavior."""

    def test_exception_contains_useful_message(self) -> None:
        """Test that InvalidTransitionError has a descriptive message."""
        error = InvalidTransitionError(
            current_status="rejected",
            target_status="approved",
            allowed=["deleted"],
        )

        message = str(error)
        assert "rejected" in message
        assert "approved" in message
        assert "deleted" in message

    def test_exception_attributes_accessible(self) -> None:
        """Test that exception attributes are accessible."""
        error = InvalidTransitionError(
            current_status="draft",
            target_status="executed",
            allowed=["pending", "cancelled"],
        )

        assert error.current_status == "draft"
        assert error.target_status == "executed"
        assert error.allowed == ["pending", "cancelled"]
