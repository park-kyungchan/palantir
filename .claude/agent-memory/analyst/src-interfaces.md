# SRC Interface Contracts

> Analyst output | 2026-02-14 | Design-Interface (P2)
> Scope: All 6 inter-component boundaries in the SRC (Smart Reactive Codebase) system
> Inputs: src-architecture.md (P2 architecture), cc-reference/* (hook I/O schemas)
> Companion: src-architecture.md (component specs, ADRs, data flow)

---

## Interface Registry

| # | Boundary | Protocol | Format | Max Size | Error Fallback |
|---|----------|----------|--------|----------|----------------|
| B1 | on-file-change.sh <-> Change Log | async, non-blocking | TSV append to /tmp file | unbounded (typ. <5KB/session) | silent no-op (exit 0) |
| B2 | Change Log <-> on-implementer-done.sh | sync read at SubagentStop | TSV file -> additionalContext JSON | 500 chars output | "No file changes detected" |
| B3 | additionalContext <-> Lead Routing | sync, single-turn injection | natural language text | 500 chars | Lead proceeds without SRC |
| B4 | execution-impact L1 <-> execution-cascade | sync, Lead-mediated handoff | YAML L1 report | ~2KB L1 | cascade skipped if no impacts |
| B5 | execution-cascade <-> Recursive Impact | sync, iterative loop | internal state + grep check | 3 iterations max | partial status, pipeline continues |
| B6 | Pipeline <-> manage-codebase (map) | async, post-pipeline | markdown (grep-parseable) | 300 lines / ~15KB | full regeneration on corruption |

---

## Boundary 1: on-file-change.sh <-> Change Log File

### Protocol
- **Type**: Async, non-blocking, fire-and-forget
- **Trigger**: PostToolUse hook with matcher `Edit|Write` (regex OR)
- **Direction**: Hook script (producer) -> /tmp file (append-only store)
- **Blocking**: No. `async: true` in settings.json. Implementer continues immediately.
- **Scope**: Fires in the IMPLEMENTER's process context (not Lead's). No additionalContext output.

### Input Schema (PostToolUse stdin JSON)

The CC runtime delivers a JSON object on stdin. The schema varies slightly between Edit and Write tools.

**Common fields (both Edit and Write):**
```json
{
  "session_id": "string (UUID)",
  "transcript_path": "string (path to session transcript)",
  "cwd": "string (current working directory)",
  "permission_mode": "string (default|acceptEdits|...)",
  "hook_event_name": "PostToolUse",
  "tool_name": "Edit | Write",
  "tool_input": {
    "file_path": "string (ABSOLUTE path to target file)"
  },
  "tool_response": {
    "filePath": "string (absolute path, echoed back)",
    "success": "boolean"
  },
  "tool_use_id": "string (toolu_01...)"
}
```

**Edit-specific tool_input fields (present but IGNORED by hook):**
```json
{
  "tool_input": {
    "file_path": "/home/palantir/.claude/skills/example/SKILL.md",
    "old_string": "string (text being replaced)",
    "new_string": "string (replacement text)",
    "replace_all": "boolean (default false)"
  }
}
```

**Write-specific tool_input fields (present but IGNORED by hook):**
```json
{
  "tool_input": {
    "file_path": "/home/palantir/.claude/skills/example/SKILL.md",
    "content": "string (full file content)"
  }
}
```

**Extraction contract**: The hook reads ONLY three fields:
1. `session_id` -- for log file naming
2. `tool_name` -- for the TSV tool column
3. `tool_input.file_path` -- for the TSV path column

All other fields are ignored. This minimizes coupling to CC internal schema changes.

### Output Schema (TSV line to /tmp file)

**File path**: `/tmp/src-changes-{session_id}.log`
- `{session_id}` is the literal UUID from stdin JSON (no transformation)
- Example: `/tmp/src-changes-a1b2c3d4-e5f6-7890-abcd-ef1234567890.log`

**Line format** (one line per successful tool call):
```
{ISO-8601-timestamp}\t{tool_name}\t{absolute_file_path}\n
```

**Field definitions:**

| Field | Format | Example | Source |
|-------|--------|---------|--------|
| timestamp | ISO-8601 with seconds | `2026-02-14T15:30:42+09:00` | `date -Iseconds` |
| tool_name | `Edit` or `Write` | `Edit` | `jq -r '.tool_name'` |
| file_path | Absolute POSIX path | `/home/palantir/.claude/skills/execution-code/SKILL.md` | `jq -r '.tool_input.file_path'` |

**Separator**: literal tab character (`\t`). Fields MUST NOT contain tabs (file paths and tool names never do).

**Line terminator**: newline (`\n`). Each line is self-contained and parseable independently.

**Sample log file content:**
```
2026-02-14T15:30:42+09:00	Edit	/home/palantir/.claude/skills/execution-code/SKILL.md
2026-02-14T15:30:45+09:00	Write	/home/palantir/.claude/hooks/on-file-change.sh
2026-02-14T15:31:02+09:00	Edit	/home/palantir/.claude/settings.json
2026-02-14T15:31:02+09:00	Edit	/home/palantir/.claude/settings.json
```

Note: Duplicate entries are expected and valid (same file edited multiple times). Deduplication happens at Boundary 2.

### Error Contract

| Failure Mode | Detection | Behavior | Rationale |
|-------------|-----------|----------|-----------|
| jq not installed | `command -v jq` returns non-zero | `exit 0` (silent no-op) | Never block implementer |
| jq parse error | `jq -r` returns non-zero | `exit 0` (silent no-op) | Malformed JSON = CC bug, not our problem |
| `session_id` missing/null | jq returns `null` | `exit 0` (skip logging) | Cannot create unique log file |
| `tool_input.file_path` missing | jq returns `null` | `exit 0` (skip this line) | Nothing meaningful to log |
| `tool_response.success` is false | jq check | `exit 0` (skip this line) | Only log successful changes |
| /tmp write fails (disk full, permissions) | redirect `>>` returns non-zero | `exit 0` (silent no-op) | /tmp failure = OS issue |
| Hook timeout (>5s) | CC runtime kills process | Hook terminated, no effect | 5s is generous for append |

**Invariant**: This hook NEVER returns a non-zero exit code. NEVER produces stdout output. NEVER produces visible stderr. It is invisible to the implementer agent.

### Concurrency Contract

**Scenario**: COMPLEX tier with 3-4 parallel implementers, all editing files simultaneously.

**Safety guarantees**:
1. Each implementer triggers its own PostToolUse hook invocation (separate process)
2. All processes append to the SAME log file (`session_id` is shared across implementers in one session)
3. POSIX guarantees: `write()` calls less than `PIPE_BUF` (4096 bytes on Linux) to a file opened with `O_APPEND` are atomic
4. Our TSV lines are ~120 bytes maximum (well under 4096)
5. Therefore: concurrent appends will NOT interleave within a single line

**Not guaranteed**: Line ORDER across concurrent implementers. Lines from implementer A and B may interleave arbitrarily. This is acceptable because Boundary 2 deduplicates by file path, not by timestamp order.

---

## Boundary 2: Change Log File <-> on-implementer-done.sh

### Protocol
- **Type**: Sync, blocking
- **Trigger**: SubagentStop hook with matcher `implementer`
- **Direction**: /tmp file (read) -> Hook script (processor) -> additionalContext JSON (output)
- **Blocking**: Yes (no `async` flag). Lead waits for completion (max 15s timeout).
- **Scope**: Fires in LEAD's process context. additionalContext injected into Lead.

### Input Schema (SubagentStop stdin JSON)

```json
{
  "session_id": "string (UUID, same as used in Boundary 1)",
  "hook_event_name": "SubagentStop",
  "agent_id": "string (agent-specific identifier, e.g., agent-def456)",
  "agent_type": "implementer",
  "agent_transcript_path": "string (path to subagent transcript JSONL)",
  "stop_hook_active": "boolean (false normally)"
}
```

**Extraction contract**: The hook reads:
1. `session_id` -- to locate the change log file at `/tmp/src-changes-{session_id}.log`
2. `agent_type` -- already matched by settings.json matcher, but validated defensively

### Processing Pipeline

```
[Read log file]
    |
    v
[Extract file_path column (cut -f3)]
    |
    v
[Sort + deduplicate (sort -u)]
    |
    v
[For each unique path: grep -rl <basename> <repo_root>]
    |
    v
[Exclude self-references and noise directories]
    |
    v
[Deduplicate grep results]
    |
    v
[Format as additionalContext (500 char max)]
    |
    v
[Output JSON to stdout]
```

**Step 1 -- Read log file:**
```bash
LOG_FILE="/tmp/src-changes-${SESSION_ID}.log"
```

**Step 2 -- Extract unique changed files:**
```bash
CHANGED_FILES=$(cut -f3 "$LOG_FILE" | sort -u)
```

**Step 3 -- Reverse-reference grep for each changed file:**
```bash
for FILE in $CHANGED_FILES; do
  BASENAME=$(basename "$FILE" | sed 's/\.[^.]*$//')  # Strip extension for broader matching
  grep -rl "$BASENAME" /home/palantir/.claude/ \
    --include='*.md' --include='*.json' --include='*.sh' \
    --exclude-dir='.git' --exclude-dir='node_modules' \
    --exclude-dir='agent-memory' \
    | grep -v "$FILE"  # Exclude self-reference
done
```

**Step 4 -- Grep scope and exclusions:**

| Include | Rationale |
|---------|-----------|
| `/home/palantir/.claude/` | SRC Phase 1 scope |
| `*.md`, `*.json`, `*.sh` | INFRA file types |

| Exclude | Rationale |
|---------|-----------|
| `.git/` | Version control internals |
| `node_modules/` | Dependencies |
| `agent-memory/` | Volatile analysis artifacts |
| `*.log` | Log files |
| The changed file itself | Self-reference is not a dependent |

**Step 5 -- Timeout enforcement:**
```bash
timeout 10 grep -rl ...
```
Each grep invocation wrapped in `timeout 10`. If any single grep exceeds 10s, it is killed and partial results used.

### Output Schema (additionalContext JSON)

**Stdout JSON format:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStop",
    "additionalContext": "SRC IMPACT ALERT: {N} files changed, {M} potential dependents detected.\nChanged: {file1}, {file2}, ...\nDependents: {dep1} (refs {file1}), {dep2} (refs {file1}, {file2}), ...\nAction: Consider running /execution-impact for full analysis."
  }
}
```

**additionalContext text format (multi-line string, max 500 chars):**

```
SRC IMPACT ALERT: {N} files changed, {M} potential dependents detected.
Changed: {file1}, {file2}, ...
Dependents: {dep1} (refs {file1}), {dep2} (refs {file1}, {file2}), ...
Action: Consider running /execution-impact for full analysis.
```

**Field definitions within the text:**

| Placeholder | Type | Source | Example |
|-------------|------|--------|---------|
| `{N}` | integer | `wc -l` of deduplicated changed files | `3` |
| `{M}` | integer | Count of unique dependent files from grep | `7` |
| `{fileN}` | basename | `basename` of changed file | `SKILL.md` |
| `{depN}` | relative path | Path relative to project root | `.claude/agents/implementer.md` |
| `(refs ...)` | basename list | Which changed files are referenced by this dependent | `(refs SKILL.md, settings.json)` |

**Truncation rule**: If the full message exceeds 500 characters:
1. Keep the header line ("SRC IMPACT ALERT: ...") -- always present
2. Keep "Changed:" line -- truncate file list with `... and {K} more`
3. Truncate "Dependents:" list first -- replace tail with `... and {K} more. Run /execution-impact for full list.`
4. Always keep "Action:" line

**Sample full output (under 500 chars):**
```
SRC IMPACT ALERT: 2 files changed, 4 potential dependents detected.
Changed: execution-code/SKILL.md, settings.json
Dependents: manage-skills/SKILL.md (refs execution-code/SKILL.md), verify-consistency/SKILL.md (refs execution-code/SKILL.md), on-subagent-start.sh (refs settings.json), CLAUDE.md (refs settings.json)
Action: Consider running /execution-impact for full analysis.
```

**Sample truncated output (over 500 chars):**
```
SRC IMPACT ALERT: 8 files changed, 23 potential dependents detected.
Changed: SKILL.md, settings.json, implementer.md, ... and 5 more
Dependents: manage-skills/SKILL.md (refs SKILL.md), verify-consistency/SKILL.md (refs SKILL.md), ... and 21 more.
Action: Run /execution-impact for full list.
```

### Error Contract

| Failure Mode | Detection | Output | Exit Code |
|-------------|-----------|--------|-----------|
| Log file does not exist | `[ ! -f "$LOG_FILE" ]` | `"SRC: No file changes detected."` | 0 |
| Log file is empty | `[ ! -s "$LOG_FILE" ]` | `"SRC: No file changes detected."` | 0 |
| Log file has only failed entries | `cut -f3` yields empty after filter | `"SRC: 0 impact candidates for 0 changed files."` | 0 |
| jq not installed | `command -v jq` fails | Raw JSON string via echo (fallback) | 0 |
| grep finds no dependents | All grep -rl return exit 1 (no match) | `"SRC: 0 impact candidates for {N} changed files."` | 0 |
| grep timeout (>10s per file) | `timeout 10` kills process | Truncated results + `"... analysis truncated (timeout)"` | 0 |
| grep error (permission denied) | grep exit code > 1 | Skip that file, continue with remaining | 0 |
| JSON output encoding error | jq fails | Fallback to printf-escaped JSON | 0 |

**Invariant**: This hook ALWAYS exits 0. ALWAYS produces valid JSON stdout (even if additionalContext is a minimal fallback message). Lead always receives some form of SRC status.

### Multi-Implementer Behavior

| Scenario | Behavior |
|----------|----------|
| 1st implementer stops | Reads FULL accumulated log (may contain only its changes). Produces alert for Lead. |
| 2nd implementer stops | Reads FULL accumulated log (contains 1st + 2nd implementer changes). Deduplication prevents re-alerting on already-seen files. |
| Parallel implementers stop near-simultaneously | Two SubagentStop hooks fire independently. Each reads the log as-is at that moment. Some overlap in reported files is possible. Lead receives two alerts. |
| Log cleanup | Log is NOT cleared between implementer stops. Accumulates for the entire session. Cleanup: /tmp auto-expiry, or explicit cleanup when execution-impact skill runs. |

---

## Boundary 3: on-implementer-done.sh additionalContext <-> Lead Routing

### Protocol
- **Type**: Sync, single-turn context injection
- **Direction**: SubagentStop hook output -> Lead's system context -> Lead's next reasoning step
- **Lifecycle**: additionalContext is injected for ONE TURN only. It does NOT persist in conversation history. Lead must act on it immediately or the signal is lost.
- **Visibility**: Not visible in user-facing conversation transcript. System-level injection only.

### Input Schema (additionalContext text)

Lead receives the exact text string from Boundary 2's `additionalContext` field. The text follows one of these patterns:

**Pattern 1 -- Impact detected (normal case):**
```
SRC IMPACT ALERT: {N} files changed, {M} potential dependents detected.
Changed: {file1}, {file2}, ...
Dependents: {dep1} (refs {file1}), {dep2} (refs {file1}, {file2}), ...
Action: Consider running /execution-impact for full analysis.
```

**Pattern 2 -- No changes detected:**
```
SRC: No file changes detected.
```

**Pattern 3 -- Changes but no dependents:**
```
SRC: 0 impact candidates for {N} changed files.
```

**Pattern 4 -- Truncated analysis:**
```
SRC IMPACT ALERT: {N} files changed, {M} potential dependents detected.
Changed: {file1}, ... and {K} more
Dependents: {dep1}, ... and {K} more.
Action: Run /execution-impact for full list.
```

### Lead Parsing Contract

Lead does NOT parse this as structured data. Lead reads it as natural language context and makes a routing decision based on semantic understanding. The key parsing signals are:

| Signal | Presence | Lead Interpretation |
|--------|----------|-------------------|
| `SRC IMPACT ALERT:` prefix | Present | Impact analysis warranted |
| `SRC IMPACT ALERT:` prefix | Absent | No impact analysis needed |
| `{M} potential dependents detected` | M > 0 | Dependents exist, invoke execution-impact |
| `{M} potential dependents detected` | M = 0 | No dependents, skip impact analysis |
| `0 impact candidates` | Present | Safe to skip execution-impact |
| `No file changes detected` | Present | Safe to skip execution-impact |
| `... analysis truncated` | Present | Partial data, execution-impact strongly recommended |

### Routing Decision Matrix

| additionalContext Pattern | Lead Action | Next Skill |
|--------------------------|-------------|------------|
| Pattern 1 (M > 0) | Invoke execution-impact with changed file list | execution-impact |
| Pattern 1 (M = 0, impossible given header) | N/A | N/A |
| Pattern 2 (no changes) | Skip impact analysis | execution-review |
| Pattern 3 (no dependents) | Skip impact analysis | execution-review |
| Pattern 4 (truncated) | Invoke execution-impact (data may be incomplete) | execution-impact |
| No additionalContext received (hook failed) | Proceed without SRC (No SRC degradation) | execution-review |
| During active cascade (Lead in cascade loop) | Ignore SubagentStop alert (avoid recursive analysis) | Continue cascade iteration |

### Data Passed to execution-impact

When Lead decides to invoke execution-impact, it includes in the skill arguments:
1. The original additionalContext text (quick reference)
2. The execution-code L1 output (authoritative file change manifest)
3. Optionally: reference to codebase-map.md path for enhanced analysis

Lead does NOT rely solely on the additionalContext for file lists. The execution-code L1 `tasks[].files` array is the authoritative source. The additionalContext serves as a triggering signal and preliminary dependent list.

### Error Contract

| Failure Mode | Lead Observation | Lead Behavior |
|-------------|-----------------|---------------|
| No additionalContext received | No "SRC" text in context after implementer stop | Proceed to execution-review (No SRC degradation level) |
| Malformed additionalContext | Text present but does not match any pattern | Treat as informational, proceed to execution-review |
| additionalContext lost to compaction | Context compacted between hook fire and Lead processing | Signal lost permanently. Lead re-reads implementer L1 for file list. No SRC for this cycle. |
| Duplicate alerts (parallel implementers) | Multiple "SRC IMPACT ALERT" strings in context | Lead processes the LAST/most complete alert, ignores earlier ones |

---

## Boundary 4: execution-impact L1/L2 <-> execution-cascade

### Protocol
- **Type**: Sync, Lead-mediated handoff
- **Direction**: execution-impact (researcher output) -> Lead (reads and routes) -> execution-cascade (receives as input)
- **Mediator**: Lead reads the execution-impact L1, evaluates `cascade_recommended`, and either invokes execution-cascade or skips to execution-review.

### execution-impact L1 Output Schema (YAML)

```yaml
# execution-impact L1 output
domain: execution                    # FIXED: always "execution"
skill: impact                        # FIXED: always "impact"
status: complete|partial|skipped     # See status definitions below
confidence: high|medium|low          # See confidence definitions below
files_changed: 0                     # Integer: count of unique files in change manifest
impact_candidates: 0                 # Integer: count of unique dependent files identified
degradation_level: full|degraded     # SRC operating level during this analysis
impacts:                             # Array: one entry per changed file with dependents
  - changed_file: ""                 # String: absolute path to changed file
    dependents:                      # Array: files that depend on changed_file
      - file: ""                     # String: absolute path to dependent file
        type: DIRECT|TRANSITIVE      # Classification (see ADR-SRC-4)
        hop_count: 1|2               # Integer: 1 for DIRECT, 2 for TRANSITIVE
        reference_pattern: ""        # String: the grep pattern that matched
        evidence: ""                 # String: "file:line_number:matched_line" from grep
    dependent_count: 0               # Integer: count of dependents for this file
cascade_recommended: true|false      # Boolean: Lead's routing signal (see decision rules)
cascade_rationale: ""                # String: why cascade is/isn't recommended
```

**Status definitions:**

| Value | Meaning | Cause |
|-------|---------|-------|
| `complete` | All changed files analyzed, all grep scans finished | Normal completion |
| `partial` | Some files analyzed but analysis was truncated | Researcher maxTurns (30) reached, or timeout |
| `skipped` | No analysis performed | No files changed, or input data missing |

**Confidence definitions:**

| Value | Meaning | Conditions |
|-------|---------|------------|
| `high` | Full coverage, map-assisted | codebase-map.md available AND fresh, all greps completed |
| `medium` | Grep-only mode | codebase-map.md unavailable or stale, all greps completed |
| `low` | Partial analysis | Researcher truncated, some files not scanned |

**cascade_recommended decision rules:**

| Condition | Value | Rationale |
|-----------|-------|-----------|
| `impact_candidates > 0` AND at least one DIRECT dependent | `true` | Direct dependents likely need updating |
| `impact_candidates > 0` AND all TRANSITIVE only | `false` | Transitive-only impacts are informational, not actionable |
| `impact_candidates == 0` | `false` | Nothing to cascade |
| `status == skipped` | `false` | No data to cascade from |
| `status == partial` AND `confidence == low` | `true` | Incomplete scan means undetected impacts likely; cascade for safety |

### execution-impact L2 Output Schema (Markdown)

```markdown
# Execution Impact Analysis Report

## Summary
- Files changed: {N}
- Impact candidates: {M}
- Confidence: {high|medium|low}
- Degradation level: {full|degraded}
- Cascade recommended: {yes|no}

## Per-File Analysis

### {changed_file_1}
**Dependents ({count}):**

| Dependent | Type | Hop | Reference Pattern | Evidence |
|-----------|------|-----|-------------------|----------|
| {dep_path} | DIRECT | 1 | {grep_pattern} | {file}:{line}:{content} |
| {dep_path} | TRANSITIVE | 2 | {grep_pattern} via {intermediate} | {file}:{line}:{content} |

### {changed_file_2}
...

## Cascade Recommendation
{Rationale paragraph explaining why cascade is/isn't recommended}

## Notes
- {Any warnings, partial results, or degradation notes}
```

### Decision Point: cascade_recommended Semantics

Lead reads `cascade_recommended` from execution-impact L1 and routes accordingly:

```
[Lead reads execution-impact L1]
    |
    |-- cascade_recommended: true
    |       |
    |       v
    |   [Lead invokes execution-cascade]
    |       Input: execution-impact L1 (full YAML)
    |       Input: execution-impact L2 (detailed evidence)
    |
    |-- cascade_recommended: false
    |       |
    |       v
    |   [Lead logs "SRC: No cascade needed" in conversation]
    |   [Lead proceeds to execution-review]
    |
    |-- status: skipped (edge case)
            |
            v
        [Lead proceeds to execution-review directly]
```

### Handoff Data: What execution-cascade Receives

execution-cascade receives the FULL execution-impact output (both L1 and L2) via Lead's conversation context. Specifically:

| Data Item | Source | Purpose in Cascade |
|-----------|--------|--------------------|
| `impacts[].changed_file` | L1 | Know what changed (root cause) |
| `impacts[].dependents[].file` | L1 | Files to update |
| `impacts[].dependents[].type` | L1 | Prioritize DIRECT over TRANSITIVE |
| `impacts[].dependents[].reference_pattern` | L1 | What to look for in dependent file |
| `impacts[].dependents[].evidence` | L1 | Exact line needing update |
| L2 per-file analysis sections | L2 | Detailed context for implementers |
| `cascade_rationale` | L1 | Understanding of why cascade is needed |

### Error Contract

| Failure Mode | Detection | Cascade Behavior |
|-------------|-----------|-----------------|
| execution-impact returns `status: partial` | Lead reads L1 | Lead invokes cascade with partial data + logs warning |
| execution-impact returns `confidence: low` | Lead reads L1 | Cascade proceeds but with extra caution; review flags low-confidence items |
| execution-impact L1 YAML malformed | Lead cannot parse impacts array | Lead skips cascade, proceeds to execution-review with warning |
| execution-impact researcher times out (maxTurns) | L1 status will be `partial` | Same as partial case above |
| No impacts found after full analysis | `impact_candidates: 0` | `cascade_recommended: false`, Lead skips cascade |
| impacts array present but dependents empty for all | All `dependent_count: 0` | `cascade_recommended: false`, Lead skips cascade |

---

## Boundary 5: execution-cascade <-> Recursive Impact Check

### Protocol
- **Type**: Sync, iterative loop with convergence detection
- **Direction**: Circular within execution-cascade skill scope:
  cascade iteration -> implementer spawns -> change detection -> grep re-check -> next iteration (or converge)
- **Mediator**: Lead orchestrates each iteration. Lead spawns implementers, waits for completion, runs convergence check, decides next step.
- **Scope**: Entirely within Lead's conversation context. No external IPC.

### Iteration Protocol

```
[ENTER execution-cascade with execution-impact L1]
    |
    v
[ITERATION 1]
    |-- Lead extracts DIRECT dependents from impacts[] array
    |-- Lead groups dependents by proximity (max 2 implementer groups)
    |-- Lead spawns implementer(s) with update instructions:
    |       Prompt includes: what changed, what reference pattern to fix,
    |       evidence line, expected update behavior
    |-- Implementers update files
    |-- PostToolUse hooks fire (Boundary 1: logs new changes)
    |-- SubagentStop hooks fire BUT:
    |       Lead is in "cascade mode" -> ignores SRC IMPACT ALERT
    |       (prevents recursive hook-driven re-entry into execution-impact)
    |-- Lead reads implementer L1 outputs
    |-- Lead runs CONVERGENCE CHECK (see below)
    |       |
    |       |-- No new impacts -> CONVERGED (exit loop)
    |       |-- New impacts detected -> increment iteration counter
    |               |
    |               |-- counter < 3 -> ITERATION 2
    |               |-- counter >= 3 -> PARTIAL (exit loop with warning)
    v
[ITERATION 2] (if triggered)
    |-- Same as Iteration 1, but operates on NEW dependents only
    |-- Files updated in Iteration 1 are excluded from update targets
    |-- New files changed by Iteration 1 implementers are the "changed files"
    |-- Convergence check runs again
    v
[ITERATION 3] (if triggered, FINAL)
    |-- Same as above
    |-- After completion: regardless of convergence check result -> EXIT
    |-- If still not converged: set status: partial, convergence: false
    v
[EXIT cascade -> Lead reads L1 -> proceeds to execution-review]
```

### Convergence Detection Algorithm

```
function check_convergence(iteration_changed_files):
    new_impacts = []
    for each file in iteration_changed_files:
        basename = strip_extension(basename(file))
        # grep for references to this file in the repo
        dependents = grep -rl basename /home/palantir/.claude/ \
            --exclude-dir=.git --exclude-dir=agent-memory \
            --include='*.md' --include='*.json' --include='*.sh'
        # Remove self-references
        dependents = dependents - {file}
        # Remove files already updated in ANY previous iteration
        dependents = dependents - all_previously_updated_files
        # Remove files already in the original execution-impact report
        # (they were already addressed)
        dependents = dependents - original_impact_files
        if dependents is not empty:
            new_impacts.append({file: file, dependents: dependents})

    return new_impacts  # empty = converged, non-empty = more work needed
```

**Key invariant**: The convergence check uses grep (same technique as execution-impact) but ONLY checks files changed in the CURRENT iteration, and ONLY considers dependents not already handled.

### State Tracking Between Iterations

The following state persists across iterations within execution-cascade's scope:

| State Item | Type | Lifecycle | Purpose |
|-----------|------|-----------|---------|
| `iteration_count` | integer | Initialized to 0, incremented per iteration | Track against max (3) |
| `all_updated_files` | set of paths | Grows each iteration (union of all implementer changes) | Prevent re-updating same file |
| `original_impact_files` | set of paths | Set once from execution-impact L1 input | Exclude from convergence check |
| `iteration_log` | array of objects | One entry per iteration | Build L2 output |
| `files_skipped` | set of paths | Files that failed update (implementer error + retry failure) | Report in L1 warnings |

**Iteration log entry schema:**
```yaml
iteration: 1
changed_files:          # Files updated by implementers this iteration
  - path: ""
    implementer: ""     # Which implementer updated it
    status: complete|failed
new_impacts_detected: 0 # Count from convergence check
new_impact_files: []    # Paths of newly-detected dependents
```

### State is NOT Persisted Externally

All cascade state lives in Lead's conversation context (natural language tracking). There is no external state file. If Lead compacts during cascade (unlikely given 62% headroom but possible):
- Cascade state is lost
- Recovery: Lead re-reads execution-impact L1 and restarts cascade from iteration 1
- PreCompact hook warns about in-progress work

### Termination Contract

| Condition | Outcome | L1 Status | L1 Convergence |
|-----------|---------|-----------|----------------|
| Iteration 1 convergence check: empty | CONVERGED | `converged` | `true` |
| Iteration 2 convergence check: empty | CONVERGED | `converged` | `true` |
| Iteration 3 convergence check: empty | CONVERGED | `converged` | `true` |
| Iteration 3 convergence check: non-empty | MAX ITERATIONS | `partial` | `false` |
| All implementers in an iteration fail | ABORT ITERATION | `partial` | `false` |
| No DIRECT dependents in initial input | SKIP CASCADE | `skipped` | N/A |

**Max iterations enforcement**: The iteration counter is checked BEFORE spawning implementers. If `iteration_count >= 3`, the loop exits unconditionally. There is no mechanism to increase the limit at runtime.

### execution-cascade L1 Output Schema (YAML)

```yaml
domain: execution
skill: cascade
status: converged|partial|skipped      # See termination contract above
iterations: 0                           # Integer: how many iterations executed (0-3)
max_iterations: 3                       # FIXED: always 3
files_updated: 0                        # Integer: total unique files updated across all iterations
files_skipped: 0                        # Integer: files that failed to update
convergence: true|false                 # Boolean: did the system converge?
iteration_details:                      # Array: one entry per iteration
  - iteration: 1
    implementers_spawned: 0
    files_changed: 0
    new_impacts_detected: 0
warnings:                               # Array of strings: any issues to flag
  - ""
```

### Error Contract

| Failure Mode | Detection | Behavior |
|-------------|-----------|----------|
| Implementer fails to update a file | Implementer L1 shows `status: failed` | Retry once with fresh implementer. If retry fails: add to `files_skipped`, continue. |
| Implementer updates wrong file | Implementer L1 `files[]` does not match assignment | Log warning, do NOT count as updated. File remains in `all_updated_files` to prevent infinite loop. |
| Convergence check grep fails | grep returns exit code > 1 | Treat as "no new impacts" (converged). Log warning. |
| Lead context approaching limit during cascade | Context >80% | PreCompact fires. Cascade state may be lost. Recovery: restart from iteration 1. |
| Circular dependency detected | Same file appears in both changed_files and new_impacts across iterations | Break cycle: mark file as updated, do not re-process. Log warning. |

---

## Boundary 6: Pipeline <-> manage-codebase (codebase-map.md)

### Protocol
- **Type**: Async, post-pipeline (not blocking pipeline delivery)
- **Trigger**: Two modes:
  1. **Post-pipeline**: Lead invokes after execution-review completes (or during P9 homeostasis cycle)
  2. **Manual**: User invokes via `/manage-codebase` slash command
- **Direction**: Pipeline changed files -> manage-codebase skill -> analyst agent -> codebase-map.md

### Input Schema

**Mode 1: Incremental update (post-pipeline)**

Lead passes to manage-codebase via skill arguments:

```
Changed files from this pipeline run:
- {file_path_1} (execution-code)
- {file_path_2} (execution-code)
- {file_path_3} (execution-cascade, iteration 1)
- {file_path_4} (execution-cascade, iteration 2)

Source: execution-code L1 tasks[].files + execution-cascade L1 iteration_details[].files_changed
Mode: incremental
```

**Mode 2: Full generation (first run or recovery)**

Lead passes to manage-codebase:

```
Mode: full
Scope: .claude/
Reason: {first-run | map-corrupted | >30%-stale | user-requested}
```

**Mode 3: Manual invocation (user slash command)**

User invokes `/manage-codebase` with optional arguments:

```
/manage-codebase               -> default: incremental if map exists, full if not
/manage-codebase full           -> force full regeneration
/manage-codebase check          -> staleness check only, no writes
```

### Output Schema (codebase-map.md)

**File path**: `/home/palantir/.claude/agent-memory/analyst/codebase-map.md`

**Full file structure:**
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

## {next/file}
refs: ...
refd_by: ...
hotspot: ...
updated: ...
```

**Entry field contracts:**

| Field | Format | Validation Rule | Example |
|-------|--------|-----------------|---------|
| `## {path}` | Relative path from project root, starts with `.claude/` | Must exist on filesystem at scan time | `## .claude/skills/execution-code/SKILL.md` |
| `refs:` | Comma-separated, space after comma, basenames or relative paths | Each ref must correspond to a tracked file | `refs: orchestration-verify, execution-review, implementer.md` |
| `refd_by:` | Comma-separated, space after comma, basenames or relative paths | Each ref-by must correspond to a tracked file | `refd_by: manage-skills/SKILL.md, CLAUDE.md` |
| `hotspot:` | One of: `low`, `medium`, `high` | Calculated from `refd_by` count | `hotspot: medium` |
| `updated:` | ISO date `YYYY-MM-DD` | Must be <= today's date | `updated: 2026-02-14` |

**Hotspot calculation:**

| Score | Condition |
|-------|-----------|
| `high` | `refd_by` count >= 10, OR file changed in last 3 pipeline runs |
| `medium` | `refd_by` count 4-9 |
| `low` | `refd_by` count 0-3 |

**Incremental update rules:**

| Changed File Status | Map Action |
|--------------------|------------|
| File modified (exists in map) | Re-scan `refs`, update `refd_by` bidirectionally, recalculate `hotspot`, set `updated` to today |
| File created (not in map) | Add new entry with full scan, update `refd_by` of referenced files |
| File deleted (in map but not on filesystem) | Remove entry, remove from all `refd_by` lists |
| File renamed (detected via git) | Remove old entry, add new entry, update all `refd_by` references |

**Full regeneration rules:**

1. Delete existing map content entirely
2. `Glob .claude/**/*` to enumerate all files in scope
3. Apply scope filters (see Scope Boundary below)
4. For each file: scan content for references to other tracked files
5. Build `refs` and `refd_by` bidirectionally (if A refs B, then B refd_by A)
6. Calculate `hotspot` scores
7. Write complete map
8. Set all `updated` dates to today

### Scope Boundary (Phase 1)

**Included paths:**
- `.claude/agents/*.md`
- `.claude/skills/*/SKILL.md`
- `.claude/hooks/*.sh`
- `.claude/settings.json`
- `.claude/CLAUDE.md`
- `.claude/projects/*/memory/MEMORY.md`

**Excluded paths:**
- `.claude/agent-memory/` (except `codebase-map.md` itself -- but map does not track itself)
- `.claude/agent-memory-local/`
- `.claude/projects/*/memory/cc-reference/*` (reference docs, not INFRA components)
- Any binary files, `.git/`, `node_modules/`

**Reference detection patterns (what counts as a "reference"):**

| Source File Type | Reference Pattern | Example |
|-----------------|-------------------|---------|
| SKILL.md frontmatter | INPUT_FROM/OUTPUT_TO values | `INPUT_FROM: execution-code` |
| SKILL.md body | Skill names, agent names, file paths | `execution-review`, `implementer` |
| Agent .md | Skill names, tool names, path references | `execution-code`, `/home/palantir/.claude/hooks/` |
| CLAUDE.md | Agent names, skill names, domain names | `implementer`, `execution` |
| Hook .sh | File paths, agent type names | `implementer`, `/tmp/src-changes-` |
| settings.json | Hook script paths, permission patterns | `/home/palantir/.claude/hooks/on-file-change.sh` |

### manage-codebase L1 Output Schema (YAML)

```yaml
domain: homeostasis
skill: manage-codebase
status: complete|partial               # complete = all entries processed; partial = timeout/error
mode: full-generation|incremental-update|staleness-check
entries: 0                              # Integer: total entries in map after operation
stale_entries_removed: 0                # Integer: entries removed (file deleted or >7 days stale)
new_entries_added: 0                    # Integer: new entries created
entries_updated: 0                      # Integer: existing entries refreshed
map_path: ".claude/agent-memory/analyst/codebase-map.md"
staleness_report:                       # Only present in staleness-check mode
  total_entries: 0
  stale_count: 0                        # Entries with updated date > 7 days ago
  missing_count: 0                      # Entries referencing non-existent files
  recommendation: "none|incremental|full-regeneration"
```

### Error Contract

| Failure Mode | Detection | Behavior | Recovery |
|-------------|-----------|----------|----------|
| codebase-map.md does not exist | `[ ! -f map_path ]` | Switch to full-generation mode automatically | Self-recovering |
| codebase-map.md corrupted (unparseable) | Grep for `## ` headers returns inconsistent results | Delete and regenerate from scratch | Analyst writes new map |
| codebase-map.md exceeds 300 lines | `wc -l > 300` | Prune `hotspot: low` entries with oldest `updated` dates | Automatic within manage-codebase |
| Missing entry (file exists but not in map) | `Glob` finds file not in map | Add entry on next incremental update | Flagged in staleness report |
| Orphaned entry (in map but file deleted) | Entry path does not exist on filesystem | Remove entry, update all `refd_by` references | Automatic |
| Bidirectional inconsistency | A refs B, but B does not list A in refd_by | Full re-scan of affected entries | Detected during incremental, fixed in-place |
| Analyst agent timeout (maxTurns: 30) | Agent stops with incomplete map | Set `status: partial`, write what was completed | Lead can re-invoke for remaining |
| Concurrent map write (two manage-codebase invocations) | Should not occur (Lead serializes skill invocations) | Last writer wins (no locking) | Re-run if suspicious |

### Validation Contract

**How to verify map correctness:**

| Check | Method | Expected Result |
|-------|--------|-----------------|
| All entries point to existing files | `for path in $(grep "^## " map \| sed 's/^## //'); do [ -f "$path" ]; done` | All files exist |
| No orphaned entries | Same as above | Zero failures |
| Bidirectional consistency | For each entry's `refs` value, check that the referenced file's `refd_by` includes this entry | All references are bidirectional |
| Hotspot scores correct | Count `refd_by` entries, compare against hotspot thresholds | All scores match thresholds |
| No entries for excluded paths | `grep "^## .claude/agent-memory" map` | Zero matches (except possibly codebase-map.md) |
| Size within limit | `wc -l map` | <= 300 |

---

## Appendix A: Data Type Summary

### Shared Type: Absolute File Path
- Format: POSIX absolute path starting with `/`
- Example: `/home/palantir/.claude/skills/execution-code/SKILL.md`
- Validation: Must start with `/`, no null bytes, no trailing whitespace
- Used in: Boundaries 1, 2, 4, 5, 6

### Shared Type: Relative File Path
- Format: Path relative to project root `/home/palantir`
- Example: `.claude/skills/execution-code/SKILL.md`
- Validation: Must start with `.claude/` (Phase 1 scope)
- Used in: Boundary 6 (codebase-map.md entries)

### Shared Type: Basename
- Format: File name without directory path, with or without extension
- Example: `SKILL.md`, `execution-code`, `implementer`
- Used in: Boundary 2 (grep patterns), Boundary 6 (refs/refd_by values)

### Shared Type: Session ID
- Format: UUID v4 string
- Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- Source: CC runtime (provided in all hook stdin JSON)
- Used in: Boundaries 1, 2 (log file naming)

### Shared Type: ISO Date
- Format: `YYYY-MM-DD`
- Example: `2026-02-14`
- Used in: Boundary 6 (updated field in codebase-map.md)

### Shared Type: ISO Timestamp
- Format: `YYYY-MM-DDTHH:MM:SS+ZZ:ZZ` (ISO-8601 with timezone)
- Example: `2026-02-14T15:30:42+09:00`
- Source: `date -Iseconds`
- Used in: Boundary 1 (TSV timestamp column)

---

## Appendix B: End-to-End Data Flow with Types

```
[Implementer calls Edit]
    | stdin JSON: {session_id: UUID, tool_name: "Edit", tool_input: {file_path: AbsPath}}
    v
[on-file-change.sh] --append--> /tmp/src-changes-{UUID}.log
    | TSV line: "{ISOTimestamp}\t{ToolName}\t{AbsPath}\n"
    v
[Implementer finishes]
    | stdin JSON: {session_id: UUID, agent_type: "implementer"}
    v
[on-implementer-done.sh] --read--> /tmp/src-changes-{UUID}.log
    | Process: deduplicate AbsPath, grep -rl Basename, format text
    | stdout JSON: {hookSpecificOutput: {additionalContext: String(max 500 chars)}}
    v
[Lead context injection]
    | Text: "SRC IMPACT ALERT: ..."
    | Decision: cascade_recommended? -> invoke execution-impact
    v
[execution-impact]
    | Input: execution-code L1 YAML + additionalContext text
    | Output: L1 YAML {impacts: [{changed_file: AbsPath, dependents: [{file: AbsPath, type: DIRECT|TRANSITIVE}]}]}
    | Decision: cascade_recommended: true|false
    v
[execution-cascade]
    | Input: execution-impact L1 YAML
    | Loop: max 3 iterations
    | Per iteration: spawn implementers -> check convergence via grep
    | Output: L1 YAML {status: converged|partial, iterations: N, files_updated: N}
    v
[manage-codebase]
    | Input: all changed file paths (execution-code + execution-cascade)
    | Output: updated codebase-map.md (incremental or full)
    | L1 YAML: {entries: N, stale_entries_removed: N, new_entries_added: N}
```

---

## Appendix C: Cross-Boundary Invariants

These invariants hold across the entire SRC system and can be used as system-level verification checks.

| # | Invariant | Boundaries | Verification |
|---|-----------|------------|-------------|
| I1 | session_id is identical across B1 and B2 | B1, B2 | Log file name matches SubagentStop session_id |
| I2 | File paths are absolute in hooks, relative in map | B1, B2, B6 | Check path format at each boundary |
| I3 | Every file in execution-impact L1 was in the change log | B2, B4 | Compare impacts[].changed_file against log entries |
| I4 | cascade never processes a file already updated | B5 | all_updated_files set prevents re-processing |
| I5 | codebase-map refs/refd_by are bidirectional | B6 | A refs B implies B refd_by A |
| I6 | Hooks never block the pipeline | B1, B2, B3 | All hooks exit 0; B1 is async; B2 has 15s timeout |
| I7 | Pipeline degrades gracefully at every boundary | All | Each error contract results in "proceed with less data", never "abort" |
| I8 | Total cascade iterations never exceed 3 | B5 | iteration_count checked before spawn |
| I9 | additionalContext is ephemeral (single-turn) | B3 | Lead acts on alert immediately; does not rely on persistence |
| I10 | No SRC component modifies implementer behavior | B1 | PostToolUse hook is async and silent; implementer is unaware |
