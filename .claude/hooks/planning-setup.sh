#!/usr/bin/env bash
# ============================================================================
# Planning Setup Hook - Gate 3a: Workload Inheritance + Research Integrity
# Version: 1.0.0
# ============================================================================
#
# Triggered by: /planning skill Setup hook (before execution)
# Purpose: Inherit workload from research, verify research artifact integrity
# Exit Codes: 0 = proceed, 1 = abort
#
# Functions Used:
#   - ensure_active_workload("inherit") : Inherit existing workload
#   - verify_upstream_hash("research")  : Verify research artifact unchanged
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
    echo "[${timestamp}] PLANNING_SETUP [${level}] ${message}" >> "$VALIDATION_GATES_LOG"
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    echo "🔍 Running Gate 3a: Workload Inheritance (Planning)"
    echo "====================================================="
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
            echo "❌ No active workload found for planning"
            echo ""
            echo "Please run /clarify → /research first, or specify --workload=<slug>"
            log_gate "ERROR" "No active workload for planning"
            exit 1
            ;;
        WORKLOAD_ORPHANED:*)
            local slug="${workload_result#WORKLOAD_ORPHANED:}"
            echo "❌ Orphaned workload: $slug (directory missing)"
            echo ""
            echo "Please run /clarify to start a new pipeline"
            log_gate "ERROR" "Orphaned workload: $slug"
            exit 1
            ;;
        *)
            if [[ $workload_exit_code -ne 0 ]]; then
                echo "❌ Workload error: $workload_result"
                log_gate "ERROR" "Workload error: $workload_result"
                exit 1
            fi
            echo "ℹ️  Workload result: $workload_result"
            log_gate "INFO" "Workload result: $workload_result"
            ;;
    esac
    echo ""

    # Step 2: Verify research artifact integrity
    echo "Step 2: Verifying research artifact integrity..."

    local hash_result
    hash_result=$(verify_upstream_hash "research" 2>&1)
    local hash_exit_code=$?

    case "$hash_result" in
        *HASH_VERIFIED:*)
            echo "✅ Research artifact integrity verified"
            log_gate "INFO" "Research hash verified"
            ;;
        *HASH_MISSING:*)
            echo "⚠️  No stored hash for research phase (backward compatibility)"
            echo "   Proceeding without integrity verification"
            log_gate "WARN" "No research hash stored"
            ;;
        *HASH_MISMATCH:*)
            if [[ "$WORKLOAD_STRICT_MODE" == "true" ]]; then
                echo "❌ Research artifact has been modified since last run"
                echo ""
                echo "Re-run /research to update the artifact and hash"
                log_gate "ERROR" "Research hash mismatch (strict mode)"
                exit 1
            else
                echo "⚠️  Research artifact modified (warning only)"
                echo "   Set WORKLOAD_STRICT_MODE=true to enforce integrity"
                log_gate "WARN" "Research hash mismatch (non-strict)"
            fi
            ;;
        *HASH_ARTIFACT_MISSING:*)
            echo "⚠️  Research artifact file not found"
            echo "   Consider running /research first"
            log_gate "WARN" "Research artifact missing"
            ;;
        *)
            echo "ℹ️  Hash verification: $hash_result"
            log_gate "INFO" "Hash result: $hash_result"
            ;;
    esac
    echo ""

    echo "✅ Gate 3a PASSED - Ready for /planning"
    echo ""

    exit 0
}

# Run main
main "$@"
