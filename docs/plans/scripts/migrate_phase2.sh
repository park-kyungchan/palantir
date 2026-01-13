#!/bin/bash
set -e

# ============================================================================
# Phase 2: Import Refactoring
# ============================================================================
# Purpose: Update all 'from scripts.' imports to 'from lib.oda.'
# Scope: All Python files in the project
# Method: sed-based replacement with verification
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
TARGET_DIR="${PROJECT_ROOT}/lib/oda"
TESTS_DIR="${PROJECT_ROOT}/tests"
LOG_FILE="${PROJECT_ROOT}/.migration_backup/phase2.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Dry run mode
DRY_RUN=false
if [[ "$1" == "--dry-run" ]] || [[ "$1" == "-n" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}[DRY-RUN MODE] No changes will be made${NC}"
fi

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${level}] ${message}"
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "$(dirname "$LOG_FILE")"
        echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
    fi
}

info() { log "INFO" "${BLUE}$1${NC}"; }
success() { log "SUCCESS" "${GREEN}$1${NC}"; }
warn() { log "WARN" "${YELLOW}$1${NC}"; }
error() { log "ERROR" "${RED}$1${NC}"; }

# ============================================================================
# Pre-flight Checks
# ============================================================================
preflight_check() {
    info "Running pre-flight checks..."

    # Check target directory exists
    if [[ ! -d "$TARGET_DIR" ]]; then
        error "Target directory not found: $TARGET_DIR"
        error "Please run migrate_phase1.sh first"
        exit 1
    fi

    # Count imports to change
    local import_count=$(grep -r "from scripts\." "$PROJECT_ROOT" --include="*.py" 2>/dev/null | wc -l)
    info "Found $import_count imports to update"

    success "Pre-flight checks passed"
}

# ============================================================================
# Import Patterns to Replace
# ============================================================================
# Pattern: from scripts.X -> from lib.oda.X
# ============================================================================

replace_imports_in_file() {
    local file=$1

    if [[ "$DRY_RUN" == "true" ]]; then
        # Show what would change
        local matches=$(grep -n "from scripts\." "$file" 2>/dev/null || true)
        if [[ -n "$matches" ]]; then
            info "[DRY-RUN] Would update: ${file#$PROJECT_ROOT/}"
            echo "$matches" | while read -r line; do
                echo "    $line"
            done
        fi
    else
        # Perform the replacement
        sed -i 's/from scripts\./from lib.oda./g' "$file"
        sed -i 's/import scripts\./import lib.oda./g' "$file"
    fi
}

# ============================================================================
# Update Imports in lib/oda
# ============================================================================
update_lib_oda_imports() {
    info "Updating imports in lib/oda/..."

    local file_count=0
    local change_count=0

    while IFS= read -r -d '' file; do
        local matches=$(grep -c "from scripts\." "$file" 2>/dev/null || echo "0")
        if [[ "$matches" -gt 0 ]]; then
            replace_imports_in_file "$file"
            ((change_count+=matches))
            ((file_count++))
        fi
    done < <(find "$TARGET_DIR" -name "*.py" -type f -print0)

    info "Updated $file_count files with $change_count import changes in lib/oda/"
}

# ============================================================================
# Update Imports in tests/
# ============================================================================
update_test_imports() {
    info "Updating imports in tests/..."

    local file_count=0
    local change_count=0

    if [[ -d "$TESTS_DIR" ]]; then
        while IFS= read -r -d '' file; do
            local matches=$(grep -c "from scripts\." "$file" 2>/dev/null || echo "0")
            if [[ "$matches" -gt 0 ]]; then
                replace_imports_in_file "$file"
                ((change_count+=matches))
                ((file_count++))
            fi
        done < <(find "$TESTS_DIR" -name "*.py" -type f -print0)
    fi

    info "Updated $file_count files with $change_count import changes in tests/"
}

# ============================================================================
# Update Imports in scripts/ (for transitional compatibility)
# ============================================================================
update_scripts_imports() {
    info "Updating imports in scripts/ (transitional)..."

    local scripts_dir="${PROJECT_ROOT}/scripts"
    local file_count=0
    local change_count=0

    if [[ -d "$scripts_dir" ]]; then
        while IFS= read -r -d '' file; do
            local matches=$(grep -c "from scripts\." "$file" 2>/dev/null || echo "0")
            if [[ "$matches" -gt 0 ]]; then
                replace_imports_in_file "$file"
                ((change_count+=matches))
                ((file_count++))
            fi
        done < <(find "$scripts_dir" -name "*.py" -type f -print0)
    fi

    info "Updated $file_count files with $change_count import changes in scripts/"
}

# ============================================================================
# Update Imports in other locations
# ============================================================================
update_other_imports() {
    info "Updating imports in other project files..."

    local other_dirs=(
        "${PROJECT_ROOT}/config"
        "${PROJECT_ROOT}/coding"
        "${PROJECT_ROOT}/governance"
    )

    for dir in "${other_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            while IFS= read -r -d '' file; do
                local matches=$(grep -c "from scripts\." "$file" 2>/dev/null || echo "0")
                if [[ "$matches" -gt 0 ]]; then
                    replace_imports_in_file "$file"
                fi
            done < <(find "$dir" -name "*.py" -type f -print0 2>/dev/null)
        fi
    done

    success "Other locations updated"
}

# ============================================================================
# Verify Phase 2
# ============================================================================
verify_phase2() {
    info "Verifying Phase 2 completion..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Verification skipped in dry-run mode"
        return
    fi

    # Count remaining old imports in lib/oda
    local remaining_lib=$(grep -r "from scripts\." "$TARGET_DIR" --include="*.py" 2>/dev/null | wc -l)

    info "Remaining 'from scripts.' imports in lib/oda: $remaining_lib"

    if [[ "$remaining_lib" -eq 0 ]]; then
        success "Phase 2 verification passed for lib/oda"
    else
        warn "Some imports remain unchanged - please review manually"
        grep -r "from scripts\." "$TARGET_DIR" --include="*.py" 2>/dev/null | head -10
    fi
}

# ============================================================================
# Generate Import Report
# ============================================================================
generate_report() {
    info "Generating import change report..."

    if [[ "$DRY_RUN" == "true" ]]; then
        return
    fi

    local report_file="${PROJECT_ROOT}/.migration_backup/phase2_report.txt"

    {
        echo "=============================================="
        echo "Phase 2: Import Refactoring Report"
        echo "Generated: $(date)"
        echo "=============================================="
        echo ""
        echo "Remaining 'from scripts.' imports:"
        echo "----------------------------------------------"
        grep -r "from scripts\." "$PROJECT_ROOT" --include="*.py" 2>/dev/null || echo "None found"
        echo ""
        echo "New 'from lib.oda.' imports count:"
        grep -r "from lib.oda\." "$PROJECT_ROOT" --include="*.py" 2>/dev/null | wc -l
    } > "$report_file"

    success "Report saved to: $report_file"
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "Phase 2: Import Refactoring"
    echo "=============================================="
    echo ""

    preflight_check
    update_lib_oda_imports
    update_test_imports
    update_scripts_imports
    update_other_imports
    verify_phase2
    generate_report

    echo ""
    success "Phase 2 completed successfully!"
    echo ""
    info "Next step: Run migrate_phase3.sh to fix hardcoded paths"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}This was a dry run. Run without --dry-run to apply changes.${NC}"
    fi
}

main "$@"
