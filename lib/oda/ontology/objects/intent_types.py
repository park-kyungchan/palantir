"""
Orion ODA v4.0 - Intent Classification ObjectTypes

ODA ObjectTypes for LLM-Native Intent Classification.
Tracks intent classification results for audit and telemetry.

User Requirements (2026-01-13):
- TriggerDetector 완전 제거
- LLM-Native 의도 분류
- 커스텀 커맨드 고도화
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, List, Optional

from pydantic import Field

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# ENUMS
# =============================================================================

class IntentMatchType(str, Enum):
    """How the intent was matched."""
    EXPLICIT = "explicit"    # User used /command directly
    SEMANTIC = "semantic"    # LLM inferred from natural language
    FALLBACK = "fallback"    # Low confidence, needs clarification


class IntentConfidenceLevel(str, Enum):
    """Confidence level categories."""
    HIGH = "high"        # >= 0.8
    MEDIUM = "medium"    # 0.5 - 0.8
    LOW = "low"          # < 0.5


class AdapterType(str, Enum):
    """LLM adapter types."""
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"
    UNKNOWN = "unknown"


# =============================================================================
# OBJECT TYPES
# =============================================================================

@register_object_type
class IntentClassification(OntologyObject):
    """
    Records an intent classification result.

    This ObjectType tracks LLM-based intent classifications for:
    - Audit trail
    - Telemetry and analytics
    - User feedback collection
    - Model improvement

    Example:
        classification = IntentClassification(
            user_input="코드 리뷰해줘",
            matched_command="/audit",
            confidence=0.92,
            reasoning="User requests code review",
            adapter_type=AdapterType.CLAUDE
        )
    """
    # Core classification fields
    user_input: str = Field(
        ...,
        max_length=10000,
        description="Original user input"
    )
    matched_command: str = Field(
        ...,
        max_length=100,
        description="Matched command (e.g., /ask, /plan, /audit, none)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence (0.0-1.0)"
    )
    reasoning: str = Field(
        default="",
        max_length=1000,
        description="LLM's explanation for classification"
    )
    match_type: IntentMatchType = Field(
        default=IntentMatchType.SEMANTIC,
        description="How the intent was matched"
    )

    # Adapter information
    adapter_type: AdapterType = Field(
        default=AdapterType.UNKNOWN,
        description="Which LLM adapter was used"
    )
    adapter_model: str = Field(
        default="",
        max_length=100,
        description="Specific model used (e.g., claude-sonnet-4-20250514)"
    )

    # Timing
    latency_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Classification latency in milliseconds"
    )

    # User feedback (optional)
    user_confirmed: Optional[bool] = Field(
        default=None,
        description="Whether user confirmed the classification"
    )
    user_corrected_command: Optional[str] = Field(
        default=None,
        max_length=100,
        description="User's corrected command if classification was wrong"
    )

    # Session tracking
    session_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Session identifier for grouping related classifications"
    )

    @property
    def confidence_level(self) -> IntentConfidenceLevel:
        """Get confidence level category."""
        if self.confidence >= 0.8:
            return IntentConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return IntentConfidenceLevel.MEDIUM
        return IntentConfidenceLevel.LOW

    @property
    def needs_clarification(self) -> bool:
        """Check if classification needs user clarification."""
        return (
            self.confidence < 0.7 and
            self.match_type != IntentMatchType.EXPLICIT
        )

    @property
    def is_successful(self) -> bool:
        """Check if classification was successful (high confidence or confirmed)."""
        if self.user_confirmed is not None:
            return self.user_confirmed
        return self.confidence >= 0.7

    def to_audit_record(self) -> dict:
        """Format for audit logging."""
        return {
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "user_input": self.user_input[:100],  # Truncate for privacy
            "matched_command": self.matched_command,
            "confidence": self.confidence,
            "match_type": self.match_type.value,
            "adapter_type": self.adapter_type.value,
            "latency_ms": self.latency_ms,
            "needs_clarification": self.needs_clarification,
        }


@register_object_type
class CommandDefinition(OntologyObject):
    """
    Defines an available command for intent classification.

    Commands are the targets for intent classification.
    Each command has a semantic description that LLM uses for matching.

    Example:
        cmd = CommandDefinition(
            name="/audit",
            description="코드 품질 검사 및 리뷰",
            examples=["코드 리뷰해줘", "검사해줘"]
        )
    """
    name: str = Field(
        ...,
        max_length=50,
        description="Command name (e.g., /ask, /plan)"
    )
    description: str = Field(
        ...,
        max_length=500,
        description="Semantic description for LLM"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Example trigger phrases"
    )
    priority: int = Field(
        default=0,
        description="Priority for conflict resolution"
    )
    is_enabled: bool = Field(
        default=True,
        description="Whether command is currently active"
    )

    # Statistics
    total_matches: int = Field(
        default=0,
        ge=0,
        description="Total times this command was matched"
    )
    success_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="User confirmation rate"
    )

    # Link to related skill (if applicable)
    skill_id: Optional[str] = Field(
        default=None,
        description="Related SkillDefinition ID"
    )

    def to_prompt_format(self) -> str:
        """Format for inclusion in LLM prompt."""
        examples_str = ""
        if self.examples:
            examples_str = f" (examples: {', '.join(self.examples[:3])})"
        return f"- {self.name}: {self.description}{examples_str}"


@register_object_type
class ClassificationSession(OntologyObject):
    """
    Groups related intent classifications in a conversation session.

    Used for:
    - Multi-turn intent tracking
    - Context accumulation
    - Session-level analytics
    """
    session_id: str = Field(
        ...,
        max_length=100,
        description="Unique session identifier"
    )
    total_classifications: int = Field(
        default=0,
        ge=0,
        description="Number of classifications in session"
    )
    successful_classifications: int = Field(
        default=0,
        ge=0,
        description="Number of successful classifications"
    )
    dominant_command: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Most frequently matched command"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Session start time"
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        description="Session end time"
    )

    @property
    def success_rate(self) -> float:
        """Calculate session success rate."""
        if self.total_classifications == 0:
            return 0.0
        return self.successful_classifications / self.total_classifications
