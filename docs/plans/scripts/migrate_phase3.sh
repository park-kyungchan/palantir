#!/bin/bash
set -e

# ============================================================================
# Phase 3: Hardcoded Path Fixes
# ============================================================================
# Purpose: Fix hardcoded 'scripts/' paths in configuration and code
# Scope: 16 files with hardcoded path references
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
LOG_FILE="${PROJECT_ROOT}/.migration_backup/phase3.log"

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
# Files with Hardcoded Paths
# ============================================================================
# These are the known files that contain hardcoded 'scripts/' references
# ============================================================================

declare -A HARDCODED_FILES=(
    # Python files with path strings
    ["lib/oda/ontology/storage/database.py"]='scripts/ontology -> lib/oda/ontology'
    ["lib/oda/data/database.py"]='scripts/data -> lib/oda/data'
    ["lib/oda/maintenance/rebuild_db.py"]='scripts/ paths'
    ["lib/oda/runtime/kernel.py"]='scripts/ paths'
    ["lib/oda/claude/protocol_runner.py"]='scripts/ paths'
    ["lib/oda/tools/cli.py"]='scripts/ paths'
    ["lib/oda/voice/ada.py"]='scripts/ paths'
    ["lib/oda/mcp/ontology_server.py"]='scripts/ paths'
    # Config files
    ["pyproject.toml"]='scripts package reference'
    ["config/mcp.json"]='scripts path in MCP config'
    [".claude/settings.json"]='scripts path in settings'
    ["docker-compose.sandbox.yml"]='scripts volume mount'
    ["Dockerfile"]='scripts COPY command'
)

# ============================================================================
# Fix Python Path Strings
# ============================================================================
fix_python_paths() {
    info "Fixing hardcoded paths in Python files..."

    local python_patterns=(
        # Path string patterns
        's|"scripts/|"lib/oda/|g'
        "s|'scripts/|'lib/oda/|g"
        's|scripts/ontology|lib/oda/ontology|g'
        's|scripts/data|lib/oda/data|g'
        's|scripts/mcp|lib/oda/mcp|g'
        's|scripts/maintenance|lib/oda/maintenance|g'
        's|scripts/runtime|lib/oda/runtime|g'
        's|scripts/claude|lib/oda/claude|g'
        's|scripts/tools|lib/oda/tools|g'
        's|scripts/voice|lib/oda/voice|g'
        # sys.path.insert patterns
        's|sys.path.insert(0, "scripts")|sys.path.insert(0, "lib/oda")|g'
        's|sys.path.append("scripts")|sys.path.append("lib/oda")|g'
    )

    # Find all Python files that might have hardcoded paths
    while IFS= read -r -d '' file; do
        local has_changes=false

        # Check if file contains any 'scripts/' references
        if grep -q "scripts/" "$file" 2>/dev/null; then
            has_changes=true

            if [[ "$DRY_RUN" == "true" ]]; then
                info "[DRY-RUN] Would fix paths in: ${file#$PROJECT_ROOT/}"
                grep -n "scripts/" "$file" | head -5
            else
                for pattern in "${python_patterns[@]}"; do
                    sed -i "$pattern" "$file"
                done
                info "Fixed paths in: ${file#$PROJECT_ROOT/}"
            fi
        fi
    done < <(find "${PROJECT_ROOT}/lib/oda" -name "*.py" -type f -print0)

    success "Python path fixes completed"
}

# ============================================================================
# Fix pyproject.toml
# ============================================================================
fix_pyproject() {
    local file="${PROJECT_ROOT}/pyproject.toml"

    if [[ ! -f "$file" ]]; then
        warn "pyproject.toml not found"
        return
    fi

    info "Fixing pyproject.toml..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Would update pyproject.toml"
        grep -n "scripts" "$file" || true
    else
        # Update package discovery
        sed -i 's|packages = \["scripts"\]|packages = ["lib.oda"]|g' "$file"
        sed -i 's|"scripts"|"lib.oda"|g' "$file"

        # Update console scripts if any
        sed -i 's|scripts\.|lib.oda.|g' "$file"

        success "Fixed pyproject.toml"
    fi
}

# ============================================================================
# Fix MCP Configuration
# ============================================================================
fix_mcp_config() {
    local mcp_files=(
        "${PROJECT_ROOT}/config/mcp.json"
        "${PROJECT_ROOT}/.mcp.json"
        "${HOME}/.mcp.json"
    )

    info "Fixing MCP configuration files..."

    for file in "${mcp_files[@]}"; do
        if [[ -f "$file" ]]; then
            if grep -q "scripts/" "$file" 2>/dev/null; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "[DRY-RUN] Would fix: $file"
                    grep -n "scripts" "$file" | head -5
                else
                    sed -i 's|scripts/mcp|lib/oda/mcp|g' "$file"
                    sed -i 's|scripts/ontology|lib/oda/ontology|g' "$file"
                    sed -i 's|"scripts"|"lib/oda"|g' "$file"
                    success "Fixed: $file"
                fi
            fi
        fi
    done
}

# ============================================================================
# Fix Docker Configuration
# ============================================================================
fix_docker_config() {
    info "Fixing Docker configuration..."

    local dockerfile="${PROJECT_ROOT}/Dockerfile"
    local compose="${PROJECT_ROOT}/docker-compose.sandbox.yml"

    # Fix Dockerfile
    if [[ -f "$dockerfile" ]]; then
        if grep -q "scripts" "$dockerfile" 2>/dev/null; then
            if [[ "$DRY_RUN" == "true" ]]; then
                info "[DRY-RUN] Would fix Dockerfile"
                grep -n "scripts" "$dockerfile" | head -5
            else
                sed -i 's|COPY scripts/|COPY lib/oda/|g' "$dockerfile"
                sed -i 's|COPY ./scripts|COPY ./lib/oda|g' "$dockerfile"
                success "Fixed Dockerfile"
            fi
        fi
    fi

    # Fix docker-compose
    if [[ -f "$compose" ]]; then
        if grep -q "scripts" "$compose" 2>/dev/null; then
            if [[ "$DRY_RUN" == "true" ]]; then
                info "[DRY-RUN] Would fix docker-compose.sandbox.yml"
                grep -n "scripts" "$compose" | head -5
            else
                sed -i 's|./scripts:|./lib/oda:|g' "$compose"
                sed -i 's|/app/scripts|/app/lib/oda|g' "$compose"
                success "Fixed docker-compose.sandbox.yml"
            fi
        fi
    fi
}

# ============================================================================
# Fix Claude Settings
# ============================================================================
fix_claude_settings() {
    info "Fixing Claude settings..."

    local settings_files=(
        "${PROJECT_ROOT}/.claude/settings.json"
        "${PROJECT_ROOT}/.claude/settings.local.json"
    )

    for file in "${settings_files[@]}"; do
        if [[ -f "$file" ]]; then
            if grep -q "scripts" "$file" 2>/dev/null; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "[DRY-RUN] Would fix: $file"
                else
                    sed -i 's|scripts/|lib/oda/|g' "$file"
                    success "Fixed: ${file#$PROJECT_ROOT/}"
                fi
            fi
        fi
    done
}

# ============================================================================
# Fix Test Fixtures
# ============================================================================
fix_test_fixtures() {
    info "Fixing test fixtures and configurations..."

    local test_configs=(
        "${PROJECT_ROOT}/tests/conftest.py"
        "${PROJECT_ROOT}/pytest.ini"
        "${PROJECT_ROOT}/setup.cfg"
    )

    for file in "${test_configs[@]}"; do
        if [[ -f "$file" ]]; then
            if grep -q "scripts" "$file" 2>/dev/null; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "[DRY-RUN] Would fix: ${file#$PROJECT_ROOT/}"
                else
                    sed -i 's|scripts\.|lib.oda.|g' "$file"
                    sed -i 's|scripts/|lib/oda/|g' "$file"
                    success "Fixed: ${file#$PROJECT_ROOT/}"
                fi
            fi
        fi
    done
}

# ============================================================================
# Verify Phase 3
# ============================================================================
verify_phase3() {
    info "Verifying Phase 3 completion..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Verification skipped in dry-run mode"
        return
    fi

    # Count remaining hardcoded paths in lib/oda
    local remaining=$(grep -r '"scripts/' "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | wc -l)
    remaining=$((remaining + $(grep -r "'scripts/" "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | wc -l)))

    info "Remaining hardcoded 'scripts/' paths in lib/oda: $remaining"

    if [[ "$remaining" -eq 0 ]]; then
        success "Phase 3 verification passed"
    else
        warn "Some hardcoded paths remain - please review manually"
        grep -r '"scripts/' "${PROJECT_ROOT}/lib/oda" --include="*.py" 2>/dev/null | head -5
    fi
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "Phase 3: Hardcoded Path Fixes"
    echo "=============================================="
    echo ""

    fix_python_paths
    fix_pyproject
    fix_mcp_config
    fix_docker_config
    fix_claude_settings
    fix_test_fixtures
    verify_phase3

    echo ""
    success "Phase 3 completed successfully!"
    echo ""
    info "Next step: Run migrate_phase4.sh to update environment configuration"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}This was a dry run. Run without --dry-run to apply changes.${NC}"
    fi
}

main "$@"
