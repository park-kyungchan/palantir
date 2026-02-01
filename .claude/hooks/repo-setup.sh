#!/bin/bash
# ============================================================
# Claude Code Setup Hook (v2.1.10+)
# ============================================================
# Triggered by: claude --init | --init-only | --maintenance
# Purpose: Repository initialization and maintenance
# ============================================================

set -e

WORKSPACE_ROOT="${ORION_WORKSPACE_ROOT:-/home/palantir}"
AGENT_DIR="${WORKSPACE_ROOT}/.agent"
CLAUDE_DIR="${WORKSPACE_ROOT}/.claude"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# ============================================================
# 1. Directory Structure Initialization
# ============================================================
log_info "Initializing directory structure..."

mkdir -p "${AGENT_DIR}/prompts"
mkdir -p "${AGENT_DIR}/logs"
mkdir -p "${AGENT_DIR}/tmp"
mkdir -p "${AGENT_DIR}/outputs"

log_success "Directory structure ready"

# ============================================================
# 2. Workload State Check
# ============================================================
ACTIVE_WORKLOAD="${AGENT_DIR}/prompts/_active_workload.yaml"

if [[ -f "$ACTIVE_WORKLOAD" ]]; then
    CURRENT_SLUG=$(grep -oP 'slug:\s*\K[^\s]+' "$ACTIVE_WORKLOAD" 2>/dev/null || echo "")
    if [[ -n "$CURRENT_SLUG" ]]; then
        log_info "Active workload found: $CURRENT_SLUG"
    fi
else
    log_info "No active workload"
fi

# ============================================================
# 3. Dependency Check
# ============================================================
log_info "Checking dependencies..."

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1: $(command -v $1)"
    else
        log_warn "$1: not found"
    fi
}

check_command python3
check_command node
check_command npm
check_command git
check_command gh

# ============================================================
# 4. Git Repository Check
# ============================================================
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
    log_success "Git repository: branch=$BRANCH"
else
    log_warn "Not a git repository"
fi

# ============================================================
# 5. MCP Server Status
# ============================================================
MCP_CONFIG="${WORKSPACE_ROOT}/.mcp.json"
if [[ -f "$MCP_CONFIG" ]]; then
    MCP_COUNT=$(grep -c '"type":' "$MCP_CONFIG" 2>/dev/null || echo "0")
    log_success "MCP servers configured: $MCP_COUNT"
else
    log_info "No MCP configuration found"
fi

# ============================================================
# 6. Cleanup (Maintenance Mode)
# ============================================================
# Clean up old temp files (older than 7 days)
if [[ -d "${AGENT_DIR}/tmp" ]]; then
    find "${AGENT_DIR}/tmp" -type f -mtime +7 -delete 2>/dev/null || true
    log_info "Cleaned up old temp files"
fi

# ============================================================
# Output Summary
# ============================================================
echo ""
echo "=========================================="
echo "  Setup Complete"
echo "=========================================="
echo "  Workspace: ${WORKSPACE_ROOT}"
echo "  Agent Dir: ${AGENT_DIR}"
echo "=========================================="
