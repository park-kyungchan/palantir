#!/bin/bash
# Hook: SessionStart(compact) — Auto-compact 후 context 복구 알림
# DIA Enforcement: Lead must re-inject context to all active teammates

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — DIA re-injection required" >> "$LOG_DIR/compact-events.log"

# Output context for Claude to consume
cat << 'EOF'
[DIA-RECOVERY] Context was compacted. As Lead, you MUST:
1. Read orchestration-plan.md to restore pipeline state
2. Read Shared Task List for current progress
3. Send [DIRECTIVE]+[INJECTION] with latest GC-v{N} to each active teammate
4. Wait for [STATUS] CONTEXT_RECEIVED from each teammate before proceeding
EOF

exit 0
