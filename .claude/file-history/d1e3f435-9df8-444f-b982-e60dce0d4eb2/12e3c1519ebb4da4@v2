#!/usr/bin/env python3
"""
============================================================================
Hook: {{hook_name}}
Event: {{event_type}}
Matcher: {{matcher}}
Created: {{timestamp}}
============================================================================

ENVIRONMENT VARIABLES:
    CC_HOOK_EVENT           - Event type (PreToolUse, PostToolUse, etc.)
    CC_TOOL_NAME            - Tool name (Bash, Read, Edit, etc.)
    CC_TOOL_INPUT           - Tool input as JSON string
    CC_TOOL_OUTPUT          - Tool output as JSON (PostToolUse only)
    CC_WORKING_DIRECTORY    - Current working directory

EXIT CODES:
    0 = Allow / Success
    1 = Block (PreToolUse only)
    2 = Error

============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

HOOK_NAME = "{{hook_name}}"
LOG_DIR = Path(os.environ.get("CC_WORKING_DIRECTORY", ".")) / ".agent" / "logs"
LOG_FILE = LOG_DIR / f"{HOOK_NAME}.log"

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configure logging to file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(HOOK_NAME)
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)

    return logger

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.environ.get(key, default)


def parse_json_env(key: str) -> dict[str, Any]:
    """Parse JSON from environment variable."""
    raw = get_env(key, "{}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def block(message: str, logger: logging.Logger) -> int:
    """Block execution with message."""
    print(f"❌ Blocked: {message}")
    logger.error(f"Blocked: {message}")
    return 1


def allow(logger: logging.Logger) -> int:
    """Allow execution."""
    logger.info("Allowed")
    return 0

# ============================================================================
# MAIN LOGIC
# ============================================================================

def main() -> int:
    """Main hook logic."""
    logger = setup_logging()

    # Parse environment
    event = get_env("CC_HOOK_EVENT")
    tool_name = get_env("CC_TOOL_NAME")
    tool_input = parse_json_env("CC_TOOL_INPUT")
    tool_output = parse_json_env("CC_TOOL_OUTPUT")  # PostToolUse only

    logger.info(f"Hook triggered: event={event}, tool={tool_name}")

    # TODO(human): Implement your hook logic here
    # Example validation:
    #
    # if tool_name == "Bash":
    #     command = tool_input.get("command", "")
    #     if "rm -rf" in command:
    #         return block("Dangerous command pattern: rm -rf", logger)
    #
    # Example logging:
    #
    # logger.info(f"Tool input: {json.dumps(tool_input)}")

    # Default: Allow
    return allow(logger)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())
