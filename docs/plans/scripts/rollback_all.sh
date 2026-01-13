#!/bin/bash
set -e

# ============================================================================
# Rollback: Restore Original State
# ============================================================================
# Purpose: Undo all migration changes and restore original state
# WARNING: This will remove lib/oda and restore scripts/ from backup
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
BACKUP_ROOT="${PROJECT_ROOT}/.migration_backup"
LOG_FILE="${BACKUP_ROOT}/rollback.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Dry run mode
DRY_RUN=false
FORCE=false
if [[ "$1" == "--dry-run" ]] || [[ "$1" == "-n" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}[DRY-RUN MODE] No changes will be made${NC}"
fi
if [[ "$1" == "--force" ]] || [[ "$1" == "-f" ]]; then
    FORCE=true
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
# Pre-rollback Checks
# ============================================================================
preflight_check() {
    info "Running pre-rollback checks..."

    # Check for backup
    if [[ ! -f "${BACKUP_ROOT}/latest" ]]; then
        error "No backup found. Cannot rollback."
        error "Expected: ${BACKUP_ROOT}/latest"
        exit 1
    fi

    local latest_backup=$(cat "${BACKUP_ROOT}/latest")
    if [[ ! -d "$latest_backup" ]]; then
        error "Backup directory not found: $latest_backup"
        exit 1
    fi

    info "Found backup: $latest_backup"

    # Confirm with user
    if [[ "$FORCE" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
        echo ""
        echo -e "${RED}WARNING: This will:${NC}"
        echo "  1. Remove lib/oda directory"
        echo "  2. Restore scripts/ from backup"
        echo "  3. Restore all configuration files"
        echo ""
        read -p "Are you sure you want to rollback? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Rollback cancelled by user"
            exit 1
        fi
    fi

    success "Pre-rollback checks passed"
}

# ============================================================================
# Remove Migrated Files
# ============================================================================
remove_migrated_files() {
    info "Removing migrated files..."

    local target_dir="${PROJECT_ROOT}/lib/oda"

    if [[ -d "$target_dir" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would remove: $target_dir"
        else
            rm -rf "$target_dir"
            success "Removed: $target_dir"
        fi
    else
        info "lib/oda not found - skipping removal"
    fi

    # Remove lib/__init__.py if we created it
    local lib_init="${PROJECT_ROOT}/lib/__init__.py"
    if [[ -f "$lib_init" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would remove: $lib_init"
        else
            rm "$lib_init"
            info "Removed: $lib_init"
        fi
    fi

    # Remove empty lib directory
    if [[ -d "${PROJECT_ROOT}/lib" ]] && [[ -z "$(ls -A "${PROJECT_ROOT}/lib")" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would remove empty: ${PROJECT_ROOT}/lib"
        else
            rmdir "${PROJECT_ROOT}/lib"
            info "Removed empty lib directory"
        fi
    fi
}

# ============================================================================
# Remove Symlinks
# ============================================================================
remove_symlinks() {
    info "Removing symlinks in scripts/..."

    local scripts_dir="${PROJECT_ROOT}/scripts"

    if [[ -d "$scripts_dir" ]]; then
        # Find and remove symlinks
        while IFS= read -r -d '' link; do
            if [[ "$DRY_RUN" == "true" ]]; then
                info "[DRY-RUN] Would remove symlink: ${link#$PROJECT_ROOT/}"
            else
                rm "$link"
                info "Removed symlink: ${link#$PROJECT_ROOT/}"
            fi
        done < <(find "$scripts_dir" -maxdepth 1 -type l -print0)
    fi

    # Restore .orig directories
    while IFS= read -r -d '' orig; do
        local target="${orig%.orig}"
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would restore: ${orig} -> ${target}"
        else
            if [[ -e "$target" ]]; then
                rm -rf "$target"
            fi
            mv "$orig" "$target"
            info "Restored: ${target#$PROJECT_ROOT/}"
        fi
    done < <(find "$scripts_dir" -maxdepth 1 -type d -name "*.orig" -print0 2>/dev/null)
}

# ============================================================================
# Restore from Backup
# ============================================================================
restore_from_backup() {
    info "Restoring from backup..."

    local latest_backup=$(cat "${BACKUP_ROOT}/latest")
    local scripts_backup="${latest_backup}/scripts_backup"

    if [[ -d "$scripts_backup" ]]; then
        local scripts_dir="${PROJECT_ROOT}/scripts"

        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would restore scripts/ from: $scripts_backup"
        else
            # Backup current scripts if it exists (for safety)
            if [[ -d "$scripts_dir" ]]; then
                mv "$scripts_dir" "${scripts_dir}.rollback.$(date +%Y%m%d_%H%M%S)"
            fi

            # Restore from backup
            cp -r "$scripts_backup" "$scripts_dir"
            success "Restored scripts/ from backup"
        fi
    else
        warn "No scripts backup found in: $latest_backup"
    fi
}

# ============================================================================
# Restore Configuration Files
# ============================================================================
restore_configs() {
    info "Restoring configuration files..."

    # Find and restore .backup files
    local config_patterns=(
        "${PROJECT_ROOT}/.mcp.json.backup.*"
        "${PROJECT_ROOT}/pyproject.toml.backup.*"
        "${PROJECT_ROOT}/.env.backup.*"
        "${HOME}/.mcp.json.backup.*"
        "${HOME}/.bashrc.backup.*"
    )

    for pattern in "${config_patterns[@]}"; do
        # Find most recent backup
        local latest_config=$(ls -t $pattern 2>/dev/null | head -1)
        if [[ -n "$latest_config" ]]; then
            local target="${latest_config%%.backup.*}"
            if [[ "$DRY_RUN" == "true" ]]; then
                info "[DRY-RUN] Would restore: $target from $latest_config"
            else
                cp "$latest_config" "$target"
                info "Restored: $target"
            fi
        fi
    done

    # Restore MCP config specifically
    local mcp_backup="${BACKUP_ROOT}/*/mcp.json.backup"
    local mcp_latest=$(ls -t $mcp_backup 2>/dev/null | head -1)
    if [[ -n "$mcp_latest" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would restore .mcp.json"
        else
            cp "$mcp_latest" "${PROJECT_ROOT}/.mcp.json"
            info "Restored .mcp.json"
        fi
    fi
}

# ============================================================================
# Clean Up Environment
# ============================================================================
cleanup_environment() {
    info "Cleaning up environment..."

    # Remove setup_env.sh
    local setup_env="${PROJECT_ROOT}/setup_env.sh"
    if [[ -f "$setup_env" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would remove: $setup_env"
        else
            rm "$setup_env"
            info "Removed: setup_env.sh"
        fi
    fi

    # Note about manual cleanup
    echo ""
    warn "Manual cleanup may be needed for:"
    echo "  - ~/.bashrc or ~/.zshrc PYTHONPATH changes"
    echo "  - VS Code settings"
    echo "  - Any IDE configurations"
}

# ============================================================================
# Verify Rollback
# ============================================================================
verify_rollback() {
    info "Verifying rollback..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Verification skipped in dry-run mode"
        return
    fi

    local errors=0

    # Check lib/oda removed
    if [[ -d "${PROJECT_ROOT}/lib/oda" ]]; then
        error "lib/oda still exists"
        ((errors++))
    else
        success "lib/oda removed"
    fi

    # Check scripts restored
    if [[ -d "${PROJECT_ROOT}/scripts" ]]; then
        local file_count=$(find "${PROJECT_ROOT}/scripts" -name "*.py" -type f | wc -l)
        info "scripts/ contains $file_count Python files"
    else
        error "scripts/ not found"
        ((errors++))
    fi

    # Test import
    local test_import='
import sys
sys.path.insert(0, "'"${PROJECT_ROOT}"'")
try:
    from scripts.ontology.registry import ActionRegistry
    print("Original import works")
    sys.exit(0)
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
'

    if python3 -c "$test_import" 2>&1; then
        success "Original imports work"
    else
        error "Original imports failed"
        ((errors++))
    fi

    if [[ "$errors" -eq 0 ]]; then
        success "Rollback verification passed"
    else
        error "Rollback verification failed with $errors errors"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "Rollback: Restore Original State"
    echo "=============================================="
    echo ""

    preflight_check
    remove_migrated_files
    remove_symlinks
    restore_from_backup
    restore_configs
    cleanup_environment
    verify_rollback

    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}This was a dry run. Run without --dry-run to apply rollback.${NC}"
    else
        success "Rollback completed!"
        echo ""
        info "The system has been restored to pre-migration state."
        info "You may need to restart your shell or IDE."
    fi
}

main "$@"
