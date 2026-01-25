#!/usr/bin/env bash
# =============================================================================
# Shared Slug Generator Module (V1.1.0)
# =============================================================================
# Purpose: Centralized workload ID and slug generation for all skills
# Architecture: Unified Slug Naming Convention (2026-01-25)
# Usage: source /home/palantir/.claude/skills/shared/slug-generator.sh
# =============================================================================
#
# CHANGELOG (V1.1.0):
# - [CRITICAL-003 FIX] Include HHMMSS in slug for uniqueness
# - Slug format changed: {topic}-{YYYYMMDD} → {topic}-{YYYYMMDD}-{HHMMSS}
# - extract_workload_from_slug updated for new format
# - Same-day collision issue resolved
#
# CHANGELOG (V1.0.0):
# - Initial implementation from unified-slug-naming plan
# - Workload ID format: {topic}_{YYYYMMDD}_{HHMMSS}
# - Slug derivation: {topic}-{YYYYMMDD}
# - Centralized workload context management
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
SLUG_VERSION="1.1.0"
WORKLOAD_STATE_DIR=".agent/tmp/workload-state"
CURRENT_WORKLOAD_FILE="${WORKLOAD_STATE_DIR}/current.json"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Get ISO8601 timestamp
_slug_timestamp_iso() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Get short date (YYYYMMDD)
_slug_date_short() {
    date +%Y%m%d
}

# Get time component (HHMMSS)
_slug_time_short() {
    date +%H%M%S
}

# ============================================================================
# generate_workload_id
# Generate unique workload identifier
#
# Args:
#   $1 - Topic (human-readable description)
#
# Output:
#   Workload ID in format: {topic}_{YYYYMMDD}_{HHMMSS}
#
# Example:
#   generate_workload_id "user authentication"
#   → user-authentication_20260125_143022
# ============================================================================
generate_workload_id() {
    local topic="$1"
    local date_part
    local time_part

    date_part=$(_slug_date_short)
    time_part=$(_slug_time_short)

    # Normalize topic to slug format
    # Use [:alnum:] for portability (supports alphanumeric in any locale)
    local topic_slug
    topic_slug=$(echo "$topic" | \
        tr '[:upper:]' '[:lower:]' | \
        tr -cs '[:alnum:]' '-' | \
        sed 's/^-//' | \
        sed 's/-$//' | \
        cut -c1-40)

    echo "${topic_slug}_${date_part}_${time_part}"
}

# ============================================================================
# generate_slug_from_workload
# Derive slug from workload ID
#
# Args:
#   $1 - Workload ID (format: {topic}_{YYYYMMDD}_{HHMMSS})
#
# Output:
#   Slug in format: {topic}-{YYYYMMDD}-{HHMMSS}
#
# Example:
#   generate_slug_from_workload "user-authentication_20260125_143022"
#   → user-authentication-20260125-143022
# ============================================================================
generate_slug_from_workload() {
    local workload_id="$1"

    # Extract topic, date, and time from workload ID
    # Format: {topic}_{YYYYMMDD}_{HHMMSS}
    local topic_part
    local date_part
    local time_part

    # Split by underscore
    topic_part=$(echo "$workload_id" | awk -F_ '{print $1}')
    date_part=$(echo "$workload_id" | awk -F_ '{print $2}')
    time_part=$(echo "$workload_id" | awk -F_ '{print $3}')

    echo "${topic_part}-${date_part}-${time_part}"
}

# ============================================================================
# extract_workload_from_slug
# Extract workload information from slug
#
# Args:
#   $1 - Slug (format: {topic}-{YYYYMMDD}-{HHMMSS})
#
# Output:
#   JSON object with:
#     - topic: Topic string
#     - date: YYYYMMDD string
#     - time: HHMMSS string
#     - workload_id: Reconstructed workload ID
#
# Example:
#   extract_workload_from_slug "user-authentication-20260125-143022"
#   → {"topic":"user-authentication","date":"20260125","time":"143022","workload_id":"user-authentication_20260125_143022"}
# ============================================================================
extract_workload_from_slug() {
    local slug="$1"

    # Extract topic, date, and time from slug
    # Format: {topic}-{YYYYMMDD}-{HHMMSS}
    local topic_part
    local date_part
    local time_part

    # Split by last two components: 8 digits (date) and 6 digits (time)
    if [[ "$slug" =~ ^(.+)-([0-9]{8})-([0-9]{6})$ ]]; then
        topic_part="${BASH_REMATCH[1]}"
        date_part="${BASH_REMATCH[2]}"
        time_part="${BASH_REMATCH[3]}"
    else
        echo "ERROR: Invalid slug format: $slug (expected: {topic}-{YYYYMMDD}-{HHMMSS})" >&2
        return 1
    fi

    # Generate JSON output using jq for safe formatting
    jq -n \
        --arg topic "$topic_part" \
        --arg date "$date_part" \
        --arg time "$time_part" \
        --arg workload_id "${topic_part}_${date_part}_${time_part}" \
        '{
            topic: $topic,
            date: $date,
            time: $time,
            workload_id: $workload_id
        }'
}

# ============================================================================
# init_workload
# Initialize new workload context
#
# Args:
#   $1 - Workload ID
#   $2 - Skill name (clarify, research, planning, etc.)
#   $3 - Description (optional)
#
# Output:
#   Workload context file created
#
# Side Effects:
#   - Creates .agent/tmp/workload-state/current.json
#   - Creates .agent/tmp/workload-state/{workload_id}.json
# ============================================================================
init_workload() {
    local workload_id="$1"
    local skill="$2"
    local description="${3:-}"

    # Ensure state directory exists
    mkdir -p "$WORKLOAD_STATE_DIR"

    # Generate slug from workload ID
    local slug
    slug=$(generate_slug_from_workload "$workload_id")

    # Create workload context file
    local workload_file="${WORKLOAD_STATE_DIR}/${workload_id}.json"

    cat > "$workload_file" <<EOF
{
  "workload_id": "${workload_id}",
  "slug": "${slug}",
  "skill": "${skill}",
  "description": "${description}",
  "created_at": "$(_slug_timestamp_iso)",
  "status": "active",
  "files": {
    "prompts": ".agent/prompts/${slug}",
    "context": ".agent/prompts/_context.yaml",
    "progress": ".agent/prompts/_progress.yaml"
  }
}
EOF

    # Set as current workload
    cp "$workload_file" "$CURRENT_WORKLOAD_FILE"

    echo "✅ Workload initialized: ${workload_id} (slug: ${slug})"
}

# ============================================================================
# get_current_workload
# Retrieve current workload context
#
# Output:
#   JSON object with workload information
#   Returns empty object if no current workload
# ============================================================================
get_current_workload() {
    if [[ ! -f "$CURRENT_WORKLOAD_FILE" ]]; then
        echo "{}"
        return 0
    fi

    cat "$CURRENT_WORKLOAD_FILE"
}

# ============================================================================
# set_workload_context
# Update current workload context field
#
# Args:
#   $1 - Field name (status, description, etc.)
#   $2 - New value
#
# Side Effects:
#   Updates both current.json and workload-specific JSON file
# ============================================================================
set_workload_context() {
    local field="$1"
    local value="$2"

    if [[ ! -f "$CURRENT_WORKLOAD_FILE" ]]; then
        echo "ERROR: No current workload context" >&2
        return 1
    fi

    # Get workload ID
    local workload_id
    workload_id=$(jq -r '.workload_id' "$CURRENT_WORKLOAD_FILE")

    if [[ -z "$workload_id" || "$workload_id" == "null" ]]; then
        echo "ERROR: Invalid workload context" >&2
        return 1
    fi

    # Update both files
    local workload_file="${WORKLOAD_STATE_DIR}/${workload_id}.json"

    # Update field using jq
    jq ".${field} = \"${value}\"" "$CURRENT_WORKLOAD_FILE" > "${CURRENT_WORKLOAD_FILE}.tmp"
    mv "${CURRENT_WORKLOAD_FILE}.tmp" "$CURRENT_WORKLOAD_FILE"

    if [[ -f "$workload_file" ]]; then
        jq ".${field} = \"${value}\"" "$workload_file" > "${workload_file}.tmp"
        mv "${workload_file}.tmp" "$workload_file"
    fi

    echo "✅ Workload context updated: ${field} = ${value}"
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f generate_workload_id
export -f generate_slug_from_workload
export -f extract_workload_from_slug
export -f init_workload
export -f get_current_workload
export -f set_workload_context

# ============================================================================
# SELF-TEST (Optional - for development)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Slug Generator Self-Test ==="

    # Test 1: Generate workload ID
    echo "Test 1: generate_workload_id"
    workload_id=$(generate_workload_id "user authentication feature")
    echo "  Result: $workload_id"

    # Test 2: Derive slug
    echo "Test 2: generate_slug_from_workload"
    slug=$(generate_slug_from_workload "$workload_id")
    echo "  Result: $slug"

    # Test 3: Extract workload info
    echo "Test 3: extract_workload_from_slug"
    workload_info=$(extract_workload_from_slug "$slug")
    echo "  Result: $workload_info"

    # Test 4: Init workload
    echo "Test 4: init_workload"
    init_workload "$workload_id" "clarify" "Test workload"

    # Test 5: Get current workload
    echo "Test 5: get_current_workload"
    current=$(get_current_workload)
    echo "  Result: $current"

    # Test 6: Update context
    echo "Test 6: set_workload_context"
    set_workload_context "status" "completed"

    echo "=== All tests completed ==="
fi
