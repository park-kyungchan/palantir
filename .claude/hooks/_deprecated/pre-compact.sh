#!/bin/bash
# ==============================================================================
# Claude Code - PreCompact Hook
# ==============================================================================
# Saves context state before Auto-Compact for session restoration.
# Preserves todos, plans, session health, and creates compact summary.
#
# Matcher: PreCompact event
# Exit Codes:
#   0 - Success
# ==============================================================================

# Don't exit on error - graceful handling is critical for PreCompact
set +e

# Configuration
CONTEXT_DIR="${HOME}/.agent/compact-state"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${HOME}/.agent/logs/pre-compact.log"

# Ensure directories exist
mkdir -p "$CONTEXT_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "PreCompact hook triggered"

# ==============================================================================
# 1. Save current todos state
# ==============================================================================
if [ -d "${HOME}/.claude/todos" ]; then
    cp -r "${HOME}/.claude/todos" "$CONTEXT_DIR/todos_${TIMESTAMP}" 2>/dev/null || true
    log "Saved todos to $CONTEXT_DIR/todos_${TIMESTAMP}"
fi

# ==============================================================================
# 2. Save active plan files (modified since last compact)
# ==============================================================================
PLAN_DIR="${HOME}/.agent/plans"
if [ -d "$PLAN_DIR" ]; then
    # Find plans modified since last compact
    if [ -f "$CONTEXT_DIR/.last_compact" ]; then
        find "$PLAN_DIR" -name "*.md" -newer "$CONTEXT_DIR/.last_compact" \
            -exec cp {} "$CONTEXT_DIR/" \; 2>/dev/null || true
        log "Saved modified plan files"
    else
        # First time - copy all plans
        cp "$PLAN_DIR"/*.md "$CONTEXT_DIR/" 2>/dev/null || true
        log "Saved all plan files (first compact)"
    fi
fi

# ==============================================================================
# 3. Save session health state
# ==============================================================================
SESSION_HEALTH_STATE="${HOME}/.agent/tmp/session_health.json"
if [ -f "$SESSION_HEALTH_STATE" ]; then
    cp "$SESSION_HEALTH_STATE" "$CONTEXT_DIR/session_health_${TIMESTAMP}.json" 2>/dev/null || true
    log "Saved session health state"
fi

# ==============================================================================
# 4. Save protocol state (current stage)
# ==============================================================================
PROTOCOL_STATE="${HOME}/.agent/tmp/protocol_state.json"
if [ -f "$PROTOCOL_STATE" ]; then
    cp "$PROTOCOL_STATE" "$CONTEXT_DIR/protocol_state_${TIMESTAMP}.json" 2>/dev/null || true
    log "Saved protocol state"
fi

# ==============================================================================
# 5. Create compact summary for quick resume
# ==============================================================================
SUMMARY_FILE="$CONTEXT_DIR/compact_summary_${TIMESTAMP}.md"
cat > "$SUMMARY_FILE" << EOF
# Pre-Compact Summary
> Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
> Auto-Compact Safe: Read this file after context restoration

## Saved Files
- todos_${TIMESTAMP}/ (if present)
- session_health_${TIMESTAMP}.json (if present)
- protocol_state_${TIMESTAMP}.json (if present)
- Plan files from .agent/plans/

## Quick Resume Instructions
1. Read active plan file: \`.agent/plans/*.md\`
2. Check TodoWrite for task status
3. Continue from first PENDING task
4. Reference \`.claude/CLAUDE.md\` for governance

## Context at Compact Time
$(cat "$CONTEXT_DIR/compact_summary_"*.md 2>/dev/null | head -50 || echo "No previous summary")
EOF
log "Created compact summary"

# ==============================================================================
# 6. Update last compact marker
# ==============================================================================
touch "$CONTEXT_DIR/.last_compact"
log "Updated last compact marker"

# ==============================================================================
# 7. Cleanup old compact states (keep last 5)
# ==============================================================================
cleanup_old_files() {
    local pattern="$1"
    local keep_count="${2:-5}"
    local is_dir="${3:-false}"

    # Use absolute paths, avoid cd
    local files=$(ls -t "$CONTEXT_DIR"/$pattern 2>/dev/null | tail -n +$((keep_count + 1)))

    for file in $files; do
        if [ -n "$file" ]; then
            if [ "$is_dir" = "true" ]; then
                rm -rf "$file" 2>/dev/null || true
            else
                rm -f "$file" 2>/dev/null || true
            fi
        fi
    done
}

cleanup_old_files "compact_summary_*.md" 5 false
cleanup_old_files "todos_*" 5 true
cleanup_old_files "session_health_*.json" 5 false
cleanup_old_files "protocol_state_*.json" 5 false
log "Cleaned up old compact states"

# ==============================================================================
# Output
# ==============================================================================
echo "PreCompact: Context saved to $CONTEXT_DIR"
log "PreCompact hook completed successfully"

exit 0
