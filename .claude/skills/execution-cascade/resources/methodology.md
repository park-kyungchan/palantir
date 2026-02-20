# Execution Cascade — Detailed Methodology

> On-demand reference. Contains implementer DPS templates, tier-specific DPS variations,
> analyst convergence check DPS, convergence algorithm, iteration log format,
> cascade hook suppression detail, and failure sub-case procedures.

---

## Step 2: Implementer DPS Template

Construct each implementer delegation prompt with:

**Context (D11 — cognitive focus first)**:
- INCLUDE: Root cause summary — which file changed and what was modified (e.g., "renamed function X to Y in `src/auth.ts`"). Evidence line from execution-impact L2: exact grep match `{dependent_file:line_number:matching_content}`. For `.claude/` files: relevant cc-reference field specifications.
- EXCLUDE: TRANSITIVE dependents (cascade updates DIRECT only). Full cascade iteration history. Full pipeline state beyond this iteration's dependent file list.
- Budget: Context field ≤ 30% of implementer effective context.

**Task**: "Update references in `<dependent_file>` to match the change in `<root_cause_file>`. Look for pattern `<reference_pattern>` and update to reflect `<new_value>`. After updating, grep the file to verify no stale references to the old pattern remain."

**Constraints**: Scope limited to assigned dependent files only — do NOT modify root cause file or other dependents. implementer has Bash (can test); infra-implementer has Edit/Write only (no Bash). maxTurns: 30.

**Expected Output**: Report as L1 YAML: `files_changed` (array), `status` (complete|failed), `verification` (grep confirms no stale references). L2: before/after for each updated reference.

**Delivery**: Upon completion, send summary to Lead via file-based signal: status (PASS/FAIL), files changed, grep verification result.

### Tier-Specific DPS Variations

| Tier | Implementers | Context Level | maxTurns |
|------|-------------|---------------|----------|
| TRIVIAL | 1 | Full file content (small files) | 15 |
| STANDARD | 1-2 | Relevant file sections | 25 |
| COMPLEX | 2 (max) | Architecture context for cross-module refs | 30 |

- TRIVIAL: Group related dependents to same implementer. Expect convergence in 1 iteration.
- STANDARD: Group related dependents to same implementer.
- COMPLEX: May require all 3 iterations.

---

## Step 3: Analyst Convergence Check DPS

Analyst delegation prompt:

**Context**: Provide `iteration_changed_files` (files modified this iteration), `all_updated_files` (cumulative set across iterations), and `original_impact_files` (initial impact set from execution-impact).

**Task**: For each file in `iteration_changed_files`, extract basename without extension. Use the CC `Grep` tool with that basename as pattern, scoped to `.claude/` directory, glob `*.{md,json,sh}`. Exclude `agent-memory/` from results. For each match, subtract: the file itself, all files in `all_updated_files`, and all files in `original_impact_files`. Report any remaining dependents as new impacts.

**Constraints**: Read-only analysis (Profile-B). No Bash. Use CC Grep tool only. Do NOT modify any files.

**Expected Output**: Return `new_impacts` as a list of `{file, dependents[]}` pairs. Empty list = converged.

**Delivery**: Upon completion, send L1 summary to Lead via file-based signal. Include: status, key metrics, cross-reference notes. L2 detail stays in your context.

### Convergence Check Algorithm

```
# For each file in iteration_changed_files:
#   basename = strip_extension(basename(file))
#   dependents = CC Grep(pattern=basename, path=".claude/", glob="*.{md,json,sh}")
#       excluding agent-memory/ results
#   dependents = dependents - {file}                    # Remove self
#   dependents = dependents - all_updated_files         # Remove already handled
#   dependents = dependents - original_impact_files     # Remove already addressed
#   if dependents is not empty:
#       new_impacts.append({file, dependents})
# return new_impacts  # empty = converged
```

Convergence verdict:
- If `new_impacts` is empty: **CONVERGED** — exit loop
- If `new_impacts` is non-empty AND `iteration_count < 3`: proceed to next iteration
- If `iteration_count >= 3`: **MAX ITERATIONS** — exit loop with partial status

---

## Step 4: Per-Iteration Log Entry Format

```yaml
iteration: 1
changed_files:
  - path: ""
    implementer: ""
    status: complete|failed
new_impacts_detected: 0
new_impact_files: []
```

State persisted across iterations (in Lead's conversation context):

| State | Type | Purpose |
|-------|------|---------|
| `iteration_count` | integer (0-3) | Track against max |
| `all_updated_files` | set of paths | Prevent re-updating |
| `original_impact_files` | set of paths | Exclude from convergence |
| `iteration_log` | array | Build L2 output |
| `files_skipped` | set of paths | Failed updates |

---

## Cascade Mode: Hook Suppression (Detail)

During active cascade, Lead operates in "cascade mode":
- SubagentStop hooks still fire for cascade-spawned implementers
- Lead **ignores** SRC IMPACT ALERT from these hooks (prevents recursive re-entry into execution-impact)
- Convergence is delegated to analyst using CC Grep, not via hook-driven analysis
- This prevents infinite loop: cascade → hook alert → execution-impact → cascade
- Lead tracks cascade mode state internally; exits when convergence reached OR max iterations hit OR all implementers failed

---

## Failure Sub-Cases (Verbose Detail)

### Impact Report Missing or Empty
- **Cause**: execution-impact did not produce an impact report, or report contains no dependents
- **Action**: Set `status: skipped` in L1. Route to execution-review with empty cascade results. Do not spawn any implementers.
- **Never proceed**: with cascade when there is no impact data to act on. "No data" is not the same as "no impacts."

### All Implementers Failed in an Iteration
- **Cause**: Every implementer in an iteration returned failure (file locked, tool error, context exhaustion)
- **Action**: FAIL the cascade. Set L1 `status: partial`, `convergence: false`. Include failed file list and error details per implementer. Route to execution-review with FAIL status.
- **Note**: Single-implementer failure is retried once (see Error Handling). ALL-implementer failure is a cascade-level failure.

### Convergence Check Analyst Failed
- **Cause**: Analyst spawned for convergence checking failed to complete (context exhaustion, tool error)
- **Action**: Treat as non-convergence. If `iteration_count < 3`: retry convergence check with fresh analyst. If retry also fails: terminate cascade with `status: partial` and route to execution-review.
- **Never proceed**: to next iteration without a convergence verdict. Skipping convergence checks risks infinite cascade.

### Cascade Triggered But No DIRECT Dependents
- **Cause**: execution-impact reported `cascade_recommended: true` but all dependents are TRANSITIVE (hop_count > 1)
- **Action**: Set `status: skipped` with explanation. Route to execution-review. This is a false trigger, not a failure.

### Files Changed Outside Cascade Scope
- **Cause**: During cascade iteration, files outside the dependent set were modified (implementer scope creep)
- **Action**: Log unexpected files in `warnings`. Include in convergence check (they may create new impacts). Report scope violations in L2.
