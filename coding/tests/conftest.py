# tests/conftest.py
"""
Shared pytest fixtures for Palantir FDE Learning System tests.
"""
import pytest
from datetime import datetime

from palantir_fde_learning.domain.types import (
    LearningConcept,
    LearnerProfile,
    KnowledgeComponentState,
    DifficultyTier,
    LearningDomain,
)


@pytest.fixture
def sample_concept() -> LearningConcept:
    """A beginner-level OSDK concept with no prerequisites."""
    return LearningConcept(
        concept_id="osdk.beginner.installation",
        domain=LearningDomain.OSDK,
        difficulty_tier=DifficultyTier.BEGINNER,
        title="OSDK Installation",
        description="How to install the Ontology SDK",
        prerequisites=[],
    )


@pytest.fixture
def intermediate_concept() -> LearningConcept:
    """An intermediate concept with prerequisites."""
    return LearningConcept(
        concept_id="osdk.intermediate.queries",
        domain=LearningDomain.OSDK,
        difficulty_tier=DifficultyTier.INTERMEDIATE,
        title="OSDK Queries",
        description="Advanced querying with OSDK",
        prerequisites=["osdk.beginner.installation"],
    )


@pytest.fixture
def sample_state() -> KnowledgeComponentState:
    """A fresh knowledge state with no mastery."""
    return KnowledgeComponentState(concept_id="osdk.beginner.installation")


@pytest.fixture
def mastered_state() -> KnowledgeComponentState:
    """A knowledge state with high mastery."""
    return KnowledgeComponentState(
        concept_id="osdk.beginner.installation",
        mastery_level=0.85,
        practice_count=10,
        correct_count=9,
        streak_current=5,
        streak_best=7,
        last_accessed=datetime.now(),
    )


@pytest.fixture
def sample_profile() -> LearnerProfile:
    """An empty learner profile."""
    return LearnerProfile(learner_id="test_user")


@pytest.fixture
def profile_with_mastery() -> LearnerProfile:
    """A learner profile with some mastered concepts."""
    state = KnowledgeComponentState(
        concept_id="osdk.beginner.installation",
        mastery_level=0.80,
        practice_count=5,
        correct_count=4,
    )
    return LearnerProfile(
        learner_id="advanced_user",
        knowledge_states={"osdk.beginner.installation": state},
    )
