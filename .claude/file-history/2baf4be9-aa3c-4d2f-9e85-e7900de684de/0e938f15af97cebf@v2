#!/bin/bash
# =============================================================================
# Boris Cherny Workspace Setup Script
# =============================================================================
# Creates isolated git worktrees for parallel Claude Code sessions
#
# Usage: ./setup-workspaces.sh <repo-url> [base-dir]
#
# Example:
#   ./setup-workspaces.sh git@github.com:user/project.git ~/workspace
#
# Creates:
#   ~/workspace/repo-main     (main branch)
#   ~/workspace/repo-feature  (feature development)
#   ~/workspace/repo-bugfix   (hotfix work)
#   ~/workspace/repo-review   (code review)
#   ~/workspace/repo-sandbox  (experiments)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arguments
REPO_URL="${1:-}"
BASE_DIR="${2:-$HOME/workspace}"

# Validate input
if [ -z "$REPO_URL" ]; then
    echo -e "${RED}Error: Repository URL required${NC}"
    echo "Usage: $0 <repo-url> [base-dir]"
    echo "Example: $0 git@github.com:user/project.git ~/workspace"
    exit 1
fi

# Extract repo name from URL
REPO_NAME=$(basename "$REPO_URL" .git)

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Boris Cherny Workspace Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Repository: ${GREEN}$REPO_URL${NC}"
echo -e "Base Directory: ${GREEN}$BASE_DIR${NC}"
echo ""

# Create base directory
mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

# Clone main repository if not exists
MAIN_DIR="$BASE_DIR/repo-main"
if [ ! -d "$MAIN_DIR" ]; then
    echo -e "${YELLOW}Cloning main repository...${NC}"
    git clone "$REPO_URL" repo-main
    cd repo-main

    # Enable worktrees
    git config extensions.worktreeConfig true

    cd ..
else
    echo -e "${GREEN}Main repository already exists${NC}"
fi

# Create worktrees for parallel sessions
create_worktree() {
    local name=$1
    local branch=$2
    local dir="$BASE_DIR/$name"

    if [ -d "$dir" ]; then
        echo -e "${GREEN}Worktree '$name' already exists${NC}"
        return
    fi

    echo -e "${YELLOW}Creating worktree: $name (branch: $branch)${NC}"

    cd "$MAIN_DIR"

    # Create branch if it doesn't exist
    if ! git show-ref --verify --quiet "refs/heads/$branch"; then
        git branch "$branch" 2>/dev/null || true
    fi

    # Create worktree
    git worktree add "$dir" "$branch" 2>/dev/null || \
        git worktree add -b "$branch" "$dir" 2>/dev/null || \
        git worktree add "$dir" HEAD --detach

    cd "$dir"

    # Copy .claude directory to each worktree for consistent configuration
    if [ -d "$MAIN_DIR/.claude" ]; then
        cp -r "$MAIN_DIR/.claude" "$dir/" 2>/dev/null || true
    fi

    echo -e "${GREEN}Created: $dir${NC}"
}

# Create worktrees
create_worktree "repo-feature" "feature/dev"
create_worktree "repo-bugfix" "hotfix/current"
create_worktree "repo-review" "review/temp"
create_worktree "repo-sandbox" "sandbox/experiment"

# Create workspace-wide .claude configuration
WORKSPACE_CLAUDE="$BASE_DIR/.claude"
mkdir -p "$WORKSPACE_CLAUDE"

cat > "$WORKSPACE_CLAUDE/workspace-config.json" << 'EOF'
{
  "workspace_type": "boris_parallel",
  "sessions": {
    "repo-main": {
      "purpose": "Primary development",
      "auto_start": true
    },
    "repo-feature": {
      "purpose": "Feature branches",
      "auto_start": true
    },
    "repo-bugfix": {
      "purpose": "Hotfixes",
      "auto_start": false
    },
    "repo-review": {
      "purpose": "Code review",
      "auto_start": false
    },
    "repo-sandbox": {
      "purpose": "Experiments",
      "auto_start": false
    }
  },
  "sync_pattern": "manual",
  "notification_mode": "desktop"
}
EOF

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Workspaces created:"
echo -e "  ${BLUE}repo-main${NC}     - Primary development"
echo -e "  ${BLUE}repo-feature${NC}  - Feature branches"
echo -e "  ${BLUE}repo-bugfix${NC}   - Hotfixes"
echo -e "  ${BLUE}repo-review${NC}   - Code review"
echo -e "  ${BLUE}repo-sandbox${NC}  - Experiments"
echo ""
echo "To start parallel sessions:"
echo -e "  ${YELLOW}mprocs --config ~/.claude/boris-workflow/mprocs.yaml${NC}"
echo ""
echo "To clean up worktrees:"
echo -e "  ${YELLOW}cd $MAIN_DIR && git worktree list${NC}"
echo -e "  ${YELLOW}git worktree remove <path>${NC}"
