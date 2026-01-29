#!/usr/bin/env bash
# =============================================================================
# Parallel Agent Module (V1.0.0)
# =============================================================================
# Purpose: Parallel agent spawning and synchronization for P2 implementation
# Architecture: Multi-agent orchestration with complexity-based scaling
# Usage: source /home/palantir/.claude/skills/shared/parallel-agent.sh
# =============================================================================
#
# PATTERN IMPLEMENTED:
# - P2: Parallel Agent Execution - Spawn multiple agents based on complexity
#
# FEATURES:
# - Agent spawning with Task tool integration
# - Multiple synchronization strategies (parallel, sequential, barrier)
# - Result aggregation (merge, vote, consensus)
# - Complexity-based agent count calculation
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
MODULE_VERSION="1.0.0"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(pwd)}"
AGENT_STATE_DIR=".agent/tmp/agent-state"
AGENT_LOG="${WORKSPACE_ROOT}/.agent/logs/parallel_agent.log"

# Complexity thresholds for agent count
declare -A COMPLEXITY_AGENT_COUNT=(
    ["simple"]=2
    ["moderate"]=3
    ["complex"]=4
    ["very_complex"]=5
)

# Ensure directories exist
mkdir -p "$AGENT_STATE_DIR" 2>/dev/null
mkdir -p "$(dirname "$AGENT_LOG")" 2>/dev/null

# ============================================================================
# LOGGING
# ============================================================================

log_agent() {
    local level="$1"
    local component="$2"
    local message="$3"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    echo "[${timestamp}] [${level}] [${component}] ${message}" >> "$AGENT_LOG"
}

# ============================================================================
# P2: PARALLEL AGENT SPAWN
# ============================================================================

# Spawn parallel agent with Task tool
# Args:
#   $1 - agent_config_json: JSON string with agent configuration
#        Required fields: agent_type, prompt, description
#        Optional fields: model, run_in_background
# Output:
#   agent_id: Unique identifier for spawned agent
parallel_agent_spawn() {
    local agent_config_json="$1"

    log_agent "INFO" "P2-SPAWN" "Spawning parallel agent"

    # Extract configuration
    local agent_type prompt description model run_in_background
    agent_type=$(echo "$agent_config_json" | jq -r '.agent_type // "general-purpose"')
    prompt=$(echo "$agent_config_json" | jq -r '.prompt // ""')
    description=$(echo "$agent_config_json" | jq -r '.description // "Parallel agent task"')
    model=$(echo "$agent_config_json" | jq -r '.model // "sonnet"')
    run_in_background=$(echo "$agent_config_json" | jq -r '.run_in_background // "false"')

    # Validate required fields
    if [[ -z "$prompt" ]]; then
        log_agent "ERROR" "P2-SPAWN" "Missing required field: prompt"
        echo "ERROR: Missing required field: prompt" >&2
        return 1
    fi

    # Generate unique agent ID
    local agent_id
    agent_id="agent-$(date +%s)-$$-$RANDOM"

    # Create agent state file
    local agent_state_file="${AGENT_STATE_DIR}/${agent_id}.json"
    cat > "$agent_state_file" <<EOF
{
  "agent_id": "${agent_id}",
  "agent_type": "${agent_type}",
  "description": "${description}",
  "model": "${model}",
  "run_in_background": ${run_in_background},
  "status": "spawned",
  "spawned_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "task_id": null,
  "output_file": null
}
EOF

    log_agent "INFO" "P2-SPAWN" "Agent spawned: ${agent_id} (type: ${agent_type}, model: ${model})"

    # Note: Actual Task tool invocation happens in caller context
    # This function prepares state and returns agent ID for tracking
    echo "$agent_id"
}

# Update agent state with task ID
update_agent_state() {
    local agent_id="$1"
    local task_id="$2"
    local output_file="${3:-}"

    local agent_state_file="${AGENT_STATE_DIR}/${agent_id}.json"

    if [[ ! -f "$agent_state_file" ]]; then
        log_agent "ERROR" "P2-STATE" "Agent state not found: ${agent_id}"
        return 1
    fi

    # Update state
    jq \
        --arg task_id "$task_id" \
        --arg output_file "$output_file" \
        --arg status "running" \
        '.task_id = $task_id | .output_file = $output_file | .status = $status | .started_at = now | .started_at |= (. | todate)' \
        "$agent_state_file" > "${agent_state_file}.tmp"
    mv "${agent_state_file}.tmp" "$agent_state_file"

    log_agent "INFO" "P2-STATE" "Updated agent ${agent_id}: task_id=${task_id}"
}

# Get agent state
get_agent_state() {
    local agent_id="$1"
    local agent_state_file="${AGENT_STATE_DIR}/${agent_id}.json"

    if [[ -f "$agent_state_file" ]]; then
        cat "$agent_state_file"
    else
        echo '{"status": "not_found"}'
    fi
}

# ============================================================================
# AGENT SYNCHRONIZATION
# ============================================================================

# Synchronize multiple agents using specified strategy
# Args:
#   $1 - agent_ids: JSON array of agent IDs
#   $2 - wait_strategy: Strategy for synchronization
#        - parallel: All agents run independently, return immediately
#        - sequential: Wait for each agent to complete before next
#        - barrier: Wait for all agents to complete (default)
# Output:
#   JSON: {"status": "completed", "agent_results": [...]}
agent_synchronization() {
    local agent_ids_json="$1"
    local wait_strategy="${2:-barrier}"

    log_agent "INFO" "P2-SYNC" "Synchronizing agents with strategy: ${wait_strategy}"

    # Parse agent IDs
    local agent_ids
    agent_ids=$(echo "$agent_ids_json" | jq -r '.[]' 2>/dev/null || echo "$agent_ids_json")

    local agent_results=()
    local all_completed=true

    case "$wait_strategy" in
        parallel)
            # Return immediately - agents run in background
            log_agent "INFO" "P2-SYNC" "Parallel mode: returning immediately"

            for agent_id in $agent_ids; do
                local state
                state=$(get_agent_state "$agent_id")
                agent_results+=("$state")
            done
            ;;

        sequential)
            # Wait for each agent sequentially
            log_agent "INFO" "P2-SYNC" "Sequential mode: waiting for agents one by one"

            for agent_id in $agent_ids; do
                log_agent "INFO" "P2-SYNC" "Waiting for agent: ${agent_id}"

                # Poll agent state until completed
                local max_wait=600  # 10 minutes
                local wait_interval=2
                local elapsed=0

                while [[ $elapsed -lt $max_wait ]]; do
                    local state
                    state=$(get_agent_state "$agent_id")
                    local status
                    status=$(echo "$state" | jq -r '.status // "unknown"')

                    if [[ "$status" == "completed" ]]; then
                        log_agent "INFO" "P2-SYNC" "Agent completed: ${agent_id}"
                        agent_results+=("$state")
                        break
                    elif [[ "$status" == "failed" ]]; then
                        log_agent "ERROR" "P2-SYNC" "Agent failed: ${agent_id}"
                        agent_results+=("$state")
                        all_completed=false
                        break
                    fi

                    sleep $wait_interval
                    elapsed=$((elapsed + wait_interval))
                done

                if [[ $elapsed -ge $max_wait ]]; then
                    log_agent "WARN" "P2-SYNC" "Agent timeout: ${agent_id}"
                    all_completed=false
                fi
            done
            ;;

        barrier)
            # Wait for all agents to complete (barrier synchronization)
            log_agent "INFO" "P2-SYNC" "Barrier mode: waiting for all agents"

            local max_wait=600  # 10 minutes
            local wait_interval=2
            local elapsed=0

            while [[ $elapsed -lt $max_wait ]]; do
                local all_done=true

                for agent_id in $agent_ids; do
                    local state
                    state=$(get_agent_state "$agent_id")
                    local status
                    status=$(echo "$state" | jq -r '.status // "unknown"')

                    if [[ "$status" != "completed" && "$status" != "failed" ]]; then
                        all_done=false
                        break
                    fi
                done

                if [[ "$all_done" == "true" ]]; then
                    log_agent "INFO" "P2-SYNC" "All agents completed"

                    # Collect results
                    for agent_id in $agent_ids; do
                        local state
                        state=$(get_agent_state "$agent_id")
                        local status
                        status=$(echo "$state" | jq -r '.status // "unknown"')

                        agent_results+=("$state")

                        if [[ "$status" == "failed" ]]; then
                            all_completed=false
                        fi
                    done
                    break
                fi

                sleep $wait_interval
                elapsed=$((elapsed + wait_interval))
            done

            if [[ $elapsed -ge $max_wait ]]; then
                log_agent "WARN" "P2-SYNC" "Barrier timeout reached"
                all_completed=false
            fi
            ;;

        *)
            log_agent "ERROR" "P2-SYNC" "Invalid wait strategy: ${wait_strategy}"
            echo "ERROR: Invalid wait strategy: ${wait_strategy}" >&2
            return 1
            ;;
    esac

    # Build result JSON
    local results_json
    results_json=$(printf '%s\n' "${agent_results[@]}" | jq -s '.')

    jq -n \
        --arg status "$(if [[ "$all_completed" == "true" ]]; then echo "completed"; else echo "partial"; fi)" \
        --arg strategy "$wait_strategy" \
        --argjson results "$results_json" \
        '{
            status: $status,
            strategy: $strategy,
            agent_results: $results
        }'
}

# ============================================================================
# RESULT AGGREGATION
# ============================================================================

# Aggregate results from multiple agents
# Args:
#   $1 - results_array: JSON array of agent results
#   $2 - strategy: Aggregation strategy
#        - merge: Concatenate all results
#        - vote: Majority voting (requires consistent result format)
#        - consensus: Require all agents to agree
# Output:
#   JSON: {"status": "success", "aggregated_result": "..."}
result_aggregation() {
    local results_array_json="$1"
    local strategy="${2:-merge}"

    log_agent "INFO" "P2-AGGREGATE" "Aggregating results with strategy: ${strategy}"

    # Parse results
    local result_count
    result_count=$(echo "$results_array_json" | jq 'length')

    if [[ "$result_count" -eq 0 ]]; then
        log_agent "WARN" "P2-AGGREGATE" "No results to aggregate"
        echo '{"status": "no_results", "aggregated_result": null}'
        return 0
    fi

    local aggregated_result=""
    local aggregation_status="success"

    case "$strategy" in
        merge)
            # Concatenate all results
            log_agent "INFO" "P2-AGGREGATE" "Merge strategy: concatenating ${result_count} results"

            local merged=""
            for i in $(seq 0 $((result_count - 1))); do
                local result
                result=$(echo "$results_array_json" | jq -r ".[$i].output // \"\"")

                if [[ -n "$result" ]]; then
                    if [[ -n "$merged" ]]; then
                        merged="${merged}\n\n---\n\n${result}"
                    else
                        merged="$result"
                    fi
                fi
            done

            aggregated_result="$merged"
            ;;

        vote)
            # Majority voting on results
            log_agent "INFO" "P2-AGGREGATE" "Vote strategy: majority voting on ${result_count} results"

            # Count occurrences of each unique result
            declare -A result_votes

            for i in $(seq 0 $((result_count - 1))); do
                local result
                result=$(echo "$results_array_json" | jq -r ".[$i].output // \"unknown\"")

                result_votes["$result"]=$((${result_votes["$result"]:-0} + 1))
            done

            # Find result with most votes
            local max_votes=0
            local winning_result=""

            for result in "${!result_votes[@]}"; do
                if [[ ${result_votes[$result]} -gt $max_votes ]]; then
                    max_votes=${result_votes[$result]}
                    winning_result="$result"
                fi
            done

            aggregated_result="$winning_result (${max_votes}/${result_count} votes)"

            # Check if majority reached (>50%)
            if [[ $max_votes -le $((result_count / 2)) ]]; then
                aggregation_status="no_majority"
                log_agent "WARN" "P2-AGGREGATE" "No majority: ${max_votes}/${result_count}"
            fi
            ;;

        consensus)
            # Require all agents to agree
            log_agent "INFO" "P2-AGGREGATE" "Consensus strategy: checking agreement on ${result_count} results"

            local first_result
            first_result=$(echo "$results_array_json" | jq -r '.[0].output // ""')

            local all_agree=true
            for i in $(seq 1 $((result_count - 1))); do
                local current_result
                current_result=$(echo "$results_array_json" | jq -r ".[$i].output // \"\"")

                if [[ "$current_result" != "$first_result" ]]; then
                    all_agree=false
                    break
                fi
            done

            if [[ "$all_agree" == "true" ]]; then
                aggregated_result="$first_result"
                log_agent "INFO" "P2-AGGREGATE" "Consensus reached"
            else
                aggregation_status="no_consensus"
                aggregated_result="No consensus: agents provided different results"
                log_agent "WARN" "P2-AGGREGATE" "No consensus reached"
            fi
            ;;

        *)
            log_agent "ERROR" "P2-AGGREGATE" "Invalid aggregation strategy: ${strategy}"
            echo "ERROR: Invalid aggregation strategy: ${strategy}" >&2
            return 1
            ;;
    esac

    # Return aggregated result
    jq -n \
        --arg status "$aggregation_status" \
        --arg strategy "$strategy" \
        --arg result "$aggregated_result" \
        --argjson count "$result_count" \
        '{
            status: $status,
            strategy: $strategy,
            result_count: $count,
            aggregated_result: $result
        }'
}

# ============================================================================
# COMPLEXITY-BASED AGENT COUNT
# ============================================================================

# Get recommended agent count based on complexity level
# Args:
#   $1 - complexity_level: Complexity level (simple, moderate, complex, very_complex)
# Output:
#   Integer: Number of agents (2-5)
get_agent_count_by_complexity() {
    local complexity_level="$1"

    log_agent "INFO" "P2-COMPLEXITY" "Getting agent count for complexity: ${complexity_level}"

    # Normalize input (lowercase, remove spaces)
    complexity_level=$(echo "$complexity_level" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

    # Map complexity to agent count
    local agent_count="${COMPLEXITY_AGENT_COUNT[$complexity_level]:-3}"

    log_agent "INFO" "P2-COMPLEXITY" "Agent count: ${agent_count} for ${complexity_level}"

    echo "$agent_count"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Clean up agent state (for testing/reset)
cleanup_agent_state() {
    local agent_id="${1:-}"

    if [[ -n "$agent_id" ]]; then
        # Clean specific agent
        local agent_state_file="${AGENT_STATE_DIR}/${agent_id}.json"
        if [[ -f "$agent_state_file" ]]; then
            rm -f "$agent_state_file"
            log_agent "INFO" "P2-CLEANUP" "Cleaned agent state: ${agent_id}"
        fi
    else
        # Clean all agents
        rm -rf "${AGENT_STATE_DIR:?}"/*
        log_agent "INFO" "P2-CLEANUP" "Cleaned all agent state"
    fi
}

# List active agents
list_active_agents() {
    if [[ ! -d "$AGENT_STATE_DIR" ]] || [[ -z "$(ls -A "$AGENT_STATE_DIR" 2>/dev/null)" ]]; then
        echo '{"active_agents": []}'
        return 0
    fi

    local agents=()
    for state_file in "$AGENT_STATE_DIR"/*.json; do
        if [[ -f "$state_file" ]]; then
            agents+=("$(cat "$state_file")")
        fi
    done

    printf '%s\n' "${agents[@]}" | jq -s '{active_agents: .}'
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f parallel_agent_spawn
export -f agent_synchronization
export -f result_aggregation
export -f get_agent_count_by_complexity
export -f update_agent_state
export -f get_agent_state
export -f cleanup_agent_state
export -f list_active_agents
export -f log_agent

# ============================================================================
# SELF-TEST (Optional - for development)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Parallel Agent Self-Test ==="

    # Test 1: Spawn agent
    echo "Test 1: parallel_agent_spawn"
    agent_config='{"agent_type":"research","prompt":"Test task","description":"Test agent"}'
    agent_id=$(parallel_agent_spawn "$agent_config")
    echo "  Agent ID: $agent_id"
    [[ -n "$agent_id" ]] && echo "  ✅ PASS" || echo "  ❌ FAIL"

    # Test 2: Get agent state
    echo "Test 2: get_agent_state"
    state=$(get_agent_state "$agent_id")
    echo "  State: $state"
    status=$(echo "$state" | jq -r '.status')
    [[ "$status" == "spawned" ]] && echo "  ✅ PASS" || echo "  ❌ FAIL"

    # Test 3: Agent count by complexity
    echo "Test 3: get_agent_count_by_complexity"
    for level in simple moderate complex very_complex; do
        count=$(get_agent_count_by_complexity "$level")
        expected="${COMPLEXITY_AGENT_COUNT[$level]}"
        echo "  $level: $count (expected: $expected)"
        [[ "$count" -eq "$expected" ]] && echo "  ✅ PASS" || echo "  ❌ FAIL"
    done

    # Test 4: Result aggregation (merge)
    echo "Test 4: result_aggregation (merge)"
    results='[{"output":"Result A"},{"output":"Result B"}]'
    aggregated=$(result_aggregation "$results" "merge")
    echo "  Aggregated: $aggregated"
    status=$(echo "$aggregated" | jq -r '.status')
    [[ "$status" == "success" ]] && echo "  ✅ PASS" || echo "  ❌ FAIL"

    # Test 5: List active agents
    echo "Test 5: list_active_agents"
    active=$(list_active_agents)
    count=$(echo "$active" | jq '.active_agents | length')
    echo "  Active agents: $count"
    [[ "$count" -gt 0 ]] && echo "  ✅ PASS" || echo "  ❌ FAIL"

    # Cleanup
    echo "Test 6: cleanup_agent_state"
    cleanup_agent_state "$agent_id"
    state=$(get_agent_state "$agent_id")
    status=$(echo "$state" | jq -r '.status')
    [[ "$status" == "not_found" ]] && echo "  ✅ PASS" || echo "  ❌ FAIL"

    echo "=== All self-tests completed ==="
fi
