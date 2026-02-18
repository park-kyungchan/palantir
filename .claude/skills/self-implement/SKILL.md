---
name: self-implement
description: >-
  Executes INFRA improvements from diagnosis findings. Spawns
  infra-implementer waves with max 2 parallel on non-overlapping
  files. Max 3 iterations for convergence. Paired with
  self-diagnose. Use after self-diagnose produces findings list
  with findings ready for implementation. Reads from self-diagnose
  categorized findings with severity and evidence. Produces
  improvement manifest and implementation report for
  delivery-pipeline and manage-infra. On FAIL (implementation
  breaks existing INFRA), routes back to self-diagnose for
  re-diagnosis. DPS needs self-diagnose findings with file:line
  evidence and cc-reference native field lists. Exclude pipeline
  state and other homeostasis skills' data.
user-invocable: false
disable-model-invocation: false
---

# Self-Implement — INFRA Fix Executor

## Execution Model
- **TRIVIAL**: 1 infra-implementer (maxTurns:15). 5 or fewer findings in non-overlapping files.
- **STANDARD**: 1-2 infra-implementer waves (maxTurns:20 each). Standard RSI fix cycle.
- **COMPLEX**: 3-4 infra-implementer waves (maxTurns:25 each) + extended verification. Major structural changes.

## Phase-Aware Execution

Runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Four-Channel Protocol — Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal to Lead, Ch4 P2P to downstream consumers.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **P2P**: Homeostasis repairs are terminal — no downstream P2P consumers. Write to disk + micro-signal to Lead.
- **File ownership**: Only modify files assigned to this wave. No overlapping edits with parallel agents.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### Fix Wave Parallelism
- **Single wave**: ≤5 findings, all in non-overlapping files. One infra-implementer handles everything.
- **Parallel waves**: 6+ findings spanning multiple file categories. Group by category, max 2 concurrent infra-implementers per wave.

### Convergence Threshold
- **Strict convergence**: Zero findings remaining. Required for pre-release cycles.
- **Partial convergence**: Severity plateau after 3 iterations. Acceptable for incremental improvement.

### Fix Priority Ordering
1. **CRITICAL**: Non-native fields, routing breaks, disable-model-invocation on pipeline skills
2. **HIGH**: Budget overflows, hook validity, agent memory config errors
3. **MEDIUM**: Settings inconsistencies, utilization below 80%, stale references
4. **LOW**: Color assignments, minor formatting, redundant content

## Methodology

### 1. Receive Findings
Read self-diagnose output: parse by severity, group by file type for wave planning, identify non-overlapping file sets for parallel execution.

### 2. Spawn Infra-Implementer Waves
Group fixes by category (field removal, routing fix, etc.) with max 2 infra-implementers per wave.
Construct DPS: INCLUDE findings with severity + file:line evidence; EXCLUDE other waves' findings and pipeline state.
Per-file instructions must specify exact change (field name, target value, line reference).

> For DPS INCLUDE/EXCLUDE block, Task/Constraints/Expected Output/Delivery templates, and finding-to-task mapping: read `resources/methodology.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

### 3. Verify Compliance
Re-run diagnostic categories for modified files only.

**Iteration logic:**
- Zero findings remain → proceed to Step 4 (convergence)
- Findings decreased → loop to Step 2 (max 3 iterations)
- Findings plateau → accept partial if all remaining are LOW

> For verification checklist (5 items): read `resources/methodology.md`

### 4. Update Records
Spawn infra-implementer: update `memory/context-engineering.md` and `MEMORY.md` session history with cycle summary.

> For memory update DPS template: read `resources/methodology.md`

### 5. Commit
Lead-direct via Bash, or route to delivery-pipeline. Stage specific files (never `-A`). Commit message: `feat(infra): RSI [scope] -- [summary]`.

> For commit procedure and message format: read `resources/methodology.md`

## Anti-Patterns

### DO NOT: Fix Issues Without Diagnosis
Never apply fixes without a prior self-diagnose run providing evidence-based findings.

### DO NOT: Fix in Discovery Order
Always sort by severity. CRITICAL first, regardless of when discovered.

### DO NOT: Modify Files Outside .claude/
Self-implement scope is strictly .claude/ infrastructure.

### DO NOT: Commit Partial Without Documenting Deferred Items
Every deferred finding must be recorded in MEMORY.md with severity and rationale.

### DO NOT: Run Multiple Cycles Without Verification
Each cycle must verify previous cycle's fixes before adding new changes.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| self-diagnose | Categorized findings with severity and evidence | L1 YAML: findings[], findings_by_severity |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| delivery-pipeline | Committed improvement cycle | Step 5 routes to delivery |
| manage-infra | Updated INFRA needing health re-check | After structural changes |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Non-convergence after 3 iterations | (Terminate partial) | Remaining findings deferred |
| Infra-implementer wave failure (after retry) | (Continue) | Failed findings deferred |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error or file write timeout in implementer wave | L0 Retry | Re-invoke same infra-implementer with same DPS |
| Implementer output missing files or incomplete change log | L1 Nudge | SendMessage with refined finding list and explicit per-file instructions |
| Implementer stuck, context polluted, or maxTurns exhausted | L2 Respawn | Kill → fresh infra-implementer with reduced wave scope |
| Non-overlapping constraint violated or parallel conflict detected | L3 Restructure | Regroup findings into non-conflicting waves, reassign file ownership |
| 3+ L2 failures on same wave or budget overflow unresolvable | L4 Escalate | AskUserQuestion with situation summary and options |

| Failure Type | Severity | Blocking? | Resolution |
|---|---|---|---|
| Budget overflow detected | HIGH | Yes | Must resolve before commit |
| Non-convergence after 3 iter | HIGH | No | Commit successes, defer rest |
| Implementer wave failure (all) | HIGH | Conditional | Re-spawn or defer |
| Implementer partial failure | MEDIUM | No | Some fixed, others deferred |

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Quality Gate
- All CRITICAL findings addressed (zero remaining)
- All HIGH findings addressed (zero remaining)
- MEDIUM/LOW findings addressed or explicitly deferred with rationale
- No routing breaks after modifications
- Budget under 90% after description edits
- Structured commit message with finding categories
- MEMORY.md updated with session history

## Output

### L1
```yaml
domain: homeostasis
skill: self-implement
status: complete|partial|blocked
pt_signal: "metadata.phase_signals.homeostasis"
signal_format: "{STATUS}|fixed:{N}|deferred:{N}|ref:tasks/{team}/homeostasis-self-implement.md"
iteration_count: 0
findings_received: 0
findings_fixed: 0
findings_deferred: 0
files_changed: 0
implementer_waves: 0
commit_hash: ""
```

### L2
- **Implementation Log**: Per-wave summary with files changed and retries
- **Verification Results**: Post-fix compliance scan
- **Deferred Items**: Remaining findings with severity and rationale
- **Commit Details**: Hash, message, staged files
- **MEMORY.md Update**: Session history entry summary
