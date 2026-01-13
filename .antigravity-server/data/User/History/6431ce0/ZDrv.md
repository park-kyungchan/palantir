# Palantir FDE Learning System: v2.0 Roadmap

Following the v1.0 audit, the system is scheduled for a **Quality Enhancement (v2.0)** to align with the current Orion ODA standard.

## 1. Key Objectives
- **Path Sanitization**: Move all KB references to root-relative `/home/palantir/park-kyungchan/palantir/coding/knowledge_bases/`.
- **ODA Integration**: Extract the 8 behavioral rules into `.agent/rules/learning/` for programmatic enforcement.
- **Workflow Automation**: Create a dedicated `/fde-learn` slash command to initialize the learning state.
- **Accuracy First Protocol**: Upgrade the "Accuracy First Mandate" (AF-1 to AF-4) from a prompt guide to a blocking rule.

## 2. Planned Changes

### A. Core Directive Update
- Update `SYSTEM_DIRECTIVE.md` to reference the unified root.
- Re-version to v2.0.

### B. Rule Extraction
- Move `Never Pre-Plan`, `KB First`, and `Universal Concept Extraction` into the `.agent` governance layer.
- Ensure the `GovernanceEngine` can load and enforce these during learning sessions.

### C. Workflow Creation
- **/fde-learn**: A new workflow that:
    1. Reads `SYSTEM_DIRECTIVE.md`.
    2. Synchronizes the 24 KB files.
    3. Sets state to `[LEARNING_INJECTED]`.

## 3. Execution Strategy
- Use the **Butterfly Effect Simulation** to ensure that path changes in the learning module do not conflict with orion-orchestrator core logic.
- Perform a final verification using the ODA E2E test suite.
