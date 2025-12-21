#!/usr/bin/env python3
"""
Orion V3.5 Learning Engine Entry Point
Usage: python scripts/ontology/learning.py --target <path> --user <id>

This script triggers the Adaptive Tutoring Engine (Phase 5).
It performs:
1. AST-based Complexity Analysis (TCS Calculation)
2. Dependency Graph Construction
3. Bayesian Knowledge Tracing (Learner State Loading)
4. ZPD-based Curriculum Scoping

The output is a 'Learning Context' JSON consumed by the AI Agent.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Engine Imports
from scripts.ontology.learning.engine import TutoringEngine
from scripts.ontology.learning.scoping import ScopingEngine
from scripts.ontology.learning.persistence import LearnerRepository
from scripts.ontology.learning.types import LearnerState

async def run_session_generation(target_path: str, user_id: str):
    print(f"🚀 Initializing Orion Adaptive Tutor for user: {user_id}")
    
    # 1. Initialize Engines
    repo = LearnerRepository()
    await repo.initialize()
    
    tutor = TutoringEngine(target_path)
    scoper = ScopingEngine(tutor)
    
    # 2. Parallel: Scan Codebase & Load Learner
    print("   • Scanning Codebase & Building Graph...")
    tutor.scan_codebase()
    tutor.calculate_scores()
    
    print("   • Loading Learner State (DB)...")
    state = await repo.get_learner(user_id)
    
    # 3. Generate Recommendations
    print("   • Calculating ZPD & Scoping Curriculum...")
    recommendations = scoper.recommend_next_files(state, limit=5)
    
    # 4. Construct Context Payload
    output_dir = Path(".agent/learning")
    output_dir.mkdir(parents=True, exist_ok=True)
    session_id = datetime.now().strftime("learn_%Y%m%d_%H%M%S")
    output_file = output_dir / f"{session_id}.json"
    
    # Enrich manifest with TCS data
    files_metadata = {}
    for path, score in tutor.scores.items():
        files_metadata[path] = {
            "tcs": round(score.total_score, 1),
            "breakdown": {
                "cognitive": round(score.cognitive_component, 1),
                "dependency": round(score.dependency_component, 1),
                "patterns": round(score.pattern_component, 1)
            }
        }

    context = {
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "learner_stats": {
            "theta": state.theta,
            "mastered_concepts": len(state.knowledge_components)
        },
        "curriculum_recommendations": recommendations,
        "codebase_metrics": files_metadata,
        "instruction": (
            "Agent: Use the 'curriculum_recommendations' to guide the user. "
            "For each recommended file, use the TCS breakdown to explain WHY it was chosen. "
            "Use BKT principles (mastery check) before moving to the next dependency."
        )
    }
    
    with open(output_file, "w") as f:
        json.dump(context, f, indent=2)
        
    print(f"\n✅ Learning Session Context Generated: {output_file}")
    print(f"==================================================")
    print(f"📚 Top Recommendation: {recommendations[0]['file'] if recommendations else 'None'}")
    print(f"🧠 Learner Theta: {state.theta}")
    print(f"==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orion Adaptive Tutor")
    parser.add_argument("--target", required=True, help="Path to codebase")
    parser.add_argument("--user", default="default_user", help="User ID")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_session_generation(args.target, args.user))
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
