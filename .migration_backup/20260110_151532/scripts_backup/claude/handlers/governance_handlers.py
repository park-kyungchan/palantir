"""
Governance Stage Handlers

Implements governance checks using ODA quality gates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from scripts.claude.evidence_tracker import EvidenceTracker


# Blocked patterns for security
BLOCKED_PATTERNS = [
    "rm -rf",
    "sudo rm",
    "chmod 777",
    "DROP TABLE",
    "DROP DATABASE",
    "eval(",
    "exec(",
    "__import__",
]


async def check_blocked_patterns(target_path: str) -> List[Dict[str, Any]]:
    """Check for blocked security patterns in files."""
    violations = []
    path = Path(target_path)

    for py_file in path.glob("**/*.py"):
        try:
            content = py_file.read_text()
            for pattern in BLOCKED_PATTERNS:
                if pattern in content:
                    # Find line number
                    for i, line in enumerate(content.split('\n'), 1):
                        if pattern in line:
                            violations.append({
                                "type": "SECURITY",
                                "severity": "CRITICAL",
                                "file_path": str(py_file),
                                "line": i,
                                "pattern": pattern,
                                "description": f"Blocked pattern '{pattern}' found",
                            })
        except Exception:
            pass

    return violations


async def governance_check_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """Run full governance check on target."""
    target_path = context["target_path"]
    evidence_tracker: EvidenceTracker = context["evidence_tracker"]

    results = {
        "security": {"status": "PASS", "violations": []},
        "schema": {"status": "PASS", "violations": []},
        "overall": "PASS",
    }

    # Layer 1: Security patterns
    security_violations = await check_blocked_patterns(target_path)
    if security_violations:
        results["security"]["status"] = "BLOCK"
        results["security"]["violations"] = security_violations
        results["overall"] = "BLOCK"

    # Track evidence
    evidence_tracker.track_file_read(
        target_path,
        purpose="governance_check"
    )

    return {
        "findings": security_violations,
        "message": f"Governance check: {results['overall']}",
        "results": results,
    }
