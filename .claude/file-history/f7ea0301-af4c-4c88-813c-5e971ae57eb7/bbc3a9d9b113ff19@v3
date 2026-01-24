#!/usr/bin/env bash
# =============================================================================
# /clarify Skill Helper Functions (V2.1.0 - YAML Compatible)
# =============================================================================
# Purpose: Provide YAML logging utilities for clarify skill
# Requires: yq (https://github.com/mikefarah/yq)
# Usage: source /home/palantir/.claude/skills/clarify/helpers.sh
# =============================================================================
#
# CHANGELOG (V2.1.0):
# - Aligned with /build parameter modules (V2.1.19 spec)
# - Removed TodoWrite dependency (deprecated → Task API)
# - Updated CLARIFY_VERSION constant
#
# CHANGELOG (V2.0.0):
# - Migrated from Markdown to YAML format
# - Added yq-based YAML manipulation
# - Added pipeline integration fields (downstream_skills, task_references)
# - Added context_hash for integrity verification
# - Maintained backward compatibility function names with yaml_ prefix
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
CLARIFY_VERSION="2.1.0"
CLARIFY_LOG_DIR=".agent/clarify"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Check if yq is available
_check_yq() {
    if ! command -v yq &> /dev/null; then
        echo "ERROR: yq not found. Install with: brew install yq" >&2
        return 1
    fi
}

# Get ISO8601 timestamp
_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# ============================================================================
# yaml_generate_slug
# Generate URL-safe slug from input text
#
# Args:
#   $1 - Input text
#
# Output:
#   Slug string (lowercase, hyphens, max 64 chars + timestamp)
# ============================================================================
yaml_generate_slug() {
    local input="$1"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)

    # Normalize: lowercase, replace spaces/special chars with hyphens
    local slug
    slug=$(echo "$input" | \
        tr '[:upper:]' '[:lower:]' | \
        sed 's/[^a-z0-9가-힣]/-/g' | \
        sed 's/--*/-/g' | \
        sed 's/^-//' | \
        sed 's/-$//' | \
        cut -c1-40)

    echo "${slug}_${timestamp}"
}

# Backward compatibility alias
generate_slug() {
    yaml_generate_slug "$@"
}

# ============================================================================
# yaml_init_log
# Initialize new YAML log file with schema
#
# Args:
#   $1 - Log file path
#   $2 - Original user request
# ============================================================================
yaml_init_log() {
    local log_path="$1"
    local original_request="$2"
    local slug
    slug=$(basename "$log_path" .yaml)

    _check_yq || return 1

    # Ensure directory exists
    mkdir -p "$(dirname "$log_path")"

    # Create initial YAML structure
    cat > "$log_path" << EOF
# /clarify Session Log
# Generated: $(_timestamp)
# Schema Version: ${CLARIFY_VERSION}

metadata:
  id: "${slug}"
  version: "${CLARIFY_VERSION}"
  created_at: "$(_timestamp)"
  updated_at: "$(_timestamp)"
  status: "in_progress"
  rounds: 0
  final_approved: false

original_request: |
$(echo "$original_request" | sed 's/^/  /')

rounds: []

final_output:
  approved_prompt: null
  pe_techniques_applied: []

pipeline:
  downstream_skills: []
  task_references: []
  context_hash: null
  decision_trace: []
EOF

    echo "✅ Log initialized: $log_path"
}

# Backward compatibility alias
write_log_header() {
    local log_path="$1"
    local original_input="$2"
    # Convert .md path to .yaml path
    local yaml_path="${log_path%.md}.yaml"
    yaml_init_log "$yaml_path" "$original_input"
}

# ============================================================================
# yaml_append_round
# Append new round entry to YAML log
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Input text
#   $4 - PE technique name
#   $5 - PE technique reason
#   $6 - Improved prompt
#   $7 - User response (pending, 승인, 수정요청, 기법변경)
# ============================================================================
yaml_append_round() {
    local log_path="$1"
    local round_num="$2"
    local input="$3"
    local technique_name="$4"
    local technique_reason="$5"
    local improved="$6"
    local response="${7:-pending}"

    _check_yq || return 1

    # Escape quotes in strings for YAML
    input="${input//\"/\\\"}"
    improved="${improved//\"/\\\"}"

    # Create temporary round file
    local temp_round
    temp_round=$(mktemp)

    cat > "$temp_round" << EOF
round: ${round_num}
timestamp: "$(_timestamp)"
input: "${input}"
pe_technique:
  name: "${technique_name}"
  reason: "${technique_reason}"
improved_prompt: "${improved}"
user_response: "${response}"
user_feedback: null
EOF

    # Append to rounds array using yq
    yq -i ".rounds += [$(cat "$temp_round" | yq -o=json)]" "$log_path"

    # Cleanup temp file
    rm -f "$temp_round"

    # Update metadata
    yq -i ".metadata.rounds = ${round_num}" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    # Add to decision trace
    yq -i ".pipeline.decision_trace += [{\"round\": ${round_num}, \"decision\": \"${technique_name} 적용\", \"reason\": \"${technique_reason}\"}]" "$log_path"

    echo "✅ Round ${round_num} appended"
}

# Backward compatibility alias
append_round_log() {
    local log_path="$1"
    local round_num="$2"
    local input="$3"
    local pe_technique="$4"
    local pe_reason="$5"
    local improved_prompt="$6"
    local user_response="$7"
    local feedback="${8:-N/A}"

    local yaml_path="${log_path%.md}.yaml"
    yaml_append_round "$yaml_path" "$round_num" "$input" "$pe_technique" "$pe_reason" "$improved_prompt" "$user_response"

    if [[ "$feedback" != "N/A" ]]; then
        yaml_update_round "$yaml_path" "$round_num" "user_feedback" "$feedback"
    fi
}

# ============================================================================
# yaml_update_round
# Update specific field in a round entry
#
# Args:
#   $1 - Log file path
#   $2 - Round number
#   $3 - Field name (user_response, user_feedback, etc.)
#   $4 - New value
# ============================================================================
yaml_update_round() {
    local log_path="$1"
    local round_num="$2"
    local field="$3"
    local value="$4"

    _check_yq || return 1

    # Find round index (0-based)
    local idx=$((round_num - 1))

    # Update field
    yq -i ".rounds[${idx}].${field} = \"${value}\"" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# yaml_finalize
# Mark log as completed with final prompt
#
# Args:
#   $1 - Log file path
#   $2 - Final approved prompt
# ============================================================================
yaml_finalize() {
    local log_path="$1"
    local final_prompt="$2"

    _check_yq || return 1

    # Escape quotes for YAML
    final_prompt="${final_prompt//\"/\\\"}"

    # Update status
    yq -i '.metadata.status = "completed"' "$log_path"
    yq -i '.metadata.final_approved = true' "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    # Set final output
    yq -i ".final_output.approved_prompt = \"${final_prompt}\"" "$log_path"

    # Collect all applied PE techniques (unique)
    yq -i '.final_output.pe_techniques_applied = [.rounds[].pe_technique.name] | unique' "$log_path"

    # Compute context hash
    local hash
    hash=$(yaml_compute_hash "$log_path")
    yq -i ".pipeline.context_hash = \"${hash}\"" "$log_path"

    echo "✅ Log finalized: $log_path"
}

# Backward compatibility alias
finalize_log() {
    local log_path="$1"
    local final_prompt="$2"
    local yaml_path="${log_path%.md}.yaml"
    yaml_finalize "$yaml_path" "$final_prompt"
}

# ============================================================================
# yaml_cancel
# Mark log as cancelled with reason
#
# Args:
#   $1 - Log file path
#   $2 - Cancellation reason
# ============================================================================
yaml_cancel() {
    local log_path="$1"
    local reason="$2"

    _check_yq || return 1

    yq -i '.metadata.status = "cancelled"' "$log_path"
    yq -i ".metadata.cancel_reason = \"${reason}\"" "$log_path"
    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"

    echo "⚠️  Log cancelled: $reason"
}

# Backward compatibility alias
cancel_log() {
    local log_path="$1"
    local reason="$2"
    local yaml_path="${log_path%.md}.yaml"
    yaml_cancel "$yaml_path" "$reason"
}

# ============================================================================
# yaml_get_field
# Read specific field from YAML log
#
# Args:
#   $1 - Log file path
#   $2 - Field path (e.g., ".metadata.rounds", ".rounds[-1].improved_prompt")
#
# Output:
#   Field value
# ============================================================================
yaml_get_field() {
    local log_path="$1"
    local field_path="$2"

    _check_yq || return 1

    yq "${field_path}" "$log_path"
}

# ============================================================================
# yaml_compute_hash
# Compute SHA256 hash of log content (for integrity verification)
#
# Args:
#   $1 - Log file path
#
# Output:
#   SHA256 hash string
# ============================================================================
yaml_compute_hash() {
    local log_path="$1"

    # Hash the original_request + all rounds (excluding pipeline metadata)
    yq '.original_request, .rounds' "$log_path" | sha256sum | cut -d' ' -f1
}

# ============================================================================
# yaml_add_downstream_skill
# Record downstream skill invocation for pipeline tracking
#
# Args:
#   $1 - Log file path
#   $2 - Skill name
#   $3 - Task ID (optional)
# ============================================================================
yaml_add_downstream_skill() {
    local log_path="$1"
    local skill_name="$2"
    local task_id="${3:-}"

    _check_yq || return 1

    yq -i ".pipeline.downstream_skills += [\"${skill_name}\"]" "$log_path"

    if [[ -n "$task_id" ]]; then
        yq -i ".pipeline.task_references += [\"${task_id}\"]" "$log_path"
    fi

    yq -i ".metadata.updated_at = \"$(_timestamp)\"" "$log_path"
}

# ============================================================================
# update_round_summary (Backward Compatibility - No-op for YAML)
# In YAML format, summary is computed dynamically from rounds array
# ============================================================================
update_round_summary() {
    # No-op for YAML format
    # Summary can be computed: yq '.rounds[] | [.round, .input[0:30], .pe_technique.name, .user_response]'
    :
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f yaml_generate_slug
export -f yaml_init_log
export -f yaml_append_round
export -f yaml_update_round
export -f yaml_finalize
export -f yaml_cancel
export -f yaml_get_field
export -f yaml_compute_hash
export -f yaml_add_downstream_skill

# Backward compatibility exports
export -f generate_slug
export -f write_log_header
export -f append_round_log
export -f finalize_log
export -f cancel_log
export -f update_round_summary
