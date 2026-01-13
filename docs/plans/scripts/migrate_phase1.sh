#!/bin/bash
set -e

# ============================================================================
# Phase 1: Directory Creation and File Copy
# ============================================================================
# Purpose: Create lib/oda directory structure and copy files from scripts/
# Backup: Creates timestamped backup before any changes
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
SOURCE_DIR="${PROJECT_ROOT}/scripts"
TARGET_DIR="${PROJECT_ROOT}/lib/oda"
BACKUP_DIR="${PROJECT_ROOT}/.migration_backup/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${PROJECT_ROOT}/.migration_backup/phase1.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

    # Check source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        error "Source directory not found: $SOURCE_DIR"
        exit 1
    fi

    # Check if target already exists
    if [[ -d "$TARGET_DIR" ]]; then
        warn "Target directory already exists: $TARGET_DIR"
        if [[ "$DRY_RUN" == "false" ]]; then
            read -p "Overwrite? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                error "Aborted by user"
                exit 1
            fi
        fi
    fi

    success "Pre-flight checks passed"
}

# ============================================================================
# Create Backup
# ============================================================================
create_backup() {
    info "Creating backup..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Would create backup at: $BACKUP_DIR"
        return
    fi

    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"

    # Backup scripts directory
    if [[ -d "$SOURCE_DIR" ]]; then
        cp -r "$SOURCE_DIR" "$BACKUP_DIR/scripts_backup"
        success "Backed up scripts/ to $BACKUP_DIR/scripts_backup"
    fi

    # Backup existing lib/oda if exists
    if [[ -d "$TARGET_DIR" ]]; then
        cp -r "$TARGET_DIR" "$BACKUP_DIR/lib_oda_backup"
        success "Backed up existing lib/oda/ to $BACKUP_DIR/lib_oda_backup"
    fi

    # Save backup location for rollback
    echo "$BACKUP_DIR" > "${PROJECT_ROOT}/.migration_backup/latest"

    success "Backup completed: $BACKUP_DIR"
}

# ============================================================================
# Create Directory Structure
# ============================================================================
create_directory_structure() {
    info "Creating lib/oda directory structure..."

    # Define target directories based on source structure
    local directories=(
        "lib/oda"
        "lib/oda/agent"
        "lib/oda/aip_logic"
        "lib/oda/api"
        "lib/oda/claude"
        "lib/oda/claude/handlers"
        "lib/oda/cognitive"
        "lib/oda/consolidation"
        "lib/oda/data"
        "lib/oda/infrastructure"
        "lib/oda/layer"
        "lib/oda/lib"
        "lib/oda/llm"
        "lib/oda/maintenance"
        "lib/oda/mcp"
        "lib/oda/memory"
        "lib/oda/observe"
        "lib/oda/ontology"
        "lib/oda/ontology/actions"
        "lib/oda/ontology/evidence"
        "lib/oda/ontology/fde_learning"
        "lib/oda/ontology/governance"
        "lib/oda/ontology/jobs"
        "lib/oda/ontology/kb"
        "lib/oda/ontology/learning"
        "lib/oda/ontology/objects"
        "lib/oda/ontology/plans"
        "lib/oda/ontology/protocols"
        "lib/oda/ontology/relays"
        "lib/oda/ontology/schemas"
        "lib/oda/ontology/storage"
        "lib/oda/ontology/validators"
        "lib/oda/osdk"
        "lib/oda/relay"
        "lib/oda/runtime"
        "lib/oda/simulation"
        "lib/oda/tools"
        "lib/oda/tools/sps"
        "lib/oda/tools/yt"
        "lib/oda/voice"
    )

    for dir in "${directories[@]}"; do
        local full_path="${PROJECT_ROOT}/${dir}"
        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would create: $full_path"
        else
            mkdir -p "$full_path"
            info "Created: $dir"
        fi
    done

    success "Directory structure created"
}

# ============================================================================
# Copy Files
# ============================================================================
copy_files() {
    info "Copying files from scripts/ to lib/oda/..."

    local file_count=0

    # Find all Python files in scripts/
    while IFS= read -r -d '' file; do
        local relative_path="${file#$SOURCE_DIR/}"
        local target_file="${TARGET_DIR}/${relative_path}"
        local target_dir="$(dirname "$target_file")"

        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would copy: $relative_path"
        else
            mkdir -p "$target_dir"
            cp "$file" "$target_file"
        fi

        ((file_count++))
    done < <(find "$SOURCE_DIR" -name "*.py" -type f -print0)

    # Copy non-Python files that might be needed
    while IFS= read -r -d '' file; do
        local relative_path="${file#$SOURCE_DIR/}"
        local target_file="${TARGET_DIR}/${relative_path}"
        local target_dir="$(dirname "$target_file")"

        if [[ "$DRY_RUN" == "true" ]]; then
            info "[DRY-RUN] Would copy: $relative_path"
        else
            mkdir -p "$target_dir"
            cp "$file" "$target_file"
        fi

        ((file_count++))
    done < <(find "$SOURCE_DIR" \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" \) -type f -print0)

    success "Copied $file_count files"
}

# ============================================================================
# Create __init__.py files
# ============================================================================
create_init_files() {
    info "Creating __init__.py files..."

    local init_count=0

    while IFS= read -r -d '' dir; do
        local init_file="${dir}/__init__.py"
        if [[ ! -f "$init_file" ]]; then
            if [[ "$DRY_RUN" == "true" ]]; then
                info "[DRY-RUN] Would create: ${init_file#$PROJECT_ROOT/}"
            else
                # Create minimal __init__.py
                echo '"""ODA module."""' > "$init_file"
            fi
            ((init_count++))
        fi
    done < <(find "$TARGET_DIR" -type d -print0)

    success "Created $init_count __init__.py files"
}

# ============================================================================
# Verify Phase 1
# ============================================================================
verify_phase1() {
    info "Verifying Phase 1 completion..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Verification skipped in dry-run mode"
        return
    fi

    # Count files in target
    local target_count=$(find "$TARGET_DIR" -name "*.py" -type f | wc -l)
    local source_count=$(find "$SOURCE_DIR" -name "*.py" -type f | wc -l)

    info "Source files: $source_count"
    info "Target files: $target_count"

    if [[ "$target_count" -ge "$source_count" ]]; then
        success "Phase 1 verification passed"
    else
        warn "File count mismatch - please verify manually"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "Phase 1: Directory Creation and File Copy"
    echo "=============================================="
    echo ""

    preflight_check
    create_backup
    create_directory_structure
    copy_files
    create_init_files
    verify_phase1

    echo ""
    success "Phase 1 completed successfully!"
    echo ""
    info "Next step: Run migrate_phase2.sh to update imports"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}This was a dry run. Run without --dry-run to apply changes.${NC}"
    fi
}

main "$@"
