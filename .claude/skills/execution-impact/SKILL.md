---
name: execution-impact
description: |
  [P7·Execution·Impact] Post-implementation dependency analyzer. Spawns analyst to classify dependents of changed files as DIRECT (import/reference) or TRANSITIVE (2-hop). Uses codebase-map.md when available, falls back to grep-only.

  WHEN: After execution-code and/or execution-infra complete. File change manifest exists. SubagentStop hook injected SRC IMPACT ALERT.
  DOMAIN: execution (skill 3 of 5). After code/infra, before cascade.
  INPUT_FROM: execution-code (file change manifest), on-implementer-done.sh (impact alert via additionalContext).
  OUTPUT_TO: execution-cascade (if cascade_recommended), execution-review (if no cascade needed).

  METHODOLOGY: (1) Read execution-code L1 file manifest, (2) Read codebase-map.md if available, (3) Spawn analyst for grep-based reverse reference analysis, (4) Classify: DIRECT (literal ref) vs TRANSITIVE (2-hop), (5) Produce impact report with cascade recommendation.
  OUTPUT_FORMAT: L1 YAML impact report with impacts array, L2 markdown analysis with grep evidence.
user-invocable: false
disable-model-invocation: false
---

# Execution — Impact

## Execution Model
- **TRIVIAL**: Lead-direct. Quick grep check for 1-2 changed files. No analyst spawn.
- **STANDARD**: Spawn 1 analyst. Grep-based reverse reference analysis for 3-8 changed files.
- **COMPLEX**: Spawn 1 analyst with extended maxTurns. Comprehensive analysis for >8 changed files with map-assisted lookups.

## Methodology

### 1. Read File Change Manifest
Load execution-code L1 output (and execution-infra L1 if applicable):
- Extract `tasks[].files` arrays for complete list of changed files
- Cross-reference with SubagentStop hook's SRC IMPACT ALERT (preliminary dependent list)
- Deduplicate file paths across all sources

### 2. Load Codebase Map (Optional)
Check for codebase-map.md at `.claude/agent-memory/analyst/codebase-map.md`:
- **If available and fresh** (<30% stale entries): Use `refd_by` fields for fast dependent lookup, supplement with grep for new files not yet in map. Set `degradation_level: full`.
- **If unavailable or stale**: Proceed with grep-only analysis. Set `degradation_level: degraded`.
- Map availability determines `confidence` level in L1 output (high vs medium).

### 3. Spawn Analyst for Analysis
Spawn analyst agent with `subagent_type: analyst`, `maxTurns: 30`.

Construct the delegation prompt with:
- **Context**: Paste the complete file change manifest — each changed file path and a one-line summary of what changed (e.g., "renamed function X to Y", "added field Z to frontmatter"). If codebase-map.md exists and is fresh, paste its `refd_by` entries for each changed file as pre-computed dependent hints.
- **Task**: For each changed file, run `Grep` with pattern `<basename_without_extension>` scoped to `.claude/` directory. Use glob `*.{md,json,sh}` for file filtering. For each match, record a structured evidence triple: `{dependent_file, line_number, matching_content}`. Then classify each dependent as DIRECT (hop_count: 1, literal reference to changed file) or TRANSITIVE (hop_count: 2, references an intermediate that references the changed file — run a second grep on DIRECT dependents to detect 2-hop chains).
- **Constraints**: Read-only analysis — do NOT modify any files. Grep scope limited to `.claude/` directory. Exclude: `.git/`, `node_modules/`, `agent-memory/` (except codebase-map.md), `*.log`. Max 30 turns — if approaching limit, report partial results for files already analyzed rather than rushing remaining files.
- **Expected Output**: Return a structured impact report: for each changed file, list its dependents with `{file, type: DIRECT|TRANSITIVE, hop_count: 1|2, reference_pattern, evidence: "file:line:content"}`. End with a summary: total dependents found, DIRECT count, TRANSITIVE count, and cascade recommendation (true if any DIRECT dependents exist).

### 4. Classify Dependents
For each dependent file found:
- **DIRECT** (hop_count: 1): File contains a literal reference to the changed file's name, path, or key identifiers. Grep match directly links dependent to changed file.
- **TRANSITIVE** (hop_count: 2): File references an intermediate file, which references the changed file. Max 2-hop limit enforced.
- Record `reference_pattern` (the grep pattern used) and `evidence` (file:line:content)

**Prioritization**: Analyze DIRECT dependents first (complete all). Pursue TRANSITIVE chains only for high-hotspot files or files in critical path. If agent turn budget < 10 remaining, skip TRANSITIVE and report DIRECT-only with `transitive_skipped: true`.

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
cascade_recommended: true|false
cascade_rationale: ""
```

### L2
- Per-file dependency analysis with grep evidence (file:line:content)
- DIRECT vs TRANSITIVE classification rationale
- Cascade recommendation with detailed reasoning
- Degradation notes (if map unavailable or analysis truncated)
