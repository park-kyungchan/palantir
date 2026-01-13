# AGENTS.md

Purpose: Global agent operating instructions for /home/palantir.

## 1) Canonical References
- If present, treat `CLAUDE.md` and `GEMINI.md` as higher-priority local guides.
- If either file is missing, proceed with this document and note the gap in your response.

## 2) Antigravity Kernel Directives
- Separate intent and execution: communicate intent in Korean, execution artifacts in English.
- Enforce Zero-Trust: do not assume files or symbols exist; verify before mutation.
- Apply the 3-stage virtual workflow (Stage A/B/C) for integration-sensitive changes.
- Use workflows in `.agent/workflows/` when tasks are complex or gated by rules.

## 3) Operating Model (ODA Alignment)
- Follow Ontology-Driven Architecture: schema-first, action-only mutation, audit-first.
- Do not bypass governance: state changes must go through Actions, not ad-hoc writes.
- Prefer event-driven side effects; avoid tight coupling between mutation and effects.

## 4) AIP-Free Runtime Expectations
- Default to Antigravity as the LLM backend when available.
- Avoid hard-coding vendor-specific defaults; route via a provider interface where possible.
- Keep configs path-agnostic; respect `ORION_WORKSPACE_ROOT` when provided.

## 5) Quality and Maintainability
- Keep modules small and cohesive; avoid cross-layer imports that violate ODA boundaries.
- Ensure async paths do not block; wrap sync calls in executors if needed.
- Keep invariants explicit: validation before mutation, audit before execution.

## 6) Changes and Documentation
- Update docs alongside behavioral changes (README, knowledge bases, or protocol docs).
- Record significant decisions in audit-friendly logs or structured notes.

## 7) Testing Expectations
- Run or update tests for modified logic paths when feasible.
- Prefer targeted tests that match ontology actions and governance flows.

## 8) Security and Safety
- Never log secrets; redact env values and tokens in output.
- Avoid destructive operations unless explicitly requested and approved.

## 9) Codex Slash Commands (Workflow Bridge)
- If user input starts with `/` and matches a workflow name in `/home/palantir/park-kyungchan/palantir/.agent/workflows`, treat it as a request to execute that workflow.
- Before execution, ensure the registry exists by running `python /home/palantir/park-kyungchan/palantir/scripts/tools/sync_codex_workflows.py`.
- Execute the workflow via `python /home/palantir/park-kyungchan/palantir/scripts/workflow_runner.py <workflow_name>` and return a concise result.
