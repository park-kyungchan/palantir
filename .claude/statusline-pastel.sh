#!/bin/bash
# Pastel Status Line for Claude Code
# Style: Information + Git Integration + Task Management

# Pastel Colors (ANSI 256)
PASTEL_SKY="\033[38;5;153m"    # User
PASTEL_ROSE="\033[38;5;217m"   # Project
PASTEL_TEAL="\033[38;5;122m"   # Git
PASTEL_YELLOW="\033[38;5;228m" # Model
PASTEL_GREEN="\033[38;5;158m"  # Context
PASTEL_PURPLE="\033[38;5;183m" # Terminal Role
PASTEL_ORANGE="\033[38;5;216m" # Task Info
PASTEL_GRAY="\033[38;5;245m"   # Separators
RESET="\033[0m"

# Task directory
TASK_DIR="${HOME}/.claude/tasks"

# Read JSON input from stdin
INPUT=$(cat)

# Get terminal role based on environment
get_terminal_role() {
    if [ -n "$CLAUDE_CODE_TASK_LIST_ID" ]; then
        # Extract last part of task list ID as worker identifier
        local worker_id=$(echo "$CLAUDE_CODE_TASK_LIST_ID" | awk -F'-' '{print toupper(substr($NF,1,1))}')
        echo "Worker-${worker_id}"
    else
        echo "Orchestrator"
    fi
}

# Get task statistics
get_task_stats() {
    if [ ! -d "$TASK_DIR" ]; then
        echo ""
        return
    fi

    local pending=0
    local in_progress=0
    local completed=0

    for task_file in "$TASK_DIR"/*.json 2>/dev/null; do
        [ -f "$task_file" ] || continue

        # Extract status using grep and sed (no jq dependency)
        local status=$(grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' "$task_file" 2>/dev/null | sed 's/.*"\([^"]*\)".*/\1/')

        case "$status" in
            pending) pending=$((pending + 1)) ;;
            in_progress) in_progress=$((in_progress + 1)) ;;
            completed) completed=$((completed + 1)) ;;
        esac
    done

    local total=$((pending + in_progress + completed))

    if [ $total -eq 0 ]; then
        echo ""
    else
        echo "P:${pending}/I:${in_progress}/C:${completed}"
    fi
}

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

# Get model name from JSON input or fallback to env
get_model_name() {
    # Try to extract from JSON input first
    local model=$(echo "$INPUT" | grep -o '"display_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' | head -n1)

    if [ -z "$model" ]; then
        # Fallback to environment variable
        model="${CLAUDE_MODEL:-opus}"
    fi

    case "$model" in
        *Opus*|*opus*) echo "Opus" ;;
        *Sonnet*|*sonnet*) echo "Sonnet" ;;
        *Haiku*|*haiku*) echo "Haiku" ;;
        *) echo "$model" ;;
    esac
}

MODEL_NAME=$(get_model_name)

# Get context usage from JSON input or fallback to env
get_context_usage() {
    # Try to extract remaining_percentage from JSON
    local remaining=$(echo "$INPUT" | grep -o '"remaining_percentage"[[:space:]]*:[[:space:]]*[0-9.]*' | sed 's/.*:[[:space:]]*\([0-9.]*\)/\1/')

    if [ -n "$remaining" ]; then
        local used=$(echo "100 - $remaining" | bc 2>/dev/null || echo "0")
        printf "%.0f" "$used"
    else
        echo "${CLAUDE_CONTEXT_PCT:-0}"
    fi
}

CONTEXT_PCT=$(get_context_usage)

# Get terminal role and task stats
TERMINAL_ROLE=$(get_terminal_role)
TASK_STATS=$(get_task_stats)

# Build status line
STATUS=""

# Terminal role section
STATUS+="${PASTEL_PURPLE}⚡ ${TERMINAL_ROLE}${RESET}"
STATUS+="${PASTEL_GRAY} | ${RESET}"

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

# Task stats section (only if tasks exist)
if [ -n "$TASK_STATS" ]; then
    STATUS+="${PASTEL_GRAY} | ${RESET}"
    STATUS+="${PASTEL_ORANGE}📋 ${TASK_STATS}${RESET}"
fi

echo -e "$STATUS"
