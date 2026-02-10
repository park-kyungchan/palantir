#!/bin/bash
# Hook: PostToolUse — RTD event capture for observability
# Captures ALL tool calls from ALL sessions as JSONL events.
# Async mode (settings.json) — zero latency impact on agentic loop.
# Any error → exit 0 (never block pipeline). AD-28.

set -e
trap 'exit 0' ERR

INPUT=$(cat)

# Require jq
command -v jq &>/dev/null || exit 0

# Parse common fields from hook input
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null) || exit 0
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
TOOL_USE_ID=$(echo "$INPUT" | jq -r '.tool_use_id // empty' 2>/dev/null) || exit 0

[ -z "$SESSION_ID" ] && exit 0
[ -z "$TOOL_NAME" ] && exit 0

# Determine project slug from .current-project
OBS_BASE="/home/palantir/.agent/observability"
PROJECT_FILE="$OBS_BASE/.current-project"
SLUG="default"
if [ -f "$PROJECT_FILE" ]; then
  SLUG=$(head -1 "$PROJECT_FILE" 2>/dev/null)
  [ -z "$SLUG" ] && SLUG="default"
fi

OBS_DIR="$OBS_BASE/$SLUG"
EVENTS_DIR="$OBS_DIR/events"
mkdir -p "$EVENTS_DIR"

# Resolve agent name from session registry
AGENT="lead"
REGISTRY="$OBS_DIR/session-registry.json"
if [ -f "$REGISTRY" ]; then
  RESOLVED=$(jq -r --arg sid "$SESSION_ID" '.[$sid].name // empty' "$REGISTRY" 2>/dev/null)
  if [ -n "$RESOLVED" ]; then
    AGENT="$RESOLVED"
  else
    # Not in registry = likely Lead (Lead's session not registered via SubagentStart)
    AGENT="lead"
  fi
fi

# Read current DP from signal file (best-effort, AD-24)
DP="null"
DP_FILE="$OBS_DIR/current-dp.txt"
if [ -f "$DP_FILE" ]; then
  DP_VAL=$(head -1 "$DP_FILE" 2>/dev/null)
  [ -n "$DP_VAL" ] && DP="\"$DP_VAL\""
fi

# Build tool-specific input_summary and output_summary
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}' 2>/dev/null) || TOOL_INPUT="{}"
TOOL_RESPONSE=$(echo "$INPUT" | jq -c '.tool_response // {}' 2>/dev/null) || TOOL_RESPONSE="{}"

case "$TOOL_NAME" in
  Write)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      file_path: .file_path,
      content_lines: (.content | split("\n") | length),
      content_bytes: (.content | length)
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY='{"success":true}'
    ;;
  Edit)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      file_path: .file_path,
      old_preview: (.old_string | .[0:80]),
      new_preview: (.new_string | .[0:80]),
      replace_all: (.replace_all // false)
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY='{"success":true}'
    ;;
  Read)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      file_path: .file_path,
      offset: .offset,
      limit: .limit
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      lines: (if type == "string" then (split("\n") | length) else 0 end)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"lines":0}'
    ;;
  Bash)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      command: (.command | .[0:200]),
      description: (.description | .[0:100])
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      exit_code: (.exit_code // 0)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"exit_code":0}'
    ;;
  Glob)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      pattern: .pattern,
      path: .path
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      count: (if type == "array" then length elif type == "string" then (split("\n") | length) else 0 end)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"count":0}'
    ;;
  Grep)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      pattern: .pattern,
      path: .path,
      glob: .glob
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      count: (if type == "array" then length elif type == "string" then (split("\n") | length) else 0 end)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"count":0}'
    ;;
  Task)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      description: (.description | .[0:100]),
      subagent_type: .subagent_type
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY='{"status":"ok"}'
    ;;
  *)
    # Generic: first 3 keys from tool_input
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c 'to_entries | .[0:3] | from_entries' 2>/dev/null) || INPUT_SUMMARY='{}'
    OUTPUT_SUMMARY='{"status":"ok"}'
    ;;
esac

# Construct JSONL event and append
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
EVENT_FILE="$EVENTS_DIR/${SESSION_ID}.jsonl"

jq -n -c \
  --arg ts "$TIMESTAMP" \
  --arg sid "$SESSION_ID" \
  --arg agent "$AGENT" \
  --arg tool "$TOOL_NAME" \
  --arg tid "$TOOL_USE_ID" \
  --argjson input_summary "$INPUT_SUMMARY" \
  --argjson output_summary "$OUTPUT_SUMMARY" \
  --argjson dp "$DP" \
  '{ts: $ts, sid: $sid, agent: $agent, tool: $tool, tid: $tid, input_summary: $input_summary, output_summary: $output_summary, dp: $dp}' \
  >> "$EVENT_FILE" 2>/dev/null

exit 0
