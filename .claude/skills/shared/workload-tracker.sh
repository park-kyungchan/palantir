#!/usr/bin/env bash
# =============================================================================
# Workload Tracker Module (V1.0.0)
# =============================================================================
# Purpose: Track and manage workload-scoped file paths
# Architecture: Unified Slug Naming Convention (2026-01-25)
# Usage: source /home/palantir/.claude/skills/shared/workload-tracker.sh
# =============================================================================
#
# CHANGELOG (V1.0.0):
# - Initial implementation for workload-based file organization
# - File path resolution: .agent/prompts/{slug}/*
# - Progress/Context file management per workload
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
TRACKER_VERSION="1.0.0"
PROMPTS_BASE_DIR=".agent/prompts"

# Source slug generator if not already loaded
if ! command -v generate_workload_id &> /dev/null; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "${SCRIPT_DIR}/slug-generator.sh"
fi

# ============================================================================
# get_workload_prompt_dir
# Get workload-specific prompt directory
#
# Args:
#   $1 - Workload ID or slug
#
# Output:
#   Directory path: .agent/prompts/{slug}
# ============================================================================
get_workload_prompt_dir() {
    local identifier="$1"
    local slug

    # Check if input is workload ID (contains underscores) or slug (contains hyphens)
    if [[ "$identifier" =~ _[0-9]{8}_ ]]; then
        # It's a workload ID, derive slug
        slug=$(generate_slug_from_workload "$identifier")
    else
        # Assume it's already a slug
        slug="$identifier"
    fi

    echo "${PROMPTS_BASE_DIR}/${slug}"
}

# ============================================================================
# get_workload_context_file
# Get workload-specific context file path
#
# Args:
#   $1 - Workload ID or slug
#
# Output:
#   File path: .agent/prompts/{slug}/_context.yaml
# ============================================================================
get_workload_context_file() {
    local identifier="$1"
    local prompt_dir

    prompt_dir=$(get_workload_prompt_dir "$identifier")
    echo "${prompt_dir}/_context.yaml"
}

# ============================================================================
# get_workload_progress_file
# Get workload-specific progress file path
#
# Args:
#   $1 - Workload ID or slug
#
# Output:
#   File path: .agent/prompts/{slug}/_progress.yaml
# ============================================================================
get_workload_progress_file() {
    local identifier="$1"
    local prompt_dir

    prompt_dir=$(get_workload_prompt_dir "$identifier")
    echo "${prompt_dir}/_progress.yaml"
}

# ============================================================================
# init_workload_directories
# Initialize directory structure for a workload
#
# Args:
#   $1 - Workload ID or slug
#
# Side Effects:
#   Creates:
#     - .agent/prompts/{slug}/
#     - .agent/prompts/{slug}/pending/
#     - .agent/prompts/{slug}/completed/
# ============================================================================
init_workload_directories() {
    local identifier="$1"
    local prompt_dir

    prompt_dir=$(get_workload_prompt_dir "$identifier")

    mkdir -p "${prompt_dir}/pending"
    mkdir -p "${prompt_dir}/completed"

    echo "✅ Workload directories initialized: ${prompt_dir}"
}

# ============================================================================
# get_worker_prompt_file
# Generate worker-specific prompt file path
#
# Args:
#   $1 - Workload ID or slug
#   $2 - Worker ID (terminal-b, terminal-c, etc.)
#   $3 - Task description (for filename)
#   $4 - Status (pending/completed, default: pending)
#
# Output:
#   File path: .agent/prompts/{slug}/{status}/worker-{worker_id}-{task_slug}.yaml
# ============================================================================
get_worker_prompt_file() {
    local identifier="$1"
    local worker_id="$2"
    local task_desc="$3"
    local status="${4:-pending}"
    local prompt_dir

    prompt_dir=$(get_workload_prompt_dir "$identifier")

    # Generate task slug (normalize task description)
    # Use [:alnum:] for portability
    local task_slug
    task_slug=$(echo "$task_desc" | \
        tr '[:upper:]' '[:lower:]' | \
        tr -cs '[:alnum:]' '-' | \
        sed 's/^-//' | \
        sed 's/-$//' | \
        cut -c1-40)

    echo "${prompt_dir}/${status}/worker-${worker_id}-${task_slug}.yaml"
}

# ============================================================================
# list_workload_prompts
# List all prompt files for a workload
#
# Args:
#   $1 - Workload ID or slug
#   $2 - Status filter (pending/completed/all, default: all)
#
# Output:
#   List of prompt file paths
# ============================================================================
list_workload_prompts() {
    local identifier="$1"
    local status_filter="${2:-all}"
    local prompt_dir

    prompt_dir=$(get_workload_prompt_dir "$identifier")

    case "$status_filter" in
        pending)
            find "${prompt_dir}/pending" -name "*.yaml" 2>/dev/null || true
            ;;
        completed)
            find "${prompt_dir}/completed" -name "*.yaml" 2>/dev/null || true
            ;;
        all)
            find "${prompt_dir}" -name "*.yaml" ! -name "_*" 2>/dev/null || true
            ;;
        *)
            echo "ERROR: Invalid status filter: $status_filter" >&2
            return 1
            ;;
    esac
}

# ============================================================================
# move_prompt_to_completed
# Move worker prompt from pending to completed
#
# Args:
#   $1 - Prompt file path
#
# Side Effects:
#   Moves file from {slug}/pending/ to {slug}/completed/
# ============================================================================
move_prompt_to_completed() {
    local prompt_file="$1"

    if [[ ! -f "$prompt_file" ]]; then
        echo "ERROR: Prompt file not found: $prompt_file" >&2
        return 1
    fi

    # Extract directory and filename
    local dir_path
    local filename

    dir_path=$(dirname "$prompt_file")
    filename=$(basename "$prompt_file")

    # Replace /pending/ with /completed/
    local dest_dir
    dest_dir=$(echo "$dir_path" | sed 's/\/pending$/\/completed/')

    if [[ "$dest_dir" == "$dir_path" ]]; then
        echo "ERROR: File is not in pending directory: $prompt_file" >&2
        return 1
    fi

    mkdir -p "$dest_dir"
    mv "$prompt_file" "${dest_dir}/${filename}"

    echo "✅ Moved to completed: ${dest_dir}/${filename}"
}

# ============================================================================
# get_workload_from_prompt_path
# Extract workload slug from prompt file path
#
# Args:
#   $1 - Prompt file path
#
# Output:
#   Workload slug
#
# Example:
#   get_workload_from_prompt_path ".agent/prompts/user-auth-20260125/pending/worker-b-task1.yaml"
#   → user-auth-20260125
# ============================================================================
get_workload_from_prompt_path() {
    local prompt_path="$1"

    # Extract slug from path: .agent/prompts/{slug}/...
    echo "$prompt_path" | sed -n 's|^.agent/prompts/\([^/]*\)/.*|\1|p'
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f get_workload_prompt_dir
export -f get_workload_context_file
export -f get_workload_progress_file
export -f init_workload_directories
export -f get_worker_prompt_file
export -f list_workload_prompts
export -f move_prompt_to_completed
export -f get_workload_from_prompt_path

# ============================================================================
# SELF-TEST (Optional - for development)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Workload Tracker Self-Test ==="

    # Test 1: Get prompt directory
    echo "Test 1: get_workload_prompt_dir"
    workload_id="user-auth_20260125_143022"
    prompt_dir=$(get_workload_prompt_dir "$workload_id")
    echo "  Result: $prompt_dir"

    # Test 2: Get context file
    echo "Test 2: get_workload_context_file"
    context_file=$(get_workload_context_file "$workload_id")
    echo "  Result: $context_file"

    # Test 3: Get progress file
    echo "Test 3: get_workload_progress_file"
    progress_file=$(get_workload_progress_file "$workload_id")
    echo "  Result: $progress_file"

    # Test 4: Initialize directories
    echo "Test 4: init_workload_directories"
    init_workload_directories "$workload_id"

    # Test 5: Get worker prompt file
    echo "Test 5: get_worker_prompt_file"
    worker_file=$(get_worker_prompt_file "$workload_id" "terminal-b" "implement auth" "pending")
    echo "  Result: $worker_file"

    # Test 6: Extract workload from path
    echo "Test 6: get_workload_from_prompt_path"
    extracted_slug=$(get_workload_from_prompt_path "$worker_file")
    echo "  Result: $extracted_slug"

    echo "=== All tests completed ==="
fi
