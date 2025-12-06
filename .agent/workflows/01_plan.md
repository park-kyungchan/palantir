---
description: Dispatch a Natural Language Task to the Orion Agent
---

# ⚡ Workflow 01: Task Dispatch & Planning

## 1. Objective
Transform a high-level user intent (Natural Language) into a **Governed Ontology Plan**, leveraging **Semantic Memory** for context awareness.

## 2. The Loop
1.  **Recall**: Engine queries `MemoryManager` (FTS5) for relevant Insights/Patterns.
2.  **Plan Generation**: (Currently Rule-Based/Stub) Creates a `Plan` object.
3.  **Governance**: Validates `Plan` against Pydantic Models.
4.  **Audit**: Logs `ACTION_START` event to `ontology.db` and `Observer`.
5.  **Execution**: Dispatches the plan.

## 3. Execution Commands

### Natural Language Dispatch
// turbo
```bash
/home/palantir/.venv/bin/python scripts/engine.py dispatch "Your task description here"
```

### File-Based Dispatch (Legacy/Specific)
```bash
/home/palantir/.venv/bin/python scripts/engine.py dispatch --file /path/to/plan.json
```

## 4. Observability
Watch the console for:
*   `🧠 [Memory] Accessing Semantic Knowledge...` (Recall Check)
*   `✨ [Memory] Recalled X relevant insights` (If context found)
*   `✅ Plan Committed to Ontology` (Governance Pass)
