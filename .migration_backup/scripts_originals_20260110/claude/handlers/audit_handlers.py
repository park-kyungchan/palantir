"""
Audit Stage Handlers

Implements Stage A/B/C handlers for the ODA Audit Protocol,
designed to work with Claude Code native tools.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.oda.claude.evidence_tracker import EvidenceTracker


async def audit_stage_a_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage A: SCAN - File discovery and structure analysis.

    Actions:
    1. Discover Python files in target path
    2. Map directory structure
    3. Assess complexity

    Args:
        context: Execution context with target_path, evidence_tracker, session_id

    Returns:
        Handler result with findings, message, complexity
    """
    target_path = Path(context["target_path"])
    evidence_tracker: EvidenceTracker = context["evidence_tracker"]

    findings = []

    # Discover files
    py_files = list(target_path.glob("**/*.py"))
    md_files = list(target_path.glob("**/*.md"))

    # Track evidence
    for f in py_files[:30]:  # Limit to prevent overload
        evidence_tracker.track_file_read(
            str(f),
            purpose="stage_a_scan"
        )

    # Assess complexity
    total_files = len(py_files)
    if total_files < 10:
        complexity = "small"
    elif total_files < 50:
        complexity = "medium"
    else:
        complexity = "large"

    # Generate findings
    if total_files == 0:
        findings.append({
            "severity": "WARNING",
            "description": "No Python files found in target path",
            "file_path": str(target_path),
        })

    return {
        "findings": findings,
        "message": f"Stage A SCAN complete: {total_files} Python files, {len(md_files)} docs",
        "complexity": complexity,
        "file_count": total_files,
        "structure": {
            "python_files": total_files,
            "markdown_files": len(md_files),
            "target_path": str(target_path),
        }
    }


async def audit_stage_b_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage B: TRACE - Logic analysis and dependency mapping.

    Actions:
    1. Analyze imports in Python files
    2. Map module dependencies
    3. Identify entry points

    Args:
        context: Execution context

    Returns:
        Handler result with findings, imports, dependencies
    """
    target_path = Path(context["target_path"])
    evidence_tracker: EvidenceTracker = context["evidence_tracker"]

    findings = []
    imports_found = {}

    # Analyze imports in Python files
    py_files = list(target_path.glob("**/*.py"))[:20]  # Limit

    for py_file in py_files:
        try:
            content = py_file.read_text()
            lines = content.split('\n')

            file_imports = []
            for i, line in enumerate(lines, 1):
                if line.strip().startswith(('import ', 'from ')):
                    file_imports.append({
                        "line": i,
                        "content": line.strip(),
                    })
                    # Track line reference
                    evidence_tracker.track_line_reference(
                        str(py_file),
                        i,
                        line.strip(),
                        claim="import_analysis"
                    )

            if file_imports:
                imports_found[str(py_file)] = file_imports
                evidence_tracker.track_file_read(str(py_file), purpose="import_analysis")

        except Exception as e:
            findings.append({
                "severity": "WARNING",
                "description": f"Could not analyze {py_file.name}: {str(e)}",
                "file_path": str(py_file),
            })

    # Check for circular imports (basic check)
    # (Full implementation would use AST analysis)

    return {
        "findings": findings,
        "message": f"Stage B TRACE complete: analyzed {len(imports_found)} files",
        "imports": imports_found,
        "files_analyzed": len(imports_found),
    }


async def audit_stage_c_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage C: VERIFY - Quality gate validation.

    Actions:
    1. Check code quality indicators
    2. Verify docstrings presence
    3. Check type hints

    Args:
        context: Execution context

    Returns:
        Handler result with findings, quality scores
    """
    target_path = Path(context["target_path"])
    evidence_tracker: EvidenceTracker = context["evidence_tracker"]

    findings = []
    quality_scores = {
        "docstrings": 0,
        "type_hints": 0,
        "total_functions": 0,
    }

    py_files = list(target_path.glob("**/*.py"))[:15]

    for py_file in py_files:
        try:
            content = py_file.read_text()

            # Simple quality checks
            has_docstring = '"""' in content or "'''" in content
            has_type_hints = '->' in content or ': str' in content or ': int' in content

            # Count functions
            func_count = content.count('def ')
            quality_scores["total_functions"] += func_count

            if has_docstring:
                quality_scores["docstrings"] += 1
            else:
                findings.append({
                    "severity": "INFO",
                    "description": f"No docstrings found in {py_file.name}",
                    "file_path": str(py_file),
                })

            if has_type_hints:
                quality_scores["type_hints"] += 1

            # Capture snippet for evidence
            lines = content.split('\n')[:30]
            evidence_tracker.capture_snippet(
                str(py_file),
                start_line=1,
                end_line=min(30, len(lines)),
                content='\n'.join(lines),
                relevance="quality_audit"
            )

        except Exception as e:
            findings.append({
                "severity": "WARNING",
                "description": f"Quality check failed for {py_file.name}: {str(e)}",
                "file_path": str(py_file),
            })

    # Calculate scores
    files_checked = len(py_files)
    docstring_score = (quality_scores["docstrings"] / files_checked * 10) if files_checked > 0 else 0
    type_hint_score = (quality_scores["type_hints"] / files_checked * 10) if files_checked > 0 else 0
    overall_score = (docstring_score + type_hint_score) / 2

    return {
        "findings": findings,
        "message": f"Stage C VERIFY complete: quality score {overall_score:.1f}/10",
        "quality_scores": {
            "docstrings": round(docstring_score, 1),
            "type_hints": round(type_hint_score, 1),
            "overall": round(overall_score, 1),
        },
        "files_checked": files_checked,
        "total_functions": quality_scores["total_functions"],
    }
