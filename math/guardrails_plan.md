# Systemic Guardrails Improvement Plan

## 1. Objective
Analyze the current session's failures and "Tunnel Vision" moments to establish systemic guardrails in `.agent/workflows`. The goal is to enforce **Meta-Cognition**, **Holistic Integration**, and **Efficiency** at the workflow engine level.

## 2. Analysis of Session Failures & Insights

### A. The "Tunnel Vision" Incident (Step 232-243)
- **Incident**: Tried to fix `test_main.py` (Backend) without checking if Frontend actually uses that API.
- **Root Cause**: Isolated problem solving. "Fix the error" mindset vs "Build the system" mindset.
- **Solution**: **Cross-Component Context Enforcement**.
    - *Rule*: You cannot modify an Interface (API/Data) without checking its Consumer (Frontend/DB).

### B. The "Legacy Trap" Incident (Step 232)
- **Incident**: Tried to migrate broken `legacy_migration` code just because it was there.
- **Root Cause**: Lack of "Deprecation Strategy". Assuming all existing code is valuable.
- **Solution**: **Relevance Audit**.
    - *Rule*: Before migration, ask "Is this feature in the target architecture?"

### C. The "Tool Failure" Incident (Step 141)
- **Incident**: `npm audit` failed because `package-lock.json` was missing (project uses `pnpm`).
- **Root Cause**: Ignoring project-specific tooling conventions.
- **Solution**: **Environment Detection**.
    - *Rule*: Detect `pnpm-lock.yaml`, `uv.lock`, `poetry.lock` BEFORE choosing commands.

## 3. Proposed Workflow Upgrades

### Upgrade 1: `00_investigate.md` (The Context Loader)
- **Add**: `Environment Detection` step.
    - Auto-detect package managers (`pnpm`, `uv`, `poetry`) and set ENV variables for subsequent steps.
- **Add**: `Architecture Alignment` step.
    - Read `refactoring_plan.json` and `CONTEXT_LOG.md` to load the "Big Picture".

### Upgrade 2: `01_plan.md` (The Strategist)
- **Add**: `Integration Impact Analysis`.
    - If touching Backend -> Grep Frontend.
    - If touching Frontend -> Check Backend Schemas.
- **Add**: `Legacy Relevance Check`.
    - Explicitly ask: "Is this code legacy? Should we delete instead of fix?"

### Upgrade 3: `02_implement.md` (The Builder)
- **Add**: `Counterpart Reading`.
    - Force `read_file` on the consumer code before writing the producer code.

### Upgrade 4: `90_self_improve.md` (The Critic)
- **Add**: `Holistic Review`.
    - Did we break the contract?
    - Did we add unnecessary complexity?

## 4. Execution Plan
1.  **Update Workflows**: Apply these changes to `.agent/workflows/*.md`.
2.  **Verify**: Run a dummy plan to see if the guardrails trigger.
