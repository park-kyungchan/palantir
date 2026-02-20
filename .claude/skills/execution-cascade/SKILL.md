---
name: execution-cascade
description: >-
  WHEN execution-impact reports cascade_recommended:true AND the
  initial change is already committed by execution-code or
  execution-infra. NOT for initial implementation — cascade
  handles downstream propagation only. Distinct from
  execution-code (initial file edits) and execution-infra
  (infra-only initial edits): cascade updates N dependent modules
  that reference the already-changed module. Iterates
  DIRECT-dependent updates (hop_count=1) in max 3 rounds with
  convergence tracking. Max 2 implementers per iteration. Reports
  converged, partial, or non-convergent status. Routes to
  execution-review on completion. DPS needs execution-impact
  DIRECT dependents with evidence + root cause change summary.
  Exclude TRANSITIVE dependents and full pipeline history.
user-invocable: true
disable-model-invocation: true
---

# Execution — Cascade

## Execution Model
- **TRIVIAL**: Lead-direct. Single implementer updates 1-2 affected files. Typically converges in 1 iteration.
- **STANDARD**: Spawn 1-2 implementers per iteration. Update 3-8 affected files. Expected 1-2 iterations.
- **COMPLEX**: Spawn 2 implementers per iteration. Update >8 affected files. May reach max 3 iterations.

## Decision Points

### Tier Classification for Cascade
Lead determines cascade depth based on execution-impact report:
- **TRIVIAL**: 1-2 DIRECT dependents, same directory, simple reference pattern.
- **STANDARD**: 3-6 DIRECT dependents across 1-2 directories, mixed reference types.
- **COMPLEX**: 7+ DIRECT dependents across 3+ directories, deep reference chains, high-hotspot files.

### When to Skip Cascade
Cascade can be skipped (set `status: skipped`) when:
- execution-impact reports `cascade_recommended: false`
- All dependents are TRANSITIVE-only (no DIRECT dependents)
- All DIRECT dependents are already in the current pipeline's change set
- execution-impact reports `status: skipped` (no analysis performed)

### Implementer Type Selection
Critical routing decision based on file path:
- **implementer** (`subagent_type: implementer`): Application source files (Python, TypeScript, etc.). Has Bash for testing.
- **infra-implementer** (`subagent_type: infra-implementer`): `.claude/` directory files. Has Edit/Write only — NO Bash.
- **Decision rule**: Path starts with `.claude/` → infra-implementer. Otherwise → implementer.
- **Mixed cascade**: When dependents span both domains, spawn BOTH types in parallel (each owns its domain).

### Convergence vs Max-Iteration Tradeoff
- **Aggressive** (default): Check after every iteration, stop at first empty impact set. For well-structured codebases.
- **Conservative**: Run all 3 iterations. Use when high-hotspot files affected or execution-impact confidence `low`.
- **Early termination**: Iteration 1 → 0 impacts AND all implementers complete → skip remaining iterations.
- For convergence check details: read `resources/methodology.md`

### Cascade Mode Activation
Lead enters "cascade mode" on start: SRC IMPACT ALERTs from cascade implementers are IGNORED (prevents recursive loop). Lead tracks state: `iteration_count`, `all_updated_files`, `original_impact_files`. Convergence delegated to analyst via CC Grep. Exits when: convergence OR max iterations OR all implementers failed.

## Methodology

### 1. Read Impact Report
Load execution-impact L1 and L2 output:
- Extract `impacts[]` array — changed files and their dependents
- Prioritize DIRECT dependents (hop_count=1) over TRANSITIVE for update ordering
- Initialize state: `iteration_count = 0`, `all_updated_files = {}`, `original_impact_files = set(impacts[].dependents[].file)`

### 2. Spawn Implementers for Affected Files
For each iteration (max 3):
- Group dependent files by proximity (max 2 implementer groups)
- Select agent type: `implementer` for source files, `infra-implementer` for `.claude/` files
- DPS context: INCLUDE root cause summary + evidence line. EXCLUDE TRANSITIVE dependents, full pipeline state.
- Each implementer verifies no stale references remain after updating (grep check)
- For full DPS template and tier-specific variations: read `resources/methodology.md`

### 3. Check Convergence After Updates
After all implementers in an iteration complete:
- Spawn an **analyst** (`subagent_type: analyst`) to perform convergence check via CC Grep
- Analyst checks each changed file's basename against `.claude/` directory (glob `*.{md,json,sh}`)
- Subtract: self, `all_updated_files`, `original_impact_files` → remaining = new impacts
- If `new_impacts` empty: **CONVERGED** — exit loop
- If non-empty AND `iteration_count < 3`: proceed to next iteration; if `>= 3`: MAX ITERATIONS → exit partial
- For analyst DPS template and algorithm: read `resources/methodology.md`

### 4. Handle Iteration State
State persisted in Lead's context across iterations:

| State | Type | Purpose |
|-------|------|---------|
| `iteration_count` | integer (0-3) | Track against max |
| `all_updated_files` | set of paths | Prevent re-updating |
| `original_impact_files` | set of paths | Exclude from convergence |
| `iteration_log` | array | Build L2 output |
| `files_skipped` | set of paths | Failed updates |

> For per-iteration log entry YAML format: read `resources/methodology.md`

### 5. Report Cascade Results
- Set `status`: `converged` (empty convergence check), `partial` (max iterations or failures), `skipped` (no DIRECT dependents)
- Set `convergence`: `true` if converged, `false` if max iterations reached
- Include `warnings` array for non-convergence details or skipped files
- L2: per-iteration narrative — what was updated, by whom, new impacts found

## Error Handling
- **Implementer Failure**: First failure → retry with fresh implementer. Second → add to `files_skipped`, continue. Never block cascade on one file.
- **Circular Dependency**: Same file in `changed_files` AND `new_impacts` → add to `all_updated_files`, do not re-process, log warning.
- **Non-Convergence**: Max 3 iterations → set `status: partial`, `convergence: false`. Pipeline CONTINUES to execution-review. P7 verify catches remaining issues.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error, implementer spawn timeout | L0 Retry | Re-invoke same implementer with same DPS |
| Incomplete output or stale references remain | L1 Nudge | SendMessage with corrected pattern or updated scope |
| Implementer exhausted turns or context polluted | L2 Respawn | Kill → fresh implementer with refined DPS |
| Cascade scope conflict or circular dependency blocks | L3 Restructure | Reorder processing, break cycle, reassign ownership |
| All implementers failed after L2, or 3+ non-convergent | L4 Escalate | AskUserQuestion with situation summary + options |

> For verbose failure sub-cases (impact missing, all failed, analyst failed, no DIRECT dependents, scope creep): read `resources/methodology.md`

## Anti-Patterns

- **DO NOT process TRANSITIVE dependents**: Cascade updates ONLY DIRECT (hop_count=1). Updating transitive causes churn and new cascading impacts.
- **DO NOT assign same file to multiple implementers**: Within each iteration, file ownership must be non-overlapping. Interdependent files → assign to SAME implementer.
- **DO NOT re-invoke execution-impact after cascade**: Convergence is handled internally by analyst. Re-invoking creates a circular loop.
- **DO NOT ignore hook alerts during cascade**: Lead reads alerts for monitoring but does NOT act on them — no re-routing to execution-impact.
- **DO NOT block pipeline on non-convergence**: Max 3 iterations is a hard limit. Report as warnings and continue. Blocking indefinitely is worse than incomplete cascade.
- **DO NOT force-update false positives**: If a dependent file doesn't actually reference the changed file, mark `status: false_positive` and exclude from further iterations.
- **DO NOT use background agents for cascade implementers**: Cascade implementers need monitoring between iterations. Always use foreground spawning.

## Transitions

> P2+ team mode: 4-channel protocol — Ch1 (PT metadata) + Ch2 (`tasks/{team}/`) + Ch3 (micro-signal to Lead) + Ch4 (P2P).
> TaskUpdate on completion. One file per implementer (no overlapping edits).
> Micro-signal format: `.claude/resources/output-micro-signal-format.md` | Phase-aware routing: `.claude/resources/phase-aware-execution.md`

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| execution-impact | Impact report with DIRECT dependents | L1 YAML: `impacts[].{changed_file, dependents[].{file, type, hop_count, reference_pattern, evidence}}` |
| execution-impact | Cascade recommendation | L1 field: `cascade_recommended: true` with `cascade_rationale` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-review | Cascade results + warnings | Always after cascade completes (converged or partial) |
| execution-impact | Re-invocation for convergence check | NEVER — convergence handled internally by analyst |
| verify domain | Cascade-modified files for validation | Via execution-review routing |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Non-convergence (3 iterations) | execution-review (with warnings) | All iteration details, unresolved file list |
| All implementers failed in iteration | execution-review (FAIL) | Failed file list, error details per implementer |
| Circular dependency detected | execution-review (with warnings) | Cycle details, files marked as updated to break cycle |
| No DIRECT dependents (false cascade trigger) | execution-review (skipped) | `status: skipped`, empty iteration_details |

### State Flow
```
Init: read impact → iteration_count=0, all_updated_files={}, original_impact_files=set(dependents)
Iter N(1-3): group → spawn implementers → collect → all_updated_files += changed
  → spawn analyst: new_impacts empty→CONVERGED exit | non-empty AND N<3→Iter N+1 | N>=3→partial exit
Post: build L1/L2 → route execution-review → exit cascade mode
```

## Quality Gate
- All DIRECT dependents processed (updated or skipped with reason)
- Each iteration's implementers reported `status: complete` for assigned files
- Convergence check ran after every iteration; non-convergent scenarios documented in warnings
- Max 3 iterations enforced; file ownership non-overlapping across implementers within each iteration

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
pt_signal: "metadata.phase_signals.p6_cascade"
signal_format: "{STATUS}|iterations:{N}|converged:{true|false}|ref:tasks/{team}/p6-cascade.md"
```

### L2
- Per-iteration update log with implementer assignments
- Files changed per iteration with before/after summary
- Convergence check results per iteration
- Final status: converged or partial with unresolved file list
