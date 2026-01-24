"""
ODA L2 Synthesizer
==================

Synthesizes multiple L2 structured reports into condensed essential context.
Enables efficient context management by extracting only what's needed.

V2.1.10 Feature: L2 Synthesizer + Structured Prompts

This module provides:
1. L2Synthesizer class for local synthesis of L2 reports
2. Prompt building for l2-synthesizer subagent delegation
3. Convenience functions for quick synthesis

Usage:
    from lib.oda.planning.l2_synthesizer import (
        L2Synthesizer,
        synthesize_l2_files,
    )

    # Using the class
    synthesizer = L2Synthesizer()
    result = synthesizer.synthesize(
        l2_paths=[
            ".agent/outputs/explore/a1b2c3d_structured.md",
            ".agent/outputs/plan/b2c3d4e_structured.md"
        ],
        synthesis_goal="security concerns for implementation"
    )

    # Using convenience function
    result = synthesize_l2_files(
        l2_paths=["path1", "path2"],
        synthesis_goal="security issues"
    )
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.oda.planning.output_schemas import SynthesisOutput, validate_output
from lib.oda.planning.prompt_templates import (
    PromptTemplateBuilder,
    get_recommended_budget,
)


# L2 output base directory
L2_BASE = Path("/home/palantir/.agent/outputs")

# Agent type to directory mapping
AGENT_TYPE_DIRS = {
    "explore": "explore",
    "plan": "plan",
    "general-purpose": "general",
    "general_purpose": "general",
    "evidence-collector": "evidence",
    "evidence_collector": "evidence",
}

# Severity ordering for prioritization
SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFO": 4,
}


class L2Synthesizer:
    """
    Synthesizes multiple L2 structured reports into condensed context.

    This class can work in two modes:
    1. Local synthesis (fast, no subagent) - for simple cases with <= 2 files
    2. Subagent synthesis (via Task) - for complex multi-file cases

    Attributes:
        l2_base: Base directory for L2 outputs

    Usage:
        synthesizer = L2Synthesizer()
        result = synthesizer.synthesize(
            l2_paths=[
                ".agent/outputs/explore/a1b2c3d_structured.md",
                ".agent/outputs/plan/b2c3d4e_structured.md"
            ],
            synthesis_goal="security concerns for implementation"
        )
        # Returns: Dict with ~500 tokens of essential context
    """

    def __init__(self, l2_base: Optional[Path] = None):
        """
        Initialize L2 Synthesizer.

        Args:
            l2_base: Base directory for L2 outputs (default: .agent/outputs)
        """
        self.l2_base = l2_base or L2_BASE

    def synthesize(
        self,
        l2_paths: List[str],
        synthesis_goal: str,
        max_output_tokens: int = 500,
    ) -> Dict[str, Any]:
        """
        Synthesize multiple L2 files into condensed context.

        This method can work in two modes:
        1. Local synthesis (fast, no subagent) - for simple cases
        2. Subagent synthesis (via Task) - for complex multi-file cases

        Args:
            l2_paths: List of L2 file paths to synthesize
            synthesis_goal: What to extract (e.g., "security issues")
            max_output_tokens: Maximum output tokens (default 500)

        Returns:
            Dict matching SynthesisOutput schema
        """
        if len(l2_paths) <= 2:
            # Simple case: local synthesis
            return self._local_synthesize(l2_paths, synthesis_goal)
        else:
            # Complex case: build prompt for subagent delegation
            return self._build_synthesis_prompt(
                l2_paths, synthesis_goal, max_output_tokens
            )

    def _local_synthesize(
        self,
        l2_paths: List[str],
        synthesis_goal: str,
    ) -> Dict[str, Any]:
        """
        Perform local synthesis without subagent (for simple cases).

        Args:
            l2_paths: List of L2 file paths
            synthesis_goal: What to extract

        Returns:
            Synthesized result dict matching SynthesisOutput schema
        """
        all_findings: List[str] = []
        all_files: List[str] = []
        cross_concerns: List[str] = []
        agent_summaries: List[Dict[str, Any]] = []

        for path in l2_paths:
            content = self._read_l2_file(path)
            if content:
                # Extract agent info
                agent_id = self._extract_agent_id(path)
                agent_type = self._extract_agent_type(path)

                findings = self._extract_findings(content, synthesis_goal)
                all_findings.extend(findings)

                files = self._extract_file_refs(content)
                all_files.extend(files)

                # Build agent summary
                agent_summaries.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "status": content.get("status", "completed"),
                        "key_findings": findings[:5],  # Top 5 per agent
                        "files_referenced": files[:10],  # Top 10 per agent
                        "l2_path": path,
                    }
                )

        # Deduplicate and prioritize
        critical = self._prioritize_findings(all_findings)[:10]
        unique_files = list(dict.fromkeys(all_files))[:50]  # Preserve order, dedupe

        # Detect cross-module concerns
        if len(l2_paths) > 1:
            cross_concerns = self._detect_cross_concerns(all_findings)

        return {
            "summary": self._generate_summary(critical, synthesis_goal),
            "total_agents": len(l2_paths),
            "agent_summaries": agent_summaries,
            "critical_findings": critical,
            "cross_module_concerns": cross_concerns[:5],
            "consolidated_files": unique_files,
            "recommended_next_action": self._recommend_action(critical),
            "additional_recommendations": self._additional_recs(critical, all_findings),
        }

    def _build_synthesis_prompt(
        self,
        l2_paths: List[str],
        synthesis_goal: str,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """
        Build prompt for l2-synthesizer subagent delegation.

        Returns a dict with 'prompt' key for Task() delegation.
        This is used when Main Agent needs to delegate synthesis.

        Args:
            l2_paths: List of L2 file paths
            synthesis_goal: What to extract
            max_tokens: Maximum output tokens

        Returns:
            Dict with prompt and delegation metadata
        """
        builder = PromptTemplateBuilder("synthesis")

        task_description = f"""
## Synthesis Goal
{synthesis_goal}

## L2 Files to Read
{chr(10).join(f"- {p}" for p in l2_paths)}

## Instructions
1. Read each L2 file using the Read tool
2. Extract ONLY information relevant to: {synthesis_goal}
3. Identify patterns across files
4. Return condensed synthesis (max {max_tokens} tokens)
"""

        prompt = builder.build(
            task_description=task_description,
            budget=max_tokens,
            additional_context=f"Total files: {len(l2_paths)}",
        )

        return {
            "prompt": prompt,
            "subagent_type": "l2-synthesizer",
            "description": f"Synthesize {len(l2_paths)} L2 files",
            "l2_paths": l2_paths,
            "synthesis_goal": synthesis_goal,
        }

    def _read_l2_file(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Read and parse L2 file content.

        Args:
            path: Path to L2 file

        Returns:
            Parsed content dict or None if read fails
        """
        try:
            full_path = Path(path)
            if not full_path.is_absolute():
                full_path = self.l2_base.parent / path

            if not full_path.exists():
                return None

            content = full_path.read_text()

            # Try to extract JSON from markdown code block
            json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try direct JSON parse
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

            # Return as structured dict from markdown
            return self._parse_markdown_l2(content)

        except Exception:
            return None

    def _parse_markdown_l2(self, content: str) -> Dict[str, Any]:
        """
        Parse markdown L2 file into structured dict.

        Args:
            content: Raw markdown content

        Returns:
            Structured dict with findings, files, and summary
        """
        result: Dict[str, Any] = {"findings": [], "files": [], "summary": ""}

        # Extract summary
        summary_match = re.search(
            r"## Summary\s*\n(.+?)(?=\n##|\Z)", content, re.DOTALL
        )
        if summary_match:
            result["summary"] = summary_match.group(1).strip()[:200]

        # Extract findings with severity
        for match in re.finditer(
            r"\[(CRITICAL|HIGH|MEDIUM|LOW|INFO)\]\s*([^\n]+)", content
        ):
            result["findings"].append(
                {"severity": match.group(1), "description": match.group(2).strip()}
            )

        # Extract file references (file.ext:line format)
        for match in re.finditer(
            r"([a-zA-Z0-9_/.-]+\.[a-z]+):(\d+)", content
        ):
            result["files"].append(f"{match.group(1)}:{match.group(2)}")

        # Also capture files without line numbers
        for match in re.finditer(
            r"(?:^|\s)([a-zA-Z0-9_/.-]+\.(?:py|ts|js|md|yaml|json|toml))\b", content
        ):
            if match.group(1) not in result["files"]:
                result["files"].append(match.group(1))

        return result

    def _extract_agent_id(self, path: str) -> str:
        """
        Extract agent ID from L2 file path.

        Args:
            path: L2 file path

        Returns:
            Agent ID string
        """
        # Pattern: .../type/agentid_structured.md
        match = re.search(r"/([a-zA-Z0-9_-]+)_structured\.md$", path)
        if match:
            return match.group(1)
        return Path(path).stem.replace("_structured", "")

    def _extract_agent_type(self, path: str) -> str:
        """
        Extract agent type from L2 file path.

        Args:
            path: L2 file path

        Returns:
            Agent type string (capitalized)
        """
        # Pattern: .../type/agentid_structured.md
        parts = Path(path).parts
        for part in parts:
            if part in AGENT_TYPE_DIRS.values():
                return part.capitalize()
        return "Unknown"

    def _extract_findings(
        self, content: Dict[str, Any], goal: str
    ) -> List[str]:
        """
        Extract findings relevant to synthesis goal.

        Args:
            content: Parsed L2 content
            goal: Synthesis goal for filtering

        Returns:
            List of finding strings with severity prefix
        """
        findings: List[str] = []

        if "findings" in content:
            for finding in content["findings"]:
                if isinstance(finding, dict):
                    desc = finding.get("description", "")
                    severity = finding.get("severity", "MEDIUM")
                    findings.append(f"[{severity}] {desc}")
                elif isinstance(finding, str):
                    findings.append(finding)

        # Also check for 'critical_findings' key
        if "critical_findings" in content:
            for f in content["critical_findings"]:
                if f not in findings:
                    findings.append(f)

        return findings

    def _extract_file_refs(self, content: Dict[str, Any]) -> List[str]:
        """
        Extract file references from content.

        Args:
            content: Parsed L2 content

        Returns:
            List of file reference strings
        """
        refs: List[str] = []
        if "files" in content:
            refs.extend(content["files"])
        if "file_references" in content:
            refs.extend(content["file_references"])
        if "files_analyzed" in content:
            refs.extend(content["files_analyzed"])
        if "consolidated_files" in content:
            refs.extend(content["consolidated_files"])
        return refs

    def _prioritize_findings(self, findings: List[str]) -> List[str]:
        """
        Sort findings by severity.

        Args:
            findings: List of finding strings

        Returns:
            Sorted list with highest severity first
        """

        def get_severity(f: str) -> int:
            for sev, order in SEVERITY_ORDER.items():
                if f"[{sev}]" in f:
                    return order
            return 5  # Unknown severity

        return sorted(findings, key=get_severity)

    def _detect_cross_concerns(self, findings: List[str]) -> List[str]:
        """
        Detect issues that span multiple modules.

        Args:
            findings: List of all findings

        Returns:
            List of cross-module concern descriptions
        """
        concerns: List[str] = []
        module_counts: Dict[str, int] = {}

        for finding in findings:
            # Extract module names from paths
            modules = re.findall(r"([a-z_]+)/", finding.lower())
            for mod in modules:
                module_counts[mod] = module_counts.get(mod, 0) + 1

        # Modules appearing in multiple findings suggest cross-concerns
        for mod, count in sorted(
            module_counts.items(), key=lambda x: x[1], reverse=True
        ):
            if count >= 2:
                concerns.append(
                    f"Multiple issues in {mod} module ({count} findings)"
                )

        return concerns

    def _generate_summary(self, findings: List[str], goal: str) -> str:
        """
        Generate a one-line summary.

        Args:
            findings: Prioritized findings list
            goal: Synthesis goal

        Returns:
            Summary string (max 100 chars)
        """
        critical_count = sum(1 for f in findings if "[CRITICAL]" in f)
        high_count = sum(1 for f in findings if "[HIGH]" in f)

        goal_short = goal[:30] if len(goal) > 30 else goal

        if critical_count > 0:
            return f"{critical_count} critical, {high_count} high priority issues for {goal_short}"
        elif high_count > 0:
            return f"{high_count} high priority issues found for {goal_short}"
        elif findings:
            return f"{len(findings)} findings for {goal_short}"
        else:
            return f"No significant issues found for {goal_short}"

    def _recommend_action(self, findings: List[str]) -> str:
        """
        Generate recommended next action based on findings.

        Args:
            findings: Prioritized findings list

        Returns:
            Action recommendation string
        """
        if not findings:
            return "Proceed with implementation"

        # Find highest severity finding
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            for finding in findings:
                if f"[{sev}]" in finding:
                    # Extract actionable part
                    action = finding.replace(f"[{sev}]", "").strip()
                    return f"Address: {action[:80]}"

        return "Review findings before proceeding"

    def _additional_recs(
        self, critical: List[str], all_findings: List[str]
    ) -> List[str]:
        """
        Generate additional recommendations.

        Args:
            critical: Top critical findings
            all_findings: All findings

        Returns:
            List of secondary recommendations
        """
        recs: List[str] = []

        # Check for patterns
        medium_count = sum(1 for f in all_findings if "[MEDIUM]" in f)
        if medium_count > 3:
            recs.append(f"Address {medium_count} medium-priority items after critical fixes")

        # Check for test-related findings
        test_findings = [f for f in all_findings if "test" in f.lower()]
        if test_findings:
            recs.append("Review test coverage for affected modules")

        return recs[:5]

    def get_l2_paths_for_task(self, task_id: str) -> List[str]:
        """
        Find all L2 files related to a parent task.

        Args:
            task_id: Parent task identifier

        Returns:
            List of L2 file paths containing task_id
        """
        paths: List[str] = []
        for agent_dir in set(AGENT_TYPE_DIRS.values()):
            dir_path = self.l2_base / agent_dir
            if dir_path.exists():
                for f in dir_path.glob("*_structured.md"):
                    # Check if file relates to task
                    try:
                        if task_id in f.read_text():
                            paths.append(str(f))
                    except Exception:
                        continue
        return paths

    def get_recent_l2_paths(
        self, agent_types: Optional[List[str]] = None, limit: int = 10
    ) -> List[str]:
        """
        Get most recent L2 files, optionally filtered by agent type.

        Args:
            agent_types: Optional list of agent types to filter
            limit: Maximum number of paths to return

        Returns:
            List of L2 file paths sorted by modification time (newest first)
        """
        paths: List[Path] = []

        dirs_to_check = (
            [self.l2_base / AGENT_TYPE_DIRS.get(t, t) for t in (agent_types or [])]
            if agent_types
            else [self.l2_base / d for d in set(AGENT_TYPE_DIRS.values())]
        )

        for dir_path in dirs_to_check:
            if dir_path.exists():
                paths.extend(dir_path.glob("*_structured.md"))

        # Sort by modification time (newest first)
        paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        return [str(p) for p in paths[:limit]]

    def validate_synthesis_result(
        self, result: Dict[str, Any]
    ) -> tuple[Optional[SynthesisOutput], Optional[str]]:
        """
        Validate synthesis result against SynthesisOutput schema.

        Args:
            result: Synthesis result dict

        Returns:
            Tuple of (validated_model, error_message)
        """
        return validate_output("synthesis", result)


# Convenience function for quick synthesis
def synthesize_l2_files(
    l2_paths: List[str],
    synthesis_goal: str,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """
    Convenience function to synthesize L2 files.

    Args:
        l2_paths: List of L2 file paths
        synthesis_goal: What to extract
        max_tokens: Maximum output tokens

    Returns:
        Synthesized result dict matching SynthesisOutput schema

    Example:
        >>> result = synthesize_l2_files(
        ...     l2_paths=[".agent/outputs/explore/abc_structured.md"],
        ...     synthesis_goal="security issues"
        ... )
        >>> "summary" in result
        True
    """
    synthesizer = L2Synthesizer()
    return synthesizer.synthesize(l2_paths, synthesis_goal, max_tokens)


def get_l2_base_path() -> Path:
    """
    Get the L2 output base directory path.

    Returns:
        Path to .agent/outputs directory
    """
    return L2_BASE


def get_agent_type_directory(agent_type: str) -> str:
    """
    Get the directory name for an agent type.

    Args:
        agent_type: Agent type string

    Returns:
        Directory name for the agent type
    """
    normalized = agent_type.lower().replace("-", "_")
    return AGENT_TYPE_DIRS.get(normalized, normalized)


# Export all public symbols
__all__ = [
    # Main class
    "L2Synthesizer",
    # Convenience functions
    "synthesize_l2_files",
    "get_l2_base_path",
    "get_agent_type_directory",
    # Constants
    "L2_BASE",
    "AGENT_TYPE_DIRS",
    "SEVERITY_ORDER",
]
