#!/bin/bash
# ============================================================================
# Validation Metrics Collector
# Version: 1.0.0
# ============================================================================
#
# Collects and aggregates Shift-Left validation metrics from gate logs.
#
# Usage:
#   ./validation-metrics.sh              # Show current metrics
#   ./validation-metrics.sh --json       # Output as JSON
#   ./validation-metrics.sh --update     # Update _progress.yaml
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# Log and output paths
VALIDATION_LOG="${WORKSPACE_ROOT}/.agent/logs/validation_gates.log"
PROGRESS_FILE="${WORKSPACE_ROOT}/.agent/prompts/_progress.yaml"

# ============================================================================
# METRICS COLLECTION
# ============================================================================

collect_gate_metrics() {
    local gate="$1"

    # Handle missing log file gracefully
    if [[ ! -f "$VALIDATION_LOG" ]]; then
        echo '{"passed":0,"passed_with_warnings":0,"failed":0,"total":0}'
        return
    fi

    local passed passed_with_warnings failed

    # Count results by gate (handle grep returning nothing)
    passed=$(grep -c "\[${gate}\].*Result: passed$" "$VALIDATION_LOG" 2>/dev/null) || passed=0
    passed_with_warnings=$(grep -c "\[${gate}\].*Result: passed_with_warnings" "$VALIDATION_LOG" 2>/dev/null) || passed_with_warnings=0
    failed=$(grep -c "\[${gate}\].*Result: failed" "$VALIDATION_LOG" 2>/dev/null) || failed=0

    # Ensure numeric values
    passed=${passed:-0}
    passed_with_warnings=${passed_with_warnings:-0}
    failed=${failed:-0}

    local total=$((passed + passed_with_warnings + failed))

    cat <<EOF
{"passed":${passed},"passed_with_warnings":${passed_with_warnings},"failed":${failed},"total":${total}}
EOF
}

collect_all_metrics() {
    local gates=("GATE1-CLARIFY" "GATE2-RESEARCH" "GATE3-PLANNING" "GATE4-ORCHESTRATE" "GATE5-WORKER")

    local total_passed=0
    local total_warnings=0
    local total_failed=0
    local total_runs=0

    echo "{"
    echo '  "gates": {'

    for i in "${!gates[@]}"; do
        local gate="${gates[$i]}"
        local metrics
        metrics=$(collect_gate_metrics "$gate")

        local p w f t
        p=$(echo "$metrics" | jq -r '.passed')
        w=$(echo "$metrics" | jq -r '.passed_with_warnings')
        f=$(echo "$metrics" | jq -r '.failed')
        t=$(echo "$metrics" | jq -r '.total')

        total_passed=$((total_passed + p))
        total_warnings=$((total_warnings + w))
        total_failed=$((total_failed + f))
        total_runs=$((total_runs + t))

        # Gate name without prefix
        local gate_name="${gate#GATE?-}"
        gate_name=$(echo "$gate_name" | tr '[:upper:]' '[:lower:]')

        echo "    \"${gate_name}\": ${metrics}$([ $i -lt $((${#gates[@]} - 1)) ] && echo ',')"
    done

    echo '  },'

    # Calculate Shift-Left Ratio
    local shift_left_ratio="0.00"
    if [[ $total_runs -gt 0 ]]; then
        # Early detection = problems found at gates before synthesis
        local early_detected=$((total_warnings + total_failed))
        shift_left_ratio=$(echo "scale=2; ($early_detected * 100) / $total_runs" | bc 2>/dev/null || echo "0.00")
    fi

    # Calculate Prevention Rate
    local prevention_rate="0.00"
    if [[ $total_runs -gt 0 ]]; then
        prevention_rate=$(echo "scale=2; ($total_failed * 100) / $total_runs" | bc 2>/dev/null || echo "0.00")
    fi

    # Calculate Success Rate
    local success_rate="100.00"
    if [[ $total_runs -gt 0 ]]; then
        success_rate=$(echo "scale=2; ($total_passed * 100) / $total_runs" | bc 2>/dev/null || echo "100.00")
    fi

    cat <<EOF
  "summary": {
    "total_runs": ${total_runs},
    "passed": ${total_passed},
    "warnings": ${total_warnings},
    "failed": ${total_failed}
  },
  "indicators": {
    "success_rate": ${success_rate},
    "shift_left_ratio": ${shift_left_ratio},
    "prevention_rate": ${prevention_rate}
  },
  "collected_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

display_dashboard() {
    local metrics
    metrics=$(collect_all_metrics)

    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║           SHIFT-LEFT VALIDATION METRICS DASHBOARD              ║"
    echo "╠════════════════════════════════════════════════════════════════╣"
    echo "║                                                                ║"

    # Gate metrics
    echo "║  Gate Metrics:                                                 ║"
    echo "║  ───────────────────────────────────────────────────────────   ║"

    for gate in clarify research planning orchestrate worker; do
        local gate_data
        gate_data=$(echo "$metrics" | jq -r ".gates.${gate}")

        if [[ "$gate_data" != "null" ]]; then
            local p w f t
            p=$(echo "$gate_data" | jq -r '.passed')
            w=$(echo "$gate_data" | jq -r '.passed_with_warnings')
            f=$(echo "$gate_data" | jq -r '.failed')
            t=$(echo "$gate_data" | jq -r '.total')

            # Calculate success percentage
            local pct="--"
            if [[ $t -gt 0 ]]; then
                pct=$(echo "scale=0; ($p * 100) / $t" | bc 2>/dev/null || echo "--")
            fi

            printf "║  %-12s │ ✅ %-3s │ ⚠️  %-3s │ ❌ %-3s │ %3s%%       ║\n" \
                   "${gate^^}" "$p" "$w" "$f" "$pct"
        fi
    done

    echo "║                                                                ║"
    echo "╠════════════════════════════════════════════════════════════════╣"

    # Summary metrics
    local total_runs passed warnings failed
    total_runs=$(echo "$metrics" | jq -r '.summary.total_runs')
    passed=$(echo "$metrics" | jq -r '.summary.passed')
    warnings=$(echo "$metrics" | jq -r '.summary.warnings')
    failed=$(echo "$metrics" | jq -r '.summary.failed')

    echo "║  Summary:                                                      ║"
    printf "║    Total Validations: %-6s                                   ║\n" "$total_runs"
    printf "║    Passed:           %-6s (✅)                               ║\n" "$passed"
    printf "║    Warnings:         %-6s (⚠️ )                               ║\n" "$warnings"
    printf "║    Failed:           %-6s (❌)                               ║\n" "$failed"

    echo "║                                                                ║"
    echo "╠════════════════════════════════════════════════════════════════╣"

    # Key indicators
    local success_rate shift_left_ratio prevention_rate
    success_rate=$(echo "$metrics" | jq -r '.indicators.success_rate')
    shift_left_ratio=$(echo "$metrics" | jq -r '.indicators.shift_left_ratio')
    prevention_rate=$(echo "$metrics" | jq -r '.indicators.prevention_rate')

    echo "║  Key Indicators:                                               ║"
    printf "║    Success Rate:      %6s%%                                  ║\n" "$success_rate"
    printf "║    Shift-Left Ratio:  %6s%% (early detection rate)           ║\n" "$shift_left_ratio"
    printf "║    Prevention Rate:   %6s%% (blocked before execution)       ║\n" "$prevention_rate"

    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"

    # Timestamp
    local collected_at
    collected_at=$(echo "$metrics" | jq -r '.collected_at')
    echo "  Collected: $collected_at"
}

# ============================================================================
# UPDATE PROGRESS FILE
# ============================================================================

update_progress_file() {
    local metrics
    metrics=$(collect_all_metrics)

    if [[ ! -f "$PROGRESS_FILE" ]]; then
        echo "⚠️  Progress file not found: $PROGRESS_FILE"
        return 1
    fi

    # Check if validation section already exists
    if grep -q "^validationMetrics:" "$PROGRESS_FILE" 2>/dev/null; then
        echo "ℹ️  Validation section already exists, skipping update"
        echo "   Run with --force to overwrite"
        return 0
    fi

    # Prepare YAML section
    local success_rate shift_left_ratio prevention_rate collected_at
    success_rate=$(echo "$metrics" | jq -r '.indicators.success_rate')
    shift_left_ratio=$(echo "$metrics" | jq -r '.indicators.shift_left_ratio')
    prevention_rate=$(echo "$metrics" | jq -r '.indicators.prevention_rate')
    collected_at=$(echo "$metrics" | jq -r '.collected_at')

    local total_runs passed warnings failed
    total_runs=$(echo "$metrics" | jq -r '.summary.total_runs')
    passed=$(echo "$metrics" | jq -r '.summary.passed')
    warnings=$(echo "$metrics" | jq -r '.summary.warnings')
    failed=$(echo "$metrics" | jq -r '.summary.failed')

    local validation_section
    validation_section=$(cat <<EOF

# =============================================================================
# VALIDATION METRICS (Auto-generated by validation-metrics.sh)
# =============================================================================
validationMetrics:
  lastUpdated: "${collected_at}"

  summary:
    totalRuns: ${total_runs}
    passed: ${passed}
    warnings: ${warnings}
    failed: ${failed}

  indicators:
    successRate: ${success_rate}
    shiftLeftRatio: ${shift_left_ratio}
    preventionRate: ${prevention_rate}

  gates:
EOF
)

    # Add per-gate metrics
    for gate in clarify research planning orchestrate worker; do
        local gate_data
        gate_data=$(echo "$metrics" | jq -r ".gates.${gate}")

        if [[ "$gate_data" != "null" ]]; then
            local p w f t
            p=$(echo "$gate_data" | jq -r '.passed')
            w=$(echo "$gate_data" | jq -r '.passed_with_warnings')
            f=$(echo "$gate_data" | jq -r '.failed')
            t=$(echo "$gate_data" | jq -r '.total')

            validation_section+="
    ${gate}:
      passed: ${p}
      warnings: ${w}
      failed: ${f}
      total: ${t}"
        fi
    done

    # Append to progress file (before END OF PROGRESS marker if exists)
    if grep -q "^# END OF PROGRESS" "$PROGRESS_FILE" 2>/dev/null; then
        # Insert before the end marker
        sed -i "/^# END OF PROGRESS/i\\
${validation_section}
" "$PROGRESS_FILE"
    else
        # Append to end
        echo "$validation_section" >> "$PROGRESS_FILE"
    fi

    echo "✅ Updated progress file with validation metrics"
    echo "   File: $PROGRESS_FILE"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    case "${1:-}" in
        --json)
            collect_all_metrics
            ;;
        --update)
            update_progress_file
            ;;
        --help|-h)
            echo "Usage: validation-metrics.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  (none)     Show dashboard in terminal"
            echo "  --json     Output metrics as JSON"
            echo "  --update   Update _progress.yaml with metrics"
            echo "  --help     Show this help"
            ;;
        *)
            display_dashboard
            ;;
    esac
}

main "$@"
