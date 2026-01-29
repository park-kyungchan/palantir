#!/usr/bin/env bash
# =============================================================================
# Skill Standalone Module (V1.0.0)
# =============================================================================
# Purpose: Enable standalone skill execution with automatic workload management
#          and standardized handoff to downstream skills
# Architecture: Unified Slug Naming Convention (2026-01-25)
# Usage: source /home/palantir/.claude/skills/shared/skill-standalone.sh
# =============================================================================
#
# CHANGELOG (V1.0.0):
# - Initial implementation for skill independence
# - init_skill_context(): Auto-detect workload (upstream → active → new)
# - generate_handoff_yaml(): Standard handoff metadata generation
# - get_upstream_workload(): Extract workload from upstream skill arguments
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
STANDALONE_VERSION="1.0.0"
ACTIVE_WORKLOAD_FILE=".agent/prompts/_active_workload.yaml"

# Source dependencies if not already loaded
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v generate_workload_id &> /dev/null; then
    source "${SCRIPT_DIR}/slug-generator.sh"
fi
if ! command -v get_workload_prompt_dir &> /dev/null; then
    source "${SCRIPT_DIR}/workload-tracker.sh"
fi

# ============================================================================
# init_skill_context
# Initialize skill execution context with automatic workload detection
#
# Args:
#   $1 - Skill name (clarify, research, planning, etc.)
#   $2 - Arguments string (may contain --*-slug flags)
#   $3 - Query/topic (optional, for new workload generation)
#
# Output:
#   JSON object: {
#     workload_id: string,
#     slug: string,
#     workload_dir: string,
#     is_standalone: boolean,
#     upstream_skill: string|null,
#     upstream_slug: string|null
#   }
#
# Strategy:
#   1. Check for upstream slug argument (--clarify-slug, --research-slug, etc.)
#   2. Check for active workload
#   3. Generate new workload (standalone mode)
# ============================================================================
init_skill_context() {
    local skill_name="$1"
    local args="${2:-}"
    local query="${3:-}"

    local workload_id=""
    local slug=""
    local is_standalone="true"
    local upstream_skill="null"
    local upstream_slug="null"

    # Strategy 1: Check for upstream slug arguments
    local upstream_result
    upstream_result=$(get_upstream_workload "$args")

    if [[ -n "$upstream_result" && "$upstream_result" != "null" ]]; then
        upstream_skill=$(echo "$upstream_result" | jq -r '.skill // "null"')
        upstream_slug=$(echo "$upstream_result" | jq -r '.slug // "null"')

        if [[ "$upstream_slug" != "null" && -n "$upstream_slug" ]]; then
            # Reuse upstream workload
            slug="$upstream_slug"

            # Try to reconstruct workload_id from slug
            local workload_info
            workload_info=$(extract_workload_from_slug "$slug" 2>/dev/null || echo "{}")
            workload_id=$(echo "$workload_info" | jq -r '.workload_id // ""')

            if [[ -z "$workload_id" ]]; then
                workload_id="$slug"
            fi

            is_standalone="false"
            echo "📋 Using upstream ${upstream_skill} slug: $slug" >&2
        fi
    fi

    # Strategy 2: Check for active workload
    if [[ -z "$workload_id" ]] && [[ -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        local active_workload
        active_workload=$(yq -r '.workload_id // ""' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null || echo "")

        if [[ -n "$active_workload" ]]; then
            workload_id="$active_workload"
            slug=$(generate_slug_from_workload "$workload_id")
            is_standalone="false"
            echo "📋 Using active workload: $slug" >&2
        fi
    fi

    # Strategy 3: Generate new workload (standalone mode)
    if [[ -z "$workload_id" ]]; then
        local topic="${query:-${skill_name}-$(date +%H%M%S)}"
        workload_id=$(generate_workload_id "$topic")
        slug=$(generate_slug_from_workload "$workload_id")
        is_standalone="true"
        echo "📋 Created standalone workload: $slug" >&2

        # Initialize workload
        init_workload "$workload_id" "$skill_name" "$topic"
    fi

    # Ensure workload directory exists
    local workload_dir
    workload_dir=$(get_workload_prompt_dir "$workload_id")
    mkdir -p "$workload_dir"

    # Set as active workload
    set_active_workload "$workload_id" "$skill_name"

    # Return JSON
    jq -n \
        --arg workload_id "$workload_id" \
        --arg slug "$slug" \
        --arg workload_dir "$workload_dir" \
        --argjson is_standalone "$is_standalone" \
        --arg upstream_skill "$upstream_skill" \
        --arg upstream_slug "$upstream_slug" \
        '{
            workload_id: $workload_id,
            slug: $slug,
            workload_dir: $workload_dir,
            is_standalone: $is_standalone,
            upstream_skill: (if $upstream_skill == "null" then null else $upstream_skill end),
            upstream_slug: (if $upstream_slug == "null" then null else $upstream_slug end)
        }'
}

# ============================================================================
# get_upstream_workload
# Extract upstream workload information from arguments
#
# Args:
#   $1 - Arguments string
#
# Output:
#   JSON object: { skill: string, slug: string } or "null"
#
# Supported flags:
#   --clarify-slug, --research-slug, --planning-slug, --plan-slug
#   --collect-slug, --synthesis-slug, --workload
# ============================================================================
get_upstream_workload() {
    local args="$1"

    # Map of flag patterns to upstream skill names
    local patterns=(
        "--clarify-slug:clarify"
        "--re-architecture-slug:re-architecture"
        "--research-slug:research"
        "--planning-slug:planning"
        "--plan-slug:planning"
        "--collect-slug:collect"
        "--synthesis-slug:synthesis"
        "--workload:orchestrate"
    )

    for pattern in "${patterns[@]}"; do
        local flag="${pattern%%:*}"
        local skill="${pattern##*:}"

        # Check if flag exists in args
        if [[ "$args" =~ $flag[[:space:]]+([^[:space:]]+) ]]; then
            local slug="${BASH_REMATCH[1]}"
            jq -n \
                --arg skill "$skill" \
                --arg slug "$slug" \
                '{ skill: $skill, slug: $slug }'
            return 0
        fi
    done

    echo "null"
}

# ============================================================================
# set_active_workload
# Set current workload as active
#
# Args:
#   $1 - Workload ID
#   $2 - Current skill name
#
# Side Effects:
#   Creates/updates .agent/prompts/_active_workload.yaml
# ============================================================================
set_active_workload() {
    local workload_id="$1"
    local skill_name="$2"
    local slug
    local timestamp

    slug=$(generate_slug_from_workload "$workload_id")
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    mkdir -p "$(dirname "$ACTIVE_WORKLOAD_FILE")"

    cat > "$ACTIVE_WORKLOAD_FILE" <<EOF
# Active Workload Pointer
# Auto-generated by skill-standalone.sh
workload_id: "$workload_id"
slug: "$slug"
current_skill: "$skill_name"
updated_at: "$timestamp"
EOF
}

# ============================================================================
# generate_handoff_yaml
# Generate standardized handoff metadata for skill output
#
# Args:
#   $1 - Current skill name
#   $2 - Workload slug
#   $3 - Next skill name
#   $4 - Next skill arguments (e.g., "--research-slug {slug}")
#   $5 - Status (completed, partial, error)
#   $6 - Reason/description
#
# Output:
#   YAML string for inclusion in skill output
# ============================================================================
generate_handoff_yaml() {
    local current_skill="$1"
    local slug="$2"
    local next_skill="$3"
    local next_args="$4"
    local status="$5"
    local reason="$6"
    local timestamp

    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Replace {slug} placeholder in next_args
    next_args="${next_args//\{slug\}/$slug}"

    cat <<EOF
handoff:
  skill: "$current_skill"
  workload_slug: "$slug"
  status: "$status"
  timestamp: "$timestamp"
  next_action:
    skill: "/$next_skill"
    arguments: "$next_args"
    required: true
    reason: "$reason"
EOF
}

# ============================================================================
# get_handoff_mapping
# Get the standard handoff mapping for a skill
#
# Args:
#   $1 - Current skill name
#   $2 - Status (completed, iterate, error)
#
# Output:
#   JSON object: { next_skill: string, arguments: string }
# ============================================================================
get_handoff_mapping() {
    local skill="$1"
    local status="${2:-completed}"

    # Standard handoff mapping
    case "$skill:$status" in
        "clarify:completed")
            echo '{"next_skill":"research","arguments":"--clarify-slug {slug}"}'
            ;;
        "re-architecture:completed")
            echo '{"next_skill":"research","arguments":"--re-architecture-slug {slug}"}'
            ;;
        "research:completed")
            echo '{"next_skill":"planning","arguments":"--research-slug {slug}"}'
            ;;
        "planning:completed")
            echo '{"next_skill":"orchestrate","arguments":"--plan-slug {slug}"}'
            ;;
        "orchestrate:completed")
            echo '{"next_skill":"assign","arguments":"--workload {slug}"}'
            ;;
        "assign:completed")
            echo '{"next_skill":"worker","arguments":"--workload {slug}"}'
            ;;
        "collect:completed")
            echo '{"next_skill":"synthesis","arguments":"--workload {slug}"}'
            ;;
        "synthesis:completed")
            echo '{"next_skill":"commit-push-pr","arguments":"--workload {slug}"}'
            ;;
        "synthesis:complete_with_warnings")
            echo '{"next_skill":"commit-push-pr","arguments":"--workload {slug} --with-warnings"}'
            ;;
        "synthesis:iterate")
            echo '{"next_skill":"rsil-plan","arguments":"--workload {slug} --iteration {iteration}"}'
            ;;
        "rsil-plan:completed"|"rsil-plan:auto_remediate")
            echo '{"next_skill":"orchestrate","arguments":"--workload {slug}"}'
            ;;
        "rsil-plan:escalate")
            echo '{"next_skill":"clarify","arguments":"--gap-description {gap}"}'
            ;;
        *)
            echo '{"next_skill":null,"arguments":null}'
            ;;
    esac
}

# ============================================================================
# append_handoff_to_output
# Append handoff section to skill output file
#
# Args:
#   $1 - Output file path
#   $2 - Current skill name
#   $3 - Workload slug
#   $4 - Status (completed, partial, error)
#   $5 - Reason
#
# Side Effects:
#   Appends handoff YAML to the output file
# ============================================================================
append_handoff_to_output() {
    local output_file="$1"
    local skill="$2"
    local slug="$3"
    local status="$4"
    local reason="$5"

    # Get mapping
    local mapping
    mapping=$(get_handoff_mapping "$skill" "$status")

    local next_skill
    local next_args
    next_skill=$(echo "$mapping" | jq -r '.next_skill // ""')
    next_args=$(echo "$mapping" | jq -r '.arguments // ""')

    if [[ -n "$next_skill" && "$next_skill" != "null" ]]; then
        # Generate handoff YAML
        local handoff_yaml
        handoff_yaml=$(generate_handoff_yaml "$skill" "$slug" "$next_skill" "$next_args" "$status" "$reason")

        # Append to file
        echo "" >> "$output_file"
        echo "---" >> "$output_file"
        echo "# Handoff Metadata (auto-generated)" >> "$output_file"
        echo "$handoff_yaml" >> "$output_file"
    fi
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f init_skill_context
export -f get_upstream_workload
export -f set_active_workload
export -f generate_handoff_yaml
export -f get_handoff_mapping
export -f append_handoff_to_output

# ============================================================================
# SELF-TEST
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Skill Standalone Self-Test ==="

    # Test 1: Init context (standalone)
    echo "Test 1: init_skill_context (standalone)"
    context=$(init_skill_context "research" "" "test query")
    echo "  Result: $context"

    # Test 2: Get upstream workload
    echo "Test 2: get_upstream_workload"
    upstream=$(get_upstream_workload "--clarify-slug my-feature-20260128-120000")
    echo "  Result: $upstream"

    # Test 3: Generate handoff YAML
    echo "Test 3: generate_handoff_yaml"
    handoff=$(generate_handoff_yaml "research" "my-feature-20260128-120000" "planning" "--research-slug {slug}" "completed" "Research complete")
    echo "  Result:"
    echo "$handoff"

    # Test 4: Get handoff mapping
    echo "Test 4: get_handoff_mapping"
    mapping=$(get_handoff_mapping "clarify" "completed")
    echo "  Result: $mapping"

    echo "=== All tests completed ==="
fi
