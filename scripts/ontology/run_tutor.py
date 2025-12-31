#!/usr/bin/env python3
"""
Orion V3.5 Learning Engine Entry Point (Phase 5)
Usage: python scripts/ontology/learning.py --target <path> --user <id>

This script triggers the Adaptive Tutoring Engine.
It performs:
1. Initialization of the Cognitive Engine
2. Loading of Learner State (OSDK)
3. ZPD-based Curriculum Scoping

The output is a 'Learning Context' JSON consumed by the AI Agent.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Phase 5 Imports
from scripts.cognitive.engine import AdaptiveTutoringEngine
from scripts.ontology.storage.database import initialize_database

async def run_session_generation(target_path: str, user_id: str):
    print(f"🚀 Initializing Orion Adaptive Tutor (Phase 5) for user: {user_id}")
    
    # 0. Initialize DB (Required for OSDK)
    await initialize_database()
    
    # 1. Initialize Engine
    engine = AdaptiveTutoringEngine(target_path)
    
    # 2. Start Session (Load State + Scope)
    print("   • Scanning Codebase & Loading Learner State...")
    session_data = await engine.initialize_session(user_id)
    
    recommendations = session_data["recommendations"]
    learner = session_data["learner"]
    
    # 3. Construct Context Payload
    output_dir = Path(".agent/learning")
    output_dir.mkdir(parents=True, exist_ok=True)
    session_id = datetime.now().strftime("learn_%Y%m%d_%H%M%S")
    output_file = output_dir / f"{session_id}.json"
    
    context = {
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "learner_stats": {
            "theta": learner["theta"],
            # "mastered_concepts": len(learner["knowledge_components"]) # dict
        },
        "curriculum_recommendations": recommendations,
        "instruction": (
            "Agent: Use the 'curriculum_recommendations' to guide the user. "
            "For each recommended file, use the TCS breakdown to explain WHY it was chosen. "
        )
    }
    
    with open(output_file, "w") as f:
        json.dump(context, f, indent=2)
        
    print(f"\n✅ Learning Session Context Generated: {output_file}")
    print(f"==================================================")
    if recommendations:
        top = recommendations[0]
        print(f"📚 Top Recommendation: {top['file']}")
        print(f"   - Score: {top['tcs']} (ZPD: {top['zpd_score']})")
    else:
        print("📚 No suitable lessons found in ZPD.")
    print(f"🧠 Learner Theta: {learner['theta']}")
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
