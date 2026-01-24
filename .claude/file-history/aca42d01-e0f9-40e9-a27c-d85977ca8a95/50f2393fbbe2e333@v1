#!/bin/bash
# =============================================================================
# ODA Setup Hook (V2.1.10 Setup Event)
# =============================================================================
#
# Purpose: Initialize workspace and verify system health on session start
# Event:   SessionStart (--init, --init-only, --maintenance flags)
# Config:  once: true - Prevents re-execution within same session
#
# Output Format (V2.1.9+):
#   JSON with hookSpecificOutput for additionalContext injection
#
# Exit Codes:
#   0: Always (setup hooks should never block session start)
#
# =============================================================================

set -e

# Configuration
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/home/palantir/park-kyungchan/palantir}"
AGENT_DIR="$WORKSPACE_ROOT/.agent"
DB_PATH="$AGENT_DIR/tmp/ontology.db"
MEMORY_PATH="$AGENT_DIR/memory/semantic"
LOG_DIR="$AGENT_DIR/logs"
OUTPUT_DIR="$AGENT_DIR/outputs"
PLANS_DIR="$AGENT_DIR/plans"
CONFIG_DIR="$AGENT_DIR/config"

# Track initialization results
INIT_RESULTS=()
WARNINGS=()
CREATED_DIRS=()

# =============================================================================
# Directory Creation
# =============================================================================

create_directories() {
    local dirs=(
        "$AGENT_DIR"
        "$AGENT_DIR/tmp"
        "$AGENT_DIR/logs"
        "$AGENT_DIR/memory"
        "$AGENT_DIR/memory/semantic"
        "$AGENT_DIR/memory/episodic"
        "$AGENT_DIR/outputs"
        "$AGENT_DIR/outputs/explore"
        "$AGENT_DIR/outputs/plan"
        "$AGENT_DIR/outputs/general"
        "$AGENT_DIR/plans"
        "$AGENT_DIR/config"
        "$AGENT_DIR/reports"
        "$AGENT_DIR/compact-state"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir" 2>/dev/null && CREATED_DIRS+=("$dir")
        fi
    done

    if [ ${#CREATED_DIRS[@]} -gt 0 ]; then
        INIT_RESULTS+=("Created ${#CREATED_DIRS[@]} directories")
    else
        INIT_RESULTS+=("All directories exist")
    fi
}

# =============================================================================
# Database Status Check
# =============================================================================

check_database() {
    if [ -f "$DB_PATH" ]; then
        local db_size
        db_size=$(du -h "$DB_PATH" 2>/dev/null | cut -f1)
        INIT_RESULTS+=("Database: OK ($db_size)")
    else
        WARNINGS+=("Database not found at $DB_PATH")
        INIT_RESULTS+=("Database: Not initialized")
    fi
}

# =============================================================================
# Agent Registry Check
# =============================================================================

check_agent_registry() {
    local registry_path="$CONFIG_DIR/agent_registry.yaml"
    if [ -f "$registry_path" ]; then
        INIT_RESULTS+=("Agent Registry: Found")
    else
        # Create default registry
        cat > "$registry_path" << 'YAML'
# Agent Registry for Resume across Auto-Compact
version: "1.0"
config:
  max_age_hours: 1
  max_entries: 50
  cleanup_on_load: true

agents: []
YAML
        INIT_RESULTS+=("Agent Registry: Created default")
    fi
}

# =============================================================================
# Plan Files Check
# =============================================================================

check_plan_files() {
    local active_plans=0
    if [ -d "$PLANS_DIR" ]; then
        active_plans=$(find "$PLANS_DIR" -name "*.md" -type f 2>/dev/null | wc -l)
    fi

    if [ "$active_plans" -gt 0 ]; then
        INIT_RESULTS+=("Active Plans: $active_plans")
        # Check for IN_PROGRESS plans
        local in_progress
        in_progress=$(grep -l "IN_PROGRESS" "$PLANS_DIR"/*.md 2>/dev/null | wc -l)
        if [ "$in_progress" -gt 0 ]; then
            WARNINGS+=("$in_progress plan(s) in IN_PROGRESS state - may need /recover")
        fi
    else
        INIT_RESULTS+=("Active Plans: None")
    fi
}

# =============================================================================
# Recovery State Check
# =============================================================================

check_recovery_state() {
    local recovery_file="$AGENT_DIR/recovery-state.json"
    if [ -f "$recovery_file" ]; then
        local recovery_needed
        recovery_needed=$(python3 -c "import json; print(json.load(open('$recovery_file')).get('recovery_needed', False))" 2>/dev/null || echo "false")
        if [ "$recovery_needed" = "True" ]; then
            WARNINGS+=("Recovery state indicates context loss - run /recover")
        fi
    fi
}

# =============================================================================
# Build Output
# =============================================================================

build_output() {
    local status="healthy"
    [ ${#WARNINGS[@]} -gt 0 ] && status="warnings"

    # Build additionalContext
    local context="## ODA Workspace Initialized\n\n"
    context+="**Status:** $status\n"
    context+="**Workspace:** $WORKSPACE_ROOT\n\n"

    context+="### Initialization Results\n"
    for result in "${INIT_RESULTS[@]}"; do
        context+="- $result\n"
    done

    if [ ${#WARNINGS[@]} -gt 0 ]; then
        context+="\n### Warnings\n"
        for warning in "${WARNINGS[@]}"; do
            context+="- ⚠️ $warning\n"
        done
    fi

    if [ ${#CREATED_DIRS[@]} -gt 0 ]; then
        context+="\n### Newly Created Directories\n"
        for dir in "${CREATED_DIRS[@]}"; do
            context+="- \`$dir\`\n"
        done
    fi

    context+="\n### Quick Commands\n"
    context+="- \`/recover\` - Restore context after Auto-Compact\n"
    context+="- \`/init\` - Full workspace initialization\n"
    context+="- \`/audit\` - Run code quality audit\n"

    # Output JSON with hookSpecificOutput (V2.1.9+)
    python3 << PYEOF
import json

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": """$context"""
    }
}

print(json.dumps(output))
PYEOF
}

# =============================================================================
# Main
# =============================================================================

main() {
    # Always succeed - setup hooks should never block session start
    trap 'echo "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"Setup hook encountered an error but session continues.\"}}"' ERR

    create_directories
    check_database
    check_agent_registry
    check_plan_files
    check_recovery_state

    build_output
}

main "$@"

exit 0
