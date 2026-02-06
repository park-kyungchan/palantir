#!/usr/bin/env bash
# ============================================================================
# Parallel Agent Coordination Module (V1.0.1)
# ============================================================================
# Purpose: Shared module for parallel agent deployment, tracking, and result aggregation
# Architecture: Part of Enhanced Feedback Loop Pattern (P2: parallel_agent_deployment)
# Usage: source /home/palantir/.claude/skills/shared/parallel-agent.sh
# ============================================================================
#
# CHANGELOG (V1.0.1):
# - Updated shebang to #!/usr/bin/env bash for portability
# - Added VERSION constant for consistency with other modules
#
# CHANGELOG (V1.0.0):
# - Initial implementation for parallel agent coordination
# - Complexity assessment, agent count calculation
# - Agent registration, completion tracking, L1 aggregation
# ============================================================================
#
# Shared module for parallel agent deployment, tracking, and result aggregation.
# Source this file: source .claude/skills/shared/parallel-agent.sh
#
# Part of: Enhanced Feedback Loop Pattern (P2: parallel_agent_deployment)
#
# ============================================================================

# ============================================================================
# CONSTANTS
# ============================================================================
PARALLEL_AGENT_VERSION="1.0.1"

# ============================================================================
# CONFIGURATION
# ============================================================================

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(pwd)}"
PARALLEL_AGENT_LOG="${WORKSPACE_ROOT}/.agent/logs/parallel_agents.log"
PARALLEL_AGENT_STATE="${WORKSPACE_ROOT}/.agent/tmp/parallel_agent_state.json"

# Agent limits
MIN_AGENTS=2
MAX_AGENTS=5
DEFAULT_AGENTS=3

# Token budgets (L1/L2/L3 Progressive Disclosure)
L1_TOKEN_LIMIT=500
L2_TOKEN_LIMIT=2000
TOTAL_TOKEN_BUDGET=10000

# Ensure directories exist
mkdir -p "$(dirname "$PARALLEL_AGENT_LOG")" 2>/dev/null
mkdir -p "$(dirname "$PARALLEL_AGENT_STATE")" 2>/dev/null

# ============================================================================
# LOGGING
# ============================================================================

log_parallel() {
    local level="$1"
    local action="$2"
    local message="$3"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    echo "[${timestamp}] [${level}] [PARALLEL-AGENT] [${action}] ${message}" >> "$PARALLEL_AGENT_LOG"
}

# ============================================================================
# COMPLEXITY ASSESSMENT
# ============================================================================

assess_complexity() {
    local scope="$1"
    local file_count=0
    local dir_depth=0
    local complexity_score=0

    log_parallel "INFO" "ASSESS" "Assessing complexity for scope: ${scope}"

    # Count files in scope
    if [[ -d "${WORKSPACE_ROOT}/${scope}" ]]; then
        file_count=$(find "${WORKSPACE_ROOT}/${scope}" -type f -name "*.md" -o -name "*.sh" -o -name "*.yaml" 2>/dev/null | wc -l)
    elif [[ -f "${WORKSPACE_ROOT}/${scope}" ]]; then
        file_count=1
    fi

    # Calculate directory depth
    dir_depth=$(echo "$scope" | tr '/' '\n' | wc -l)

    # Scoring
    # File count: <10 = LOW, 10-50 = MEDIUM, >50 = HIGH
    if [[ $file_count -lt 10 ]]; then
        complexity_score=$((complexity_score + 1))
    elif [[ $file_count -lt 50 ]]; then
        complexity_score=$((complexity_score + 2))
    else
        complexity_score=$((complexity_score + 3))
    fi

    # Directory depth: <3 = LOW, 3-5 = MEDIUM, >5 = HIGH
    if [[ $dir_depth -lt 3 ]]; then
        complexity_score=$((complexity_score + 1))
    elif [[ $dir_depth -lt 6 ]]; then
        complexity_score=$((complexity_score + 2))
    else
        complexity_score=$((complexity_score + 3))
    fi

    local complexity_level="LOW"
    if [[ $complexity_score -ge 5 ]]; then
        complexity_level="HIGH"
    elif [[ $complexity_score -ge 3 ]]; then
        complexity_level="MEDIUM"
    fi

    log_parallel "INFO" "ASSESS" "Complexity: ${complexity_level} (score: ${complexity_score}, files: ${file_count})"

    cat <<EOF
{
  "scope": "${scope}",
  "fileCount": ${file_count},
  "directoryDepth": ${dir_depth},
  "complexityScore": ${complexity_score},
  "complexityLevel": "${complexity_level}"
}
EOF
}

# ============================================================================
# AGENT COUNT CALCULATION
# ============================================================================

calculate_agent_count() {
    local complexity_level="$1"
    local token_budget="${2:-$TOTAL_TOKEN_BUDGET}"
    local agent_count=$DEFAULT_AGENTS

    case "$complexity_level" in
        "LOW")
            agent_count=2
            ;;
        "MEDIUM")
            agent_count=3
            ;;
        "HIGH")
            agent_count=4
            ;;
        "CRITICAL")
            agent_count=5
            ;;
    esac

    # Adjust based on token budget
    local max_by_budget=$((token_budget / (L1_TOKEN_LIMIT * 2)))
    if [[ $max_by_budget -lt $agent_count ]]; then
        agent_count=$max_by_budget
    fi

    # Enforce limits
    if [[ $agent_count -lt $MIN_AGENTS ]]; then
        agent_count=$MIN_AGENTS
    fi
    if [[ $agent_count -gt $MAX_AGENTS ]]; then
        agent_count=$MAX_AGENTS
    fi

    log_parallel "INFO" "CALC" "Agent count: ${agent_count} (complexity: ${complexity_level}, budget: ${token_budget})"

    echo "$agent_count"
}

# ============================================================================
# AGENT REGISTRATION
# ============================================================================

init_parallel_session() {
    local session_id="$1"
    local expected_agents="$2"

    log_parallel "INFO" "INIT" "Initializing parallel session: ${session_id} (expecting ${expected_agents} agents)"

    cat > "$PARALLEL_AGENT_STATE" <<EOF
{
  "sessionId": "${session_id}",
  "expectedAgents": ${expected_agents},
  "registeredAgents": [],
  "completedAgents": [],
  "results": {},
  "startTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "RUNNING"
}
EOF

    echo "$session_id"
}

register_agent() {
    local session_id="$1"
    local agent_id="$2"
    local agent_type="$3"
    local partition="$4"

    log_parallel "INFO" "REGISTER" "Registering agent: ${agent_id} (type: ${agent_type}, partition: ${partition})"

    if [[ -f "$PARALLEL_AGENT_STATE" ]]; then
        local temp_file="${PARALLEL_AGENT_STATE}.tmp"
        jq --arg aid "$agent_id" --arg atype "$agent_type" --arg part "$partition" \
           '.registeredAgents += [{"agentId": $aid, "agentType": $atype, "partition": $part, "status": "RUNNING", "registeredAt": now | todate}]' \
           "$PARALLEL_AGENT_STATE" > "$temp_file" && mv "$temp_file" "$PARALLEL_AGENT_STATE"
    fi

    cat <<EOF
{
  "agentId": "${agent_id}",
  "agentType": "${agent_type}",
  "partition": "${partition}",
  "status": "REGISTERED"
}
EOF
}

# ============================================================================
# AGENT COMPLETION TRACKING
# ============================================================================

mark_agent_complete() {
    local agent_id="$1"
    local l1_summary="$2"
    local l2_path="$3"
    local token_count="${4:-0}"

    log_parallel "INFO" "COMPLETE" "Agent completed: ${agent_id} (tokens: ${token_count})"

    if [[ -f "$PARALLEL_AGENT_STATE" ]]; then
        local temp_file="${PARALLEL_AGENT_STATE}.tmp"
        jq --arg aid "$agent_id" --arg l1 "$l1_summary" --arg l2 "$l2_path" --argjson tokens "$token_count" \
           '.completedAgents += [$aid] |
            .results[$aid] = {"l1Summary": $l1, "l2Path": $l2, "tokenCount": $tokens, "completedAt": now | todate} |
            (.registeredAgents[] | select(.agentId == $aid) | .status) = "COMPLETED"' \
           "$PARALLEL_AGENT_STATE" > "$temp_file" && mv "$temp_file" "$PARALLEL_AGENT_STATE"
    fi

    cat <<EOF
{
  "agentId": "${agent_id}",
  "status": "COMPLETED",
  "l2Path": "${l2_path}",
  "tokenCount": ${token_count}
}
EOF
}

check_all_complete() {
    if [[ ! -f "$PARALLEL_AGENT_STATE" ]]; then
        echo "false"
        return
    fi

    local expected
    local completed
    expected=$(jq -r '.expectedAgents' "$PARALLEL_AGENT_STATE")
    completed=$(jq -r '.completedAgents | length' "$PARALLEL_AGENT_STATE")

    if [[ "$completed" -ge "$expected" ]]; then
        echo "true"
    else
        echo "false"
    fi
}

wait_for_agents() {
    local timeout="${1:-300}"  # Default 5 minutes
    local poll_interval="${2:-5}"
    local elapsed=0

    log_parallel "INFO" "WAIT" "Waiting for all agents (timeout: ${timeout}s)"

    while [[ $elapsed -lt $timeout ]]; do
        if [[ "$(check_all_complete)" == "true" ]]; then
            log_parallel "INFO" "WAIT" "All agents completed"
            return 0
        fi
        sleep "$poll_interval"
        elapsed=$((elapsed + poll_interval))
    done

    log_parallel "WARN" "WAIT" "Timeout waiting for agents"
    return 1
}

# ============================================================================
# L1 AGGREGATION
# ============================================================================

aggregate_l1_results() {
    local output_file="$1"
    local dedup="${2:-true}"

    log_parallel "INFO" "AGGREGATE" "Aggregating L1 results (dedup: ${dedup})"

    if [[ ! -f "$PARALLEL_AGENT_STATE" ]]; then
        echo '{"error": "No parallel session state found"}'
        return 1
    fi

    local results
    results=$(jq -r '.results' "$PARALLEL_AGENT_STATE")

    local total_tokens=0
    local agent_count
    agent_count=$(jq -r '.completedAgents | length' "$PARALLEL_AGENT_STATE")

    # Calculate total tokens
    total_tokens=$(jq -r '[.results[].tokenCount] | add // 0' "$PARALLEL_AGENT_STATE")

    # Extract all L1 summaries
    local l1_summaries
    l1_summaries=$(jq -r '[.results[].l1Summary] | join("\n\n---\n\n")' "$PARALLEL_AGENT_STATE")

    # Deduplication (simple line-based)
    if [[ "$dedup" == "true" ]]; then
        l1_summaries=$(echo "$l1_summaries" | sort -u)
    fi

    log_parallel "INFO" "AGGREGATE" "Aggregated ${agent_count} agents, total tokens: ${total_tokens}"

    # Write aggregated result
    if [[ -n "$output_file" ]]; then
        cat > "$output_file" <<EOF
# Aggregated L1 Results

**Session:** $(jq -r '.sessionId' "$PARALLEL_AGENT_STATE")
**Agents:** ${agent_count}
**Total Tokens:** ${total_tokens}
**Aggregated At:** $(date -u +%Y-%m-%dT%H:%M:%SZ)

---

${l1_summaries}
EOF
        log_parallel "INFO" "AGGREGATE" "Written to: ${output_file}"
    fi

    cat <<EOF
{
  "sessionId": "$(jq -r '.sessionId' "$PARALLEL_AGENT_STATE")",
  "agentCount": ${agent_count},
  "totalTokens": ${total_tokens},
  "outputFile": "${output_file}",
  "status": "AGGREGATED"
}
EOF
}

# ============================================================================
# TOKEN BUDGET MANAGEMENT
# ============================================================================

get_token_usage_summary() {
    if [[ ! -f "$PARALLEL_AGENT_STATE" ]]; then
        echo '{"error": "No parallel session state found"}'
        return 1
    fi

    local total_used
    local budget_remaining
    total_used=$(jq -r '[.results[].tokenCount] | add // 0' "$PARALLEL_AGENT_STATE")
    budget_remaining=$((TOTAL_TOKEN_BUDGET - total_used))

    local status="OK"
    if [[ $budget_remaining -lt $((TOTAL_TOKEN_BUDGET / 4)) ]]; then
        status="WARNING"
    fi
    if [[ $budget_remaining -lt 0 ]]; then
        status="EXCEEDED"
    fi

    cat <<EOF
{
  "totalBudget": ${TOTAL_TOKEN_BUDGET},
  "totalUsed": ${total_used},
  "budgetRemaining": ${budget_remaining},
  "l1Limit": ${L1_TOKEN_LIMIT},
  "l2Limit": ${L2_TOKEN_LIMIT},
  "status": "${status}"
}
EOF
}

validate_token_budget() {
    local requested_tokens="$1"
    local total_used
    total_used=$(jq -r '[.results[].tokenCount] | add // 0' "$PARALLEL_AGENT_STATE" 2>/dev/null || echo "0")

    local projected=$((total_used + requested_tokens))

    if [[ $projected -gt $TOTAL_TOKEN_BUDGET ]]; then
        log_parallel "WARN" "BUDGET" "Token budget would be exceeded: ${projected} > ${TOTAL_TOKEN_BUDGET}"
        echo "EXCEEDED"
        return 1
    fi

    echo "OK"
    return 0
}

# ============================================================================
# PARTITION HELPERS
# ============================================================================

partition_search_space() {
    local scope="$1"
    local agent_count="$2"
    local partitions=()

    log_parallel "INFO" "PARTITION" "Partitioning scope: ${scope} into ${agent_count} partitions"

    # For directory scope, partition by subdirectories or file patterns
    if [[ -d "${WORKSPACE_ROOT}/${scope}" ]]; then
        local subdirs
        subdirs=$(find "${WORKSPACE_ROOT}/${scope}" -maxdepth 1 -type d | tail -n +2 | head -n "$agent_count")

        local i=0
        while IFS= read -r subdir; do
            [[ -z "$subdir" ]] && continue
            partitions+=("$(basename "$subdir")")
            i=$((i + 1))
        done <<< "$subdirs"

        # If not enough subdirs, use file patterns
        if [[ ${#partitions[@]} -lt $agent_count ]]; then
            partitions=()
            for ((i=0; i<agent_count; i++)); do
                partitions+=("partition_$((i + 1))")
            done
        fi
    else
        # Single file or abstract scope
        for ((i=0; i<agent_count; i++)); do
            partitions+=("partition_$((i + 1))")
        done
    fi

    # Output as JSON array
    printf '%s\n' "${partitions[@]}" | jq -R . | jq -s '.'
}

# ============================================================================
# CLEANUP
# ============================================================================

cleanup_parallel_session() {
    local session_id="$1"

    log_parallel "INFO" "CLEANUP" "Cleaning up session: ${session_id}"

    if [[ -f "$PARALLEL_AGENT_STATE" ]]; then
        local current_session
        current_session=$(jq -r '.sessionId' "$PARALLEL_AGENT_STATE")
        if [[ "$current_session" == "$session_id" ]]; then
            # Update status to COMPLETED
            local temp_file="${PARALLEL_AGENT_STATE}.tmp"
            jq '.status = "COMPLETED" | .endTime = (now | todate)' \
               "$PARALLEL_AGENT_STATE" > "$temp_file" && mv "$temp_file" "$PARALLEL_AGENT_STATE"
        fi
    fi

    echo '{"status": "CLEANED"}'
}

# ============================================================================
# MAIN (if run directly)
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-help}" in
        assess)
            assess_complexity "$2"
            ;;
        calc-agents)
            calculate_agent_count "$2" "$3"
            ;;
        init)
            init_parallel_session "$2" "$3"
            ;;
        register)
            register_agent "$2" "$3" "$4" "$5"
            ;;
        complete)
            mark_agent_complete "$2" "$3" "$4" "$5"
            ;;
        check)
            check_all_complete
            ;;
        wait)
            wait_for_agents "$2" "$3"
            ;;
        aggregate)
            aggregate_l1_results "$2" "$3"
            ;;
        tokens)
            get_token_usage_summary
            ;;
        validate-budget)
            validate_token_budget "$2"
            ;;
        partition)
            partition_search_space "$2" "$3"
            ;;
        cleanup)
            cleanup_parallel_session "$2"
            ;;
        *)
            cat <<EOF
Usage: parallel-agent.sh <command> [args]

Commands:
  assess <scope>                    - Assess complexity of scope
  calc-agents <level> [budget]      - Calculate optimal agent count
  init <session_id> <agent_count>   - Initialize parallel session
  register <sid> <aid> <type> <part> - Register an agent
  complete <aid> <l1> <l2> [tokens] - Mark agent as complete
  check                             - Check if all agents complete
  wait [timeout] [interval]         - Wait for all agents
  aggregate <output_file> [dedup]   - Aggregate L1 results
  tokens                            - Get token usage summary
  validate-budget <requested>       - Validate token budget
  partition <scope> <count>         - Partition search space
  cleanup <session_id>              - Cleanup session

Configuration:
  MIN_AGENTS=${MIN_AGENTS}
  MAX_AGENTS=${MAX_AGENTS}
  L1_TOKEN_LIMIT=${L1_TOKEN_LIMIT}
  L2_TOKEN_LIMIT=${L2_TOKEN_LIMIT}
  TOTAL_TOKEN_BUDGET=${TOTAL_TOKEN_BUDGET}
EOF
            ;;
    esac
fi
