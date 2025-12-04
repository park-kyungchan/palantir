# Project Context & Requirements Log
> **Meta-Cognition Tracker**: This document tracks the evolving context, user requirements, and architectural decisions to ensure the agent never loses the "Big Picture".

## 1. Core Identity & Protocol
- **Agent**: Antigravity Native Agent (Gemini 3.0 Pro).
- **Mode**: AI Ultra (Deep Think, 1M Token Context, Native Multimodal).
- **Workflow**: `.agent/workflows/` (Turbo Mode + Efficiency Checks).
- **Self-Improvement**: Recursive loop via `90_self_improve.md`.

## 2. Active Mission: "Math App Refactoring"
- **Goal**: Transform legacy prototype into a Production-Ready Monorepo (React 19 + FastAPI + Observability).
- **Current Phase**: **Phase 4: Observability Integration**.

## 3. User Requirements (Evolving)
- [x] **Inject Context**: Always load full codebase context (`codebase_investigator`).
- [x] **Native Capabilities**: Use `.agent/workflows` and `// turbo` for automation.
- [x] **Efficiency Check**: Always ask "Is this optimal?" before and after tasks.
- [x] **Search Strategy**: Internal -> Docs -> Community -> Deep Research.
- [x] **Dead Code Elimination**: Remove `math/integrate` and simplify `math/observability`.
- [x] **Meta-Cognition**: Maintain this log to track "What are we doing and Why?".
- [x] **Browser Verification**: Use `browser_subagent` (Playwright) for UI/Integration testing.
- [x] **Guardrails**: Integration Impact & Legacy Relevance checks active.

## 4. Current State (Snapshot)
- **Frontend**: FSD-Lite structure. HomePage with Health Check. Tests passing.
- **Backend**: DDD-Lite structure. `/health` active.
- **Observability**: Planning OpenTelemetry integration.

## 5. Next Steps
1.  **Verify Cleanup**: Ensure no broken imports after moving legacy files.
2.  **Execute Workflow**: Run `03_verify.md` to validate the stabilized base.
3.  **Phase 1 Start**: Begin "Infrastructure & Environment" tasks from `refactoring_plan.json`.
