# Execution Impact — Detailed Methodology

> On-demand reference. Contains DPS construction detail, analyst task instructions, tier-specific variations,
> classification algorithms, reference patterns, and Output L2 format.
> Loaded when the SKILL.md summary is insufficient for execution.

## Step 1 — Read File Change Manifest

Load execution-code L1 output (and execution-infra L1 if applicable):
- Extract `tasks[].files` arrays for complete list of changed files
- Cross-reference with SubagentStop hook's SRC IMPACT ALERT (preliminary dependent list)
- Read persistent impact file at `/tmp/src-impact-{session_id}.md` if available
  (written by on-implementer-done.sh; persists across compaction)
- Deduplicate file paths across all sources

## Step 2 — Load Predicted Propagation Paths (Shift-Left)

Load audit-impact L3 predicted propagation paths from research-coordinator output:
- Read the audit-impact L3 file (path passed via research-coordinator or PT metadata)
- Extract predicted DIRECT and TRANSITIVE dependents per changed file
- These predictions were generated during P2 research phase before implementation
- **If audit-impact L3 unavailable** (TRIVIAL/STANDARD tier, or research phase skipped):
  Fall back to codebase-map.md or grep-only (legacy path). Set `prediction_available: false`.

Also check for codebase-map.md at `.claude/agent-memory/analyst/codebase-map.md`:
- **Available and fresh** (<30% stale entries): Use `refd_by` as supplementary lookup. `degradation_level: full`.
- **Unavailable or stale**: Proceed with predicted paths + grep. `degradation_level: degraded`.

## Step 3 — Analyst DPS Construction

### INCLUDE / EXCLUDE / Budget (D11 Cognitive Focus)

- **INCLUDE**: Complete file change manifest (each path + one-line change summary). Audit-impact L3 predictions
  as primary propagation paths to verify first. Codebase-map.md `refd_by` entries if available and fresh
  (supplementary hints only).
- **EXCLUDE**: Implementation detail beyond file paths and change summaries. Full pipeline state. Design
  rationale and ADR history. Other phases' outputs.
- **Budget**: DPS Context field ≤ 30% of analyst effective context.

### Analyst Task Instructions (Predicted-First Pattern)

1. For each changed file, verify predicted impacts from audit-impact L3 — grep each predicted dependent
   to confirm the reference still exists → classify as `predicted_confirmed`.
2. Grep for unpredicted impacts using `<basename_without_extension>` scoped to `.claude/`,
   glob `*.{md,json,sh}` → record as `newly_discovered`.
3. For each match: record evidence triple `{dependent_file, line_number, matching_content}`.
4. Classify as DIRECT (hop_count: 1) or TRANSITIVE (hop_count: 2).
   If no predictions available: fall back to full grep scan (legacy path).

**Constraints**: Read-only. Grep scope: `.claude/`. Exclude: `.git/`, `node_modules/`,
`agent-memory/` (except codebase-map.md), `*.log`. Report partial if approaching turn limit.

### Tier-Specific DPS Variations

| Tier | Analyst Spawn | maxTurns | Notes |
|------|--------------|----------|-------|
| TRIVIAL | Lead-direct grep (no spawn) | — | 1-2 files; quick grep; 5-min max |
| STANDARD | Single analyst | 20 | Include L3 predictions if available; skip TRANSITIVE if DIRECT resolved by turn 15 |
| COMPLEX | Single analyst | 30 | MUST include predictions + map; DIRECT prioritized; report `transitive_skipped: true` near limit |

## Step 4 — Classify Dependents

### Hop Classification
- **DIRECT** (hop_count: 1): File contains literal reference to changed file's name/path/key identifiers.
  Grep match directly links dependent to changed file.
- **TRANSITIVE** (hop_count: 2): File references an intermediate file which references the changed file.
  Max 2-hop enforced.

### Discovery Classification
- **predicted_confirmed**: In audit-impact L3 predictions AND confirmed by grep. High confidence.
- **newly_discovered**: NOT in predictions, found by grep scan. May indicate audit-impact gap or dependency
  created during implementation.
- **predicted_invalidated**: In predictions but NOT confirmed by grep — dependency likely removed during
  implementation. Mark informational only.

### Decision — Predicted vs Discovered Impacts
- If >30% impacts are `newly_discovered`: audit-impact L3 may have been incomplete.
  Flag in L2 report for research phase improvement.
- Prioritize: predicted impacts first (targeted grep) → unpredicted scan → DIRECT before TRANSITIVE →
  skip TRANSITIVE if <10 turns remain (`transitive_skipped: true`).

### Reference Patterns for `.claude/` INFRA Files

| File Type | Reference Patterns to Grep |
|-----------|---------------------------|
| Skill descriptions | INPUT_FROM/OUTPUT_TO values, agent names, skill names |
| Agent files | Skill names, tool names, path references |
| CLAUDE.md | Agent names, skill counts, domain names |
| Hooks | File paths, agent type names |
| Settings | Hook script paths, permission patterns |

## Step 5 — Produce Impact Report

Calculate `cascade_recommended`:
- `true` if `impact_candidates > 0` AND at least one DIRECT dependent exists
- `true` if `status == partial` AND `confidence == low` (safety: incomplete scan)
- `false` if all dependents are TRANSITIVE-only (informational)
- `false` if `impact_candidates == 0` or `status == skipped`

Set confidence:
- `high`: map-assisted analysis (full degradation_level)
- `medium`: grep-only analysis (degraded mode)
- `low`: truncated or partial analysis (maxTurns reached or individual grep timed out)

## Output L2 Detail

The L2 markdown body of `tasks/{team}/p6-impact.md` must contain:
- Per-file dependency analysis with grep evidence (file:line:content) for each dependent
- DIRECT vs TRANSITIVE classification rationale (why each dependent was classified as it was)
- Predicted vs Discovered impact breakdown: predicted_confirmed count, newly_discovered count,
  predicted_invalidated count — with Shift-Left accuracy assessment (% of predictions confirmed)
- Cascade recommendation with detailed reasoning referencing specific dependents
- Degradation notes if map unavailable, analysis truncated, or transitive_skipped
