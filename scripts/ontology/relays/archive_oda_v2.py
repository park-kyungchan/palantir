#!/usr/bin/env python3
import sys
import os

# Ensure project root is in path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.schemas.memory import OrionInsight, OrionPattern, InsightContent, InsightProvenance, PatternStructure
from scripts.ontology.manager import ObjectManager

def main():
    manager = ObjectManager()
    
    # 1. Archive the "Self-Driving ODA" Pattern
    oda_pattern = OrionPattern(
        structure=PatternStructure(
            trigger="Header # ODA_PHASE: 2. Execution (Relay)",
            steps=[
                "Agent recognizes 'ODA_PHASE' header in Handoff artifact",
                "Agent executes the Objective within the context",
                "Agent generates 'result_job_{id}.py' using Mandatory Relay Protocol",
                "Orchestrator consolidates result via ObjectManager"
            ],
            anti_patterns=[
                "Manual unstructured reporting via chat",
                "Editing files without generating a Result Checksum"
            ]
        ),
        frequency_count=1,
        success_rate=1.0,
        code_snippet_ref="scripts/ontology/handoff.py"
    )
    manager.save(oda_pattern)
    print(f"✅ Archived Pattern: Self-Driving ODA ({oda_pattern.id})")

    # 2. Archive the "RSI" Insight
    rsi_insight = OrionInsight(
        content=InsightContent(
            summary="Recursive Self-Improvement (RSI) is triggered by JobResult(status='FAILURE')",
            domain="Orchestration",
            tags=["RSI", "Error-Handling", "Cognitive-Loop"]
        ),
        provenance=InsightProvenance(
            method="Session Refactoring",
            source_episodic_ids=["session-2025-12-13-optimization"]
        ),
        confidence_score=0.9
    )
    manager.save(rsi_insight)
    print(f"✅ Archived Insight: RSI Logic ({rsi_insight.id})")

if __name__ == "__main__":
    main()
