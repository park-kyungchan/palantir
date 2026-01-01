#!/usr/bin/env python3
"""
Example: Zone of Proximal Development (ZPD) Recommendations

This example demonstrates how to:
1. Initialize a learner with partial mastery
2. Get ZPD-based concept recommendations
3. Understand the recommendation scoring

Run with: python examples/zpd_recommendations.py
"""

from palantir_fde_learning.domain import (
    DifficultyTier,
    LearnerProfile,
    KnowledgeComponentState,
    LearningDomain,
    LearningConcept,
)
from palantir_fde_learning.application import ScopingEngine


def main():
    print("=" * 60)
    print("ZPD Recommendation Engine Demonstration")
    print("=" * 60)
    print()
    
    # 1. Create learner with some mastered concepts
    profile = LearnerProfile(learner_id="fde_candidate_002")
    
    # Set up mastery states (simulating a learner mid-journey)
    mastery_data = {
        # Beginner concepts - mostly mastered
        "typescript.basics": 0.92,
        "typescript.interfaces": 0.88,
        "typescript.generics": 0.75,
        # Intermediate concepts - in progress
        "osdk.client_setup": 0.65,
        "osdk.object_queries": 0.45,
        "osdk.actions": 0.30,
        # Advanced concepts - not started
        "workshop.variables": 0.15,
        "workshop.events": 0.05,
        "pipeline.transforms": 0.0,
    }
    
    for concept_id, mastery in mastery_data.items():
        profile.knowledge_states[concept_id] = KnowledgeComponentState(
            concept_id=concept_id,
            mastery_level=mastery,
        )
    
    print("Learner State:")
    print("-" * 50)
    print(f"{'Concept':<30} {'Mastery':>8} {'Status':>12}")
    print("-" * 50)
    
    for concept_id, kc in profile.knowledge_states.items():
        if kc.mastery_level >= 0.95:
            status = "✓ Mastered"
        elif kc.mastery_level >= 0.70:
            status = "◐ Near"
        elif kc.mastery_level >= 0.30:
            status = "○ Learning"
        else:
            status = "· New"
        print(f"  {concept_id:<28} {kc.mastery_level:>7.0%} {status:>12}")
    
    print()
    print(f"Overall Mastery: {profile.overall_mastery():.1%}")
    print()
    
    # 2. Get ZPD-based recommendations
    engine = ScopingEngine()
    
    print("=" * 60)
    print("ZPD Recommendations")
    print("=" * 60)
    print()
    print("Zone of Proximal Development (ZPD) identifies concepts that are:")
    print("  • Not too easy (already mastered)")
    print("  • Not too hard (missing prerequisites)")
    print("  • Just right (optimal stretch)")
    print()
    
    recommendations = engine.recommend_next_concept(profile, n=5)
    
    if recommendations:
        print(f"Top {len(recommendations)} Recommended Concepts:")
        print("-" * 50)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.title}")
            print(f"   ID: {rec.concept_id}")
            print(f"   Domain: {rec.domain.value}")
            print(f"   Difficulty: {rec.difficulty_tier.value}")
            print(f"   Time: ~{rec.estimated_minutes} minutes")
    else:
        print("No recommendations available.")
        print("(This may happen if no concepts are defined in KB)")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
