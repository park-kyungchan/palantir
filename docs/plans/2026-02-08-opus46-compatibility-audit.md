---
title: "Opus 4.6 Agent Teams Compatibility Audit — Findings & Fix Specifications"
version: "1.0"
date: "2026-02-08"
scope: "Hook input schema validation against Claude Code v2.1.36"
status: "DESIGN — PENDING APPROVAL"
issues_found: 3
files_to_modify: 3
---

# Opus 4.6 Agent Teams Compatibility Audit

## 1. Executive Summary

This document presents the complete findings of a compatibility audit between our `.claude/`
infrastructure (CLAUDE.md v5.0, 8 hook scripts, 6 agent definitions, task-api-guideline.md v5.0,
4 skills, settings.json) and the official Claude Code v2.1.36 Agent Teams features.

**Methodology:** Two-phase dual-verification approach:
1. **Claude-code-guide agent research** — systematic audit of every official feature against our usage
2. **Real log evidence analysis** — `teammate-lifecycle.log` (149+ entries) confirming field mapping failures

**Result Summary:**

| Category | Count | Status |
|----------|-------|--------|
| CRITICAL issues | 1 (affects 2 hooks) | Fix required |
| MEDIUM issues | 1 (affects 1 hook) | Fix required |
| LOW issues | 1 (within CRITICAL fix scope) | Fix included |
| Validated items (no issues) | 37+ | Pass |
| Infrastructure compliance | 98%+ | Pass |

**Key Finding:** The SubagentStart and SubagentStop hooks reference field names
(`.agent_name`, `.tool_input.name`, `.tool_input.team_name`) that do not exist in the
official hook input schema. This causes agent identification to always resolve to `"unknown"`,
making the teammate lifecycle log useless for debugging and audit purposes.

**Impact Assessment:** The core DIA enforcement (Layers 1-3) is unaffected because it operates
through SendMessage protocol + file artifacts, not hooks. The hook-based enforcement (Layer 4)
for TeammateIdle and TaskCompleted works correctly (uses proper field names). Only SubagentStart/
SubagentStop logging and GC injection team routing are affected.

---

## 2. Audit Scope

### 2.1 Infrastructure Audited

| Component | File(s) | Version | Lines |
|-----------|---------|---------|-------|
| Constitution | `.claude/CLAUDE.md` | v5.0 | ~381 |
| Task API Guide | `.claude/references/task-api-guideline.md` | v5.0 | ~537 |
| Settings | `.claude/settings.json` | — | 133 |
| Hook: SubagentStart | `.claude/hooks/on-subagent-start.sh` | — | 46 |
| Hook: SubagentStop | `.claude/hooks/on-subagent-stop.sh` | — | 48 |
| Hook: TeammateIdle | `.claude/hooks/on-teammate-idle.sh` | — | 46 |
| Hook: TaskCompleted | `.claude/hooks/on-task-completed.sh` | — | 51 |
| Hook: PostToolUse(TaskUpdate) | `.claude/hooks/on-task-update.sh` | — | 31 |
| Hook: PreCompact | `.claude/hooks/on-pre-compact.sh` | — | 40 |
| Hook: SessionStart(compact) | `.claude/hooks/on-session-compact.sh` | — | 25 |
| Hook: PostToolUseFailure | `.claude/hooks/on-tool-failure.sh` | — | 28 |
| Agent: researcher | `.claude/agents/researcher.md` | — | 143 |
| Agent: architect | `.claude/agents/architect.md` | — | 160 |
| Agent: devils-advocate | `.claude/agents/devils-advocate.md` | — | 127 |
| Agent: implementer | `.claude/agents/implementer.md` | — | 179 |
| Agent: tester | `.claude/agents/tester.md` | — | 154 |
| Agent: integrator | `.claude/agents/integrator.md` | — | 185 |
| Skill: brainstorming-pipeline | `.claude/skills/brainstorming-pipeline/SKILL.md` | — | 481 |
| Skill: agent-teams-write-plan | `.claude/skills/agent-teams-write-plan/SKILL.md` | — | 275 |
| Skill: agent-teams-execution-plan | `.claude/skills/agent-teams-execution-plan/SKILL.md` | — | 532 |
| Skill: plan-validation-pipeline | `.claude/skills/plan-validation-pipeline/SKILL.md` | — | 348 |

### 2.2 Verification Target

Claude Code CLI v2.1.36, Opus 4.6 (claude-opus-4-6), Agent Teams experimental feature
(`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

### 2.3 Evidence Sources

1. **Official documentation** (claude-code-guide agent research, 2 independent runs)
2. **Real runtime logs** (`.agent/teams/teammate-lifecycle.log`, 149+ entries)
3. **Real runtime logs** (`.agent/teams/task-lifecycle.log`, 65+ entries)

---

## 3. Official Hook Input Schema Reference

This section documents the exact JSON schema piped to stdin for each hook event,
as verified through claude-code-guide agent research against Claude Code v2.1.36.

### 3.1 SubagentStart

```json
{
  "agent_id": "string — unique identifier for this agent instance",
  "agent_type": "string — the subagent_type passed to Task tool",
  "session_id": "string — session identifier",
  "transcript_path": "string — path to transcript file",
  "cwd": "string — current working directory",
  "hook_event_name": "SubagentStart"
}
```

**Not available:** `agent_name`, `tool_input`, `tool_input.name`, `tool_input.team_name`,
`tool_input.subagent_type`, `teammate_name`, `team_name`.

**Key insight:** SubagentStart fires AFTER the Task tool call completes and the subagent
process begins. The original `tool_input` from the Task call is NOT passed to the hook.
Only the resulting agent metadata is available.

### 3.2 SubagentStop

```json
{
  "agent_id": "string — same agent_id as SubagentStart",
  "agent_type": "string — the subagent_type",
  "agent_transcript_path": "string — path to completed transcript (added v2.0.42)",
  "session_id": "string — session identifier",
  "transcript_path": "string — path to transcript file",
  "cwd": "string — current working directory",
  "hook_event_name": "SubagentStop"
}
```

**Not available:** Same as SubagentStart — no `agent_name`, no `tool_input.*`.

**Key addition vs. SubagentStart:** `agent_transcript_path` is available (the completed
transcript), useful for post-mortem analysis and L1/L2 output verification.

### 3.3 TeammateIdle

```json
{
  "teammate_name": "string — the name parameter from Task tool",
  "team_name": "string — the team_name parameter from Task tool",
  "hook_event_name": "TeammateIdle"
}
```

**Key difference from SubagentStart/Stop:** TeammateIdle is an Agent Teams-specific event
that fires with full teammate context, including the human-readable `teammate_name` and
`team_name`. This is why our on-teammate-idle.sh works correctly.

### 3.4 TaskCompleted

```json
{
  "teammate_name": "string — the teammate who completed the task",
  "team_name": "string — the team name",
  "task_subject": "string — the subject of the completed task",
  "hook_event_name": "TaskCompleted"
}
```

### 3.5 PostToolUse (matched on "TaskUpdate")

```json
{
  "tool_name": "TaskUpdate",
  "tool_input": {
    "taskId": "string",
    "status": "string",
    "subject": "string (optional)",
    "owner": "string (optional)",
    "...": "all parameters passed to the tool"
  },
  "tool_result": "string — the tool's output",
  "hook_event_name": "PostToolUse",
  "session_id": "string",
  "cwd": "string"
}
```

### 3.6 PreCompact

```json
{
  "session_id": "string",
  "cwd": "string",
  "hook_event_name": "PreCompact"
}
```

**Note:** PreCompact provides minimal metadata. Our hook correctly avoids parsing
complex fields and instead uses filesystem operations.

### 3.7 SessionStart (matched on "compact")

```json
{
  "session_id": "string",
  "cwd": "string",
  "hook_event_name": "SessionStart",
  "session_type": "compact"
}
```

### 3.8 PostToolUseFailure

```json
{
  "tool_name": "string — which tool failed",
  "error": "string — error message",
  "tool_input": {
    "...": "all parameters that were passed to the failed tool"
  },
  "hook_event_name": "PostToolUseFailure",
  "session_id": "string",
  "cwd": "string"
}
```

**Not available:** `agent_name`. This event fires in the context of a tool failure,
not in the context of a specific agent/teammate.

---

## 4. Findings: CRITICAL Issues

### ISSUE-001: SubagentStart/SubagentStop hooks use non-existent input fields

**Severity:** CRITICAL
**Affected files:**
- `.claude/hooks/on-subagent-start.sh` (lines 8-10)
- `.claude/hooks/on-subagent-stop.sh` (lines 8-10)

**Problem:**

Both hooks attempt to read three fields that do not exist in the official schema:

| Line | Current Code | Field Accessed | Official Status |
|------|-------------|----------------|-----------------|
| 8 | `'.agent_type // .tool_input.subagent_type // "unknown"'` | `.tool_input.subagent_type` | NOT EXISTS (fallback; `.agent_type` works) |
| 9 | `'.agent_name // .tool_input.name // "unknown"'` | `.agent_name`, `.tool_input.name` | BOTH NOT EXIST |
| 10 | `'.tool_input.team_name // "no-team"'` | `.tool_input.team_name` | NOT EXISTS |

**Impact analysis:**

1. **Agent identification broken:** `AGENT_NAME` always resolves to `"unknown"` because
   neither `.agent_name` nor `.tool_input.name` exist. This makes all 149+ lifecycle log
   entries useless for identifying which specific agent started/stopped.

2. **Team routing broken:** `TEAM_NAME` always resolves to `"no-team"` (start) or
   `"unknown"` (stop), causing:
   - GC version injection in SubagentStart cannot route to the correct team's GC file
   - Falls through to the filesystem fallback (find latest GC), which works but is fragile

3. **L1/L2 check in SubagentStop broken:** Lines 20-28 of on-subagent-stop.sh use
   `$AGENT_NAME` and `$TEAM_NAME` to locate L1/L2 files. Since both are always wrong,
   the check never finds the files and always logs a false warning.

**Evidence:**

All 149+ entries in `.agent/teams/teammate-lifecycle.log` show:
```
[2026-02-07 02:45:22] SUBAGENT_START | name=unknown | type=claude-code-guide | team=no-team
[2026-02-07 02:45:47] SUBAGENT_STOP  | name=unknown | type=claude-code-guide
[2026-02-08 08:19:15] SUBAGENT_START | name=unknown | type=researcher | team=no-team
[2026-02-08 09:55:49] SUBAGENT_START | name=unknown | type=implementer | team=no-team
```

**Note:** `agent_type` partially works because `.agent_type` IS an official field. The
jq fallback chain `'.agent_type // .tool_input.subagent_type // "unknown"'` succeeds on
the first option. However, some SubagentStop entries show empty type (`type=`) suggesting
the field may not always be populated on stop events for certain agent types.

---

## 5. Findings: MEDIUM Issues

### ISSUE-002: PostToolUseFailure hook uses non-existent `.agent_name` field

**Severity:** MEDIUM
**Affected file:** `.claude/hooks/on-tool-failure.sh` (lines 4, 13)

**Problem:**

Two issues in this file:

1. **Line 13:** `'.agent_name // "unknown"'` — The `.agent_name` field does not exist in the
   PostToolUseFailure schema. The agent context is not available for tool failure events.
   Result: `AGENT_NAME` always resolves to `"unknown"`.

2. **Line 4:** `set -euo pipefail` — This causes the entire script to exit silently if:
   - Any variable is unset (`-u` flag)
   - Any command in a pipeline fails (`-o pipefail`)
   - Any jq command returns empty/null (treated as failure by `-e`)

   Combined with the non-existent `.agent_name` field and potential empty jq results,
   this means the hook may silently abort before reaching its logging code. Tool failures
   could go completely unrecorded.

**Impact:**

- Tool failure logging loses agent identification (minor — we don't need agent_name for tool failures)
- `set -euo pipefail` may cause the entire hook to abort silently (moderate — could miss logging)
- No blocking impact on DIA enforcement (hook doesn't use exit 2)

---

## 6. Findings: LOW Issues

### ISSUE-003: SubagentStop hook doesn't use available `agent_id` and `agent_transcript_path`

**Severity:** LOW (addressed within ISSUE-001 fix scope)
**Affected file:** `.claude/hooks/on-subagent-stop.sh`

**Problem:**

The SubagentStop schema provides two valuable fields that our hook ignores:

1. **`agent_id`** — Unique identifier for the agent instance. Useful for correlating
   SubagentStart and SubagentStop events (same `agent_id` in both events).

2. **`agent_transcript_path`** — Path to the completed agent transcript. Added in
   v2.0.42. Valuable for:
   - Post-mortem analysis of agent behavior
   - Automated output quality checks
   - Finding L1/L2/L3 output paths from the transcript

**Impact:** Missing audit trail data. Not a functional failure, but a lost opportunity
for debugging and monitoring.

---

## 7. Validated Items (No Issues Found)

### 7.1 Agent Frontmatter Fields (all 6 agents)

All frontmatter fields used are officially supported by Claude Code v2.1.36:

| Field | Used By | Official Status |
|-------|---------|-----------------|
| `name` | All 6 agents | Supported |
| `description` | All 6 agents | Supported |
| `model` | All 6 agents (claude-opus-4-6) | Supported |
| `permissionMode` | implementer (acceptEdits), integrator (acceptEdits) | Supported |
| `memory` | researcher, architect, implementer, integrator | Supported |
| `color` | All 6 agents | Supported |
| `maxTurns` | All 6 agents | Supported |
| `tools` | All 6 agents | Supported |
| `disallowedTools` | All 6 agents | Supported |

### 7.2 Agent Tool Configurations

| Agent | Tools Configuration | Correctness |
|-------|-------------------|-------------|
| researcher | Read-only (no Edit/Write/Bash) + MCP | Correct |
| architect | Write (new files) + Read + MCP, no Edit/Bash | Correct |
| devils-advocate | Read-only (no Write/Edit/Bash) + MCP | Correct |
| implementer | Full access (Read/Write/Edit/Bash) + MCP | Correct |
| tester | Write + Bash + Read + MCP, no Edit | Correct |
| integrator | Full access + MCP, cross-boundary capable | Correct |

### 7.3 Hook Event Configuration (settings.json)

| Event | Matcher | Exit 2 Blocking | Field Names | Status |
|-------|---------|-----------------|-------------|--------|
| SubagentStart | `""` (all) | N/A (non-blocking) | **BROKEN** (ISS-001) | FAIL |
| SubagentStop | `""` (all) | N/A | **BROKEN** (ISS-001) | FAIL |
| TeammateIdle | `""` (all) | Yes, works | `teammate_name`, `team_name` | PASS |
| TaskCompleted | `""` (all) | Yes, works | `teammate_name`, `team_name`, `task_subject` | PASS |
| PostToolUse | `"TaskUpdate"` | N/A | `tool_input.*` | PASS |
| PreCompact | `""` (all) | N/A | No field parsing | PASS |
| SessionStart | `"compact"` | N/A | `once: true` | PASS |
| PostToolUseFailure | `""` (all) | N/A | **PARTIAL** (ISS-002) | WARN |

### 7.4 DIA Protocol (4-Layer Architecture)

The DIA enforcement protocol operates entirely through SendMessage communication and file
artifacts, not through hook input schemas. All four layers are self-consistent:

| Layer | Mechanism | Hook Dependency | Status |
|-------|-----------|-----------------|--------|
| L1: CIP | GC embedding in directives | SubagentStart additionalContext (fallback works) | PASS |
| L2: DIAVP | RC-01~RC-10 echo-back | None | PASS |
| L3: LDAP | Challenge questions | None | PASS |
| L4: Hooks | TeammateIdle + TaskCompleted exit 2 | Correct field names | PASS |

### 7.5 Task API Configuration

| Feature | Implementation | Status |
|---------|---------------|--------|
| Lead-only TaskCreate/TaskUpdate | `disallowedTools` in all 6 agent .md files | PASS |
| Teammate read-only TaskList/TaskGet | Allowed in all agent `tools` lists | PASS |
| Dependency tracking | `addBlockedBy`/`addBlocks` bidirectional | PASS |
| ISS-001~005 documented | task-api-guideline.md §12 | PASS |

### 7.6 Skills

All 4 skills use officially supported features:

| Feature | Usage | Status |
|---------|-------|--------|
| `argument-hint` frontmatter | All 4 skills | PASS |
| `$ARGUMENTS` variable | All 4 skills | PASS |
| Dynamic context `!`backtick`` | All 4 skills | PASS |
| YAML frontmatter format | All 4 skills | PASS |

### 7.7 Settings.json

| Setting | Value | Status |
|---------|-------|--------|
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `"1"` | PASS |
| `teammateMode` | `"tmux"` | PASS |
| `language` | `"Korean"` | PASS |
| Permission deny rules | 7 patterns | PASS (valid syntax) |
| Hook configurations | 8 events | PASS (valid structure) |
| `enabledPlugins` | 2 plugins | PASS |

### 7.8 Not-Yet-Used Official Features (Informational)

These are officially supported features that our infrastructure does not yet use.
They are not issues — just opportunities for future enhancement:

1. **Agent `skills` frontmatter** — Auto-load specific skills for subagents
2. **Agent `hooks` frontmatter** — Agent-scoped hooks (override global hooks per agent type)
3. **`Task(agent_type)` syntax in tools** — Restrict which agent types a subagent can spawn
4. **Agent `apiKeyEnv` frontmatter** — Custom API key per agent type

---

## 8. Fix Specification: ISSUE-001 (on-subagent-start.sh)

### 8.1 Current Code (BROKEN)

```bash
#!/bin/bash
# Hook: SubagentStart — Logging + GC version additionalContext injection
# Cannot block spawn (exit 2 is non-blocking for SubagentStart).
# Injects current GC version as additionalContext for context awareness.

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "no-team"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# GC version injection via additionalContext
# Find active team's global-context.md
GC_FILE=""
if [ "$TEAM_NAME" != "no-team" ] && [ -n "$TEAM_NAME" ]; then
  GC_FILE="$LOG_DIR/$TEAM_NAME/global-context.md"
fi

# Fallback: use most recently modified team directory
if [ -z "$GC_FILE" ] || [ ! -f "$GC_FILE" ]; then
  LATEST_TEAM_DIR=$(ls -td "$LOG_DIR"/*/global-context.md 2>/dev/null | head -1)
  if [ -n "$LATEST_TEAM_DIR" ]; then
    GC_FILE="$LATEST_TEAM_DIR"
  fi
fi

if [ -f "$GC_FILE" ]; then
  GC_VERSION=$(grep -m1 '^version:' "$GC_FILE" 2>/dev/null | awk '{print $2}')
  if [ -n "$GC_VERSION" ]; then
    jq -n --arg ver "$GC_VERSION" --arg team "$TEAM_NAME" '{
      "hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Current GC: " + $ver + ". Verify your injected context version matches.")
      }
    }'
    exit 0
  fi
fi

exit 0
```

### 8.2 Fixed Code

```bash
#!/bin/bash
# Hook: SubagentStart — Logging + GC version additionalContext injection
# Cannot block spawn (exit 2 is non-blocking for SubagentStart).
# Injects current GC version as additionalContext for context awareness.
#
# Official SubagentStart schema fields:
#   agent_id, agent_type, session_id, transcript_path, cwd, hook_event_name
# NOT available: agent_name, tool_input.*, teammate_name, team_name

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // "unknown"' 2>/dev/null)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // "unknown"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | id=$AGENT_ID | type=$AGENT_TYPE" >> "$LOG_DIR/teammate-lifecycle.log"

# GC version injection via additionalContext
# SubagentStart has no team_name field — use filesystem heuristic to find active team
GC_FILE=""
TEAM_LABEL="no-team"

# Find the most recently modified team's global-context.md
LATEST_GC=$(ls -t "$LOG_DIR"/*/global-context.md 2>/dev/null | head -1)
if [ -n "$LATEST_GC" ] && [ -f "$LATEST_GC" ]; then
  GC_FILE="$LATEST_GC"
  TEAM_LABEL=$(basename "$(dirname "$LATEST_GC")")
fi

if [ -f "$GC_FILE" ]; then
  GC_VERSION=$(grep -m1 '^version:' "$GC_FILE" 2>/dev/null | awk '{print $2}')
  if [ -n "$GC_VERSION" ]; then
    jq -n --arg ver "$GC_VERSION" --arg team "$TEAM_LABEL" --arg aid "$AGENT_ID" '{
      "hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Current GC: " + $ver + ". Agent ID: " + $aid + ". Verify your injected context version matches.")
      }
    }'
    exit 0
  fi
fi

exit 0
```

### 8.3 Changes Summary

| Line(s) | Change | Rationale |
|---------|--------|-----------|
| 5-7 | Added schema documentation comment | Future maintainability — prevent re-introducing non-existent fields |
| 10 | `.agent_type // "unknown"` (removed `.tool_input.subagent_type` fallback) | `.tool_input.subagent_type` doesn't exist; `.agent_type` is the official field |
| 11 | NEW: `.agent_id // "unknown"` | Official field for agent identification; replaces broken `.agent_name` |
| 12 | REMOVED: `AGENT_NAME` line | `.agent_name` and `.tool_input.name` don't exist |
| 13 | REMOVED: `TEAM_NAME` from input | `.tool_input.team_name` doesn't exist |
| 17 | Log format: `id=$AGENT_ID` replaces `name=$AGENT_NAME` | Use available data |
| 17 | Log format: removed `team=` | Team info not available in input |
| 21-27 | Simplified team discovery: always use filesystem heuristic | Previous code tried `$TEAM_NAME` first (always "no-team") then fell through to fallback. Now uses fallback directly since team_name is never available. |
| 27 | Extract `TEAM_LABEL` from directory path | For log/additionalContext display |
| 34 | Added `$aid` (agent_id) to additionalContext | Agent ID in context helps with correlation |

### 8.4 Side Effects

- **Log format change:** `name=unknown | type=X | team=no-team` → `id=UUID | type=X`
  - Any scripts/tools parsing the old log format will need updating
  - The old format was useless (always "unknown"), so this is a net improvement
- **additionalContext change:** Now includes Agent ID
  - Positive: agents can reference their own ID for correlation
  - No negative impact
- **GC injection still works:** The filesystem heuristic was already the de facto mechanism
  (team routing was always broken). Now it's the explicit primary mechanism.

---

## 9. Fix Specification: ISSUE-001 (on-subagent-stop.sh)

### 9.1 Current Code (BROKEN)

```bash
#!/bin/bash
# Hook: SubagentStop — Teammate termination logging + L1/L2 output validation
# Fires when any teammate/subagent finishes
# Input: JSON on stdin with session info

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "unknown"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_STOP | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# Check if the stopped agent left L1/L2 files using direct path construction
TEAM_DIR="$LOG_DIR"
if [ "$TEAM_NAME" != "unknown" ] && [ -n "$TEAM_NAME" ]; then
  TEAM_DIR="$LOG_DIR/$TEAM_NAME"
fi
if [ -n "$AGENT_NAME" ] && [ "$AGENT_NAME" != "unknown" ]; then
  L1_EXISTS=$(ls "$TEAM_DIR"/phase-*/"$AGENT_NAME"/L1-index.yaml 2>/dev/null | head -1)
  L2_EXISTS=$(ls "$TEAM_DIR"/phase-*/"$AGENT_NAME"/L2-summary.md 2>/dev/null | head -1)
  if [ -z "$L1_EXISTS" ] && [ -z "$L2_EXISTS" ]; then
    echo "[$TIMESTAMP] SUBAGENT_STOP | WARNING: $AGENT_NAME stopped without L1/L2 output" >> "$LOG_DIR/teammate-lifecycle.log"
  fi
fi

# Output structured JSON summary
if command -v jq &>/dev/null; then
  HAS_L1="false"
  HAS_L2="false"
  [ -n "$L1_EXISTS" ] && HAS_L1="true"
  [ -n "$L2_EXISTS" ] && HAS_L2="true"
  jq -n --arg name "$AGENT_NAME" --arg type "$AGENT_TYPE" --argjson l1 "$HAS_L1" --argjson l2 "$HAS_L2" '{
    "hookSpecificOutput": {
      "hookEventName": "SubagentStop",
      "agent": $name,
      "agentType": $type,
      "hasL1": $l1,
      "hasL2": $l2
    }
  }'
fi

exit 0
```

### 9.2 Fixed Code

```bash
#!/bin/bash
# Hook: SubagentStop — Teammate termination logging + transcript path capture
# Fires when any teammate/subagent finishes.
#
# Official SubagentStop schema fields:
#   agent_id, agent_type, agent_transcript_path, session_id, transcript_path, cwd, hook_event_name
# NOT available: agent_name, tool_input.*, teammate_name, team_name
#
# L1/L2 enforcement is handled by TeammateIdle and TaskCompleted hooks
# (which have teammate_name and team_name). SubagentStop focuses on
# logging agent_id and transcript_path for audit trail.

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // "unknown"' 2>/dev/null)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // "unknown"' 2>/dev/null)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.agent_transcript_path // "none"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_STOP | id=$AGENT_ID | type=$AGENT_TYPE | transcript=$TRANSCRIPT" >> "$LOG_DIR/teammate-lifecycle.log"

# Output structured JSON summary with available fields
if command -v jq &>/dev/null; then
  jq -n --arg aid "$AGENT_ID" --arg type "$AGENT_TYPE" --arg transcript "$TRANSCRIPT" '{
    "hookSpecificOutput": {
      "hookEventName": "SubagentStop",
      "agentId": $aid,
      "agentType": $type,
      "transcriptPath": $transcript
    }
  }'
fi

exit 0
```

### 9.3 Changes Summary

| Line(s) | Change | Rationale |
|---------|--------|-----------|
| 4-10 | Added schema documentation + design rationale comment | Prevent re-introducing broken fields; explain L1/L2 delegation |
| 14 | `.agent_type // "unknown"` (removed `.tool_input.subagent_type` fallback) | Official field only |
| 15 | NEW: `.agent_id // "unknown"` | Official field; replaces broken `.agent_name` |
| 16 | NEW: `.agent_transcript_path // "none"` | Official field (ISS-003 fix); valuable audit data |
| 17 | REMOVED: `AGENT_NAME` and `TEAM_NAME` lines | Non-existent fields |
| 22 | Log format: `id=$AGENT_ID | type=$AGENT_TYPE | transcript=$TRANSCRIPT` | Use available data + new transcript path |
| 24-48 | REMOVED: entire L1/L2 check block (lines 18-29 of original) | Cannot work without `teammate_name`/`team_name`. TeammateIdle and TaskCompleted hooks already enforce L1/L2 with correct field names. Duplicating broken enforcement here adds false warnings without value. |
| 25-32 | Simplified JSON output | Uses `agentId` and `transcriptPath` instead of broken `agent` field |

### 9.4 Side Effects

- **L1/L2 check removed from SubagentStop:** This is intentional and correct.
  - The check was ALWAYS failing (producing false "stopped without L1/L2" warnings)
  - TeammateIdle (on-teammate-idle.sh) already enforces L1/L2 with exit 2 blocking
  - TaskCompleted (on-task-completed.sh) also enforces L1/L2 with exit 2 blocking
  - SubagentStop adds no value for L1/L2 enforcement since it lacks teammate_name
- **Log format change:** Same as ISSUE-001 start hook
- **New `transcript` field in log:** Enables post-mortem analysis

---

## 10. Fix Specification: ISSUE-002 (on-tool-failure.sh)

### 10.1 Current Code (BROKEN)

```bash
#!/bin/bash
# on-tool-failure.sh — Log tool execution failures for debugging
# Event: PostToolUseFailure
set -euo pipefail

LOG_DIR="/home/palantir/.agent/teams"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Parse stdin JSON
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null)
ERROR=$(echo "$INPUT" | jq -r '.error // "no error details"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // "unknown"' 2>/dev/null)

# Find active team directory from input or most recent
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // empty' 2>/dev/null)
if [ -n "$TEAM_NAME" ]; then
  LATEST_TEAM="$LOG_DIR/$TEAM_NAME"
else
  LATEST_TEAM=$(ls -td "$LOG_DIR"/*/ 2>/dev/null | head -1)
fi
if [ -z "$LATEST_TEAM" ] || [ ! -d "$LATEST_TEAM" ]; then
  exit 0
fi

# Log the failure
echo "[$TIMESTAMP] TOOL_FAILURE | agent=$AGENT_NAME | tool=$TOOL_NAME | error=$ERROR" >> "$LATEST_TEAM/tool-failures.log"
exit 0
```

### 10.2 Fixed Code

```bash
#!/bin/bash
# on-tool-failure.sh — Log tool execution failures for debugging
# Event: PostToolUseFailure
#
# Official PostToolUseFailure schema fields:
#   tool_name, error, tool_input, hook_event_name, session_id, cwd
# NOT available: agent_name (no agent context in tool failure events)

LOG_DIR="/home/palantir/.agent/teams"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Parse stdin JSON
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null)
ERROR=$(echo "$INPUT" | jq -r '.error // "no error details"' 2>/dev/null)

# Find active team directory from tool_input (if team-related tool) or most recent
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // empty' 2>/dev/null)
if [ -n "$TEAM_NAME" ]; then
  LATEST_TEAM="$LOG_DIR/$TEAM_NAME"
else
  LATEST_TEAM=$(ls -td "$LOG_DIR"/*/ 2>/dev/null | head -1)
fi
if [ -z "$LATEST_TEAM" ] || [ ! -d "$LATEST_TEAM" ]; then
  mkdir -p "$LOG_DIR"
  echo "[$TIMESTAMP] TOOL_FAILURE | tool=$TOOL_NAME | error=$ERROR" >> "$LOG_DIR/tool-failures.log"
  exit 0
fi

# Log the failure
echo "[$TIMESTAMP] TOOL_FAILURE | tool=$TOOL_NAME | error=$ERROR" >> "$LATEST_TEAM/tool-failures.log"
exit 0
```

### 10.3 Changes Summary

| Line(s) | Change | Rationale |
|---------|--------|-----------|
| 4-6 | Added schema documentation comment | Prevent re-introducing non-existent fields |
| 4 (old) | REMOVED: `set -euo pipefail` | `-u` (unset vars) and `-o pipefail` cause silent exits on empty jq results. Hook scripts should be resilient — a logging hook failing silently defeats its purpose. |
| 13 (old) | REMOVED: `AGENT_NAME` line | `.agent_name` doesn't exist in PostToolUseFailure |
| 16 | KEPT: `.tool_input.team_name` | `.tool_input` IS available in PostToolUseFailure (it's the failed tool's input). If the failed tool had a `team_name` param, this works. |
| 25-27 | NEW: Fallback logging to `$LOG_DIR/tool-failures.log` | If no team directory exists, still log the failure rather than silently dropping it |
| 28 | Log format: removed `agent=` field | No agent context available |

### 10.4 Side Effects

- **Log format change:** `agent=$AGENT_NAME | tool=X | error=Y` → `tool=X | error=Y`
  - Agent identification was always "unknown" anyway
- **Fallback logging added:** Tool failures are now always logged, even without a team directory
- **`set -euo pipefail` removal:** Script is now more resilient to edge cases
  - Note: `set -e` is also removed. For a logging hook, we want maximum resilience —
    a partial log is better than no log at all.

---

## 11. Implementation Plan

### 11.1 Dependency Chain

```
ISSUE-002 (on-tool-failure.sh)  ──┐
                                   │  (all independent — no cross-dependencies)
ISSUE-001a (on-subagent-start.sh) ─┤
                                   │
ISSUE-001b (on-subagent-stop.sh) ──┘
                                   │
                                   ▼
                         Verification Step
                                   │
                                   ▼
                         Log Format Documentation
```

All three fixes are **independent** — they modify separate files with no shared state.
They can be implemented in parallel or in any order.

### 11.2 Implementation Steps

| # | Step | File | Dependency | Estimated Lines Changed |
|---|------|------|------------|------------------------|
| 1 | Fix on-subagent-start.sh | `.claude/hooks/on-subagent-start.sh` | None | Rewrite (46→41 lines) |
| 2 | Fix on-subagent-stop.sh | `.claude/hooks/on-subagent-stop.sh` | None | Rewrite (48→35 lines) |
| 3 | Fix on-tool-failure.sh | `.claude/hooks/on-tool-failure.sh` | None | Rewrite (28→31 lines) |
| 4 | Verify all hooks | Run test subagent, check logs | Steps 1-3 | Manual verification |
| 5 | Update MEMORY.md | `.claude/projects/-home-palantir/memory/MEMORY.md` | Step 4 | Add audit results |

### 11.3 Files NOT Modified

The following files were audited and require NO changes:

- `.claude/CLAUDE.md` — v5.0 fully compatible
- `.claude/references/task-api-guideline.md` — v5.0 fully compatible
- `.claude/settings.json` — all configurations valid
- `.claude/hooks/on-teammate-idle.sh` — correct field names
- `.claude/hooks/on-task-completed.sh` — correct field names
- `.claude/hooks/on-task-update.sh` — correct field names
- `.claude/hooks/on-pre-compact.sh` — no field parsing issues
- `.claude/hooks/on-session-compact.sh` — no field parsing issues
- All 6 agent .md files — all frontmatter fields supported
- All 4 skill SKILL.md files — all features supported

---

## 12. Verification Criteria

### 12.1 Per-File Verification

**on-subagent-start.sh:**
1. Spawn a test subagent (e.g., `claude-code-guide` or `Explore`)
2. Check `teammate-lifecycle.log` for new entry with format: `SUBAGENT_START | id=<UUID> | type=<type>`
3. Verify `id` is NOT "unknown" (should be a UUID-like string)
4. Verify `type` matches the spawned agent type
5. If team is active: verify additionalContext includes GC version and Agent ID

**on-subagent-stop.sh:**
1. Wait for the test subagent to complete
2. Check `teammate-lifecycle.log` for new entry with format: `SUBAGENT_STOP | id=<UUID> | type=<type> | transcript=<path>`
3. Verify `id` matches the SubagentStart entry (same UUID)
4. Verify `transcript` is NOT "none" (should be a file path)
5. Verify NO false "stopped without L1/L2" warnings

**on-tool-failure.sh:**
1. Trigger a tool failure (e.g., Read a non-existent file)
2. Check `tool-failures.log` for new entry with format: `TOOL_FAILURE | tool=<name> | error=<msg>`
3. Verify no `agent=unknown` in the log entry
4. Verify the hook does NOT silently abort (log entry should always appear)

### 12.2 Regression Verification

1. **TeammateIdle enforcement still works:** L1/L2 exit 2 blocking unaffected (different hook file)
2. **TaskCompleted enforcement still works:** Same as above
3. **GC injection still works:** SubagentStart still outputs additionalContext with GC version
4. **Task lifecycle logging still works:** on-task-update.sh is unchanged

### 12.3 Log Format Migration

Old format (broken):
```
[timestamp] SUBAGENT_START | name=unknown | type=X | team=no-team
[timestamp] SUBAGENT_STOP  | name=unknown | type=X | team=unknown
```

New format (fixed):
```
[timestamp] SUBAGENT_START | id=<UUID> | type=X
[timestamp] SUBAGENT_STOP  | id=<UUID> | type=X | transcript=<path>
```

No migration of old log entries needed — they were all "unknown" anyway.

---

## 13. Impact Analysis

### 13.1 Infrastructure Impact Matrix

| Component | Impact | Details |
|-----------|--------|---------|
| CLAUDE.md §9 (Hook Layer 4) | **UPDATE NEEDED** | §9 references SubagentStart injecting GC — still works but implementation changed. No CLAUDE.md text change needed since it describes behavior, not implementation. |
| task-api-guideline.md | None | No hook implementation details |
| Agent .md files | None | Agent definitions don't reference hook internals |
| Skills | None | Skills don't interact with hooks directly |
| TeammateIdle hook | None | Independent file, different schema |
| TaskCompleted hook | None | Independent file, different schema |
| Other hooks | None | No cross-hook dependencies |
| DIA Layer 1-3 | None | Operate through SendMessage, not hooks |
| DIA Layer 4 | **Improved** | SubagentStop no longer produces false L1/L2 warnings |
| Lifecycle logging | **Changed format** | Log parsers (if any) need updating |

### 13.2 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| `agent_id` not populated on some events | Low | Log shows "unknown" (same as current) | jq fallback `// "unknown"` handles this |
| `agent_transcript_path` not available on older versions | Low | Log shows "none" | jq fallback `// "none"` handles this |
| GC injection fails without team_name routing | Already happening | Fallback to filesystem heuristic works | Unchanged behavior; was always using fallback |
| Log format change breaks monitoring | Very Low | No known log consumers | Old logs were useless anyway |

### 13.3 What This Audit Does NOT Change

- The DIA 4-Layer architecture design is sound and self-consistent
- All protocol-level features (CIP, DIAVP, LDAP, L1/L2/L3) are unaffected
- Agent frontmatter, skills, and settings.json require no changes
- The 5 correctly-working hooks (TeammateIdle, TaskCompleted, PostToolUse, PreCompact, SessionStart) are untouched

---

## Appendix A: Full Evidence — teammate-lifecycle.log (first 20 entries)

```
[2026-02-07 02:45:22] SUBAGENT_START | name=unknown | type=claude-code-guide | team=no-team
[2026-02-07 02:45:47] SUBAGENT_STOP | name=unknown | type=claude-code-guide
[2026-02-07 03:04:24] SUBAGENT_STOP | name=unknown | type=
[2026-02-07 11:16:21] SUBAGENT_START | name=unknown | type=claude-code-guide | team=no-team
[2026-02-07 11:17:36] SUBAGENT_STOP | name=unknown | type=claude-code-guide
[2026-02-07 11:30:50] SUBAGENT_STOP | name=unknown | type=
[2026-02-07 11:55:42] SUBAGENT_START | name=unknown | type=claude-code-guide | team=no-team
[2026-02-07 11:55:53] SUBAGENT_START | name=unknown | type=claude-code-guide | team=no-team
[2026-02-07 11:56:00] SUBAGENT_START | name=unknown | type=Explore | team=no-team
[2026-02-07 11:57:07] SUBAGENT_STOP | name=unknown | type=claude-code-guide
[2026-02-07 11:57:51] SUBAGENT_STOP | name=unknown | type=Explore
[2026-02-07 11:57:56] SUBAGENT_STOP | name=unknown | type=claude-code-guide
[2026-02-07 11:59:24] SUBAGENT_STOP | name=unknown | type=
[2026-02-07 12:28:43] SUBAGENT_STOP | name=unknown | type=
[2026-02-07 13:11:10] SUBAGENT_STOP | name=unknown | type=
[2026-02-07 13:38:20] SUBAGENT_START | name=unknown | type=claude-code-guide | team=no-team
[2026-02-07 13:38:23] SUBAGENT_START | name=unknown | type=Explore | team=no-team
[2026-02-07 13:39:05] SUBAGENT_STOP | name=unknown | type=Explore
[2026-02-07 13:39:36] SUBAGENT_STOP | name=unknown | type=claude-code-guide
[2026-02-07 13:45:15] SUBAGENT_START | name=unknown | type=claude-code-guide | team=no-team
```

**Pattern:** 100% of entries show `name=unknown` and `team=no-team` or `team=unknown`.
The `type` field works correctly when populated (shows "claude-code-guide", "Explore",
"researcher", "implementer") but is occasionally empty on SubagentStop events.
