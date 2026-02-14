---
name: execution-impact
description: |
  [P7·Execution·Impact] Post-implementation dependency analyzer. Spawns researcher to classify dependents of changed files as DIRECT (import/reference) or TRANSITIVE (2-hop). Uses codebase-map.md when available, falls back to grep-only.

  WHEN: After execution-code and/or execution-infra complete. File change manifest exists. SubagentStop hook injected SRC IMPACT ALERT.
  DOMAIN: execution (skill 3 of 5). After code/infra, before cascade.
  INPUT_FROM: execution-code (file change manifest), on-implementer-done.sh (impact alert via additionalContext).
  OUTPUT_TO: execution-cascade (if cascade_recommended), execution-review (if no cascade needed).

  METHODOLOGY: (1) Read execution-code L1 file manifest, (2) Read codebase-map.md if available, (3) Spawn researcher for grep-based reverse reference analysis, (4) Classify: DIRECT (literal ref) vs TRANSITIVE (2-hop), (5) Produce impact report with cascade recommendation.
  OUTPUT_FORMAT: L1 YAML impact report with impacts array, L2 markdown analysis with grep evidence.
user-invocable: false
disable-model-invocation: false
---

# Execution — Impact

## Execution Model
- **TRIVIAL**: Lead-direct. Quick grep check for 1-2 changed files. No researcher spawn.
- **STANDARD**: Spawn 1 researcher. Grep-based reverse reference analysis for 3-8 changed files.
- **COMPLEX**: Spawn 1 researcher with extended maxTurns. Comprehensive analysis for >8 changed files with map-assisted lookups.

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

### 3. Spawn Researcher for Analysis
Spawn researcher agent with `subagent_type: researcher`, `maxTurns: 30`:
- Provide: list of changed files, codebase-map data (if available), grep scope rules
- Researcher performs `grep -rl <basename>` for each changed file within `.claude/` scope
- Grep scope includes: `*.md`, `*.json`, `*.sh` files in `.claude/`
- Grep excludes: `.git/`, `node_modules/`, `agent-memory/` (except codebase-map.md), `*.log`
- For each match: record file path, matching line number, matching content as evidence
- For TRANSITIVE detection: follow 2-hop chains (A refs B, B refs changed file C)

### 4. Classify Dependents
For each dependent file found:
- **DIRECT** (hop_count: 1): File contains a literal reference to the changed file's name, path, or key identifiers. Grep match directly links dependent to changed file.
- **TRANSITIVE** (hop_count: 2): File references an intermediate file, which references the changed file. Max 2-hop limit enforced.
- Record `reference_pattern` (the grep pattern used) and `evidence` (file:line:content)

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
- Researcher completed within maxTurns (30)

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
- If researcher maxTurns reached: report analyzed files, set `status: partial`, `confidence: low`
- If individual grep times out: skip that file, note in warnings
- Pipeline continues regardless — partial data is better than no data

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
