---
name: manage-codebase
description: |
  Generates per-file dependency map across .claude/ scope. Creates/updates codebase-map.md with refs, refd_by, hotspot scores. Full scan on first run, incremental after pipeline execution. Max 150 entries, 300 lines.

  Use when: After pipeline execution or major codebase changes. Periodic maintenance.
  WHEN: After pipeline execution completes, after major codebase changes, or periodic maintenance. AI can auto-invoke.
  CONSUMES: .claude/ directory files (Glob+Grep structural references).
  PRODUCES: L1 YAML map health report (entries, mode, staleness), codebase-map.md file.
user-invocable: true
argument-hint: "[full|incremental]"
disable-model-invocation: false
---

# Manage — Codebase

## Execution Model
- **TRIVIAL**: Lead-direct. Quick staleness check or single-file incremental update. No agent spawn.
- **STANDARD**: Spawn 1 analyst (maxTurns:20). Incremental update for 3-8 changed files.
- **COMPLEX**: Spawn 1 analyst (maxTurns:30). Full generation scan of entire `.claude/` scope.

## Phase-Aware Execution
- **Standalone / P0-P1**: Spawn agent with `run_in_background`. Lead reads TaskOutput directly.
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers result via SendMessage micro-signal per conventions.md protocol.

## Methodology

### 1. Determine Mode
Check operating mode based on input:
- **User argument** `full`: Force full regeneration regardless of existing map state
- **User argument** `incremental`: Incremental update only (fail if no map exists)
- **No argument (default)**: Auto-detect — if `codebase-map.md` exists and is valid, use incremental; otherwise full
- **Post-pipeline invocation**: Lead provides list of changed files for incremental update

Check codebase-map.md at `.claude/agent-memory/analyst/codebase-map.md`:
- If file does not exist: switch to full generation
- If file is corrupted (unparseable): delete and regenerate from scratch
- If >30% of entries have `updated` date older than 7 days: recommend full regeneration

### 2. Full Generation (First Run or Recovery)
Spawn analyst agent with `subagent_type: analyst`, `maxTurns: 30`:

1. **Enumerate files**: `Glob .claude/**/*` to list all files in scope
2. **Apply scope filters**:
   - Include: `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.sh`, `.claude/settings.json`, `.claude/CLAUDE.md`, `.claude/projects/*/memory/MEMORY.md`
   - Exclude: `.claude/agent-memory/` (except codebase-map.md tracking), `.claude/agent-memory-local/`, `.claude/projects/*/memory/cc-reference/*`, binary files
3. **For each file**: Grep content for references to other tracked files
   - Reference detection patterns:
     - SKILL.md: INPUT_FROM/OUTPUT_TO values, agent names, skill names
     - Agent .md: skill names, tool names, path references
     - CLAUDE.md: agent names, skill names, domain names
     - Hook .sh: file paths, agent type names
     - settings.json: hook script paths, permission patterns
4. **Build bidirectional refs**: If file A references file B, then A's `refs` includes B and B's `refd_by` includes A
5. **Calculate hotspot scores**: Based on `refd_by` count
6. **Write complete map** to `.claude/agent-memory/analyst/codebase-map.md`

**Full Generation DPS** (STANDARD/COMPLEX tiers):
- **Context**: Scope paths from Scope Boundary section. Exclusion list. Reference detection patterns above.
- **Task**: "Enumerate all .claude/ files within scope filters. For each file, grep for structural references to other tracked files. Build bidirectional refs and calculate hotspot scores. Write complete codebase-map.md."
- **Constraints**: analyst agent, maxTurns:30. Write output to `.claude/agent-memory/analyst/codebase-map.md` only. Max 150 entries / 300 lines.
- **Expected Output**: L1 YAML with entries count, mode: full-generation, hotspot distribution. Complete codebase-map.md file per map schema.
- **Delivery**: Write full result to `/tmp/pipeline/homeostasis-manage-codebase.md`. Send micro-signal to Lead via SendMessage: `{STATUS}|entries:{N}|mode:full|ref:/tmp/pipeline/homeostasis-manage-codebase.md`.

### 3. Incremental Update
For each changed file from pipeline execution:

1. **Re-scan `refs`**: Read file content, grep for references to other tracked files
2. **Update `refd_by` bidirectionally**: Add/remove from referenced files' `refd_by` lists
3. **Handle new files**: If changed file not in map, add new entry with full scan
4. **Handle deleted files**: If file in map no longer exists on filesystem, remove entry and clean `refd_by` references
5. **Handle renames** (detected via git): Remove old entry, add new, update all `refd_by` refs
6. **Recalculate hotspot** for all affected entries
7. **Set `updated` date** to today for all modified entries

For STANDARD/COMPLEX tiers, construct the delegation prompt for the analyst with:
- **Context**: Paste the list of changed files from pipeline execution (from Lead's context or SRC log). Include the current codebase-map.md content (or relevant entries for changed files). Include scope filters and exclusion list.
- **Task**: "For each changed file: (1) Re-scan refs by grepping content for references to other tracked files, (2) Update refd_by bidirectionally, (3) Handle new files (add entry), deleted files (remove entry), renames (old→new). Recalculate hotspot scores. Set updated date."
- **Constraints**: Write output to `.claude/agent-memory/analyst/codebase-map.md` only. Follow the existing map schema. Stay within 150 entries / 300 lines.
- **Expected Output**: L1 YAML with entries updated/added/removed counts, mode: incremental-update. Updated codebase-map.md file.
- **Delivery**: Write full result to `/tmp/pipeline/homeostasis-manage-codebase.md`. Send micro-signal to Lead via SendMessage: `{STATUS}|entries:{N}|mode:{mode}|ref:/tmp/pipeline/homeostasis-manage-codebase.md`.

### 4. Staleness Detection
For each existing entry in the map:
- Compare `updated` date against file's last git modification: `git log --format=%cd --date=short -1 -- {file_path}`
- Files modified after their `updated` date are flagged for re-scan
- Files not found on filesystem are removed immediately
- New `.claude/` files without map entries are flagged for addition
- If >30% of entries are stale: trigger full regeneration instead of incremental

### 5. Write Map and Report
**Map schema** (codebase-map.md):
```markdown
# Codebase Dependency Map
<!-- Generated by manage-codebase skill -->
<!-- Last full scan: {YYYY-MM-DD} -->
<!-- Last incremental: {YYYY-MM-DD} -->
<!-- Entry count: {N} -->
<!-- Scope: .claude/ -->

## {relative/path/to/file}
refs: {comma-separated basenames of files this file references}
refd_by: {comma-separated basenames of files that reference this file}
hotspot: {low|medium|high}
updated: {YYYY-MM-DD}
```

**Hotspot scoring**:

| Score | Condition |
|-------|-----------|
| `high` | `refd_by` count >= 5 |
| `medium` | `refd_by` count 3-4 |
| `low` | `refd_by` count 0-2 |

**Size limits**: Max 150 entries (~300 lines, ~15KB). If exceeding: prune `hotspot: low` entries with oldest `updated` dates first.

## Decision Points

### Mode Selection
- **Auto-detect** (default, no argument): If `codebase-map.md` exists and is valid, use incremental mode. If it doesn't exist or is corrupted, switch to full generation. Safest option for routine invocations.
- **Force full** (`full` argument): Regenerate from scratch regardless of existing map state. Use after major structural changes (e.g., skill domain reorganization, agent renames) where incremental updates would miss cascading reference changes.
- **Force incremental** (`incremental` argument): Update only changed files. Fails if no map exists. Use when Lead provides a specific changed-file list from pipeline execution and full scan is unnecessary.

### Staleness Threshold
- **30% stale triggers full regeneration** (default): When more than 30% of map entries have `updated` dates older than their git modification dates, an incremental update would touch so many entries that full regeneration is more efficient.
- **Accept higher staleness**: For very large maps approaching the 150-entry limit, tolerate up to 50% staleness to avoid costly full scans. Only use when map health is otherwise good (no orphans, no broken refs).

### Pruning Strategy When Exceeding Limits
- **Prune by hotspot+age** (default): Remove `hotspot: low` entries with oldest `updated` dates first. Preserves high-traffic files that are most useful for impact analysis.
- **Prune by scope relevance**: Remove entries outside the current pipeline's scope. Use when the map has grown to include Phase 2 (application source) entries that are no longer actively tracked.

### Bidirectional Inconsistency Handling
- **Full re-scan of affected entries** (default): When A refs B but B doesn't refd_by A, re-scan both files completely. Most accurate but slower.
- **Patch the missing direction**: Simply add the missing reverse reference without re-scanning. Faster but may miss other inconsistencies in those files.

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
- `.claude/agent-memory/` (except codebase-map.md itself — but map does not track itself)
- `.claude/agent-memory-local/`
- `.claude/projects/*/memory/cc-reference/*` (reference docs, not INFRA components)
- `.claude/plugins/`
- Binary files, `.git/`, `node_modules/`

### Phase 2 (Future, Deferred): Application Source Code
- Triggered by user configuration flag
- Would require: separate map file, language-specific reference detection
- NOT part of current SRC implementation scope

## Failure Handling
- **Map corrupted**: Delete and regenerate from scratch (full scan)
- **Map exceeds 300 lines**: Prune lowest-hotspot, oldest-updated entries
- **Filesystem scan timeout**: Produce partial map with `status: partial`
- **Missing entry detected**: Flag for addition on next update
- **Orphaned entry found**: Remove immediately, clean `refd_by` references
- **Bidirectional inconsistency**: Full re-scan of affected entries to fix

## Anti-Patterns

### DO NOT: Track Agent-Memory Files as INFRA Components
Agent-memory directories are volatile runtime data, not structural INFRA components. Including them inflates the map with entries that change constantly, consuming the 150-entry budget with low-value data. Only track the declared scope paths.

### DO NOT: Skip Bidirectional Consistency Checks
Writing `refs` without updating the target's `refd_by` (or vice versa) creates silent inconsistencies that compound over time. Every reference must be written bidirectionally in the same operation.

### DO NOT: Run Full Scan When Incremental Suffices
Full scans of `.claude/` consume 20-30 analyst turns. If only 2-3 files changed, incremental mode completes in 5-10 turns. Always check the changed-file count before selecting mode.

### DO NOT: Include Non-Structural References in refs
Only track structural references (imports, INPUT_FROM/OUTPUT_TO, settings.json paths, hook script references). Content mentions (e.g., a skill's L2 body mentioning another skill as an example) are not structural dependencies and should not appear in refs.

### DO NOT: Allow Map to Exceed 300 Lines Without Pruning
The 300-line limit exists to keep the map readable as context for analysts during impact analysis. Exceeding it degrades the map's utility. Prune proactively when approaching 250 lines.

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
| (user) | Map health report | Always (terminal -- L1/L2 health summary) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Map corrupted | Self (full mode) | Deletes corrupt map, triggers full regeneration |
| Map exceeds 300 lines | Self (prune) | Prune lowest-hotspot, oldest-updated entries |
| Filesystem scan timeout | (user) | Partial map with `status: partial` |
| Incremental fails (no map exists) | Self (full mode) | Switches to full generation automatically |

## Quality Gate
- All entries point to files that exist on filesystem
- `refs` and `refd_by` are bidirectionally consistent (A refs B implies B refd_by A)
- Hotspot scores match threshold criteria
- No entries for excluded paths
- Map within 300-line limit
- Analyst completed within maxTurns (30)

## Output

### L1
```yaml
domain: homeostasis
skill: manage-codebase
status: complete|partial
mode: full-generation|incremental-update|staleness-check
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
