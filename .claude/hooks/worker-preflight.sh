#!/bin/bash
# ============================================================================
# Worker Preflight Hook - Gate 5: Pre-execution Validation
# Version: 1.0.0
# ============================================================================
#
# Triggered by: /worker skill Setup hook (before start)
# Purpose: Validate task readiness before worker execution
# Exit Codes: 0 = passed, 1 = failed, 2 = warning
#
# ============================================================================

set -euo pipefail

# Source validation gates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "${WORKSPACE_ROOT}/.claude/skills/shared/validation-gates.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

TASK_ID="${1:-}"
PROMPT_FILE="${2:-}"

# ============================================================================
# HELPER: Find prompt file for task
# ============================================================================

find_prompt_file() {
    local task_id="$1"

    # Search in pending directory
    for file in .agent/prompts/pending/*.yaml; do
        [[ -f "$file" ]] || continue
        if grep -q "nativeTaskId: \"${task_id}\"" "$file" 2>/dev/null || \
           grep -q "taskId: \"${task_id}\"" "$file" 2>/dev/null; then
            echo "$file"
            return 0
        fi
    done

    return 1
}

# ============================================================================
# HELPER: Check blockedBy status via task files
# ============================================================================

check_blockers_resolved() {
    local task_id="$1"
    local task_dir=".claude/tasks"

    # Find task file pattern
    for project_dir in "$task_dir"/*; do
        [[ -d "$project_dir" ]] || continue

        task_file="${project_dir}/${task_id}.json"
        if [[ -f "$task_file" ]]; then
            # Extract blockedBy array
            local blocked_by
            blocked_by=$(jq -r '.blockedBy[]?' "$task_file" 2>/dev/null || echo "")

            if [[ -z "$blocked_by" ]]; then
                # No blockers
                return 0
            fi

            # Check each blocker's status
            for blocker_id in $blocked_by; do
                blocker_file="${project_dir}/${blocker_id}.json"
                if [[ -f "$blocker_file" ]]; then
                    local blocker_status
                    blocker_status=$(jq -r '.status' "$blocker_file" 2>/dev/null || echo "pending")

                    if [[ "$blocker_status" != "completed" ]]; then
                        echo "Task #${blocker_id} (${blocker_status})"
                        return 1
                    fi
                fi
            done

            return 0
        fi
    done

    # No task file found, assume no blockers
    return 0
}

# ============================================================================
# MAIN
# ============================================================================

echo "🔍 Running Gate 5: Pre-execution Validation"
echo "=========================================="

# If no task ID provided, try to detect from context
if [[ -z "$TASK_ID" ]]; then
    # Check if there's a pending task being started
    # This is a placeholder - actual implementation depends on context passing
    echo "ℹ️  No specific task ID provided, running general validation"
fi

# Initialize result tracking
WARNINGS=()
ERRORS=()

# ============================================================================
# Check 1: BlockedBy Resolution
# ============================================================================

if [[ -n "$TASK_ID" ]]; then
    echo ""
    echo "📋 Checking task #${TASK_ID} blockers..."

    blocker_result=$(check_blockers_resolved "$TASK_ID" 2>&1)
    blocker_status=$?

    if [[ $blocker_status -ne 0 ]]; then
        ERRORS+=("Task is blocked by incomplete task(s): ${blocker_result}")
    else
        echo "   ✅ No active blockers"
    fi
fi

# ============================================================================
# Check 2: Prompt File Validation
# ============================================================================

if [[ -z "$PROMPT_FILE" && -n "$TASK_ID" ]]; then
    PROMPT_FILE=$(find_prompt_file "$TASK_ID" 2>/dev/null || echo "")
fi

if [[ -n "$PROMPT_FILE" ]]; then
    echo ""
    echo "📄 Validating prompt file: $PROMPT_FILE"

    # Run pre_execution_gate from validation-gates.sh
    GATE_RESULT=$(pre_execution_gate "$TASK_ID" "$PROMPT_FILE")

    GATE_STATUS=$(echo "$GATE_RESULT" | jq -r '.result' 2>/dev/null || echo "unknown")
    GATE_WARNINGS=$(echo "$GATE_RESULT" | jq -r '.warnings[]?' 2>/dev/null || echo "")
    GATE_ERRORS=$(echo "$GATE_RESULT" | jq -r '.errors[]?' 2>/dev/null || echo "")

    # Collect warnings and errors
    if [[ -n "$GATE_WARNINGS" ]]; then
        while IFS= read -r warning; do
            [[ -n "$warning" ]] && WARNINGS+=("$warning")
        done <<< "$GATE_WARNINGS"
    fi

    if [[ -n "$GATE_ERRORS" ]]; then
        while IFS= read -r error; do
            [[ -n "$error" ]] && ERRORS+=("$error")
        done <<< "$GATE_ERRORS"
    fi
else
    echo ""
    echo "ℹ️  No prompt file found (optional)"
fi

# ============================================================================
# Check 3: Target File Access (if prompt file exists)
# ============================================================================

if [[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" ]]; then
    echo ""
    echo "🔐 Checking target file access..."

    # Extract target files from prompt
    target_files=$(grep -E '^\s*-?\s*path:' "$PROMPT_FILE" 2>/dev/null | \
                   sed 's/.*path:\s*//' | tr -d '"' || echo "")

    if [[ -n "$target_files" ]]; then
        while IFS= read -r target_file; do
            target_file=$(echo "$target_file" | xargs)
            [[ -z "$target_file" ]] && continue

            full_path="${WORKSPACE_ROOT}/${target_file}"

            if [[ -f "$full_path" ]]; then
                if [[ ! -w "$full_path" ]]; then
                    ERRORS+=("Target file not writable: ${target_file}")
                else
                    echo "   ✅ ${target_file}"
                fi
            else
                # New file - check if parent dir exists
                parent_dir=$(dirname "$full_path")
                if [[ ! -d "$parent_dir" ]]; then
                    WARNINGS+=("Parent directory missing for: ${target_file}")
                else
                    echo "   ✅ ${target_file} (new file, parent exists)"
                fi
            fi
        done <<< "$target_files"
    else
        echo "   ℹ️  No explicit target files defined"
    fi
fi

# ============================================================================
# Results Summary
# ============================================================================

echo ""
echo "=========================================="

# Determine final result
RESULT="passed"
if [[ ${#ERRORS[@]} -gt 0 ]]; then
    RESULT="failed"
elif [[ ${#WARNINGS[@]} -gt 0 ]]; then
    RESULT="passed_with_warnings"
fi

# Display warnings
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    echo "⚠️  Warnings:"
    for warning in "${WARNINGS[@]}"; do
        echo "  - $warning"
    done
fi

# Display errors
if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo ""
    echo "❌ Errors:"
    for error in "${ERRORS[@]}"; do
        echo "  - $error"
    done
fi

echo ""

# Exit based on result
case "$RESULT" in
    passed)
        echo "✅ Gate 5 PASSED - Worker ready to execute"
        log_validation "INFO" "GATE5-WORKER" "Task ${TASK_ID:-unknown} passed pre-execution gate"
        exit 0
        ;;
    passed_with_warnings)
        echo "⚠️  Gate 5 PASSED WITH WARNINGS - Review before proceeding"
        echo ""
        echo "The task can proceed, but please address the warnings above."
        log_validation "WARN" "GATE5-WORKER" "Task ${TASK_ID:-unknown} passed with warnings"
        exit 0
        ;;
    failed)
        echo "❌ Gate 5 FAILED - Cannot start task"
        echo ""
        echo "Please resolve the errors above before starting this task."
        echo ""
        echo "Options:"
        echo "  1. Wait for blocking tasks to complete"
        echo "  2. Fix file access issues"
        echo "  3. Run /worker status for current status"
        log_validation "ERROR" "GATE5-WORKER" "Task ${TASK_ID:-unknown} failed pre-execution gate"
        exit 1
        ;;
    *)
        echo "⚠️  Unknown validation result"
        exit 0
        ;;
esac
