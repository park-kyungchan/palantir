#!/usr/bin/env python3
"""
ODA PostToolUse Hook: Task Result Validator
===========================================

Validates subagent results for completeness after Task tool execution.
This hook enforces the automatic result verification system.

Exit Codes:
    0: Allow - Result is complete OR detailed access provided
    2: Block and Prompt - Incomplete result, needs L2/L3 access or re-delegation

Behavior:
    1. Check if result is summary-only (truncated/incomplete)
    2. If summary-only:
       a. Check for L2 structured report
       b. Check for L3 raw output
       c. If neither available, suggest re-delegation
    3. Return guidance in systemMessage

Configuration: ~/.claude/hooks/config/validate_task_config.yaml
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# =============================================================================
# Configuration
# =============================================================================

CONFIG_PATH = Path("/home/palantir/.claude/hooks/config/validate_task_config.yaml")
LOG_PATH = Path("/home/palantir/park-kyungchan/palantir/.agent/logs/task_validation.log")
L2_BASE = Path("/home/palantir/.agent/outputs")
L3_BASE = Path("/tmp/claude")

# Summary detection patterns (raw strings)
_SUMMARY_INDICATOR_STRS = [
    r"^\s*✅\s+\w+\[",             # L1 Headline format: "✅ Explore[abc123]:"
    r"^\s*⚠️\s+\w+\[",
    r"^\s*❌\s+\w+\[",
    r"^\s*🔄\s+\w+\[",
    r"summary\s*only",
    r"truncated",
    r"\.{3}\s*$",                   # Ending with "..."
    r"see\s+(L2|L3|full|detailed)",
    r"for\s+details",
    r"abbreviated",
]

_COMPLETENESS_INDICATOR_STRS = [
    r"files_viewed\s*[=:]\s*\[",    # Evidence section
    r"lines_referenced",
    r"code_snippets",
    r"## Critical Findings",
    r"## Recommendations",
    r"## Details",
]

# Pre-compiled regex patterns (cached at module load)
# This avoids repeated re.compile() calls on each is_summary_only() invocation
SUMMARY_PATTERNS = [
    (re.compile(p, re.IGNORECASE | re.MULTILINE), p[:20])
    for p in _SUMMARY_INDICATOR_STRS
]
COMPLETENESS_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.MULTILINE)
    for p in _COMPLETENESS_INDICATOR_STRS
]

# Minimum content thresholds
MIN_COMPLETE_CHARS = 500        # Results shorter than this are likely summaries
MIN_COMPLETE_LINES = 20         # Results with fewer lines are likely summaries
MIN_EVIDENCE_ITEMS = 2          # Need at least 2 evidence items


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML or use defaults."""
    defaults = {
        "enabled": True,
        "enforcement_mode": "WARN",  # WARN | BLOCK
        "min_complete_chars": MIN_COMPLETE_CHARS,
        "min_complete_lines": MIN_COMPLETE_LINES,
        "auto_access_l2": True,
        "auto_access_l3": False,
        "suggest_resume": True,
        "log_validations": True,
    }

    if not HAS_YAML or not CONFIG_PATH.exists():
        return defaults

    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
        return {**defaults, **config}
    except Exception:
        return defaults


CONFIG = load_config()


# =============================================================================
# Summary Detection
# =============================================================================

def is_summary_only(result: str) -> Tuple[bool, List[str]]:
    """
    Detect if result is a summary/headline rather than complete output.

    Returns:
        (is_summary, reasons) tuple
    """
    reasons = []

    # Empty or very short
    if not result or len(result.strip()) < 50:
        return True, ["empty_or_too_short"]

    # Check for summary indicators (using pre-compiled patterns)
    for compiled_pattern, pattern_preview in SUMMARY_PATTERNS:
        if compiled_pattern.search(result):
            reasons.append(f"pattern:{pattern_preview}")

    # Check length thresholds
    char_count = len(result)
    line_count = result.count('\n') + 1

    if char_count < CONFIG.get("min_complete_chars", MIN_COMPLETE_CHARS):
        reasons.append(f"short_chars:{char_count}")

    if line_count < CONFIG.get("min_complete_lines", MIN_COMPLETE_LINES):
        reasons.append(f"few_lines:{line_count}")

    # Check for completeness indicators (negative evidence, using pre-compiled patterns)
    completeness_score = 0
    for compiled_pattern in COMPLETENESS_PATTERNS:
        if compiled_pattern.search(result):
            completeness_score += 1

    if completeness_score >= MIN_EVIDENCE_ITEMS:
        # Has completeness indicators, likely not just a summary
        return False, []

    # If we have reasons and low completeness, it's a summary
    if reasons and completeness_score < MIN_EVIDENCE_ITEMS:
        return True, reasons

    return False, []


def extract_agent_id(result: str) -> Optional[str]:
    """Extract agent ID from result text."""
    # Try L1 headline format: "✅ Explore[a1b2c3d]:"
    match = re.search(r'\[([a-f0-9]{7,})\]', result)
    if match:
        return match.group(1)

    # Try agent_id field
    match = re.search(r'agent_id["\s:=]+([a-f0-9-]{7,})', result, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def extract_agent_type(result: str) -> str:
    """Extract agent type from result text."""
    # Try L1 headline format
    match = re.search(r'(Explore|Plan|general-purpose|evidence-collector)\[', result, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try agent_type field
    match = re.search(r'agent_type["\s:=]+["\']?(\w+)', result, re.IGNORECASE)
    if match:
        return match.group(1)

    return "general"


# =============================================================================
# L2/L3 Access
# =============================================================================

def find_l2_report(agent_id: str, agent_type: str = "general") -> Optional[Path]:
    """Find L2 structured report for agent."""
    if not agent_id:
        return None

    # Try exact path
    type_dir = agent_type.lower().replace("-", "_").replace(" ", "_")
    exact_path = L2_BASE / type_dir / f"{agent_id}.md"
    if exact_path.exists():
        return exact_path

    # Search in all type directories
    if L2_BASE.exists():
        for subdir in L2_BASE.iterdir():
            if subdir.is_dir():
                report = subdir / f"{agent_id}.md"
                if report.exists():
                    return report
                # Try partial match
                for f in subdir.glob(f"{agent_id[:7]}*.md"):
                    return f

    return None


def find_l3_output(agent_id: str) -> Optional[Path]:
    """Find L3 raw output for agent."""
    if not agent_id or not L3_BASE.exists():
        return None

    # Search in /tmp/claude/*/tasks/
    for session_dir in L3_BASE.iterdir():
        if session_dir.is_dir():
            tasks_dir = session_dir / "tasks"
            if tasks_dir.exists():
                output_file = tasks_dir / f"{agent_id}.output"
                if output_file.exists():
                    return output_file
                # Try partial match
                for f in tasks_dir.glob(f"{agent_id[:7]}*.output"):
                    return f

    return None


def read_l2_summary(l2_path: Path, max_chars: int = 2000) -> str:
    """Read L2 report summary section."""
    try:
        content = l2_path.read_text()
        # Extract just the summary and key findings
        lines = []
        in_section = False
        section_count = 0

        for line in content.split('\n'):
            if line.startswith('## '):
                section_count += 1
                if section_count > 4:  # Limit sections
                    break
                in_section = True
            if in_section:
                lines.append(line)

        summary = '\n'.join(lines)
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "\n... [truncated, read full L2 for details]"

        return summary
    except Exception as e:
        return f"[Error reading L2: {e}]"


# =============================================================================
# Validation Logic
# =============================================================================

def validate_task_result(tool_input: Dict, tool_output: str) -> Dict[str, Any]:
    """
    Validate Task tool result for completeness.

    Returns decision dict with:
        - decision: "allow" | "block"
        - systemMessage: Guidance for Main Agent
    """
    # Extract agent info
    agent_id = extract_agent_id(tool_output)
    agent_type = extract_agent_type(tool_output)

    # Check if summary only
    is_summary, reasons = is_summary_only(tool_output)

    if not is_summary:
        # Result appears complete
        return {
            "decision": "allow",
            "systemMessage": None
        }

    # Result is summary-only, check for L2/L3
    l2_path = find_l2_report(agent_id, agent_type) if agent_id else None
    l3_path = find_l3_output(agent_id) if agent_id else None

    # Build guidance message
    guidance_parts = [
        f"[VALIDATE] Task result appears to be summary-only.",
        f"Reasons: {', '.join(reasons[:3])}",
    ]

    if l2_path:
        guidance_parts.append(f"L2 available: {l2_path}")
        if CONFIG.get("auto_access_l2"):
            l2_summary = read_l2_summary(l2_path)
            guidance_parts.append(f"L2 Content:\n{l2_summary}")

    if l3_path:
        guidance_parts.append(f"L3 available: {l3_path}")

    if not l2_path and not l3_path:
        guidance_parts.append(
            "No L2/L3 found. Consider: Task(resume=agent_id) or re-delegate task."
        )

    # Determine decision based on mode
    mode = CONFIG.get("enforcement_mode", "WARN").upper()

    # V2.1.9: Build recovery guidance for additionalContext
    recovery_template = f"""## Task Result Incomplete

The subagent result appears to be summary-only.

**Detected Issues:**
{chr(10).join(f'- {r}' for r in reasons[:3])}

**Recovery Options:**
"""

    if l2_path:
        recovery_template += f"""
1. **Read L2 Structured Report (Recommended):**
   ```python
   Read("{l2_path}")
   ```
   Cost: ~2000 tokens
"""

    if l3_path:
        recovery_template += f"""
2. **Read L3 Raw Output:**
   ```python
   Read("{l3_path}")
   ```
   Cost: Full output
"""

    if agent_id:
        recovery_template += f"""
3. **Resume Subagent:**
   ```python
   Task(
       resume="{agent_id}",
       prompt="Continue and provide complete results",
       subagent_type="{agent_type or 'general-purpose'}"
   )
   ```
   Cost: New execution
"""

    if not l2_path and not l3_path:
        recovery_template += """
**Warning:** No L2/L3 outputs found. Re-delegation may be required.
"""

    recovery_template += """
**Reference:** CLAUDE.md Section 5.1 (Automatic Result Verification)"""

    if mode == "BLOCK" and not l2_path and not l3_path:
        # Block only if no detailed output available
        return {
            "decision": "block",
            "systemMessage": '\n'.join(guidance_parts) + "\n[ACTION REQUIRED] Read L2/L3 or re-delegate before proceeding.",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "permissionDecision": "deny",
                "additionalContext": recovery_template
            }
        }

    # WARN or BLOCK with L2/L3 available
    permission_decision = "ask" if (l2_path or l3_path) else "deny"
    return {
        "decision": "allow",
        "systemMessage": '\n'.join(guidance_parts),
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "permissionDecision": permission_decision,
            "additionalContext": recovery_template
        }
    }


# =============================================================================
# Logging
# =============================================================================

def log_validation(
    agent_id: Optional[str],
    is_summary: bool,
    reasons: List[str],
    l2_found: bool,
    l3_found: bool,
    decision: str
) -> None:
    """Log validation result."""
    if not CONFIG.get("log_validations", True):
        return

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(),
            "agent_id": agent_id or "unknown",
            "is_summary": is_summary,
            "reasons": reasons[:5],
            "l2_found": l2_found,
            "l3_found": l3_found,
            "decision": decision,
            "session": os.environ.get('CLAUDE_SESSION_ID', 'unknown')[:8]
        }
        with open(LOG_PATH, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point for PostToolUse hook."""
    try:
        if not CONFIG.get("enabled", True):
            print(json.dumps({"decision": "allow"}))
            return

        # Read hook input
        data = json.load(sys.stdin)
        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})
        tool_output = data.get('tool_output', '')

        # Only validate Task tool results
        if tool_name != 'Task':
            print(json.dumps({"decision": "allow"}))
            return

        # Convert tool_output to string if needed
        if isinstance(tool_output, dict):
            tool_output = json.dumps(tool_output, indent=2)
        elif not isinstance(tool_output, str):
            tool_output = str(tool_output)

        # Validate result
        result = validate_task_result(tool_input, tool_output)

        # Log validation
        agent_id = extract_agent_id(tool_output)
        is_summary, reasons = is_summary_only(tool_output)
        l2_path = find_l2_report(agent_id, extract_agent_type(tool_output)) if agent_id else None
        l3_path = find_l3_output(agent_id) if agent_id else None

        log_validation(
            agent_id=agent_id,
            is_summary=is_summary,
            reasons=reasons,
            l2_found=l2_path is not None,
            l3_found=l3_path is not None,
            decision=result["decision"]
        )

        # Output result
        print(json.dumps(result))

    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # Fallback to allow on error
        print(json.dumps({
            "decision": "allow",
            "systemMessage": f"[FALLBACK] Task validation error: {e}"
        }))
    finally:
        sys.exit(0)


if __name__ == '__main__':
    main()
