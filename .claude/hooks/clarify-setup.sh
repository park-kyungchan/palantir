#!/usr/bin/env bash
# ============================================================================
# Clarify Setup Hook - Gate 1: Workload Initialization
# Version: 1.0.0
# ============================================================================
#
# Triggered by: /clarify skill Setup hook (before execution)
# Purpose: Initialize new workload, check for stale workloads
# Exit Codes: 0 = proceed, 1 = abort
#
# Functions Used:
#   - detect_workload_staleness()  : Check if existing workload is stale
#   - ensure_active_workload("create") : Create new workload for clarify
#
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
VALIDATION_GATES_LOG=".agent/logs/validation_gates.log"

# Source workload-init module
if [[ -f "${WORKSPACE_ROOT}/.claude/skills/shared/workload-init.sh" ]]; then
    source "${WORKSPACE_ROOT}/.claude/skills/shared/workload-init.sh"
else
    echo "ERROR: workload-init.sh not found" >&2
    exit 1
fi

# ============================================================================
# LOGGING
# ============================================================================
log_gate() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date -Iseconds)

    mkdir -p "$(dirname "$VALIDATION_GATES_LOG")"
    echo "[${timestamp}] CLARIFY_SETUP [${level}] ${message}" >> "$VALIDATION_GATES_LOG"
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    echo "🔍 Running Gate 1: Workload Initialization (Clarify)"
    echo "======================================================"
    echo ""

    # Step 1: Check for stale workload
    echo "Step 1: Checking workload staleness..."
    local staleness_result
    staleness_result=$(detect_workload_staleness)

    case "$staleness_result" in
        WORKLOAD_STALE:*)
            local stale_info="${staleness_result#WORKLOAD_STALE:}"
            echo "⚠️  Previous workload is stale: $stale_info"
            echo "   Creating new workload for this clarify session"
            log_gate "WARN" "Stale workload detected: $stale_info"
            ;;
        WORKLOAD_ORPHANED:*)
            local orphan_slug="${staleness_result#WORKLOAD_ORPHANED:}"
            echo "⚠️  Orphaned workload detected: $orphan_slug"
            echo "   Creating new workload for this clarify session"
            log_gate "WARN" "Orphaned workload: $orphan_slug"
            ;;
        WORKLOAD_FRESH:*)
            local fresh_info="${staleness_result#WORKLOAD_FRESH:}"
            echo "ℹ️  Existing fresh workload: $fresh_info"
            echo "   /clarify will create a NEW workload (overwriting context)"
            log_gate "INFO" "Fresh workload exists: $fresh_info"
            ;;
        NO_ACTIVE_WORKLOAD)
            echo "ℹ️  No active workload (starting fresh)"
            log_gate "INFO" "No active workload"
            ;;
        *)
            echo "ℹ️  Staleness check: $staleness_result"
            log_gate "INFO" "Staleness result: $staleness_result"
            ;;
    esac
    echo ""

    # Step 2: Create new workload
    echo "Step 2: Creating new workload..."

    # Extract topic from skill arguments if available
    export TOPIC="${CLARIFY_TOPIC:-${1:-unnamed}}"

    local workload_result
    workload_result=$(ensure_active_workload "create")

    case "$workload_result" in
        WORKLOAD_CREATED:*)
            local new_slug="${workload_result#WORKLOAD_CREATED:}"
            echo "✅ New workload created: $new_slug"
            log_gate "INFO" "Created workload: $new_slug"
            ;;
        *)
            echo "❌ Unexpected result: $workload_result"
            log_gate "ERROR" "Unexpected result: $workload_result"
            exit 1
            ;;
    esac

    echo ""
    echo "✅ Gate 1 PASSED - Workload initialized for /clarify"
    echo ""

    exit 0
}

# Run main
main "$@"
