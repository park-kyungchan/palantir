# tests/unit/test_scoping.py
"""
Unit tests for the ZPD Scoping Engine.

Tests:
- Stretch factor calculation
- Prerequisite readiness
- Recommendation generation
- Learning path construction
"""
import pytest
from palantir_fde_learning.application.scoping import (
    ScopingEngine,
    ZPDRecommendation,
    OPTIMAL_STRETCH_MIN,
    OPTIMAL_STRETCH_MAX,
    MASTERY_THRESHOLD,
)
from palantir_fde_learning.domain.types import (
    LearningConcept,
    LearnerProfile,
    KnowledgeComponentState,
    DifficultyTier,
    LearningDomain,
)


@pytest.fixture
def concept_library():
    """A small library of concepts for testing."""
    return [
        LearningConcept(
            concept_id="osdk.beginner.intro",
            domain=LearningDomain.OSDK,
            difficulty_tier=DifficultyTier.BEGINNER,
            title="OSDK Introduction",
            prerequisites=[],
        ),
        LearningConcept(
            concept_id="osdk.beginner.install",
            domain=LearningDomain.OSDK,
            difficulty_tier=DifficultyTier.BEGINNER,
            title="OSDK Installation",
            prerequisites=["osdk.beginner.intro"],
        ),
        LearningConcept(
            concept_id="osdk.intermediate.queries",
            domain=LearningDomain.OSDK,
            difficulty_tier=DifficultyTier.INTERMEDIATE,
            title="OSDK Queries",
            prerequisites=["osdk.beginner.install"],
        ),
        LearningConcept(
            concept_id="osdk.advanced.optimization",
            domain=LearningDomain.OSDK,
            difficulty_tier=DifficultyTier.ADVANCED,
            title="Query Optimization",
            prerequisites=["osdk.intermediate.queries"],
        ),
    ]


@pytest.fixture
def empty_profile():
    """A learner with no progress."""
    return LearnerProfile(learner_id="beginner")


@pytest.fixture
def partial_profile():
    """A learner with some mastery."""
    states = {
        "osdk.beginner.intro": KnowledgeComponentState(
            concept_id="osdk.beginner.intro",
            mastery_level=0.80,
        ),
    }
    return LearnerProfile(learner_id="partial", knowledge_states=states)


class TestZPDRecommendation:
    """Test ZPDRecommendation model."""

    def test_is_in_zpd_true(self, sample_concept):
        rec = ZPDRecommendation(
            concept=sample_concept,
            stretch_factor=0.20,  # Within 0.10-0.30
            readiness_score=1.0,
            rationale="Test",
        )
        assert rec.is_in_zpd() is True

    def test_is_in_zpd_too_easy(self, sample_concept):
        rec = ZPDRecommendation(
            concept=sample_concept,
            stretch_factor=0.05,  # Below 0.10
            readiness_score=1.0,
            rationale="Test",
        )
        assert rec.is_in_zpd() is False

    def test_is_in_zpd_too_hard(self, sample_concept):
        rec = ZPDRecommendation(
            concept=sample_concept,
            stretch_factor=0.50,  # Above 0.30
            readiness_score=1.0,
            rationale="Test",
        )
        assert rec.is_in_zpd() is False


class TestScopingEngine:
    """Test ScopingEngine recommendation logic."""

    def test_init_builds_concept_map(self, concept_library, empty_profile):
        engine = ScopingEngine(concept_library, empty_profile)
        assert len(engine._concept_map) == 4
        assert "osdk.beginner.intro" in engine._concept_map

    def test_prerequisite_readiness_no_prereqs(self, concept_library, empty_profile):
        engine = ScopingEngine(concept_library, empty_profile)
        intro = engine._concept_map["osdk.beginner.intro"]
        readiness = engine._calculate_prerequisite_readiness(intro)
        assert readiness == 1.0  # No prereqs = fully ready

    def test_prerequisite_readiness_unmet(self, concept_library, empty_profile):
        engine = ScopingEngine(concept_library, empty_profile)
        install = engine._concept_map["osdk.beginner.install"]
        readiness = engine._calculate_prerequisite_readiness(install)
        assert readiness == 0.0  # Prereq not mastered

    def test_prerequisite_readiness_met(self, concept_library, partial_profile):
        engine = ScopingEngine(concept_library, partial_profile)
        install = engine._concept_map["osdk.beginner.install"]
        readiness = engine._calculate_prerequisite_readiness(install)
        assert readiness == 1.0  # Prereq is mastered (0.80 >= 0.70)

    def test_stretch_factor_beginner(self, concept_library, empty_profile):
        engine = ScopingEngine(concept_library, empty_profile)
        intro = engine._concept_map["osdk.beginner.intro"]
        stretch = engine._calculate_stretch_factor(intro)
        assert stretch == 0.33  # BEGINNER normalized difficulty

    def test_recommend_next_concept_empty_profile(self, concept_library, empty_profile):
        engine = ScopingEngine(concept_library, empty_profile)
        recs = engine.recommend_next_concept(limit=3)
        
        # Should recommend intro first (only one with no prereqs)
        assert len(recs) >= 1
        assert recs[0].concept.concept_id == "osdk.beginner.intro"

    def test_recommend_filters_mastered(self, concept_library, partial_profile):
        engine = ScopingEngine(concept_library, partial_profile)
        recs = engine.recommend_next_concept(limit=5)
        
        # Should NOT recommend already mastered concepts
        concept_ids = [r.concept.concept_id for r in recs]
        assert "osdk.beginner.intro" not in concept_ids

    def test_recommend_domain_filter(self, concept_library, empty_profile):
        # Add a concept from different domain
        blueprint_concept = LearningConcept(
            concept_id="blueprint.beginner.intro",
            domain=LearningDomain.BLUEPRINT,
            difficulty_tier=DifficultyTier.BEGINNER,
            title="Blueprint Intro",
            prerequisites=[],
        )
        library = concept_library + [blueprint_concept]
        engine = ScopingEngine(library, empty_profile)
        
        recs = engine.recommend_next_concept(limit=5, domain_filter="blueprint")
        assert all(r.concept.domain == LearningDomain.BLUEPRINT for r in recs)

    def test_get_learning_path(self, concept_library, empty_profile):
        engine = ScopingEngine(concept_library, empty_profile)
        path = engine.get_learning_path("osdk.advanced.optimization")
        
        # Path should include all prerequisites in order
        assert len(path) == 4
        path_ids = [c.concept_id for c in path]
        assert path_ids.index("osdk.beginner.intro") < path_ids.index("osdk.beginner.install")

    def test_get_domain_progress_empty(self, concept_library, empty_profile):
        engine = ScopingEngine(concept_library, empty_profile)
        progress = engine.get_domain_progress("osdk")
        
        assert progress["total_concepts"] == 4
        assert progress["mastered_count"] == 0
        assert progress["not_started_count"] == 4

    def test_get_domain_progress_partial(self, concept_library, partial_profile):
        engine = ScopingEngine(concept_library, partial_profile)
        progress = engine.get_domain_progress("osdk")
        
        assert progress["mastered_count"] == 1
        assert progress["not_started_count"] == 3
