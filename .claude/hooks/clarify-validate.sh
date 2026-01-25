#!/bin/bash
# ============================================================================
# Clarify Validation Hook - Gate 1: Requirement Feasibility
# Version: 1.0.0
# ============================================================================
#
# Triggered by: /clarify skill Stop hook
# Purpose: Validate requirement feasibility before proceeding
# Exit Codes: 0 = passed, 1 = failed, 2 = warning
#
# ============================================================================

set -euo pipefail

# Source validation gates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "${WORKSPACE_ROOT}/.claude/skills/shared/validation-gates.sh"

# ============================================================================
# MAIN
# ============================================================================

# Extract requirement from clarify output
CLARIFY_OUTPUT="${1:-}"

if [[ -z "$CLARIFY_OUTPUT" ]]; then
    echo "⚠️  No clarify output provided to validation hook"
    exit 0
fi

# Find the most recent clarify YAML file
LATEST_CLARIFY=$(ls -t .agent/clarify/*.yaml 2>/dev/null | head -n 1)

if [[ -z "$LATEST_CLARIFY" || ! -f "$LATEST_CLARIFY" ]]; then
    echo "⚠️  No clarify YAML file found, skipping validation"
    exit 0
fi

# Extract approved prompt from YAML
APPROVED_PROMPT=$(grep -A 10000 'approved_prompt:' "$LATEST_CLARIFY" | sed '1d; /^[a-z]/q' | sed '$d' || echo "")

if [[ -z "$APPROVED_PROMPT" ]]; then
    echo "⚠️  No approved prompt found in clarify output"
    exit 0
fi

# Run validation
echo "🔍 Running Gate 1: Requirement Feasibility Validation"
echo "=================================================="

VALIDATION_RESULT=$(validate_requirement_feasibility "$APPROVED_PROMPT")

# Parse result
RESULT_STATUS=$(echo "$VALIDATION_RESULT" | jq -r '.result')
WARNINGS=$(echo "$VALIDATION_RESULT" | jq -r '.warnings[]' 2>/dev/null || echo "")
ERRORS=$(echo "$VALIDATION_RESULT" | jq -r '.errors[]' 2>/dev/null || echo "")

# Display results
echo ""
echo "Validation Result: $RESULT_STATUS"

if [[ -n "$WARNINGS" ]]; then
    echo ""
    echo "⚠️  Warnings:"
    echo "$WARNINGS" | while IFS= read -r warning; do
        echo "  - $warning"
    done
fi

if [[ -n "$ERRORS" ]]; then
    echo ""
    echo "❌ Errors:"
    echo "$ERRORS" | while IFS= read -r error; do
        echo "  - $error"
    done
fi

echo ""

# Exit based on result
case "$RESULT_STATUS" in
    passed)
        echo "✅ Gate 1 PASSED - Requirements are feasible"
        exit 0
        ;;
    passed_with_warnings)
        echo "⚠️  Gate 1 PASSED WITH WARNINGS - Review recommended"
        echo ""
        echo "You can proceed, but please review the warnings above."
        exit 0
        ;;
    failed)
        echo "❌ Gate 1 FAILED - Requirements need clarification"
        echo ""
        echo "Please address the errors above and run /clarify again."
        exit 1
        ;;
    *)
        echo "⚠️  Unknown validation result: $RESULT_STATUS"
        exit 0
        ;;
esac
