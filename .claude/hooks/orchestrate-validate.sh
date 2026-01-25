#!/bin/bash
# ============================================================================
# Orchestrate Validation Hook
# Version: 1.0.0
# ============================================================================
#
# Gate 4 validation for /orchestrate skill
# Runs validate_phase_dependencies() before Task creation
#
# Usage: Called automatically before orchestration
#        Or manually: ./orchestrate-validate.sh '<phases_json>'
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# Source validation gates
VALIDATION_GATES="${WORKSPACE_ROOT}/.claude/skills/shared/validation-gates.sh"

if [[ ! -f "$VALIDATION_GATES" ]]; then
    echo "ERROR: Validation gates not found: $VALIDATION_GATES"
    exit 1
fi

source "$VALIDATION_GATES"

# ============================================================================
# MAIN
# ============================================================================

main() {
    local phases_json="$1"

    echo "=== Gate 4: Orchestrate Phase Dependency Validation ==="
    echo ""

    # 1. Check if phases JSON is provided
    if [[ -z "$phases_json" ]]; then
        echo "⚠️  No phases JSON provided."
        echo "   Usage: ./orchestrate-validate.sh '<phases_json>'"
        echo ""
        echo "   Example:"
        echo '   ./orchestrate-validate.sh '\''[{"id":"phase1","dependencies":[]},{"id":"phase2","dependencies":["phase1"]}]'\'''
        exit 0
    fi

    # 2. Validate JSON format
    if ! echo "$phases_json" | jq . >/dev/null 2>&1; then
        echo "❌ Invalid JSON format"
        exit 1
    fi

    # 3. Run validate_phase_dependencies
    echo "Running phase dependency validation..."
    echo ""

    result=$(validate_phase_dependencies "$phases_json")

    # 4. Parse result
    status=$(echo "$result" | jq -r '.result' 2>/dev/null || echo "unknown")
    warnings=$(echo "$result" | jq -r '.warnings[]' 2>/dev/null || true)
    errors=$(echo "$result" | jq -r '.errors[]' 2>/dev/null || true)

    # 5. Display results
    echo "$result" | jq . 2>/dev/null || echo "$result"
    echo ""

    case "$status" in
        "passed")
            echo "✅ Gate 4 PASSED: Phase dependencies validated"
            echo "   → Proceeding to Task creation"
            exit 0
            ;;
        "passed_with_warnings")
            echo "⚠️  Gate 4 PASSED WITH WARNINGS:"
            echo "$warnings" | while read -r warning; do
                [[ -n "$warning" ]] && echo "   - $warning"
            done
            echo ""
            echo "   → Proceeding to Task creation (review warnings)"
            exit 0
            ;;
        "failed")
            echo "❌ Gate 4 FAILED:"
            echo "$errors" | while read -r error; do
                [[ -n "$error" ]] && echo "   - $error"
            done
            echo ""
            echo "   → Fix errors before creating Tasks"
            exit 1
            ;;
        *)
            echo "⚠️  Gate 4: Unknown status - $status"
            echo "   → Proceeding with caution"
            exit 0
            ;;
    esac
}

# ============================================================================
# ADDITIONAL VALIDATIONS
# ============================================================================

# Detect duplicate phase IDs
detect_duplicate_ids() {
    local phases_json="$1"

    local duplicates
    duplicates=$(echo "$phases_json" | jq -r '.[].id' | sort | uniq -d)

    if [[ -n "$duplicates" ]]; then
        echo "Duplicate IDs found: $duplicates"
        return 1
    fi

    return 0
}

# Detect undefined dependencies
detect_undefined_deps() {
    local phases_json="$1"

    local phase_ids
    phase_ids=$(echo "$phases_json" | jq -r '.[].id')

    local all_deps
    all_deps=$(echo "$phases_json" | jq -r '.[].dependencies[]?' || true)

    local undefined=()

    while IFS= read -r dep; do
        [[ -z "$dep" ]] && continue
        if ! echo "$phase_ids" | grep -q "^${dep}$"; then
            undefined+=("$dep")
        fi
    done <<< "$all_deps"

    if [[ ${#undefined[@]} -gt 0 ]]; then
        printf '%s\n' "${undefined[@]}"
        return 1
    fi

    return 0
}

# Validate from planning document
validate_from_plan() {
    local plan_path="$1"

    if [[ ! -f "$plan_path" ]]; then
        echo "Planning document not found: $plan_path"
        exit 1
    fi

    # Extract phases from YAML and convert to JSON
    # This is a simplified extraction - real implementation should use yq
    local phases_json
    phases_json=$(python3 -c "
import yaml
import json
import sys

with open('$plan_path', 'r') as f:
    doc = yaml.safe_load(f)

phases = doc.get('phases', [])
result = []
for p in phases:
    result.append({
        'id': p.get('id', ''),
        'dependencies': p.get('dependencies', [])
    })
print(json.dumps(result))
" 2>/dev/null || echo "[]")

    main "$phases_json"
}

# Run main with all arguments
if [[ "$1" == "--from-plan" ]]; then
    validate_from_plan "$2"
else
    main "$@"
fi
