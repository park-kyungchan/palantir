#!/bin/bash
# ============================================================================
# /build Skill - Validation Helpers
# Version: 1.0.0
# ============================================================================
#
# Input validation utilities for Agent, Skill, and Hook builders.
# Source this file: source .claude/skills/build/helpers/validation.sh
#
# ============================================================================

# ============================================================================
# NAME VALIDATION
# ============================================================================

validate_kebab_case() {
    local name="$1"
    local component_type="${2:-component}"

    # Check format: lowercase, numbers, hyphens, no leading/trailing hyphens
    if [[ ! "$name" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ && ! "$name" =~ ^[a-z]$ ]]; then
        echo "❌ Invalid $component_type name: '$name'"
        echo "   Use kebab-case format: lowercase letters, numbers, hyphens"
        echo "   Examples: my-agent, code-review, test-runner"
        return 1
    fi

    return 0
}

validate_agent_name() {
    local name="$1"

    # Reserved names
    local reserved=("default" "system" "claude" "anthropic" "agent")
    for r in "${reserved[@]}"; do
        if [[ "$name" == "$r" ]]; then
            echo "❌ Reserved agent name: '$name'"
            return 1
        fi
    done

    validate_kebab_case "$name" "agent"
}

validate_skill_name() {
    local name="$1"

    # Reserved command names
    local reserved=("help" "clear" "compact" "memory" "config" "init" "exit")
    for r in "${reserved[@]}"; do
        if [[ "$name" == "$r" ]]; then
            echo "❌ Reserved skill name: '$name' (built-in command)"
            return 1
        fi
    done

    validate_kebab_case "$name" "skill"
}

validate_hook_name() {
    local name="$1"
    validate_kebab_case "$name" "hook"
}

# ============================================================================
# PATH VALIDATION
# ============================================================================

validate_path_exists() {
    local path="$1"
    local type="${2:-file}"

    if [[ "$type" == "file" && ! -f "$path" ]]; then
        echo "❌ File not found: $path"
        return 1
    elif [[ "$type" == "dir" && ! -d "$path" ]]; then
        echo "❌ Directory not found: $path"
        return 1
    fi

    return 0
}

validate_path_writable() {
    local path="$1"
    local parent_dir
    parent_dir=$(dirname "$path")

    if [[ ! -w "$parent_dir" ]]; then
        echo "❌ Cannot write to: $path"
        echo "   Parent directory is not writable"
        return 1
    fi

    return 0
}

check_file_exists_prompt() {
    local path="$1"
    local type="${2:-file}"

    if [[ -e "$path" ]]; then
        echo "⚠️  $type already exists: $path"
        echo "   Overwrite? (yes/no)"
        return 2  # Exists, needs confirmation
    fi

    return 0  # Does not exist, safe to create
}

# ============================================================================
# VERSION VALIDATION
# ============================================================================

validate_semver() {
    local version="$1"

    # SemVer pattern: X.Y.Z or X.Y.Z-prerelease
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
        echo "❌ Invalid version: '$version'"
        echo "   Use SemVer format: X.Y.Z (e.g., 1.0.0, 0.1.0-beta)"
        return 1
    fi

    return 0
}

# ============================================================================
# MODEL VALIDATION
# ============================================================================

validate_model() {
    local model="$1"
    local valid_models=("haiku" "sonnet" "opus" "inherit")

    for valid in "${valid_models[@]}"; do
        if [[ "$model" == "$valid" ]]; then
            return 0
        fi
    done

    echo "❌ Invalid model: '$model'"
    echo "   Valid options: ${valid_models[*]}"
    return 1
}

# ============================================================================
# PERMISSION MODE VALIDATION
# ============================================================================

validate_permission_mode() {
    local mode="$1"
    local valid_modes=("default" "acceptEdits" "dontAsk" "bypassPermissions" "plan")

    for valid in "${valid_modes[@]}"; do
        if [[ "$mode" == "$valid" ]]; then
            return 0
        fi
    done

    echo "❌ Invalid permission mode: '$mode'"
    echo "   Valid options: ${valid_modes[*]}"
    return 1
}

# ============================================================================
# CONTEXT VALIDATION
# ============================================================================

validate_context() {
    local context="$1"

    if [[ "$context" != "standard" && "$context" != "fork" ]]; then
        echo "❌ Invalid context: '$context'"
        echo "   Valid options: standard, fork"
        return 1
    fi

    return 0
}

# ============================================================================
# HOOK EVENT VALIDATION
# ============================================================================

validate_hook_event() {
    local event="$1"
    local valid_events=("PreToolUse" "PostToolUse" "Notification" "Stop" "SubagentStop")

    for valid in "${valid_events[@]}"; do
        if [[ "$event" == "$valid" ]]; then
            return 0
        fi
    done

    echo "❌ Invalid hook event: '$event'"
    echo "   Valid options: ${valid_events[*]}"
    return 1
}

validate_hook_type() {
    local type="$1"

    if [[ "$type" != "command" && "$type" != "prompt" ]]; then
        echo "❌ Invalid hook type: '$type'"
        echo "   Valid options: command, prompt"
        return 1
    fi

    return 0
}

# ============================================================================
# TOOL VALIDATION
# ============================================================================

validate_tool_name() {
    local tool="$1"
    local core_tools=("Read" "Write" "Edit" "Glob" "Grep" "Bash" "Task" "TaskCreate" "TaskUpdate" "TaskList" "TaskGet" "AskUserQuestion" "WebFetch" "WebSearch" "NotebookEdit" "Skill" "EnterPlanMode" "ExitPlanMode")

    # Check core tools
    for valid in "${core_tools[@]}"; do
        if [[ "$tool" == "$valid" ]]; then
            return 0
        fi
    done

    # Check MCP tools pattern
    if [[ "$tool" =~ ^mcp__ ]]; then
        return 0
    fi

    echo "⚠️  Unknown tool: '$tool' (may be valid if from MCP server)"
    return 0  # Allow unknown tools (MCP can add custom tools)
}

# ============================================================================
# REGEX VALIDATION
# ============================================================================

validate_regex_pattern() {
    local pattern="$1"

    # Try to compile the regex with grep
    if ! echo "" | grep -E "$pattern" >/dev/null 2>&1; then
        echo "❌ Invalid regex pattern: '$pattern'"
        return 1
    fi

    return 0
}

# ============================================================================
# COMPOSITE VALIDATION
# ============================================================================

validate_agent_config() {
    local name="$1"
    local model="$2"
    local permission_mode="$3"

    local errors=0

    validate_agent_name "$name" || ((errors++))
    validate_model "$model" || ((errors++))
    validate_permission_mode "$permission_mode" || ((errors++))

    return $errors
}

validate_skill_config() {
    local name="$1"
    local context="$2"
    local model="$3"
    local version="$4"

    local errors=0

    validate_skill_name "$name" || ((errors++))
    validate_context "$context" || ((errors++))
    validate_model "$model" || ((errors++))
    validate_semver "$version" || ((errors++))

    return $errors
}

validate_hook_config() {
    local name="$1"
    local event="$2"
    local type="$3"
    local matcher="$4"

    local errors=0

    validate_hook_name "$name" || ((errors++))
    validate_hook_event "$event" || ((errors++))
    validate_hook_type "$type" || ((errors++))
    validate_regex_pattern "$matcher" || ((errors++))

    return $errors
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_validation_summary() {
    local errors="$1"
    local component="$2"

    if [[ "$errors" -eq 0 ]]; then
        echo "✅ $component validation passed"
        return 0
    else
        echo "❌ $component validation failed with $errors error(s)"
        return 1
    fi
}
