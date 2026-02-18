---
name: manage-codebase
description: >-
  Generates per-file dependency map across .claude/ scope.
  Creates or updates codebase-map.md with refs, refd_by, and
  hotspot scores. Supports full scan or incremental mode. Use
  after pipeline execution, major codebase changes, or periodic
  maintenance. AI can auto-invoke. Reads from .claude/ directory
  files via structural reference scanning. Produces
  codebase-map.md and map health report with entries count,
  mode, and staleness metrics for self-diagnose structural
  analysis. On FAIL (scan timeout or map corruption), Lead
  applies L0 retry; 3+ failures escalate to L4.
  DPS needs changed file list from pipeline execution and
  current codebase-map.md. Exclude historical rationale and
  full pipeline state.
user-invocable: true
argument-hint: "[full|incremental]"
disable-model-invocation: false
---

# Manage — Codebase

## Current Map State
- Codebase map lines: !`wc -l < .claude/agent-memory/analyst/codebase-map.md 2>/dev/null || echo "0"`

## Execution Model
- **TRIVIAL**: Lead-direct. Quick staleness check or single-file incremental update. No agent spawn.
- **STANDARD**: Spawn 1 analyst (maxTurns:20). Incremental update for 3-8 changed files.
- **COMPLEX**: Spawn 1 analyst (maxTurns:30). Full generation scan of entire `.claude/` scope.

## Phase-Aware Execution

P2+ Team mode only. Use 4-channel protocol (Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal to Lead, Ch4 P2P).
Homeostasis utility — no downstream P2P consumers. Write to disk + micro-signal to Lead only.

> D17 Note: Micro-signal format — read `.claude/resources/output-micro-signal-format.md`
> Phase-aware routing details — read `.claude/resources/phase-aware-execution.md`

## Methodology

### 1. Determine Mode
- **`full` argument**: Force full regeneration regardless of existing map state.
- **`incremental` argument**: Incremental update only (fail if no map exists).
- **No argument (default)**: Auto-detect — if `codebase-map.md` exists and is valid, use incremental; otherwise full.
- **Post-pipeline invocation**: Lead provides list of changed files for incremental update.

Check `.claude/agent-memory/analyst/codebase-map.md`:
- Missing → switch to full generation.
- Corrupted (unparseable) → delete and regenerate.
- >30% entries with `updated` older than git modification date → trigger full regeneration.

### 2. Full Generation (First Run or Recovery)

1. `Glob .claude/**/*` — enumerate all files in scope.
2. Apply scope filters (see Scope Boundary section).
3. For each file: grep for structural references using detection patterns — SKILL.md (INPUT_FROM/OUTPUT_TO, agent names), Agent .md (skill names, tool names), CLAUDE.md (domain names), Hook .sh (file paths), settings.json (hook paths).
4. Build bidirectional refs: A refs B → B's `refd_by` includes A.
5. Calculate hotspot scores by `refd_by` count.
6. Write complete map to `.claude/agent-memory/analyst/codebase-map.md`.

> For Full Generation DPS template: read `resources/methodology.md`

### 3. Incremental Update

For each changed file from pipeline execution:
1. Re-scan `refs` by grepping content for tracked-file references.
2. Update `refd_by` bidirectionally — add/remove as needed.
3. New files → add entry. Deleted files → remove entry + clean `refd_by`. Renames → old→new + update all `refd_by`.
4. Recalculate hotspot for affected entries. Set `updated` to today.

> For Incremental Update DPS template: read `resources/methodology.md`

### 4. Staleness Detection

Compare `updated` vs git modification (`git log --format=%cd --date=short -1 -- {file_path}`).
Flag stale files for re-scan. Remove missing-filesystem entries. Add new `.claude/` files without entries.
If >30% stale → trigger full regeneration.

### 5. Write Map and Report

Write updated map to `.claude/agent-memory/analyst/codebase-map.md`.

> For map schema format and hotspot scoring table: read `resources/methodology.md`

## Decision Points

### Mode Selection
- **Auto-detect** (default): If `codebase-map.md` valid → incremental. If missing/corrupted → full.
- **Force full** (`full`): Use after major structural changes (skill domain reorganization, agent renames).
- **Force incremental** (`incremental`): Use when Lead provides specific changed-file list. Fails without existing map.

> For staleness threshold, pruning strategy, and bidirectional handling details: read `resources/methodology.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Scope Boundary

### Phase 1 (Current): `.claude/` Directory Only

**Included paths:**
- `.claude/agents/*.md`
- `.claude/skills/*/SKILL.md`
- `.claude/hooks/*.sh`
- `.claude/settings.json`
- `.claude/CLAUDE.md`
- `.claude/projects/*/memory/MEMORY.md`

**Excluded paths:**
- `.claude/agent-memory/` (except codebase-map.md itself)
- `.claude/agent-memory-local/`
- `.claude/projects/*/memory/cc-reference/*`
- `.claude/plugins/`
- Binary files, `.git/`, `node_modules/`

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| Filesystem scan timeout or partial read | L0 Retry | Re-invoke same analyst with same DPS |
| Analyst output missing hotspot scoring or bidirectional refs | L1 Nudge | SendMessage with refined reference detection patterns |
| Analyst stuck, map corrupted on repeated attempts | L2 Respawn | Kill → fresh analyst with force-full mode DPS |
| Map size limit exceeded and incremental fails repeatedly | L3 Restructure | Switch to targeted scan by scope segment, prune aggressively |
| 3+ L2 failures or scan structurally blocked | L4 Escalate | AskUserQuestion with situation summary and options |

- **Map corrupted**: Delete and regenerate (full scan).
- **Map exceeds 300 lines**: Prune lowest-hotspot, oldest-updated entries.
- **Orphaned entry found**: Remove immediately, clean `refd_by` references.

## Anti-Patterns

### DO NOT: Track Agent-Memory Files as INFRA Components
Agent-memory directories are volatile runtime data. Including them inflates the map with entries that change constantly, consuming the 150-entry budget with low-value data.

### DO NOT: Skip Bidirectional Consistency Checks
Writing `refs` without updating the target's `refd_by` creates silent inconsistencies that compound over time. Every reference must be written bidirectionally in the same operation.

### DO NOT: Run Full Scan When Incremental Suffices
Full scans consume 20-30 analyst turns. If only 2-3 files changed, incremental completes in 5-10 turns. Always check changed-file count before selecting mode.

### DO NOT: Include Non-Structural References in refs
Only track structural references (imports, INPUT_FROM/OUTPUT_TO, settings.json paths, hook script references). Content mentions of other skills are not structural dependencies.

### DO NOT: Allow Map to Exceed 300 Lines Without Pruning
The 300-line limit keeps the map readable as context for analysts. Prune proactively when approaching 250 lines.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (self-triggered) | Periodic maintenance or post-pipeline invocation | User argument: `full` or `incremental`, or auto-detect |
| execution-impact | Changed file list from pipeline execution | L1 YAML: file change manifest with paths |
| delivery-pipeline | Post-delivery map update request | L1 YAML: pipeline completion status with changed files |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (filesystem) | Updated codebase-map.md | Always (writes to `.claude/agent-memory/analyst/codebase-map.md`) |
| execution-impact | Fresh dependency data for impact analysis | When impact analysis requests codebase-map data |
| (user) | Map health report | Always (terminal — L1/L2 health summary) |

> D17 Note: 4-channel protocol (Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal, Ch4 P2P) — format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- All entries point to existing filesystem files. No entries for excluded paths.
- `refs` and `refd_by` bidirectionally consistent (A refs B → B refd_by A).
- Hotspot scores match threshold criteria. Map within 300-line limit.
- Analyst completed within maxTurns (30).

## Output

### L1
```yaml
domain: homeostasis
skill: manage-codebase
status: complete|partial
mode: full-generation|incremental-update|staleness-check
pt_signal: "metadata.phase_signals.homeostasis"
signal_format: "{STATUS}|entries:{N}|mode:{mode}|ref:tasks/{team}/homeostasis-manage-codebase.md"
entries: 0
stale_entries_removed: 0
new_entries_added: 0
entries_updated: 0
map_path: ".claude/agent-memory/analyst/codebase-map.md"
staleness_report:
  total_entries: 0
  stale_count: 0
  missing_count: 0
  recommendation: "none|incremental|full-regeneration"
```

### L2
- Mode selection rationale (full vs incremental)
- Files scanned and references discovered
- Staleness detection results
- Entries added, updated, or removed
- Map health summary with hotspot distribution
