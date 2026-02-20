# Manage Codebase — Detailed Methodology

> On-demand reference. Contains DPS templates, tech debt detection patterns,
> risk scoring matrix, blast-radius calculation, revert procedure, and
> test runner auto-detection logic.

---

## DPS Template — STANDARD Tier (1 Implementer)

Spawn `subagent_type: infra-implementer`, `maxTurns: 30`:

- **Context** (D11 priority: cognitive focus > token efficiency):
  - INCLUDE: Project root path, target file pattern (or default exclusions list), test command,
    change plan from Step 3 (action type + target files), baseline test pass confirmation.
  - EXCLUDE: .claude/ directory contents, pipeline history, agent-memory data.
  - Budget: context ≤ 30% of implementer context window.
- **Task**: "Execute the change plan. For each file: apply the specified refactoring action using
  Edit/Write. Read-back after each edit to verify. Then run test command. On test fail: restore
  original content (Write original back). Report L1 YAML + per-file diff summary."
- **Constraints**: Never modify any file under `.claude/`. Max 10 files per invocation.
- **Delivery**: Write full result to `tasks/{work_dir}/homeostasis-manage-codebase.md`.
  Send micro-signal to Lead: `{STATUS}|files:{N}|reverted:{R}|ref:tasks/{work_dir}/homeostasis-manage-codebase.md`.
  Fallback if no team active: `/tmp/pipeline/homeostasis-manage-codebase.md`.

---

## DPS Template — COMPLEX Tier (2 Implementers, Module Split)

Spawn 2 × `subagent_type: infra-implementer`, `maxTurns: 30` each:

- **Split rule**: Divide by top-level source directory (e.g., `src/api/` vs `src/ui/`). Each implementer
  gets a non-overlapping file set.
- **Context per implementer**:
  - INCLUDE: Its assigned file set, test command, change plan for its segment only.
  - EXCLUDE: Other implementer's file set, .claude/ directory contents.
- **Coordination**: Both implementers run in parallel (wave 1). After both complete, Lead runs test
  command once more against full suite. If full-suite test fails: identify which segment caused failure
  → revert only that segment.
- **Delivery**: Each writes to its own segment file (`tasks/{work_dir}/homeostasis-manage-codebase-seg{N}.md`).
  Lead synthesizes into `tasks/{work_dir}/homeostasis-manage-codebase.md`.

---

## Tech Debt Detection Patterns

### By Issue Type

| Issue Type | Detection Signal | Risk Level |
|------------|-----------------|------------|
| Dead code | Unexported symbol, zero `import`/`from` references in project | LOW |
| Large file | File line count > 800 | MEDIUM |
| Duplicate block | ≥10 identical consecutive lines found in 2+ files | MEDIUM |
| God function | Single function > 50 lines | LOW |
| Circular import | A imports B, B imports A (grep bidirectional) | HIGH |
| Stale TODO | `TODO` or `FIXME` comment older than 90 days (git blame) | LOW |

### By Language — File Glob Patterns

| Language | Include Pattern | Common Tech Debt Signals |
|----------|----------------|--------------------------|
| TypeScript | `**/*.ts`, `**/*.tsx` | `export` unused, `any` type overuse, file >400L |
| JavaScript | `**/*.js`, `**/*.mjs` | `require()` unused, mixed module styles |
| Python | `**/*.py` | `import` unused, function >50 lines, class >300L |
| HTML | `**/*.html` | Inline `<style>` or `<script>`, deprecated tags |
| CSS/SCSS | `**/*.css`, `**/*.scss` | Unused class selectors, `!important` overuse |

---

## Risk Scoring Matrix

Used in Step 2 (Analyze) to determine refactor vs. report-only threshold.

| Metric | Score 0 (Safe) | Score 1 (Caution) | Score 2 (Risky) |
|--------|---------------|-------------------|-----------------|
| Importer count | 0–2 files import this | 3–4 files import this | 5+ files import this |
| File size | <400 lines | 400–800 lines | >800 lines |
| Refactoring type | DELETE (dead code) | EXTRACT (split) | RENAME (public API) |
| Test coverage | >80% | 50–80% | <50% or unknown |

**Total score**: Sum the four metrics.
- `0–2`: Auto-refactor in execute mode.
- `3–5`: Flag for user confirmation before executing.
- `6–8`: Report-only. Never auto-refactor.

---

## Blast-Radius Calculation

For each candidate file:
1. Grep all project files for the candidate's filename (without extension) in import statements.
2. Count unique importing files → `importer_count`.
3. Grep all project files for exported symbol names → `symbol_reference_count`.
4. Blast radius = `importer_count + (symbol_reference_count / 5)` (integer).

Threshold: blast_radius > 5 → report-only regardless of other risk scores.

---

## Revert Procedure

When Step 5 (Test) fails after applying changes:

1. For each modified file (in reverse order of modification):
   a. Retrieve original content stored in implementer context (logged before Edit/Write).
   b. Call `Write` with original content to restore the file.
   c. Verify restoration by read-back comparison (first 20 lines).
2. After all files reverted: run test command once more to confirm baseline restored.
3. If baseline restoration fails → L4 Escalate immediately (data integrity issue).
4. Report in L1: `status: FAIL`, `files_reverted: N`, `tests_passed: false`.

**Storage note**: Implementer MUST capture original file content in its own context before
applying any Edit/Write. Do not rely on git for revert — the pipeline may not have committed
the pre-refactor state.

---

## Test Runner Auto-Detection Logic

When `--test-cmd` is not supplied, detect in priority order:

1. Check `package.json` at project root → if `scripts.test` exists → use `pnpm test`
2. Check `package.json` → if `scripts.test:unit` exists → use `pnpm test:unit`
3. Check `pytest.ini` or `pyproject.toml` at project root → use `pytest`
4. Check `Makefile` → if `test` target exists → use `make test`
5. No detection possible → abort, switch to report-only mode, include note in L1.

**Fallback behavior**: If no test command detected or provided, never proceed to Step 4
(Execute). Always report candidates only, with explicit note: "No test command available —
manual review required before applying changes."
