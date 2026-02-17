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
  execution-review.
user-invocable: false
disable-model-invocation: false
---

# Execution — Impact

## Execution Model
- **TRIVIAL**: Lead-direct. Quick grep check for 1-2 changed files. No analyst spawn.
- **STANDARD**: Spawn 1 analyst. Grep-based reverse reference analysis for 3-8 changed files.
- **COMPLEX**: Spawn 1 analyst with extended maxTurns. Comprehensive analysis for >8 changed files with map-assisted lookups.

## Decision Points

### Tier Classification for Impact Analysis
- **TRIVIAL indicators**: 1-2 changed files, all in the same module, no cross-module references expected. Lead can do a quick grep check directly without spawning an analyst.
- **STANDARD indicators**: 3-8 changed files, spanning 1-2 modules. Spawn 1 analyst for systematic grep-based analysis.
- **COMPLEX indicators**: 8+ changed files across 3+ modules, or files that are high-hotspot in codebase-map.md. Spawn 1 analyst with extended maxTurns and map-assisted analysis.

### When to Skip Impact Analysis
Impact analysis can be skipped (set `status: skipped`, `cascade_recommended: false`) when:
- Changes are documentation-only (README, comments, non-functional text)
- Changes are in test files only (no production code impact)
- Changes are in isolated leaf files with zero known dependents
- TRIVIAL tier AND Lead has manually verified no references exist via quick grep

Impact analysis should NEVER be skipped when:
- Any `.claude/` INFRA file was changed (always check for cross-references)
- Any interface file was changed (function signatures, type definitions, API contracts)
- Any high-hotspot file was changed (codebase-map.md `hotspot: high`)

### Codebase Map Decision
- **Map available AND fresh** (>70% entries updated within 7 days): Use map's `refd_by` fields as pre-computed hints. Supplement with grep for files not in map. Set `degradation_level: full`.
- **Map available BUT stale** (>30% entries outdated): Use map as hints only, do NOT trust as complete. Grep-verify all map suggestions. Set `degradation_level: degraded`.
- **Map unavailable**: Pure grep-based analysis. Set `degradation_level: degraded`. Analysis is slower but functionally complete for DIRECT dependencies. TRANSITIVE detection may be incomplete.
- **Recommendation**: If map is unavailable, include a note in L2 recommending `manage-codebase full` run before next pipeline execution.

### Cascade Recommendation Logic
The cascade decision is the primary output of this skill:
- **cascade_recommended: true** when:
  - At least 1 DIRECT dependent exists (literal reference to changed file)
  - OR analysis is partial/incomplete (safety: err on side of checking)
  - AND dependent files are NOT already in the pipeline's current change set
- **cascade_recommended: false** when:
  - Zero DIRECT dependents found
  - OR all dependents are already being handled by current pipeline execution
  - OR all dependents are TRANSITIVE-only (informational, no action needed)
- **Edge case**: If a DIRECT dependent is a hook script (.sh file), cascade is recommended but Lead should note that hook changes require special handling (hooks run in shell context, not agent context).

### SRC Hook Integration
The SubagentStop hook (`on-implementer-done.sh`) injects an SRC IMPACT ALERT into Lead's context when implementers complete. This alert contains:
- Preliminary dependent file list (from the hook's quick grep)
- Changed file paths
- This alert is a TRIGGER to invoke execution-impact, not a complete analysis
- Lead should pass the hook's preliminary data as additional context to the analyst, but the analyst performs the authoritative analysis

The hook alert may arrive before execution-code/infra L1 is fully consolidated. Wait for consolidation before spawning the impact analyst to avoid analyzing an incomplete change set.

## Methodology

### 1. Read File Change Manifest
Load execution-code L1 output (and execution-infra L1 if applicable):
- Extract `tasks[].files` arrays for complete list of changed files
- Cross-reference with SubagentStop hook's SRC IMPACT ALERT (preliminary dependent list)
- Read persistent impact file at `/tmp/src-impact-{session_id}.md` if available (written by on-implementer-done.sh, persists across compaction)
- Deduplicate file paths across all sources

### 2. Load Predicted Propagation Paths (Shift-Left)
Load audit-impact L3 predicted propagation paths from research-coordinator output:
- Read the audit-impact L3 file (path passed via research-coordinator or PT metadata)
- Extract predicted DIRECT and TRANSITIVE dependents per changed file
- These predictions were generated during P2 research phase before implementation
- **If audit-impact L3 unavailable** (TRIVIAL/STANDARD tier, or research phase skipped): Fall back to codebase-map.md or grep-only (legacy path). Set `prediction_available: false`.

Also check for codebase-map.md at `.claude/agent-memory/analyst/codebase-map.md`:
- **If available and fresh** (<30% stale entries): Use `refd_by` fields as supplementary lookup. Set `degradation_level: full`.
- **If unavailable or stale**: Proceed with predicted paths + grep. Set `degradation_level: degraded`.

### 3. Spawn Analyst for Predicted-First Analysis
Spawn analyst agent with `subagent_type: analyst`, `maxTurns: 30`.

Construct the delegation prompt with:
- **Context**: Paste the complete file change manifest — each changed file path and a one-line summary of what changed (e.g., "renamed function X to Y", "added field Z to frontmatter"). If audit-impact L3 predictions are available, paste them as the primary predicted propagation paths to verify first. If codebase-map.md exists and is fresh, paste its `refd_by` entries as supplementary hints.
- **Task**: **Predicted-first pattern**: (1) For each changed file, first verify predicted impacts from audit-impact L3 — grep each predicted dependent to confirm the reference still exists and classify as `predicted_confirmed`. (2) Then grep for unpredicted additional impacts using pattern `<basename_without_extension>` scoped to `.claude/` directory, glob `*.{md,json,sh}`. Record newly found dependents as `newly_discovered`. (3) For each match, record a structured evidence triple: `{dependent_file, line_number, matching_content}`. (4) Classify each dependent as DIRECT (hop_count: 1) or TRANSITIVE (hop_count: 2). If no audit-impact L3 predictions available, fall back to full grep scan (legacy path).
- **Constraints**: Read-only analysis — do NOT modify any files. Grep scope limited to `.claude/` directory. Exclude: `.git/`, `node_modules/`, `agent-memory/` (except codebase-map.md), `*.log`. Max 30 turns — if approaching limit, report partial results for files already analyzed rather than rushing remaining files.
- **Expected Output**: Return a structured impact report: for each changed file, list its dependents with `{file, type: DIRECT|TRANSITIVE, hop_count: 1|2, reference_pattern, evidence: "file:line:content"}`. End with a summary: total dependents found, DIRECT count, TRANSITIVE count, and cascade recommendation (true if any DIRECT dependents exist).
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

#### Step 3 Tier-Specific DPS Variations

**TRIVIAL**: Lead-direct quick grep. No analyst spawn. Lead greps for 1-2 changed file basenames, checks for DIRECT references. If none found: set `cascade_recommended: false`. If found: set `cascade_recommended: true`. Max 5 minutes lead-direct.

**STANDARD**: Single analyst with standard scope:
- maxTurns: 20 (reduced from 30 — fewer files to analyze)
- Include audit-impact L3 predictions if available
- Skip TRANSITIVE analysis if all DIRECT dependents resolved within 15 turns

**COMPLEX**: Single analyst with extended scope:
- maxTurns: 30 (full budget — many files to analyze)
- MUST include audit-impact L3 predictions AND codebase-map.md if available
- Prioritize DIRECT analysis over TRANSITIVE — if approaching turn limit, report DIRECT-only with `transitive_skipped: true`

### 4. Classify Dependents
For each dependent file found, apply dual classification:

**Hop Classification:**
- **DIRECT** (hop_count: 1): File contains a literal reference to the changed file's name, path, or key identifiers. Grep match directly links dependent to changed file.
- **TRANSITIVE** (hop_count: 2): File references an intermediate file, which references the changed file. Max 2-hop limit enforced.

**Discovery Classification (Predicted-First Pattern):**
- **predicted_confirmed**: Dependent was predicted by audit-impact L3 AND confirmed by grep evidence. High confidence.
- **newly_discovered**: Dependent was NOT in audit-impact L3 predictions but found by grep scan. May indicate audit-impact missed this path, or the dependency was created during implementation.

Record `reference_pattern` (the grep pattern used), `evidence` (file:line:content), and `discovery` (predicted_confirmed|newly_discovered).

**Decision Point -- Predicted vs Discovered Impacts:**
- If >30% of impacts are `newly_discovered`: audit-impact L3 may have been incomplete. Flag in L2 report for research phase improvement.
- If a predicted impact is NOT confirmed by grep: the dependency may have been removed during implementation. Mark as `predicted_invalidated` (informational).

**Prioritization**: Verify predicted impacts first (faster, targeted grep). Then scan for unpredicted impacts. Analyze DIRECT dependents before TRANSITIVE. If agent turn budget < 10 remaining, skip TRANSITIVE and report DIRECT-only with `transitive_skipped: true`.

Reference patterns for `.claude/` INFRA files:
- Skill descriptions: INPUT_FROM/OUTPUT_TO values, agent names, skill names
- Agent files: skill names, tool names, path references
- CLAUDE.md: agent names, skill counts, domain names
- Hooks: file paths, agent type names
- Settings: hook script paths, permission patterns

### 5. Produce Impact Report
Generate L1 YAML and L2 markdown:
- Calculate `cascade_recommended` based on decision rules:
  - `true` if `impact_candidates > 0` AND at least one DIRECT dependent exists
  - `true` if `status == partial` AND `confidence == low` (safety: incomplete scan)
  - `false` if all dependents are TRANSITIVE-only (informational)
  - `false` if `impact_candidates == 0` or `status == skipped`
- Set confidence: `high` (map-assisted), `medium` (grep-only), `low` (truncated/partial)

## Quality Gate
- All changed files from manifest have been analyzed
- Every dependent has type classification (DIRECT or TRANSITIVE) with evidence
- `cascade_recommended` decision has explicit rationale in `cascade_rationale`
- L1 YAML is valid and parseable by downstream skills
- Analyst completed within maxTurns (30)

## Degradation Handling

### Full SRC (codebase-map available)
- Map `refd_by` fields provide instant dependent lookup
- Grep validates and supplements map data
- Confidence: `high`
- TRANSITIVE detection: map-assisted 2-hop traversal

### Degraded SRC (grep-only, no map)
- Full `grep -rl` scan for each changed file
- Slower but functionally complete for DIRECT dependencies
- TRANSITIVE detection: sequential grep (grep results of grep results)
- Confidence: `medium`
- Core value (DIRECT dependency detection) fully preserved

### Partial Results
- If analyst maxTurns reached: report analyzed files, set `status: partial`, `confidence: low`
- If individual grep times out: skip that file, note in warnings
- Pipeline continues regardless — partial data is better than no data

## Failure Handling
- **Analyst maxTurns exhausted / all greps fail**: Set `status: partial`, `confidence: low` in L1 output
- **Cascade default on failure**: `cascade_recommended: false` (conservative -- no cascade without evidence)
- **Routing**: Pipeline continues to execution-review regardless; impact analysis is informational, not blocking
- **Pipeline impact**: Non-blocking. Partial or missing impact data does not halt the pipeline

## Anti-Patterns

### DO NOT: Cascade on TRANSITIVE-Only Dependencies
TRANSITIVE dependencies (2-hop) are informational. They indicate potential future impact but do not require immediate code changes. Only DIRECT dependencies (1-hop, literal reference) should trigger cascade. Cascading on TRANSITIVE deps causes unnecessary file modifications.

### DO NOT: Trust Hook Alert as Authoritative
The SubagentStop hook performs a quick grep for preliminary impact detection. This is a trigger signal, not a complete analysis. The hook may miss references that use different naming patterns (e.g., hook greps for filename but the reference uses a function name from that file). Always perform full analyst-driven analysis.

### DO NOT: Analyze Files Outside Changed Set
The analyst should ONLY analyze dependents of files in the change manifest. Do not explore the entire codebase for general dependency issues — that is manage-codebase's job.

### DO NOT: Skip TRANSITIVE When Time-Budgeted
If analyst turns are running low, skip TRANSITIVE analysis (it is optional) but NEVER skip DIRECT analysis. Report `transitive_skipped: true` rather than rushing through an incomplete TRANSITIVE scan.

### DO NOT: Cascade When Dependents Are Already Being Changed
If a dependent file is already in the current pipeline's change set (assigned to an implementer), it does not need cascade updates — it is already being handled. Check the execution-code/infra manifests before recommending cascade.

### DO NOT: Re-Invoke Impact After Cascade
After execution-cascade runs, it has its own convergence checking. Do NOT re-invoke execution-impact after cascade completion — this creates a circular loop. The cascade's analyst-driven convergence check serves the same purpose.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| execution-code | Code file change manifest | L1 YAML: `tasks[].{files[], status}` |
| execution-infra | Infra file change manifest | L1 YAML: `files_changed[]` |
| on-implementer-done.sh | SRC IMPACT ALERT (preliminary) | Hook additionalContext: `changed_files[]`, `preliminary_dependents[]` |
| on-implementer-done.sh | Persistent SRC impact file (supplementary) | File: `/tmp/src-impact-{session_id}.md` with Changed Files + Dependents sections |
| research-coordinator | Predicted propagation paths from audit-impact L3 | L3 file: per-file DIRECT/TRANSITIVE predicted dependents for Shift-Left verification |
| manage-codebase | Codebase dependency map (optional) | File: `.claude/agent-memory/analyst/codebase-map.md` with `refd_by` fields |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-cascade | Impact report with DIRECT dependents | `cascade_recommended: true` |
| execution-review | Impact report (informational) | Always — review uses impact data for context |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Analyst maxTurns exhausted | execution-review (continue) | Partial impact report, `confidence: low` |
| All greps fail | execution-review (continue) | `status: partial`, `cascade_recommended: false` (conservative) |
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
```

### L2
- Per-file dependency analysis with grep evidence (file:line:content)
- DIRECT vs TRANSITIVE classification rationale
- Predicted vs Discovered impact breakdown (predicted_confirmed, newly_discovered, predicted_invalidated counts)
- Cascade recommendation with detailed reasoning
- Degradation notes (if map unavailable or analysis truncated)
- Shift-Left accuracy assessment (% of predictions confirmed)
