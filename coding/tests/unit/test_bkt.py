# tests/unit/test_bkt.py
"""
Unit tests for Bayesian Knowledge Tracing implementation.

Tests cover:
- Parameter validation
- Mastery updates (correct/incorrect responses)
- Convergence to mastery
- Edge cases and boundary conditions
"""
import pytest
from palantir_fde_learning.domain.bkt import (
    BKTParameters,
    BKTState,
    BKTModel,
    get_bkt_model,
    PARAMETER_PRESETS,
)


class TestBKTParameters:
    """Test BKT parameter validation."""

    def test_default_parameters(self):
        """Test default parameters are valid."""
        params = BKTParameters()
        assert 0 <= params.p_init <= 1
        assert 0 <= params.p_learn <= 1
        assert 0 <= params.p_slip <= 1
        assert 0 <= params.p_guess <= 1

    def test_invalid_probability_raises(self):
        """Test that invalid probabilities raise ValueError."""
        with pytest.raises(ValueError, match="p_init"):
            BKTParameters(p_init=-0.1)
        
        with pytest.raises(ValueError, match="p_learn"):
            BKTParameters(p_learn=1.5)

    def test_identifiability_constraint(self):
        """Test that P(G) + P(S) < 1 is enforced."""
        with pytest.raises(ValueError, match="identifiable"):
            BKTParameters(p_slip=0.5, p_guess=0.5)


class TestBKTState:
    """Test BKT state management."""

    def test_initial_state(self):
        """Test default state values."""
        state = BKTState()
        assert state.mastery == 0.0
        assert state.attempts == 0
        assert state.correct == 0
        assert state.history == []

    def test_accuracy_calculation(self):
        """Test accuracy property."""
        state = BKTState(attempts=10, correct=7)
        assert state.accuracy == 0.7

    def test_accuracy_zero_attempts(self):
        """Test accuracy with no attempts."""
        state = BKTState()
        assert state.accuracy == 0.0

    def test_is_mastered_threshold(self):
        """Test mastery threshold (0.95)."""
        state = BKTState(mastery=0.94)
        assert not state.is_mastered
        
        state = BKTState(mastery=0.95)
        assert state.is_mastered


class TestBKTModel:
    """Test BKT model operations."""

    def test_update_after_correct(self):
        """Test mastery increases after correct response."""
        model = BKTModel()
        state = BKTState()
        
        new_state = model.update(state, correct=True)
        
        assert new_state.mastery > state.mastery
        assert new_state.attempts == 1
        assert new_state.correct == 1
        assert new_state.history == [True]

    def test_update_after_incorrect(self):
        """Test mastery still increases (due to learning) but less than correct."""
        model = BKTModel()
        state = BKTState(mastery=0.5, attempts=5, correct=3)
        
        # Incorrect response
        after_incorrect = model.update(state, correct=False)
        
        # Reset and try correct
        after_correct = model.update(state, correct=True)
        
        # Mastery after correct should be higher than after incorrect
        assert after_correct.mastery > after_incorrect.mastery

    def test_convergence_to_mastery(self):
        """Test that repeated correct answers lead to mastery."""
        model = BKTModel()
        state = BKTState()
        
        # Simulate 20 correct answers
        for _ in range(20):
            state = model.update(state, correct=True)
        
        assert state.is_mastered
        assert state.mastery > 0.95

    def test_predict_correct(self):
        """Test correct prediction probability."""
        model = BKTModel()
        
        # Low mastery -> low probability
        low_state = BKTState(mastery=0.1)
        p_low = model.predict_correct(low_state)
        
        # High mastery -> high probability
        high_state = BKTState(mastery=0.9, attempts=1)
        p_high = model.predict_correct(high_state)
        
        assert p_high > p_low

    def test_expected_attempts_mastered(self):
        """Test expected attempts when already mastered."""
        model = BKTModel()
        state = BKTState(mastery=0.98)
        
        assert model.expected_attempts_to_mastery(state) == 0


class TestParameterPresets:
    """Test pre-configured parameter sets."""

    def test_all_presets_valid(self):
        """Test all presets create valid models."""
        for name in PARAMETER_PRESETS:
            model = get_bkt_model(name)
            assert isinstance(model, BKTModel)

    def test_unknown_preset_raises(self):
        """Test that unknown preset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown preset"):
            get_bkt_model("nonexistent")

    def test_interview_preset_stricter(self):
        """Test interview preset has lower guess rate."""
        interview = PARAMETER_PRESETS["interview"]
        default = PARAMETER_PRESETS["default"]
        
        assert interview.p_guess < default.p_guess
