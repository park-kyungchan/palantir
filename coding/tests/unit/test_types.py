# tests/unit/test_types.py
"""
Unit tests for domain types.

Tests:
- DifficultyTier enum methods
- KnowledgeComponentState mastery tracking
- LearnerProfile aggregation
- LearningConcept validation
"""
import pytest
from datetime import datetime, timedelta

from palantir_fde_learning.domain.types import (
    DifficultyTier,
    LearningDomain,
    LearningConcept,
    KnowledgeComponentState,
    LearnerProfile,
)


class TestDifficultyTier:
    """Test DifficultyTier enum conversions."""

    def test_to_numeric_beginner(self):
        assert DifficultyTier.BEGINNER.to_numeric() == 1

    def test_to_numeric_intermediate(self):
        assert DifficultyTier.INTERMEDIATE.to_numeric() == 2

    def test_to_numeric_advanced(self):
        assert DifficultyTier.ADVANCED.to_numeric() == 3

    def test_from_numeric_valid(self):
        assert DifficultyTier.from_numeric(1) == DifficultyTier.BEGINNER
        assert DifficultyTier.from_numeric(2) == DifficultyTier.INTERMEDIATE
        assert DifficultyTier.from_numeric(3) == DifficultyTier.ADVANCED

    def test_from_numeric_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid tier numeric value"):
            DifficultyTier.from_numeric(5)

    def test_from_numeric_zero_raises(self):
        with pytest.raises(ValueError):
            DifficultyTier.from_numeric(0)


class TestLearningConcept:
    """Test LearningConcept validation and methods."""

    def test_create_valid_concept(self, sample_concept):
        assert sample_concept.concept_id == "osdk.beginner.installation"
        assert sample_concept.domain == LearningDomain.OSDK
        assert sample_concept.difficulty_tier == DifficultyTier.BEGINNER

    def test_invalid_concept_id_format(self):
        with pytest.raises(ValueError):
            LearningConcept(
                concept_id="INVALID_UPPERCASE",  # Must be lowercase
                domain=LearningDomain.OSDK,
                difficulty_tier=DifficultyTier.BEGINNER,
                title="Test",
            )

    def test_is_beginner_friendly_no_prereqs(self, sample_concept):
        assert sample_concept.is_beginner_friendly() is True

    def test_is_beginner_friendly_with_prereqs(self, intermediate_concept):
        assert intermediate_concept.is_beginner_friendly() is False

    def test_has_prerequisite(self, intermediate_concept):
        assert intermediate_concept.has_prerequisite("osdk.beginner.installation") is True
        assert intermediate_concept.has_prerequisite("nonexistent") is False

    def test_tag_normalization(self):
        concept = LearningConcept(
            concept_id="test.concept",
            domain=LearningDomain.FOUNDRY,
            difficulty_tier=DifficultyTier.BEGINNER,
            title="Test",
            tags=["  UPPERCASE  ", "mixed Case", "lowercase"],
        )
        assert concept.tags == ["uppercase", "mixed case", "lowercase"]


class TestKnowledgeComponentState:
    """Test KnowledgeComponentState BKT tracking."""

    def test_initial_state(self, sample_state):
        assert sample_state.mastery_level == 0.0
        assert sample_state.practice_count == 0
        assert sample_state.streak_current == 0

    def test_record_correct_attempt(self, sample_state):
        new_state = sample_state.record_attempt(correct=True)
        assert new_state.mastery_level > 0
        assert new_state.practice_count == 1
        assert new_state.correct_count == 1
        assert new_state.streak_current == 1

    def test_record_incorrect_attempt(self, mastered_state):
        new_state = mastered_state.record_attempt(correct=False)
        assert new_state.mastery_level < mastered_state.mastery_level
        assert new_state.streak_current == 0

    def test_accuracy_calculation(self, mastered_state):
        accuracy = mastered_state.accuracy()
        assert accuracy == 0.9  # 9/10 correct

    def test_accuracy_zero_attempts(self, sample_state):
        assert sample_state.accuracy() == 0.0

    def test_is_mastered_threshold(self):
        state_75 = KnowledgeComponentState(concept_id="test", mastery_level=0.75)
        state_65 = KnowledgeComponentState(concept_id="test", mastery_level=0.65)
        
        assert state_75.is_mastered(threshold=0.70) is True
        assert state_65.is_mastered(threshold=0.70) is False

    def test_is_stale_never_accessed(self, sample_state):
        assert sample_state.is_stale(days=7) is True

    def test_is_stale_recent(self, mastered_state):
        # mastered_state has last_accessed = now
        assert mastered_state.is_stale(days=7) is False

    def test_is_stale_old(self):
        old_date = datetime.now() - timedelta(days=10)
        state = KnowledgeComponentState(
            concept_id="test",
            mastery_level=0.5,
            last_accessed=old_date,
        )
        assert state.is_stale(days=7) is True


class TestLearnerProfile:
    """Test LearnerProfile aggregation methods."""

    def test_empty_profile(self, sample_profile):
        assert sample_profile.overall_mastery() == 0.0
        assert sample_profile.get_mastered_concepts() == []

    def test_get_mastery_existing(self, profile_with_mastery):
        mastery = profile_with_mastery.get_mastery("osdk.beginner.installation")
        assert mastery == 0.80

    def test_get_mastery_nonexistent(self, sample_profile):
        mastery = sample_profile.get_mastery("nonexistent")
        assert mastery == 0.0

    def test_get_mastered_concepts(self, profile_with_mastery):
        mastered = profile_with_mastery.get_mastered_concepts(threshold=0.70)
        assert "osdk.beginner.installation" in mastered

    def test_overall_mastery_calculation(self):
        state1 = KnowledgeComponentState(concept_id="concept.a", mastery_level=0.5)
        state2 = KnowledgeComponentState(concept_id="concept.b", mastery_level=0.7)
        profile = LearnerProfile(
            learner_id="test",
            knowledge_states={"concept.a": state1, "concept.b": state2},
        )
        assert profile.overall_mastery() == 0.6  # (0.5 + 0.7) / 2
