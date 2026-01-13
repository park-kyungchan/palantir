#!/bin/bash
set -e

# ============================================================================
# Verify Migration Success
# ============================================================================
# Purpose: Comprehensive verification of migration success
# Scope: All aspects of the migration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
LOG_FILE="${PROJECT_ROOT}/.migration_backup/verify.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0
declare -a ISSUES

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${level}] ${message}"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

info() { log "INFO" "${BLUE}$1${NC}"; }
success() { log "PASS" "${GREEN}$1${NC}"; }
warn() { log "WARN" "${YELLOW}$1${NC}"; }
error() { log "FAIL" "${RED}$1${NC}"; }
header() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

pass() {
    success "$1"
    ((CHECKS_PASSED++))
}

fail() {
    error "$1"
    ((CHECKS_FAILED++))
    ISSUES+=("$1")
}

warning() {
    warn "$1"
    ((CHECKS_WARNED++))
}

# ============================================================================
# Check 1: Directory Structure
# ============================================================================
check_directory_structure() {
    header "Check 1: Directory Structure"

    local required_dirs=(
        "lib/oda"
        "lib/oda/ontology"
        "lib/oda/ontology/storage"
        "lib/oda/ontology/actions"
        "lib/oda/mcp"
        "lib/oda/agent"
        "lib/oda/claude"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ -d "${PROJECT_ROOT}/${dir}" ]]; then
            pass "Directory exists: $dir"
        else
            fail "Directory missing: $dir"
        fi
    done
}

# ============================================================================
# Check 2: Import Residue
# ============================================================================
check_import_residue() {
    header "Check 2: Import Residue Analysis"

    # Check lib/oda for old imports
    local lib_oda_residue=$(grep -r "from scripts\." "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | wc -l)
    if [[ "$lib_oda_residue" -eq 0 ]]; then
        pass "No 'from scripts.' imports in lib/oda"
    else
        fail "Found $lib_oda_residue old imports in lib/oda"
        grep -r "from scripts\." "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | head -5
    fi

    # Check tests for old imports
    local tests_residue=$(grep -r "from scripts\." "${PROJECT_ROOT}/tests" --include="*.py" 2>/dev/null | wc -l)
    if [[ "$tests_residue" -eq 0 ]]; then
        pass "No 'from scripts.' imports in tests/"
    else
        warning "Found $tests_residue old imports in tests/ (may need updating)"
    fi

    # Count new imports
    local new_imports=$(grep -r "from lib.oda\." "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | wc -l)
    info "New 'from lib.oda.' imports: $new_imports"
}

# ============================================================================
# Check 3: Python Import Test
# ============================================================================
check_python_imports() {
    header "Check 3: Python Import Test"

    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

    # Core imports
    local core_modules=(
        "lib.oda.ontology.registry"
        "lib.oda.ontology.storage.database"
        "lib.oda.mcp.ontology_server"
        "lib.oda.agent.executor"
        "lib.oda.claude.protocol_runner"
    )

    for module in "${core_modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            pass "Import OK: $module"
        else
            fail "Import FAILED: $module"
        fi
    done
}

# ============================================================================
# Check 4: Configuration Files
# ============================================================================
check_configurations() {
    header "Check 4: Configuration Files"

    # MCP config
    if [[ -f "${PROJECT_ROOT}/.mcp.json" ]]; then
        if grep -q "lib.oda.mcp" "${PROJECT_ROOT}/.mcp.json"; then
            pass "MCP config uses lib.oda.mcp"
        else
            fail "MCP config still references scripts"
        fi
    else
        warning ".mcp.json not found"
    fi

    # pyproject.toml
    if [[ -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
        if ! grep -q '"scripts"' "${PROJECT_ROOT}/pyproject.toml" 2>/dev/null; then
            pass "pyproject.toml updated"
        else
            warning "pyproject.toml may still reference scripts"
        fi
    fi

    # .env file
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        if grep -q "PYTHONPATH" "${PROJECT_ROOT}/.env"; then
            pass "PYTHONPATH configured in .env"
        else
            warning "PYTHONPATH not in .env"
        fi
    fi
}

# ============================================================================
# Check 5: File Count Comparison
# ============================================================================
check_file_counts() {
    header "Check 5: File Count Analysis"

    local lib_oda_files=$(find "${PROJECT_ROOT}/lib/oda" -name "*.py" -type f 2>/dev/null | wc -l)
    local scripts_files=$(find "${PROJECT_ROOT}/scripts" -name "*.py" -type f 2>/dev/null | wc -l)

    info "Python files in lib/oda: $lib_oda_files"
    info "Python files in scripts: $scripts_files"

    if [[ "$lib_oda_files" -gt 0 ]]; then
        pass "lib/oda contains Python files"
    else
        fail "lib/oda is empty or missing Python files"
    fi

    # Expected: lib/oda should have at least as many files as scripts
    if [[ "$lib_oda_files" -ge "$scripts_files" ]]; then
        pass "lib/oda has >= scripts file count"
    else
        warning "lib/oda has fewer files than scripts ($lib_oda_files < $scripts_files)"
    fi
}

# ============================================================================
# Check 6: Hardcoded Paths
# ============================================================================
check_hardcoded_paths() {
    header "Check 6: Hardcoded Path Analysis"

    # Check for remaining hardcoded paths in lib/oda
    local hardcoded=$(grep -r '"scripts/' "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | wc -l)
    hardcoded=$((hardcoded + $(grep -r "'scripts/" "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | wc -l)))

    if [[ "$hardcoded" -eq 0 ]]; then
        pass "No hardcoded 'scripts/' paths in lib/oda"
    else
        fail "Found $hardcoded hardcoded paths in lib/oda"
        grep -r "scripts/" "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | head -5
    fi
}

# ============================================================================
# Check 7: Syntax Validation
# ============================================================================
check_syntax() {
    header "Check 7: Syntax Validation"

    local syntax_errors=0
    local checked=0

    while IFS= read -r -d '' file; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            error "Syntax error: ${file#$PROJECT_ROOT/}"
            ((syntax_errors++))
        fi
        ((checked++))
    done < <(find "${PROJECT_ROOT}/lib/oda" -name "*.py" -type f -print0)

    if [[ "$syntax_errors" -eq 0 ]]; then
        pass "All $checked Python files have valid syntax"
    else
        fail "$syntax_errors files have syntax errors"
    fi
}

# ============================================================================
# Check 8: MCP Server Test
# ============================================================================
check_mcp_server() {
    header "Check 8: MCP Server Module"

    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

    local mcp_test='
import sys
sys.path.insert(0, "'"${PROJECT_ROOT}"'")
try:
    from lib.oda.mcp.ontology_server import mcp, list_actions
    # Try to call a basic function
    actions = list_actions()
    print(f"MCP server ready with {len(actions)} actions")
    sys.exit(0)
except Exception as e:
    print(f"MCP test failed: {e}")
    sys.exit(1)
'

    if python3 -c "$mcp_test" 2>&1; then
        pass "MCP server module functional"
    else
        fail "MCP server module not functional"
    fi
}

# ============================================================================
# Check 9: Backward Compatibility
# ============================================================================
check_backward_compat() {
    header "Check 9: Backward Compatibility"

    # Check if scripts/ symlinks or re-exports exist
    if [[ -f "${PROJECT_ROOT}/scripts/__init__.py" ]]; then
        if grep -q "DeprecationWarning\|lib.oda" "${PROJECT_ROOT}/scripts/__init__.py" 2>/dev/null; then
            pass "Backward compatibility layer in place"
        else
            warning "scripts/__init__.py exists but may not have re-exports"
        fi
    else
        warning "No backward compatibility layer (scripts/__init__.py missing)"
    fi

    # Check for symlinks
    local symlink_count=$(find "${PROJECT_ROOT}/scripts" -maxdepth 1 -type l 2>/dev/null | wc -l)
    if [[ "$symlink_count" -gt 0 ]]; then
        info "Found $symlink_count compatibility symlinks in scripts/"
    fi
}

# ============================================================================
# Check 10: Test Readiness
# ============================================================================
check_test_readiness() {
    header "Check 10: Test Readiness"

    if command -v pytest &> /dev/null; then
        pass "pytest is available"

        # Quick syntax check on test files
        local test_errors=0
        while IFS= read -r -d '' file; do
            if ! python3 -m py_compile "$file" 2>/dev/null; then
                ((test_errors++))
            fi
        done < <(find "${PROJECT_ROOT}/tests" -name "*.py" -type f -print0 2>/dev/null)

        if [[ "$test_errors" -eq 0 ]]; then
            pass "All test files have valid syntax"
        else
            warning "$test_errors test files have syntax issues"
        fi
    else
        warning "pytest not available"
    fi
}

# ============================================================================
# Generate Summary
# ============================================================================
generate_summary() {
    echo ""
    echo "=============================================="
    echo "           MIGRATION VERIFICATION SUMMARY"
    echo "=============================================="
    echo ""
    echo -e "  ${GREEN}Passed:${NC}  $CHECKS_PASSED"
    echo -e "  ${RED}Failed:${NC}  $CHECKS_FAILED"
    echo -e "  ${YELLOW}Warned:${NC}  $CHECKS_WARNED"
    echo ""

    if [[ ${#ISSUES[@]} -gt 0 ]]; then
        echo -e "${RED}Issues to address:${NC}"
        for issue in "${ISSUES[@]}"; do
            echo "  - $issue"
        done
        echo ""
    fi

    if [[ "$CHECKS_FAILED" -eq 0 ]]; then
        echo -e "${GREEN}=============================================="
        echo "  MIGRATION VERIFIED SUCCESSFULLY!"
        echo "==============================================${NC}"
        echo ""
        echo "The migration from scripts/ to lib/oda/ is complete."
        echo ""
        echo "Next steps:"
        echo "  1. Run full test suite: pytest tests/"
        echo "  2. Verify MCP server: python -m lib.oda.mcp.ontology_server"
        echo "  3. Update any external references to the codebase"
        return 0
    else
        echo -e "${RED}=============================================="
        echo "  MIGRATION VERIFICATION FAILED"
        echo "==============================================${NC}"
        echo ""
        echo "Please address the issues above before proceeding."
        echo "Run rollback_all.sh if you need to restore the original state."
        return 1
    fi
}

# ============================================================================
# Save Report
# ============================================================================
save_report() {
    local report_file="${PROJECT_ROOT}/.migration_backup/verification_report.txt"

    {
        echo "Migration Verification Report"
        echo "Generated: $(date)"
        echo "=============================================="
        echo ""
        echo "Results:"
        echo "  Passed: $CHECKS_PASSED"
        echo "  Failed: $CHECKS_FAILED"
        echo "  Warned: $CHECKS_WARNED"
        echo ""
        if [[ ${#ISSUES[@]} -gt 0 ]]; then
            echo "Issues:"
            for issue in "${ISSUES[@]}"; do
                echo "  - $issue"
            done
        fi
        echo ""
        echo "Full log: $LOG_FILE"
    } > "$report_file"

    info "Report saved to: $report_file"
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "     Migration Verification Suite"
    echo "=============================================="

    # Set up environment
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

    # Run all checks
    check_directory_structure
    check_import_residue
    check_python_imports
    check_configurations
    check_file_counts
    check_hardcoded_paths
    check_syntax
    check_mcp_server
    check_backward_compat
    check_test_readiness

    # Generate report
    save_report
    generate_summary

    exit $?
}

main "$@"
