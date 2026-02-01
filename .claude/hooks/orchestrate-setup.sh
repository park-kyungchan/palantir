#!/usr/bin/env bash
# ============================================================================
# Orchestrate Setup Hook - Gate 4a: Workload Inheritance + Planning Integrity
# Version: 1.0.0
# ============================================================================
#
# Triggered by: /orchestrate skill Setup hook (before execution)
# Purpose: Inherit workload, verify planning artifact integrity
# Exit Codes: 0 = proceed, 1 = abort
#
# Functions Used:
#   - ensure_active_workload("inherit") : Inherit existing workload
#   - verify_upstream_hash("planning")  : Verify planning artifact unchanged
#
# Note: This hook does NOT block on planning hash mismatch by default
#       (orchestrate may be called independently for ad-hoc task decomposition)
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
    echo "[${timestamp}] ORCHESTRATE_SETUP [${level}] ${message}" >> "$VALIDATION_GATES_LOG"
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    echo "🔍 Running Gate 4a: Workload Inheritance (Orchestrate)"
    echo "========================================================"
    echo ""

    # Step 1: Inherit workload
    echo "Step 1: Inheriting active workload..."

    local workload_result
    workload_result=$(ensure_active_workload "inherit" 2>&1)
    local workload_exit_code=$?

    case "$workload_result" in
        WORKLOAD_INHERITED:*)
            local slug="${workload_result#WORKLOAD_INHERITED:}"
            echo "✅ Workload inherited: $slug"
            log_gate "INFO" "Inherited workload: $slug"
            ;;
        WORKLOAD_SET:*)
            local slug="${workload_result#WORKLOAD_SET:}"
            echo "✅ Workload set from WORKLOAD_SLUG: $slug"
            log_gate "INFO" "Set workload: $slug"
            ;;
        WORKLOAD_MISSING*)
            echo "⚠️  No active workload found"
            echo ""
            echo "Note: /orchestrate can work without an active workload"
            echo "      (standalone task decomposition mode)"
            echo ""
            echo "For full pipeline, run /clarify → /research → /planning first"
            log_gate "WARN" "No active workload (standalone mode)"
            # Don't exit - allow standalone orchestration
            ;;
        WORKLOAD_ORPHANED:*)
            local slug="${workload_result#WORKLOAD_ORPHANED:}"
            echo "⚠️  Orphaned workload: $slug (directory missing)"
            echo "   Proceeding in standalone mode"
            log_gate "WARN" "Orphaned workload: $slug"
            # Don't exit - allow proceeding
            ;;
        *)
            if [[ $workload_exit_code -ne 0 ]]; then
                echo "⚠️  Workload warning: $workload_result"
                log_gate "WARN" "Workload issue: $workload_result"
                # Don't exit for orchestrate - more lenient
            else
                echo "ℹ️  Workload result: $workload_result"
                log_gate "INFO" "Workload result: $workload_result"
            fi
            ;;
    esac
    echo ""

    # Step 2: Verify planning artifact integrity (optional - warn only)
    echo "Step 2: Checking planning artifact integrity..."

    local hash_result
    hash_result=$(verify_upstream_hash "planning" 2>&1)

    case "$hash_result" in
        *HASH_VERIFIED:*)
            echo "✅ Planning artifact integrity verified"
            log_gate "INFO" "Planning hash verified"
            ;;
        *HASH_MISSING:*)
            echo "ℹ️  No stored hash for planning phase"
            echo "   (Normal for standalone orchestration)"
            log_gate "INFO" "No planning hash (standalone mode)"
            ;;
        *HASH_MISMATCH:*)
            echo "⚠️  Planning artifact has been modified"
            echo "   Proceeding with caution - verify plan is up-to-date"
            log_gate "WARN" "Planning hash mismatch"
            # Don't exit - orchestrate is more lenient
            ;;
        *HASH_ARTIFACT_MISSING:*)
            echo "ℹ️  Planning artifact not found"
            echo "   (Normal for standalone orchestration)"
            log_gate "INFO" "No planning artifact"
            ;;
        *)
            echo "ℹ️  Hash check: $hash_result"
            log_gate "INFO" "Hash result: $hash_result"
            ;;
    esac
    echo ""

    echo "✅ Gate 4a PASSED - Ready for /orchestrate"
    echo ""

    exit 0
}

# Run main
main "$@"
