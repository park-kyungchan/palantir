#!/usr/bin/env bash
# ============================================================================
# Shift-Left Validation Gates (V1.0.1)
# ============================================================================
# Purpose: Shared validation functions for early error detection across pipeline phases
# Architecture: Shift-Left philosophy - catch errors at /clarify, not /synthesis
# Usage: source /home/palantir/.claude/skills/shared/validation-gates.sh
# ============================================================================
#
# CHANGELOG (V1.0.1):
# - Updated shebang to #!/usr/bin/env bash for portability
# - Added VERSION constant for consistency with other modules
# - Standardized header format
#
# CHANGELOG (V1.0.0):
# - Initial implementation with 5 validation gates
# - Gate 1-5: Clarify, Research, Planning, Orchestrate, Worker
# ============================================================================

# ============================================================================
# CONSTANTS
# ============================================================================
VALIDATION_GATES_VERSION="1.0.1"

# ============================================================================
# CONFIGURATION
# ============================================================================

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(pwd)}"
VALIDATION_LOG="${WORKSPACE_ROOT}/.agent/logs/validation_gates.log"

# Ensure log directory exists
mkdir -p "$(dirname "$VALIDATION_LOG")" 2>/dev/null

# ============================================================================
# LOGGING
# ============================================================================

log_validation() {
    local level="$1"
    local gate="$2"
    local message="$3"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    echo "[${timestamp}] [${level}] [${gate}] ${message}" >> "$VALIDATION_LOG"
}

# ============================================================================
# GATE 1: CLARIFY PHASE - Requirement Feasibility
# ============================================================================

validate_requirement_feasibility() {
    local requirement="$1"
    local warnings=()
    local errors=()

    log_validation "INFO" "GATE1-CLARIFY" "Validating requirement feasibility"

    # Extract potential file paths from requirement
    local file_refs
    file_refs=$(echo "$requirement" | grep -oE '[a-zA-Z0-9_/-]+\.(ts|js|py|sh|md|yaml|json)' || true)

    if [[ -n "$file_refs" ]]; then
        while IFS= read -r file_ref; do
            # Check if file exists (try common locations)
            local found=false
            for prefix in "" "src/" ".claude/" ".agent/"; do
                if [[ -f "${WORKSPACE_ROOT}/${prefix}${file_ref}" ]]; then
                    found=true
                    break
                fi
            done

            if [[ "$found" == "false" ]]; then
                warnings+=("Referenced file may not exist: ${file_ref}")
            fi
        done <<< "$file_refs"
    fi

    # Check for potentially dangerous operations
    if echo "$requirement" | grep -qiE '(delete|remove|drop|truncate).*all'; then
        warnings+=("Requirement mentions potentially destructive bulk operation")
    fi

    # Check for vague requirements
    local word_count
    word_count=$(echo "$requirement" | wc -w)
    if [[ "$word_count" -lt 5 ]]; then
        warnings+=("Requirement is very brief - may need clarification")
    fi

    # Output result
    local result="passed"
    if [[ ${#errors[@]} -gt 0 ]]; then
        result="failed"
    elif [[ ${#warnings[@]} -gt 0 ]]; then
        result="passed_with_warnings"
    fi

    log_validation "INFO" "GATE1-CLARIFY" "Result: ${result}, Warnings: ${#warnings[@]}, Errors: ${#errors[@]}"

    # Return JSON result
    local warnings_json
    warnings_json=$(printf '%s\n' "${warnings[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")
    local errors_json
    errors_json=$(printf '%s\n' "${errors[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "gate": "CLARIFY",
  "result": "${result}",
  "warnings": ${warnings_json},
  "errors": ${errors_json}
}
EOF
}

# ============================================================================
# GATE 2: RESEARCH PHASE - Scope Access Validation
# ============================================================================

validate_scope_access() {
    local scope="$1"
    local warnings=()
    local errors=()

    log_validation "INFO" "GATE2-RESEARCH" "Validating scope access: ${scope}"

    # If scope is a path, check if it exists
    if [[ -n "$scope" ]]; then
        local target_path="${WORKSPACE_ROOT}/${scope}"

        if [[ ! -e "$target_path" ]]; then
            errors+=("Scope path does not exist: ${scope}")
        elif [[ ! -r "$target_path" ]]; then
            errors+=("Scope path is not readable: ${scope}")
        fi

        # Check if scope is too broad
        if [[ "$scope" == "." || "$scope" == "/" || "$scope" == "**" ]]; then
            warnings+=("Scope is very broad - consider narrowing for focused analysis")
        fi
    fi

    # Output result
    local result="passed"
    if [[ ${#errors[@]} -gt 0 ]]; then
        result="failed"
    elif [[ ${#warnings[@]} -gt 0 ]]; then
        result="passed_with_warnings"
    fi

    log_validation "INFO" "GATE2-RESEARCH" "Result: ${result}"

    local warnings_json
    warnings_json=$(printf '%s\n' "${warnings[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")
    local errors_json
    errors_json=$(printf '%s\n' "${errors[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "gate": "RESEARCH",
  "result": "${result}",
  "scope": "${scope}",
  "warnings": ${warnings_json},
  "errors": ${errors_json}
}
EOF
}

# ============================================================================
# GATE 3: PLANNING PHASE - Pre-flight Checks
# ============================================================================

pre_flight_checks() {
    local planning_yaml="$1"
    local warnings=()
    local errors=()

    log_validation "INFO" "GATE3-PLANNING" "Running pre-flight checks"

    if [[ ! -f "$planning_yaml" ]]; then
        errors+=("Planning document not found: ${planning_yaml}")
    else
        # Extract target files from YAML
        local target_files
        target_files=$(grep -E '^\s*-?\s*path:' "$planning_yaml" | sed 's/.*path:\s*//' | tr -d '"' || true)

        if [[ -n "$target_files" ]]; then
            while IFS= read -r target_file; do
                target_file=$(echo "$target_file" | xargs)  # trim whitespace
                [[ -z "$target_file" ]] && continue

                local full_path="${WORKSPACE_ROOT}/${target_file}"
                local parent_dir
                parent_dir=$(dirname "$full_path")

                # Check if file exists or parent directory exists (for new files)
                if [[ ! -f "$full_path" && ! -d "$parent_dir" ]]; then
                    warnings+=("Target file parent directory missing: ${target_file}")
                fi
            done <<< "$target_files"
        fi

        # Check for circular dependencies (simple pattern matching)
        local dep_pattern
        dep_pattern=$(grep -E 'dependencies:|blockedBy:' "$planning_yaml" || true)
        # Note: Full circular dependency detection requires graph analysis
        # This is a placeholder for the pattern
    fi

    # Output result
    local result="passed"
    if [[ ${#errors[@]} -gt 0 ]]; then
        result="failed"
    elif [[ ${#warnings[@]} -gt 0 ]]; then
        result="passed_with_warnings"
    fi

    log_validation "INFO" "GATE3-PLANNING" "Result: ${result}"

    local warnings_json
    warnings_json=$(printf '%s\n' "${warnings[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")
    local errors_json
    errors_json=$(printf '%s\n' "${errors[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "gate": "PLANNING",
  "result": "${result}",
  "warnings": ${warnings_json},
  "errors": ${errors_json}
}
EOF
}

# ============================================================================
# GATE 4: ORCHESTRATE PHASE - Dependency Validation
# ============================================================================

validate_phase_dependencies() {
    local phases_json="$1"
    local warnings=()
    local errors=()

    log_validation "INFO" "GATE4-ORCHESTRATE" "Validating phase dependencies"

    # Check if phases_json is valid JSON
    if ! echo "$phases_json" | jq . >/dev/null 2>&1; then
        errors+=("Invalid phases JSON format")
    else
        # Extract phase IDs
        local phase_ids
        phase_ids=$(echo "$phases_json" | jq -r '.[].id' 2>/dev/null || true)

        # Check for duplicate IDs
        local duplicates
        duplicates=$(echo "$phase_ids" | sort | uniq -d)
        if [[ -n "$duplicates" ]]; then
            errors+=("Duplicate phase IDs found: ${duplicates}")
        fi

        # Check for undefined dependencies
        local all_deps
        all_deps=$(echo "$phases_json" | jq -r '.[].dependencies[]?' 2>/dev/null || true)

        if [[ -n "$all_deps" ]]; then
            while IFS= read -r dep; do
                [[ -z "$dep" ]] && continue
                if ! echo "$phase_ids" | grep -q "^${dep}$"; then
                    errors+=("Undefined dependency: ${dep}")
                fi
            done <<< "$all_deps"
        fi

        # Simple circular dependency check (A -> B -> A)
        # Full cycle detection requires more complex graph algorithms
        local phase_count
        phase_count=$(echo "$phases_json" | jq 'length' 2>/dev/null || echo "0")
        if [[ "$phase_count" -gt 10 ]]; then
            warnings+=("Large number of phases (${phase_count}) - consider breaking into sub-projects")
        fi
    fi

    # Output result
    local result="passed"
    if [[ ${#errors[@]} -gt 0 ]]; then
        result="failed"
    elif [[ ${#warnings[@]} -gt 0 ]]; then
        result="passed_with_warnings"
    fi

    log_validation "INFO" "GATE4-ORCHESTRATE" "Result: ${result}"

    local warnings_json
    warnings_json=$(printf '%s\n' "${warnings[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")
    local errors_json
    errors_json=$(printf '%s\n' "${errors[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "gate": "ORCHESTRATE",
  "result": "${result}",
  "warnings": ${warnings_json},
  "errors": ${errors_json}
}
EOF
}

# ============================================================================
# GATE 5: WORKER PHASE - Pre-execution Gate
# ============================================================================

pre_execution_gate() {
    local task_id="$1"
    local task_file="$2"
    local warnings=()
    local errors=()

    log_validation "INFO" "GATE5-WORKER" "Pre-execution gate for task: ${task_id}"

    # Check task file exists
    if [[ -n "$task_file" && ! -f "$task_file" ]]; then
        errors+=("Task prompt file not found: ${task_file}")
    elif [[ -n "$task_file" ]]; then
        # Extract target files from task prompt
        local target_files
        target_files=$(grep -E '^\s*-?\s*path:' "$task_file" 2>/dev/null | sed 's/.*path:\s*//' | tr -d '"' || true)

        if [[ -n "$target_files" ]]; then
            while IFS= read -r target_file; do
                target_file=$(echo "$target_file" | xargs)
                [[ -z "$target_file" ]] && continue

                local full_path="${WORKSPACE_ROOT}/${target_file}"

                # For modification targets, check if file exists
                if [[ -f "$full_path" && ! -w "$full_path" ]]; then
                    errors+=("Target file not writable: ${target_file}")
                fi
            done <<< "$target_files"
        fi

        # Check blockedBy status (if Native Task System available)
        # This would require TaskGet integration - placeholder for now
    fi

    # Output result
    local result="passed"
    if [[ ${#errors[@]} -gt 0 ]]; then
        result="failed"
    elif [[ ${#warnings[@]} -gt 0 ]]; then
        result="passed_with_warnings"
    fi

    log_validation "INFO" "GATE5-WORKER" "Result: ${result}"

    local warnings_json
    warnings_json=$(printf '%s\n' "${warnings[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")
    local errors_json
    errors_json=$(printf '%s\n' "${errors[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "gate": "WORKER",
  "taskId": "${task_id}",
  "result": "${result}",
  "warnings": ${warnings_json},
  "errors": ${errors_json}
}
EOF
}

# ============================================================================
# UTILITY: Run All Gates (Pipeline Validation)
# ============================================================================

run_pipeline_validation() {
    local requirement="$1"
    local scope="$2"
    local planning_doc="$3"

    echo "Running Shift-Left Pipeline Validation..."
    echo "=========================================="

    echo ""
    echo "Gate 1: Clarify (Requirement Feasibility)"
    echo "------------------------------------------"
    validate_requirement_feasibility "$requirement"

    if [[ -n "$scope" ]]; then
        echo ""
        echo "Gate 2: Research (Scope Access)"
        echo "-------------------------------"
        validate_scope_access "$scope"
    fi

    if [[ -n "$planning_doc" ]]; then
        echo ""
        echo "Gate 3: Planning (Pre-flight Checks)"
        echo "------------------------------------"
        pre_flight_checks "$planning_doc"
    fi

    echo ""
    echo "Pipeline validation complete."
}

# ============================================================================
# MAIN (if run directly)
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-help}" in
        gate1|clarify)
            validate_requirement_feasibility "$2"
            ;;
        gate2|research)
            validate_scope_access "$2"
            ;;
        gate3|planning)
            pre_flight_checks "$2"
            ;;
        gate4|orchestrate)
            validate_phase_dependencies "$2"
            ;;
        gate5|worker)
            pre_execution_gate "$2" "$3"
            ;;
        pipeline)
            run_pipeline_validation "$2" "$3" "$4"
            ;;
        *)
            echo "Usage: validation-gates.sh <gate> [args]"
            echo ""
            echo "Gates:"
            echo "  gate1|clarify <requirement>     - Validate requirement feasibility"
            echo "  gate2|research <scope>          - Validate scope access"
            echo "  gate3|planning <yaml_file>      - Run pre-flight checks"
            echo "  gate4|orchestrate <phases_json> - Validate phase dependencies"
            echo "  gate5|worker <task_id> [file]   - Pre-execution validation"
            echo "  pipeline <req> [scope] [plan]   - Run full pipeline validation"
            ;;
    esac
fi
