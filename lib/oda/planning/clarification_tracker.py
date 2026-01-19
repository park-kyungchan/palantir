"""
Orion ODA v3.0 - Clarification Tracker (V2.1.8)
================================================

Semantic Integrity preservation for /ask Skill.
Implements Socratic clarification flow with mandatory approval gate.

This module ensures:
- User intent is accurately understood before execution
- Ambiguities are resolved through structured questioning
- NO execution without explicit user approval
- Auto-Compact survival through JSON serialization

State Machine Flow:
    INITIAL -> UNDERSTANDING -> QUESTIONING -> CLARIFIED -> APPROVED -> EXECUTING

Usage:
    tracker = create_clarification_tracker("코드 리뷰해줘")

    tracker.start_understanding()
    tracker.state_understanding("사용자가 코드 품질 검사를 원하는 것으로 이해됩니다.")

    tracker.identify_ambiguities(["어떤 파일/디렉토리?", "검사 범위는?"])
    tracker.start_questioning()

    tracker.record_response(1, "lib/ 디렉토리만 봐줘")
    tracker.mark_clarified()

    # MANDATORY: Must get approval before execution
    approval = tracker.request_approval()
    # User approves...
    tracker.mark_approved()

    tracker.start_execution("/audit", "lib/")  # Only works if approved
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class ClarificationError(Exception):
    """Raised when clarification protocol is violated."""
    pass


class ClarificationState(str, Enum):
    """
    State machine for clarification flow.

    Transitions are forward-only:
    INITIAL -> UNDERSTANDING -> QUESTIONING -> CLARIFIED -> APPROVED -> EXECUTING
    """
    INITIAL = "initial"              # 최초 입력
    UNDERSTANDING = "understanding"  # AI stating "내가 이해한 바로는..."
    QUESTIONING = "questioning"      # Asking Socratic questions
    CLARIFIED = "clarified"          # All ambiguities resolved
    APPROVED = "approved"            # USER APPROVED - mandatory gate
    EXECUTING = "executing"          # Skill execution in progress


# Valid state transitions (forward-only)
VALID_TRANSITIONS: Dict[ClarificationState, List[ClarificationState]] = {
    ClarificationState.INITIAL: [ClarificationState.UNDERSTANDING],
    ClarificationState.UNDERSTANDING: [ClarificationState.QUESTIONING, ClarificationState.CLARIFIED],
    ClarificationState.QUESTIONING: [ClarificationState.CLARIFIED],
    ClarificationState.CLARIFIED: [ClarificationState.APPROVED],
    ClarificationState.APPROVED: [ClarificationState.EXECUTING],
    ClarificationState.EXECUTING: [],  # Terminal state
}


# Confidence levels (categorical, NO numerical scores)
ConfidenceLevel = Literal["high", "medium", "low"]


@dataclass
class ClarificationRound:
    """
    A single round of clarification.

    Attributes:
        round_number: Round number (1-indexed)
        ai_understanding: What AI understood from the input
        ambiguities_identified: List of identified ambiguities
        questions_asked: Questions posed to user
        user_responses: User's responses to questions
        timestamp: When this round occurred
    """
    round_number: int
    ai_understanding: str = ""
    ambiguities_identified: List[str] = field(default_factory=list)
    questions_asked: List[str] = field(default_factory=list)
    user_responses: Dict[int, str] = field(default_factory=dict)  # question_index -> response
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "round_number": self.round_number,
            "ai_understanding": self.ai_understanding,
            "ambiguities_identified": self.ambiguities_identified,
            "questions_asked": self.questions_asked,
            "user_responses": self.user_responses,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClarificationRound":
        """Deserialize from dictionary."""
        return cls(
            round_number=data["round_number"],
            ai_understanding=data.get("ai_understanding", ""),
            ambiguities_identified=data.get("ambiguities_identified", []),
            questions_asked=data.get("questions_asked", []),
            user_responses={int(k): v for k, v in data.get("user_responses", {}).items()},
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )


@dataclass
class ApprovalRequest:
    """
    Request for user approval before execution.

    Attributes:
        final_prompt: The clarified, unambiguous prompt
        skill_recommendation: Recommended skill to execute
        confidence_level: Categorical confidence (high|medium|low)
        clarification_summary: Summary of clarification rounds
    """
    final_prompt: str
    skill_recommendation: str
    confidence_level: ConfidenceLevel
    clarification_summary: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "final_prompt": self.final_prompt,
            "skill_recommendation": self.skill_recommendation,
            "confidence_level": self.confidence_level,
            "clarification_summary": self.clarification_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalRequest":
        """Deserialize from dictionary."""
        return cls(
            final_prompt=data["final_prompt"],
            skill_recommendation=data["skill_recommendation"],
            confidence_level=data.get("confidence_level", "medium"),
            clarification_summary=data.get("clarification_summary", ""),
        )

    def format_for_user(self) -> str:
        """Format approval request for user display."""
        confidence_emoji = {
            "high": "[HIGH]",
            "medium": "[MEDIUM]",
            "low": "[LOW]",
        }

        return f"""
## Approval Request

**Confidence:** {confidence_emoji[self.confidence_level]}

**Clarified Intent:**
{self.final_prompt}

**Recommended Action:**
Execute `/{self.skill_recommendation}`

**Summary:**
{self.clarification_summary}

---
Do you approve this execution? (yes/no)
"""


@dataclass
class SemanticIntegrityRecord:
    """
    Complete record of semantic integrity preservation.

    This record survives Auto-Compact and enables audit trail.

    Attributes:
        original_input: User's original input
        rounds: All clarification rounds
        final_prompt: The clarified, unambiguous prompt
        approved: Whether user approved execution
        approval_timestamp: When approval was given
        routed_to: Skill that was invoked
    """
    original_input: str
    rounds: List[ClarificationRound] = field(default_factory=list)
    final_prompt: str = ""
    approved: bool = False
    approval_timestamp: Optional[datetime] = None
    routed_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "original_input": self.original_input,
            "rounds": [r.to_dict() for r in self.rounds],
            "final_prompt": self.final_prompt,
            "approved": self.approved,
            "approval_timestamp": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
            "routed_to": self.routed_to,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticIntegrityRecord":
        """Deserialize from dictionary."""
        return cls(
            original_input=data["original_input"],
            rounds=[ClarificationRound.from_dict(r) for r in data.get("rounds", [])],
            final_prompt=data.get("final_prompt", ""),
            approved=data.get("approved", False),
            approval_timestamp=(
                datetime.fromisoformat(data["approval_timestamp"])
                if data.get("approval_timestamp")
                else None
            ),
            routed_to=data.get("routed_to"),
        )


class ClarificationTracker:
    """
    State machine for semantic integrity preservation.

    Implements Socratic clarification flow with mandatory approval gate.
    Forward-only state transitions ensure proper protocol adherence.

    Key invariants:
    - Cannot skip states
    - Cannot execute without approval
    - Maximum 3 rounds of questioning (prevents infinite loops)
    - All state persists for Auto-Compact survival

    Example:
        tracker = ClarificationTracker("코드 좀 봐줘")

        tracker.start_understanding()
        tracker.state_understanding("코드 리뷰를 원하시는 것으로 이해합니다.")

        tracker.identify_ambiguities(["검사 대상 파일은?"])
        tracker.start_questioning()

        tracker.record_response(0, "lib/ 디렉토리")
        tracker.mark_clarified()

        # Get approval (MANDATORY)
        approval = tracker.request_approval()
        tracker.mark_approved()

        tracker.start_execution("/audit", "lib/")
    """

    MAX_ROUNDS = 3  # Prevent infinite questioning loops

    def __init__(self, user_input: str):
        """
        Initialize ClarificationTracker.

        Args:
            user_input: The original user input to clarify
        """
        self._state = ClarificationState.INITIAL
        self._record = SemanticIntegrityRecord(original_input=user_input)
        self._current_round: Optional[ClarificationRound] = None
        self._pending_approval: Optional[ApprovalRequest] = None
        self._created_at = datetime.now()
        self._updated_at = datetime.now()

    # ========== State Properties ==========

    @property
    def state(self) -> ClarificationState:
        """Current state in the clarification flow."""
        return self._state

    @property
    def original_input(self) -> str:
        """The original user input."""
        return self._record.original_input

    @property
    def round_count(self) -> int:
        """Number of clarification rounds completed."""
        return len(self._record.rounds)

    @property
    def current_round(self) -> Optional[ClarificationRound]:
        """The current clarification round."""
        return self._current_round

    # ========== State Transition Methods ==========

    def _transition_to(self, new_state: ClarificationState) -> None:
        """
        Transition to a new state with validation.

        Args:
            new_state: Target state

        Raises:
            ClarificationError: If transition is invalid
        """
        valid_next = VALID_TRANSITIONS.get(self._state, [])
        if new_state not in valid_next:
            raise ClarificationError(
                f"Invalid state transition: {self._state.value} -> {new_state.value}. "
                f"Valid transitions: {[s.value for s in valid_next]}"
            )

        self._state = new_state
        self._updated_at = datetime.now()

    def start_understanding(self) -> None:
        """
        Begin understanding phase.

        Call this when AI starts analyzing user input.
        """
        self._transition_to(ClarificationState.UNDERSTANDING)

        # Create new round
        self._current_round = ClarificationRound(
            round_number=self.round_count + 1
        )

    def state_understanding(self, understanding: str) -> None:
        """
        Record AI's understanding of user input.

        Args:
            understanding: "내가 이해한 바로는..." statement
        """
        if self._state != ClarificationState.UNDERSTANDING:
            raise ClarificationError(
                f"Cannot state understanding in {self._state.value} state"
            )

        if self._current_round is None:
            raise ClarificationError("No active round. Call start_understanding() first.")

        self._current_round.ai_understanding = understanding
        self._updated_at = datetime.now()

    def identify_ambiguities(self, ambiguities: List[str]) -> None:
        """
        Identify ambiguities in user input.

        Args:
            ambiguities: List of identified ambiguities/unclear points
        """
        if self._state != ClarificationState.UNDERSTANDING:
            raise ClarificationError(
                f"Cannot identify ambiguities in {self._state.value} state"
            )

        if self._current_round is None:
            raise ClarificationError("No active round.")

        self._current_round.ambiguities_identified = ambiguities
        self._updated_at = datetime.now()

    def start_questioning(self, questions: Optional[List[str]] = None) -> None:
        """
        Begin Socratic questioning phase.

        Args:
            questions: Optional questions to ask (can also be set via ambiguities)
        """
        self._transition_to(ClarificationState.QUESTIONING)

        if self._current_round is None:
            raise ClarificationError("No active round.")

        if questions:
            self._current_round.questions_asked = questions
        elif self._current_round.ambiguities_identified:
            # Convert ambiguities to questions
            self._current_round.questions_asked = [
                f"{amb}?" if not amb.endswith("?") else amb
                for amb in self._current_round.ambiguities_identified
            ]

        self._updated_at = datetime.now()

    def record_response(self, question_index: int, response: str) -> None:
        """
        Record user's response to a question.

        Args:
            question_index: Index of the question being answered
            response: User's response
        """
        if self._state != ClarificationState.QUESTIONING:
            raise ClarificationError(
                f"Cannot record response in {self._state.value} state"
            )

        if self._current_round is None:
            raise ClarificationError("No active round.")

        self._current_round.user_responses[question_index] = response
        self._updated_at = datetime.now()

    def mark_clarified(self, final_prompt: Optional[str] = None) -> None:
        """
        Mark clarification as complete.

        All ambiguities should be resolved at this point.

        Args:
            final_prompt: The clarified, unambiguous prompt
        """
        # Can transition from UNDERSTANDING (no questions needed) or QUESTIONING
        if self._state not in (ClarificationState.UNDERSTANDING, ClarificationState.QUESTIONING):
            raise ClarificationError(
                f"Cannot mark clarified in {self._state.value} state"
            )

        # Finalize current round
        if self._current_round is not None:
            self._record.rounds.append(self._current_round)
            self._current_round = None

        if final_prompt:
            self._record.final_prompt = final_prompt
        else:
            # Synthesize from rounds
            self._record.final_prompt = self._synthesize_final_prompt()

        self._state = ClarificationState.CLARIFIED
        self._updated_at = datetime.now()

    def _synthesize_final_prompt(self) -> str:
        """
        Synthesize final prompt from clarification rounds.

        Returns:
            Synthesized clarified prompt
        """
        if not self._record.rounds:
            return self._record.original_input

        last_round = self._record.rounds[-1]

        # Combine understanding with responses
        parts = [last_round.ai_understanding]

        for idx, response in sorted(last_round.user_responses.items()):
            if idx < len(last_round.questions_asked):
                question = last_round.questions_asked[idx]
                parts.append(f"{question} -> {response}")

        return " | ".join(parts)

    # ========== Approval Gate (MANDATORY) ==========

    def request_approval(
        self,
        skill_recommendation: str = "ask",
        confidence_level: ConfidenceLevel = "medium",
    ) -> ApprovalRequest:
        """
        Create approval request for user.

        MANDATORY: No execution without approval.

        Args:
            skill_recommendation: Recommended skill to execute
            confidence_level: Categorical confidence (high|medium|low)

        Returns:
            ApprovalRequest for user review
        """
        if self._state != ClarificationState.CLARIFIED:
            raise ClarificationError(
                f"Cannot request approval in {self._state.value} state. "
                "Must be CLARIFIED first."
            )

        # Generate clarification summary
        summary_parts = []
        for round in self._record.rounds:
            if round.ai_understanding:
                summary_parts.append(f"Round {round.round_number}: {round.ai_understanding}")
            if round.user_responses:
                for idx, resp in round.user_responses.items():
                    summary_parts.append(f"  - Q{idx}: {resp}")

        self._pending_approval = ApprovalRequest(
            final_prompt=self._record.final_prompt,
            skill_recommendation=skill_recommendation,
            confidence_level=confidence_level,
            clarification_summary="\n".join(summary_parts) if summary_parts else "Direct clarification",
        )

        return self._pending_approval

    def mark_approved(self) -> None:
        """
        Mark as user-approved.

        MANDATORY gate before execution.
        """
        if self._state != ClarificationState.CLARIFIED:
            raise ClarificationError(
                f"Cannot approve in {self._state.value} state"
            )

        if self._pending_approval is None:
            raise ClarificationError(
                "No pending approval request. Call request_approval() first."
            )

        self._record.approved = True
        self._record.approval_timestamp = datetime.now()

        self._state = ClarificationState.APPROVED
        self._updated_at = datetime.now()

    def is_approved(self) -> bool:
        """
        Check if execution is approved.

        Returns:
            True if user has approved execution
        """
        return self._record.approved and self._state == ClarificationState.APPROVED

    # ========== Execution Control ==========

    def start_execution(self, skill: str, scope: Optional[str] = None) -> None:
        """
        Begin skill execution.

        BLOCKED if not approved.

        Args:
            skill: Skill to execute (e.g., "/audit")
            scope: Optional execution scope

        Raises:
            ClarificationError: If not approved
        """
        if not self.is_approved():
            raise ClarificationError(
                "EXECUTION BLOCKED: User approval required. "
                "Call request_approval() and mark_approved() first."
            )

        self._transition_to(ClarificationState.EXECUTING)
        self._record.routed_to = skill

        if scope:
            self._record.final_prompt = f"{self._record.final_prompt} [scope: {scope}]"

    # ========== Record Access ==========

    def get_record(self) -> SemanticIntegrityRecord:
        """
        Get the complete semantic integrity record.

        Returns:
            Full record for audit/persistence
        """
        return self._record

    def get_approval_request(self) -> Optional[ApprovalRequest]:
        """Get pending approval request."""
        return self._pending_approval

    # ========== TodoWrite Integration ==========

    def to_todowrite_json(self) -> List[Dict[str, Any]]:
        """
        Generate TodoWrite-compatible JSON for UI display.

        Returns:
            List of todo items showing clarification progress
        """
        todos = []

        # Header: Clarification flow status
        state_display = {
            ClarificationState.INITIAL: "Receiving input",
            ClarificationState.UNDERSTANDING: "Analyzing intent",
            ClarificationState.QUESTIONING: "Asking clarifying questions",
            ClarificationState.CLARIFIED: "Awaiting approval",
            ClarificationState.APPROVED: "Approved - ready to execute",
            ClarificationState.EXECUTING: "Executing skill",
        }

        state_status = {
            ClarificationState.INITIAL: "pending",
            ClarificationState.UNDERSTANDING: "in_progress",
            ClarificationState.QUESTIONING: "in_progress",
            ClarificationState.CLARIFIED: "in_progress",
            ClarificationState.APPROVED: "in_progress",
            ClarificationState.EXECUTING: "completed",
        }

        # Main status todo
        todos.append({
            "content": f"[/ask] {state_display[self._state]} | Input: {self.original_input[:50]}...",
            "status": state_status[self._state],
            "activeForm": state_display[self._state],
        })

        # Round todos
        for round in self._record.rounds:
            round_status = "completed"
            todos.append({
                "content": f"  Round {round.round_number}: {round.ai_understanding[:50]}..." if round.ai_understanding else f"  Round {round.round_number}",
                "status": round_status,
                "activeForm": f"Completed round {round.round_number}",
            })

        # Current round (if any)
        if self._current_round:
            todos.append({
                "content": f"  Round {self._current_round.round_number}: In progress",
                "status": "in_progress",
                "activeForm": "Processing current round",
            })

        # Approval status
        if self._state in (ClarificationState.CLARIFIED, ClarificationState.APPROVED, ClarificationState.EXECUTING):
            approval_status = "completed" if self._record.approved else "pending"
            todos.append({
                "content": f"  [GATE] User Approval: {'APPROVED' if self._record.approved else 'PENDING'}",
                "status": approval_status,
                "activeForm": "Checking user approval",
            })

        return todos

    # ========== Persistence (Auto-Compact Survival) ==========

    def to_json(self) -> str:
        """
        Serialize to JSON for persistence.

        Returns:
            JSON string for storage
        """
        data = {
            "state": self._state.value,
            "record": self._record.to_dict(),
            "current_round": self._current_round.to_dict() if self._current_round else None,
            "pending_approval": self._pending_approval.to_dict() if self._pending_approval else None,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ClarificationTracker":
        """
        Deserialize from JSON.

        Args:
            json_str: JSON string from to_json()

        Returns:
            Restored ClarificationTracker
        """
        data = json.loads(json_str)

        # Create instance with original input
        record_data = data["record"]
        tracker = cls(record_data["original_input"])

        # Restore state
        tracker._state = ClarificationState(data["state"])
        tracker._record = SemanticIntegrityRecord.from_dict(record_data)

        # Restore current round
        if data.get("current_round"):
            tracker._current_round = ClarificationRound.from_dict(data["current_round"])

        # Restore pending approval
        if data.get("pending_approval"):
            tracker._pending_approval = ApprovalRequest.from_dict(data["pending_approval"])

        # Restore timestamps
        tracker._created_at = datetime.fromisoformat(data["created_at"])
        tracker._updated_at = datetime.fromisoformat(data["updated_at"])

        return tracker

    # ========== Additional Rounds ==========

    def needs_more_clarification(self) -> bool:
        """
        Check if more clarification rounds are allowed.

        Returns:
            True if under MAX_ROUNDS and not yet clarified
        """
        return (
            self.round_count < self.MAX_ROUNDS
            and self._state in (ClarificationState.UNDERSTANDING, ClarificationState.QUESTIONING)
        )

    def start_new_round(self) -> bool:
        """
        Start a new clarification round.

        Returns:
            True if new round started, False if max rounds reached
        """
        if self.round_count >= self.MAX_ROUNDS:
            return False

        if self._state == ClarificationState.QUESTIONING:
            # Save current round and start new one
            if self._current_round:
                self._record.rounds.append(self._current_round)

            self._current_round = ClarificationRound(
                round_number=self.round_count + 1
            )
            self._state = ClarificationState.UNDERSTANDING
            return True

        return False


# ========== Convenience Functions ==========

def create_clarification_tracker(user_input: str) -> ClarificationTracker:
    """
    Create a new ClarificationTracker instance.

    Args:
        user_input: The user input to clarify

    Returns:
        New ClarificationTracker instance
    """
    return ClarificationTracker(user_input)


def load_clarification_tracker(json_str: str) -> ClarificationTracker:
    """
    Load ClarificationTracker from JSON (for Auto-Compact recovery).

    Args:
        json_str: JSON string from to_json()

    Returns:
        Restored ClarificationTracker
    """
    return ClarificationTracker.from_json(json_str)


def determine_confidence(
    ambiguity_count: int,
    response_count: int,
    round_count: int,
) -> ConfidenceLevel:
    """
    Determine categorical confidence level.

    NO numerical scores - uses categorical assessment.

    Args:
        ambiguity_count: Number of ambiguities identified
        response_count: Number of responses received
        round_count: Number of clarification rounds

    Returns:
        Confidence level: "high", "medium", or "low"
    """
    # All ambiguities resolved in first round
    if ambiguity_count > 0 and response_count >= ambiguity_count and round_count == 1:
        return "high"

    # Required multiple rounds but resolved
    if response_count >= ambiguity_count and round_count <= 2:
        return "medium"

    # Still have unresolved ambiguities or too many rounds
    return "low"
