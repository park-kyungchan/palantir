---
description: Transform User Intent into a Governed Ontology Plan
---

# ⚡ Workflow 01: Ontology-Driven Planning

## 1. Objective
Transform `UserIntent` (Natural Language) into a **Governed Ontology Plan**, leveraging **Semantic Memory** for context awareness.
This workflow enforces the "Think, Model, Act" cycle.

## 2. The Cognitive Pipeline

### Step 2.1: Recursive Thinking
Use `sequential-thinking` to decompose the user's request.
**Mandatory Hypothesis**:
- What Ontology Concepts are involved?
- What `Actions` are required?
- Does this violate any Safety Rules?

### Step 2.2: Context & Schema Alignment
Check `scripts/ontology/plan.py` and `scripts/ontology/job.py`.
Construct a JSON object that strictly adheres to the schema:
```python
Plan(
  objective="...",
  jobs=[
    Job(action_name="read_file", action_args={"path": "..."}),
    ...
  ]
)
```

### Step 2.3: Persist Plan
Write the JSON plan to a file.
```bash
/home/palantir/.venv/bin/python scripts/action_registry.py write_to_file --TargetFile /home/palantir/.agent/plans/current_plan.json --CodeContent 'JSON_STRING'
```
*(Note: Use the Agent Tool `write_to_file` directly if available)*

## 3. Execution (Dispatch)
Once the plan is saved, dispatch it to the Orion Engine for Governance Validation and Execution.

// turbo
```bash
/home/palantir/.venv/bin/python scripts/engine.py dispatch --file /home/palantir/.agent/plans/current_plan.json
```

## 4. Observability
Watch the console for:
*   `✅ Plan Committed to Ontology` (Governance Pass)
*   `⚙️ Executing Job [1/N]...`
