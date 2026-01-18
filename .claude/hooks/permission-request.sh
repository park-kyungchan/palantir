#!/bin/bash
# =============================================================================
# permission-request.sh - PermissionRequest Handling Hook
# =============================================================================
# Logs permission requests for audit and governance compliance.
# Part of the ODA Workspace Hook Infrastructure.
#
# Exit codes:
#   0 - Success (always, to allow permission flow to continue)
#
# Log location: .agent/logs/permission_requests.log
# =============================================================================

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.agent/logs/permission_requests.log"
MAX_LOG_SIZE=5242880  # 5MB max log size

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Rotate log if too large
if [ -f "$LOG_FILE" ] && [ "$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)" -gt "$MAX_LOG_SIZE" ]; then
    mv "$LOG_FILE" "${LOG_FILE}.1"
fi

# Parse input (permission request comes from stdin as JSON)
INPUT=$(cat)
# Extract fields using python (jq may not be available)
PERMISSION_TYPE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('permission_type','unknown'))" 2>/dev/null || echo "unknown")
RESOURCE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('resource','N/A'))" 2>/dev/null || echo "N/A")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log permission request
echo "[$TIMESTAMP] Permission: $PERMISSION_TYPE | Resource: $RESOURCE" >> "$LOG_FILE"

exit 0
