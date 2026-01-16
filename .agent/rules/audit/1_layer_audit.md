# 1-Layer Audit (Outer Shell) for Progressive-Deep-Dive-Audit

Purpose: Provide the outermost audit layer so Antigravity Gemini-3.0-Pro can run a full E2E verification pass and produce a compliant audit report before deeper layers are executed.

## Scope (Outer Layer Only)
- Verify system prompts and ODA alignment (no code changes in this layer).
- Confirm LLM-independence and Antigravity routing rules.
- Run all custom workflow commands E2E and log results.
- Produce a structured audit summary with file references.

## Canonical Inputs
- System prompts: `/home/palantir/.gemini/GEMINI.md`, `/home/palantir/.claude/CLAUDE.md`, `/home/palantir/.codex/AGENTS.md`
- ODA root: `/home/palantir/park-kyungchan/palantir`
- Ontology registry export: `.agent/schemas/ontology_registry.json` (generated via `python -m scripts.ontology.registry`)
- Workflows: `.agent/workflows/*.md`

## Non-Negotiables
- Treat `ORION_SYSTEM_PROMPT` and `ORION_WORKSPACE_ROOT` as canonical inputs.
- LLM access must route through `scripts/llm/config.py` (no vendor hard-coding).
- ObjectTypes must be sourced from `scripts/ontology/objects/task_types.py` and exported via `scripts/ontology/registry.py`.
- Use ActionTypes for mutation; do not write state ad-hoc.
- Keep Zero-Trust: verify file paths and imports before asserting conclusions.

## Progressive-Deep-Dive-Audit: Outer Layer Checklist
1) Prompt Alignment
   - Confirm GEMINI/CLAUDE/AGENTS are consistent on ODA, registry, and LLM-independence rules.
2) Ontology Registry Integrity
   - Ensure registry export exists and matches canonical source.
3) LLM Independence
   - Verify default model selection is config-driven and Antigravity-aware.
4) Workflow Health
   - Validate all workflows are runnable via `scripts/workflow_runner.py`.
5) Governance + Protocol
   - Confirm `/deep-audit` requires AuditProtocol and notes its constraints.

## E2E Execution Plan (Run All Workflows)
Run in this order unless a workflow specifies otherwise:
1. `python scripts/workflow_runner.py 00_start`
2. `python scripts/workflow_runner.py 01_plan`
3. `python scripts/workflow_runner.py 02_manage_memory`
4. `python scripts/workflow_runner.py 07_memory_sync`
5. `python scripts/workflow_runner.py 03_maintenance`
6. `python scripts/workflow_runner.py 04_governance_audit`
7. `python scripts/workflow_runner.py deep-audit`
8. `python scripts/workflow_runner.py 05_consolidate`
9. `python scripts/workflow_runner.py 06_deprecation_check`

Notes:
- `03_maintenance` is destructive; proceed only with explicit approval (already granted in this session).
- `deep-audit` may require external verification steps when network access is available; follow system prompt constraints.

## Report Format (Outer Layer)
- Findings ordered by severity, with file references.
- E2E results with pass/fail per workflow.
- Explicit gaps or blocked steps (e.g., network-restricted validations).
