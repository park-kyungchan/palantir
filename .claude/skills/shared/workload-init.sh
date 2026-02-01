#!/usr/bin/env bash
# =============================================================================
# Workload Initialization & Integrity Module (V1.0.0)
# =============================================================================
# Purpose: Workload lifecycle management and semantic integrity verification
# Architecture: Shift-Left validation for pipeline consistency
# Usage: source /home/palantir/.claude/skills/shared/workload-init.sh
# =============================================================================
#
# FUNCTIONS:
#   1. ensure_active_workload(mode)   - Create/inherit/require workload
#   2. store_workload_hash(hash, phase) - Store artifact hash
#   3. verify_upstream_hash(phase)    - Verify upstream artifact integrity
#   4. detect_workload_staleness()    - Check if workload is stale (>24h)
#   5. migrate_legacy_slug(slug)      - Migrate pre-V1.1.0 slug format
#
# CHANGELOG (V1.0.0):
#   - Initial implementation from Pipeline Workload Consistency plan
#   - Shift-Left validation gates for all pipeline skills
#   - Hash-based semantic integrity verification
#   - TTL-based staleness detection (24h default)
#   - Legacy slug format migration support
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
WORKLOAD_INIT_VERSION="1.0.0"
WORKLOAD_TTL_HOURS="${WORKLOAD_TTL_HOURS:-24}"
ACTIVE_WORKLOAD_FILE=".agent/prompts/_active_workload.yaml"
VALIDATION_GATES_LOG=".agent/logs/validation_gates.log"

# Strict mode (fail on hash mismatch) - default is warn only
WORKLOAD_STRICT_MODE="${WORKLOAD_STRICT_MODE:-false}"

# ============================================================================
# SOURCE DEPENDENCIES
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source required modules (check if already loaded to avoid circular deps)
if ! command -v generate_workload_id &> /dev/null; then
    # shellcheck source=./slug-generator.sh
    source "${SCRIPT_DIR}/slug-generator.sh"
fi

if ! command -v init_workload_directory &> /dev/null; then
    # shellcheck source=./workload-files.sh
    source "${SCRIPT_DIR}/workload-files.sh"
fi

if ! command -v get_workload_prompt_dir &> /dev/null; then
    # shellcheck source=./workload-tracker.sh
    source "${SCRIPT_DIR}/workload-tracker.sh"
fi

# ============================================================================
# UTILITY: Logging
# ============================================================================
_log_gate() {
    local gate="$1"
    local level="$2"
    local message="$3"
    local timestamp
    timestamp=$(date -Iseconds)

    mkdir -p "$(dirname "$VALIDATION_GATES_LOG")"
    echo "[${timestamp}] GATE_${gate} [${level}] ${message}" >> "$VALIDATION_GATES_LOG"
}

# ============================================================================
# ensure_active_workload(mode)
# ============================================================================
# Ensure an active workload exists based on the specified mode
#
# Args:
#   $1 - mode: "create" | "inherit" | "require"
#        - create:  Create new workload (for /clarify)
#        - inherit: Use existing or create if WORKLOAD_SLUG provided (for /research, /planning)
#        - require: Must have existing workload, fail if not (for /worker)
#
# Environment Variables:
#   TOPIC         - Topic for new workload (used with mode=create)
#   WORKLOAD_SLUG - Explicit workload slug to set (used with mode=inherit)
#
# Output:
#   WORKLOAD_CREATED:<slug>   - New workload created
#   WORKLOAD_INHERITED:<slug> - Existing workload inherited
#   WORKLOAD_SET:<slug>       - Workload set from explicit parameter
#   WORKLOAD_VERIFIED:<slug>  - Workload verified (require mode)
#   WORKLOAD_MISSING          - No workload found (error)
#   WORKLOAD_ORPHANED:<slug>  - Directory missing for workload (error)
#
# Returns:
#   0 - Success
#   1 - Error (no workload, orphaned directory, etc.)
# ============================================================================
ensure_active_workload() {
    local mode="${1:-inherit}"
    local current_workload

    # Get current active workload (may be empty)
    current_workload=$(get_active_workload 2>/dev/null || echo "")

    case "$mode" in
        create)
            # Always create new workload for /clarify
            local topic="${TOPIC:-unnamed}"
            local new_workload_id
            local new_slug

            new_workload_id=$(generate_workload_id "$topic")
            new_slug=$(generate_slug_from_workload "$new_workload_id")

            # Initialize workload
            set_active_workload "$new_workload_id"
            init_workload_directory "$new_workload_id"

            _log_gate "WORKLOAD" "INFO" "Created new workload: $new_slug (topic: $topic)"
            echo "WORKLOAD_CREATED:$new_slug"
            ;;

        inherit)
            if [[ -n "$current_workload" ]]; then
                # Validate workload directory exists
                local workload_dir
                workload_dir=$(get_workload_prompt_dir "$current_workload")

                if [[ -d "$workload_dir" ]]; then
                    _log_gate "WORKLOAD" "INFO" "Inherited workload: $current_workload"
                    echo "WORKLOAD_INHERITED:$current_workload"
                else
                    _log_gate "WORKLOAD" "ERROR" "Orphaned workload: $current_workload (dir missing: $workload_dir)"
                    echo "WORKLOAD_ORPHANED:$current_workload" >&2
                    return 1
                fi
            else
                # No active workload - check for explicit parameter
                if [[ -n "${WORKLOAD_SLUG:-}" ]]; then
                    set_active_workload "$WORKLOAD_SLUG"

                    # Initialize directory if it doesn't exist
                    local workload_dir
                    workload_dir=$(get_workload_prompt_dir "$WORKLOAD_SLUG")
                    if [[ ! -d "$workload_dir" ]]; then
                        init_workload_directory "$WORKLOAD_SLUG"
                    fi

                    _log_gate "WORKLOAD" "INFO" "Set workload from WORKLOAD_SLUG: $WORKLOAD_SLUG"
                    echo "WORKLOAD_SET:$WORKLOAD_SLUG"
                else
                    _log_gate "WORKLOAD" "WARN" "No active workload and no WORKLOAD_SLUG provided"
                    echo "WORKLOAD_MISSING" >&2
                    return 1
                fi
            fi
            ;;

        require)
            if [[ -z "$current_workload" ]]; then
                _log_gate "WORKLOAD" "ERROR" "Active workload required but not found"
                echo "ERROR: Active workload required but not found" >&2
                echo "Run /clarify or /orchestrate first" >&2
                return 1
            fi

            local workload_dir
            workload_dir=$(get_workload_prompt_dir "$current_workload")

            if [[ ! -d "$workload_dir" ]]; then
                _log_gate "WORKLOAD" "ERROR" "Workload directory not found: $workload_dir"
                echo "ERROR: Workload directory not found: $current_workload" >&2
                return 1
            fi

            _log_gate "WORKLOAD" "INFO" "Verified workload: $current_workload"
            echo "WORKLOAD_VERIFIED:$current_workload"
            ;;

        *)
            _log_gate "WORKLOAD" "ERROR" "Unknown mode: $mode"
            echo "ERROR: Unknown mode: $mode" >&2
            return 1
            ;;
    esac

    return 0
}

# ============================================================================
# store_workload_hash(hash, phase)
# ============================================================================
# Store artifact hash in _active_workload.yaml for integrity verification
#
# Args:
#   $1 - hash:  SHA256 hash of the artifact
#   $2 - phase: Pipeline phase (clarify, research, planning, orchestrate)
#
# Output:
#   HASH_STORED:<phase>:<hash>
#
# Side Effects:
#   Updates _active_workload.yaml with {phase}_hash field
#
# Returns:
#   0 - Success
#   1 - No active workload
# ============================================================================
store_workload_hash() {
    local hash="$1"
    local phase="$2"
    local workload

    workload=$(get_active_workload 2>/dev/null || echo "")

    if [[ -z "$workload" ]]; then
        _log_gate "HASH" "ERROR" "No active workload to store hash"
        echo "ERROR: No active workload to store hash" >&2
        return 1
    fi

    # Update _active_workload.yaml with phase hash
    if [[ -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        # Check if hash field already exists
        if grep -q "^${phase}_hash:" "$ACTIVE_WORKLOAD_FILE"; then
            # Update existing hash
            sed -i "s/^${phase}_hash:.*/${phase}_hash: \"${hash}\"/" "$ACTIVE_WORKLOAD_FILE"
        else
            # Append new hash field
            echo "${phase}_hash: \"${hash}\"" >> "$ACTIVE_WORKLOAD_FILE"
        fi

        # Update last_activity timestamp
        local now
        now=$(date -Iseconds)
        if grep -q "^last_activity:" "$ACTIVE_WORKLOAD_FILE"; then
            sed -i "s/^last_activity:.*/last_activity: \"${now}\"/" "$ACTIVE_WORKLOAD_FILE"
        else
            echo "last_activity: \"${now}\"" >> "$ACTIVE_WORKLOAD_FILE"
        fi
    fi

    _log_gate "HASH" "INFO" "Stored ${phase} hash: ${hash:0:16}..."
    echo "HASH_STORED:${phase}:${hash}"
    return 0
}

# ============================================================================
# verify_upstream_hash(upstream_phase)
# ============================================================================
# Verify the hash from upstream phase hasn't changed (semantic integrity)
#
# Args:
#   $1 - upstream_phase: The phase to verify (clarify, research, planning)
#
# Output:
#   HASH_VERIFIED:<phase>      - Hash matches
#   HASH_MISMATCH:<phase>      - Hash differs (artifact modified)
#   WARN: No stored hash       - No hash to verify (backward compatibility)
#
# Environment Variables:
#   WORKLOAD_STRICT_MODE - If "true", return 1 on mismatch
#
# Returns:
#   0 - Hash verified or no hash stored (warn only)
#   1 - Hash mismatch AND strict mode enabled
# ============================================================================
verify_upstream_hash() {
    local upstream="$1"
    local workload

    workload=$(get_active_workload 2>/dev/null || echo "")

    if [[ -z "$workload" ]]; then
        _log_gate "HASH" "ERROR" "No active workload for hash verification"
        echo "ERROR: No active workload for hash verification" >&2
        return 1
    fi

    # Get stored hash from _active_workload.yaml
    local stored_hash=""
    if [[ -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        stored_hash=$(grep "^${upstream}_hash:" "$ACTIVE_WORKLOAD_FILE" 2>/dev/null | \
            sed 's/^[^:]*: *"\?\([^"]*\)"\?/\1/' || echo "")
    fi

    if [[ -z "$stored_hash" ]]; then
        _log_gate "HASH" "WARN" "No stored hash for ${upstream} phase (backward compatibility)"
        echo "WARN: No stored hash for $upstream phase" >&2
        return 0  # Allow proceeding for backward compatibility
    fi

    # Determine artifact path based on upstream phase
    local workload_dir
    workload_dir=$(get_workload_prompt_dir "$workload")
    local artifact_path

    case "$upstream" in
        clarify)
            artifact_path="${workload_dir}/clarify.yaml"
            ;;
        research)
            artifact_path="${workload_dir}/research.md"
            ;;
        planning)
            artifact_path="${workload_dir}/plan.yaml"
            ;;
        orchestrate)
            artifact_path="${workload_dir}/_context.yaml"
            ;;
        re-architecture)
            artifact_path="${workload_dir}/re-architecture-log.yaml"
            ;;
        *)
            _log_gate "HASH" "ERROR" "Unknown upstream phase: $upstream"
            echo "ERROR: Unknown upstream phase: $upstream" >&2
            return 1
            ;;
    esac

    # Compute current hash if artifact exists
    if [[ -f "$artifact_path" ]]; then
        local current_hash
        current_hash=$(sha256sum "$artifact_path" | cut -d' ' -f1)

        if [[ "$stored_hash" != "$current_hash" ]]; then
            _log_gate "HASH" "ERROR" "Hash mismatch for ${upstream}: stored=${stored_hash:0:16}... current=${current_hash:0:16}..."
            echo "ERROR: Hash mismatch for $upstream" >&2
            echo "  Stored:  ${stored_hash}" >&2
            echo "  Current: ${current_hash}" >&2
            echo "  File:    ${artifact_path}" >&2
            echo "HASH_MISMATCH:${upstream}" >&2

            if [[ "$WORKLOAD_STRICT_MODE" == "true" ]]; then
                return 1
            fi
            return 0  # Warn only in non-strict mode
        fi

        _log_gate "HASH" "INFO" "Hash verified for ${upstream}: ${stored_hash:0:16}..."
    else
        _log_gate "HASH" "WARN" "Artifact file not found: $artifact_path"
        echo "WARN: Artifact file not found: $artifact_path" >&2
    fi

    echo "HASH_VERIFIED:${upstream}"
    return 0
}

# ============================================================================
# detect_workload_staleness()
# ============================================================================
# Check if active workload is stale (exceeds TTL)
#
# Output:
#   NO_ACTIVE_WORKLOAD        - No active workload
#   WORKLOAD_FRESH:<slug>:<hours>h - Workload is fresh
#   WORKLOAD_STALE:<slug>:<hours>h - Workload exceeds TTL
#   WORKLOAD_ORPHANED:<slug>  - Workload directory missing
#
# Environment Variables:
#   WORKLOAD_TTL_HOURS - TTL in hours (default: 24)
#
# Returns:
#   0 - Fresh or no active workload
#   1 - Orphaned workload
#   2 - Stale workload (exceeds TTL)
# ============================================================================
detect_workload_staleness() {
    local workload
    workload=$(get_active_workload 2>/dev/null || echo "")

    if [[ -z "$workload" ]]; then
        echo "NO_ACTIVE_WORKLOAD"
        return 0
    fi

    local workload_dir
    workload_dir=$(get_workload_prompt_dir "$workload")

    if [[ ! -d "$workload_dir" ]]; then
        _log_gate "STALENESS" "ERROR" "Orphaned workload: $workload"
        echo "WORKLOAD_ORPHANED:$workload"
        return 1
    fi

    # Find most recent file modification in workload directory
    local last_modified
    last_modified=$(find "$workload_dir" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1)

    if [[ -z "$last_modified" ]]; then
        # No files in workload directory - check directory mtime
        last_modified=$(stat -c '%Y' "$workload_dir" 2>/dev/null || echo "")
        if [[ -z "$last_modified" ]]; then
            echo "NO_FILES_IN_WORKLOAD"
            return 0
        fi
    fi

    # Calculate age in hours
    local now
    now=$(date +%s)
    local age_seconds
    age_seconds=$(( now - ${last_modified%.*} ))
    local age_hours
    age_hours=$(( age_seconds / 3600 ))

    if [[ $age_hours -ge $WORKLOAD_TTL_HOURS ]]; then
        _log_gate "STALENESS" "WARN" "Stale workload: $workload (${age_hours}h >= ${WORKLOAD_TTL_HOURS}h TTL)"
        echo "WORKLOAD_STALE:${workload}:${age_hours}h"
        return 2
    fi

    _log_gate "STALENESS" "INFO" "Fresh workload: $workload (${age_hours}h < ${WORKLOAD_TTL_HOURS}h TTL)"
    echo "WORKLOAD_FRESH:${workload}:${age_hours}h"
    return 0
}

# ============================================================================
# migrate_legacy_slug(slug)
# ============================================================================
# Convert pre-V1.1.0 slug format to current format
#
# Args:
#   $1 - old_slug: Legacy slug in format {topic}-{YYYYMMDD}
#
# Output:
#   ALREADY_MIGRATED:<slug>     - Already in new format
#   MIGRATED:<old>→<new>        - Successfully migrated
#   MIGRATION_SKIPPED:reason    - Migration skipped (conflict, etc.)
#   UNKNOWN_FORMAT:<slug>       - Unrecognized format
#
# Side Effects:
#   - Renames workload directory from old to new format
#   - Updates _active_workload.yaml to new slug
#
# Returns:
#   0 - Success (migrated or already migrated)
#   1 - Unknown format or error
# ============================================================================
migrate_legacy_slug() {
    local old_slug="$1"

    # Check if already in new format: {topic}-{YYYYMMDD}-{HHMMSS}
    if [[ "$old_slug" =~ ^(.+)-([0-9]{8})-([0-9]{6})$ ]]; then
        _log_gate "MIGRATION" "INFO" "Slug already in new format: $old_slug"
        echo "ALREADY_MIGRATED:$old_slug"
        return 0
    fi

    # Check if in old format: {topic}-{YYYYMMDD}
    if [[ "$old_slug" =~ ^(.+)-([0-9]{8})$ ]]; then
        local topic="${BASH_REMATCH[1]}"
        local date="${BASH_REMATCH[2]}"
        local new_slug="${old_slug}-000000"

        local old_dir=".agent/prompts/$old_slug"
        local new_dir=".agent/prompts/$new_slug"

        # Check for directory rename conditions
        if [[ -d "$old_dir" && ! -d "$new_dir" ]]; then
            mv "$old_dir" "$new_dir"

            # Update active workload if it was the old slug
            local current
            current=$(get_active_workload 2>/dev/null || echo "")
            if [[ "$current" == "$old_slug" ]]; then
                set_active_workload "$new_slug"
            fi

            _log_gate "MIGRATION" "INFO" "Migrated slug: $old_slug → $new_slug"
            echo "MIGRATED:${old_slug}→${new_slug}"
            return 0
        elif [[ -d "$new_dir" ]]; then
            _log_gate "MIGRATION" "WARN" "Migration skipped: target directory exists: $new_dir"
            echo "MIGRATION_SKIPPED:target_exists"
            return 0
        elif [[ ! -d "$old_dir" ]]; then
            _log_gate "MIGRATION" "WARN" "Migration skipped: source directory not found: $old_dir"
            echo "MIGRATION_SKIPPED:source_not_found"
            return 0
        fi

        echo "MIGRATION_SKIPPED:unknown_reason"
        return 0
    fi

    _log_gate "MIGRATION" "ERROR" "Unknown slug format: $old_slug"
    echo "UNKNOWN_FORMAT:$old_slug"
    return 1
}

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Compute and store hash for current phase artifact
# Usage: compute_and_store_hash "clarify" "/path/to/clarify.yaml"
compute_and_store_hash() {
    local phase="$1"
    local artifact_path="$2"

    if [[ ! -f "$artifact_path" ]]; then
        echo "ERROR: Artifact file not found: $artifact_path" >&2
        return 1
    fi

    local hash
    hash=$(sha256sum "$artifact_path" | cut -d' ' -f1)

    store_workload_hash "$hash" "$phase"
}

# Check if workload is ready for a specific phase
# Usage: check_phase_ready "research" (checks if clarify is complete)
check_phase_ready() {
    local target_phase="$1"

    case "$target_phase" in
        research)
            verify_upstream_hash "clarify"
            ;;
        planning)
            verify_upstream_hash "research"
            ;;
        orchestrate)
            verify_upstream_hash "planning"
            ;;
        worker)
            verify_upstream_hash "orchestrate"
            ;;
        *)
            echo "READY" # No upstream dependency
            return 0
            ;;
    esac
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f ensure_active_workload
export -f store_workload_hash
export -f verify_upstream_hash
export -f detect_workload_staleness
export -f migrate_legacy_slug
export -f compute_and_store_hash
export -f check_phase_ready

export WORKLOAD_INIT_VERSION
export WORKLOAD_TTL_HOURS
export WORKLOAD_STRICT_MODE

# ============================================================================
# SELF-TEST (Optional - for development)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Workload Init Self-Test (V${WORKLOAD_INIT_VERSION}) ==="
    echo ""

    # Test 1: ensure_active_workload create mode
    echo "Test 1: ensure_active_workload (create mode)"
    export TOPIC="test-self-test"
    result=$(ensure_active_workload "create")
    echo "  Result: $result"
    unset TOPIC
    echo ""

    # Test 2: ensure_active_workload inherit mode
    echo "Test 2: ensure_active_workload (inherit mode)"
    result=$(ensure_active_workload "inherit")
    echo "  Result: $result"
    echo ""

    # Test 3: ensure_active_workload require mode
    echo "Test 3: ensure_active_workload (require mode)"
    result=$(ensure_active_workload "require")
    echo "  Result: $result"
    echo ""

    # Test 4: detect_workload_staleness
    echo "Test 4: detect_workload_staleness"
    result=$(detect_workload_staleness)
    echo "  Result: $result"
    echo ""

    # Test 5: store_workload_hash
    echo "Test 5: store_workload_hash"
    result=$(store_workload_hash "abc123def456" "clarify")
    echo "  Result: $result"
    echo ""

    # Test 6: verify_upstream_hash (no artifact)
    echo "Test 6: verify_upstream_hash (clarify - may warn)"
    result=$(verify_upstream_hash "clarify" 2>&1)
    echo "  Result: $result"
    echo ""

    # Test 7: migrate_legacy_slug (already new format)
    echo "Test 7: migrate_legacy_slug (new format)"
    result=$(migrate_legacy_slug "test-feature-20260127-143000")
    echo "  Result: $result"
    echo ""

    # Test 8: migrate_legacy_slug (old format - no dir)
    echo "Test 8: migrate_legacy_slug (old format - no dir)"
    result=$(migrate_legacy_slug "test-feature-20260127")
    echo "  Result: $result"
    echo ""

    echo "=== All tests completed ==="
fi
