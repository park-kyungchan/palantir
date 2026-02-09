# Current Hook Code Reference (All 8 Hooks)

Captured at: 2026-02-08, pre-COA-7 fix

## 1. on-subagent-start.sh (46 lines) — BROKEN (ISSUE-001)

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

## 2. on-subagent-stop.sh (48 lines) — BROKEN (ISSUE-001 + ISSUE-003)

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

## 3. on-tool-failure.sh (28 lines) — BROKEN (ISSUE-002)

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

## 4. on-teammate-idle.sh (46 lines) — OK

```bash
#!/bin/bash
# Hook: TeammateIdle — Layer 4 Speed Bump
# Validates L1/L2 output files exist before allowing teammate to go idle.
# Exit 2 blocks idle and sends stderr as feedback to teammate.

INPUT=$(cat)

TEAMMATE_NAME=$(echo "$INPUT" | jq -r '.teammate_name // empty' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.team_name // empty' 2>/dev/null)

# Skip validation for non-team sessions
if [ -z "$TEAM_NAME" ]; then
  exit 0
fi

TEAM_DIR="/home/palantir/.agent/teams/$TEAM_NAME"

# Skip if team directory doesn't exist yet (early setup)
if [ ! -d "$TEAM_DIR" ]; then
  exit 0
fi

# Search for L1 and L2 files under team directory for this teammate
L1_FILE=$(ls "$TEAM_DIR"/phase-*/"$TEAMMATE_NAME"/L1-index.yaml 2>/dev/null | head -1)
L2_FILE=$(ls "$TEAM_DIR"/phase-*/"$TEAMMATE_NAME"/L2-summary.md 2>/dev/null | head -1)

MISSING=""

if [ -z "$L1_FILE" ] || [ ! -s "$L1_FILE" ] || [ "$(wc -c < "$L1_FILE" 2>/dev/null)" -lt 50 ]; then
  MISSING="L1-index.yaml (>=50 bytes)"
fi

if [ -z "$L2_FILE" ] || [ ! -s "$L2_FILE" ] || [ "$(wc -c < "$L2_FILE" 2>/dev/null)" -lt 100 ]; then
  if [ -n "$MISSING" ]; then
    MISSING="$MISSING, L2-summary.md (>=100 bytes)"
  else
    MISSING="L2-summary.md (>=100 bytes)"
  fi
fi

if [ -n "$MISSING" ]; then
  echo "Missing output files for $TEAMMATE_NAME: $MISSING. Write L1-index.yaml and L2-summary.md under .agent/teams/$TEAM_NAME/ before going idle." >&2
  exit 2
fi

exit 0
```

## 5. on-task-completed.sh (51 lines) — OK

```bash
#!/bin/bash
# Hook: TaskCompleted — Layer 4 Speed Bump
# Validates L1/L2 output files exist before allowing task completion.
# Exit 2 blocks completion and sends stderr as feedback to teammate.

INPUT=$(cat)

TEAMMATE_NAME=$(echo "$INPUT" | jq -r '.teammate_name // empty' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.team_name // empty' 2>/dev/null)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject // "unknown"' 2>/dev/null)

# Skip for non-team tasks
if [ -z "$TEAM_NAME" ]; then
  exit 0
fi

# Skip for Lead tasks (Lead has no L1/L2 obligation)
if [ -z "$TEAMMATE_NAME" ]; then
  exit 0
fi

TEAM_DIR="/home/palantir/.agent/teams/$TEAM_NAME"

# Skip if team directory doesn't exist
if [ ! -d "$TEAM_DIR" ]; then
  exit 0
fi

L1_FILE=$(ls "$TEAM_DIR"/phase-*/"$TEAMMATE_NAME"/L1-index.yaml 2>/dev/null | head -1)
L2_FILE=$(ls "$TEAM_DIR"/phase-*/"$TEAMMATE_NAME"/L2-summary.md 2>/dev/null | head -1)

MISSING=""

if [ -z "$L1_FILE" ] || [ ! -s "$L1_FILE" ] || [ "$(wc -c < "$L1_FILE" 2>/dev/null)" -lt 50 ]; then
  MISSING="L1-index.yaml (>=50 bytes)"
fi

if [ -z "$L2_FILE" ] || [ ! -s "$L2_FILE" ] || [ "$(wc -c < "$L2_FILE" 2>/dev/null)" -lt 100 ]; then
  if [ -n "$MISSING" ]; then
    MISSING="$MISSING, L2-summary.md (>=100 bytes)"
  else
    MISSING="L2-summary.md (>=100 bytes)"
  fi
fi

if [ -n "$MISSING" ]; then
  echo "Cannot complete task '$TASK_SUBJECT': missing output files for $TEAMMATE_NAME: $MISSING. Write L1-index.yaml and L2-summary.md before marking task as completed." >&2
  exit 2
fi

exit 0
```

## 6. on-task-update.sh (31 lines) — OK

```bash
#!/bin/bash
# Hook: PostToolUse(TaskUpdate) — Task state change logging + JSON output
# Fires after TaskUpdate is called (task completion, status changes)

INPUT=$(cat)

TASK_ID=$(echo "$INPUT" | jq -r '.tool_input.taskId // "unknown"' 2>/dev/null)
STATUS=$(echo "$INPUT" | jq -r '.tool_input.status // "unchanged"' 2>/dev/null)
SUBJECT=$(echo "$INPUT" | jq -r '.tool_input.subject // empty' 2>/dev/null)
OWNER=$(echo "$INPUT" | jq -r '.tool_input.owner // empty' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] TASK_UPDATE | id=$TASK_ID | status=$STATUS | owner=${OWNER:-unset}" >> "$LOG_DIR/task-lifecycle.log"

# Output structured JSON for machine parsing
if command -v jq &>/dev/null; then
  jq -n --arg id "$TASK_ID" --arg status "$STATUS" --arg subject "$SUBJECT" --arg owner "$OWNER" '{
    "hookSpecificOutput": {
      "hookEventName": "TaskUpdate",
      "taskId": $id,
      "status": $status,
      "subject": (if $subject != "" then $subject else null end),
      "owner": (if $owner != "" then $owner else null end)
    }
  }'
fi

exit 0
```

## 7. on-pre-compact.sh (40 lines) — OK

```bash
#!/bin/bash
# Hook: PreCompact — Context compaction state preservation
# Saves orchestration state before context loss for DIA recovery

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] PRE_COMPACT | Saving orchestration state before compaction" >> "$LOG_DIR/compact-events.log"

# Save current task list state snapshot
if ! command -v jq &>/dev/null; then
  echo "[$TIMESTAMP] PRE_COMPACT | WARNING: jq not available, skipping task snapshot" >> "$LOG_DIR/compact-events.log"
  exit 0
fi

# Use CLAUDE_CODE_TASK_LIST_ID if available, otherwise find most recent
if [ -n "${CLAUDE_CODE_TASK_LIST_ID:-}" ]; then
  TASK_DIR="/home/palantir/.claude/tasks/$CLAUDE_CODE_TASK_LIST_ID/"
else
  TASK_DIR=$(ls -td /home/palantir/.claude/tasks/*/ 2>/dev/null | head -1)
fi
if [ -n "$TASK_DIR" ]; then
  SNAPSHOT_FILE="$LOG_DIR/pre-compact-tasks-$(date '+%s').json"
  echo "[" > "$SNAPSHOT_FILE"
  first=true
  for f in "$TASK_DIR"*.json; do
    [ -f "$f" ] || continue
    if [ "$first" = true ]; then
      first=false
    else
      echo "," >> "$SNAPSHOT_FILE"
    fi
    cat "$f" >> "$SNAPSHOT_FILE"
  done
  echo "]" >> "$SNAPSHOT_FILE"
  echo "[$TIMESTAMP] PRE_COMPACT | Task snapshot saved: $SNAPSHOT_FILE" >> "$LOG_DIR/compact-events.log"
fi

exit 0
```

## 8. on-session-compact.sh (25 lines) — OK

```bash
#!/bin/bash
# Hook: SessionStart(compact) — Auto-compact recovery notification
# DIA Enforcement: Lead must re-inject context to all active teammates
# Output: JSON with additionalContext for Claude to consume

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — DIA re-injection required" >> "$LOG_DIR/compact-events.log"

# Output structured JSON for Claude to consume
if command -v jq &>/dev/null; then
  jq -n '{
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": "[DIA-RECOVERY] Context was compacted. As Lead: 1) Read orchestration-plan.md 2) Read Shared Task List 3) Send [DIRECTIVE]+[INJECTION] with latest GC to each active teammate 4) Wait for [STATUS] CONTEXT_RECEIVED before proceeding."
    }
  }'
else
  # Fallback: plain JSON without jq
  echo '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[DIA-RECOVERY] Context was compacted. As Lead: 1) Read orchestration-plan.md 2) Read Shared Task List 3) Send [DIRECTIVE]+[INJECTION] with latest GC to each active teammate 4) Wait for [STATUS] CONTEXT_RECEIVED before proceeding."}}'
fi

exit 0
```
