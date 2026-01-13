#!/bin/bash
set -e

# ============================================================================
# Phase 5: Verification Tests
# ============================================================================
# Purpose: Run tests to verify migration success
# Scope: Import tests, unit tests, integration tests
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
LOG_FILE="${PROJECT_ROOT}/.migration_backup/phase5.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Dry run mode
DRY_RUN=false
VERBOSE=false
if [[ "$1" == "--dry-run" ]] || [[ "$1" == "-n" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}[DRY-RUN MODE] Only checking test readiness${NC}"
fi
if [[ "$1" == "--verbose" ]] || [[ "$1" == "-v" ]]; then
    VERBOSE=true
fi

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${level}] ${message}"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

info() { log "INFO" "${BLUE}$1${NC}"; }
success() { log "SUCCESS" "${GREEN}$1${NC}"; }
warn() { log "WARN" "${YELLOW}$1${NC}"; }
error() { log "ERROR" "${RED}$1${NC}"; }

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0
declare -a FAILED_TESTS

# ============================================================================
# Test Helpers
# ============================================================================
run_test() {
    local test_name=$1
    local test_command=$2

    info "Running: $test_name"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Would run: $test_command"
        return 0
    fi

    if eval "$test_command" 2>&1; then
        success "PASSED: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        error "FAILED: $test_name"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$test_name")
        return 1
    fi
}

# ============================================================================
# Test 1: Import Verification
# ============================================================================
test_imports() {
    info "=== Test 1: Import Verification ==="

    # Test that lib.oda can be imported
    local import_test='
import sys
sys.path.insert(0, "'"${PROJECT_ROOT}"'")
try:
    from lib.oda.ontology import registry
    from lib.oda.ontology.storage import database
    from lib.oda.mcp import ontology_server
    print("All imports successful")
    sys.exit(0)
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
'

    run_test "lib.oda imports" "cd ${PROJECT_ROOT} && python3 -c '$import_test'"
}

# ============================================================================
# Test 2: No Old Imports Remain
# ============================================================================
test_no_old_imports() {
    info "=== Test 2: No Old Imports in lib/oda ==="

    local check_cmd="grep -r 'from scripts\\.' ${PROJECT_ROOT}/lib/oda --include='*.py' | wc -l"
    local count=$(eval "$check_cmd" 2>/dev/null || echo "0")

    if [[ "$count" == "0" ]]; then
        success "PASSED: No old 'from scripts.' imports in lib/oda"
        ((TESTS_PASSED++))
    else
        error "FAILED: Found $count old imports in lib/oda"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("No old imports check")
        grep -r "from scripts\." "${PROJECT_ROOT}/lib/oda" --include="*.py" | head -5
    fi
}

# ============================================================================
# Test 3: Module Structure
# ============================================================================
test_module_structure() {
    info "=== Test 3: Module Structure ==="

    local required_files=(
        "lib/__init__.py"
        "lib/oda/__init__.py"
        "lib/oda/ontology/__init__.py"
        "lib/oda/ontology/registry.py"
        "lib/oda/ontology/storage/__init__.py"
        "lib/oda/ontology/storage/database.py"
        "lib/oda/mcp/__init__.py"
        "lib/oda/mcp/ontology_server.py"
    )

    local all_exist=true
    for file in "${required_files[@]}"; do
        local full_path="${PROJECT_ROOT}/${file}"
        if [[ ! -f "$full_path" ]]; then
            error "Missing: $file"
            all_exist=false
        fi
    done

    if [[ "$all_exist" == "true" ]]; then
        success "PASSED: All required module files exist"
        ((TESTS_PASSED++))
    else
        error "FAILED: Some required files are missing"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Module structure")
    fi
}

# ============================================================================
# Test 4: MCP Server Startup
# ============================================================================
test_mcp_server() {
    info "=== Test 4: MCP Server Can Start ==="

    local mcp_test='
import sys
sys.path.insert(0, "'"${PROJECT_ROOT}"'")
try:
    from lib.oda.mcp.ontology_server import mcp
    print("MCP server module loaded")
    sys.exit(0)
except Exception as e:
    print(f"MCP server failed: {e}")
    sys.exit(1)
'

    run_test "MCP server module" "cd ${PROJECT_ROOT} && python3 -c '$mcp_test'"
}

# ============================================================================
# Test 5: Registry Initialization
# ============================================================================
test_registry() {
    info "=== Test 5: Registry Initialization ==="

    local registry_test='
import sys
sys.path.insert(0, "'"${PROJECT_ROOT}"'")
try:
    from lib.oda.ontology.registry import ActionRegistry
    registry = ActionRegistry()
    print(f"Registry loaded with {len(registry.list_actions())} actions")
    sys.exit(0)
except Exception as e:
    print(f"Registry failed: {e}")
    sys.exit(1)
'

    run_test "Registry initialization" "cd ${PROJECT_ROOT} && python3 -c '$registry_test'"
}

# ============================================================================
# Test 6: Database Connection
# ============================================================================
test_database() {
    info "=== Test 6: Database Connection ==="

    local db_test='
import sys
sys.path.insert(0, "'"${PROJECT_ROOT}"'")
try:
    from lib.oda.ontology.storage.database import get_connection
    conn = get_connection()
    print("Database connection successful")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"Database failed: {e}")
    sys.exit(1)
'

    run_test "Database connection" "cd ${PROJECT_ROOT} && python3 -c '$db_test'"
}

# ============================================================================
# Test 7: Unit Tests (if pytest available)
# ============================================================================
test_unit_tests() {
    info "=== Test 7: Unit Tests ==="

    if command -v pytest &> /dev/null; then
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would run: pytest ${PROJECT_ROOT}/tests/unit -v --tb=short"
        else
            cd "${PROJECT_ROOT}"
            if pytest tests/unit -v --tb=short -x 2>&1 | tee -a "$LOG_FILE"; then
                success "PASSED: Unit tests"
                ((TESTS_PASSED++))
            else
                warn "Some unit tests failed (may need import updates)"
                ((TESTS_FAILED++))
                FAILED_TESTS+=("Unit tests")
            fi
        fi
    else
        warn "pytest not found - skipping unit tests"
    fi
}

# ============================================================================
# Test 8: Syntax Check
# ============================================================================
test_syntax() {
    info "=== Test 8: Python Syntax Check ==="

    local syntax_errors=0

    while IFS= read -r -d '' file; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            error "Syntax error in: ${file#$PROJECT_ROOT/}"
            ((syntax_errors++))
        fi
    done < <(find "${PROJECT_ROOT}/lib/oda" -name "*.py" -type f -print0)

    if [[ "$syntax_errors" -eq 0 ]]; then
        success "PASSED: All Python files have valid syntax"
        ((TESTS_PASSED++))
    else
        error "FAILED: $syntax_errors files have syntax errors"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("Syntax check")
    fi
}

# ============================================================================
# Generate Test Report
# ============================================================================
generate_report() {
    info "Generating test report..."

    local report_file="${PROJECT_ROOT}/.migration_backup/phase5_report.txt"

    {
        echo "=============================================="
        echo "Phase 5: Test Results Report"
        echo "Generated: $(date)"
        echo "=============================================="
        echo ""
        echo "Summary:"
        echo "  Passed: $TESTS_PASSED"
        echo "  Failed: $TESTS_FAILED"
        echo "  Total:  $((TESTS_PASSED + TESTS_FAILED))"
        echo ""

        if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
            echo "Failed Tests:"
            for test in "${FAILED_TESTS[@]}"; do
                echo "  - $test"
            done
            echo ""
        fi

        echo "Detailed log: $LOG_FILE"
    } > "$report_file"

    cat "$report_file"
    success "Report saved to: $report_file"
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "Phase 5: Verification Tests"
    echo "=============================================="
    echo ""

    # Set PYTHONPATH
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

    test_imports
    test_no_old_imports
    test_module_structure
    test_mcp_server
    test_registry
    test_database
    test_syntax
    test_unit_tests

    echo ""
    generate_report

    echo ""
    if [[ "$TESTS_FAILED" -eq 0 ]]; then
        success "All tests passed! Migration verified successfully."
        echo ""
        info "Next step: Run migrate_phase6_symlink.sh to create compatibility symlinks"
    else
        error "$TESTS_FAILED tests failed. Please review and fix before proceeding."
        echo ""
        warn "You may need to run rollback_all.sh to restore the original state"
        exit 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}This was a dry run. Run without --dry-run to execute tests.${NC}"
    fi
}

main "$@"
