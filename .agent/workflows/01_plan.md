---
description: Transform User Intent into a Governed Handoff Artifact
---
# 01_plan: Ontology Planning & Handoff Generation

This workflow defines how Gemini transforms a user request into actionable Handoff Files for other Agents.

## 1. Intent Analysis
- **Goal**: Understand the user's request.
- **Actions**:
    - Use `tavily` if external context is needed.
    - Use `read_file` to understand the codebase state.

## 2. Plan Definition (Ontology)
- **Goal**: Create a structured `Plan` object.
- **Actions**:
    - Define `Objective`.
    - Break down into `Jobs`.
    - Assign `Role` to each Job (`Architect` for Claude, `Automation` for GPT).

## 3. Handoff Artifact Generation (Crucial)
- **Goal**: Create files for manual routing programmatically.
- **Actions**:
    - **Execute Script**:
        ```bash
        python -m scripts.ontology.handoff --plan .agent/plans/plan_[ID].json --job [INDEX]
        ```
    - **Verify**: Check `.agent/handoffs/pending/` for the new file.

## 4. User Notification
- **Action**: Inform the user:
    > "Handoff File Created: `.agent/handoffs/pending/job_a1b2_claude.md`. Please switch to Claude and ask it to read this file."
