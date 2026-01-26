#!/bin/bash
# Claude Code StatusLine - Cotton Candy Theme
# Sections: CWD | Git | Model | Context | Task ID
# Created: 2026-01-26

# Read JSON input from Claude Code (stdin)
INPUT=$(cat)

# ═══════════════════════════════════════════════════════════════
# Color Definitions (Truecolor ANSI - Cotton Candy Palette)
# ═══════════════════════════════════════════════════════════════
BG_CWD="\033[48;2;180;120;230m"         # Vivid Purple +40% saturation (디렉토리)
BG_GIT="\033[48;2;100;220;140m"         # Vivid Green +40% saturation (Git)
BG_MODEL="\033[48;2;240;160;120m"       # Vivid Peach +40% saturation (모델)
BG_TASK="\033[48;2;100;160;230m"        # Vivid Blue +40% saturation (Task ID)
FG_DARK="\033[38;2;255;255;255m"        # White (high contrast)
RESET="\033[0m"

# ═══════════════════════════════════════════════════════════════
# Data Extraction Functions
# ═══════════════════════════════════════════════════════════════

get_cwd() {
    local cwd=""
    if command -v jq &>/dev/null && [ -n "$INPUT" ]; then
        cwd=$(echo "$INPUT" | jq -r '.workspace.current_dir // empty' 2>/dev/null)
    fi
    [ -z "$cwd" ] && cwd=$(pwd)
    # Shorten home directory to ~
    echo "${cwd/#$HOME/~}"
}

get_git_branch() {
    local branch=""
    branch=$(git branch --show-current 2>/dev/null)
    if [ -n "$branch" ]; then
        # Check for uncommitted changes
        local dirty=""
        git diff --quiet 2>/dev/null || dirty="*"
        git diff --cached --quiet 2>/dev/null || dirty="*"
        echo "${branch}${dirty}"
    fi
}

get_model() {
    if command -v jq &>/dev/null && [ -n "$INPUT" ]; then
        local model=$(echo "$INPUT" | jq -r '.model.display_name // empty' 2>/dev/null)
        [ -n "$model" ] && echo "$model"
    fi
}

get_task_id() {
    local task_id="${CLAUDE_CODE_TASK_LIST_ID:-}"
    [ -n "$task_id" ] && echo "$task_id"
}

# ═══════════════════════════════════════════════════════════════
# Gather Data
# ═══════════════════════════════════════════════════════════════
CWD=$(get_cwd)
GIT_BRANCH=$(get_git_branch)
MODEL=$(get_model)
TASK_ID=$(get_task_id)

# ═══════════════════════════════════════════════════════════════
# Render (각 섹션별 다른 파스텔 배경)
# ═══════════════════════════════════════════════════════════════
OUTPUT=""

# 1. 디렉토리 (항상 표시) - 💜 Purple 배경 → 🗂️ 흰색 폴더
OUTPUT="${BG_CWD}${FG_DARK} 🗂️ ${CWD} ${RESET}"

# 2. Git 브랜치 (있을 때만) - 💚 Green 배경 → 🔀 파란색 merge
if [ -n "$GIT_BRANCH" ]; then
    OUTPUT="${OUTPUT}${BG_GIT}${FG_DARK} 🔀 ${GIT_BRANCH} ${RESET}"
fi

# 3. 모델명 (있을 때만) - 🧡 Peach 배경 → 🤖 회색 로봇
if [ -n "$MODEL" ]; then
    OUTPUT="${OUTPUT}${BG_MODEL}${FG_DARK} 🤖 ${MODEL} ${RESET}"
fi

# 4. Task ID (있을 때만) - 💙 Blue 배경 → 📝 노란색 메모
if [ -n "$TASK_ID" ]; then
    OUTPUT="${OUTPUT}${BG_TASK}${FG_DARK} 📝 ${TASK_ID} ${RESET}"
fi

echo -e "${OUTPUT}"
