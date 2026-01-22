#!/bin/bash
# Notification Hook
# Surfaces ODA events for user awareness
#
# Environment variables used:
#   NOTIFICATION_TYPE - Type of notification (info, warn, error, success)
#   NOTIFICATION_MESSAGE - The notification message
#   NOTIFICATION_SOURCE - Source component of the notification
#
# Exit codes:
#   0 - Always succeeds

set -euo pipefail

NOTIFICATION_TYPE="${NOTIFICATION_TYPE:-info}"
NOTIFICATION_MESSAGE="${NOTIFICATION_MESSAGE:-}"
NOTIFICATION_SOURCE="${NOTIFICATION_SOURCE:-system}"
TIMESTAMP=$(date -Iseconds)

# Ensure log directory exists
mkdir -p .agent/logs

# Define notification level prefixes for display
declare -A LEVEL_PREFIX
LEVEL_PREFIX["info"]="[INFO]"
LEVEL_PREFIX["warn"]="[WARN]"
LEVEL_PREFIX["error"]="[ERROR]"
LEVEL_PREFIX["success"]="[OK]"

PREFIX="${LEVEL_PREFIX[$NOTIFICATION_TYPE]:-[INFO]}"

# Log notification to dedicated notifications log
echo "$TIMESTAMP | $NOTIFICATION_TYPE | $NOTIFICATION_SOURCE | $NOTIFICATION_MESSAGE" >> .agent/logs/oda_notifications.log

# For important notifications, also echo to stderr for visibility
case "$NOTIFICATION_TYPE" in
  "error")
    echo "$PREFIX $NOTIFICATION_MESSAGE" >&2
    ;;
  "warn")
    echo "$PREFIX $NOTIFICATION_MESSAGE" >&2
    ;;
  "success")
    echo "$PREFIX $NOTIFICATION_MESSAGE"
    ;;
  *)
    # Info level - only log, don't output
    ;;
esac

exit 0
