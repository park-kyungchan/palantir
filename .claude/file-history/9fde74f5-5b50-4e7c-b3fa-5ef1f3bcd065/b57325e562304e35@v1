"""
Output Verification Module - Lightweight Edition
================================================

V2.1.12: Extracted from output_layer_manager.py for Output Preservation enforcement.

Purpose:
    Provide essential functions for detecting summary-only results and
    verifying subagent output completeness.

Key Functions:
    - is_summary_only() - Detects if result is summary vs complete output
    - verify_subagent_result() - Verifies result and retrieves L2/L3 if needed
    - read_l2_file() / read_l3_file() - Layer access utilities

Usage:
    # In PostToolUse Hook
    from lib.oda.planning.output_verification import is_summary_only
    is_summary, reasons = is_summary_only(task_result)

    # In /execute Step 6
    from lib.oda.planning.output_verification import verify_subagent_result
    result, status = verify_subagent_result(task_output, agent_id)

Source Reference:
    Extracted from lib/oda/planning/output_layer_manager.py:625-812
"""

from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import List, Optional, Tuple


# ============================================================================
# CONSTANTS
# ============================================================================

SUMMARY_INDICATORS = [
    r"^\s*✅\s+\w+\[",             # L1 Headline: ✅ Explore[id]
    r"^\s*⚠️\s+\w+\[",             # Warning headline
    r"^\s*❌\s+\w+\[",             # Error headline
    r"summary\s*only",             # Explicit summary marker
    r"truncated",                  # Truncation marker
    r"\.{3}\s*$",                  # Trailing ellipsis
    r"see\s+(L2|L3|full|detailed)", # Reference to detailed layer
    r"abbreviated",                # Abbreviated marker
]

COMPLETENESS_INDICATORS = [
    r"files_viewed\s*[=:]\s*\[",   # Evidence: files_viewed
    r"lines_referenced",           # Evidence: line references
    r"## Critical Findings",       # Report section
    r"## Recommendations",         # Report section
    r"## Evidence",                # Report section
]

MIN_COMPLETE_CHARS = 500
MIN_COMPLETE_LINES = 20


# ============================================================================
# CORE DETECTION FUNCTION
# ============================================================================

def is_summary_only(result: str) -> Tuple[bool, List[str]]:
    """
    Detect if result is a summary/headline rather than complete output.

    This is the core detection function used by:
    1. PostToolUse Hook - to decide if L2 should be written
    2. /execute Step 6 - to verify result completeness

    Args:
        result: The subagent result text to analyze

    Returns:
        Tuple of (is_summary: bool, reasons: List[str])

    Example:
        >>> is_summary, reasons = is_summary_only("✅ Explore[abc]: Found 8 files")
        >>> print(is_summary)  # True
        >>> print(reasons)     # ['pattern:^\\s*✅\\s+\\w+\\[', 'short_chars:35']

        >>> is_summary, _ = is_summary_only(detailed_report_with_evidence)
        >>> print(is_summary)  # False (has completeness indicators)
    """
    reasons: List[str] = []

    # Edge case: empty or tiny result
    if not result or len(result.strip()) < 50:
        return True, ["empty_or_too_short"]

    # Check for summary indicator patterns
    for pattern in SUMMARY_INDICATORS:
        if re.search(pattern, result, re.IGNORECASE | re.MULTILINE):
            reasons.append(f"pattern:{pattern[:20]}")

    # Check length thresholds
    char_count = len(result)
    line_count = result.count('\n') + 1

    if char_count < MIN_COMPLETE_CHARS:
        reasons.append(f"short_chars:{char_count}")

    if line_count < MIN_COMPLETE_LINES:
        reasons.append(f"few_lines:{line_count}")

    # Check for completeness indicators (positive evidence)
    completeness_score = sum(
        1 for pattern in COMPLETENESS_INDICATORS
        if re.search(pattern, result, re.IGNORECASE | re.MULTILINE)
    )

    # If 2+ completeness indicators found, consider complete
    if completeness_score >= 2:
        return False, []

    # Summary if we have reasons and low completeness
    if reasons and completeness_score < 2:
        return True, reasons

    return False, []


# ============================================================================
# LAYER ACCESS FUNCTIONS
# ============================================================================

def read_l2_file(
    agent_id: str,
    agent_type: str = "general",
    workspace_root: Optional[str] = None,
) -> Optional[str]:
    """
    Read L2 structured report if it exists.

    L2 files are written to .agent/outputs/{type}/{id}_structured.md
    and contain ~2000 tokens of structured content.

    Args:
        agent_id: The subagent ID (e.g., "a1b2c3d")
        agent_type: Type of agent (e.g., "explore", "plan", "general")
        workspace_root: Optional workspace root path

    Returns:
        L2 file content or None if not found
    """
    root = Path(workspace_root) if workspace_root else Path(".")

    # Try multiple path patterns
    patterns = [
        root / f".agent/outputs/{agent_type}/{agent_id}_structured.md",
        root / f".agent/outputs/{agent_type}/{agent_id}.md",
        root / f".agent/outputs/{agent_type.lower()}/{agent_id}_structured.md",
        root / f".agent/outputs/{agent_type.lower()}/{agent_id}.md",
    ]

    for path in patterns:
        if path.exists():
            return path.read_text(encoding="utf-8")

    return None


def read_l3_file(agent_id: str) -> Optional[str]:
    """
    Read L3 raw output file if it exists.

    L3 files are written by Claude Code to /tmp/claude/.../tasks/{id}.output
    and contain the full untruncated output.

    Args:
        agent_id: The subagent ID

    Returns:
        L3 file content or None if not found
    """
    # Search for L3 output file
    search_patterns = [
        f"/tmp/claude/**/tasks/{agent_id}.output",
        f"/tmp/claude-*/tasks/{agent_id}.output",
    ]

    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return Path(matches[0]).read_text(encoding="utf-8")

    return None


# ============================================================================
# MAIN VERIFICATION FUNCTION
# ============================================================================

def verify_subagent_result(
    result: str,
    agent_id: str,
    agent_type: str = "general",
) -> Tuple[str, str]:
    """
    Verify subagent result completeness and retrieve detailed content if needed.

    This is the main entry point for /execute Step 6 verification.
    It checks if the result is a summary, and if so, automatically retrieves
    the detailed L2/L3 content.

    Args:
        result: The subagent result to verify
        agent_id: The subagent ID
        agent_type: Type of agent (e.g., "explore", "plan", "general")

    Returns:
        Tuple of (verified_result, status) where status is one of:
        - "complete": Original result is complete, no action needed
        - "l2_accessed": Summary detected, L2 content retrieved
        - "l3_accessed": Summary detected, L3 content retrieved (L2 missing)
        - "needs_redelegation": Summary detected, no L2/L3 available

    Usage in /execute:
        result, status = verify_subagent_result(task_output, agent_id, agent_type)

        if status == "complete":
            update_todo_status(phase, "completed")
        elif status in ("l2_accessed", "l3_accessed"):
            task_output = result  # Use detailed content
            update_todo_status(phase, "completed", f"({status})")
        elif status == "needs_redelegation":
            # BLOCK - must re-delegate
            Task(resume=agent_id, prompt="Continue and provide full results")
    """
    # Step 1: Check if summary only
    is_summary, reasons = is_summary_only(result)

    if not is_summary:
        return result, "complete"

    # Step 2: Try L2 (preferred - structured, ~2000 tokens)
    l2_content = read_l2_file(agent_id, agent_type)
    if l2_content:
        return l2_content, "l2_accessed"

    # Step 3: Try L3 (fallback - full raw output)
    l3_content = read_l3_file(agent_id)
    if l3_content:
        return l3_content, "l3_accessed"

    # Step 4: No detailed content available
    return result, "needs_redelegation"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_agent_id_from_result(result: str) -> Optional[str]:
    """
    Extract agent ID from a subagent result headline.

    Tries multiple patterns to find the agent ID:
    - ✅ Explore[abc123]: ...
    - Agent ID: abc123
    - agent_id: abc123

    Args:
        result: The subagent result text

    Returns:
        Agent ID string or None if not found
    """
    patterns = [
        r"[✅⚠️❌]\s*\w+\[([a-f0-9]{7,})\]",  # Headline format
        r"(?:agent[_\s]?id|Agent ID)[:\s]+([a-f0-9]{7,})",  # Explicit ID
    ]

    for pattern in patterns:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Constants
    "SUMMARY_INDICATORS",
    "COMPLETENESS_INDICATORS",
    "MIN_COMPLETE_CHARS",
    "MIN_COMPLETE_LINES",
    # Core functions
    "is_summary_only",
    "verify_subagent_result",
    # Layer access
    "read_l2_file",
    "read_l3_file",
    # Utilities
    "extract_agent_id_from_result",
]
