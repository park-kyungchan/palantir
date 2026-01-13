#!/bin/bash
set -e

# ============================================================================
# Phase 4: Environment Configuration Update
# ============================================================================
# Purpose: Update MCP, PYTHONPATH, and environment configurations
# Scope: MCP server configs, .env files, shell profiles
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
LOG_FILE="${PROJECT_ROOT}/.migration_backup/phase4.log"

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
# Update MCP Configuration
# ============================================================================
update_mcp_config() {
    info "Updating MCP configuration..."

    local mcp_config="${PROJECT_ROOT}/.mcp.json"
    local home_mcp="${HOME}/.mcp.json"

    # Create updated MCP config for lib/oda
    local new_mcp_content='{
  "mcpServers": {
    "oda-ontology": {
      "command": "python",
      "args": ["-m", "lib.oda.mcp.ontology_server"],
      "cwd": "'"${PROJECT_ROOT}"'",
      "env": {
        "PYTHONPATH": "'"${PROJECT_ROOT}"'",
        "ODA_DB_PATH": "'"${PROJECT_ROOT}/.agent/tmp/ontology.db"'"
      }
    },
    "github-mcp-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}'

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Would update MCP config at: $mcp_config"
        echo "New content:"
        echo "$new_mcp_content" | head -20
    else
        # Backup existing config
        if [[ -f "$mcp_config" ]]; then
            cp "$mcp_config" "${mcp_config}.backup.$(date +%Y%m%d_%H%M%S)"
        fi

        echo "$new_mcp_content" > "$mcp_config"
        success "Updated MCP config: $mcp_config"

        # Update home MCP if exists
        if [[ -f "$home_mcp" ]]; then
            cp "$home_mcp" "${home_mcp}.backup.$(date +%Y%m%d_%H%M%S)"
            # Update PYTHONPATH in home MCP
            sed -i 's|"PYTHONPATH": "[^"]*scripts[^"]*"|"PYTHONPATH": "'"${PROJECT_ROOT}"'"|g' "$home_mcp"
            sed -i 's|scripts/mcp|lib/oda/mcp|g' "$home_mcp"
            sed -i 's|scripts\.mcp|lib.oda.mcp|g' "$home_mcp"
            success "Updated home MCP config: $home_mcp"
        fi
    fi
}

# ============================================================================
# Update Environment Files
# ============================================================================
update_env_files() {
    info "Updating environment files..."

    local env_files=(
        "${PROJECT_ROOT}/.env"
        "${PROJECT_ROOT}/.env.local"
        "${PROJECT_ROOT}/.env.development"
    )

    for file in "${env_files[@]}"; do
        if [[ -f "$file" ]]; then
            if grep -q "scripts" "$file" 2>/dev/null; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "[DRY-RUN] Would update: $file"
                else
                    sed -i 's|scripts/|lib/oda/|g' "$file"
                    sed -i 's|PYTHONPATH=.*scripts|PYTHONPATH='"${PROJECT_ROOT}"'|g' "$file"
                    success "Updated: $file"
                fi
            fi
        fi
    done

    # Create/update .env if needed
    local env_file="${PROJECT_ROOT}/.env"
    if [[ "$DRY_RUN" == "false" ]]; then
        if [[ ! -f "$env_file" ]] || ! grep -q "PYTHONPATH" "$env_file"; then
            echo "# ODA Environment Configuration" >> "$env_file"
            echo "PYTHONPATH=${PROJECT_ROOT}" >> "$env_file"
            echo "ODA_ROOT=${PROJECT_ROOT}/lib/oda" >> "$env_file"
            echo "ODA_DB_PATH=${PROJECT_ROOT}/.agent/tmp/ontology.db" >> "$env_file"
            success "Added PYTHONPATH to .env"
        fi
    fi
}

# ============================================================================
# Update Shell Profiles
# ============================================================================
update_shell_profiles() {
    info "Updating shell profiles..."

    local profiles=(
        "${HOME}/.bashrc"
        "${HOME}/.zshrc"
        "${PROJECT_ROOT}/.bashrc"
    )

    local pythonpath_line="export PYTHONPATH=\"${PROJECT_ROOT}:\${PYTHONPATH}\""
    local oda_alias="alias oda='python -m lib.oda.tools.cli'"

    for profile in "${profiles[@]}"; do
        if [[ -f "$profile" ]]; then
            # Check if already has our PYTHONPATH
            if ! grep -q "PYTHONPATH.*park-kyungchan/palantir" "$profile" 2>/dev/null; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "[DRY-RUN] Would add PYTHONPATH to: $profile"
                else
                    echo "" >> "$profile"
                    echo "# ODA Migration - PYTHONPATH" >> "$profile"
                    echo "$pythonpath_line" >> "$profile"
                    echo "$oda_alias" >> "$profile"
                    success "Updated: $profile"
                fi
            fi

            # Update any existing scripts references
            if grep -q "scripts/" "$profile" 2>/dev/null; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "[DRY-RUN] Would update scripts/ references in: $profile"
                else
                    sed -i 's|scripts/|lib/oda/|g' "$profile"
                fi
            fi
        fi
    done
}

# ============================================================================
# Update CLAUDE.md
# ============================================================================
update_claude_md() {
    info "Updating CLAUDE.md configuration..."

    local claude_md="${PROJECT_ROOT}/.claude/CLAUDE.md"
    local home_claude_md="${HOME}/.claude/CLAUDE.md"

    for file in "$claude_md" "$home_claude_md"; do
        if [[ -f "$file" ]]; then
            if grep -q "scripts/" "$file" 2>/dev/null; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    info "[DRY-RUN] Would update: $file"
                else
                    # Update workspace paths
                    sed -i 's|scripts/ontology|lib/oda/ontology|g' "$file"
                    sed -i 's|scripts/mcp|lib/oda/mcp|g' "$file"
                    sed -i 's|"scripts"|"lib/oda"|g' "$file"
                    success "Updated: $file"
                fi
            fi
        fi
    done
}

# ============================================================================
# Update VS Code Settings
# ============================================================================
update_vscode_settings() {
    info "Updating VS Code settings..."

    local vscode_settings="${PROJECT_ROOT}/.vscode/settings.json"

    if [[ -f "$vscode_settings" ]]; then
        if grep -q "scripts" "$vscode_settings" 2>/dev/null; then
            if [[ "$DRY_RUN" == "true" ]]; then
                info "[DRY-RUN] Would update: $vscode_settings"
            else
                sed -i 's|"scripts/|"lib/oda/|g' "$vscode_settings"
                sed -i 's|scripts\.|lib.oda.|g' "$vscode_settings"
                success "Updated VS Code settings"
            fi
        fi
    fi

    # Create/update python analysis settings
    if [[ "$DRY_RUN" == "false" ]]; then
        local python_settings='{
  "python.analysis.extraPaths": [
    "${workspaceFolder}",
    "${workspaceFolder}/lib",
    "${workspaceFolder}/lib/oda"
  ],
  "python.envFile": "${workspaceFolder}/.env"
}'

        if [[ ! -f "$vscode_settings" ]]; then
            mkdir -p "${PROJECT_ROOT}/.vscode"
            echo "$python_settings" > "$vscode_settings"
            success "Created VS Code settings"
        fi
    fi
}

# ============================================================================
# Create lib/__init__.py
# ============================================================================
create_lib_init() {
    info "Ensuring lib/__init__.py exists..."

    local lib_init="${PROJECT_ROOT}/lib/__init__.py"

    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p "${PROJECT_ROOT}/lib"
        if [[ ! -f "$lib_init" ]]; then
            echo '"""ODA Library Package."""' > "$lib_init"
            success "Created lib/__init__.py"
        fi
    fi
}

# ============================================================================
# Verify Phase 4
# ============================================================================
verify_phase4() {
    info "Verifying Phase 4 completion..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY-RUN] Verification skipped in dry-run mode"
        return
    fi

    # Check MCP config
    if [[ -f "${PROJECT_ROOT}/.mcp.json" ]]; then
        if grep -q "lib.oda.mcp" "${PROJECT_ROOT}/.mcp.json"; then
            success "MCP config updated correctly"
        else
            warn "MCP config may need manual review"
        fi
    fi

    # Check PYTHONPATH in .env
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        if grep -q "PYTHONPATH" "${PROJECT_ROOT}/.env"; then
            success "PYTHONPATH configured in .env"
        fi
    fi

    success "Phase 4 verification completed"
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo "=============================================="
    echo "Phase 4: Environment Configuration Update"
    echo "=============================================="
    echo ""

    update_mcp_config
    update_env_files
    update_shell_profiles
    update_claude_md
    update_vscode_settings
    create_lib_init
    verify_phase4

    echo ""
    success "Phase 4 completed successfully!"
    echo ""
    info "Next step: Run migrate_phase5_test.sh to verify migration"
    echo ""
    warn "IMPORTANT: Restart your shell or run 'source ~/.bashrc' to apply changes"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}This was a dry run. Run without --dry-run to apply changes.${NC}"
    fi
}

main "$@"
