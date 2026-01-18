#!/bin/bash
# =============================================================================
# pre-tool-use-oda.sh - PreToolUse Hook for ODA Context Injection
# =============================================================================
# Provides brief ODA context reminder before tool execution (for debugging).
# Part of the ODA Workspace Hook Infrastructure.
#
# Exit codes:
#   0 - Allow tool use to proceed
#
# Output: JSON with {"continue": true}
# =============================================================================

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.agent/logs/pre-tool-use.log"
DEBUG="${ODA_DEBUG:-false}"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Parse input (tool name comes from stdin as JSON)
INPUT=$(cat)
# Extract tool_name using python (jq may not be available)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log if debug enabled
if [ "$DEBUG" = "true" ]; then
    echo "[$TIMESTAMP] PreToolUse: $TOOL_NAME" >> "$LOG_FILE"
fi

# Output JSON response - allow tool use to proceed
echo '{"continue": true}'

exit 0
