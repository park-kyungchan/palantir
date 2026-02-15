---
name: execution-cascade
description: |
  [P7·Execution·Cascade] Recursive affected-file updater. Spawns implementers to update files identified by execution-impact. Iterates until convergence (no new impacts) or max 3 iterations. Reports partial status if non-convergent.

  WHEN: After execution-impact reports cascade_recommended: true. Affected files identified and classified.
  DOMAIN: execution (skill 4 of 5, before review). After impact, before review.
  INPUT_FROM: execution-impact (impact report with dependent files and classification).
  OUTPUT_TO: execution-review (cascade results for review), execution-impact (re-invoked per iteration for convergence check).

  METHODOLOGY: (1) Read impact report, (2) Spawn implementers for affected files (max 2 per iteration), (3) After updates: re-run grep check on modified files, (4) If new impacts: iterate (max 3), (5) Report convergence status.
  CONSTRAINT: Max 3 iterations. Max 2 implementers/iteration (maxTurns:30 each).
  OUTPUT_FORMAT: L1 YAML cascade result with iteration_details, L2 markdown update log.
user-invocable: false
disable-model-invocation: false
---

# Execution — Cascade

## Execution Model
- **TRIVIAL**: Lead-direct. Single implementer updates 1-2 affected files. Typically converges in 1 iteration.
- **STANDARD**: Spawn 1-2 implementers per iteration. Update 3-8 affected files. Expected 1-2 iterations.
- **COMPLEX**: Spawn 2 implementers per iteration. Update >8 affected files. May reach max 3 iterations.

## Methodology

### 1. Read Impact Report
Load execution-impact L1 and L2 output:
- Extract `impacts[]` array with changed files and their dependents
- Prioritize DIRECT dependents over TRANSITIVE for update ordering
- Record all dependent file paths as initial update targets
- Initialize state tracking: `iteration_count = 0`, `all_updated_files = {}`, `original_impact_files = set(impacts[].dependents[].file)`

### 2. Spawn Implementers for Affected Files
For each iteration (max 3):
- Group dependent files by proximity (max 2 implementer groups)
- Spawn implementers with `subagent_type: implementer`, `maxTurns: 30`. For affected files in `.claude/` scope, spawn `infra-implementer` (subagent_type: infra-implementer) instead of `implementer` to maintain security boundary.
- Each implementer prompt includes:
  - What changed (root cause file and what was modified)
  - What reference pattern to look for in the dependent file
  - Evidence line (exact grep match from execution-impact L2)
  - Expected update behavior (fix the reference to match the change)
- Set mode: "default" for cascade implementers (agent permissions inherited from settings).

### 3. Check Convergence After Updates
After all implementers in an iteration complete:
- Collect files changed by implementers this iteration
- Spawn an **analyst** agent (`subagent_type: analyst`) to perform the convergence check

Analyst delegation prompt (DPS structure):
- **Context**: Provide `iteration_changed_files` (files modified this iteration), `all_updated_files` (cumulative set across iterations), and `original_impact_files` (initial impact set from execution-impact).
- **Task**: For each file in `iteration_changed_files`, extract basename without extension. Use the CC `Grep` tool with that basename as pattern, scoped to `.claude/` directory, glob `*.{md,json,sh}`. Exclude `agent-memory/` from results. For each match, subtract: the file itself, all files in `all_updated_files`, and all files in `original_impact_files`. Report any remaining dependents as new impacts.
- **Constraints**: Read-only analysis (Profile-B). No Bash. Use CC Grep tool only. Do NOT modify any files.
- **Expected Output**: Return `new_impacts` as a list of `{file, dependents[]}` pairs. Empty list = converged.

```
# Analyst convergence check logic:
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

- If `new_impacts` is empty: **CONVERGED** — exit loop
- If `new_impacts` is non-empty AND `iteration_count < 3`: proceed to next iteration
- If `iteration_count >= 3`: **MAX ITERATIONS** — exit loop with partial status

### 4. Handle Iteration State
State persisted across iterations (in Lead's conversation context):

| State | Type | Purpose |
|-------|------|---------|
| `iteration_count` | integer (0-3) | Track against max |
| `all_updated_files` | set of paths | Prevent re-updating |
| `original_impact_files` | set of paths | Exclude from convergence |
| `iteration_log` | array | Build L2 output |
| `files_skipped` | set of paths | Failed updates |

Per-iteration log entry:
```yaml
iteration: 1
changed_files:
  - path: ""
    implementer: ""
    status: complete|failed
new_impacts_detected: 0
new_impact_files: []
```

### 5. Report Cascade Results
Generate L1 YAML and L2 markdown:
- Set `status`: `converged` (empty convergence check), `partial` (max iterations or failures), `skipped` (no DIRECT dependents)
- Set `convergence`: `true` if converged, `false` if max iterations reached
- Include `warnings` array for any non-convergence details or skipped files
- L2 includes per-iteration narrative: what was updated, by whom, new impacts found

## Cascade Mode: Hook Suppression
During active cascade, Lead operates in "cascade mode":
- SubagentStop hooks still fire for cascade-spawned implementers
- Lead **ignores** SRC IMPACT ALERT from these hooks (prevents recursive re-entry into execution-impact)
- Convergence is delegated to analyst using CC Grep, not via hook-driven analysis
- This prevents infinite loop: cascade -> hook alert -> execution-impact -> cascade

## Error Handling

### Implementer Failure
- If implementer fails to update a file: retry once with fresh implementer
- If retry fails: add file to `files_skipped`, continue with remaining
- Never block cascade on a single file failure

### Circular Dependency
- If same file appears in both `changed_files` and `new_impacts` across iterations: break cycle
- Mark file as updated (add to `all_updated_files`), do not re-process
- Log warning in L1 `warnings` array

### Non-Convergence
When max 3 iterations reached without convergence:
1. Set L1 `status: partial`, `convergence: false`
2. Add unresolved files to `warnings` array
3. Pipeline **CONTINUES** to execution-review (never blocks indefinitely)
4. execution-review receives warnings and applies extra scrutiny
5. verify-* phase (P8) catches remaining inconsistencies
6. Delivery (P9) commit message notes "partial cascade convergence"

## Quality Gate
- All DIRECT dependents from execution-impact have been processed (updated or skipped with reason)
- Each iteration's implementers reported `status: complete` for assigned files
- Convergence check ran after every iteration
- Non-convergent scenarios explicitly documented in warnings
- No infinite loops (max 3 iterations enforced)
- File ownership non-overlapping across implementers within each iteration

## Output

### L1
```yaml
domain: execution
skill: cascade
status: converged|partial|skipped
iterations: 0
max_iterations: 3
files_updated: 0
files_skipped: 0
convergence: true|false
iteration_details:
  - iteration: 1
    implementers_spawned: 0
    files_changed: 0
    new_impacts_detected: 0
warnings:
  - ""
```

### L2
- Per-iteration update log with implementer assignments
- Files changed per iteration with before/after summary
- Convergence check results per iteration
- Final status: converged or partial with unresolved file list
