#!/bin/bash
# =============================================================================
# task-sync.sh - Task State Synchronization Utility
# =============================================================================
# Provides cross-session Task state visibility and change detection.
# Used by session hooks and can be called manually.
#
# Usage:
#   task-sync.sh status       - Show current Task List status
#   task-sync.sh changes      - Show recently changed Tasks
#   task-sync.sh watch        - Watch for Task changes (blocking)
#   task-sync.sh notify       - Send notification about pending Tasks
#
# Version: 1.0.0
# =============================================================================

set +e

#=============================================================================
# Configuration
#=============================================================================

TASK_DIR="${HOME}/.claude/tasks"
TASK_LIST_ID="${CLAUDE_CODE_TASK_LIST_ID:-}"
SYNC_STATE_FILE="${HOME}/.agent/tmp/task_sync_state.json"
NOTIFICATION_LOG="${HOME}/.agent/logs/task_notifications.log"

# Ensure directories exist
mkdir -p "$(dirname "$SYNC_STATE_FILE")" 2>/dev/null
mkdir -p "$(dirname "$NOTIFICATION_LOG")" 2>/dev/null

#=============================================================================
# JSON Helper
#=============================================================================

HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

json_get() {
    local field="$1"
    local file="$2"

    if [ ! -f "$file" ]; then
        echo ""
        return
    fi

    if $HAS_JQ; then
        jq -r "$field // empty" "$file" 2>/dev/null || echo ""
    else
        python3 -c "
import json
try:
    with open('$file') as f:
        data = json.load(f)
    keys = '$field'.lstrip('.').split('.')
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, '')
        else:
            val = ''
    print(val if val else '')
except:
    print('')
" 2>/dev/null || echo ""
    fi
}

#=============================================================================
# Commands
#=============================================================================

cmd_status() {
    echo "=== Task List Status ==="
    echo "Task List ID: ${TASK_LIST_ID:-'(not set)'}"
    echo "Task Directory: $TASK_DIR"
    echo ""

    if [ ! -d "$TASK_DIR" ]; then
        echo "No tasks found."
        return
    fi

    local pending=0
    local in_progress=0
    local completed=0
    local total=0

    for task_file in "$TASK_DIR"/*.json; do
        [ -f "$task_file" ] || continue
        total=$((total + 1))

        local status=$(json_get '.status' "$task_file")
        case "$status" in
            pending) pending=$((pending + 1)) ;;
            in_progress) in_progress=$((in_progress + 1)) ;;
            completed) completed=$((completed + 1)) ;;
        esac
    done

    echo "Total: $total | Pending: $pending | In Progress: $in_progress | Completed: $completed"
    echo ""

    # Show pending and in_progress tasks
    if [ $pending -gt 0 ] || [ $in_progress -gt 0 ]; then
        echo "=== Active Tasks ==="
        for task_file in "$TASK_DIR"/*.json; do
            [ -f "$task_file" ] || continue

            local status=$(json_get '.status' "$task_file")
            local subject=$(json_get '.subject' "$task_file")
            local owner=$(json_get '.owner' "$task_file")

            if [ "$status" = "pending" ] || [ "$status" = "in_progress" ]; then
                local owner_info=""
                [ -n "$owner" ] && owner_info=" (owner: $owner)"
                echo "[$status] $subject$owner_info"
            fi
        done
    fi
}

cmd_changes() {
    echo "=== Recently Changed Tasks (last 10 minutes) ==="

    if [ ! -d "$TASK_DIR" ]; then
        echo "No tasks found."
        return
    fi

    # Find tasks modified in the last 10 minutes
    local changed_files=$(find "$TASK_DIR" -name "*.json" -mmin -10 2>/dev/null)

    if [ -z "$changed_files" ]; then
        echo "No recent changes."
        return
    fi

    for task_file in $changed_files; do
        local status=$(json_get '.status' "$task_file")
        local subject=$(json_get '.subject' "$task_file")
        local mtime=$(stat -c %y "$task_file" 2>/dev/null | cut -d'.' -f1)

        echo "[$status] $subject"
        echo "    Modified: $mtime"
    done
}

cmd_watch() {
    echo "Watching for Task changes... (Ctrl+C to stop)"
    echo "Task Directory: $TASK_DIR"
    echo ""

    # Check if inotifywait is available
    if command -v inotifywait &> /dev/null; then
        inotifywait -m -e modify,create,delete "$TASK_DIR" 2>/dev/null | while read path action file; do
            if [[ "$file" == *.json ]]; then
                local timestamp=$(date '+%H:%M:%S')
                echo "[$timestamp] $action: $file"

                if [ "$action" = "MODIFY" ] || [ "$action" = "CREATE" ]; then
                    local status=$(json_get '.status' "$path$file")
                    local subject=$(json_get '.subject' "$path$file")
                    echo "    Status: $status | Subject: $subject"
                fi
            fi
        done
    else
        # Fallback: polling-based watch
        echo "(inotifywait not available, using polling)"

        local last_check=$(date +%s)

        while true; do
            sleep 5

            local changed_files=$(find "$TASK_DIR" -name "*.json" -newermt "@$last_check" 2>/dev/null)
            last_check=$(date +%s)

            for task_file in $changed_files; do
                local timestamp=$(date '+%H:%M:%S')
                local status=$(json_get '.status' "$task_file")
                local subject=$(json_get '.subject' "$task_file")
                local basename=$(basename "$task_file")

                echo "[$timestamp] MODIFIED: $basename"
                echo "    Status: $status | Subject: $subject"
            done
        done
    fi
}

cmd_notify() {
    # Generate notification message for pending tasks
    if [ ! -d "$TASK_DIR" ]; then
        return
    fi

    local pending_count=0
    local message=""

    for task_file in "$TASK_DIR"/*.json; do
        [ -f "$task_file" ] || continue

        local status=$(json_get '.status' "$task_file")

        if [ "$status" = "pending" ] || [ "$status" = "in_progress" ]; then
            pending_count=$((pending_count + 1))
            local subject=$(json_get '.subject' "$task_file")
            message="${message}- [$status] $subject\n"
        fi
    done

    if [ $pending_count -gt 0 ]; then
        local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

        # Log notification
        echo "[$timestamp] Pending tasks: $pending_count" >> "$NOTIFICATION_LOG"

        # Output notification
        echo "=== Task Notification ==="
        echo "You have $pending_count pending task(s):"
        echo -e "$message"
        echo "Use 'TaskList' to view all tasks."
    fi
}

#=============================================================================
# Main
#=============================================================================

case "${1:-status}" in
    status)   cmd_status ;;
    changes)  cmd_changes ;;
    watch)    cmd_watch ;;
    notify)   cmd_notify ;;
    *)
        echo "Usage: $0 {status|changes|watch|notify}"
        exit 1
        ;;
esac
