---
description: Recursive Self-Improvement Loop (Meta-Cognition)
---
# 🧬 Workflow: Recursive Self-Improvement

## 🎯 Objective
To analyze the performance of the previous session, extract lessons, and **Upgrade the Agent System** (`.agent/`) immediately.
This ensures that the system gets smarter with every interaction.

## 🔄 Algorithmic Steps

### Phase 1: Meta-Analysis (Post-Mortem)
1.  **Trigger:** Task Completion.
2.  **Action:** Review the `task_{id}_viz.md` and execution logs.
3.  **Question:**
    - Did we hit any Governance Blocks? (Why?)
    - Did we hallucinate? (Why?)
    - Was the Context Injection sufficient?

### Phase 2: Kernel Memory Update
1.  **Action:** Update `/home/palantir/GEMINI.md` -> `<meta_memory>`.
2.  **Format:**
    ```xml
    <entry date="{YYYY-MM-DD}" topic="{Topic}">
        {Observation} -> {Lesson} -> {Action Taken}
    </entry>
    ```

### Phase 3: System Evolution (Code Level)
1.  **Condition:** If a recurrent issue is found (e.g., "Agent keeps forgetting absolute paths").
2.  **Action:**
    - **Modify Role:** Update `.agent/roles/worker.md` to make the constraint explicit.
    - **Modify Schema:** Update `.agent/schemas/plan.schema.json` to add a validation rule.
    - **Modify Tool:** Update `scripts/orion` to enforce the rule programmatically.

### Phase 4: Validation
1.  **Action:** Run `make audit` (or equivalent) to verify the system upgrade didn't break anything.

## 🚀 Execution Command
```bash
# Manually trigger self-improvement if needed
python3 scripts/orion report "Self-Improvement Analysis"
```
