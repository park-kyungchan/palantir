"""
Zone of Proximal Development (ZPD) Scoping Engine

This module implements the core recommendation logic for the learning system.
Based on Vygotsky's Zone of Proximal Development theory:

- ZPD is the difference between what a learner can do without help
  and what they can do with guidance
- Optimal learning occurs when challenges are slightly beyond current ability
- We target the "stretch zone" - not too easy, not too hard

Key Parameters:
- OPTIMAL_STRETCH_MIN (0.10): Minimum stretch for engagement
- OPTIMAL_STRETCH_MAX (0.30): Maximum stretch before frustration
- MASTERY_THRESHOLD (0.70): When a concept is considered "learned"

Algorithm:
1. Filter concepts where prerequisites are mastered
2. Calculate "stretch" = difficulty - current_mastery
3. Select concepts in optimal stretch range
4. Rank by relevance and learning path coherence
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from palantir_fde_learning.domain.types import (
    DifficultyTier,
    KnowledgeComponentState,
    LearnerProfile,
    LearningConcept,
)

# ZPD Configuration Constants
OPTIMAL_STRETCH_MIN: float = 0.10  # Minimum stretch for engagement
OPTIMAL_STRETCH_MAX: float = 0.30  # Maximum stretch before frustration
MASTERY_THRESHOLD: float = 0.70   # When a concept is considered mastered


class ZPDRecommendation(BaseModel):
    """
    Represents a recommended learning concept with ZPD analysis.

    Attributes:
        concept: The recommended LearningConcept
        stretch_factor: How much this concept stretches the learner
        readiness_score: How ready the learner is for this concept
        rationale: Human-readable explanation for the recommendation
        priority: Ranking priority (lower = higher priority)
    """

    concept: LearningConcept = Field(
        ...,
        description="The recommended learning concept",
    )
    stretch_factor: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How much this concept stretches the learner",
    )
    readiness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How ready the learner is (prerequisite mastery)",
    )
    rationale: str = Field(
        ...,
        description="Human-readable explanation for recommendation",
    )
    priority: int = Field(
        default=0,
        ge=0,
        description="Ranking priority (lower = higher priority)",
    )

    def is_in_zpd(self) -> bool:
        """Check if this recommendation falls within the ZPD."""
        return OPTIMAL_STRETCH_MIN <= self.stretch_factor <= OPTIMAL_STRETCH_MAX

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }


class ScopingEngine:
    """
    Zone of Proximal Development (ZPD) Scoping Engine.

    This engine recommends the next concept to learn based on:
    1. Prerequisite mastery
    2. Optimal stretch factor
    3. Learning path coherence
    4. Time since last interaction

    Example usage:
        engine = ScopingEngine(
            concepts=concept_library,
            learner_profile=profile
        )
        recommendations = engine.recommend_next_concept(limit=3)
    """

    def __init__(
        self,
        concepts: list[LearningConcept],
        learner_profile: LearnerProfile,
        stretch_min: float = OPTIMAL_STRETCH_MIN,
        stretch_max: float = OPTIMAL_STRETCH_MAX,
        mastery_threshold: float = MASTERY_THRESHOLD,
    ):
        """
        Initialize the scoping engine.

        Args:
            concepts: Library of all available learning concepts
            learner_profile: The learner's current knowledge state
            stretch_min: Minimum stretch factor for recommendations
            stretch_max: Maximum stretch factor for recommendations
            mastery_threshold: Threshold for considering a concept mastered
        """
        self.concepts = concepts
        self.learner_profile = learner_profile
        self.stretch_min = stretch_min
        self.stretch_max = stretch_max
        self.mastery_threshold = mastery_threshold

        # Build concept lookup for efficient prerequisite checking
        self._concept_map: dict[str, LearningConcept] = {
            c.concept_id: c for c in concepts
        }

    def _calculate_prerequisite_readiness(self, concept: LearningConcept) -> float:
        """
        Calculate how ready the learner is based on prerequisites.

        Returns 1.0 if all prerequisites are mastered, 0.0 if none are.
        """
        if not concept.prerequisites:
            return 1.0

        mastered_count = 0
        for prereq_id in concept.prerequisites:
            mastery = self.learner_profile.get_mastery(prereq_id)
            if mastery >= self.mastery_threshold:
                mastered_count += 1

        return mastered_count / len(concept.prerequisites)

    def _calculate_stretch_factor(self, concept: LearningConcept) -> float:
        """
        Calculate the stretch factor for a concept.

        Stretch = difficulty_normalized - current_mastery

        Difficulty is normalized:
        - BEGINNER: 0.33
        - INTERMEDIATE: 0.66
        - ADVANCED: 1.0
        """
        difficulty_map = {
            DifficultyTier.BEGINNER: 0.33,
            DifficultyTier.INTERMEDIATE: 0.66,
            DifficultyTier.ADVANCED: 1.0,
        }

        difficulty_normalized = difficulty_map[concept.difficulty_tier]
        current_mastery = self.learner_profile.get_mastery(concept.concept_id)

        # Stretch is how much harder this is than what they know
        stretch = max(0.0, difficulty_normalized - current_mastery)
        return min(1.0, stretch)

    def _is_concept_eligible(self, concept: LearningConcept) -> bool:
        """
        Check if a concept is eligible for recommendation.

        Eligibility criteria:
        1. Not already mastered
        2. All prerequisites are at least partially known
        """
        # Skip already mastered concepts
        current_mastery = self.learner_profile.get_mastery(concept.concept_id)
        if current_mastery >= self.mastery_threshold:
            return False

        # Check prerequisite readiness (at least 70% ready)
        readiness = self._calculate_prerequisite_readiness(concept)
        if readiness < 0.7:
            return False

        return True

    def _generate_rationale(
        self,
        concept: LearningConcept,
        stretch: float,
        readiness: float,
    ) -> str:
        """Generate a human-readable rationale for the recommendation."""
        parts = []

        # Stretch explanation
        if stretch < self.stretch_min:
            parts.append("This concept is close to your current level")
        elif stretch <= self.stretch_max:
            parts.append("This concept is in your optimal learning zone")
        else:
            parts.append("This concept will be challenging")

        # Readiness explanation
        if readiness >= 1.0:
            parts.append("all prerequisites are mastered")
        elif readiness >= 0.7:
            parts.append("most prerequisites are mastered")
        else:
            parts.append("some prerequisite knowledge may need review")

        # Tier context
        tier_context = {
            DifficultyTier.BEGINNER: "foundational concept",
            DifficultyTier.INTERMEDIATE: "intermediate skill-building",
            DifficultyTier.ADVANCED: "advanced mastery topic",
        }
        parts.append(f"({tier_context[concept.difficulty_tier]})")

        return "; ".join(parts)

    def recommend_next_concept(
        self,
        limit: int = 3,
        domain_filter: Optional[str] = None,
        include_review: bool = True,
    ) -> list[ZPDRecommendation]:
        """
        Recommend the next concepts to learn based on ZPD analysis.

        The algorithm:
        1. Filter to eligible concepts (not mastered, prerequisites met)
        2. Calculate stretch factor for each
        3. Prioritize concepts in optimal ZPD range
        4. Optionally include stale concepts for review
        5. Return top N recommendations

        Args:
            limit: Maximum number of recommendations to return
            domain_filter: Optional domain to filter by
            include_review: Whether to include stale concepts for review

        Returns:
            List of ZPDRecommendation objects, sorted by priority
        """
        candidates: list[ZPDRecommendation] = []

        for concept in self.concepts:
            # Apply domain filter if specified
            if domain_filter and concept.domain.value != domain_filter:
                continue

            # Check eligibility
            if not self._is_concept_eligible(concept):
                continue

            # Calculate metrics
            stretch = self._calculate_stretch_factor(concept)
            readiness = self._calculate_prerequisite_readiness(concept)
            rationale = self._generate_rationale(concept, stretch, readiness)

            # Calculate priority (lower = better)
            # Prioritize concepts in ZPD, with higher readiness
            if self.stretch_min <= stretch <= self.stretch_max:
                priority = 0  # Optimal ZPD
            elif stretch < self.stretch_min:
                priority = 1  # Slightly too easy
            else:
                priority = 2  # Slightly too hard

            # Adjust priority by readiness
            priority_adjustment = int((1.0 - readiness) * 10)
            priority += priority_adjustment

            recommendation = ZPDRecommendation(
                concept=concept,
                stretch_factor=round(stretch, 3),
                readiness_score=round(readiness, 3),
                rationale=rationale,
                priority=priority,
            )
            candidates.append(recommendation)

        # Add stale concepts for review if requested
        if include_review:
            stale_ids = self.learner_profile.get_stale_concepts(days=7)
            for concept_id in stale_ids:
                if concept_id in self._concept_map:
                    concept = self._concept_map[concept_id]
                    current_mastery = self.learner_profile.get_mastery(concept_id)

                    # Only recommend review for partially learned concepts
                    if 0.3 <= current_mastery < self.mastery_threshold:
                        review_rec = ZPDRecommendation(
                            concept=concept,
                            stretch_factor=0.05,  # Review is low stretch
                            readiness_score=1.0,
                            rationale="Review recommended - concept needs reinforcement",
                            priority=0,  # High priority for review
                        )
                        # Avoid duplicates
                        if not any(c.concept.concept_id == concept_id for c in candidates):
                            candidates.append(review_rec)

        # Sort by priority (lower = better) and return top N
        candidates.sort(key=lambda r: (r.priority, -r.readiness_score))
        return candidates[:limit]

    def get_learning_path(
        self,
        target_concept_id: str,
        max_depth: int = 10,
    ) -> list[LearningConcept]:
        """
        Generate a learning path to reach a target concept.

        Uses topological sorting to order prerequisites,
        ensuring the learner builds up to the target.

        Args:
            target_concept_id: The concept to reach
            max_depth: Maximum depth of prerequisite chain

        Returns:
            Ordered list of concepts to learn
        """
        if target_concept_id not in self._concept_map:
            return []

        target = self._concept_map[target_concept_id]
        path: list[LearningConcept] = []
        visited: set[str] = set()

        def visit(concept_id: str, depth: int) -> None:
            if depth > max_depth or concept_id in visited:
                return

            visited.add(concept_id)

            if concept_id not in self._concept_map:
                return

            concept = self._concept_map[concept_id]

            # Visit prerequisites first
            for prereq_id in concept.prerequisites:
                visit(prereq_id, depth + 1)

            # Skip already mastered concepts
            mastery = self.learner_profile.get_mastery(concept_id)
            if mastery < self.mastery_threshold:
                path.append(concept)

        visit(target_concept_id, 0)
        return path

    def get_domain_progress(self, domain: str) -> dict[str, float]:
        """
        Calculate learning progress for a specific domain.

        Returns:
            Dict with mastery statistics for the domain
        """
        domain_concepts = [c for c in self.concepts if c.domain.value == domain]

        if not domain_concepts:
            return {
                "total_concepts": 0,
                "mastered_count": 0,
                "in_progress_count": 0,
                "not_started_count": 0,
                "overall_mastery": 0.0,
            }

        mastered = 0
        in_progress = 0
        not_started = 0
        total_mastery = 0.0

        for concept in domain_concepts:
            mastery = self.learner_profile.get_mastery(concept.concept_id)
            total_mastery += mastery

            if mastery >= self.mastery_threshold:
                mastered += 1
            elif mastery > 0:
                in_progress += 1
            else:
                not_started += 1

        return {
            "total_concepts": len(domain_concepts),
            "mastered_count": mastered,
            "in_progress_count": in_progress,
            "not_started_count": not_started,
            "overall_mastery": round(total_mastery / len(domain_concepts), 3),
        }
