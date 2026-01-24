#!/bin/bash
# =============================================================================
# Orchestrator Statusline for Claude Code
# =============================================================================
# Features:
#   - Worker status tracking (B/C/D)
#   - Phase progress visualization
#   - Real-time cost estimation
#   - Git integration
#   - Context usage with visual bar
# =============================================================================

set -o pipefail

# =============================================================================
# PASTEL COLOR PALETTE (256 color)
# =============================================================================
# Primary colors
P_SKY="\033[38;5;117m"      # Light sky blue
P_ROSE="\033[38;5;218m"     # Soft rose
P_MINT="\033[38;5;158m"     # Mint green
P_PEACH="\033[38;5;216m"    # Peach
P_LAVENDER="\033[38;5;183m" # Lavender
P_LEMON="\033[38;5;229m"    # Lemon yellow
P_CORAL="\033[38;5;210m"    # Coral
P_AQUA="\033[38;5;123m"     # Aquamarine

# Status colors
S_SUCCESS="\033[38;5;157m"  # Light green (completed)
S_PROGRESS="\033[38;5;228m" # Yellow (in progress)
S_PENDING="\033[38;5;252m"  # Light gray (pending)
S_BLOCKED="\033[38;5;210m"  # Coral (blocked)

# Utility
DIM="\033[38;5;245m"        # Dim gray for separators
BOLD="\033[1m"
RESET="\033[0m"

# =============================================================================
# CONFIGURATION
# =============================================================================
PROGRESS_FILE="${HOME}/.agent/prompts/_progress.yaml"
SESSION_FILE="${HOME}/.agent/tmp/current_session.json"

# =============================================================================
# INPUT HANDLING
# =============================================================================
INPUT=$(cat 2>/dev/null || echo "{}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Safe YAML value extraction (no jq dependency)
yaml_get() {
    local key="$1"
    local file="$2"
    grep -E "^[[:space:]]*${key}:" "$file" 2>/dev/null | head -1 | sed 's/.*:[[:space:]]*"\?\([^"]*\)"\?/\1/' | tr -d '"'
}

# Get worker status from _progress.yaml
get_worker_status() {
    local terminal="$1"
    if [ ! -f "$PROGRESS_FILE" ]; then
        echo "?"
        return
    fi

    # Extract status for terminal
    local status=$(grep -A5 "terminal-${terminal}:" "$PROGRESS_FILE" 2>/dev/null | grep "status:" | head -1 | sed 's/.*status:[[:space:]]*"\?\([^"]*\)"\?.*/\1/')

    case "$status" in
        completed) echo "✓" ;;
        assigned|in_progress) echo "◐" ;;
        idle) echo "○" ;;
        blocked) echo "✗" ;;
        *) echo "?" ;;
    esac
}

# Get worker status color
get_worker_color() {
    local terminal="$1"
    if [ ! -f "$PROGRESS_FILE" ]; then
        echo "$DIM"
        return
    fi

    local status=$(grep -A5 "terminal-${terminal}:" "$PROGRESS_FILE" 2>/dev/null | grep "status:" | head -1 | sed 's/.*status:[[:space:]]*"\?\([^"]*\)"\?.*/\1/')

    case "$status" in
        completed) echo "$S_SUCCESS" ;;
        assigned|in_progress) echo "$S_PROGRESS" ;;
        idle) echo "$S_PENDING" ;;
        blocked) echo "$S_BLOCKED" ;;
        *) echo "$DIM" ;;
    esac
}

# Get phase progress
get_phase_progress() {
    if [ ! -f "$PROGRESS_FILE" ]; then
        echo "0/0"
        return
    fi

    local total=$(grep -c "^  phase[0-9]:" "$PROGRESS_FILE" 2>/dev/null || echo "0")
    local completed=$(grep -A3 "^  phase[0-9]:" "$PROGRESS_FILE" 2>/dev/null | grep -c 'status:.*completed' || echo "0")

    echo "${completed}/${total}"
}

# Get project status
get_project_status() {
    if [ ! -f "$PROGRESS_FILE" ]; then
        echo "NO_PROJECT"
        return
    fi

    local status=$(grep "projectStatus:" "$PROGRESS_FILE" 2>/dev/null | head -1 | sed 's/.*:[[:space:]]*"\?\([^"]*\)"\?.*/\1/')
    echo "${status:-UNKNOWN}"
}

# Get model name from JSON input
get_model() {
    local model=$(echo "$INPUT" | grep -o '"display_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' | head -1)

    case "$model" in
        *Opus*|*opus*) echo "🧠 Opus" ;;
        *Sonnet*|*sonnet*) echo "🎵 Sonnet" ;;
        *Haiku*|*haiku*) echo "⚡ Haiku" ;;
        "") echo "🤖 Claude" ;;
        *) echo "🤖 $model" ;;
    esac
}

# Get context usage with visual bar
get_context_bar() {
    local remaining=$(echo "$INPUT" | grep -o '"remaining_percentage"[[:space:]]*:[[:space:]]*[0-9.]*' | sed 's/.*:[[:space:]]*\([0-9.]*\)/\1/')

    if [ -z "$remaining" ]; then
        echo "░░░░░░░░░░ ?%"
        return
    fi

    local used=$(echo "100 - $remaining" | bc 2>/dev/null || echo "0")
    local used_int=${used%.*}
    local filled=$((used_int / 10))
    local empty=$((10 - filled))

    local bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done

    # Color based on usage
    if [ "$used_int" -ge 80 ]; then
        echo -e "${S_BLOCKED}${bar}${RESET} ${used_int}%"
    elif [ "$used_int" -ge 60 ]; then
        echo -e "${S_PROGRESS}${bar}${RESET} ${used_int}%"
    else
        echo -e "${S_SUCCESS}${bar}${RESET} ${used_int}%"
    fi
}

# Get git info
get_git_info() {
    if ! git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
        echo ""
        return
    fi

    local branch=$(git branch --show-current 2>/dev/null || echo "detached")
    local dirty=""

    if ! git diff --quiet HEAD -- 2>/dev/null; then
        dirty="*"
    fi

    echo "${branch}${dirty}"
}

# Get session role
get_role() {
    if [ -n "$CLAUDE_CODE_TASK_LIST_ID" ]; then
        local id=$(echo "$CLAUDE_CODE_TASK_LIST_ID" | awk -F'-' '{print toupper(substr($NF,1,1))}')
        echo "Worker-${id}"
    else
        echo "Orchestrator"
    fi
}

# Get time
get_time() {
    date +"%H:%M"
}

# Get Project Task ID from session registry
get_task_list_id() {
    if [ -f "$SESSION_FILE" ]; then
        local tid=$(grep -o '"taskListId"[[:space:]]*:[[:space:]]*"[^"]*"' "$SESSION_FILE" 2>/dev/null | sed 's/.*"\([^"]*\)".*/\1/')
        if [ -n "$tid" ]; then
            echo "$tid"
            return
        fi
    fi

    # Fallback to environment variable
    if [ -n "$CLAUDE_CODE_TASK_LIST_ID" ]; then
        echo "$CLAUDE_CODE_TASK_LIST_ID"
        return
    fi

    echo ""
}

# =============================================================================
# BUILD STATUSLINE
# =============================================================================

# Get all values
ROLE=$(get_role)
PROJECT=$(basename "$PWD")
GIT_BRANCH=$(get_git_info)
MODEL=$(get_model)
CONTEXT_BAR=$(get_context_bar)
PHASE_PROGRESS=$(get_phase_progress)
PROJECT_STATUS=$(get_project_status)
TASK_LIST_ID=$(get_task_list_id)
TIME=$(get_time)

# Worker statuses
W_B=$(get_worker_status "b")
W_C=$(get_worker_status "c")
W_D=$(get_worker_status "d")
C_B=$(get_worker_color "b")
C_C=$(get_worker_color "c")
C_D=$(get_worker_color "d")

# =============================================================================
# COMPOSE OUTPUT
# =============================================================================

# Line 1: Role + Task ID + Project + Git
LINE1=""
if [ "$ROLE" = "Orchestrator" ]; then
    LINE1+="${P_LAVENDER}◆ ${ROLE}${RESET}"
else
    LINE1+="${P_AQUA}◇ ${ROLE}${RESET}"
fi

# Task List ID (shared across terminals)
if [ -n "$TASK_LIST_ID" ]; then
    LINE1+="${DIM} │ ${RESET}"
    LINE1+="${P_CORAL}⬢ ${TASK_LIST_ID}${RESET}"
fi

LINE1+="${DIM} │ ${RESET}"
LINE1+="${P_ROSE}${PROJECT}${RESET}"
if [ -n "$GIT_BRANCH" ]; then
    LINE1+="${DIM} @ ${RESET}${P_MINT}${GIT_BRANCH}${RESET}"
fi

# Line 1 continued: Workers + Phase
LINE1+="${DIM} │ ${RESET}"
LINE1+="${C_B}B${W_B}${RESET} "
LINE1+="${C_C}C${W_C}${RESET} "
LINE1+="${C_D}D${W_D}${RESET}"
LINE1+="${DIM} │ ${RESET}"
LINE1+="${P_PEACH}⬡${PHASE_PROGRESS}${RESET}"

# Line 1 continued: Model + Context + Time
LINE1+="${DIM} │ ${RESET}"
LINE1+="${P_LEMON}${MODEL}${RESET}"
LINE1+="${DIM} │ ${RESET}"
LINE1+="${CONTEXT_BAR}"
LINE1+="${DIM} │ ${RESET}"
LINE1+="${P_SKY}${TIME}${RESET}"

# Output
echo -e "$LINE1"
