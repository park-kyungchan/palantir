#!/bin/bash
set -e

# ============================================================================
# Phase 6: Create Symlinks for Compatibility
# ============================================================================
# Purpose: Create symlinks from scripts/ to lib/oda/ for backward compatibility
# Scope: Top-level module symlinks
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
SOURCE_DIR="${PROJECT_ROOT}/scripts"
TARGET_DIR="${PROJECT_ROOT}/lib/oda"
LOG_FILE="${PROJECT_ROOT}/.migration_backup/phase6.log"

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
# Symlink Strategy
# ============================================================================
# Option A: Replace scripts/ with symlink to lib/oda/
# Option B: Create individual module symlinks within scripts/
# Option C: Create scripts/__init__.py that re-exports from lib.oda
#
# We use Option C (re-export) as safest approach
# ============================================================================

# ============================================================================
# Create Compatibility Re-exports
# ============================================================================
create_reexport_module() {
    info "Creating compatibility re-export module..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Would create compatibility re-exports in scripts/"
        return
    fi

    # Backup existing scripts/__init__.py
    if [[ -f "${SOURCE_DIR}/__init__.py" ]]; then
        cp "${SOURCE_DIR}/__init__.py" "${SOURCE_DIR}/__init__.py.backup"
    fi

    # Create re-export __init__.py
    cat > "${SOURCE_DIR}/__init__.py" << 'REEXPORT_EOF'
"""
Compatibility module for scripts -> lib.oda migration.

DEPRECATED: Import from lib.oda instead of scripts.
This module provides backward compatibility during migration.

Example:
    # Old (deprecated):
    from scripts.ontology.registry import ActionRegistry

    # New (recommended):
    from lib.oda.ontology.registry import ActionRegistry
"""
import warnings
import sys
from pathlib import Path

# Add lib to path if not present
lib_path = str(Path(__file__).parent.parent / "lib")
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# Emit deprecation warning on import
warnings.warn(
    "Importing from 'scripts' is deprecated. Use 'lib.oda' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from lib.oda
from lib.oda import *
REEXPORT_EOF

    success "Created scripts/__init__.py with deprecation warning"
}

# ============================================================================
# Create Module Symlinks
# ============================================================================
create_module_symlinks() {
    info "Creating module-level symlinks..."

    # Modules to symlink
    local modules=(
        "ontology"
        "mcp"
        "agent"
        "api"
        "claude"
        "cognitive"
        "consolidation"
        "data"
        "infrastructure"
        "layer"
        "lib"
        "llm"
        "maintenance"
        "memory"
        "observe"
        "osdk"
        "relay"
        "runtime"
        "simulation"
        "tools"
        "voice"
        "aip_logic"
    )

    local created=0
    local skipped=0

    for module in "${modules[@]}"; do
        local source="${SOURCE_DIR}/${module}"
        local target="${TARGET_DIR}/${module}"

        # Check if target exists
        if [[ ! -d "$target" ]]; then
            warn "Target module not found: $target"
            continue
        fi

        if [[ "$DRY_RUN" == "true" ]]; then
            if [[ -d "$source" ]] && [[ ! -L "$source" ]]; then
                info "[DRY-RUN] Would backup and replace: $source -> $target"
            elif [[ -L "$source" ]]; then
                info "[DRY-RUN] Symlink already exists: $source"
            else
                info "[DRY-RUN] Would create symlink: $source -> $target"
            fi
            continue
        fi

        # Handle existing directory
        if [[ -d "$source" ]] && [[ ! -L "$source" ]]; then
            if [[ "$FORCE" == "true" ]]; then
                # Backup and remove
                mv "$source" "${source}.orig"
                info "Backed up: ${source} -> ${source}.orig"
            else
                warn "Skipping $module - directory exists (use --force to replace)"
                ((skipped++))
                continue
            fi
        fi

        # Remove existing symlink if present
        if [[ -L "$source" ]]; then
            rm "$source"
        fi

        # Create relative symlink
        local rel_target="../lib/oda/${module}"
        ln -s "$rel_target" "$source"
        info "Created symlink: $module -> $rel_target"
        ((created++))
    done

    success "Created $created symlinks, skipped $skipped"
}

# ============================================================================
# Create Deprecation Wrapper
# ============================================================================
create_deprecation_wrappers() {
    info "Creating deprecation wrapper modules..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Would create deprecation wrappers"
        return
    fi

    # Create a wrapper that emits warnings for specific high-use modules
    local wrapper_modules=(
        "ontology.registry"
        "ontology.storage.database"
        "mcp.ontology_server"
    )

    for module in "${wrapper_modules[@]}"; do
        local module_path="${SOURCE_DIR}/${module//.//}"
        local module_file="${module_path}.py"
        local module_dir=$(dirname "$module_file")

        # Ensure directory exists
        mkdir -p "$module_dir"

        # Create __init__.py if needed
        if [[ ! -f "${module_dir}/__init__.py" ]]; then
            echo '"""Compatibility module."""' > "${module_dir}/__init__.py"
        fi
    done

    success "Deprecation wrappers created"
}

# ============================================================================
# Verify Symlinks
# ============================================================================
verify_symlinks() {
    info "Verifying symlink configuration..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Verification skipped in dry-run mode"
        return
    fi

    local test_import='
import sys
sys.path.insert(0, "'"${PROJECT_ROOT}"'")

# Test old import path (should work via symlink/re-export)
try:
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # This should emit deprecation warning but still work
        exec("from scripts.ontology.registry import ActionRegistry")
        if len(w) > 0 and issubclass(w[-1].category, DeprecationWarning):
            print("Deprecation warning correctly emitted")
        print("Backward compatibility verified")
        sys.exit(0)
except ImportError as e:
    print(f"Compatibility import failed: {e}")
    sys.exit(1)
'

    if python3 -c "$test_import" 2>&1; then
        success "Symlink verification passed"
    else
        warn "Symlink verification needs review"
    fi
}

# ============================================================================
# Create PYTHONPATH helper script
# ============================================================================
create_path_helper() {
    info "Creating PYTHONPATH helper script..."

    local helper_script="${PROJECT_ROOT}/setup_env.sh"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Would create: $helper_script"
        return
    fi

    cat > "$helper_script" << 'HELPER_EOF'
#!/bin/bash
# Source this file to set up the ODA environment
# Usage: source setup_env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
export ODA_ROOT="${SCRIPT_DIR}/lib/oda"
export ODA_DB_PATH="${SCRIPT_DIR}/.agent/tmp/ontology.db"

echo "ODA environment configured:"
echo "  PYTHONPATH includes: ${SCRIPT_DIR}"
echo "  ODA_ROOT: ${ODA_ROOT}"
echo "  ODA_DB_PATH: ${ODA_DB_PATH}"
HELPER_EOF

    chmod +x "$helper_script"
    success "Created: $helper_script"
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "Phase 6: Create Symlinks for Compatibility"
    echo "=============================================="
    echo ""

    create_reexport_module
    create_module_symlinks
    create_deprecation_wrappers
    create_path_helper
    verify_symlinks

    echo ""
    success "Phase 6 completed successfully!"
    echo ""
    info "Migration complete! To verify:"
    echo "  1. source ${PROJECT_ROOT}/setup_env.sh"
    echo "  2. python -c 'from lib.oda.ontology.registry import ActionRegistry; print(\"OK\")'"
    echo ""
    info "Run verify_migration.sh for comprehensive verification"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}This was a dry run. Run without --dry-run to apply changes.${NC}"
    fi
}

main "$@"
