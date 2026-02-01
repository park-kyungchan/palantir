#!/usr/bin/env bash
# =============================================================================
# Workload Initialization Module (V1.0.0)
# =============================================================================
# Purpose: Initialize, validate, and manage active workload lifecycle
# Architecture: Unified Slug Naming Convention (2026-01-25)
# Usage: source /home/palantir/.claude/skills/shared/workload-init.sh
# =============================================================================
#
# FUNCTIONS:
#   ensure_active_workload(mode)     - Create/inherit/require active workload
#   detect_workload_staleness()      - Check if workload is fresh/stale/orphaned
#   verify_upstream_hash(phase)      - Verify upstream artifact integrity
#   store_workload_hash(hash, phase) - Store artifact hash in active workload
#
# MODES for ensure_active_workload:
#   create  - Generate new workload (for /clarify)
#   inherit - Use existing workload (for downstream skills)
#   require - Strict mode, fail if no workload exists
#
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
WORKLOAD_INIT_VERSION="1.0.0"
STALENESS_THRESHOLD_HOURS=24
PROMPTS_BASE_DIR=".agent/prompts"
ACTIVE_WORKLOAD_FILE="${PROMPTS_BASE_DIR}/_active_workload.yaml"

# ============================================================================
# SOURCE DEPENDENCIES
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source slug-generator if not already loaded
if ! command -v generate_workload_id &> /dev/null; then
    source "${SCRIPT_DIR}/slug-generator.sh"
fi

# Source workload-files if not already loaded
if ! command -v set_active_workload &> /dev/null; then
    source "${SCRIPT_DIR}/workload-files.sh"
fi

# Source workload-tracker if not already loaded
if ! command -v get_workload_prompt_dir &> /dev/null; then
    source "${SCRIPT_DIR}/workload-tracker.sh"
fi

# ============================================================================
# LOGGING
# ============================================================================
_workload_init_log() {
    local level="$1"
    local message="$2"
    local log_file="${WORKSPACE_ROOT:-.}/.agent/logs/workload_init.log"

    mkdir -p "$(dirname "$log_file")"
    echo "[$(date -Iseconds)] [$level] [WORKLOAD-INIT] $message" >> "$log_file"
}

# ============================================================================
# detect_workload_staleness
# Check if the active workload is fresh, stale, or orphaned
#
# Output (stdout):
#   WORKLOAD_FRESH:{slug}     - Workload is active and recently used
#   WORKLOAD_STALE:{reason}   - Workload exists but hasn't been used
#   WORKLOAD_ORPHANED:{slug}  - Workload directory missing or corrupted
#   NO_ACTIVE_WORKLOAD        - No active workload file exists
#
# Returns:
#   0 - Always (use output to determine state)
# ============================================================================
detect_workload_staleness() {
    local active_slug
    local workload_dir
    local updated_at
    local hours_since_update

    # Check if active workload file exists
    if [[ ! -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        echo "NO_ACTIVE_WORKLOAD"
        return 0
    fi

    # Get active workload slug
    active_slug=$(get_active_workload_slug 2>/dev/null || echo "")

    if [[ -z "$active_slug" ]]; then
        echo "NO_ACTIVE_WORKLOAD"
        return 0
    fi

    # Check if workload directory exists
    workload_dir="${PROMPTS_BASE_DIR}/${active_slug}"
    if [[ ! -d "$workload_dir" ]]; then
        _workload_init_log "WARN" "Orphaned workload: $active_slug (directory missing)"
        echo "WORKLOAD_ORPHANED:${active_slug}"
        return 0
    fi

    # Check if _context.yaml exists
    if [[ ! -f "${workload_dir}/_context.yaml" ]]; then
        _workload_init_log "WARN" "Orphaned workload: $active_slug (context missing)"
        echo "WORKLOAD_ORPHANED:${active_slug}"
        return 0
    fi

    # Check staleness by updated_at timestamp
    updated_at=$(grep -oP 'updated_at:\s*"\K[^"]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null || echo "")

    if [[ -z "$updated_at" ]]; then
        # No timestamp, consider stale
        echo "WORKLOAD_STALE:no_timestamp"
        return 0
    fi

    # Calculate hours since last update
    local now_epoch
    local updated_epoch
    now_epoch=$(date +%s)
    updated_epoch=$(date -d "$updated_at" +%s 2>/dev/null || echo "0")

    if [[ "$updated_epoch" == "0" ]]; then
        echo "WORKLOAD_STALE:invalid_timestamp"
        return 0
    fi

    hours_since_update=$(( (now_epoch - updated_epoch) / 3600 ))

    if [[ $hours_since_update -gt $STALENESS_THRESHOLD_HOURS ]]; then
        _workload_init_log "INFO" "Stale workload: $active_slug (${hours_since_update}h old)"
        echo "WORKLOAD_STALE:${hours_since_update}h_old"
        return 0
    fi

    _workload_init_log "INFO" "Fresh workload: $active_slug"
    echo "WORKLOAD_FRESH:${active_slug}"
    return 0
}

# ============================================================================
# ensure_active_workload
# Ensure an active workload exists with the specified mode
#
# Args:
#   $1 - Mode: "create" | "inherit" | "require"
#
# Environment Variables (optional):
#   WORKLOAD_SLUG - Specific slug to use (for resume scenarios)
#   TOPIC         - Topic for new workload (defaults to "unnamed")
#
# Output (stdout):
#   WORKLOAD_CREATED:{slug}   - New workload was created
#   WORKLOAD_INHERITED:{slug} - Existing workload was inherited
#   WORKLOAD_SET:{slug}       - Workload was explicitly set from env
#   WORKLOAD_MISSING          - No workload found (inherit mode)
#
# Returns:
#   0 - Success
#   1 - Failure (require mode with no workload)
# ============================================================================
ensure_active_workload() {
    local mode="${1:-inherit}"
    local workload_slug="${WORKLOAD_SLUG:-}"
    local topic="${TOPIC:-unnamed}"
    local workload_id
    local slug

    _workload_init_log "INFO" "ensure_active_workload called with mode=$mode"

    # If WORKLOAD_SLUG is explicitly set, use it
    if [[ -n "$workload_slug" ]]; then
        _workload_init_log "INFO" "Using explicit WORKLOAD_SLUG: $workload_slug"

        # Verify the workload directory exists
        local workload_dir="${PROMPTS_BASE_DIR}/${workload_slug}"
        if [[ -d "$workload_dir" ]]; then
            # Update active workload file
            _update_active_workload_file "$workload_slug"
            echo "WORKLOAD_SET:${workload_slug}"
            return 0
        else
            _workload_init_log "WARN" "Specified workload directory not found: $workload_dir"
            # Fall through to mode-based handling
        fi
    fi

    case "$mode" in
        create)
            # Generate new workload
            workload_id=$(generate_workload_id "$topic")
            slug=$(generate_slug_from_workload "$workload_id")

            _workload_init_log "INFO" "Creating new workload: $workload_id (slug: $slug)"

            # Initialize workload directory
            init_workload_directory "$workload_id"

            # Set as active workload
            set_active_workload "$workload_id"

            echo "WORKLOAD_CREATED:${slug}"
            return 0
            ;;

        inherit)
            # Try to use existing workload
            local current_id
            current_id=$(get_active_workload 2>/dev/null || echo "")

            if [[ -n "$current_id" ]]; then
                slug=$(generate_slug_from_workload "$current_id")

                # Verify workload directory exists
                local workload_dir="${PROMPTS_BASE_DIR}/${slug}"
                if [[ -d "$workload_dir" ]]; then
                    # Update timestamp
                    _touch_active_workload
                    _workload_init_log "INFO" "Inherited workload: $slug"
                    echo "WORKLOAD_INHERITED:${slug}"
                    return 0
                fi
            fi

            _workload_init_log "WARN" "No active workload to inherit"
            echo "WORKLOAD_MISSING"
            return 0
            ;;

        require)
            # Strict mode - fail if no workload
            local current_id
            current_id=$(get_active_workload 2>/dev/null || echo "")

            if [[ -z "$current_id" ]]; then
                _workload_init_log "ERROR" "Required workload not found"
                echo "WORKLOAD_MISSING"
                return 1
            fi

            slug=$(generate_slug_from_workload "$current_id")

            # Verify workload directory exists
            local workload_dir="${PROMPTS_BASE_DIR}/${slug}"
            if [[ ! -d "$workload_dir" ]]; then
                _workload_init_log "ERROR" "Required workload directory missing: $slug"
                echo "WORKLOAD_MISSING"
                return 1
            fi

            _touch_active_workload
            _workload_init_log "INFO" "Required workload verified: $slug"
            echo "WORKLOAD_INHERITED:${slug}"
            return 0
            ;;

        *)
            _workload_init_log "ERROR" "Unknown mode: $mode"
            echo "ERROR:unknown_mode"
            return 1
            ;;
    esac
}

# ============================================================================
# verify_upstream_hash
# Verify the integrity of upstream artifact hash
#
# Args:
#   $1 - Phase: "clarify" | "research" | "planning"
#
# Output (stdout):
#   HASH_VERIFIED:{hash}        - Hash matches stored value
#   HASH_MISSING:{phase}        - No hash stored for this phase
#   HASH_MISMATCH:{expected}    - Hash doesn't match (tampering detected)
#   HASH_ARTIFACT_MISSING:{path} - Artifact file doesn't exist
#
# Returns:
#   0 - Verified or missing (soft failure)
#   1 - Mismatch (hard failure)
# ============================================================================
verify_upstream_hash() {
    local phase="$1"
    local slug
    local artifact_path
    local stored_hash
    local computed_hash

    # Get active workload slug
    slug=$(get_active_workload_slug 2>/dev/null || echo "")

    if [[ -z "$slug" ]]; then
        echo "HASH_MISSING:no_active_workload"
        return 0
    fi

    # Determine artifact path based on phase
    case "$phase" in
        clarify)
            artifact_path="${PROMPTS_BASE_DIR}/${slug}/clarify.yaml"
            ;;
        research)
            artifact_path="${PROMPTS_BASE_DIR}/${slug}/research.md"
            ;;
        planning)
            artifact_path="${PROMPTS_BASE_DIR}/${slug}/plan.yaml"
            ;;
        *)
            echo "HASH_MISSING:unknown_phase"
            return 0
            ;;
    esac

    # Check if artifact exists
    if [[ ! -f "$artifact_path" ]]; then
        _workload_init_log "WARN" "Artifact missing for $phase: $artifact_path"
        echo "HASH_ARTIFACT_MISSING:${artifact_path}"
        return 0
    fi

    # Get stored hash from active workload file
    local hash_field="${phase}_hash"
    stored_hash=$(grep -oP "${hash_field}:\s*\"\K[^\"]+|${hash_field}:\s*\K[^\s]+" "$ACTIVE_WORKLOAD_FILE" 2>/dev/null || echo "")

    if [[ -z "$stored_hash" || "$stored_hash" == "null" ]]; then
        _workload_init_log "INFO" "No stored hash for $phase"
        echo "HASH_MISSING:${phase}"
        return 0
    fi

    # Compute current hash
    computed_hash=$(sha256sum "$artifact_path" | cut -d' ' -f1)

    if [[ "$stored_hash" == "$computed_hash" ]]; then
        _workload_init_log "INFO" "Hash verified for $phase"
        echo "HASH_VERIFIED:${computed_hash}"
        return 0
    else
        _workload_init_log "ERROR" "Hash mismatch for $phase: expected=$stored_hash, got=$computed_hash"
        echo "HASH_MISMATCH:${stored_hash}"
        return 1
    fi
}

# ============================================================================
# store_workload_hash
# Store artifact hash in the active workload file
#
# Args:
#   $1 - Hash value (SHA256)
#   $2 - Phase: "clarify" | "research" | "planning" | "re-architecture"
#
# Returns:
#   0 - Success
#   1 - Failure
# ============================================================================
store_workload_hash() {
    local hash="$1"
    local phase="$2"
    local hash_field="${phase}_hash"

    if [[ ! -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        _workload_init_log "ERROR" "Cannot store hash: no active workload file"
        return 1
    fi

    # Check if hash field already exists
    if grep -q "^${hash_field}:" "$ACTIVE_WORKLOAD_FILE" 2>/dev/null; then
        # Update existing field
        sed -i "s/^${hash_field}:.*/${hash_field}: \"${hash}\"/" "$ACTIVE_WORKLOAD_FILE"
    else
        # Append new field
        echo "${hash_field}: \"${hash}\"" >> "$ACTIVE_WORKLOAD_FILE"
    fi

    # Update timestamp
    _touch_active_workload

    _workload_init_log "INFO" "Stored $phase hash: ${hash:0:16}..."
    return 0
}

# ============================================================================
# INTERNAL HELPER FUNCTIONS
# ============================================================================

# Update active workload file with new slug (creates if not exists)
_update_active_workload_file() {
    local slug="$1"
    local workload_id

    # Try to derive workload_id from slug
    workload_id=$(echo "$slug" | tr '-' '_')

    mkdir -p "$(dirname "$ACTIVE_WORKLOAD_FILE")"

    cat > "$ACTIVE_WORKLOAD_FILE" <<EOF
# Active Workload Pointer
# Generated by workload-init.sh V${WORKLOAD_INIT_VERSION}

workload_id: "${workload_id}"
slug: "${slug}"
current_skill: "unknown"
updated_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EOF

    _workload_init_log "INFO" "Updated active workload file: $slug"
}

# Touch active workload file to update timestamp
_touch_active_workload() {
    if [[ -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        local new_timestamp
        new_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        if grep -q "^updated_at:" "$ACTIVE_WORKLOAD_FILE" 2>/dev/null; then
            sed -i "s/^updated_at:.*/updated_at: \"${new_timestamp}\"/" "$ACTIVE_WORKLOAD_FILE"
        else
            echo "updated_at: \"${new_timestamp}\"" >> "$ACTIVE_WORKLOAD_FILE"
        fi
    fi
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f ensure_active_workload
export -f detect_workload_staleness
export -f verify_upstream_hash
export -f store_workload_hash

# ============================================================================
# SELF-TEST (when run directly)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== workload-init.sh Self-Test ==="
    echo "Version: $WORKLOAD_INIT_VERSION"
    echo ""

    echo "Test 1: detect_workload_staleness"
    result=$(detect_workload_staleness)
    echo "  Result: $result"
    echo ""

    echo "Test 2: ensure_active_workload (inherit mode)"
    export TOPIC="self-test"
    result=$(ensure_active_workload "inherit")
    echo "  Result: $result"
    echo ""

    echo "Test 3: ensure_active_workload (create mode)"
    result=$(ensure_active_workload "create")
    echo "  Result: $result"
    echo ""

    echo "Test 4: verify_upstream_hash (research)"
    result=$(verify_upstream_hash "research")
    echo "  Result: $result"
    echo ""

    echo "=== Self-Test Complete ==="
fi
