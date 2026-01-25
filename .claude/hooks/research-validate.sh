#!/bin/bash
# ============================================================================
# Research Validation Hook - Gate 2: Scope Access Validation
# Version: 1.0.0
# ============================================================================
#
# Triggered by: /research skill Setup hook (before execution)
# Purpose: Validate scope access before starting research
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

# Extract scope from arguments
SCOPE="${1:-}"

if [[ -z "$SCOPE" ]]; then
    # Try to extract from skill arguments
    if [[ -n "${SKILL_ARGUMENTS:-}" ]]; then
        # Parse --scope argument
        SCOPE=$(echo "$SKILL_ARGUMENTS" | grep -oP '(?<=--scope\s)[^\s]+' || echo "")
    fi
fi

# If no scope provided, default to current directory (broad scope warning)
if [[ -z "$SCOPE" ]]; then
    SCOPE="."
fi

# Run validation
echo "🔍 Running Gate 2: Scope Access Validation"
echo "=========================================="
echo "Scope: $SCOPE"
echo ""

VALIDATION_RESULT=$(validate_scope_access "$SCOPE")

# Parse result
RESULT_STATUS=$(echo "$VALIDATION_RESULT" | jq -r '.result')
WARNINGS=$(echo "$VALIDATION_RESULT" | jq -r '.warnings[]' 2>/dev/null || echo "")
ERRORS=$(echo "$VALIDATION_RESULT" | jq -r '.errors[]' 2>/dev/null || echo "")

# Display results
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
        echo "✅ Gate 2 PASSED - Scope is accessible"
        exit 0
        ;;
    passed_with_warnings)
        echo "⚠️  Gate 2 PASSED WITH WARNINGS - Consider narrowing scope"
        echo ""
        echo "Research will proceed, but consider specifying a more focused scope."
        exit 0
        ;;
    failed)
        echo "❌ Gate 2 FAILED - Scope is not accessible"
        echo ""
        echo "Please check the scope path and try again:"
        echo "  /research --scope <valid-path> \"your query\""
        exit 1
        ;;
    *)
        echo "⚠️  Unknown validation result: $RESULT_STATUS"
        exit 0
        ;;
esac
