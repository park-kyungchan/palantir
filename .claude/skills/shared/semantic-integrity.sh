#!/usr/bin/env bash
# =============================================================================
# Semantic Integrity Module (V1.0.0)
# =============================================================================
# Purpose: SHA256 hash calculation, verification, and manifest generation
#          for pipeline artifact integrity tracking
# Usage: source /home/palantir/.claude/skills/shared/semantic-integrity.sh
# =============================================================================
#
# FUNCTIONS:
# - compute_artifact_hash()      - SHA256 hash of file or content
# - generate_worker_manifest()   - Create completion manifest with hashes
# - verify_artifact_integrity()  - Check artifact against stored hash
# - verify_upstream_chain()      - Validate entire pipeline chain
# - get_upstream_hash()          - Retrieve hash from upstream artifact
#
# PIPELINE CHAIN:
#   /clarify → /research → /planning → /orchestrate → /worker
#   Each phase stores hash of its output + reference to upstream hash
#
# =============================================================================

set -euo pipefail

# ============================================================================
# CONSTANTS
# ============================================================================
MODULE_VERSION="1.0.0"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(pwd)}"
INTEGRITY_LOG="${WORKSPACE_ROOT}/.agent/logs/integrity.log"

# Pipeline phase order for chain validation
declare -a PIPELINE_PHASES=("clarify" "research" "planning" "orchestrate" "worker")

# Ensure log directory exists
mkdir -p "$(dirname "$INTEGRITY_LOG")" 2>/dev/null

# ============================================================================
# LOGGING
# ============================================================================

log_integrity() {
    local level="$1"
    local component="$2"
    local message="$3"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    echo "[${timestamp}] [${level}] [INTEGRITY:${component}] ${message}" >> "$INTEGRITY_LOG"
}

# ============================================================================
# compute_artifact_hash()
# =============================================================================
# Compute SHA256 hash of an artifact (file or content)
#
# Args:
#   $1 - artifact_path: Path to artifact file
#   $2 - hash_mode: "full" (default) | "content_only" | "metadata_stripped"
#
# Output:
#   SHA256 hash string (64 hex characters)
#
# Modes:
#   full           - Hash entire file content
#   content_only   - For YAML: hash content excluding metadata section
#   metadata_stripped - Strip timestamps/generated fields before hashing
# =============================================================================
compute_artifact_hash() {
    local artifact_path="$1"
    local hash_mode="${2:-full}"

    log_integrity "INFO" "HASH" "Computing hash for: ${artifact_path} (mode: ${hash_mode})"

    # Validate file exists
    if [[ ! -f "$artifact_path" ]]; then
        log_integrity "ERROR" "HASH" "Artifact not found: ${artifact_path}"
        echo "ERROR:FILE_NOT_FOUND"
        return 1
    fi

    local hash_value=""

    case "$hash_mode" in
        "full")
            # Hash entire file
            hash_value=$(sha256sum "$artifact_path" | cut -d' ' -f1)
            ;;

        "content_only")
            # For YAML files: exclude metadata section
            if [[ "$artifact_path" == *.yaml || "$artifact_path" == *.yml ]]; then
                if command -v yq &>/dev/null; then
                    # Extract non-metadata content and hash
                    hash_value=$(yq 'del(.metadata) | del(.pipeline)' "$artifact_path" 2>/dev/null | sha256sum | cut -d' ' -f1)
                else
                    # Fallback: strip lines starting with metadata:
                    hash_value=$(grep -v '^\s*metadata:' "$artifact_path" | grep -v '^\s*pipeline:' | sha256sum | cut -d' ' -f1)
                fi
            else
                # Non-YAML: use full hash
                hash_value=$(sha256sum "$artifact_path" | cut -d' ' -f1)
            fi
            ;;

        "metadata_stripped")
            # Strip timestamps and auto-generated fields
            hash_value=$(sed -E \
                -e 's/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?/TIMESTAMP/g' \
                -e 's/updated_at:.*/updated_at: STRIPPED/g' \
                -e 's/created_at:.*/created_at: STRIPPED/g' \
                -e 's/generated_at:.*/generated_at: STRIPPED/g' \
                "$artifact_path" | sha256sum | cut -d' ' -f1)
            ;;

        *)
            log_integrity "WARN" "HASH" "Unknown hash mode: ${hash_mode}, using full"
            hash_value=$(sha256sum "$artifact_path" | cut -d' ' -f1)
            ;;
    esac

    log_integrity "INFO" "HASH" "Computed hash: ${hash_value:0:16}..."
    echo "$hash_value"
}

# ============================================================================
# generate_worker_manifest()
# =============================================================================
# Generate completion manifest for worker task with integrity hashes
#
# Args:
#   $1 - task_id: Native Task ID
#   $2 - worker_id: Worker identifier (terminal-b, etc.)
#   $3 - output_files: Comma-separated list of output file paths
#   $4 - upstream_phase: Phase this worker depends on (e.g., "orchestrate")
#   $5 - upstream_artifact: Path to upstream artifact for chain reference
#
# Output:
#   YAML manifest written to workload output directory
#   Returns manifest path
# =============================================================================
generate_worker_manifest() {
    local task_id="$1"
    local worker_id="$2"
    local output_files="$3"
    local upstream_phase="${4:-orchestrate}"
    local upstream_artifact="${5:-}"

    log_integrity "INFO" "MANIFEST" "Generating manifest for task ${task_id}, worker ${worker_id}"

    # Get workload slug for output path
    local workload_slug=""
    if [[ -f "${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml" ]]; then
        workload_slug=$(yq '.active_workload // ""' "${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml" 2>/dev/null || echo "")
    fi

    # Determine output directory
    local manifest_dir
    if [[ -n "$workload_slug" ]]; then
        manifest_dir="${WORKSPACE_ROOT}/.agent/prompts/${workload_slug}/outputs/${worker_id}"
    else
        manifest_dir="${WORKSPACE_ROOT}/.agent/outputs/${worker_id}"
    fi
    mkdir -p "$manifest_dir"

    local manifest_path="${manifest_dir}/task-${task_id}-manifest.yaml"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Compute upstream hash if artifact provided
    local upstream_hash="null"
    if [[ -n "$upstream_artifact" && -f "$upstream_artifact" ]]; then
        upstream_hash="\"$(compute_artifact_hash "$upstream_artifact" "content_only")\""
    fi

    # Start manifest
    cat > "$manifest_path" << EOF
# Worker Completion Manifest
# Generated: ${timestamp}
# Schema Version: ${MODULE_VERSION}

metadata:
  task_id: "${task_id}"
  worker_id: "${worker_id}"
  generated_at: "${timestamp}"
  schema_version: "${MODULE_VERSION}"

upstream:
  phase: "${upstream_phase}"
  artifact: "${upstream_artifact:-null}"
  hash: ${upstream_hash}

outputs:
EOF

    # Add output files with hashes
    IFS=',' read -ra files_array <<< "$output_files"
    for file_path in "${files_array[@]}"; do
        file_path=$(echo "$file_path" | xargs)  # trim whitespace
        [[ -z "$file_path" ]] && continue

        local file_hash="null"
        local file_size="0"
        local file_exists="false"

        if [[ -f "$file_path" ]]; then
            file_hash=$(compute_artifact_hash "$file_path" "full")
            file_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "0")
            file_exists="true"
        fi

        cat >> "$manifest_path" << EOF
  - path: "${file_path}"
    exists: ${file_exists}
    hash: "${file_hash}"
    size: ${file_size}
EOF
    done

    # Add chain reference
    cat >> "$manifest_path" << EOF

integrity:
  manifest_hash: null  # Will be computed after manifest is complete
  chain_valid: null    # Set by verify_upstream_chain
EOF

    # Compute manifest's own hash (excluding the hash field itself)
    local manifest_content_hash
    manifest_content_hash=$(grep -v 'manifest_hash:' "$manifest_path" | sha256sum | cut -d' ' -f1)

    # Update manifest_hash in file (use sed for compatibility - yq not always available)
    sed -i "s/manifest_hash: null.*$/manifest_hash: \"${manifest_content_hash}\"/" "$manifest_path"

    log_integrity "INFO" "MANIFEST" "Generated manifest: ${manifest_path}"
    echo "$manifest_path"
}

# ============================================================================
# verify_artifact_integrity()
# =============================================================================
# Verify artifact against stored/expected hash
#
# Args:
#   $1 - artifact_path: Path to artifact to verify
#   $2 - expected_hash: Expected SHA256 hash
#   $3 - hash_mode: "full" | "content_only" | "metadata_stripped" (default: full)
#
# Output:
#   JSON: {"status": "VERIFIED|TAMPERED|MISSING", "current_hash": "...", "expected_hash": "..."}
# =============================================================================
verify_artifact_integrity() {
    local artifact_path="$1"
    local expected_hash="$2"
    local hash_mode="${3:-full}"

    log_integrity "INFO" "VERIFY" "Verifying: ${artifact_path}"

    local status="MISSING"
    local current_hash="null"

    if [[ -f "$artifact_path" ]]; then
        current_hash=$(compute_artifact_hash "$artifact_path" "$hash_mode")

        if [[ "$current_hash" == "$expected_hash" ]]; then
            status="VERIFIED"
            log_integrity "INFO" "VERIFY" "VERIFIED: ${artifact_path}"
        else
            status="TAMPERED"
            log_integrity "WARN" "VERIFY" "TAMPERED: ${artifact_path} (expected: ${expected_hash:0:16}..., got: ${current_hash:0:16}...)"
        fi
    else
        log_integrity "WARN" "VERIFY" "MISSING: ${artifact_path}"
    fi

    # Return JSON result
    jq -n \
        --arg status "$status" \
        --arg current_hash "$current_hash" \
        --arg expected_hash "$expected_hash" \
        --arg artifact "$artifact_path" \
        --arg hash_mode "$hash_mode" \
        '{
            status: $status,
            artifact: $artifact,
            current_hash: $current_hash,
            expected_hash: $expected_hash,
            hash_mode: $hash_mode
        }'
}

# ============================================================================
# get_upstream_hash()
# =============================================================================
# Retrieve hash from upstream pipeline artifact
#
# Args:
#   $1 - upstream_artifact: Path to upstream artifact (YAML with hash field)
#   $2 - hash_field: Field path to hash (default: ".pipeline.context_hash" or ".integrity.manifest_hash")
#
# Output:
#   Hash string or "null" if not found
# =============================================================================
get_upstream_hash() {
    local upstream_artifact="$1"
    local hash_field="${2:-}"

    log_integrity "INFO" "UPSTREAM" "Getting hash from: ${upstream_artifact}"

    if [[ ! -f "$upstream_artifact" ]]; then
        log_integrity "WARN" "UPSTREAM" "Upstream artifact not found: ${upstream_artifact}"
        echo "null"
        return 1
    fi

    # Try common hash field locations
    local hash_value="null"

    if command -v yq &>/dev/null; then
        if [[ -n "$hash_field" ]]; then
            hash_value=$(yq "${hash_field}" "$upstream_artifact" 2>/dev/null || echo "null")
        else
            # Try common locations in order
            for field in ".pipeline.context_hash" ".integrity.manifest_hash" ".metadata.hash" ".hash"; do
                hash_value=$(yq "${field}" "$upstream_artifact" 2>/dev/null || echo "null")
                if [[ "$hash_value" != "null" && -n "$hash_value" ]]; then
                    break
                fi
            done
        fi
    else
        # Fallback: parse YAML manually using grep/sed
        # Extract the key from field path (e.g., ".pipeline.context_hash" -> "context_hash")
        local key_to_find=""
        if [[ -n "$hash_field" ]]; then
            key_to_find=$(echo "$hash_field" | sed 's/.*\.//')
        fi

        if [[ -n "$key_to_find" ]]; then
            # Look for the specific key
            hash_value=$(grep -E "^\s*${key_to_find}:" "$upstream_artifact" 2>/dev/null | \
                         sed -E 's/.*:\s*"?([a-f0-9]{64}|[a-zA-Z0-9_-]+)"?.*/\1/' | \
                         head -1 || echo "null")
        fi

        # If not found or empty, try common hash patterns
        if [[ -z "$hash_value" || "$hash_value" == "null" ]]; then
            for key in "context_hash" "manifest_hash" "hash"; do
                hash_value=$(grep -E "^\s*${key}:" "$upstream_artifact" 2>/dev/null | \
                             sed -E 's/.*:\s*"?([a-f0-9]{64}|[a-zA-Z0-9_-]+)"?.*/\1/' | \
                             head -1 || echo "")
                if [[ -n "$hash_value" && "$hash_value" != "null" ]]; then
                    break
                fi
            done
        fi

        # Final fallback: look for any 64-char hex string labeled as hash
        if [[ -z "$hash_value" || "$hash_value" == "null" ]]; then
            hash_value=$(grep -oE '[a-f0-9]{64}' "$upstream_artifact" | head -1 || echo "null")
        fi
    fi

    # Clean up null/empty output
    hash_value=$(echo "$hash_value" | tr -d '"' | xargs)
    if [[ -z "$hash_value" || "$hash_value" == "null" ]]; then
        log_integrity "WARN" "UPSTREAM" "No hash found in: ${upstream_artifact}"
        echo "null"
        return 1
    fi

    log_integrity "INFO" "UPSTREAM" "Found hash: ${hash_value:0:16}..."
    echo "$hash_value"
}

# ============================================================================
# verify_upstream_chain()
# =============================================================================
# Validate entire pipeline chain integrity
#
# Args:
#   $1 - workload_slug: Workload directory slug
#   $2 - target_phase: Phase to validate up to (default: "worker")
#
# Output:
#   JSON: {
#     "valid": true/false,
#     "chain": [{"phase": "...", "status": "VERIFIED|TAMPERED|MISSING", "hash": "..."}],
#     "break_point": "phase_name or null"
#   }
# =============================================================================
verify_upstream_chain() {
    local workload_slug="$1"
    local target_phase="${2:-worker}"

    log_integrity "INFO" "CHAIN" "Verifying chain for workload: ${workload_slug}, up to: ${target_phase}"

    local workload_dir="${WORKSPACE_ROOT}/.agent/prompts/${workload_slug}"

    if [[ ! -d "$workload_dir" ]]; then
        log_integrity "ERROR" "CHAIN" "Workload directory not found: ${workload_dir}"
        echo '{"valid": false, "chain": [], "break_point": "workload_not_found", "error": "Workload directory not found"}'
        return 1
    fi

    # Build chain validation result
    local chain_json="[]"
    local chain_valid=true
    local break_point="null"
    local previous_hash="null"

    for phase in "${PIPELINE_PHASES[@]}"; do
        # Determine artifact path for this phase
        local artifact_path=""
        local hash_field=""

        case "$phase" in
            "clarify")
                artifact_path="${workload_dir}/clarify.yaml"
                hash_field=".pipeline.context_hash"
                ;;
            "research")
                artifact_path="${workload_dir}/research.md"
                # research.md may not have embedded hash - compute fresh
                ;;
            "planning")
                artifact_path="${workload_dir}/plan.yaml"
                hash_field=".metadata.hash"
                ;;
            "orchestrate")
                artifact_path="${workload_dir}/_context.yaml"
                hash_field=".metadata.integrity_hash"
                ;;
            "worker")
                # Worker phase has multiple manifests - check all in outputs/
                artifact_path="${workload_dir}/outputs"
                ;;
        esac

        local phase_status="MISSING"
        local phase_hash="null"
        local upstream_valid=true

        if [[ "$phase" == "worker" ]]; then
            # Worker phase: check all worker manifests
            if [[ -d "$artifact_path" ]]; then
                local all_manifests_valid=true
                for manifest in "${artifact_path}"/*/task-*-manifest.yaml; do
                    [[ ! -f "$manifest" ]] && continue

                    local manifest_hash
                    manifest_hash=$(get_upstream_hash "$manifest" ".integrity.manifest_hash")

                    if [[ "$manifest_hash" != "null" ]]; then
                        # Verify manifest integrity
                        local computed_hash
                        computed_hash=$(grep -v 'manifest_hash:' "$manifest" | sha256sum | cut -d' ' -f1)

                        if [[ "$computed_hash" != "$manifest_hash" ]]; then
                            all_manifests_valid=false
                        fi
                    fi
                done

                if $all_manifests_valid; then
                    phase_status="VERIFIED"
                else
                    phase_status="TAMPERED"
                fi
            fi
        elif [[ -f "$artifact_path" ]]; then
            phase_hash=$(compute_artifact_hash "$artifact_path" "content_only")

            # Check if artifact has stored hash
            if [[ -n "$hash_field" ]]; then
                local stored_hash
                stored_hash=$(get_upstream_hash "$artifact_path" "$hash_field")

                if [[ "$stored_hash" != "null" && "$stored_hash" == "$phase_hash" ]]; then
                    phase_status="VERIFIED"
                elif [[ "$stored_hash" != "null" ]]; then
                    phase_status="TAMPERED"
                else
                    phase_status="VERIFIED"  # No stored hash, but file exists
                fi
            else
                phase_status="VERIFIED"  # File exists, no embedded hash to check
            fi

            # Verify upstream reference (if not first phase)
            if [[ "$previous_hash" != "null" && "$phase" != "clarify" ]]; then
                local upstream_ref
                upstream_ref=$(get_upstream_hash "$artifact_path" ".upstream.hash" 2>/dev/null || echo "null")

                if [[ "$upstream_ref" != "null" && "$upstream_ref" != "$previous_hash" ]]; then
                    upstream_valid=false
                    phase_status="CHAIN_BREAK"
                fi
            fi
        fi

        # Add to chain
        chain_json=$(echo "$chain_json" | jq \
            --arg phase "$phase" \
            --arg status "$phase_status" \
            --arg hash "$phase_hash" \
            --argjson upstream_valid "$upstream_valid" \
            '. += [{"phase": $phase, "status": $status, "hash": $hash, "upstream_valid": $upstream_valid}]')

        # Track chain validity
        if [[ "$phase_status" != "VERIFIED" ]]; then
            chain_valid=false
            if [[ "$break_point" == "null" ]]; then
                break_point="\"$phase\""
            fi
        fi

        # Update previous hash for chain tracking
        previous_hash="$phase_hash"

        # Stop at target phase
        if [[ "$phase" == "$target_phase" ]]; then
            break
        fi
    done

    log_integrity "INFO" "CHAIN" "Chain validation complete: valid=${chain_valid}"

    # Return result
    jq -n \
        --argjson valid "$chain_valid" \
        --argjson chain "$chain_json" \
        --argjson break_point "$break_point" \
        '{
            valid: $valid,
            chain: $chain,
            break_point: $break_point
        }'
}

# ============================================================================
# UTILITY: Quick Integrity Check for Current Workload
# ============================================================================

quick_integrity_check() {
    log_integrity "INFO" "QUICK" "Running quick integrity check"

    # Get active workload
    local active_workload=""
    if [[ -f "${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml" ]]; then
        active_workload=$(yq '.active_workload // ""' "${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml" 2>/dev/null || echo "")
    fi

    if [[ -z "$active_workload" ]]; then
        echo '{"status": "no_active_workload", "message": "No active workload found"}'
        return 1
    fi

    verify_upstream_chain "$active_workload"
}

# ============================================================================
# EXPORTS
# ============================================================================
export -f compute_artifact_hash
export -f generate_worker_manifest
export -f verify_artifact_integrity
export -f verify_upstream_chain
export -f get_upstream_hash
export -f quick_integrity_check
export -f log_integrity

# ============================================================================
# SELF-TEST (if run directly)
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "=== Semantic Integrity Module Self-Test ==="
    echo "Version: ${MODULE_VERSION}"
    echo ""

    # Test 1: compute_artifact_hash
    echo "Test 1: compute_artifact_hash"
    test_file=$(mktemp)
    echo "test content for hashing" > "$test_file"
    hash_result=$(compute_artifact_hash "$test_file" "full")
    echo "  Hash: ${hash_result:0:32}..."
    rm -f "$test_file"

    # Test 2: verify_artifact_integrity
    echo ""
    echo "Test 2: verify_artifact_integrity"
    test_file=$(mktemp)
    echo "verify me" > "$test_file"
    expected_hash=$(sha256sum "$test_file" | cut -d' ' -f1)
    verify_result=$(verify_artifact_integrity "$test_file" "$expected_hash" "full")
    echo "  Result: $(echo "$verify_result" | jq -r '.status')"
    rm -f "$test_file"

    # Test 3: Missing file verification
    echo ""
    echo "Test 3: Missing file verification"
    missing_result=$(verify_artifact_integrity "/nonexistent/file.yaml" "abc123" "full")
    echo "  Result: $(echo "$missing_result" | jq -r '.status')"

    echo ""
    echo "=== Self-test complete ==="
fi
