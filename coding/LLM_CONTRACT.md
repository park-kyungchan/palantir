# LLM-Independent Contract: Orion Learning Context (v1)

This repository supports **LLM-agnostic** learning over an arbitrary mixed-language codebase (Python/TS/JS/Go/…).

The **single source of truth** is the JSON emitted by `scripts/ontology/run_tutor.py`.
Any LLM (Claude/Codex/Gemini/…) must treat that JSON as the canonical interface and follow the rules below.

---

## 1) Contract Identification

The context JSON MUST include:
- `contract.name` = `orion_learning_context`
- `contract.version` = `1.0`
- `contract.schema_path` = `scripts/ontology/schemas/learning_context_v1.schema.json`
- `contract.spec_path` = `coding/LLM_CONTRACT.md`

If these fields are missing, the LLM should ask for a regenerated context.

---

## 2) Minimal Operating Procedure (LLM)

Given a user prompt and a context JSON:

1. **Parse the JSON** and locate:
   - `prompt_scope` (if present)
   - `kb_matches` (if present)
   - `workflow` (if present)
   - `codebase.entrypoints` / `codebase.workflow_artifacts` (if present)
2. **Never invent a curriculum.**
   - Treat `prompt_scope.allowlist` as the current “scope boundary”.
3. **Start from workflow when asked.**
   - If user intent is “entrypoint/workflow”, prefer `workflow.path` when available.
   - Otherwise pick from `prompt_scope.suggested_entrypoints` and regenerate context with `--entrypoint`.
4. **Ground explanations in KB.**
   - Use `kb_matches[].path` as the preferred KB documents to read first.
5. **Across-language is allowed and expected.**
   - Use file-level dependencies (`dependencies`) and workflow artifacts to connect Python↔TS/JS↔Go.
   - Validate non-local assumptions against upstream docs/specs/tooling when possible; if you cannot verify, explicitly state the limitation and keep the conclusion scoped to static/local analysis.

Optional outputs:
- `outputs.learning_brief_md` is a portable, LLM-ready markdown summary of the same context.
- `role.effective` indicates the lens used for weighting (`fde` / `deployment_strategist` / `general`).

---

## 3) Required Output Shape (LLM)

The LLM’s learning response should be derived from:
- `curriculum_recommendations` (difficulty/ZPD)
- `prompt_scope.ranked_files` (relevance)
- `workflow.path` (entrypoint-first sequence)
- `kb_matches` (knowledge grounding)

When multiple lists conflict:
1) `workflow.path` (if user asked workflow/entrypoint)  
2) `prompt_scope.ranked_files`  
3) `curriculum_recommendations`  

---

## 4) 7-Component Response Quality Rules (LLM)

If the LLM is operating in the 7-component tutoring mode (`coding/SYSTEM_DIRECTIVE.md`):

- **Cross-Stack Comparison** must be more than a syntax table:
  - include “binding vs mutation”, “scope/lifetime”, “type enforcement”, “memory/concurrency model (brief)”, and “common pitfalls”
  - add 3–5 semantic bullets after the table
- **Design Philosophy** must contain:
  - a direct quote (1–3 lines) + a URL to a primary source (spec/docs/talk)
  - a brief trade-off explanation tied to the user prompt
- **Practice Exercise** must be level-safe:
  - if learner level is unclear, ask 2–3 **Socratic** questions (definition → application → boundary case) and STOP (no task yet)
  - if learner level is known (or the user explicitly asks to practice), provide a **time-boxed** exercise with:
    - Goal, Starting Point, Constraints, Acceptance Criteria
    - 2–4 checkpoints, each ending with a short Socratic reflection question
    - two size options (e.g., 5-min micro vs 20-min standard) so the user stays in control (Agile)
    - hints only when the user asks

---

## 5) Safety / Non-Goals

- The contract guarantees **decomposition** (what to study, why, and in what order), not code execution.
- If orchestration files reference tools not present in the environment, the LLM must state the limitation and continue with static analysis.
