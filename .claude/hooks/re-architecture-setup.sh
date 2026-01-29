#!/usr/bin/env bash
# ============================================================================
# Re-Architecture Setup Hook - Gate 0: Workload Hybrid Mode
# Version: 1.0.0
# ============================================================================
#
# Triggered by: /re-architecture skill Setup hook
# Purpose: Initialize or resume session, handle workload context
# Exit Codes: 0 = proceed, 1 = abort
#
# Modes:
#   - New session: Create workload OR inherit existing
#   - Resume (--resume <slug>): Inherit specific workload
#
# Functions Used:
#   - detect_workload_staleness()    : Check if existing workload is stale
#   - ensure_active_workload(mode)   : Create/inherit/require workload
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
    echo "WARNING: workload-init.sh not found" >&2
fi

# Source validation-feedback-loop module (P4/P5/P6 integration - V2.0.0)
if [[ -f "${WORKSPACE_ROOT}/.claude/skills/shared/validation-feedback-loop.sh" ]]; then
    source "${WORKSPACE_ROOT}/.claude/skills/shared/validation-feedback-loop.sh"
    VALIDATION_FEEDBACK_AVAILABLE=true
else
    echo "WARNING: validation-feedback-loop.sh not found (P4/P5/P6 degraded)" >&2
    VALIDATION_FEEDBACK_AVAILABLE=false
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
    echo "[${timestamp}] RE_ARCH_SETUP [${level}] ${message}" >> "$VALIDATION_GATES_LOG"
}

# ============================================================================
# ARGUMENT PARSING
# ============================================================================
parse_arguments() {
    RESUME_MODE=false
    RESUME_SLUG=""
    RE_ARCH_TOPIC="re-architecture"

    # Parse from SKILL_ARGUMENTS environment variable
    local args="${SKILL_ARGUMENTS:-$*}"

    # Check for --resume flag
    if [[ "$args" == *"--resume"* ]]; then
        RESUME_MODE=true
        # Extract slug after --resume
        RESUME_SLUG=$(echo "$args" | grep -oP '(?<=--resume\s)[^\s]+' || echo "")
    fi

    # Extract topic (path to analyze) - first non-flag argument
    local topic
    topic=$(echo "$args" | sed 's/--resume\s*[^\s]*//g' | sed 's/--[a-zA-Z-]*//g' | xargs | head -c 50)
    [[ -n "$topic" ]] && RE_ARCH_TOPIC="$topic"
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    echo "🔍 Running Gate 0: Workload Initialization (Re-Architecture)"
    echo "=============================================================="
    echo ""

    parse_arguments "$@"

    # Show mode
    if [[ "$RESUME_MODE" == "true" ]]; then
        echo "ℹ️  Resume mode requested (--resume ${RESUME_SLUG:-<missing>})"
        if [[ -z "$RESUME_SLUG" ]]; then
            echo "❌ Resume mode requires a slug: --resume <workload-slug>"
            log_gate "ERROR" "Resume mode missing slug"
            exit 1
        fi
    fi
    echo ""

    # ========================================================================
    # RESUME MODE: Inherit specific workload
    # ========================================================================
    if [[ "$RESUME_MODE" == "true" && -n "$RESUME_SLUG" ]]; then
        echo "Step 1: Resuming session: $RESUME_SLUG"

        if ! type ensure_active_workload &>/dev/null; then
            echo "⚠️  Workload functions not available"
            log_gate "WARN" "Workload functions not available for resume"
            echo ""
            echo "✅ Gate 0 PASSED (degraded) - Continuing without workload context"
            exit 0
        fi

        # Set WORKLOAD_SLUG for ensure_active_workload to use
        export WORKLOAD_SLUG="$RESUME_SLUG"
        local workload_result
        workload_result=$(ensure_active_workload "inherit" 2>&1)

        case "$workload_result" in
            WORKLOAD_SET:*|WORKLOAD_INHERITED:*)
                local slug="${workload_result#*:}"
                echo "✅ Resumed session: $slug"
                log_gate "INFO" "Resumed re-architecture session: $slug"
                echo ""
                echo "📁 Workload Directory: .agent/prompts/${slug}/"
                ;;
            WORKLOAD_MISSING*|WORKLOAD_ORPHANED:*)
                echo "❌ Workload not found: $RESUME_SLUG"
                echo "   Check that the workload directory exists at:"
                echo "   .agent/prompts/${RESUME_SLUG}/"
                log_gate "ERROR" "Resume failed - workload not found: $RESUME_SLUG"
                exit 1
                ;;
            *)
                echo "⚠️  Resume warning: $workload_result"
                log_gate "WARN" "Resume unexpected result: $workload_result"
                ;;
        esac

        echo ""
        echo "✅ Gate 0 PASSED - Ready for /re-architecture (resume mode)"
        exit 0
    fi

    # ========================================================================
    # HYBRID MODE: Inherit if fresh, create if stale/missing
    # ========================================================================
    echo "Step 1: Checking existing workload..."

    if ! type detect_workload_staleness &>/dev/null; then
        echo "ℹ️  Workload validation not available (proceeding without context)"
        log_gate "INFO" "Workload functions not available"
        echo ""
        echo "✅ Gate 0 PASSED (degraded) - Continuing without workload context"
        exit 0
    fi

    local staleness
    staleness=$(detect_workload_staleness 2>&1 || echo "NO_ACTIVE_WORKLOAD")

    case "$staleness" in
        WORKLOAD_FRESH:*)
            local fresh_slug="${staleness#WORKLOAD_FRESH:}"
            echo "✅ Fresh workload found: $fresh_slug"
            echo "   Will use existing context"
            log_gate "INFO" "Using fresh workload: $fresh_slug"

            # Inherit the fresh workload
            local workload_result
            workload_result=$(ensure_active_workload "inherit" 2>&1)

            case "$workload_result" in
                WORKLOAD_INHERITED:*|WORKLOAD_SET:*)
                    local slug="${workload_result#*:}"
                    echo ""
                    echo "📁 Workload Directory: .agent/prompts/${slug}/"
                    ;;
                *)
                    echo "ℹ️  Workload result: $workload_result"
                    ;;
            esac
            ;;

        WORKLOAD_STALE:*)
            local stale_info="${staleness#WORKLOAD_STALE:}"
            echo "⚠️  Previous workload is stale: $stale_info"
            echo "   Creating new workload for this re-architecture session"
            log_gate "WARN" "Stale workload detected: $stale_info"

            # Create new workload
            export TOPIC="$RE_ARCH_TOPIC"
            local create_result
            create_result=$(ensure_active_workload "create" 2>&1)

            case "$create_result" in
                WORKLOAD_CREATED:*)
                    local new_slug="${create_result#WORKLOAD_CREATED:}"
                    echo "✅ New workload created: $new_slug"
                    log_gate "INFO" "Created workload: $new_slug"
                    echo ""
                    echo "📁 Workload Directory: .agent/prompts/${new_slug}/"
                    ;;
                *)
                    echo "⚠️  Could not create workload: $create_result"
                    log_gate "WARN" "Failed to create workload: $create_result"
                    ;;
            esac
            ;;

        WORKLOAD_ORPHANED:*)
            local orphan_slug="${staleness#WORKLOAD_ORPHANED:}"
            echo "⚠️  Orphaned workload detected: $orphan_slug"
            echo "   Creating new workload for this re-architecture session"
            log_gate "WARN" "Orphaned workload: $orphan_slug"

            # Create new workload
            export TOPIC="$RE_ARCH_TOPIC"
            local create_result
            create_result=$(ensure_active_workload "create" 2>&1)

            case "$create_result" in
                WORKLOAD_CREATED:*)
                    local new_slug="${create_result#WORKLOAD_CREATED:}"
                    echo "✅ New workload created: $new_slug"
                    log_gate "INFO" "Created workload: $new_slug"
                    echo ""
                    echo "📁 Workload Directory: .agent/prompts/${new_slug}/"
                    ;;
                *)
                    echo "⚠️  Could not create workload: $create_result"
                    log_gate "WARN" "Failed to create workload: $create_result"
                    ;;
            esac
            ;;

        NO_ACTIVE_WORKLOAD|WORKLOAD_MISSING*)
            echo "ℹ️  No active workload - creating new workload"
            log_gate "INFO" "No active workload, creating new"

            # Create new workload
            export TOPIC="$RE_ARCH_TOPIC"
            local create_result
            create_result=$(ensure_active_workload "create" 2>&1)

            case "$create_result" in
                WORKLOAD_CREATED:*)
                    local new_slug="${create_result#WORKLOAD_CREATED:}"
                    echo "✅ New workload created: $new_slug"
                    log_gate "INFO" "Created workload: $new_slug"
                    echo ""
                    echo "📁 Workload Directory: .agent/prompts/${new_slug}/"
                    ;;
                *)
                    echo "⚠️  Could not create workload: $create_result"
                    log_gate "WARN" "Failed to create workload: $create_result"
                    echo "   Re-architecture will proceed without workload context"
                    ;;
            esac
            ;;

        *)
            echo "ℹ️  Staleness check: $staleness"
            log_gate "INFO" "Staleness result: $staleness"
            ;;
    esac

    echo ""
    echo "✅ Gate 0 PASSED - Ready for /re-architecture"
    exit 0
}

# Run main
main "$@"
