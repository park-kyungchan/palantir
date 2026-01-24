#!/usr/bin/env python3
"""
PostToolUse Hook: Output Preservation
=====================================

Enforces Output Preservation by detecting summary-only results.

Trigger: Task tool completion
Matcher: Task
Exit Codes:
    0 - Success (with JSON output)

Action:
    1. Detect if result is summary-only (using is_summary_only())
    2. If summary: Write L2 file + inject guidance for Main Agent
    3. If complete: Pass through unchanged

This hook solves the Output Preservation Problem:
    Parallel Subagent -> Large Output -> Auto-Compact -> Summary only
    -> Main Agent works with summary only -> Data loss

With this hook:
    Task result -> Hook intercepts -> Summary? -> Write L2 + Guide recovery
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Environment-based workspace root with fallback
WORKSPACE_ROOT = Path(os.environ.get("CLAUDE_WORKSPACE_ROOT", os.getcwd()))

# Summary detection patterns for Output Preservation
SUMMARY_INDICATORS = [
    r"^\s*✅\s+\w+\[",
    r"^\s*⚠️\s+\w+\[",
    r"^\s*❌\s+\w+\[",
    r"summary\s*only",
    r"truncated",
]


def is_summary_only(result: str) -> Tuple[bool, List[str]]:
    """
    Detect if result is summary-only (potentially truncated or incomplete).

    Returns:
        tuple: (is_summary: bool, reasons: list[str])
    """
    if not result or len(result.strip()) < 50:
        return True, ["empty_or_too_short"]

    reasons = []
    for pattern in SUMMARY_INDICATORS:
        if re.search(pattern, result, re.IGNORECASE | re.MULTILINE):
            reasons.append(f"pattern:{pattern[:15]}")

    if len(result) < 500:
        reasons.append(f"short_chars:{len(result)}")

    if result.count('\n') + 1 < 20:
        reasons.append(f"few_lines:{result.count(chr(10)) + 1}")

    return bool(reasons), reasons


def get_agent_id_from_result(result_obj):
    """Extract agent_id from tool result object."""
    if isinstance(result_obj, dict):
        return result_obj.get("agent_id", "unknown")
    return "unknown"


def get_agent_type_from_input(input_obj):
    """Extract agent type from tool input object."""
    if isinstance(input_obj, dict):
        return input_obj.get("subagent_type", "general").lower()
    return "general"


def write_l2_report(agent_id, agent_type, content):
    """Write L2 structured report to .agent/outputs/."""
    output_dir = WORKSPACE_ROOT / ".agent" / "outputs" / agent_type
    output_dir.mkdir(parents=True, exist_ok=True)

    l2_path = output_dir / f"{agent_id}_structured.md"

    report = f"""# Agent Output: {agent_id}

## Metadata
| Field | Value |
|-------|-------|
| Agent Type | {agent_type} |
| Timestamp | {datetime.now().isoformat()} |
| Hook | output_preservation |

## Content
{content}

## Recovery Info
- **L2 Path:** {l2_path}
- **Resume:** `Task(resume="{agent_id}")`
"""
    l2_path.write_text(report, encoding="utf-8")
    return str(l2_path.relative_to(WORKSPACE_ROOT))


def log_hook_action(action, agent_id, reasons):
    """Log hook action for audit trail."""
    log_dir = WORKSPACE_ROOT / ".agent" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / "output_preservation.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {action} | agent={agent_id} | reasons={reasons}\n")


def main():
    """Main hook entry point."""
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Invalid input - pass through
        print(json.dumps({"continue": True}))
        return

    tool_name = hook_input.get("tool_name", "")

    # Only process Task tool
    if tool_name != "Task":
        print(json.dumps({"continue": True}))
        return

    tool_result = hook_input.get("tool_result", {})
    tool_input = hook_input.get("tool_input", {})

    # Get result text
    if isinstance(tool_result, dict):
        result_text = str(tool_result.get("result", tool_result.get("output", "")))
    else:
        result_text = str(tool_result)

    agent_id = get_agent_id_from_result(tool_result)
    agent_type = get_agent_type_from_input(tool_input)

    # Check if summary only
    is_summary, reasons = is_summary_only(result_text)

    if not is_summary:
        # Complete result - pass through (no additional context needed)
        log_hook_action("PASS_THROUGH", agent_id, [])
        print(json.dumps({}))  # Empty output, let primary hook (post-task-output.sh) handle
        return

    # Summary detected - write L2 and provide guidance
    l2_path = write_l2_report(agent_id, agent_type, result_text)
    log_hook_action("L2_WRITTEN", agent_id, reasons)

    guidance = f"""
## Output Preservation Alert

**Summary detected** - Main Agent must access detailed content before proceeding.

| Field | Value |
|-------|-------|
| Agent ID | `{agent_id}` |
| Agent Type | {agent_type} |
| Detection | {', '.join(reasons[:3])} |

### Recovery Options

1. **Read L2 Report:**
   ```
   Read("{l2_path}")
   ```

2. **Resume Agent (if more detail needed):**
   ```
   Task(resume="{agent_id}", prompt="Provide complete results")
   ```

### BLOCKING RULE
Do NOT proceed with summary-only results. Access L2/L3 first.
"""

    # Use hookSpecificOutput format for consistency with other hooks
    print(json.dumps({
        "hookSpecificOutput": {
            "preservationAlert": True,
            "agentId": agent_id,
            "agentType": agent_type,
            "l2Path": l2_path,
            "guidance": guidance
        }
    }))


if __name__ == "__main__":
    main()
