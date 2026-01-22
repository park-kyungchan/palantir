#!/usr/bin/env python3
"""
{HOOK_NAME} - {HOOK_EVENT}

File: .claude/hooks/{PATH}/{NAME}.py
Version: 1.0.0
Trigger: {HOOK_EVENT} on {MATCHER}

Purpose:
    {HOOK_DESCRIPTION}

Event Types:
    PreToolUse     - Before tool execution (can modify, block)
    PostToolUse    - After tool execution (can block)
    PermissionRequest - Auto-approve/deny permissions
    UserPromptSubmit  - Pre-process user input
    SessionStart   - Session initialization
    SessionEnd     - Session cleanup
    SubagentStop   - Control subagent termination
    Stop           - Prevent session end
    PreCompact     - Before context compaction
    Setup          - Environment setup
    Notification   - Log notifications

Native Capabilities (PreToolUse/PostToolUse):
    updatedInput      - Modify tool parameters
    additionalContext - Inject context to Claude
    permissionDecision - allow | deny | ask
"""

import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional


# ============================================
# Input Data Structure
# ============================================

class HookInput:
    """Parsed hook input data."""

    def __init__(self, data: Dict[str, Any]):
        self.raw = data
        self.session_id = data.get("session_id", "")
        self.tool_name = data.get("tool_name", "")
        self.tool_input = data.get("tool_input", {})
        self.tool_use_id = data.get("tool_use_id", "")
        self.transcript_path = data.get("transcript_path", "")
        self.cwd = data.get("cwd", "")
        self.permission_mode = data.get("permission_mode", "")

        # PostToolUse specific
        self.tool_result = data.get("tool_result", None)


# ============================================
# Response Builder
# ============================================

class HookResponse:
    """Build hook response with native capabilities."""

    def __init__(self):
        self.permission_decision: str = "allow"
        self.reason: Optional[str] = None
        self.updated_input: Optional[Dict[str, Any]] = None
        self.additional_context: Optional[str] = None
        self.decision: Optional[str] = None  # For PostToolUse: "block"
        self.continue_execution: Optional[bool] = None
        self.stop_reason: Optional[str] = None
        self.suppress_output: Optional[bool] = None
        self.system_message: Optional[str] = None

    def allow(self) -> "HookResponse":
        """Allow the operation."""
        self.permission_decision = "allow"
        return self

    def deny(self, reason: str = "") -> "HookResponse":
        """Deny the operation."""
        self.permission_decision = "deny"
        self.reason = reason
        return self

    def ask(self) -> "HookResponse":
        """Ask user for permission."""
        self.permission_decision = "ask"
        return self

    def with_updated_input(self, updates: Dict[str, Any]) -> "HookResponse":
        """Modify tool parameters via updatedInput."""
        self.updated_input = updates
        return self

    def with_context(self, context: str) -> "HookResponse":
        """Inject additionalContext to Claude."""
        self.additional_context = context
        return self

    def block(self, reason: str = "") -> "HookResponse":
        """Block execution (PostToolUse, Stop, SubagentStop)."""
        self.decision = "block"
        self.stop_reason = reason
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        hook_output: Dict[str, Any] = {}

        if self.permission_decision:
            hook_output["permissionDecision"] = self.permission_decision

        if self.reason:
            hook_output["reason"] = self.reason

        if self.updated_input is not None:
            hook_output["updatedInput"] = self.updated_input

        if self.additional_context is not None:
            hook_output["additionalContext"] = self.additional_context

        if self.decision:
            hook_output["decision"] = self.decision

        result: Dict[str, Any] = {
            "hookSpecificOutput": hook_output
        }

        if self.continue_execution is not None:
            result["continue"] = self.continue_execution

        if self.stop_reason:
            result["stopReason"] = self.stop_reason

        if self.suppress_output is not None:
            result["suppressOutput"] = self.suppress_output

        if self.system_message:
            result["systemMessage"] = self.system_message

        return result

    def output(self) -> None:
        """Print response to stdout."""
        print(json.dumps(self.to_dict()))


# ============================================
# Logging Helper
# ============================================

def log(message: str, log_path: str = ".agent/logs/hook.log") -> None:
    """Append message to log file."""
    try:
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(f"{message}\n")
    except Exception:
        pass  # Silent fail for logging


# ============================================
# Main Hook Logic
# ============================================

def process_hook(hook_input: HookInput) -> HookResponse:
    """
    TODO(human): Implement hook logic here.

    Args:
        hook_input: Parsed input from Claude Code

    Returns:
        HookResponse with appropriate action
    """
    response = HookResponse()

    # Example: Check tool name pattern
    # if hook_input.tool_name in ("Bash", "Edit", "Write"):
    #     # Perform validation
    #     pass

    # Example: Modify tool input
    # if hook_input.tool_name == "Task":
    #     updated = dict(hook_input.tool_input)
    #     updated["run_in_background"] = True
    #     response.with_updated_input(updated)

    # Example: Inject context
    # context = "Additional information for Claude"
    # response.with_context(context)

    # Example: Deny dangerous operations
    # if "rm -rf" in str(hook_input.tool_input.get("command", "")):
    #     return response.deny("Dangerous operation blocked")

    # Default: allow
    return response.allow()


def main() -> None:
    """Entry point."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        hook_input = HookInput(input_data)

        # Process and respond
        response = process_hook(hook_input)
        response.output()

    except json.JSONDecodeError as e:
        # Invalid JSON input
        error_response = HookResponse()
        error_response.allow()  # Fail-safe: allow on error
        error_response.output()
        log(f"JSON decode error: {e}")

    except Exception as e:
        # Unexpected error
        error_response = HookResponse()
        error_response.allow()  # Fail-safe: allow on error
        error_response.output()
        log(f"Hook error: {e}")


if __name__ == "__main__":
    main()
