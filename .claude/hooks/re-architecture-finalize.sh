#!/bin/bash
# re-architecture-finalize.sh
# Stop hook for /re-architecture skill
# Purpose: Finalize analysis session and prepare handoff context

set -euo pipefail

LOG_DIR=".agent/logs"
LOG_FILE="${LOG_DIR}/re-architecture.log"
mkdir -p "$LOG_DIR"

# ============================================================================
# SOURCE WORKLOAD-INIT (for centralized hash management)
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKLOAD_INIT="${SCRIPT_DIR}/../skills/shared/workload-init.sh"
WORKLOAD_INIT_AVAILABLE=false

if [[ -f "$WORKLOAD_INIT" ]]; then
    # shellcheck source=../skills/shared/workload-init.sh
    source "$WORKLOAD_INIT"
    WORKLOAD_INIT_AVAILABLE=true
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== /re-architecture Stop Hook Started ==="

# Find most recent re-architecture log
LATEST_LOG=$(find .agent/prompts -name "re-architecture-log.yaml" -type f 2>/dev/null | head -1)

if [[ -z "$LATEST_LOG" ]]; then
    log "WARNING: No re-architecture log found"
    echo "⚠️ No active re-architecture session found"
    exit 0
fi

log "Processing log: $LATEST_LOG"

# Extract slug from path
SLUG=$(dirname "$LATEST_LOG" | xargs basename)
log "Session slug: $SLUG"

# Update metadata status to completed
if command -v yq &> /dev/null; then
    yq -i '.metadata.status = "completed"' "$LATEST_LOG"
    yq -i '.metadata.updated_at = now | strftime("%Y-%m-%dT%H:%M:%SZ")' "$LATEST_LOG"
    log "Updated metadata via yq"
else
    # Fallback: sed-based update
    sed -i 's/status: "in_progress"/status: "completed"/' "$LATEST_LOG"
    log "Updated metadata via sed"
fi

# Generate context hash for integrity
if command -v sha256sum &> /dev/null; then
    HASH=$(sha256sum "$LATEST_LOG" | cut -d' ' -f1)
    log "Context hash: $HASH"

    # Store hash via workload-init.sh (preferred) or direct yq (fallback)
    if [[ "$WORKLOAD_INIT_AVAILABLE" == "true" ]]; then
        if store_workload_hash "$HASH" "re-architecture" 2>/dev/null; then
            log "Stored hash via workload-init.sh (re-architecture_hash in _active_workload.yaml)"
        else
            log "WARNING: store_workload_hash failed, using fallback"
            if command -v yq &> /dev/null; then
                yq -i ".pipeline.context_hash = \"$HASH\"" "$LATEST_LOG"
                log "Stored hash via direct yq (fallback)"
            fi
        fi
    elif command -v yq &> /dev/null; then
        # Fallback: direct yq if workload-init.sh unavailable
        yq -i ".pipeline.context_hash = \"$HASH\"" "$LATEST_LOG"
        log "Stored hash via direct yq (workload-init.sh unavailable)"
    fi
fi

# Count statistics
ROUND_COUNT="0"
COMPONENT_COUNT="0"
FINDINGS_COUNT="0"
ISSUES_COUNT="0"

if command -v yq &> /dev/null; then
    ROUND_COUNT=$(yq '.rounds | length' "$LATEST_LOG" 2>/dev/null || echo "0")
    COMPONENT_COUNT=$(yq '.decomposition.components | length' "$LATEST_LOG" 2>/dev/null || echo "0")
    FINDINGS_COUNT=$(yq '[.component_feedback[].findings | length] | add // 0' "$LATEST_LOG" 2>/dev/null || echo "0")
    ISSUES_COUNT=$(yq '[.component_feedback[].issues | length] | add // 0' "$LATEST_LOG" 2>/dev/null || echo "0")
    log "Statistics: ${ROUND_COUNT} rounds, ${COMPONENT_COUNT} components, ${FINDINGS_COUNT} findings"

    # Update EFL metadata (V2.0.0)
    L2_ITERATIONS=$(yq '.efl_metadata.agent_delegation.phase_3a_l2_horizontal.iterations // 1' "$LATEST_LOG" 2>/dev/null || echo "1")
    L3_ITERATIONS=$(yq '.efl_metadata.agent_delegation.phase_3b_l3_vertical.iterations // 1' "$LATEST_LOG" 2>/dev/null || echo "1")
    REVIEW_APPROVED=$(yq '.efl_metadata.review_gate.approved // false' "$LATEST_LOG" 2>/dev/null || echo "false")

    # Ensure EFL metadata exists
    yq -i '.efl_metadata.version = "2.0.0"' "$LATEST_LOG" 2>/dev/null || true
    log "EFL metadata version set to 2.0.0"
fi

# Generate L1 summary (V2.0.0)
L1_SUMMARY=$(cat << EOF
# Re-Architecture L1 Summary

**Session:** ${SLUG}
**Status:** completed
**Components:** ${COMPONENT_COUNT}
**Findings:** ${FINDINGS_COUNT}
**Issues:** ${ISSUES_COUNT}

**Next:** /research --clarify-slug ${SLUG}
EOF
)

# Output summary
echo "✅ /re-architecture session finalized (V2.0.0)"
echo "   Session: $SLUG"
echo "   Log: $LATEST_LOG"
if [[ -n "${ROUND_COUNT:-}" ]]; then
    echo "   Rounds: $ROUND_COUNT"
    echo "   Components: $COMPONENT_COUNT"
    echo "   Findings: $FINDINGS_COUNT"
    echo "   Issues: $ISSUES_COUNT"
fi
echo ""
echo "📊 L1 Summary:"
echo "   Components analyzed: $COMPONENT_COUNT"
echo "   Findings documented: $FINDINGS_COUNT"
echo ""
echo "📋 Next step: /research --clarify-slug $SLUG"

log "=== /re-architecture Stop Hook Completed ==="
exit 0
