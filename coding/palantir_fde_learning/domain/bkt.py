# domain/bkt.py
"""
Bayesian Knowledge Tracing (BKT) Implementation.

This module implements the standard BKT algorithm for mastery estimation,
following the original Corbett & Anderson (1994) formulation.

BKT Models Knowledge as a Hidden Markov Model:
- Hidden State: Mastered (L) or Unlearned (1-L)
- Observations: Correct (1) or Incorrect (0) responses

Parameters:
- P(L0): Initial probability of mastery (prior)
- P(T): Probability of learning on each attempt (transition)
- P(S): Probability of "slip" (incorrect despite mastery)
- P(G): Probability of "guess" (correct despite no mastery)

The algorithm updates mastery probability after each observation using
Bayesian inference.

References:
- Corbett, A.T., & Anderson, J.R. (1994). Knowledge tracing: Modeling the
  acquisition of procedural knowledge. User modeling and user-adapted
  interaction, 4(4), 253-278.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import math


@dataclass
class BKTParameters:
    """
    BKT model parameters.
    
    All probabilities must be in [0, 1].
    Default values are based on typical educational settings.
    """
    p_init: float = 0.0      # P(L0): Initial mastery probability
    p_learn: float = 0.1     # P(T): Learning rate per attempt
    p_slip: float = 0.1      # P(S): Slip probability
    p_guess: float = 0.25    # P(G): Guess probability
    
    def __post_init__(self):
        """Validate parameters are valid probabilities."""
        for name, value in [
            ("p_init", self.p_init),
            ("p_learn", self.p_learn),
            ("p_slip", self.p_slip),
            ("p_guess", self.p_guess),
        ]:
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be in [0, 1], got {value}")
        
        # Validate identifiability constraint
        if self.p_guess + self.p_slip >= 1:
            raise ValueError(
                "Model not identifiable: P(G) + P(S) must be < 1. "
                f"Got P(G)={self.p_guess}, P(S)={self.p_slip}"
            )


@dataclass
class BKTState:
    """
    BKT state for a single knowledge component.
    
    Tracks the current mastery probability and observation history.
    """
    mastery: float = 0.0
    attempts: int = 0
    correct: int = 0
    history: List[bool] = field(default_factory=list)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy rate."""
        if self.attempts == 0:
            return 0.0
        return self.correct / self.attempts
    
    @property
    def is_mastered(self) -> bool:
        """Check if mastery threshold is reached (0.95 is standard)."""
        return self.mastery >= 0.95
    

class BKTModel:
    """
    Bayesian Knowledge Tracing model.
    
    Example usage:
        >>> params = BKTParameters(p_init=0.0, p_learn=0.1, p_slip=0.1, p_guess=0.25)
        >>> bkt = BKTModel(params)
        >>> state = BKTState()
        >>> state = bkt.update(state, correct=True)
        >>> print(f"Mastery: {state.mastery:.2%}")
    """
    
    def __init__(self, params: Optional[BKTParameters] = None):
        """Initialize BKT model with parameters."""
        self.params = params or BKTParameters()
    
    def update(self, state: BKTState, correct: bool) -> BKTState:
        """
        Update mastery estimate after an observation.
        
        This implements the standard BKT update equations:
        
        1. P(L_n | correct) = P(correct | L_n) * P(L_n) / P(correct)
           where:
           - P(correct | L_n) = (1 - P_slip) if mastered, P_guess if not
           - P(correct) = P(L_n) * (1 - P_slip) + (1 - P(L_n)) * P_guess
        
        2. P(L_{n+1}) = P(L_n | obs) + (1 - P(L_n | obs)) * P_learn
        
        Args:
            state: Current BKT state
            correct: Whether the response was correct
            
        Returns:
            Updated BKT state
        """
        p = self.params
        L = state.mastery if state.attempts > 0 else p.p_init
        
        # Step 1: Compute P(L_n | observation) using Bayes' theorem
        if correct:
            # P(correct | L) = 1 - P_slip
            # P(correct | ~L) = P_guess
            p_correct_given_L = 1 - p.p_slip
            p_correct_given_not_L = p.p_guess
            
            # P(correct) = L * P(correct|L) + (1-L) * P(correct|~L)
            p_correct = L * p_correct_given_L + (1 - L) * p_correct_given_not_L
            
            # P(L | correct) = P(correct | L) * P(L) / P(correct)
            if p_correct > 0:
                L_given_obs = (p_correct_given_L * L) / p_correct
            else:
                L_given_obs = L
        else:
            # P(incorrect | L) = P_slip
            # P(incorrect | ~L) = 1 - P_guess
            p_incorrect_given_L = p.p_slip
            p_incorrect_given_not_L = 1 - p.p_guess
            
            # P(incorrect) = L * P(incorrect|L) + (1-L) * P(incorrect|~L)
            p_incorrect = L * p_incorrect_given_L + (1 - L) * p_incorrect_given_not_L
            
            # P(L | incorrect) = P(incorrect | L) * P(L) / P(incorrect)
            if p_incorrect > 0:
                L_given_obs = (p_incorrect_given_L * L) / p_incorrect
            else:
                L_given_obs = L
        
        # Step 2: Apply learning transition
        # P(L_{n+1}) = P(L_n | obs) + (1 - P(L_n | obs)) * P_learn
        new_mastery = L_given_obs + (1 - L_given_obs) * p.p_learn
        
        # Clamp to valid range
        new_mastery = max(0.0, min(1.0, new_mastery))
        
        # Update state
        return BKTState(
            mastery=new_mastery,
            attempts=state.attempts + 1,
            correct=state.correct + (1 if correct else 0),
            history=state.history + [correct],
        )
    
    def predict_correct(self, state: BKTState) -> float:
        """
        Predict probability of correct response.
        
        P(correct) = P(L) * (1 - P_slip) + (1 - P(L)) * P_guess
        """
        p = self.params
        L = state.mastery if state.attempts > 0 else p.p_init
        return L * (1 - p.p_slip) + (1 - L) * p.p_guess
    
    def expected_attempts_to_mastery(self, state: BKTState) -> Optional[int]:
        """
        Estimate attempts needed to reach mastery threshold.
        
        Uses geometric model: E[attempts] ≈ log(1-0.95) / log(1 - P_learn)
        """
        if state.is_mastered:
            return 0
        
        p = self.params
        if p.p_learn <= 0:
            return None  # Will never learn
        
        # How many successful learning transitions needed?
        target = 0.95
        L = state.mastery
        
        if L >= target:
            return 0
        
        # Solve: L + (1-L)(1-(1-p_learn)^n) >= target
        # Simplified: estimate using learning rate only
        remaining = (target - L) / (1 - L)
        if remaining <= 0:
            return 0
        
        try:
            attempts = math.ceil(math.log(1 - remaining) / math.log(1 - p.p_learn))
            return max(1, attempts)
        except (ValueError, ZeroDivisionError):
            return None


# Pre-configured parameter sets for different learning contexts
PARAMETER_PRESETS = {
    # Default balanced parameters
    "default": BKTParameters(p_init=0.0, p_learn=0.1, p_slip=0.1, p_guess=0.25),
    
    # Easy concepts (high learning rate, low slip)
    "easy": BKTParameters(p_init=0.1, p_learn=0.3, p_slip=0.05, p_guess=0.2),
    
    # Difficult concepts (low learning rate, higher slip)
    "difficult": BKTParameters(p_init=0.0, p_learn=0.05, p_slip=0.15, p_guess=0.1),
    
    # Multiple choice questions (higher guess rate)
    "multiple_choice": BKTParameters(p_init=0.0, p_learn=0.1, p_slip=0.1, p_guess=0.25),
    
    # Open-ended questions (lower guess rate)
    "open_ended": BKTParameters(p_init=0.0, p_learn=0.1, p_slip=0.1, p_guess=0.05),
    
    # Interview prep (strict - low guess, moderate slip)
    "interview": BKTParameters(p_init=0.0, p_learn=0.08, p_slip=0.12, p_guess=0.1),
}


def get_bkt_model(preset: str = "default") -> BKTModel:
    """
    Get a BKT model with pre-configured parameters.
    
    Args:
        preset: Name of parameter preset ("default", "easy", "difficult", etc.)
        
    Returns:
        Configured BKT model
    """
    if preset not in PARAMETER_PRESETS:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(PARAMETER_PRESETS.keys())}")
    return BKTModel(PARAMETER_PRESETS[preset])
