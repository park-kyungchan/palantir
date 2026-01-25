#!/bin/bash
# ============================================================================
# Shift-Left E2E Integration Test
# Version: 1.0.0
# ============================================================================
#
# Tests all 5 validation gates with various scenarios
# Exit: 0 = all passed, 1 = some failed
#
# ============================================================================

set -uo pipefail
# Note: Not using 'set -e' to allow test assertions to continue on failure

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
TOTAL=0

# Source validation gates
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
source "${WORKSPACE_ROOT}/.claude/skills/shared/validation-gates.sh"

# ============================================================================
# TEST HELPERS
# ============================================================================

log_test() {
    local test_name="$1"
    ((TOTAL++))
    echo -e "${BLUE}[TEST $TOTAL]${NC} $test_name"
}

assert_result() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    if [[ "$actual" == "$expected" ]]; then
        echo -e "  ${GREEN}✓ PASSED${NC} - Expected '$expected', got '$expected'"
        ((PASSED++))
        return 0
    else
        echo -e "  ${RED}✗ FAILED${NC} - Expected '$expected', got '$actual'"
        ((FAILED++))
        return 1
    fi
}

assert_contains() {
    local needle="$1"
    local haystack="$2"
    local test_name="$3"

    if echo "$haystack" | grep -q "$needle"; then
        echo -e "  ${GREEN}✓ PASSED${NC} - Output contains '$needle'"
        ((PASSED++))
        return 0
    else
        echo -e "  ${RED}✗ FAILED${NC} - Output does not contain '$needle'"
        ((FAILED++))
        return 1
    fi
}

# ============================================================================
# TEST 1: Gate 1 (Clarify) - Requirement Feasibility
# ============================================================================

echo ""
echo "=============================================="
echo "GATE 1: Clarify - Requirement Feasibility"
echo "=============================================="

# Test 1.1: Very brief requirement (should warn)
log_test "Very brief requirement should produce warning"
RESULT=$(validate_requirement_feasibility "Fix bug")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed_with_warnings" "$STATUS" "Brief requirement warning" || true

# Test 1.2: Normal requirement (should pass)
log_test "Normal requirement should pass"
RESULT=$(validate_requirement_feasibility "Implement user authentication with JWT tokens for the API endpoints in the backend service")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed" "$STATUS" "Normal requirement passes" || true

# Test 1.3: Requirement with non-existent file reference (should warn)
log_test "Reference to non-existent file should produce warning"
RESULT=$(validate_requirement_feasibility "Update the code in nonexistent-file-abc123.ts to fix the issue")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed_with_warnings" "$STATUS" "Non-existent file warning" || true

# ============================================================================
# TEST 2: Gate 2 (Research) - Scope Access Validation
# ============================================================================

echo ""
echo "=============================================="
echo "GATE 2: Research - Scope Access Validation"
echo "=============================================="

# Test 2.1: Non-existent scope path (should fail)
log_test "Non-existent scope path should fail"
RESULT=$(validate_scope_access "nonexistent/path/that/does/not/exist")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "failed" "$STATUS" "Non-existent path fails" || true

# Test 2.2: Existing scope path (should pass)
log_test "Existing scope path should pass"
RESULT=$(validate_scope_access ".claude/skills")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed" "$STATUS" "Existing path passes" || true

# Test 2.3: Very broad scope (should warn)
log_test "Very broad scope should produce warning"
RESULT=$(validate_scope_access ".")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed_with_warnings" "$STATUS" "Broad scope warning" || true

# ============================================================================
# TEST 3: Gate 3 (Planning) - Pre-flight Checks
# ============================================================================

echo ""
echo "=============================================="
echo "GATE 3: Planning - Pre-flight Checks"
echo "=============================================="

# Create temporary test files
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Test 3.1: Non-existent planning document (should fail)
log_test "Non-existent planning document should fail"
RESULT=$(pre_flight_checks "${TEMP_DIR}/nonexistent.yaml")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "failed" "$STATUS" "Missing planning doc fails" || true

# Test 3.2: Valid planning document (should pass)
log_test "Valid planning document should pass"
cat > "${TEMP_DIR}/valid-plan.yaml" << 'EOF'
phases:
  - id: phase1
    targetFiles:
      - path: ".claude/skills/shared/validation-gates.sh"
EOF
RESULT=$(pre_flight_checks "${TEMP_DIR}/valid-plan.yaml")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed" "$STATUS" "Valid plan passes" || true

# Test 3.3: Planning doc with invalid target paths (should warn)
log_test "Planning doc with invalid target paths should warn"
cat > "${TEMP_DIR}/invalid-paths.yaml" << 'EOF'
phases:
  - id: phase1
    targetFiles:
      - path: "nonexistent/deeply/nested/dir/file.ts"
EOF
RESULT=$(pre_flight_checks "${TEMP_DIR}/invalid-paths.yaml")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed_with_warnings" "$STATUS" "Invalid target path warns" || true

# ============================================================================
# TEST 4: Gate 4 (Orchestrate) - Dependency Validation
# ============================================================================

echo ""
echo "=============================================="
echo "GATE 4: Orchestrate - Dependency Validation"
echo "=============================================="

# Test 4.1: Duplicate phase IDs (should fail)
log_test "Duplicate phase IDs should fail"
PHASES_JSON='[{"id":"phase1","dependencies":[]},{"id":"phase1","dependencies":[]}]'
RESULT=$(validate_phase_dependencies "$PHASES_JSON")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "failed" "$STATUS" "Duplicate IDs fail" || true

# Test 4.2: Undefined dependency (should fail)
log_test "Undefined dependency should fail"
PHASES_JSON='[{"id":"phase1","dependencies":[]},{"id":"phase2","dependencies":["phase99"]}]'
RESULT=$(validate_phase_dependencies "$PHASES_JSON")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "failed" "$STATUS" "Undefined dependency fails" || true

# Test 4.3: Valid dependencies (should pass)
log_test "Valid dependencies should pass"
PHASES_JSON='[{"id":"phase1","dependencies":[]},{"id":"phase2","dependencies":["phase1"]}]'
RESULT=$(validate_phase_dependencies "$PHASES_JSON")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed" "$STATUS" "Valid dependencies pass" || true

# Test 4.4: Large number of phases (should warn)
log_test "Large number of phases should produce warning"
PHASES_JSON='['
for i in {1..12}; do
    [[ $i -gt 1 ]] && PHASES_JSON+=','
    PHASES_JSON+="{\"id\":\"phase${i}\",\"dependencies\":[]}"
done
PHASES_JSON+=']'
RESULT=$(validate_phase_dependencies "$PHASES_JSON")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed_with_warnings" "$STATUS" "Large phase count warns" || true

# ============================================================================
# TEST 5: Gate 5 (Worker) - Pre-execution Gate
# ============================================================================

echo ""
echo "=============================================="
echo "GATE 5: Worker - Pre-execution Gate"
echo "=============================================="

# Test 5.1: Non-existent task file (should fail)
log_test "Non-existent task file should fail"
RESULT=$(pre_execution_gate "task-1" "${TEMP_DIR}/nonexistent-task.yaml")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "failed" "$STATUS" "Missing task file fails" || true

# Test 5.2: Valid task with writable targets (should pass)
log_test "Valid task with writable targets should pass"
cat > "${TEMP_DIR}/valid-task.yaml" << 'EOF'
taskId: "1"
targetFiles:
  - path: ".claude/CLAUDE.md"
EOF
RESULT=$(pre_execution_gate "task-1" "${TEMP_DIR}/valid-task.yaml")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed" "$STATUS" "Valid task passes" || true

# Test 5.3: Task without file (should pass - no file to validate)
log_test "Task without file specified should pass"
RESULT=$(pre_execution_gate "task-1" "")
STATUS=$(echo "$RESULT" | jq -r '.result')
assert_result "passed" "$STATUS" "No file task passes" || true

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "=============================================="
echo "TEST SUMMARY"
echo "=============================================="
echo -e "Total Tests: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}"
    exit 1
fi
