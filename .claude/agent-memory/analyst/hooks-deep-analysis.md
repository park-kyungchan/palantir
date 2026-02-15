# Hook Scripts Deep Analysis

> Date: 2026-02-15
> Scope: 5 hooks in /home/palantir/.claude/hooks/ + settings.json configuration
> Reference: cc-reference/hook-events.md, agent-teams-bugs.md (BUG-003)
> Method: Logic-level correctness, error handling, performance, integration, data flow

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 1     | Parallel implementer data loss in SRC pipeline |
| HIGH     | 3     | jq hard dependency, JSON escape gaps, race window |
| MEDIUM   | 4     | Task dir selection, stale documentation, output format, success detection |
| LOW      | 4     | Minor inefficiencies, cosmetic, defensive gaps |

**Overall Assessment**: The hooks are well-structured and demonstrate good defensive coding patterns. However, the SRC pipeline (on-file-change.sh + on-implementer-done.sh) has a critical parallel execution flaw, and several JSON handling gaps could cause silent failures.

---

## CRITICAL Findings

### CRIT-01: Parallel Implementer SRC Data Loss
**File**: `/home/palantir/.claude/hooks/on-implementer-done.sh`, lines 20, 98-99
**File**: `/home/palantir/.claude/hooks/on-file-change.sh`, line 28

**Bug**: Both SRC stages use `SESSION_ID` to name the log file: `/tmp/src-changes-${SESSION_ID}.log`. Per BUG-003 in agent-teams-bugs.md (line 44), the `session_id` in stdin JSON is always the **parent (Lead) session ID**, not the child agent's session ID. This means:

1. Two parallel implementers (e.g., `implementer` and `infra-implementer`) both write to the **same** log file.
2. When the first implementer finishes, on-implementer-done.sh reads the log (line 29), processes it, and renames it to `.processed` (line 99: `mv -f "$LOGFILE" "${LOGFILE}.processed"`).
3. Meanwhile, the second implementer may still be appending to the original path. After the `mv`, the second implementer's `echo >> "$LOGFILE"` recreates the file (due to `>>` append semantics), so writes after the rename go to a NEW file.
4. But any writes from the second implementer that were already in the file BEFORE the rename are now in the `.processed` file and get attributed to the first implementer's impact analysis.
5. When the second implementer finishes, on-implementer-done.sh reads only the NEW file (post-rename writes), missing all changes logged before the first implementer finished.

**Scenario**: Implementer A and B run in parallel. B modifies 10 files. A finishes first. On-implementer-done.sh reads the log containing B's 10 changes + A's changes, renames to `.processed`. B then modifies 2 more files (new log created). B finishes. On-implementer-done.sh sees only 2 files, missing the 10 that were swept into `.processed`.

**Impact**: False "SRC: No file changes detected" or incomplete impact analysis for parallel implementers. Cascade (P7.4) may skip necessary consistency updates.

**Fix direction**: Use agent-scoped log files (e.g., keyed by `agent_id` from SubagentStop input, or a combination of session_id + tool_use_id). On-implementer-done.sh would need to identify which log entries belong to the finishing agent. Alternative: use file locking + atomic read-and-truncate instead of rename.

---

## HIGH Findings

### HIGH-01: on-file-change.sh Has No jq Fallback (Hard Dependency)
**File**: `/home/palantir/.claude/hooks/on-file-change.sh`, lines 13-16

**Bug**: The script uses `jq` for all field extraction with no fallback. Compare with on-implementer-done.sh (lines 12-16) which has a `grep`-based fallback, and on-pre-compact.sh (lines 16-19) which warns and exits gracefully.

If `jq` is unavailable, `set -euo pipefail` (line 7) causes the script to exit immediately on the first failed `jq` call (exit code non-zero). Since this is an async hook, the failure is silent -- no error is surfaced to the user or logged. The SRC log file is never written, and Stage 2 reports "No file changes detected" for every implementer run.

**Impact**: Complete SRC pipeline failure in jq-less environments, with no visible error. The system silently degrades to no impact analysis.

**Evidence**: on-file-change.sh line 13 (`jq -r '.session_id // empty'`) vs on-implementer-done.sh lines 12-16 (has `if command -v jq` guard with grep fallback).

### HIGH-02: JSON Escape in on-implementer-done.sh Is Incomplete
**File**: `/home/palantir/.claude/hooks/on-implementer-done.sh`, line 114

```bash
MSG=$(echo "$MSG" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\n/\\n/g')
```

**Bug 1 -- Literal newline not matched**: The `sed` expression `s/\n/\\n/g` matches the two-character sequence `\n`, not an actual newline character. In sed, literal newlines in the pattern space require different handling. However, since `$MSG` is built from `echo` and string concatenation (not heredocs), it is unlikely to contain literal newlines in practice. This is a **latent** bug.

**Bug 2 -- Missing control character escaping**: JSON requires escaping of control characters (U+0000 through U+001F). File paths could theoretically contain characters that break JSON parsing. The `\t` handling is present but `\r`, `\b`, `\f`, and other control chars are not escaped.

**Bug 3 -- Filename containing backslash**: If a file path contains a backslash (valid on Linux), the order of sed substitutions is correct (backslash first), but the `awk` short-name extraction (line 44, 59, 83) does not escape backslashes, so `SEARCH_PATTERN` could contain unescaped backslashes fed to `grep -F` (which treats them literally -- actually safe for `-F`).

**Impact**: Malformed JSON output from on-implementer-done.sh if file paths contain control characters. Claude Code would fail to parse the hook output, potentially losing the entire SRC impact alert.

### HIGH-03: Async Race Window Between Stage 1 and Stage 2
**File**: `/home/palantir/.claude/hooks/on-file-change.sh` (async: true)
**File**: `/home/palantir/.claude/hooks/on-implementer-done.sh` (sync)
**Config**: `/home/palantir/.claude/settings.json`, line 83 (`"async": true`)

**Bug**: on-file-change.sh runs asynchronously per the settings.json config. Per the CC reference (hook-events.md line 197): "Async hook results are delivered on the NEXT conversation turn." This means:

1. The implementer's last Edit/Write triggers on-file-change.sh asynchronously.
2. If the implementer's very next action is to complete (triggering SubagentStop), on-file-change.sh may not have finished writing to the log file yet.
3. On-implementer-done.sh (synchronous) runs and reads the log file, potentially missing the last file change.

The window is small (on-file-change.sh is fast -- one jq call + one echo), but it exists. The `>> "$LOGFILE"` append could be buffered or delayed.

**Impact**: The last file changed by an implementer may be missing from the SRC impact analysis. This was previously identified in infra-audit-v3-iter4.md as a known async race condition.

**Mitigation already present**: The `|| true` on line 29 of on-file-change.sh and the append semantics make the window very small. In practice, the SubagentStop event fires after the last tool response is complete, by which time the async hook from that same PostToolUse has likely already finished. But there is no synchronization guarantee.

---

## MEDIUM Findings

### MED-01: on-pre-compact.sh Task Directory Selection Gets First, Not Most Recent
**File**: `/home/palantir/.claude/hooks/on-pre-compact.sh`, lines 26-28

```bash
for d in /home/palantir/.claude/tasks/*/; do
    [ -d "$d" ] && TASK_DIR="$d" && break
done
```

**Bug**: The comment on line 21 says "find most recent" but the glob `*/` returns directories in alphabetical order, and `break` exits on the first match. If task list IDs are UUIDs (as typical in Claude Code), the first alphabetically is not the most recent.

**Impact**: In sessions with multiple task lists, the snapshot may capture a stale/wrong task list instead of the active one. The snapshot is only used for crash recovery, so impact is limited to post-compaction recovery quality.

**Fix**: Sort by modification time: `ls -td /home/palantir/.claude/tasks/*/ 2>/dev/null | head -1`

### MED-02: hook-events.md Documents "once: true" for on-session-compact.sh, But settings.json Has No "once" Field
**File**: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md`, line 233
**File**: `/home/palantir/.claude/settings.json`, lines 62-74

**Documentation bug**: hook-events.md line 233 states: "Timeout: 15s, once: true (fires only once per session)". But settings.json has no `once` field on the SessionStart:compact hook entry. The default is `false` (per hook-events.md line 72).

**Impact**: The on-session-compact.sh hook fires on EVERY compaction recovery, not just the first one. This means repeated recovery messages cluttering the agent's context. In a session with multiple compactions, the same recovery instructions are injected each time -- benign but wasteful.

### MED-03: on-pre-compact.sh Produces No stdout JSON (Missing additionalContext Opportunity)
**File**: `/home/palantir/.claude/hooks/on-pre-compact.sh`

**Observation**: PreCompact supports `additionalContext` output (per hook-events.md line 181). This hook writes a snapshot file and logs to a file, but produces NO stdout output. The snapshot path (`$SNAPSHOT_FILE`) is only logged to the file -- it is never communicated back to the agent.

**Impact**: After compaction, the agent has no way to know WHERE the pre-compact snapshot was saved without searching /tmp/claude-hooks/. The hook could inject the snapshot path via additionalContext. Low urgency since the SessionStart:compact hook provides recovery instructions.

### MED-04: on-file-change.sh Success Detection May Misclassify
**File**: `/home/palantir/.claude/hooks/on-file-change.sh`, line 16

```bash
SUCCESS=$(echo "$INPUT" | jq -r 'if .tool_response.success == false then "false" else "true" end')
```

**Bug**: This expression defaults to `"true"` when `.tool_response.success` is `null` (field absent), `true` (boolean), or any non-false value. Per the CC reference (hook-events.md line 108), `tool_response.success` is a boolean field. However, if the PostToolUse event does not include `tool_response` at all (possible for some tool types or error conditions), jq would evaluate `null == false` as `false`, so `SUCCESS` would be `"true"` -- logging a file change that may not have actually succeeded.

**Impact**: Phantom entries in the SRC log for tools that failed in unexpected ways. These phantom entries would cause unnecessary grep work in Stage 2 but are unlikely to match real dependents (the files may not exist or may not have changed).

---

## LOW Findings

### LOW-01: on-implementer-done.sh Calls git for Every Changed File
**File**: `/home/palantir/.claude/hooks/on-implementer-done.sh`, line 69

```bash
GIT_ROOT=$(git -C "$HOME" rev-parse --show-toplevel 2>/dev/null || echo "$HOME")
```

**Issue**: This `git rev-parse` call is inside the `while IFS= read -r changed` loop (line 57), meaning it executes once per changed file. The git root does not change between iterations. Should be hoisted outside the loop.

**Impact**: Negligible performance cost (git rev-parse is fast, <5ms), but wasteful. With MAX_DEPS=8 capping the outer loop, the worst case is ~8 redundant calls.

### LOW-02: on-pre-compact.sh Empty Task Directory Produces Invalid JSON
**File**: `/home/palantir/.claude/hooks/on-pre-compact.sh`, lines 32-43

If `$TASK_DIR` exists but contains no `.json` files, the output file will contain just `[\n]` (an empty JSON array) -- this is actually valid JSON. However, if the glob `"$TASK_DIR"*.json` matches no files, bash expands it literally to the glob pattern string. The `[ -f "$f" ] || continue` guard on line 35 handles this correctly by skipping.

**Actual issue**: The snapshot file with `[ ]` is saved but never cleaned up. Over many compaction cycles, `/tmp/claude-hooks/` accumulates snapshot files. No rotation or cleanup mechanism exists.

**Impact**: Disk space accumulation in /tmp. Mitigated by OS tmpfile cleanup (typically on reboot for WSL2).

### LOW-03: on-subagent-start.sh Field Extraction Redundancy
**File**: `/home/palantir/.claude/hooks/on-subagent-start.sh`, line 12

```bash
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
```

**Issue**: The SubagentStart input schema (per hook-events.md line 87) provides `agent_type` directly. The fallback chain `.tool_input.subagent_type` is from an older schema version. This is harmless defensive coding but indicates potential schema uncertainty.

### LOW-04: on-session-compact.sh Does Not Read stdin
**File**: `/home/palantir/.claude/hooks/on-session-compact.sh`

**Observation**: Unlike all other hooks, this script does NOT read stdin (`INPUT=$(cat)` is absent). Per the hook input specification, SessionStart events provide `session_id`, `event`, `matcher`, and `transcript_summary` on stdin. Not reading stdin is harmless (the data is ignored), but `transcript_summary` could be useful for providing more context-aware recovery instructions.

---

## Integration Verification: settings.json vs Script Logic

| Hook | Event | Matcher (settings) | Matcher (script logic) | Consistent? |
|------|-------|--------------------|----------------------|-------------|
| on-subagent-start.sh | SubagentStart | `""` (all) | Checks `team_name` internally | YES -- fires for all, filters internally |
| on-pre-compact.sh | PreCompact | `""` (all) | No matcher-dependent logic | YES |
| on-session-compact.sh | SessionStart | `"compact"` | No matcher-dependent logic | YES |
| on-file-change.sh | PostToolUse | `"Edit\|Write"` | Uses `TOOL_NAME` from input | YES -- matcher pre-filters |
| on-implementer-done.sh | SubagentStop | `"implementer\|infra-implementer"` | Uses `SESSION_ID` from input | YES -- matcher pre-filters |

| Hook | Timeout (settings) | Actual Runtime Risk | Adequate? |
|------|-------------------|--------------------|-----------|
| on-subagent-start.sh | 10s | <1s (jq + echo) | YES |
| on-pre-compact.sh | 30s | <5s (file copy) | YES |
| on-session-compact.sh | 15s | <1s (jq + echo) | YES |
| on-file-change.sh | 5s | <1s (jq + echo), async | YES |
| on-implementer-done.sh | 30s | 10-25s (multiple grep -r with timeout 10) | TIGHT -- two grep -r calls per changed file, each with 10s timeout. With many changed files, could approach 30s. The MAX_DEPS=8 cap limits total grep iterations. |

---

## Data Flow Analysis: SRC Pipeline (Stage 1 -> Stage 2)

```
PostToolUse(Edit|Write)  ──async──>  on-file-change.sh
                                         │
                                    jq extract fields
                                         │
                                    /tmp/src-changes-{LEAD_SESSION_ID}.log
                                    (TSV: timestamp \t tool \t filepath)
                                         │
SubagentStop(implementer)  ──sync──>  on-implementer-done.sh
                                         │
                                    Read + dedup changed files
                                         │
                                    grep -Frl for reverse refs
                                         │
                                    Rename .log -> .log.processed
                                         │
                                    stdout JSON: additionalContext
                                         │
                                    Lead receives SRC IMPACT ALERT
```

**Data Loss Scenarios**:
1. **CRIT-01**: Parallel implementers share log file, first-to-finish steals second's data.
2. **HIGH-03**: Async race -- last file change may not be in log when Stage 2 reads.
3. **Edge**: If on-file-change.sh fails silently (jq missing, HIGH-01), log is never written.

**Data Integrity**:
- TSV format with tab-sanitized file paths: GOOD
- POSIX atomic append for lines < PIPE_BUF (4096 bytes): GOOD for typical paths
- Dedup via `sort -u`: GOOD (handles repeated edits to same file)

---

## Recommendations (Priority Order)

1. **CRIT-01 Fix**: Add agent identification to SRC log files. Options:
   - (a) Use `agent_id` from SubagentStop to filter log entries (requires adding agent_id to PostToolUse log -- but PostToolUse doesn't have agent_id per BUG-003)
   - (b) Use atomic `cp + truncate` instead of `mv` in on-implementer-done.sh, so the log is preserved for subsequent implementers
   - (c) Accept the limitation and document that SRC works correctly only for sequential implementer execution

2. **HIGH-01 Fix**: Add jq fallback to on-file-change.sh (grep-based extraction like on-implementer-done.sh line 15)

3. **HIGH-02 Fix**: Use `jq` for JSON encoding in on-implementer-done.sh output (like on-session-compact.sh does on line 18-23), or at minimum handle literal newlines in sed

4. **MED-01 Fix**: Replace for-loop with `ls -td ... | head -1` for most-recent task directory

5. **MED-02 Fix**: Either add `"once": true` to settings.json SessionStart:compact entry, or update hook-events.md documentation to remove the false claim
