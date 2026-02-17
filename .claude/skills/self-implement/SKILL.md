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
  delivery-pipeline and manage-infra.
user-invocable: false
disable-model-invocation: false
allowed-tools: "Read Glob Grep Edit Write"
metadata:
  category: homeostasis
  tags: [infra-improvement, wave-implementation, convergence-tracking]
  version: 2.0.0
---

# Self-Implement — INFRA Fix Executor

## Execution Model
- **TRIVIAL**: 1 infra-implementer (maxTurns:15). 5 or fewer findings in non-overlapping files.
- **STANDARD**: 1-2 infra-implementer waves (maxTurns:20 each). Standard RSI fix cycle.
- **COMPLEX**: 3-4 infra-implementer waves (maxTurns:25 each) + extended verification. Major structural changes.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Decision Points

### Fix Wave Parallelism
- **Single wave**: ≤5 findings, all in non-overlapping files. One infra-implementer handles everything.
- **Parallel waves**: 6+ findings spanning multiple file categories. Group by category with max 2 concurrent infra-implementers per wave.

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
Read findings list from self-diagnose output:
- Parse findings by severity category
- Group by file type for wave planning
- Identify non-overlapping file sets for parallel execution

### 2. Spawn Infra-Implementer Waves
Spawn infra-implementer agents in parallel waves:
- Group fixes by category (field removal, feature addition, routing fix, etc.)
- Max 2 infra-implementers per wave to avoid file conflicts

Construct each delegation prompt with:
- **Context**: Specific findings for this wave with severity and category. CC native field reference from cc-reference cache. For description edits, include current character count and the 1024-char limit.
- **Task**: For each file, specify exact change: "Remove field X from Y.md", "Change value A to B in Z/SKILL.md", etc. Provide target value where possible.
- **Constraints**: Write and Edit tools only — no Bash. Files in this wave must not overlap with other concurrent infra-implementers. Only modify files listed in findings.
- **Expected Output**: L1 YAML with files_changed, findings_fixed, status. L2 with per-file change log: finding ID, what changed, before→after.
- **Delivery**: Write full result to `/tmp/pipeline/homeostasis-self-implement.md`. Send micro-signal to Lead via SendMessage: `{STATUS}|fixed:{N}|deferred:{N}|ref:/tmp/pipeline/homeostasis-self-implement.md`.

Await infra-implementer result via SendMessage (P2+) or TaskOutput (standalone). If a wave fails, re-spawn with corrected instructions (max 1 retry per wave).

### 3. Verify Compliance
Post-implementation verification. Re-run diagnostic categories from self-diagnose, but only for modified files.

**Verification checklist:**
- Re-scan modified files: zero non-native fields (CRITICAL)
- Verify routing: all auto-loaded skills visible, no disable-model-invocation:true on pipeline skills
- Verify budget: total description chars within 32,000
- Cross-reference check: INPUT_FROM/OUTPUT_TO bidirectionality intact
- Hook scripts: shebang, exit codes, JSON output format valid

**Iteration logic:**
- Zero findings remain: proceed to Step 4 (convergence)
- Findings decreased: loop to Step 2 (max 3 iterations)
- Findings plateau: accept partial if all remaining are LOW

### 4. Update Records
Spawn infra-implementer for memory updates:
- **Context**: Improvement cycle findings, files changed, cc-reference updates
- **Task**: Update memory/context-engineering.md with new findings. Update MEMORY.md session history with cycle summary.
- **Constraints**: Edit tool only — modify existing sections, don't restructure.
- **Expected Output**: L1 YAML with files_updated, status. L2 with change summary.
- **Delivery**: SendMessage to Lead: `PASS|files:{N}|ref:/tmp/pipeline/homeostasis-self-implement-records.md`.

### 5. Commit
Lead-direct via Bash tool, or route to /delivery-pipeline:
- Stage changed files with `git add` (specific files, never `-A`)
- Structured commit message: `feat(infra): RSI [scope] -- [summary]`
- Include finding categories in body
- Report ASCII status visualization

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
| manage-skills | Updated skills needing inventory refresh | After skill frontmatter modifications |
| manage-infra | Updated INFRA needing health re-check | After structural changes |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Non-convergence after 3 iterations | (Terminate partial) | Remaining findings deferred |
| Infra-implementer wave failure (after retry) | (Continue) | Failed findings deferred |

## Failure Handling
| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Budget overflow detected | HIGH | Fix | Yes | Must resolve before commit |
| Non-convergence after 3 iter | HIGH | Terminate partial | No | Commit successes, defer rest |
| Implementer wave failure (all) | HIGH | Retry once | Conditional | Re-spawn or defer |
| Implementer partial failure | MEDIUM | Continue | No | Some fixed, others deferred |

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
