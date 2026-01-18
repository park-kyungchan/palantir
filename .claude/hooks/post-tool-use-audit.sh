#!/bin/bash
# =============================================================================
# post-tool-use-audit.sh - PostToolUse Audit Logging Hook
# =============================================================================
# Logs tool name and timestamp to audit log after tool execution.
# Part of the ODA Workspace Hook Infrastructure for governance compliance.
#
# Exit codes:
#   0 - Success (always, to not block tool completion)
#
# Log location: .agent/logs/tool_audit.log
# =============================================================================

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.agent/logs/tool_audit.log"
MAX_LOG_SIZE=10485760  # 10MB max log size

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Rotate log if too large
if [ -f "$LOG_FILE" ] && [ "$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)" -gt "$MAX_LOG_SIZE" ]; then
    mv "$LOG_FILE" "${LOG_FILE}.1"
fi

# Parse input (tool result comes from stdin as JSON)
INPUT=$(cat)
# Extract fields using python (jq may not be available)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
TOOL_STATUS=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','completed'))" 2>/dev/null || echo "completed")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log audit entry
echo "[$TIMESTAMP] Tool: $TOOL_NAME | Status: $TOOL_STATUS" >> "$LOG_FILE"

exit 0
