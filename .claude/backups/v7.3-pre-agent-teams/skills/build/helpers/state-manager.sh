#!/bin/bash
# ============================================================================
# /build Skill - State Manager
# Version: 1.0.0
# ============================================================================
#
# State persistence utilities for multi-round builder sessions.
# Source this file: source .claude/skills/build/helpers/state-manager.sh
#
# ============================================================================

# ============================================================================
# CONFIGURATION
# ============================================================================

BUILD_STATE_DIR="${BUILD_STATE_DIR:-.agent/builds}"
BUILD_STATE_FILE=""

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

generate_build_id() {
    # Generate unique build session ID
    local prefix="${1:-build}"
    local timestamp
    timestamp=$(date +%s)
    local random
    random=$(head -c 4 /dev/urandom | xxd -p)
    echo "${prefix}-${random}"
}

init_build_session() {
    local component_type="$1"  # agent | skill | hook
    local build_id
    build_id=$(generate_build_id "$component_type")

    # Create state directory
    mkdir -p "$BUILD_STATE_DIR"

    # Set state file path
    BUILD_STATE_FILE="$BUILD_STATE_DIR/${build_id}.yaml"

    # Initialize state file
    cat > "$BUILD_STATE_FILE" << EOF
# Build Session State
# ID: ${build_id}
# Type: ${component_type}
# Created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

metadata:
  id: "${build_id}"
  type: "${component_type}"
  created_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  status: "in_progress"
  current_round: 1

state:
  # Collected values from each round
EOF

    echo "$build_id"
}

load_build_session() {
    local build_id="$1"
    BUILD_STATE_FILE="$BUILD_STATE_DIR/${build_id}.yaml"

    if [[ ! -f "$BUILD_STATE_FILE" ]]; then
        echo "❌ Build session not found: $build_id"
        return 1
    fi

    echo "✅ Loaded build session: $build_id"
    return 0
}

# ============================================================================
# STATE READ/WRITE
# ============================================================================

get_state_value() {
    local key="$1"
    local default="${2:-}"

    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        echo "$default"
        return 1
    fi

    # Use yq if available, otherwise grep
    if command -v yq &> /dev/null; then
        local value
        value=$(yq -r ".state.$key // \"$default\"" "$BUILD_STATE_FILE")
        echo "$value"
    else
        # Fallback: simple grep (limited)
        grep -E "^  $key:" "$BUILD_STATE_FILE" | sed 's/.*: //' | tr -d '"' || echo "$default"
    fi
}

set_state_value() {
    local key="$1"
    local value="$2"

    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        echo "❌ No active build session"
        return 1
    fi

    # Update timestamp
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    if command -v yq &> /dev/null; then
        # Use yq for proper YAML handling
        yq -i ".state.$key = \"$value\" | .metadata.updated_at = \"$timestamp\"" "$BUILD_STATE_FILE"
    else
        # Fallback: append to state section
        echo "  $key: \"$value\"" >> "$BUILD_STATE_FILE"
        sed -i "s/updated_at:.*/updated_at: \"$timestamp\"/" "$BUILD_STATE_FILE"
    fi
}

set_state_array() {
    local key="$1"
    shift
    local values=("$@")

    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        echo "❌ No active build session"
        return 1
    fi

    if command -v yq &> /dev/null; then
        # Build JSON array
        local json_array
        json_array=$(printf '%s\n' "${values[@]}" | jq -R . | jq -s .)

        yq -i ".state.$key = $json_array" "$BUILD_STATE_FILE"
    else
        # Fallback: manual YAML array
        {
            echo "  $key:"
            for v in "${values[@]}"; do
                echo "    - \"$v\""
            done
        } >> "$BUILD_STATE_FILE"
    fi
}

increment_round() {
    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        return 1
    fi

    if command -v yq &> /dev/null; then
        yq -i '.metadata.current_round += 1' "$BUILD_STATE_FILE"
    fi
}

get_current_round() {
    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        echo "1"
        return
    fi

    if command -v yq &> /dev/null; then
        yq -r '.metadata.current_round // 1' "$BUILD_STATE_FILE"
    else
        echo "1"
    fi
}

# ============================================================================
# SESSION STATUS
# ============================================================================

set_session_status() {
    local status="$1"  # in_progress | completed | cancelled | error

    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        return 1
    fi

    if command -v yq &> /dev/null; then
        yq -i ".metadata.status = \"$status\"" "$BUILD_STATE_FILE"
    else
        sed -i "s/status:.*/status: \"$status\"/" "$BUILD_STATE_FILE"
    fi
}

get_session_status() {
    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        echo "unknown"
        return
    fi

    if command -v yq &> /dev/null; then
        yq -r '.metadata.status // "unknown"' "$BUILD_STATE_FILE"
    else
        grep "status:" "$BUILD_STATE_FILE" | head -1 | sed 's/.*: //' | tr -d '"'
    fi
}

finalize_session() {
    local output_path="$1"

    set_session_status "completed"
    set_state_value "output_path" "$output_path"

    echo "✅ Build session completed"
    echo "   Output: $output_path"
    echo "   State: $BUILD_STATE_FILE"
}

cancel_session() {
    local reason="${1:-User cancelled}"

    set_session_status "cancelled"
    set_state_value "cancel_reason" "$reason"

    echo "⚠️  Build session cancelled: $reason"
}

# ============================================================================
# STATE EXPORT
# ============================================================================

export_state_as_yaml() {
    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        echo "❌ No active build session"
        return 1
    fi

    cat "$BUILD_STATE_FILE"
}

export_state_as_json() {
    if [[ -z "$BUILD_STATE_FILE" || ! -f "$BUILD_STATE_FILE" ]]; then
        echo "{}"
        return 1
    fi

    if command -v yq &> /dev/null; then
        yq -o=json '.state' "$BUILD_STATE_FILE"
    else
        echo "{}"
    fi
}

get_state_for_template() {
    # Export state in a format suitable for template rendering
    export_state_as_json | jq -c '.'
}

# ============================================================================
# SESSION LISTING
# ============================================================================

list_build_sessions() {
    local filter="${1:-}"  # Optional: agent | skill | hook | in_progress

    if [[ ! -d "$BUILD_STATE_DIR" ]]; then
        echo "No build sessions found"
        return
    fi

    echo "Build Sessions:"
    echo "==============="

    for file in "$BUILD_STATE_DIR"/*.yaml; do
        [[ -f "$file" ]] || continue

        local id
        local type
        local status
        local created

        if command -v yq &> /dev/null; then
            id=$(yq -r '.metadata.id' "$file")
            type=$(yq -r '.metadata.type' "$file")
            status=$(yq -r '.metadata.status' "$file")
            created=$(yq -r '.metadata.created_at' "$file")
        else
            id=$(basename "$file" .yaml)
            type="unknown"
            status="unknown"
            created="unknown"
        fi

        # Apply filter
        if [[ -n "$filter" ]]; then
            if [[ "$filter" != "$type" && "$filter" != "$status" ]]; then
                continue
            fi
        fi

        printf "  %-20s  %-8s  %-12s  %s\n" "$id" "$type" "$status" "$created"
    done
}

cleanup_old_sessions() {
    local days="${1:-7}"  # Days to keep

    if [[ ! -d "$BUILD_STATE_DIR" ]]; then
        return
    fi

    find "$BUILD_STATE_DIR" -name "*.yaml" -mtime "+$days" -delete

    echo "✅ Cleaned up sessions older than $days days"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

get_build_state_file() {
    echo "$BUILD_STATE_FILE"
}

get_build_state_dir() {
    echo "$BUILD_STATE_DIR"
}

# Check if yq is available (better YAML handling)
check_yq_available() {
    if command -v yq &> /dev/null; then
        return 0
    else
        echo "⚠️  yq not found. Using fallback methods."
        echo "   Install yq for better YAML handling: https://github.com/mikefarah/yq"
        return 1
    fi
}
