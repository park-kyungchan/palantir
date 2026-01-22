"""
Orion ODA v3.0 - Output Layer Manager
=====================================

3-Layer Progressive-Disclosure Output System for Resume-Enhanced Orchestration.

This module implements the 3-Layer output structure that enables efficient
context management while preserving full agent outputs for resume capability.

Layer Structure:
    L1 (Headline):    ~50 tokens in Main Context
    L2 (Structured):  .agent/outputs/{type}/{agent_id}.md
    L3 (Raw):         /tmp/claude/.../tasks/{agent_id}.output

Usage:
    manager = OutputLayerManager()

    # After subagent completes
    headline = manager.format_headline(agent_id, result, task_type)
    manager.write_structured_report(agent_id, result, task_type)

    # User asks for details
    l2_content = manager.read_layer(agent_id, OutputLayer.L2_STRUCTURED)
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class OutputLayer(str, Enum):
    """Output layer levels for progressive disclosure."""
    L1_HEADLINE = "headline"      # Main context (~50 tokens)
    L2_STRUCTURED = "structured"  # .agent/outputs/ (~2000 tokens)
    L3_RAW = "raw"               # /tmp/claude/.../tasks/


class TaskType(str, Enum):
    """Task type classification for layer access decision."""
    DESIGN = "설계"           # High-level understanding
    PLANNING = "계획"         # Detailed planning
    EXECUTION = "실행계획"    # Ready-to-execute


class AgentStatus(str, Enum):
    """Status indicators for headlines."""
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    IN_PROGRESS = "🔄"
    PAUSED = "⏸️"


@dataclass
class HeadlineResult:
    """Result of headline formatting."""
    headline: str
    agent_id: str
    agent_type: str
    status: AgentStatus
    summary: str
    token_estimate: int


@dataclass
class StructuredReport:
    """Structured report for L2 output."""
    agent_id: str
    agent_type: str
    task_description: str
    timestamp: str
    status: str

    # Content sections
    summary: str
    key_findings: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    # References
    l3_path: str = ""
    related_files: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = [
            f"# Agent Output: {self.agent_id}",
            "",
            "## Metadata",
            f"- **Agent Type**: {self.agent_type}",
            f"- **Task**: {self.task_description}",
            f"- **Timestamp**: {self.timestamp}",
            f"- **Status**: {self.status}",
            "",
            "## Summary",
            self.summary,
            "",
        ]

        if self.key_findings:
            lines.append("## Key Findings")
            for i, finding in enumerate(self.key_findings, 1):
                lines.append(f"{i}. {finding}")
            lines.append("")

        if self.evidence:
            lines.append("## Evidence")
            lines.append("```yaml")
            if "files_viewed" in self.evidence:
                lines.append(f"files_viewed: {len(self.evidence['files_viewed'])} files")
                for f in self.evidence["files_viewed"][:10]:  # Limit to 10
                    lines.append(f"  - {f}")
                if len(self.evidence["files_viewed"]) > 10:
                    lines.append(f"  ... and {len(self.evidence['files_viewed']) - 10} more")
            if "lines_referenced" in self.evidence:
                lines.append(f"lines_referenced: {self.evidence['lines_referenced']}")
            lines.append("```")
            lines.append("")

        if self.recommendations:
            lines.append("## Recommendations")
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        if self.next_steps:
            lines.append("## Next Steps")
            for step in self.next_steps:
                lines.append(f"- [ ] {step}")
            lines.append("")

        lines.append("## Layer References")
        lines.append(f"- L3 Raw Output: `{self.l3_path}`")
        if self.related_files:
            lines.append("- Related Files:")
            for f in self.related_files[:5]:
                lines.append(f"  - `{f}`")

        return "\n".join(lines)


@dataclass
class LayerAccessDecision:
    """Decision for which layers to access."""
    task_type: TaskType
    default_layer: OutputLayer
    include_code_snippets: bool
    expansion_layer: OutputLayer
    rationale: str


class OutputLayerManager:
    """
    Manages 3-Layer Progressive-Disclosure output for subagents.

    Responsibilities:
    1. Format L1 Headlines for Main Context
    2. Generate L2 Structured Reports to .agent/outputs/
    3. Track L3 Raw Output paths in /tmp/claude/.../tasks/
    4. Decide default layer access based on task type
    """

    # Base paths
    L2_BASE_PATH = ".agent/outputs"
    L3_BASE_PATH = "/tmp/claude"

    # Token estimates
    HEADLINE_TOKENS = 50
    STRUCTURED_MIN_TOKENS = 500
    STRUCTURED_MAX_TOKENS = 2000

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize OutputLayerManager.

        Args:
            workspace_root: Root path for L2 outputs
            session_id: Claude session ID for L3 path construction
        """
        self.workspace_root = workspace_root or os.path.expanduser("~")
        self.session_id = session_id or self._detect_session_id()

        # Ensure L2 directory exists
        self._ensure_l2_directory()

        logger.info(f"OutputLayerManager initialized: workspace={self.workspace_root}")

    def _detect_session_id(self) -> str:
        """Detect Claude session ID from environment or L3 path."""
        # Check environment variable
        session_id = os.environ.get("CLAUDE_SESSION_ID", "")
        if session_id:
            return session_id

        # Try to detect from existing L3 outputs
        l3_parent = Path(self.L3_BASE_PATH)
        if l3_parent.exists():
            for item in l3_parent.iterdir():
                if item.is_dir() and item.name.startswith("-"):
                    return item.name

        return "unknown-session"

    def _ensure_l2_directory(self):
        """Ensure L2 output directory structure exists."""
        l2_path = Path(self.workspace_root) / self.L2_BASE_PATH

        # Create subdirectories for agent types
        for subdir in ["explore", "plan", "general", "audit", "evidence"]:
            (l2_path / subdir).mkdir(parents=True, exist_ok=True)

    def get_l2_path(self, agent_id: str, agent_type: str = "general") -> str:
        """Get L2 structured output path."""
        type_dir = agent_type.lower().replace("-", "_").replace(" ", "_")
        return os.path.join(
            self.workspace_root,
            self.L2_BASE_PATH,
            type_dir,
            f"{agent_id}.md"
        )

    def get_l3_path(self, agent_id: str) -> str:
        """Get L3 raw output path."""
        # Claude Code stores task outputs in /tmp/claude/{session_path}/tasks/
        session_path = self.session_id.replace("/", "-")
        return os.path.join(
            self.L3_BASE_PATH,
            session_path,
            "tasks",
            f"{agent_id}.output"
        )

    def format_headline(
        self,
        agent_id: str,
        agent_type: str,
        summary: str,
        status: AgentStatus = AgentStatus.SUCCESS,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> HeadlineResult:
        """
        Format L1 Headline for Main Context.

        Format: "{status_emoji} {Agent}[{id}]: {summary} | {metrics}"

        Args:
            agent_id: Short agent ID (e.g., "a1b2c3d")
            agent_type: Type of agent (e.g., "Explore", "Plan")
            summary: One-line summary of results
            status: Status indicator
            metrics: Optional metrics (files_count, issues_found, etc.)

        Returns:
            HeadlineResult with formatted headline
        """
        # Truncate agent_id if needed
        short_id = agent_id[:7] if len(agent_id) > 7 else agent_id

        # Build metrics string
        metrics_str = ""
        if metrics:
            parts = []
            if "files" in metrics:
                parts.append(f"{metrics['files']} files")
            if "issues" in metrics:
                parts.append(f"{metrics['issues']} issues")
            if "duration" in metrics:
                parts.append(f"{metrics['duration']}s")
            if parts:
                metrics_str = f" | {', '.join(parts)}"

        # Truncate summary to fit token budget
        max_summary_len = 60  # Approximate chars for ~50 tokens
        if len(summary) > max_summary_len:
            summary = summary[:max_summary_len - 3] + "..."

        headline = f"{status.value} {agent_type}[{short_id}]: {summary}{metrics_str}"

        return HeadlineResult(
            headline=headline,
            agent_id=agent_id,
            agent_type=agent_type,
            status=status,
            summary=summary,
            token_estimate=self.HEADLINE_TOKENS,
        )

    def write_structured_report(
        self,
        agent_id: str,
        agent_type: str,
        task_description: str,
        result: Dict[str, Any],
        status: str = "completed",
    ) -> str:
        """
        Write L2 Structured Report to .agent/outputs/.

        Args:
            agent_id: Agent ID
            agent_type: Type of agent
            task_description: Original task description
            result: Agent execution result
            status: Execution status

        Returns:
            Path to written file
        """
        # Extract information from result
        summary = result.get("summary", "No summary provided")
        key_findings = result.get("findings", result.get("key_findings", []))
        evidence = result.get("evidence", {})
        recommendations = result.get("recommendations", [])
        next_steps = result.get("next_steps", [])
        related_files = result.get("files_viewed", result.get("files_modified", []))

        # Create structured report
        report = StructuredReport(
            agent_id=agent_id,
            agent_type=agent_type,
            task_description=task_description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=status,
            summary=summary if isinstance(summary, str) else str(summary),
            key_findings=key_findings if isinstance(key_findings, list) else [str(key_findings)],
            evidence=evidence if isinstance(evidence, dict) else {"raw": evidence},
            recommendations=recommendations if isinstance(recommendations, list) else [],
            next_steps=next_steps if isinstance(next_steps, list) else [],
            l3_path=self.get_l3_path(agent_id),
            related_files=related_files if isinstance(related_files, list) else [],
        )

        # Write to file
        l2_path = self.get_l2_path(agent_id, agent_type)
        os.makedirs(os.path.dirname(l2_path), exist_ok=True)

        with open(l2_path, "w") as f:
            f.write(report.to_markdown())

        logger.info(f"L2 structured report written: {l2_path}")
        return l2_path

    def read_layer(
        self,
        agent_id: str,
        layer: OutputLayer,
        agent_type: str = "general",
    ) -> Optional[str]:
        """
        Read content from specified layer.

        Args:
            agent_id: Agent ID
            layer: Which layer to read
            agent_type: Agent type (for L2 path)

        Returns:
            Content string or None if not found
        """
        if layer == OutputLayer.L1_HEADLINE:
            # Headlines are not persisted, return None
            return None

        elif layer == OutputLayer.L2_STRUCTURED:
            path = self.get_l2_path(agent_id, agent_type)
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read()
            return None

        elif layer == OutputLayer.L3_RAW:
            path = self.get_l3_path(agent_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read()
            return None

        return None

    def decide_layer_access(
        self,
        task_type: TaskType,
        context: Optional[str] = None,
    ) -> LayerAccessDecision:
        """
        Decide which layer to access by default based on task type.

        Layer Access Decision Matrix (from Plan File):
        - 설계 (Design): L1 → L2 (full access, structure matters)
        - 계획 (Planning): L1 → L2 → L3 (need full details)
        - 실행계획 (Execution): L1 → L3 (skip L2, need raw for audit)

        Args:
            task_type: Type of task
            context: Optional additional context

        Returns:
            LayerAccessDecision with recommended layers
        """
        decisions = {
            TaskType.DESIGN: LayerAccessDecision(
                task_type=TaskType.DESIGN,
                default_layer=OutputLayer.L1_HEADLINE,
                include_code_snippets=False,
                expansion_layer=OutputLayer.L2_STRUCTURED,
                rationale="설계: 구조 파악이 중요하므로 L1 요약 후 필요시 L2 확장",
            ),
            TaskType.PLANNING: LayerAccessDecision(
                task_type=TaskType.PLANNING,
                default_layer=OutputLayer.L2_STRUCTURED,
                include_code_snippets=True,
                expansion_layer=OutputLayer.L3_RAW,
                rationale="계획: 전체 내용이 필요하므로 L2 기본, 디버그시 L3",
            ),
            TaskType.EXECUTION: LayerAccessDecision(
                task_type=TaskType.EXECUTION,
                default_layer=OutputLayer.L2_STRUCTURED,
                include_code_snippets=True,
                expansion_layer=OutputLayer.L3_RAW,
                rationale="실행계획: 상세 결과 필요, 감사 추적시 L3 접근",
            ),
        }

        return decisions.get(task_type, decisions[TaskType.PLANNING])

    def classify_task_type(self, task_description: str) -> TaskType:
        """
        Classify task type from description.

        Args:
            task_description: Task description text

        Returns:
            Classified TaskType
        """
        desc_lower = task_description.lower()

        # Design keywords
        design_keywords = [
            "설계", "아키텍처", "구조", "design", "architecture", "structure",
            "diagram", "overview", "high-level"
        ]
        if any(kw in desc_lower for kw in design_keywords):
            return TaskType.DESIGN

        # Execution keywords
        execution_keywords = [
            "실행", "구현", "implement", "execute", "run", "deploy",
            "build", "code", "write"
        ]
        if any(kw in desc_lower for kw in execution_keywords):
            return TaskType.EXECUTION

        # Default to planning
        return TaskType.PLANNING

    def list_outputs(
        self,
        agent_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List available L2 outputs.

        Args:
            agent_type: Filter by agent type
            limit: Maximum number of results

        Returns:
            List of output metadata
        """
        outputs = []
        l2_base = Path(self.workspace_root) / self.L2_BASE_PATH

        if not l2_base.exists():
            return outputs

        # Iterate through type directories
        for type_dir in l2_base.iterdir():
            if not type_dir.is_dir():
                continue

            if agent_type and type_dir.name != agent_type.lower():
                continue

            for output_file in type_dir.glob("*.md"):
                outputs.append({
                    "agent_id": output_file.stem,
                    "agent_type": type_dir.name,
                    "path": str(output_file),
                    "modified": datetime.fromtimestamp(
                        output_file.stat().st_mtime
                    ).isoformat(),
                })

                if len(outputs) >= limit:
                    return outputs

        # Sort by modification time (newest first)
        outputs.sort(key=lambda x: x["modified"], reverse=True)
        return outputs[:limit]

    def cleanup_old_outputs(
        self,
        max_age_hours: int = 24,
        agent_type: Optional[str] = None,
    ) -> List[str]:
        """
        Remove outputs older than specified age.

        Args:
            max_age_hours: Maximum age in hours
            agent_type: Optional filter by agent type

        Returns:
            List of removed file paths
        """
        removed = []
        l2_base = Path(self.workspace_root) / self.L2_BASE_PATH
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        if not l2_base.exists():
            return removed

        for type_dir in l2_base.iterdir():
            if not type_dir.is_dir():
                continue

            if agent_type and type_dir.name != agent_type.lower():
                continue

            for output_file in type_dir.glob("*.md"):
                if output_file.stat().st_mtime < cutoff:
                    output_file.unlink()
                    removed.append(str(output_file))

        if removed:
            logger.info(f"Cleaned up {len(removed)} old L2 outputs")

        return removed


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────

def format_agent_headline(
    agent_id: str,
    agent_type: str,
    summary: str,
    success: bool = True,
    metrics: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Quick function to format agent headline.

    Usage:
        headline = format_agent_headline("a1b2c3d", "Explore", "8 files scanned")
    """
    manager = OutputLayerManager()
    status = AgentStatus.SUCCESS if success else AgentStatus.ERROR
    result = manager.format_headline(agent_id, agent_type, summary, status, metrics)
    return result.headline


def save_structured_output(
    agent_id: str,
    agent_type: str,
    task: str,
    result: Dict[str, Any],
) -> str:
    """
    Quick function to save structured output.

    Returns path to saved file.
    """
    manager = OutputLayerManager()
    return manager.write_structured_report(agent_id, agent_type, task, result)


def get_layer_for_task(task_description: str) -> Tuple[OutputLayer, str]:
    """
    Get recommended layer for task type.

    Returns (layer, rationale).
    """
    manager = OutputLayerManager()
    task_type = manager.classify_task_type(task_description)
    decision = manager.decide_layer_access(task_type)
    return decision.default_layer, decision.rationale


# Module-level singleton
_output_manager: Optional[OutputLayerManager] = None


def get_output_manager() -> OutputLayerManager:
    """Get or create session-wide OutputLayerManager."""
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputLayerManager()
    return _output_manager


# ─────────────────────────────────────────────────────────────────────────────
# V2.1.7: Automatic Result Validation Methods
# ─────────────────────────────────────────────────────────────────────────────

# Summary detection patterns
SUMMARY_INDICATORS = [
    r"^\s*✅\s+\w+\[",             # L1 Headline format
    r"^\s*⚠️\s+\w+\[",
    r"^\s*❌\s+\w+\[",
    r"summary\s*only",
    r"truncated",
    r"\.{3}\s*$",
    r"see\s+(L2|L3|full|detailed)",
    r"abbreviated",
]

COMPLETENESS_INDICATORS = [
    r"files_viewed\s*[=:]\s*\[",
    r"lines_referenced",
    r"## Critical Findings",
    r"## Recommendations",
    r"## Evidence",
]

MIN_COMPLETE_CHARS = 500
MIN_COMPLETE_LINES = 20


def is_summary_only(result: str) -> Tuple[bool, List[str]]:
    """
    Detect if result is a summary/headline rather than complete output.

    This is the core detection function for the automatic result verification
    system. It checks multiple indicators to determine if a subagent result
    is just a summary that needs L2/L3 access for full details.

    Args:
        result: The subagent result text to analyze

    Returns:
        Tuple of (is_summary: bool, reasons: List[str])

    Usage:
        is_summary, reasons = is_summary_only(task_result)
        if is_summary:
            l2_content = read_layer_auto(agent_id)

    Example:
        >>> is_summary, reasons = is_summary_only("✅ Explore[a1b2c3d]: 8 files found")
        >>> print(is_summary)  # True
        >>> print(reasons)     # ['pattern:✅ Explore[', 'short_chars:35']
    """
    reasons = []

    if not result or len(result.strip()) < 50:
        return True, ["empty_or_too_short"]

    # Check for summary indicators
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
    completeness_score = 0
    for pattern in COMPLETENESS_INDICATORS:
        if re.search(pattern, result, re.IGNORECASE | re.MULTILINE):
            completeness_score += 1

    if completeness_score >= 2:
        return False, []

    if reasons and completeness_score < 2:
        return True, reasons

    return False, []


def read_layer_auto(
    agent_id: str,
    agent_type: str = "general",
    workspace_root: Optional[str] = None,
) -> Optional[str]:
    """
    Automatically read the best available layer (L2 → L3 fallback).

    This function implements the automatic layer access pattern for the
    result verification system. It tries L2 first (structured, ~2000 tokens),
    then falls back to L3 if L2 is not available.

    Args:
        agent_id: The subagent ID (e.g., "a1b2c3d")
        agent_type: Type of agent for L2 path (e.g., "explore", "plan")
        workspace_root: Optional workspace root for L2 path

    Returns:
        Content from L2 or L3, or None if neither found

    Usage:
        is_summary, _ = is_summary_only(result)
        if is_summary:
            detailed = read_layer_auto(agent_id, "explore")
            if detailed:
                return detailed
            else:
                return re_delegate_task(agent_id)

    Layer Priority:
        1. L2 Structured Report (.agent/outputs/{type}/{id}.md) - ~2000 tokens
        2. L3 Raw Output (/tmp/claude/.../tasks/{id}.output) - Full output
    """
    manager = get_output_manager()
    if workspace_root:
        manager.workspace_root = workspace_root

    # Try L2 first (preferred - structured and smaller)
    l2_content = manager.read_layer(agent_id, OutputLayer.L2_STRUCTURED, agent_type)
    if l2_content:
        return l2_content

    # Fallback to L3 (full raw output)
    l3_content = manager.read_layer(agent_id, OutputLayer.L3_RAW, agent_type)
    if l3_content:
        return l3_content

    return None


def verify_subagent_result(
    result: str,
    agent_id: str,
    agent_type: str = "general",
) -> Tuple[str, str]:
    """
    Verify subagent result completeness and return detailed content if needed.

    This is the main entry point for the automatic result verification system.
    It checks if the result is a summary, and if so, automatically retrieves
    the detailed L2/L3 content.

    Args:
        result: The subagent result to verify
        agent_id: The subagent ID
        agent_type: Type of agent

    Returns:
        Tuple of (verified_result, status)
        - verified_result: Either the original result or L2/L3 content
        - status: "complete" | "l2_accessed" | "l3_accessed" | "needs_redelegation"

    Usage:
        result, status = verify_subagent_result(task_output, agent_id)
        if status == "needs_redelegation":
            Task(resume=agent_id, prompt="Continue and provide full results")

    Example Flow:
        1. Main Agent receives Task result
        2. Call verify_subagent_result(result, agent_id)
        3. If status == "complete": proceed with result
        4. If status == "l2_accessed": use returned detailed content
        5. If status == "needs_redelegation": re-delegate task
    """
    # Check if summary only
    is_summary, reasons = is_summary_only(result)

    if not is_summary:
        return result, "complete"

    # Try to get detailed content
    manager = get_output_manager()

    # Try L2
    l2_content = manager.read_layer(agent_id, OutputLayer.L2_STRUCTURED, agent_type)
    if l2_content:
        return l2_content, "l2_accessed"

    # Try L3
    l3_content = manager.read_layer(agent_id, OutputLayer.L3_RAW, agent_type)
    if l3_content:
        return l3_content, "l3_accessed"

    # No detailed content available
    return result, "needs_redelegation"


def extract_agent_id_from_result(result: str) -> Optional[str]:
    """
    Extract agent ID from a subagent result.

    Tries multiple patterns to find the agent ID in the result text.

    Args:
        result: The subagent result text

    Returns:
        Agent ID string or None if not found

    Patterns tried:
        1. L1 headline format: "✅ Explore[a1b2c3d]:"
        2. agent_id field: "agent_id: a1b2c3d"
        3. ID in brackets: "[a1b2c3d]"
    """
    # Try L1 headline format
    match = re.search(r'\[([a-f0-9]{7,})\]', result)
    if match:
        return match.group(1)

    # Try agent_id field
    match = re.search(r'agent_id["\s:=]+([a-f0-9-]{7,})', result, re.IGNORECASE)
    if match:
        return match.group(1)

    return None
