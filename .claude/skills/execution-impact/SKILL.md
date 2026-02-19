---
name: execution-impact
description: >-
  Classifies changed-file dependencies as DIRECT (1-hop) or
  TRANSITIVE (2+ hops) with Shift-Left validation against
  audit-impact predictions. Outputs cascade_recommended flag for
  downstream routing. Use after execution-code and/or
  execution-infra complete when file change manifest exists.
  Reads from execution-code code manifest, execution-infra infra
  manifest, and research-coordinator audit-impact L3 predicted
  paths. Produces impact report with cascade flag for
  execution-cascade if recommended and always for
  execution-review. On FAIL (analyst exhausted), defaults
  cascade_recommended: false and routes to execution-review with
  partial impact data. DPS needs execution-code/infra manifests
  + audit-impact L3 predictions. Exclude implementation details
  beyond file paths and change summaries.
user-invocable: true
disable-model-invocation: true
---

# Execution — Impact

## Execution Model
- **TRIVIAL**: Lead-direct. Quick grep check for 1-2 changed files. No analyst spawn.
- **STANDARD**: Spawn 1 analyst, maxTurns: 20. Grep-based reverse reference for 3-8 changed files.
- **COMPLEX**: Spawn 1 analyst, maxTurns: 30. Comprehensive analysis for >8 changed files with map-assisted lookups.

## Decision Points

### Tier Classification
- **TRIVIAL**: 1-2 files, same module, no cross-module refs expected → Lead-direct grep.
- **STANDARD**: 3-8 files, 1-2 modules → single analyst.
- **COMPLEX**: 8+ files across 3+ modules, or high-hotspot in codebase-map.md → analyst + extended turns.

### Skip Conditions
**Skip** (set `status: skipped`, `cascade_recommended: false`) when: documentation-only changes, test-only changes, isolated leaf files with zero known dependents, or TRIVIAL tier AND Lead verified no refs via grep.

**Never skip** when: any `.claude/` INFRA file changed, any interface file changed (signatures/contracts), or any high-hotspot file changed (`hotspot: high` in codebase-map.md).

### Codebase Map Decision
- **Map fresh** (>70% entries updated in 7 days): Use `refd_by` as primary hints, grep supplements. `degradation_level: full`.
- **Map stale** (>30% entries outdated): Use as hints only, grep-verify all suggestions. `degradation_level: degraded`.
- **Map unavailable**: Pure grep. `degradation_level: degraded`. DIRECT detection intact; TRANSITIVE may be incomplete.
- If map unavailable, include recommendation in L2 to run `manage-codebase full` before next pipeline.

### Cascade Recommendation Logic
- `cascade_recommended: true` when: ≥1 DIRECT dependent exists AND NOT already in current change set; OR analysis is partial/incomplete (safety: err on side of checking).
- `cascade_recommended: false` when: zero DIRECT dependents; OR all dependents already in pipeline's change set; OR all dependents are TRANSITIVE-only.
- **Edge case**: DIRECT dependent is a hook script (.sh) → cascade recommended, but note hook context differs from agent context.

### SRC Hook Integration
The SubagentStop hook (`on-implementer-done.sh`) injects an SRC IMPACT ALERT into Lead's context on implementer completion. This alert is a trigger to invoke execution-impact, not a complete analysis.
- Pass hook's preliminary data as additional context to analyst; analyst performs authoritative analysis.
- Wait for execution-code/infra L1 consolidation before spawning analyst (avoid analyzing incomplete change set).

## Methodology

Five-step execution sequence:
1. **Read manifest**: Load execution-code/infra L1 `tasks[].files`, cross-reference SRC IMPACT ALERT and `/tmp/src-impact-{session_id}.md`. Deduplicate.
2. **Load predictions**: Read audit-impact L3 predicted DIRECT/TRANSITIVE paths. Check codebase-map.md freshness. Set `prediction_available`, `degradation_level`.
3. **Spawn analyst**: Construct DPS with D11 cognitive focus (change manifest + predictions only). Use predicted-first grep pattern. Classify `predicted_confirmed` vs `newly_discovered`.
4. **Classify dependents**: DIRECT (hop_count: 1) vs TRANSITIVE (hop_count: 2). Skip TRANSITIVE if <10 turns remain; report `transitive_skipped: true`.
5. **Produce report**: Calculate `cascade_recommended`. Set confidence: `high`/`medium`/`low` based on map availability and completeness.

> For DPS construction detail, tier-specific variations, classification algorithms, and reference patterns: read `resources/methodology.md`

## Quality Gate
- All changed files from manifest have been analyzed
- Every dependent has type classification (DIRECT or TRANSITIVE) with evidence
- `cascade_recommended` decision has explicit rationale in `cascade_rationale`
- L1 YAML is valid and parseable by downstream skills
- Analyst completed within maxTurns

## Degradation Handling

| Mode | Source | Confidence | TRANSITIVE |
|------|--------|-----------|------------|
| Full SRC | Map `refd_by` + grep validation | `high` | Map-assisted 2-hop traversal |
| Degraded SRC | Grep-only (`grep -rl`) | `medium` | Sequential grep |
| Partial | maxTurns reached or grep timeout | `low` | Report partial; pipeline continues |

Core value (DIRECT dependency detection) is fully preserved in all modes. Partial data is better than no data.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Grep timeout or analyst turn limit hit | L0 Retry | Re-invoke same analyst with same DPS |
| Partial analysis — key files not analyzed | L1 Nudge | SendMessage with narrowed scope or additional predictions context |
| Analyst context exhausted or stuck in loop | L2 Respawn | Kill → fresh analyst with refined DPS and reduced file scope |
| Codebase-map stale AND grep incomplete, cascade decision uncertain | L3 Restructure | Split into smaller batches, re-sequence with manage-codebase first |
| Systematic grep failure, tool unavailable, or 3+ L2 failures | L4 Escalate | AskUserQuestion with situation summary + options |

- **Default on failure**: `cascade_recommended: false` (conservative — no cascade without evidence)
- **Pipeline impact**: Non-blocking. Partial or missing impact data does not halt the pipeline.

## Anti-Patterns
- **DO NOT cascade on TRANSITIVE-only**: TRANSITIVE (2-hop) dependents are informational. Only DIRECT (1-hop, literal reference) triggers cascade. Cascading on TRANSITIVE causes unnecessary edits.
- **DO NOT trust hook alert as authoritative**: SubagentStop performs quick grep for preliminary detection only. Always perform full analyst analysis — hook may miss reference variants.
- **DO NOT analyze files outside changed set**: Only analyze dependents of files in the change manifest. General dependency issues are manage-codebase's responsibility.
- **DO NOT skip DIRECT analysis**: If turns are running low, skip TRANSITIVE (optional) but never DIRECT. Report `transitive_skipped: true`.
- **DO NOT cascade when dependents already handled**: If a dependent is already in the current pipeline's change set, it does not need cascade. Check execution-code/infra manifests first.
- **DO NOT re-invoke impact after cascade**: execution-cascade has its own convergence check. Re-invoking creates a circular loop.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Four-Channel Protocol — Ch1 (PT metadata), Ch2 (`tasks/{team}/p6-impact.md`), Ch3 (micro-signal to Lead), Ch4 (P2P to downstream consumers).
- **Task tracking**: Update task status via TaskUpdate after completion.
- **P2P**: Read upstream outputs directly from `tasks/{team}/` files via $ARGUMENTS. Send P2P signals to downstream consumers.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| execution-code | Code file change manifest | L1 YAML: `tasks[].{files[], status}` |
| execution-infra | Infra file change manifest | L1 YAML: `files_changed[]` |
| on-implementer-done.sh | SRC IMPACT ALERT (preliminary) | Hook additionalContext: `changed_files[]`, `preliminary_dependents[]` |
| on-implementer-done.sh | Persistent SRC impact file | File: `/tmp/src-impact-{session_id}.md` |
| research-coordinator | Predicted propagation paths (audit-impact L3) | L3 file: per-file DIRECT/TRANSITIVE predicted dependents |
| manage-codebase | Codebase dependency map (optional) | File: `.claude/agent-memory/analyst/codebase-map.md` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-cascade | Impact report with DIRECT dependents | `cascade_recommended: true` |
| execution-review | Impact report (informational) | Always |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Analyst maxTurns exhausted | execution-review (continue) | Partial impact report, `confidence: low` |
| All greps fail | execution-review (continue) | `status: partial`, `cascade_recommended: false` |
| No changed files in manifest | Skip (no-op) | `status: skipped`, empty impacts array |

## Output

### L1
```yaml
domain: execution
skill: impact
status: complete|partial|skipped
confidence: high|medium|low
files_changed: 0
impact_candidates: 0
degradation_level: full|degraded
impacts:
  - changed_file: ""
    dependents:
      - file: ""
        type: DIRECT|TRANSITIVE
        hop_count: 1|2
        reference_pattern: ""
        evidence: ""
    dependent_count: 0
predicted_confirmed: 0
newly_discovered: 0
prediction_available: true|false
cascade_recommended: true|false
cascade_rationale: ""
pt_signal: "metadata.phase_signals.p6_impact"
signal_format: "{STATUS}|cascade:{true|false}|confidence:{level}|ref:tasks/{team}/p6-impact.md"
```

### L2
- Per-file dependency analysis with grep evidence (file:line:content)
- DIRECT vs TRANSITIVE classification rationale
- Predicted vs Discovered breakdown (predicted_confirmed, newly_discovered, predicted_invalidated)
- Cascade recommendation with detailed reasoning + Shift-Left accuracy assessment (% predictions confirmed)

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
