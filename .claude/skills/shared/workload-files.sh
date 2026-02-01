#!/usr/bin/env bash
# =============================================================================
# Workload Files Module (V1.1.0)
# =============================================================================
# Purpose: Manage workload-specific _context.yaml and _progress.yaml files
# Architecture: Unified Slug Naming Convention (2026-01-25)
# Usage: source /home/palantir/.claude/skills/shared/workload-files.sh
# =============================================================================
#
# CHANGELOG (V1.1.0):
# - [WARNING-005 FIX] Added deprecation warnings for global fallback paths
# - get_workload_context_path(): warns when using global fallback
# - get_workload_progress_path(): warns when using global fallback
# - Prepares for future removal of global fallback behavior
#
# CHANGELOG (V1.0.0):
# - Workload-scoped context/progress files
# - Active workload tracking
# - Backward compatibility with global _context.yaml
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
WORKLOAD_FILES_VERSION="1.1.0"
PROMPTS_BASE_DIR=".agent/prompts"
ACTIVE_WORKLOAD_FILE="${PROMPTS_BASE_DIR}/_active_workload.yaml"

# Source dependencies
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v get_workload_prompt_dir &> /dev/null; then
    source "${SCRIPT_DIR}/workload-tracker.sh"
fi

# ============================================================================
# init_workload_directory
# Initialize workload-specific directory structure
#
# Args:
#   $1 - Workload ID
#
# Side Effects:
#   Creates:
#     - .agent/prompts/{slug}/
#     - .agent/prompts/{slug}/_context.yaml
#     - .agent/prompts/{slug}/_progress.yaml
#     - .agent/prompts/{slug}/pending/
#     - .agent/prompts/{slug}/completed/
# ============================================================================
init_workload_directory() {
    local workload_id="$1"
    local prompt_dir

    prompt_dir=$(get_workload_prompt_dir "$workload_id")

    # Create directory structure
    mkdir -p "${prompt_dir}/pending"
    mkdir -p "${prompt_dir}/completed"

    # Initialize _context.yaml if not exists
    local context_file="${prompt_dir}/_context.yaml"
    if [[ ! -f "$context_file" ]]; then
        cat > "$context_file" <<EOF
# Workload Context
# Workload ID: ${workload_id}
# Created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

workload_id: "${workload_id}"
created_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Upstream references
upstream:
  clarify_source: null
  research_source: null
  planning_source: null

# Global context that applies to all workers
global_context:
  project_root: "."
  coding_standards: null
  test_framework: null

# References to relevant files discovered during research
reference_files: []

# Shared decisions or patterns across workers
shared_decisions: []
EOF
    fi

    # Initialize _progress.yaml if not exists
    local progress_file="${prompt_dir}/_progress.yaml"
    if [[ ! -f "$progress_file" ]]; then
        cat > "$progress_file" <<EOF
# Workload Progress
# Workload ID: ${workload_id}
# Created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

workload_id: "${workload_id}"
started_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
status: "active"  # active | paused | completed | cancelled

# Worker progress tracking
workers:
  terminal-b:
    assigned_tasks: []
    current_task: null
    completed_tasks: []
    status: "idle"
    startedAt: null
    completedAt: null

  terminal-c:
    assigned_tasks: []
    current_task: null
    completed_tasks: []
    status: "idle"
    startedAt: null
    completedAt: null

  terminal-d:
    assigned_tasks: []
    current_task: null
    completed_tasks: []
    status: "idle"
    startedAt: null
    completedAt: null

# Blockers reported by workers
blockers: []

# Overall progress metrics
metrics:
  total_tasks: 0
  completed_tasks: 0
  in_progress_tasks: 0
  blocked_tasks: 0
  progress_percent: 0
EOF
    fi

    echo "✅ Workload directory initialized: ${prompt_dir}"
}

# ============================================================================
# get_workload_context_path
# Get path to workload-specific _context.yaml
#
# Args:
#   $1 - Workload ID (optional, defaults to active workload)
#
# Output:
#   Path to _context.yaml file
# ============================================================================
get_workload_context_path() {
    local identifier="${1:-}"

    if [[ -z "$identifier" ]]; then
        # Use active workload slug (not ID)
        identifier=$(get_active_workload_slug)
    fi

    if [[ -z "$identifier" ]]; then
        # DEPRECATED: Fallback to global _context.yaml
        # This behavior will be removed in future versions
        echo "⚠️  WARNING: No active workload set. Using global _context.yaml (deprecated)" >&2
        echo "   Run 'set_active_workload <workload_id>' to set context" >&2
        echo "${PROMPTS_BASE_DIR}/_context.yaml"
        return 0
    fi

    local prompt_dir
    prompt_dir=$(get_workload_prompt_dir "$identifier")
    echo "${prompt_dir}/_context.yaml"
}

# ============================================================================
# get_workload_progress_path
# Get path to workload-specific _progress.yaml
#
# Args:
#   $1 - Workload ID (optional, defaults to active workload)
#
# Output:
#   Path to _progress.yaml file
# ============================================================================
get_workload_progress_path() {
    local identifier="${1:-}"

    if [[ -z "$identifier" ]]; then
        # Use active workload slug (not ID)
        identifier=$(get_active_workload_slug)
    fi

    if [[ -z "$identifier" ]]; then
        # DEPRECATED: Fallback to global _progress.yaml
        # This behavior will be removed in future versions
        echo "⚠️  WARNING: No active workload set. Using global _progress.yaml (deprecated)" >&2
        echo "   Run 'set_active_workload <workload_id>' to set context" >&2
        echo "${PROMPTS_BASE_DIR}/_progress.yaml"
        return 0
    fi

    local prompt_dir
    prompt_dir=$(get_workload_prompt_dir "$identifier")
    echo "${prompt_dir}/_progress.yaml"
}

# ============================================================================
# set_active_workload
# Set the currently active workload
#
# Args:
#   $1 - Workload ID
#
# Side Effects:
#   Updates .agent/prompts/_active_workload.yaml
# ============================================================================
set_active_workload() {
    local workload_id="$1"
    local slug

    # Derive slug from workload ID
    if [[ "$workload_id" =~ _[0-9]{8}_ ]]; then
        # It's a full workload ID, derive slug
        slug=$(generate_slug_from_workload "$workload_id")
    else
        # It's already a slug, keep as-is
        slug="$workload_id"
        # Try to reconstruct workload ID (but this is lossy - time component missing)
        # For now, just use slug as ID
        workload_id="$slug"
    fi

    mkdir -p "$PROMPTS_BASE_DIR"

    cat > "$ACTIVE_WORKLOAD_FILE" <<EOF
# Active Workload Pointer
# Auto-generated by workload-files.sh
workload_id: "${workload_id}"
slug: "${slug}"
current_skill: "unknown"
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EOF

    echo "✅ Active workload set to: ${workload_id} (slug: ${slug})"
}

# ============================================================================
# get_active_workload
# Get the currently active workload ID
#
# Output:
#   Active workload ID, or empty string if none
# ============================================================================
get_active_workload() {
    if [[ ! -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        echo ""
        return 0
    fi

    # Extract workload ID from YAML (V7.1 format: workload_id)
    # Fallback to legacy format (active_workload_id) for backward compatibility
    local result
    result=$(grep -oP 'workload_id:\s*"\K[^"]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null || echo "")
    if [[ -z "$result" ]]; then
        result=$(grep -oP 'active_workload_id:\s*"\K[^"]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null || echo "")
    fi
    echo "$result"
}

# ============================================================================
# get_active_workload_slug
# Get the currently active workload slug (for directory names)
#
# Output:
#   Active workload slug, or empty string if none
# ============================================================================
get_active_workload_slug() {
    if [[ ! -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        echo ""
        return 0
    fi

    # Extract slug from YAML (V7.1 format: slug)
    # Fallback to legacy format (active_workload_slug) for backward compatibility
    local slug
    slug=$(grep -oP '^slug:\s*"\K[^"]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null || echo "")
    if [[ -z "$slug" ]]; then
        slug=$(grep -oP 'active_workload_slug:\s*"\K[^"]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null || echo "")
    fi

    if [[ -z "$slug" ]]; then
        # Fallback: derive from workload ID
        local workload_id
        workload_id=$(get_active_workload)
        if [[ -n "$workload_id" ]]; then
            slug=$(generate_slug_from_workload "$workload_id")
        fi
    fi

    echo "$slug"
}

# ============================================================================
# list_workloads
# List all workload directories
#
# Output:
#   List of workload slugs (directory names)
# ============================================================================
list_workloads() {
    if [[ ! -d "$PROMPTS_BASE_DIR" ]]; then
        return 0
    fi

    find "$PROMPTS_BASE_DIR" -mindepth 1 -maxdepth 1 -type d ! -name "_*" -exec basename {} \; 2>/dev/null || true
}

# ============================================================================
# switch_workload
# Switch to a different workload (with validation)
#
# Args:
#   $1 - Workload ID or slug
#
# Side Effects:
#   Updates active workload if target exists
# ============================================================================
switch_workload() {
    local identifier="$1"
    local prompt_dir

    prompt_dir=$(get_workload_prompt_dir "$identifier")

    if [[ ! -d "$prompt_dir" ]]; then
        echo "ERROR: Workload directory not found: $prompt_dir" >&2
        return 1
    fi

    # Extract workload ID from directory (could be slug)
    local workload_id
    if [[ "$identifier" =~ _[0-9]{8}_ ]]; then
        workload_id="$identifier"
    else
        # Try to read from _context.yaml
        local context_file="${prompt_dir}/_context.yaml"
        if [[ -f "$context_file" ]]; then
            workload_id=$(grep -oP 'workload_id:\s*"\K[^"]+' "$context_file" || echo "$identifier")
        else
            workload_id="$identifier"
        fi
    fi

    set_active_workload "$workload_id"
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f init_workload_directory
export -f get_workload_context_path
export -f get_workload_progress_path
export -f set_active_workload
export -f get_active_workload
export -f get_active_workload_slug
export -f list_workloads
export -f switch_workload

# ============================================================================
# SELF-TEST (Optional - for development)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Workload Files Self-Test ==="

    # Test 1: Initialize workload directory
    echo "Test 1: init_workload_directory"
    test_workload_id="test-workload_20260125_173800"
    init_workload_directory "$test_workload_id"

    # Test 2: Set active workload
    echo "Test 2: set_active_workload"
    set_active_workload "$test_workload_id"

    # Test 3: Get active workload
    echo "Test 3: get_active_workload"
    active=$(get_active_workload)
    echo "  Result: $active"

    # Test 4: Get context path
    echo "Test 4: get_workload_context_path"
    context_path=$(get_workload_context_path)
    echo "  Result: $context_path"

    # Test 5: Get progress path
    echo "Test 5: get_workload_progress_path"
    progress_path=$(get_workload_progress_path)
    echo "  Result: $progress_path"

    # Test 6: List workloads
    echo "Test 6: list_workloads"
    list_workloads

    echo "=== All tests completed ==="
fi
