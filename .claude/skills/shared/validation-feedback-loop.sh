#!/usr/bin/env bash
# =============================================================================
# Validation Feedback Loop Module (V1.0.0)
# =============================================================================
# Purpose: Severity-based feedback loop for P4/P5/P6 patterns
# Architecture: Selective feedback + Review gates + Agent internal loops
# Usage: source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh
# =============================================================================
#
# PATTERNS IMPLEMENTED:
# - P4: Selective Feedback - Severity-based threshold (MEDIUM+)
# - P5: Phase 3.5 Review - Orchestrator review between orchestrate/assign
# - P6: Agent Internal Loop - Max 3 iterations per agent
#
# INTEGRATION:
# - Extends validation-gates.sh with feedback/review logic
# - Compatible with existing validation infrastructure
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
MODULE_VERSION="1.0.0"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(pwd)}"
VALIDATION_LOG="${WORKSPACE_ROOT}/.agent/logs/validation_gates.log"
FEEDBACK_LOG="${WORKSPACE_ROOT}/.agent/logs/feedback_loop.log"

# Severity thresholds for P4
declare -A SEVERITY_LEVELS=(
    ["CRITICAL"]=4
    ["HIGH"]=3
    ["MEDIUM"]=2
    ["LOW"]=1
    ["INFO"]=0
)

# P6 constants
MAX_AGENT_ITERATIONS=3
AGENT_LOOP_STATE_DIR=".agent/tmp/agent-loops"

# Ensure directories exist
mkdir -p "$(dirname "$VALIDATION_LOG")" 2>/dev/null
mkdir -p "$(dirname "$FEEDBACK_LOG")" 2>/dev/null
mkdir -p "$AGENT_LOOP_STATE_DIR" 2>/dev/null

# ============================================================================
# LOGGING
# ============================================================================

log_feedback() {
    local level="$1"
    local component="$2"
    local message="$3"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    echo "[${timestamp}] [${level}] [${component}] ${message}" >> "$FEEDBACK_LOG"
}

# ============================================================================
# P4: SELECTIVE FEEDBACK - Severity-Based Threshold
# ============================================================================

# Check if validation result requires feedback based on severity
# Args:
#   $1 - config_file: Path to skill config (for threshold override)
#   $2 - result_json: Validation result JSON string
# Output:
#   JSON: {"needs_feedback": true/false, "reason": "...", "severity": "..."}
check_selective_feedback() {
    local config_file="$1"
    local result_json="$2"

    log_feedback "INFO" "P4-SELECTIVE" "Checking feedback requirement"

    # Default threshold: MEDIUM+ (P4 spec)
    local threshold="MEDIUM"

    # Override from config if exists
    if [[ -f "$config_file" ]] && grep -q "feedback_threshold:" "$config_file"; then
        threshold=$(grep "feedback_threshold:" "$config_file" | awk '{print $2}' | tr -d '"' || echo "MEDIUM")
    fi

    # Extract validation result
    local gate result errors warnings
    gate=$(echo "$result_json" | jq -r '.gate // "UNKNOWN"')
    result=$(echo "$result_json" | jq -r '.result // "passed"')
    errors=$(echo "$result_json" | jq '.errors // [] | length')
    warnings=$(echo "$result_json" | jq '.warnings // [] | length')

    # Determine severity based on validation result
    local severity="INFO"
    local needs_feedback=false
    local reason=""

    if [[ "$result" == "failed" ]]; then
        if [[ "$errors" -gt 0 ]]; then
            severity="CRITICAL"
            needs_feedback=true
            reason="Validation failed with ${errors} error(s)"
        else
            severity="HIGH"
            needs_feedback=true
            reason="Validation failed"
        fi
    elif [[ "$result" == "passed_with_warnings" ]]; then
        if [[ "$warnings" -ge 3 ]]; then
            severity="MEDIUM"
            needs_feedback=true
            reason="Multiple warnings detected (${warnings})"
        else
            severity="LOW"
            reason="Minor warnings (${warnings})"
        fi
    else
        severity="INFO"
        reason="Validation passed cleanly"
    fi

    # Compare severity against threshold
    local severity_value="${SEVERITY_LEVELS[$severity]:-0}"
    local threshold_value="${SEVERITY_LEVELS[$threshold]:-2}"

    if [[ "$severity_value" -ge "$threshold_value" ]]; then
        needs_feedback=true
    fi

    log_feedback "INFO" "P4-SELECTIVE" "Severity: ${severity}, Threshold: ${threshold}, Feedback: ${needs_feedback}"

    # Return result JSON
    jq -n \
        --arg needs_feedback "$needs_feedback" \
        --arg reason "$reason" \
        --arg severity "$severity" \
        --arg threshold "$threshold" \
        --arg gate "$gate" \
        '{
            needs_feedback: ($needs_feedback == "true"),
            reason: $reason,
            severity: $severity,
            threshold: $threshold,
            gate: $gate
        }'
}

# ============================================================================
# P5: PHASE 3.5 REVIEW GATE - Orchestrator Review
# ============================================================================

# Execute review gate between orchestrate and assign phases
# Args:
#   $1 - skill_name: Name of skill being reviewed (orchestrate, planning, etc.)
#   $2 - result_json: Validation/orchestration result JSON
#   $3 - auto_approve: true/false (default: false)
# Output:
#   JSON: {"approved": true/false, "reason": "...", "reviewer": "..."}
review_gate() {
    local skill_name="$1"
    local result_json="$2"
    local auto_approve="${3:-false}"

    log_feedback "INFO" "P5-REVIEW" "Executing review gate for ${skill_name}"

    # Extract key metrics from result
    local task_count dependency_count complexity
    task_count=$(echo "$result_json" | jq '.tasks // [] | length' 2>/dev/null || echo "0")
    dependency_count=$(echo "$result_json" | jq '[.tasks[]?.blockedBy // [] | length] | add // 0' 2>/dev/null || echo "0")
    complexity=$(echo "$result_json" | jq -r '.metadata.complexity // "unknown"' 2>/dev/null || echo "unknown")

    # Phase 3.5 Review Criteria (from P5 spec):
    # 1. Task count reasonable (<= 10 for most cases)
    # 2. Dependency chains not too deep (<= 3 levels)
    # 3. Complexity matches requirement

    local warnings=()
    local errors=()
    local approved=true

    # Criterion 1: Task count
    if [[ "$task_count" -gt 10 ]]; then
        warnings+=("High task count (${task_count}): Consider grouping related tasks")
    elif [[ "$task_count" -gt 15 ]]; then
        errors+=("Excessive task count (${task_count}): Break into smaller phases")
        approved=false
    fi

    # Criterion 2: Dependency depth (simplified check - full check requires graph traversal)
    if [[ "$dependency_count" -gt "$((task_count * 2))" ]]; then
        warnings+=("High dependency count (${dependency_count}): May indicate complex dependency chains")
    fi

    # Criterion 3: Complexity validation (placeholder - requires external context)
    if [[ "$complexity" == "unknown" ]]; then
        warnings+=("Complexity level not specified in result")
    fi

    # Auto-approve logic
    if [[ "$auto_approve" == "true" ]] && [[ ${#errors[@]} -eq 0 ]]; then
        approved=true
        log_feedback "INFO" "P5-REVIEW" "Auto-approved (no errors)"
    elif [[ ${#errors[@]} -gt 0 ]]; then
        approved=false
        log_feedback "WARN" "P5-REVIEW" "Review failed with ${#errors[@]} error(s)"
    fi

    # Construct result
    local warnings_json errors_json
    warnings_json=$(printf '%s\n' "${warnings[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")
    errors_json=$(printf '%s\n' "${errors[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    jq -n \
        --argjson approved "$approved" \
        --arg reason "Review gate for ${skill_name}" \
        --arg reviewer "system" \
        --arg skill_name "$skill_name" \
        --argjson task_count "$task_count" \
        --argjson dependency_count "$dependency_count" \
        --argjson warnings "$warnings_json" \
        --argjson errors "$errors_json" \
        '{
            approved: $approved,
            reason: $reason,
            reviewer: $reviewer,
            skill_name: $skill_name,
            metrics: {
                task_count: $task_count,
                dependency_count: $dependency_count
            },
            warnings: $warnings,
            errors: $errors
        }'
}

# ============================================================================
# P6: AGENT INTERNAL LOOP - Max 3 Iterations
# ============================================================================

# Execute feedback loop with max iterations per agent
# Args:
#   $1 - skill_name: Name of skill (research, planning, etc.)
#   $2 - max_iterations: Maximum iterations (default: 3)
#   $3 - trigger_condition: Bash expression for continuation (e.g., "[[ $errors -gt 0 ]]")
# Returns:
#   0 if loop completed successfully, 1 if max iterations reached
run_feedback_loop() {
    local skill_name="$1"
    local max_iterations="${2:-$MAX_AGENT_ITERATIONS}"
    local trigger_condition="${3:-[[ \$errors -gt 0 ]]}"

    local iteration=0
    local loop_state_file="${AGENT_LOOP_STATE_DIR}/${skill_name}-loop.json"

    log_feedback "INFO" "P6-LOOP" "Starting feedback loop for ${skill_name} (max: ${max_iterations})"

    # Initialize loop state
    cat > "$loop_state_file" <<EOF
{
    "skill_name": "${skill_name}",
    "max_iterations": ${max_iterations},
    "current_iteration": 0,
    "status": "running",
    "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

    while [[ "$iteration" -lt "$max_iterations" ]]; do
        iteration=$((iteration + 1))

        log_feedback "INFO" "P6-LOOP" "Iteration ${iteration}/${max_iterations} for ${skill_name}"

        # Update state
        jq ".current_iteration = ${iteration}" "$loop_state_file" > "${loop_state_file}.tmp"
        mv "${loop_state_file}.tmp" "$loop_state_file"

        # Note: Actual validation execution happens externally
        # This function manages iteration counting and state

        # Check if we should continue (this is a placeholder - actual check done by caller)
        local errors=0  # Caller should update this based on validation result

        # Evaluate trigger condition (simplified - actual implementation may vary)
        if ! eval "$trigger_condition"; then
            log_feedback "INFO" "P6-LOOP" "Loop completed successfully at iteration ${iteration}"
            jq '.status = "completed"' "$loop_state_file" > "${loop_state_file}.tmp"
            mv "${loop_state_file}.tmp" "$loop_state_file"
            return 0
        fi

        if [[ "$iteration" -eq "$max_iterations" ]]; then
            log_feedback "WARN" "P6-LOOP" "Max iterations reached for ${skill_name}"
            jq '.status = "max_iterations_reached"' "$loop_state_file" > "${loop_state_file}.tmp"
            mv "${loop_state_file}.tmp" "$loop_state_file"
            return 1
        fi
    done

    return 1
}

# Get current loop state for a skill
get_loop_state() {
    local skill_name="$1"
    local loop_state_file="${AGENT_LOOP_STATE_DIR}/${skill_name}-loop.json"

    if [[ -f "$loop_state_file" ]]; then
        cat "$loop_state_file"
    else
        echo '{"status": "not_started"}'
    fi
}

# Reset loop state for a skill
reset_loop_state() {
    local skill_name="$1"
    local loop_state_file="${AGENT_LOOP_STATE_DIR}/${skill_name}-loop.json"

    if [[ -f "$loop_state_file" ]]; then
        rm -f "$loop_state_file"
        log_feedback "INFO" "P6-LOOP" "Reset loop state for ${skill_name}"
    fi
}

# ============================================================================
# AGENT PROMPT GENERATION - Internal Loop Instructions
# ============================================================================

# Generate agent prompt with internal feedback loop instructions
# Args:
#   $1 - agent_type: Type of agent (research, planning, etc.)
#   $2 - validation_criteria: JSON string with validation requirements
# Output:
#   Agent prompt text with internal loop instructions
generate_agent_prompt_with_internal_loop() {
    local agent_type="$1"
    local validation_criteria="$2"

    log_feedback "INFO" "P6-PROMPT" "Generating agent prompt with internal loop for ${agent_type}"

    # Extract validation requirements
    local required_sections completeness_checks quality_thresholds
    required_sections=$(echo "$validation_criteria" | jq -r '.required_sections // [] | join(", ")' 2>/dev/null || echo "")
    completeness_checks=$(echo "$validation_criteria" | jq -r '.completeness_checks // [] | join(", ")' 2>/dev/null || echo "")
    quality_thresholds=$(echo "$validation_criteria" | jq -r '.quality_thresholds // {} | to_entries | map("\(.key): \(.value)") | join(", ")' 2>/dev/null || echo "")

    # Generate prompt with internal loop instructions
    cat <<EOF
# ${agent_type} Agent - With Internal Feedback Loop (P6)

## Objective
Execute ${agent_type} task with self-validation and iterative improvement.

## Internal Feedback Loop Instructions

You MUST follow this iterative process (max ${MAX_AGENT_ITERATIONS} iterations):

### 1. Execute Task
Perform your primary ${agent_type} task according to specifications.

### 2. Self-Validate
After each iteration, validate your output against these criteria:

**Required Sections:** ${required_sections:-"See task specification"}
**Completeness Checks:** ${completeness_checks:-"All requirements addressed"}
**Quality Thresholds:** ${quality_thresholds:-"See task specification"}

### 3. Identify Issues
Use validation result to identify:
- Missing sections or incomplete content
- Quality issues below threshold
- Logical gaps or inconsistencies

### 4. Iterate or Complete
- If validation PASSES → Proceed to output
- If validation FAILS + iterations < ${MAX_AGENT_ITERATIONS} → Refine and re-validate
- If max iterations reached → Output best result with issues documented

### 5. Document Loop
Include in your output:
\`\`\`yaml
internal_feedback_loop:
  iterations_used: <number>
  final_validation_status: <passed|passed_with_warnings|max_iterations_reached>
  issues_resolved: [<list>]
  remaining_issues: [<list>]
\`\`\`

## Validation Criteria
${validation_criteria}

## Important Notes
- Each iteration should show measurable improvement
- Do NOT output intermediate iterations to user
- Document your self-validation process
- Maximize quality within ${MAX_AGENT_ITERATIONS} iterations

---
Generated by validation-feedback-loop.sh v${MODULE_VERSION}
EOF
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f check_selective_feedback
export -f review_gate
export -f run_feedback_loop
export -f get_loop_state
export -f reset_loop_state
export -f generate_agent_prompt_with_internal_loop
export -f log_feedback

# ============================================================================
# SELF-TEST (Optional - for development)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Validation Feedback Loop Self-Test ==="

    # Test 1: Check selective feedback (MEDIUM severity)
    echo "Test 1: check_selective_feedback"
    test_result_json='{"gate":"CLARIFY","result":"passed_with_warnings","errors":[],"warnings":["Warning 1","Warning 2","Warning 3"]}'
    feedback_result=$(check_selective_feedback "/dev/null" "$test_result_json")
    echo "  Result: $feedback_result"
    needs_feedback=$(echo "$feedback_result" | jq -r '.needs_feedback')
    echo "  Needs feedback: $needs_feedback (expected: true for 3+ warnings)"

    # Test 2: Review gate
    echo "Test 2: review_gate"
    orchestrate_result='{"tasks":[{"id":1},{"id":2},{"id":3}],"metadata":{"complexity":"moderate"}}'
    review_result=$(review_gate "orchestrate" "$orchestrate_result" "false")
    echo "  Result: $review_result"
    approved=$(echo "$review_result" | jq -r '.approved')
    echo "  Approved: $approved (expected: true for 3 tasks)"

    # Test 3: Agent prompt generation
    echo "Test 3: generate_agent_prompt_with_internal_loop"
    validation_criteria='{"required_sections":["overview","details"],"completeness_checks":["all_requirements"]}'
    prompt=$(generate_agent_prompt_with_internal_loop "research" "$validation_criteria")
    echo "  Prompt length: $(echo "$prompt" | wc -l) lines"
    echo "  Contains 'Internal Feedback Loop': $(echo "$prompt" | grep -c 'Internal Feedback Loop')"

    # Test 4: Loop state management
    echo "Test 4: Loop state management"
    reset_loop_state "test-skill"
    initial_state=$(get_loop_state "test-skill")
    echo "  Initial state: $initial_state"

    echo "=== All self-tests completed ==="
fi
