#!/usr/bin/env python3
"""
Example: Basic Learner Profile Management

This example demonstrates how to:
1. Create a learner profile
2. Track knowledge component states
3. Record practice attempts with BKT updates
4. Check mastery levels

Run with: python examples/basic_profile.py
"""

from datetime import datetime

from palantir_fde_learning.domain import (
    DifficultyTier,
    LearnerProfile,
    KnowledgeComponentState,
    LearningDomain,
    BKTModel,
    BKTState,
    get_bkt_model,
)


def main():
    print("=" * 60)
    print("FDE Learning System - Basic Profile Example")
    print("=" * 60)
    print()
    
    # 1. Create a new learner profile
    profile = LearnerProfile(learner_id="fde_candidate_001")
    print(f"Created profile: {profile.learner_id}")
    print()
    
    # 2. Add knowledge component states
    concepts = [
        "osdk.client_initialization",
        "osdk.object_operations", 
        "workshop.widget_binding",
        "pipeline.transform_basics",
    ]
    
    for concept_id in concepts:
        profile.knowledge_states[concept_id] = KnowledgeComponentState(
            concept_id=concept_id,
            mastery_level=0.0,
        )
    
    print(f"Added {len(concepts)} knowledge components")
    print()
    
    # 3. Simulate practice with BKT updates
    print("Simulating practice sessions with BKT...")
    print("-" * 50)
    
    # Get BKT model for interview prep (strict parameters)
    bkt = get_bkt_model("interview")
    print(f"Using BKT model: P(learn)={bkt.params.p_learn}, P(guess)={bkt.params.p_guess}")
    print()
    
    # Practice OSDK client initialization
    concept_id = "osdk.client_initialization"
    kc = profile.knowledge_states[concept_id]
    bkt_state = BKTState()
    
    responses = [True, True, False, True, True, True, True, True]
    
    for i, correct in enumerate(responses, 1):
        bkt_state = bkt.update(bkt_state, correct)
        # Sync BKT mastery back to KC state
        kc.mastery_level = bkt_state.mastery
        kc.practice_count = bkt_state.attempts
        kc.correct_count = bkt_state.correct
        
        status = "✓" if correct else "✗"
        print(f"  Attempt {i}: {status} → Mastery: {kc.mastery_level:.1%}")
    
    print()
    
    # 4. Check mastery status
    print("Mastery Status:")
    print("-" * 50)
    print(f"{'Concept':<35} {'Mastery':>8} {'Status':>10}")
    print("-" * 60)
    
    for concept_id, kc in profile.knowledge_states.items():
        status = "✓ Mastered" if kc.is_mastered() else "○ Learning"
        print(f"  {concept_id:<33} {kc.mastery_level:>7.1%} {status:>10}")
    
    print()
    print(f"Overall Profile Mastery: {profile.overall_mastery():.1%}")
    print(f"Mastered Concepts: {[c for c in profile.get_mastered_concepts()]}")


if __name__ == "__main__":
    main()
