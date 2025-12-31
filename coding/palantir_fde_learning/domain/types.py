"""
Core Domain Types for the Palantir FDE Learning System

This module defines the fundamental entities and value objects
for the learning system. These types are pure domain objects
with no external dependencies beyond Pydantic.

Design Principles:
- Immutable by default (frozen=True where appropriate)
- Rich validation through Pydantic
- Clear semantic meaning through type annotations
- Prerequisites modeled as a DAG (Directed Acyclic Graph)
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DifficultyTier(str, Enum):
    """
    Represents the difficulty level of a learning concept.

    Tiers are based on Bloom's Taxonomy progression:
    - BEGINNER: Knowledge & Comprehension (understand concepts)
    - INTERMEDIATE: Application & Analysis (apply in practice)
    - ADVANCED: Synthesis & Evaluation (create and optimize)
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    def to_numeric(self) -> int:
        """Convert tier to numeric value for comparison."""
        mapping = {
            DifficultyTier.BEGINNER: 1,
            DifficultyTier.INTERMEDIATE: 2,
            DifficultyTier.ADVANCED: 3,
        }
        return mapping[self]

    @classmethod
    def from_numeric(cls, value: int) -> "DifficultyTier":
        """Convert numeric value to tier."""
        mapping = {
            1: cls.BEGINNER,
            2: cls.INTERMEDIATE,
            3: cls.ADVANCED,
        }
        if value not in mapping:
            raise ValueError(f"Invalid tier numeric value: {value}")
        return mapping[value]


class LearningDomain(str, Enum):
    """
    Represents the knowledge domain for a learning concept.

    Based on actual Palantir AIP/Foundry products (2024-2025).
    
    Categories:
    - Core Platform: FOUNDRY, AIP, ONTOLOGY
    - AIP Features: AIP_LOGIC, AIP_AGENT_STUDIO, AIP_EVALS
    - Foundry Applications: WORKSHOP, QUIVER, SLATE, CODE_REPOS, PIPELINE_BUILDER, DATA_CONNECTION
    - Developer Tools: OSDK, FUNCTIONS, ACTIONS
    - UI/UX: BLUEPRINT
    
    Reference: https://www.palantir.com/docs/foundry/
    """

    # ═══════════════════════════════════════════════════════════════════
    # CORE PLATFORM
    # ═══════════════════════════════════════════════════════════════════
    FOUNDRY = "foundry"              # Palantir Foundry platform
    AIP = "aip"                      # AI Platform (LLM integration)
    ONTOLOGY = "ontology"            # Ontology (core data modeling)

    # ═══════════════════════════════════════════════════════════════════
    # AIP FEATURES
    # ═══════════════════════════════════════════════════════════════════
    AIP_LOGIC = "aip_logic"          # AIP Logic (no-code AI function builder)
    AIP_AGENT_STUDIO = "aip_agent_studio"  # AIP Agent Studio (AI agents)
    AIP_EVALS = "aip_evals"          # AIP Evaluations (AI evaluation system)

    # ═══════════════════════════════════════════════════════════════════
    # FOUNDRY APPLICATIONS
    # ═══════════════════════════════════════════════════════════════════
    WORKSHOP = "workshop"            # Workshop (no-code app builder)
    QUIVER = "quiver"               # Quiver (ontology-based analytics)
    SLATE = "slate"                 # Slate (custom app builder)
    CODE_REPOSITORIES = "code_repositories"  # Code Repositories (web IDE)
    PIPELINE_BUILDER = "pipeline_builder"    # Pipeline Builder (data pipelines)
    DATA_CONNECTION = "data_connection"      # Data Connection (external data sync)

    # ═══════════════════════════════════════════════════════════════════
    # DEVELOPER TOOLS
    # ═══════════════════════════════════════════════════════════════════
    OSDK = "osdk"                    # Ontology SDK 2.0 (external app development)
    FUNCTIONS = "functions"          # Foundry Functions (TypeScript/Python)
    ACTIONS = "actions"              # Ontology Actions (data mutation logic)

    # ═══════════════════════════════════════════════════════════════════
    # UI/UX
    # ═══════════════════════════════════════════════════════════════════
    BLUEPRINT = "blueprint"          # Blueprint (React design system)


class LearningConcept(BaseModel):
    """
    Represents a single learning concept in the knowledge graph.

    A concept is a discrete unit of knowledge that can be:
    - Tracked for mastery
    - Linked to prerequisites
    - Associated with learning materials

    The concept_id follows the format: domain.tier.topic
    Example: "osdk.beginner.installation"

    Attributes:
        concept_id: Unique identifier following domain.tier.topic format
        domain: The knowledge domain this concept belongs to
        difficulty_tier: The difficulty level of the concept
        prerequisites: List of concept_ids that must be mastered first
        title: Human-readable title of the concept
        description: Optional detailed description
        estimated_minutes: Estimated time to learn in minutes
        tags: Optional tags for filtering and organization
    """

    concept_id: str = Field(
        ...,
        min_length=3,
        max_length=128,
        pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$",
        description="Unique identifier in dot-notation format",
    )
    domain: LearningDomain = Field(
        ...,
        description="Knowledge domain this concept belongs to",
    )
    difficulty_tier: DifficultyTier = Field(
        ...,
        description="Difficulty level of this concept",
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="List of concept_ids that must be mastered before this one",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Human-readable title",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Detailed description of the concept",
    )
    estimated_minutes: int = Field(
        default=30,
        ge=5,
        le=480,
        description="Estimated learning time in minutes",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for filtering and organization",
    )

    @field_validator("prerequisites")
    @classmethod
    def validate_prerequisites(cls, v: list[str]) -> list[str]:
        """Ensure prerequisites follow the concept_id format."""
        import re
        pattern = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
        for prereq in v:
            if not pattern.match(prereq):
                raise ValueError(f"Invalid prerequisite format: {prereq}")
        return v

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags to lowercase."""
        return [tag.lower().strip() for tag in v if tag.strip()]

    def has_prerequisite(self, concept_id: str) -> bool:
        """Check if this concept requires a specific prerequisite."""
        return concept_id in self.prerequisites

    def is_beginner_friendly(self) -> bool:
        """Check if this concept is suitable for beginners."""
        return (
            self.difficulty_tier == DifficultyTier.BEGINNER
            and len(self.prerequisites) == 0
        )

    model_config = {
        "frozen": False,
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class KnowledgeComponentState(BaseModel):
    """
    Tracks the learner's mastery state for a single concept.

    Based on Bayesian Knowledge Tracing (BKT) principles:
    - mastery_level: P(L) - probability that the skill is learned
    - Updated based on learner interactions

    Attributes:
        concept_id: The concept this state tracks
        mastery_level: Current mastery probability [0.0, 1.0]
        last_accessed: When the learner last interacted with this concept
        practice_count: Number of practice attempts
        correct_count: Number of correct responses
        streak_current: Current streak of correct responses
        streak_best: Best streak achieved
    """

    concept_id: str = Field(
        ...,
        min_length=3,
        max_length=128,
        pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$",
        description="The concept this state tracks",
    )
    mastery_level: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Current mastery probability [0.0, 1.0]",
    )
    last_accessed: Optional[datetime] = Field(
        default=None,
        description="When the learner last interacted with this concept",
    )
    practice_count: int = Field(
        default=0,
        ge=0,
        description="Number of practice attempts",
    )
    correct_count: int = Field(
        default=0,
        ge=0,
        description="Number of correct responses",
    )
    streak_current: int = Field(
        default=0,
        ge=0,
        description="Current streak of correct responses",
    )
    streak_best: int = Field(
        default=0,
        ge=0,
        description="Best streak achieved",
    )

    @field_validator("correct_count")
    @classmethod
    def validate_correct_count(cls, v: int, info) -> int:
        """Ensure correct_count does not exceed practice_count."""
        if "practice_count" in info.data and v > info.data["practice_count"]:
            raise ValueError("correct_count cannot exceed practice_count")
        return v

    def accuracy(self) -> float:
        """Calculate the learner's accuracy for this concept."""
        if self.practice_count == 0:
            return 0.0
        return self.correct_count / self.practice_count

    def is_mastered(self, threshold: float = 0.70) -> bool:
        """Check if the concept is considered mastered."""
        return self.mastery_level >= threshold

    def is_stale(self, days: int = 7) -> bool:
        """Check if the concept needs review (not accessed recently)."""
        if self.last_accessed is None:
            return True
        delta = datetime.now() - self.last_accessed
        return delta.days >= days

    def record_attempt(self, correct: bool, timestamp: Optional[datetime] = None) -> "KnowledgeComponentState":
        """
        Record a practice attempt and return updated state.

        Uses a simple exponential moving average for mastery updates:
        - Correct: mastery increases toward 1.0
        - Incorrect: mastery decreases toward 0.0

        Args:
            correct: Whether the attempt was correct
            timestamp: When the attempt occurred (defaults to now)

        Returns:
            New KnowledgeComponentState with updated values
        """
        now = timestamp or datetime.now()
        learning_rate = 0.1

        new_mastery = self.mastery_level
        if correct:
            new_mastery = self.mastery_level + learning_rate * (1.0 - self.mastery_level)
            new_streak = self.streak_current + 1
        else:
            new_mastery = self.mastery_level - learning_rate * self.mastery_level
            new_streak = 0

        return KnowledgeComponentState(
            concept_id=self.concept_id,
            mastery_level=round(new_mastery, 4),
            last_accessed=now,
            practice_count=self.practice_count + 1,
            correct_count=self.correct_count + (1 if correct else 0),
            streak_current=new_streak,
            streak_best=max(self.streak_best, new_streak),
        )

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }


class LearnerProfile(BaseModel):
    """
    Aggregates knowledge state across all concepts for a learner.

    This is a domain entity that represents the learner's complete
    knowledge state, enabling personalized learning recommendations.

    Attributes:
        learner_id: Unique identifier for the learner
        knowledge_states: Mapping of concept_id to KnowledgeComponentState
        created_at: When the profile was created
        updated_at: When the profile was last updated
    """

    learner_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Unique identifier for the learner",
    )
    knowledge_states: dict[str, KnowledgeComponentState] = Field(
        default_factory=dict,
        description="Mapping of concept_id to knowledge state",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the profile was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When the profile was last updated",
    )

    def get_mastery(self, concept_id: str) -> float:
        """Get the mastery level for a specific concept."""
        if concept_id in self.knowledge_states:
            return self.knowledge_states[concept_id].mastery_level
        return 0.0

    def get_mastered_concepts(self, threshold: float = 0.70) -> list[str]:
        """Get list of concept_ids that are considered mastered."""
        return [
            concept_id
            for concept_id, state in self.knowledge_states.items()
            if state.is_mastered(threshold)
        ]

    def get_stale_concepts(self, days: int = 7) -> list[str]:
        """Get list of concept_ids that need review."""
        return [
            concept_id
            for concept_id, state in self.knowledge_states.items()
            if state.is_stale(days)
        ]

    def overall_mastery(self) -> float:
        """Calculate average mastery across all tracked concepts."""
        if not self.knowledge_states:
            return 0.0
        total = sum(state.mastery_level for state in self.knowledge_states.values())
        return total / len(self.knowledge_states)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
