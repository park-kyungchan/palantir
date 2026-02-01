#!/bin/bash
# ============================================================================
# Research Validation Hook - Gate 2: Argument + Scope Validation
# Version: 2.0.0
# ============================================================================
#
# Triggered by: /research skill Setup hook (before execution)
# Purpose:
#   1. Validate required arguments (query)
#   2. Validate scope access
# Exit Codes: 0 = passed, 1 = failed (blocks skill execution)
#
# ============================================================================

set -euo pipefail

# Source validation gates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# Safely source validation gates if exists
if [[ -f "${WORKSPACE_ROOT}/.claude/skills/shared/validation-gates.sh" ]]; then
    source "${WORKSPACE_ROOT}/.claude/skills/shared/validation-gates.sh"
fi

# ============================================================================
# ARGUMENT VALIDATION (Gate 2-A)
# ============================================================================

show_usage() {
    cat << 'EOF'
Usage: /research [OPTIONS] <query>

Arguments:
  <query>                Research topic or question (REQUIRED)

Options:
  --scope <path>         Limit research to specific directory
  --external             Include external resource gathering (WebSearch)
  --clarify-slug <slug>  Link to upstream /clarify workload
  --help, -h             Show this help message

Examples:
  /research "authentication patterns"
  /research --scope src/auth/ "OAuth2 implementation"
  /research --external --clarify-slug user-auth-20260129 "JWT refresh"

Pipeline Position:
  /clarify → /research → /planning
EOF
}

# Get skill arguments
ARGS="${SKILL_ARGUMENTS:-$*}"

# Check for help flag
if echo "$ARGS" | grep -qE '(--help|-h)'; then
    show_usage
    exit 1  # Block execution, show help
fi

# Extract query (non-option argument)
QUERY=$(echo "$ARGS" | sed -E 's/--scope\s+[^\s]+//g; s/--clarify-slug\s+[^\s]+//g; s/--external//g' | xargs)

# Validate: Query is required
if [[ -z "$QUERY" ]]; then
    echo "❌ Gate 2-A FAILED: Research query is required"
    echo ""
    show_usage
    echo ""
    echo "Skill execution blocked. Please provide a research query."
    exit 1
fi

echo "✅ Gate 2-A PASSED: Query provided"
echo "   Query: $QUERY"
echo ""

# ============================================================================
# SCOPE VALIDATION (Gate 2-B)
# ============================================================================

# Extract scope from arguments
SCOPE=""
if echo "$ARGS" | grep -qE '--scope\s+'; then
    SCOPE=$(echo "$ARGS" | grep -oP '(?<=--scope\s)[^\s]+' || echo "")
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
