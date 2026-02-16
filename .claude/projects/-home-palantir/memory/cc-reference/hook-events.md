# CC Hook Events Reference
<!-- Last verified: 2026-02-16 via claude-code-guide, exit code nuance added, event count verified -->
<!-- Update policy: Re-verify after CC version updates -->

## All 14 Hook Events

> Note: Some community guides list 12 events (omitting TeammateIdle and TaskCompleted as agent-team specific). All 14 events below are verified from official docs and GitHub issues.

| Event | Fires When | Can Block | Matcher | Scope |
|-------|-----------|-----------|---------|-------|
| SessionStart | Session begins/resumes | no | startup, resume, clear, compact | global, agent, skill |
| UserPromptSubmit | User submits prompt | yes | no | global, agent, skill |
| PreToolUse | Before tool executes | yes | tool name | global, agent, skill |
| PermissionRequest | Permission dialog | yes | tool name | global, agent, skill |
| PostToolUse | Tool succeeds | no | tool name | global, agent, skill |
| PostToolUseFailure | Tool fails | no | tool name | global, agent, skill |
| Notification | Claude needs attention | no | notification type | global |
| SubagentStart | Subagent spawned | no | agent type | global |
| SubagentStop | Subagent finishes | yes | agent type | global |
| Stop | Claude finishes responding | yes | no | global, agent, skill |
| TeammateIdle | Teammate about to idle | yes (exit 2) | no | global |
| TaskCompleted | Task marked complete | yes (exit 2) | no | global |
| PreCompact | Before compaction | no | manual, auto | global |
| SessionEnd | Session terminates | no | clear, logout, other | global |

## Hook Types

| Type | Description | Return Format |
|------|-------------|---------------|
| command | Bash script, receives JSON on stdin | exit code + stdout JSON |
| prompt | Single LLM call (Haiku default) | `{ "ok": bool, "reason": string }` |
| agent | Multi-turn subagent with tools (Read, Grep, Glob, Bash). Max 50 turns, default 60s timeout | `{ "ok": bool, "reason": string }` |

### Prompt Hook Type Details (verified 2026-02-15)
- Single-turn LLM evaluation (no tool access)
- Returns `{ "ok": true/false, "reason": "..." }`
- Configurable timeout (default 10s)
- Configurable model via `model` field (default: haiku for cost efficiency)
- Use case: lightweight quality gates, verification without shell scripting
- Ideal for: style checks, naming conventions, commit message validation

### Agent Hook Type Details (verified 2026-02-15)
- Spawns a subagent with tool access (Read, Grep, Glob, Bash) for verification logic
- Returns `{ "ok": true }` or `{ "ok": false, "reason": "..." }`
- Max 50 turns, default 60s timeout (configurable via `timeout` field)
- Supported on: PreToolUse, PostToolUse, Stop, SubagentStop, TaskCompleted
- Use case: complex verification gates that need file inspection or grep analysis

### Example: Prompt and Agent Hook Configuration

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if the task is complete. Reply {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}",
            "model": "haiku",
            "timeout": 10
          }
        ]
      }
    ],
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify the task is truly complete by reading changed files and running tests",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

## Hook Definition Structure (settings.json)

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "pattern or empty string for all",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/script.sh",
            "timeout": 10,
            "statusMessage": "Displayed in UI during execution",
            "once": false,
            "async": false
          }
        ]
      }
    ]
  }
}
```

### Hook Definition Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| type | enum | yes | none | command, prompt, or agent |
| command | string | yes (command) | none | Shell command or script path |
| prompt | string | yes (prompt) | none | LLM prompt text |
| timeout | number | no | 60 | Seconds before timeout |
| statusMessage | string | no | none | UI status text while running |
| once | boolean | no | false | Fire only once per session |
| async | boolean | no | false | Run in background (command only) |

## Hook Input (stdin JSON for command type)

```json
{
  "session_id": "uuid",
  "event": "EventName",
  "matcher": "matched-pattern",
  "tool_name": "ToolName",
  "tool_input": { "...tool-specific..." },
  "agent_type": "agent-name",
  "agent_name": "display-name",
  "transcript_summary": "recent conversation summary"
}
```

Fields vary by event type. Not all fields present in every event.

## PostToolUse Full Input Schema (verified 2026-02-14)

```json
{
  "session_id": "uuid",
  "transcript_path": "~/.claude/projects/.../transcript.jsonl",
  "cwd": "/home/user/project",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

Key fields: `tool_name` distinguishes Edit vs Write. `tool_input` has full parameters. `tool_response` has success/failure.

## SubagentStop Full Input Schema (verified 2026-02-14)

```json
{
  "session_id": "uuid",
  "hook_event_name": "SubagentStop",
  "agent_id": "agent-def456",
  "agent_type": "implementer",
  "agent_transcript_path": "~/.claude/projects/.../subagents/agent-def456.jsonl",
  "stop_hook_active": false
}
```

SubagentStop can block (exit 2 prevents agent from stopping). Matcher matches on agent_type.

## TaskCompleted Full Input Schema (verified 2026-02-15)

```json
{
  "hook_event_name": "TaskCompleted",
  "task_id": "task-uuid",
  "task_subject": "task subject line",
  "task_description": "full task description",
  "teammate_name": "agent-display-name",
  "team_name": "team-name"
}
```

Exit code 2 blocks completion, stderr fed as feedback. No JSON decision control -- exit code only.

## TeammateIdle Full Input Schema (verified 2026-02-15)

```json
{
  "hook_event_name": "TeammateIdle",
  "teammate_name": "agent-display-name",
  "team_name": "team-name"
}
```

Exit code 2 prevents idle, teammate continues. Can enforce quality gates (e.g., require all tasks complete before allowing idle).

## Hook Output Format (stdout JSON for command type)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "EventName",
    "additionalContext": "Injected into Claude's context",
    "permissionDecision": "allow|deny|ask"
  }
}
```

### Output Fields by Event

| Event | additionalContext | permissionDecision | Other |
|-------|-------------------|-------------------|-------|
| SessionStart | yes | no | - |
| UserPromptSubmit | yes | no | - |
| PreToolUse | yes | yes (allow/deny/ask) | - |
| PermissionRequest | yes | yes (allow/deny/ask) | - |
| PostToolUse | yes | no | - |
| SubagentStart | yes | no | - |
| PreCompact | yes | no | - |
| Stop | yes | no | - |
| SubagentStop | yes | no | - |
| TaskCompleted | no | no | exit 2 blocks, stderr as feedback |
| TeammateIdle | no | no | exit 2 prevents idle |

## Exit Codes

| Code | Meaning | Behavior |
|------|---------|----------|
| 0 | Success | Action proceeds, stdout JSON parsed for structured control |
| 2 | Block | Action blocked, stderr fed back as user-visible feedback. JSON stdout ignored |
| other | Error | Non-blocking error, logged but action proceeds |

### Exit Code 0 with JSON Decision (structured control)
- Exit 0 + `{ "hookSpecificOutput": { "permissionDecision": "deny" } }` = blocks via structured decision
- Exit 0 + `{ "hookSpecificOutput": { "permissionDecision": "allow" } }` = allows explicitly
- Exit 0 + `{ "hookSpecificOutput": { "additionalContext": "..." } }` = injects context, action proceeds
- Exit 0 without JSON = action proceeds (default allow)
- **Important**: Choose ONE approach per hook — either exit codes only OR exit 0 with JSON. Do not mix.

### Exit Code 2 (binary block)
- Blocks the action immediately
- stderr content fed back to Claude as feedback
- JSON stdout is ignored on exit 2
- Use for hard blocks that don't need structured reasoning

## Async Hooks
- `"async": true` on command hooks only
- Runs in background, does not block Claude's response
- Async hook results are delivered on the NEXT conversation turn
- `additionalContext` from async hooks injected when results arrive
- Cannot return blocking decisions (exit 2 ignored)
- Use case: logging, external notifications, non-critical side effects

## Matcher Patterns

| Event | Matcher Values | Behavior |
|-------|---------------|----------|
| SessionStart | startup, resume, clear, compact | Fires on specific session events |
| PreToolUse / PostToolUse | tool name (e.g., "Bash", "Edit") | Fires for specific tools only |
| SubagentStart / SubagentStop | agent type name | Fires for specific agent types |
| PreCompact | manual, auto | Fires on specific compaction triggers |
| SessionEnd | clear, logout, other | Fires on specific end conditions |
| (empty string) | matches all | Fires for every occurrence |

Matchers use regex syntax. Multiple tools can be matched with `|` operator (e.g., `Edit|Write` matches both).

## Our Hook Configuration

### SubagentStart (on-subagent-start.sh)
- Purpose: Team context injection via additionalContext
- Matcher: empty (fires for all agents)
- Behavior: Logs spawn event, injects PT reference when team_name present
- Timeout: 10s

### PreCompact (on-pre-compact.sh)
- Purpose: Task snapshot preservation before context loss
- Matcher: empty (fires for all compaction events)
- Behavior: Saves task list JSON snapshot, warns about missing L1/L2 outputs
- Timeout: 30s

### SessionStart:compact (on-session-compact.sh)
- Purpose: Recovery guidance after compaction
- Matcher: "compact" (fires only on compaction recovery)
- Behavior: Injects recovery instructions (TaskList, TaskGet on PT, teammate re-sync)
- Timeout: 15s, once: true (fires only once per session)

### SessionEnd (on-session-end.sh)
- Purpose: Cleanup temporary files on session termination
- Matcher: empty (fires for all session end conditions)
- Behavior: Removes /tmp/src-changes-*.log, .processed, src-failures-*.log, /tmp/claude-hooks/
- Timeout: 10s

### PostToolUse:Edit|Write (on-file-change.sh) — SRC Stage 1 [Agent-Scoped]
- Purpose: Silent file change logger for Smart Reactive Codebase
- Matcher: "Edit|Write" (fires for Edit and Write tool calls)
- Scope: Agent-scoped on implementer.md and infra-implementer.md (not global settings.json). Only fires during active implementer/infra-implementer agent execution.
- Behavior: Logs changed file path to /tmp/src-changes-{session_id}.log
- Timeout: 5s, async: true
- Output: None (silent, no additionalContext)

### PostToolUseFailure:Edit|Write (on-file-change-fail.sh) [Agent-Scoped]
- Purpose: Log failed Edit/Write operations for debugging
- Matcher: "Edit|Write" (fires for Edit and Write tool failures)
- Scope: Agent-scoped on implementer.md and infra-implementer.md (not global settings.json)
- Behavior: Logs failed file path to /tmp/src-failures-{session_id}.log
- Timeout: 5s, async: true
- Output: None (silent, no additionalContext)

### SubagentStop:implementer|infra-implementer (on-implementer-done.sh) — SRC Stage 2
- Purpose: Impact summary injector after implementer/infra-implementer completes
- Matcher: "implementer|infra-implementer" (fires for both agent types)
- Behavior: Reads change log, greps reverse references, injects impact alert. Log renamed to .processed (not deleted) to preserve data for parallel/sequential implementers.
- Timeout: 30s
- Output: additionalContext with SRC IMPACT ALERT and dependent file list

### TaskCompleted (on-task-completed.sh)
- Purpose: Log task completion events for pipeline tracking
- Matcher: empty (fires for all task completions)
- Behavior: Logs task_id, subject, teammate, team to /tmp/task-completions-{session_id}.log
- Timeout: 10s
- Output: None (logging only, always exit 0)

### Stop:delivery-agent (prompt hook) [Agent-Scoped]
- Purpose: Haiku quality gate for delivery-agent completion
- Scope: Agent-scoped on delivery-agent.md only
- Type: prompt (Haiku model, single-turn LLM evaluation)
- Behavior: Verifies git commit, MEMORY.md update, and PT TaskUpdate all completed
- Timeout: 15s
- Output: `{ok: true/false, reason: "..."}` -- blocks delivery if incomplete
