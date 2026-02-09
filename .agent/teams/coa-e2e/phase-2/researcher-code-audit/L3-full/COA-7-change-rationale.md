# COA-7: Hook Fix Change Rationale

## Validation Summary

| Hook | Current Code | Audit Fix Spec | Live Drift | Schema Validation | Verdict |
|------|-------------|----------------|------------|-------------------|---------|
| on-subagent-start.sh | Matches §8.1 exactly | §8.2 | None | All fields verified vs §3.1 | APPROVED |
| on-subagent-stop.sh | Matches §9.1 exactly | §9.2 | None | All fields verified vs §3.2 | APPROVED |
| on-tool-failure.sh | Matches §10.1 exactly | §10.2 | None | All fields verified vs §3.8 | APPROVED |

**Zero drift detected** between current live code and audit document's "Current Code (BROKEN)" sections.

## Hook 1: on-subagent-start.sh

### Changes (line-by-line)

| Current | Fixed | Rationale |
|---------|-------|-----------|
| No schema comment | Added schema comment (lines 5-7) | Prevents re-introducing non-existent fields |
| `.agent_type // .tool_input.subagent_type // "unknown"` | `.agent_type // "unknown"` | `.tool_input.subagent_type` doesn't exist in SubagentStart schema; `.agent_type` is the official field |
| `.agent_name // .tool_input.name // "unknown"` | `.agent_id // "unknown"` | Neither `.agent_name` nor `.tool_input.name` exist; `.agent_id` is the official identifier |
| `.tool_input.team_name // "no-team"` | REMOVED | `.tool_input` not available in SubagentStart |
| `name=$AGENT_NAME \| type=$AGENT_TYPE \| team=$TEAM_NAME` | `id=$AGENT_ID \| type=$AGENT_TYPE` | Use available fields only |
| Team routing via TEAM_NAME, then filesystem fallback | Filesystem heuristic only | TEAM_NAME was always "no-team" anyway; now explicit |
| No agent_id in additionalContext | Added $aid to additionalContext | Enables agent-level correlation |

### Observations
- `agent_type` field occasionally empty on some SubagentStop events (from log evidence); handled by `// "unknown"` fallback
- GC injection mechanism unchanged in principle — filesystem heuristic was always the de facto mechanism
- Log format change: old entries were 100% "unknown" — new format provides real agent_id UUID

## Hook 2: on-subagent-stop.sh

### Changes (line-by-line)

| Current | Fixed | Rationale |
|---------|-------|-----------|
| No schema comment | Added schema + design rationale comment (lines 4-10) | Documents L1/L2 delegation to other hooks |
| `.agent_type // .tool_input.subagent_type // "unknown"` | `.agent_type // "unknown"` | Official field only |
| `.agent_name // .tool_input.name // "unknown"` | `.agent_id // "unknown"` | Official field replaces non-existent ones |
| `.tool_input.team_name // "unknown"` | REMOVED | Not available |
| — | `.agent_transcript_path // "none"` (NEW) | Official field (v2.0.42+); captures transcript path |
| L1/L2 check block (lines 18-29) | REMOVED entirely | Always produced false warnings (AGENT_NAME/TEAM_NAME always "unknown"); TeammateIdle + TaskCompleted hooks already enforce L1/L2 with correct fields and exit 2 blocking |
| JSON output with `agent: $name, hasL1, hasL2` | JSON with `agentId, agentType, transcriptPath` | Uses real data instead of always-"unknown" |

### L1/L2 Check Removal Justification
The removed L1/L2 check was:
1. **Always failing** — used AGENT_NAME (always "unknown") and TEAM_NAME (always "unknown") for path construction
2. **Producing 100% false warnings** — every SubagentStop logged "WARNING: unknown stopped without L1/L2"
3. **Redundant** — TeammateIdle hook (exit 2) and TaskCompleted hook (exit 2) both enforce L1/L2 with correct field names (teammate_name, team_name)
4. **Non-blocking** — SubagentStop cannot use exit 2 to block (agent already stopped)

## Hook 3: on-tool-failure.sh

### Changes (line-by-line)

| Current | Fixed | Rationale |
|---------|-------|-----------|
| `set -euo pipefail` | REMOVED | `-u` (unset vars) and `-o pipefail` cause silent exits on empty jq results; a logging hook should maximize resilience |
| No schema comment | Added schema comment (lines 4-6) | Documents available fields |
| `.agent_name // "unknown"` | REMOVED | `.agent_name` doesn't exist in PostToolUseFailure schema |
| `.tool_input.team_name // empty` | KEPT | `.tool_input` IS available (failed tool's params); team_name exists if the failed tool had that param |
| `exit 0` on no team dir | Fallback: `mkdir -p "$LOG_DIR"` + log to `$LOG_DIR/tool-failures.log` | Failures should never be silently dropped |
| `agent=$AGENT_NAME \| tool=$TOOL_NAME \| error=$ERROR` | `tool=$TOOL_NAME \| error=$ERROR` | Removed always-"unknown" agent field |

### set -euo pipefail Removal Justification
For a **logging hook** (no exit 2, no enforcement), resilience is more important than fail-fast:
- `-e`: Any jq returning empty could abort the script before logging
- `-u`: Unset variables (from failed jq) cause immediate exit
- `-o pipefail`: Pipeline failures in `echo | jq` chain abort entire script
- A partial log entry is always better than no log at all

## 5 Working Hooks — Verification Results

| Hook | Schema Fields Used | Correct? | Issues |
|------|-------------------|----------|--------|
| on-teammate-idle.sh | `.teammate_name`, `.team_name` | ✓ Yes — TeammateIdle schema | None |
| on-task-completed.sh | `.teammate_name`, `.team_name`, `.task_subject` | ✓ Yes — TaskCompleted schema | None |
| on-task-update.sh | `.tool_input.taskId`, `.tool_input.status`, `.tool_input.subject`, `.tool_input.owner` | ✓ Yes — PostToolUse schema | None |
| on-pre-compact.sh | No stdin field parsing | ✓ N/A — uses filesystem | None |
| on-session-compact.sh | No field parsing needed | ✓ N/A — outputs only | None |

## Additional Findings

1. **No undocumented hook issues found.** The audit's 3 issues (ISSUE-001/002/003) are comprehensive.
2. **settings.json configurations valid.** All 8 hook entries have correct event names, matchers, and timeouts.
3. **agent_type occasionally empty on SubagentStop.** Some log entries show `type=` (empty). This is a Claude Code runtime behavior, not a hook bug. The `// "unknown"` fallback handles this correctly.
4. **No additional operational constraints discovered** beyond BUG-001, BUG-002, RTDI-009.
