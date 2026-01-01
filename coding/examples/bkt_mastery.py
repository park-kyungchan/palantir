#!/usr/bin/env python3
"""
Example: Bayesian Knowledge Tracing (BKT)

This example demonstrates how to:
1. Initialize BKT models with different parameter presets
2. Track mastery updates with correct/incorrect responses
3. Predict future performance
4. Estimate attempts needed for mastery

Run with: python examples/bkt_mastery.py
"""

from palantir_fde_learning.domain.bkt import (
    BKTParameters,
    BKTState,
    BKTModel,
    get_bkt_model,
    PARAMETER_PRESETS,
)


def demonstrate_bkt_update():
    """Show how BKT updates mastery based on responses."""
    print("=" * 60)
    print("BKT Mastery Update Demonstration")
    print("=" * 60)
    print()
    
    # Use interview preset (strict parameters for FDE prep)
    bkt = get_bkt_model("interview")
    print("Using 'interview' preset:")
    print(f"  P(L0) = {bkt.params.p_init:.2f}  (initial mastery)")
    print(f"  P(T)  = {bkt.params.p_learn:.2f}  (learning rate)")
    print(f"  P(S)  = {bkt.params.p_slip:.2f}  (slip probability)")
    print(f"  P(G)  = {bkt.params.p_guess:.2f}  (guess probability)")
    print()
    
    # Simulate learning sequence
    state = BKTState()
    responses = [True, True, False, True, True, True, True, True, True, True]
    
    print("Simulating learning sequence:")
    print("-" * 50)
    print(f"{'Attempt':>7} {'Response':>10} {'Mastery':>10} {'Mastered':>10}")
    print("-" * 50)
    
    for i, correct in enumerate(responses, 1):
        state = bkt.update(state, correct)
        mastered = "✓ Yes" if state.is_mastered else "○ No"
        response = "Correct" if correct else "Incorrect"
        print(f"{i:>7} {response:>10} {state.mastery:>9.1%} {mastered:>10}")
    
    print("-" * 50)
    print(f"Final mastery: {state.mastery:.1%}")
    print(f"Accuracy: {state.accuracy:.1%} ({state.correct}/{state.attempts})")
    print()


def compare_presets():
    """Compare how different presets affect learning curves."""
    print("=" * 60)
    print("Comparing BKT Parameter Presets")
    print("=" * 60)
    print()
    
    # All correct responses
    responses = [True] * 15
    
    presets_to_compare = ["easy", "default", "difficult", "interview"]
    
    print(f"{'Preset':<12} ", end="")
    for i in range(1, 16, 2):
        print(f"{'A'+str(i):>6}", end="")
    print("  Final")
    print("-" * 60)
    
    for preset_name in presets_to_compare:
        bkt = get_bkt_model(preset_name)
        state = BKTState()
        
        print(f"{preset_name:<12} ", end="")
        for i, correct in enumerate(responses):
            state = bkt.update(state, correct)
            if i % 2 == 0:
                print(f"{state.mastery:>5.0%} ", end="")
        print(f" {state.mastery:>5.1%}")
    
    print()
    print("Legend: A1, A3, ... = Attempt 1, 3, etc. (all correct)")
    print()


def demonstrate_prediction():
    """Show mastery prediction capability."""
    print("=" * 60)
    print("Performance Prediction")
    print("=" * 60)
    print()
    
    bkt = get_bkt_model("default")
    
    # Three different mastery levels
    states = [
        BKTState(mastery=0.2, attempts=5),
        BKTState(mastery=0.5, attempts=10),
        BKTState(mastery=0.8, attempts=20),
    ]
    
    print(f"{'Mastery':>10} {'P(Correct)':>12} {'Est. to Mastery':>18}")
    print("-" * 45)
    
    for state in states:
        p_correct = bkt.predict_correct(state)
        est_attempts = bkt.expected_attempts_to_mastery(state)
        est_str = str(est_attempts) if est_attempts is not None else "∞"
        print(f"{state.mastery:>9.0%} {p_correct:>11.0%} {est_str:>18}")
    
    print()


def main():
    demonstrate_bkt_update()
    compare_presets()
    demonstrate_prediction()
    print("BKT demonstration complete!")


if __name__ == "__main__":
    main()
