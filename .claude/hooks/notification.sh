#!/bin/bash
# =============================================================================
# notification.sh - Notification Hook
# =============================================================================
# Logs system notifications for audit and monitoring.
# Part of the ODA Workspace Hook Infrastructure.
#
# Exit codes:
#   0 - Success (always, to allow notification flow to continue)
#
# Log location: .agent/logs/notifications.log
# =============================================================================

set -euo pipefail

# Configuration
LOG_FILE="${HOME}/.agent/logs/notifications.log"
MAX_LOG_SIZE=5242880  # 5MB max log size

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Rotate log if too large
if [ -f "$LOG_FILE" ] && [ "$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)" -gt "$MAX_LOG_SIZE" ]; then
    mv "$LOG_FILE" "${LOG_FILE}.1"
fi

# Parse input (notification comes from stdin as JSON)
INPUT=$(cat)
# Extract fields using python (jq may not be available)
NOTIFICATION_TYPE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('type','info'))" 2>/dev/null || echo "info")
MESSAGE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','No message'))" 2>/dev/null || echo "No message")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log notification
echo "[$TIMESTAMP] Type: $NOTIFICATION_TYPE | Message: $MESSAGE" >> "$LOG_FILE"

exit 0
