#!/bin/bash
# ============================================
# Claude Code v2.2+ Native Capabilities Setup
# Codebase Improvement Planning Configuration
# ============================================

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Claude Code v2.2+ Native Capabilities Setup                  ║"
echo "║  Codebase Improvement Planning Configuration                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLAUDE_USER_DIR="$HOME/.claude"
CLAUDE_PROJECT_DIR=".claude"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================
# Functions
# ============================================

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

create_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        print_success "Created directory: $1"
    else
        print_warning "Directory exists: $1"
    fi
}

backup_if_exists() {
    if [ -f "$1" ]; then
        backup_file="$1.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$1" "$backup_file"
        print_warning "Backed up existing file to: $backup_file"
    fi
}

# ============================================
# Step 1: Create User-Level Structure
# ============================================

print_step "Creating user-level Claude Code structure..."

create_directory "$CLAUDE_USER_DIR"
create_directory "$CLAUDE_USER_DIR/skills"
create_directory "$CLAUDE_USER_DIR/agents"
create_directory "$CLAUDE_USER_DIR/commands"
create_directory "$CLAUDE_USER_DIR/rules"
create_directory "$CLAUDE_USER_DIR/tasks"
create_directory "$CLAUDE_USER_DIR/tmp"

# ============================================
# Step 2: Create Project-Level Structure
# ============================================

print_step "Creating project-level Claude Code structure..."

create_directory "$CLAUDE_PROJECT_DIR"
create_directory "$CLAUDE_PROJECT_DIR/skills"
create_directory "$CLAUDE_PROJECT_DIR/agents"
create_directory "$CLAUDE_PROJECT_DIR/commands"
create_directory "$CLAUDE_PROJECT_DIR/rules"
create_directory "$CLAUDE_PROJECT_DIR/plans"
create_directory "$CLAUDE_PROJECT_DIR/reports"
create_directory "$CLAUDE_PROJECT_DIR/checkpoints"
create_directory "$CLAUDE_PROJECT_DIR/sessions"

# ============================================
# Step 3: Install Skills
# ============================================

print_step "Installing codebase improvement skills..."

# Check if skill files exist in script directory
if [ -d "$SCRIPT_DIR/skills" ]; then
    cp -r "$SCRIPT_DIR/skills/"* "$CLAUDE_USER_DIR/skills/" 2>/dev/null || true
    print_success "Installed skills to user directory"
fi

# Also install to project if in a project
if [ -d "$CLAUDE_PROJECT_DIR/skills" ]; then
    cp -r "$SCRIPT_DIR/skills/"* "$CLAUDE_PROJECT_DIR/skills/" 2>/dev/null || true
    print_success "Installed skills to project directory"
fi

# ============================================
# Step 4: Install Agents
# ============================================

print_step "Installing analysis agents..."

if [ -d "$SCRIPT_DIR/agents" ]; then
    cp -r "$SCRIPT_DIR/agents/"* "$CLAUDE_USER_DIR/agents/" 2>/dev/null || true
    print_success "Installed agents to user directory"
fi

# ============================================
# Step 5: Install Commands
# ============================================

print_step "Installing custom commands..."

if [ -d "$SCRIPT_DIR/commands" ]; then
    cp -r "$SCRIPT_DIR/commands/"* "$CLAUDE_USER_DIR/commands/" 2>/dev/null || true
    print_success "Installed commands to user directory"
fi

# ============================================
# Step 6: Install Settings Template
# ============================================

print_step "Installing settings template..."

if [ -f "$SCRIPT_DIR/templates/settings.json" ]; then
    if [ ! -f "$CLAUDE_PROJECT_DIR/settings.json" ]; then
        cp "$SCRIPT_DIR/templates/settings.json" "$CLAUDE_PROJECT_DIR/settings.json"
        print_success "Installed settings.json to project"
    else
        print_warning "settings.json already exists, skipping..."
    fi
fi

# ============================================
# Step 7: Update Shell Configuration
# ============================================

print_step "Updating shell configuration..."

SHELL_RC="$HOME/.bashrc"
[ -n "$ZSH_VERSION" ] && SHELL_RC="$HOME/.zshrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"

# Check if already configured
if ! grep -q "CLAUDE_CODE_TASK_LIST_ID" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << 'SHELL_CONFIG'

# ============================================
# Claude Code v2.2+ Configuration
# ============================================

# Task Management
export CLAUDE_CODE_TASK_LIST_ID="main-dev"
export CLAUDE_CONFIG_DIR="$HOME/.claude"
export CLAUDE_CODE_TMPDIR="$HOME/.claude/tmp"

# Performance
export MAX_THINKING_TOKENS=10000
export BASH_DEFAULT_TIMEOUT_MS=300000
export BASH_MAX_TIMEOUT_MS=600000
export MAX_MCP_OUTPUT_TOKENS=25000

# Feature Toggles
export DISABLE_PROMPT_CACHING_HAIKU=0
export DISABLE_PROMPT_CACHING_OPUS=0
export DISABLE_PROMPT_CACHING_SONNET=0
export USE_BUILTIN_RIPGREP=1

# Aliases
alias cc='claude'
alias ccr='claude --resume'
alias ccc='claude --continue'
alias ccp='claude --permission-mode plan'

# Task-specific sessions
alias cc-dev='CLAUDE_CODE_TASK_LIST_ID=dev-main claude'
alias cc-refactor='CLAUDE_CODE_TASK_LIST_ID=refactor claude'
alias cc-test='CLAUDE_CODE_TASK_LIST_ID=testing claude'
alias cc-docs='CLAUDE_CODE_TASK_LIST_ID=documentation claude'
alias cc-improve='CLAUDE_CODE_TASK_LIST_ID=improvement claude'

# Model shortcuts
alias cc-opus='claude --model opus'
alias cc-sonnet='claude --model sonnet'

# Debugging
alias cc-debug='claude --debug --mcp-debug --verbose'

# Quick analysis
cc-analyze() {
    claude -p "Analyze the codebase and provide improvement recommendations" --output-format json
}

SHELL_CONFIG

    print_success "Added Claude Code configuration to $SHELL_RC"
else
    print_warning "Claude Code configuration already exists in $SHELL_RC"
fi

# ============================================
# Step 8: Update .gitignore
# ============================================

print_step "Updating .gitignore..."

if [ -f ".gitignore" ]; then
    if ! grep -q ".claude/settings.local.json" ".gitignore" 2>/dev/null; then
        cat >> ".gitignore" << 'GITIGNORE'

# Claude Code
.claude/settings.local.json
.claude/checkpoints/
.claude/sessions/
.claude/reports/
.claude/tmp/
GITIGNORE
        print_success "Added Claude Code entries to .gitignore"
    else
        print_warning "Claude Code entries already in .gitignore"
    fi
else
    print_warning "No .gitignore found, skipping..."
fi

# ============================================
# Step 9: Create CLAUDE.md if not exists
# ============================================

print_step "Checking for CLAUDE.md..."

if [ ! -f "CLAUDE.md" ]; then
    cat > "CLAUDE.md" << 'CLAUDE_MD'
# Project Context for Claude Code

## Overview
[Add project description here]

## Tech Stack
- Language: [e.g., TypeScript, Python]
- Framework: [e.g., React, FastAPI]
- Database: [e.g., PostgreSQL, MongoDB]

## Directory Structure
```
src/
├── [directory structure here]
```

## Build & Run Commands
```bash
# Development
[dev command]

# Build
[build command]

# Test
[test command]

# Lint
[lint command]
```

## Code Standards
- [Standard 1]
- [Standard 2]

## Git Workflow
- Branch naming: `feature/`, `fix/`, `refactor/`
- Commit format: `type(scope): description`

## Session Management
- Use CLAUDE_CODE_TASK_LIST_ID for parallel work
- Run /checkpoint before major changes
- Check .claude/reports/ for analysis results

## Current Priorities
1. [Priority 1]
2. [Priority 2]

## Known Issues / Tech Debt
- [ ] [Issue 1]
- [ ] [Issue 2]
CLAUDE_MD
    print_success "Created CLAUDE.md template"
else
    print_warning "CLAUDE.md already exists"
fi

# ============================================
# Step 10: Copy reference documentation
# ============================================

print_step "Installing reference documentation..."

if [ -f "$SCRIPT_DIR/claude-code-native-capabilities-v2.2.md" ]; then
    cp "$SCRIPT_DIR/claude-code-native-capabilities-v2.2.md" "$CLAUDE_PROJECT_DIR/"
    print_success "Installed native capabilities reference"
fi

# ============================================
# Final Summary
# ============================================

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Setup Complete!                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Created Structure:${NC}"
echo "  ~/.claude/              (User-level configuration)"
echo "  .claude/                (Project-level configuration)"
echo ""
echo -e "${GREEN}Installed Components:${NC}"
echo "  • Codebase Improvement Planner skill"
echo "  • Code Analyzer agent"
echo "  • /improve command"
echo "  • Settings template"
echo "  • Shell aliases and functions"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Reload shell: source $SHELL_RC"
echo "  2. Edit CLAUDE.md with your project details"
echo "  3. Review .claude/settings.json"
echo "  4. Start Claude Code: claude"
echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo "  • cc                    - Start Claude Code"
echo "  • cc-improve            - Start improvement session"
echo "  • cc-analyze            - Quick codebase analysis"
echo "  • /improve full         - Run full improvement workflow"
echo "  • /skills               - View available skills"
echo "  • /agents               - View available agents"
echo ""
