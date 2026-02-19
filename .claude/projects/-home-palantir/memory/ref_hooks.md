# Hook System — 14 Lifecycle Events

> Verified: 2026-02-17 via claude-code-guide team investigation

---

## 1. Overview

Hooks are user-defined shell commands, LLM prompts, or agent invocations that execute automatically at specific points in Claude Code's lifecycle. Hooks run with full user permissions — there is NO sandbox for hooks.

### Complete Lifecycle Diagram

```
SESSION LIFECYCLE                    MAIN CONVERSATION LOOP
━━━━━━━━━━━━━━━━━━━━                ━━━━━━━━━━━━━━━━━━━━━━━━━
SessionStart (startup/resume/       UserPromptSubmit
  clear/compact)                       ↓
  ↓                                  Claude Reasoning
  │                                    ↓
  │                                ┌─ PreToolUse ──→ PermissionRequest
  │                                │     ↓
  │                                │  Tool Execution
  │                                │     ↓
  │                                ├─ PostToolUse (on success)
  │                                └─ PostToolUseFailure (on failure)
  │                                    ↓
  │                                SubagentStart → [Subagent Works] → SubagentStop
  │                                    ↓
  │                                Notification (async)
  │                                    ↓
  │                                Stop
  ↓
PreCompact (before compaction)       TaskCompleted (Agent Teams)
  ↓                                  TeammateIdle (Agent Teams)
SessionEnd (clear/logout/other)
```

---

## 2. Complete Event Map

| Event | Fires When | Can Block | Matcher | Scope |
|-------|-----------|-----------|---------|-------|
| SessionStart | Session begins/resumes/clears/compacts | no | startup, resume, clear, compact | global, agent, skill |
| UserPromptSubmit | User submits prompt | yes (exit 2) | no | global, agent, skill |
| PreToolUse | Before tool executes | yes (exit 2) | tool name | global, agent, skill |
| PermissionRequest | Permission dialog appears | yes | tool name | global, agent, skill |
| PostToolUse | Tool succeeds | no (feedback only) | tool name | global, agent, skill |
| PostToolUseFailure | Tool fails | no | tool name | global, agent, skill |
| Notification | Claude sends notification | no | notification type | global |
| SubagentStart | Subagent spawned | no | agent type | global |
| SubagentStop | Subagent finishes | yes (exit 2) | agent type | global |
| Stop | Claude finishes responding | yes (exit 2) | no | global, agent, skill |
| TeammateIdle | Teammate about to idle | yes (exit 2) | no | global |
| TaskCompleted | Task marked complete | yes (exit 2) | no | global |
| PreCompact | Before compaction | no | manual, auto | global |
| SessionEnd | Session terminates | no | clear, logout, other | global |

**Handler type support**: `TeammateIdle` and `TaskCompleted` do NOT support `prompt` or `agent` hook types — exit code (0/2) only. No JSON decision control for these events.

---

## 3. Handler Types

| Type | Description | Supported Events | Default Timeout |
|------|-------------|-----------------|-----------------|
| command | Shell script; receives JSON on stdin | All 14 events | 60s |
| prompt | Single-turn LLM eval (Haiku default) | PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, UserPromptSubmit, Stop, SubagentStop | 30s |
| agent | Multi-turn subagent with tools (Read, Grep, Glob, Bash). Max 50 turns | Same as prompt | 60s |

### Hook Definition Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| type | enum | yes | none | command, prompt, or agent |
| command | string | yes (command) | none | Shell command or script path |
| prompt | string | yes (prompt/agent) | none | LLM/agent prompt text |
| timeout | number | no | 60 | Seconds before timeout |
| statusMessage | string | no | none | UI status text while running |
| once | boolean | no | false | Fire only once per session |
| async | boolean | no | false | Background (command type ONLY) |
| model | string | no | haiku | Model for prompt type |

---

## 4. Hook I/O Contract

### Input (stdin JSON, command type)

```json
{
  "session_id": "uuid",
  "transcript_path": "~/.claude/projects/.../transcript.jsonl",
  "cwd": "/project/path",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "/path", "content": "..." },
  "tool_response": { "filePath": "/path", "success": true },
  "tool_use_id": "toolu_01ABC..."
}
```

Fields vary by event:
- SubagentStop: + `agent_id`, `agent_type`, `agent_transcript_path`
- TaskCompleted: + `task_id`, `task_subject`, `task_description`, `teammate_name`, `team_name`
- TeammateIdle: + `teammate_name`, `team_name`

### Output (stdout JSON, command type)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "Injected into Claude's next turn",
    "permissionDecision": "allow|deny|ask"
  }
}
```

### additionalContext

The primary mechanism for hooks to inject information into Claude's reasoning. When returned, the string appears in Claude's context on the very next turn.

- Scope: SINGLE TURN only
- Does NOT survive compaction
- NOT visible to spawned subagents
- Multiple hooks same turn: concatenated in declaration order

| Event | additionalContext | permissionDecision |
|-------|-------------------|-------------------|
| SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, SubagentStart, PreCompact, Stop, SubagentStop | yes | PreToolUse/PermissionRequest only |
| TaskCompleted, TeammateIdle | no | no (exit code only) |

---

## 5. Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| 0 | Success | Action proceeds, stdout JSON parsed |
| 2 | Block | Action blocked, stderr fed back |
| other | Error | Non-blocking error, logged |

Exit code 2 behavior by event:
- PreToolUse: blocks tool call
- PermissionRequest: denies permission
- UserPromptSubmit: blocks prompt, erases it
- Stop/SubagentStop: prevents stopping (agent continues)
- TeammateIdle: prevents idle (teammate continues)
- TaskCompleted: blocks completion, stderr as feedback
- PostToolUse/Notification/SubagentStart/SessionStart/SessionEnd/PreCompact: cannot block

---

## 6. Async Hooks

- `"async": true` on command type ONLY (not prompt or agent)
- Runs in background, does not block Claude
- Results delivered on NEXT conversation turn
- Cannot return blocking decisions (exit 2 ignored)

---

## 7. Matcher Patterns

- Regex syntax: `Edit|Write` matches both
- MCP tools: `mcp__servername__toolname`
- Empty string matches all occurrences

---

## 8. Hook Scopes (6 levels)

| Scope | Location | Shareable |
|-------|----------|-----------|
| Organization (managed) | managed-settings.json | IT deployed |
| User | `~/.claude/settings.json` | No |
| Project | `.claude/settings.json` | Yes (git) |
| Project local | `.claude/settings.local.json` | No (gitignored) |
| Plugin | `hooks/hooks.json` in plugin dir | With plugin |
| Skill/Agent | Frontmatter in SKILL.md or agent .md | With component |

Hooks follow 5-layer settings precedence. `allowManagedHooksOnly` blocks user, project, and plugin hooks.

### 8.5 Hook Propagation Scope

> **Empirical finding** (2026-02-17): All global hooks fire in ALL execution contexts — lead session, teammates, AND subagents. There is NO built-in scoping mechanism.

Evidence: 315 PreToolUse hook invocations across 9 distinct session_ids in a single Agent Teams session. Global hooks cannot be restricted to lead-only via configuration alone.

**Workaround — session_id guard pattern** (for command-type hooks):

```bash
# Session_id guard — lead-only execution
TEAM_CONFIG=$(find ~/.claude/teams/ -name "config.json" -print -quit 2>/dev/null)
if [[ -n "$TEAM_CONFIG" ]]; then
  LEAD_SESSION=$(jq -r '.leadSessionId // empty' "$TEAM_CONFIG" 2>/dev/null)
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
  if [[ -n "$LEAD_SESSION" && -n "$SESSION_ID" && "$SESSION_ID" != "$LEAD_SESSION" ]]; then
    exit 0  # Skip non-lead sessions
  fi
fi
```

This pattern reads `leadSessionId` from team config and compares against the hook's `session_id` input. Non-lead sessions exit 0 (no-op). Used in: `anti-rationalization.sh`, `on-session-end.sh`.

### 8.6 Known Issues

| Issue | Event | Description |
|-------|-------|-------------|
| SubagentStop prompt blocking (#20221) | SubagentStop | Prompt-type hooks cannot actually prevent subagent termination (exit 2 ineffective) |
| Stop prompt context | Stop | Prompt-type Stop hooks see metadata only, not the full assistant response text |
| Global hook cost | All | Prompt-type global hooks fire in every context, multiplying LLM call cost by number of active sessions |

---

## 9. Our Hook Configuration

| Hook | Event | Matcher | Type | Scope | Purpose |
|------|-------|---------|------|-------|---------|
| on-subagent-start.sh | SubagentStart | (all) | command | global | Team context injection |
| on-pre-compact.sh | PreCompact | (all) | command | global | Task snapshot preservation |
| on-session-compact.sh | SessionStart | compact | command | global | Compaction recovery guidance |
| on-session-end.sh | SessionEnd | (all) | command | global | Temp file cleanup (lead-only via session_id guard) |
| on-file-change.sh | PostToolUse | Edit\|Write | command | agent (impl/infra-impl) | SRC Stage 1 file logger |
| on-file-change-fail.sh | PostToolUseFailure | Edit\|Write | command | agent (impl/infra-impl) | Failed write logger |
| on-implementer-done.sh | SubagentStop | implementer\|infra-implementer | command | global | SRC Stage 2 impact summary |
| on-task-completed.sh | TaskCompleted | (all) | command | global | Pipeline task logging |
| anti-rationalization.sh | Stop | (all) | command | global | Rationalization cop-out check (lead-only via session_id guard) |
| anti-rm-rf.sh | PreToolUse | Bash | command | global | Destructive command guard |
| anti-push-main.sh | PreToolUse | Bash | command | global | Git push safety |
| input-modifier.sh | PreToolUse | Bash\|Edit\|Write | command | global | Co-author + file lock + path safety |
| budget-monitor.sh | PreToolUse | (all) | command | global | Tool budget monitoring |
| idle-quality-gate.sh | TeammateIdle | (all) | command | global | Teammate output verification |
| block-taskoutput-relay.sh | PreToolUse | TaskOutput | command | global | Data Relay Tax guard — blocks TaskOutput(block:true) in Lead context (session_id guard) |
