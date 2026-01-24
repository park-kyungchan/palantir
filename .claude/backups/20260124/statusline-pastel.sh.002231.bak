#!/bin/bash
# Pastel Status Line for Claude Code
# Style: Information + Git Integration

# Pastel Colors (ANSI 256)
PASTEL_SKY="\033[38;5;153m"    # User
PASTEL_ROSE="\033[38;5;217m"   # Project
PASTEL_TEAL="\033[38;5;122m"   # Git
PASTEL_YELLOW="\033[38;5;228m" # Model
PASTEL_GREEN="\033[38;5;158m"  # Context
PASTEL_GRAY="\033[38;5;245m"   # Separators
RESET="\033[0m"

# Get user info
USER_INFO="${USER:-$(whoami)}"

# Get project directory (basename only)
PROJECT_DIR=$(basename "${PWD}")

# Get git branch and status
get_git_info() {
    if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
        local branch=$(git branch --show-current 2>/dev/null)
        if [ -z "$branch" ]; then
            branch="detached"
        fi

        # Check if clean or dirty
        if git diff --quiet HEAD -- 2>/dev/null; then
            echo "${branch} ✓"
        else
            echo "${branch} ✗"
        fi
    else
        echo ""
    fi
}

GIT_INFO=$(get_git_info)

# Get model name (shortened)
get_model_name() {
    local model="${CLAUDE_MODEL:-opus}"
    case "$model" in
        *opus*) echo "Opus" ;;
        *sonnet*) echo "Sonnet" ;;
        *haiku*) echo "Haiku" ;;
        *) echo "$model" ;;
    esac
}

MODEL_NAME=$(get_model_name)

# Get context usage (placeholder - actual value comes from Claude)
CONTEXT_PCT="${CLAUDE_CONTEXT_PCT:-0}"

# Build status line
STATUS=""

# User section
STATUS+="${PASTEL_SKY}👤 ${USER_INFO}${RESET}"
STATUS+="${PASTEL_GRAY} | ${RESET}"

# Project section with git
STATUS+="${PASTEL_ROSE}📁 ${PROJECT_DIR}${RESET}"
if [ -n "$GIT_INFO" ]; then
    STATUS+=" ${PASTEL_TEAL}[${GIT_INFO}]${RESET}"
fi
STATUS+="${PASTEL_GRAY} | ${RESET}"

# Model section
STATUS+="${PASTEL_YELLOW}🤖 ${MODEL_NAME}${RESET}"
STATUS+="${PASTEL_GRAY} | ${RESET}"

# Context section
STATUS+="${PASTEL_GREEN}📊 ${CONTEXT_PCT}% context${RESET}"

echo -e "$STATUS"
