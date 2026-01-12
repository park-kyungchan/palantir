from __future__ import annotations

from lib.oda.ontology.learning.brief import render_learning_brief


def test_render_learning_brief_contains_contract_and_prompt() -> None:
    context = {
        "contract": {
            "name": "orion_learning_context",
            "version": "1.0",
            "schema_path": "scripts/ontology/schemas/learning_context_v1.schema.json",
            "spec_path": "coding/LLM_CONTRACT.md",
        },
        "session_id": "learn_test",
        "timestamp": "2026-01-01T00:00:00",
        "role": {"requested": "auto", "effective": "auto", "rationale": None},
        "prompt": "entrypoint workflow",
        "codebase": {"root": "/repo", "entrypoints": ["main.go"], "workflow_artifacts": []},
        "prompt_scope": {"terms": ["entrypoint", "workflow"], "intent": {"wants_entrypoint": True}},
        "kb_matches": [],
        "curriculum_recommendations": [{"file": "main.go", "tcs": 10.0, "zpd_score": 1.0, "reason": "Optimal"}],
        "workflow": None,
    }

    brief = render_learning_brief(context)
    assert "orion_learning_context" in brief
    assert "coding/LLM_CONTRACT.md" in brief
    assert "entrypoint workflow" in brief
    assert "main.go" in brief

