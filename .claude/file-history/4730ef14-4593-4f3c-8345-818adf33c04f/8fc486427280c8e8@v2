#!/bin/bash
# =============================================================================
# Orion ODA - Auto-Format Hook
# =============================================================================
# Boris Cherny Pattern 10: PostToolUse Hooks
#
# Automatically formats code after Edit/Write operations.
# Supports: Python (black), JavaScript/TypeScript (prettier), JSON (prettier)
#
# Hook Type: PostToolUse
# Matcher: Edit|Write
# Triggers: After file modifications
#
# Environment Variables (from Claude Code):
#   CLAUDE_TOOL_NAME - Name of the tool (Edit or Write)
#   CLAUDE_TOOL_INPUT - JSON input with file_path
#   CLAUDE_TOOL_OUTPUT - JSON output from tool
#   CLAUDE_SESSION_ID - Current session ID
#
# Exit Codes:
#   0 - Success (formatting applied or skipped)
#   Non-zero - Error (but non-blocking)
# =============================================================================

# Non-blocking - don't fail the tool call if formatting fails
set +e

# Configuration
WORKSPACE_ROOT="${ORION_WORKSPACE_ROOT:-/home/palantir}"
CONFIG_FILE="$WORKSPACE_ROOT/.claude/hooks/.format-config.json"
FORMAT_LOG="$WORKSPACE_ROOT/park-kyungchan/palantir/.agent/tmp/format_operations.jsonl"

# Default settings (if no config file)
AUTO_FORMAT_ENABLED="${ODA_AUTO_FORMAT:-false}"
LOG_FORMATTING="${ODA_LOG_FORMATTING:-true}"

# Parse environment
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-{}}"
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Ensure log directory exists
mkdir -p "$(dirname "$FORMAT_LOG")" 2>/dev/null || true

# Load config if exists
if [ -f "$CONFIG_FILE" ]; then
    if command -v jq &> /dev/null; then
        AUTO_FORMAT_ENABLED=$(jq -r '.auto_format_enabled // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
        LOG_FORMATTING=$(jq -r '.log_formatting_operations // true' "$CONFIG_FILE" 2>/dev/null || echo "true")
    fi
fi

# Exit early if auto-format is disabled
if [ "$AUTO_FORMAT_ENABLED" != "true" ]; then
    echo '{"status":"skipped","reason":"auto_format_disabled"}'
    exit 0
fi

# Only process Edit and Write tools
if [ "$TOOL_NAME" != "Edit" ] && [ "$TOOL_NAME" != "Write" ]; then
    echo '{"status":"skipped","reason":"not_edit_or_write"}'
    exit 0
fi

# Extract file path from tool input
FILE_PATH=""
if command -v jq &> /dev/null; then
    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // ""' 2>/dev/null)
else
    # Fallback: simple grep extraction
    FILE_PATH=$(echo "$TOOL_INPUT" | grep -oP '"file_path"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
fi

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    echo '{"status":"skipped","reason":"file_not_found"}'
    exit 0
fi

# Determine file type and formatter
get_formatter() {
    local file="$1"
    local ext="${file##*.}"

    case "$ext" in
        py)
            # Python: use black
            if command -v black &> /dev/null; then
                echo "black"
            elif command -v autopep8 &> /dev/null; then
                echo "autopep8"
            else
                echo ""
            fi
            ;;
        js|jsx|ts|tsx|json|md|yaml|yml|css|scss|html)
            # JavaScript/TypeScript/JSON/Markdown: use prettier
            if command -v prettier &> /dev/null; then
                echo "prettier"
            else
                echo ""
            fi
            ;;
        *)
            echo ""
            ;;
    esac
}

# Format the file
format_file() {
    local file="$1"
    local formatter="$2"
    local result=""
    local exit_code=0

    case "$formatter" in
        black)
            result=$(black --quiet "$file" 2>&1)
            exit_code=$?
            ;;
        autopep8)
            result=$(autopep8 --in-place "$file" 2>&1)
            exit_code=$?
            ;;
        prettier)
            result=$(prettier --write "$file" 2>&1)
            exit_code=$?
            ;;
    esac

    echo "$exit_code"
}

# Check exclusion patterns
is_excluded() {
    local file="$1"

    # Default exclusions
    local exclusions=(
        "*.min.js"
        "*.min.css"
        "dist/*"
        "build/*"
        "node_modules/*"
        ".venv/*"
        "__pycache__/*"
        "*.pyc"
    )

    # Load custom exclusions from config
    if [ -f "$CONFIG_FILE" ] && command -v jq &> /dev/null; then
        local custom_exclusions
        custom_exclusions=$(jq -r '.exclude_patterns[]? // empty' "$CONFIG_FILE" 2>/dev/null)
        if [ -n "$custom_exclusions" ]; then
            while IFS= read -r pattern; do
                exclusions+=("$pattern")
            done <<< "$custom_exclusions"
        fi
    fi

    # Check against exclusion patterns
    for pattern in "${exclusions[@]}"; do
        if [[ "$file" == $pattern ]]; then
            return 0  # excluded
        fi
    done

    return 1  # not excluded
}

# Main formatting logic
FORMATTER=$(get_formatter "$FILE_PATH")
FORMAT_STATUS="skipped"
FORMAT_EXIT_CODE=0
FORMAT_REASON=""

if [ -z "$FORMATTER" ]; then
    FORMAT_REASON="no_formatter_available"
elif is_excluded "$FILE_PATH"; then
    FORMAT_REASON="file_excluded"
else
    # Perform formatting
    FORMAT_EXIT_CODE=$(format_file "$FILE_PATH" "$FORMATTER")

    if [ "$FORMAT_EXIT_CODE" -eq 0 ]; then
        FORMAT_STATUS="formatted"
        FORMAT_REASON="success"
    else
        FORMAT_STATUS="error"
        FORMAT_REASON="formatter_failed"
    fi
fi

# Log formatting operation
if [ "$LOG_FORMATTING" = "true" ]; then
    # Get file extension for logging
    FILE_EXT="${FILE_PATH##*.}"

    LOG_ENTRY="{\"timestamp\":\"$TIMESTAMP\",\"session_id\":\"$SESSION_ID\",\"tool\":\"$TOOL_NAME\",\"file_path\":\"$FILE_PATH\",\"extension\":\"$FILE_EXT\",\"formatter\":\"${FORMATTER:-none}\",\"status\":\"$FORMAT_STATUS\",\"exit_code\":$FORMAT_EXIT_CODE}"
    echo "$LOG_ENTRY" >> "$FORMAT_LOG"
fi

# Output result
echo "{\"status\":\"$FORMAT_STATUS\",\"file\":\"$FILE_PATH\",\"formatter\":\"${FORMATTER:-none}\",\"reason\":\"$FORMAT_REASON\"}"

exit 0
