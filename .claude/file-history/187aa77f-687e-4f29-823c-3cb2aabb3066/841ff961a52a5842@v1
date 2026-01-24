"""
Orion ODA v3.0 - Plan File Model
================================

Bidirectional Markdown <-> Python synchronization for Plan Files.

This module provides:
- PlanFile dataclass representing .agent/plans/{slug}.md
- from_markdown() parser for markdown -> PlanFile
- to_markdown() serializer for PlanFile -> markdown
- Automatic status tracking and updates

Usage:
    # Load existing plan
    plan = PlanFile.from_markdown(Path(".agent/plans/my_plan.md").read_text())

    # Update status
    plan.update_phase_status(1, "completed")
    plan.add_agent("a1b2c3d", 2, "Explore")

    # Save changes
    Path(".agent/plans/my_plan.md").write_text(plan.to_markdown())
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class PlanStatus(str, Enum):
    """Plan execution status."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class PhaseStatus(str, Enum):
    """Phase execution status."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PlanMetadata:
    """Plan file metadata from blockquote header."""
    version: str = "1.0"
    status: PlanStatus = PlanStatus.PENDING_APPROVAL
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    auto_compact_safe: bool = True


@dataclass
class Overview:
    """Overview section data."""
    complexity: str = "medium"
    total_phases: int = 0
    files_affected: int = 0
    new_files: int = 0
    modified_files: int = 0


@dataclass
class Requirement:
    """Single requirement entry."""
    id: str  # e.g., "R1"
    description: str
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW


@dataclass
class PhaseTask:
    """Task within a phase."""
    description: str
    completed: bool = False


@dataclass
class Phase:
    """Plan phase definition."""
    number: int
    name: str
    goal: str = ""
    effort: str = "medium"  # trivial, small, medium, large, xlarge
    dependencies: List[str] = field(default_factory=list)
    tasks: List[PhaseTask] = field(default_factory=list)
    files_affected: List[str] = field(default_factory=list)
    status: PhaseStatus = PhaseStatus.PENDING
    agent_id: Optional[str] = None


@dataclass
class AgentEntry:
    """Agent registry entry for resume tracking."""
    task: str
    agent_id: str
    status: AgentStatus = AgentStatus.PENDING
    resume_eligible: bool = True


@dataclass
class ProgressEntry:
    """Progress tracking entry per phase."""
    phase_name: str
    total_tasks: int
    completed_tasks: int
    status: PhaseStatus


@dataclass
class PlanFile:
    """
    In-memory representation of .agent/plans/{slug}.md

    Supports bidirectional sync:
    - from_markdown(): Parse markdown -> PlanFile
    - to_markdown(): Serialize PlanFile -> markdown
    """

    # Core fields
    title: str
    path: Optional[str] = None
    metadata: PlanMetadata = field(default_factory=PlanMetadata)
    overview: Overview = field(default_factory=Overview)

    # Content sections
    requirements: List[Requirement] = field(default_factory=list)
    phases: List[Phase] = field(default_factory=list)
    agents: List[AgentEntry] = field(default_factory=list)

    # Progress tracking
    progress: List[ProgressEntry] = field(default_factory=list)

    # Raw sections (preserved for round-trip)
    _analysis_summary: str = ""
    _critical_file_paths: str = ""
    _risk_register: str = ""
    _success_criteria: str = ""
    _quick_resume: str = ""
    _execution_strategy: str = ""

    # ==========================================================================
    # Class Methods - Parsing
    # ==========================================================================

    @classmethod
    def from_markdown(cls, content: str, path: Optional[str] = None) -> "PlanFile":
        """
        Parse markdown content into PlanFile.

        Args:
            content: Raw markdown content
            path: Optional file path for reference

        Returns:
            Parsed PlanFile instance
        """
        plan = cls(title="", path=path)

        # Parse title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            plan.title = title_match.group(1).strip()

        # Parse metadata blockquote
        plan.metadata = cls._parse_metadata(content)

        # Parse overview table
        plan.overview = cls._parse_overview(content)

        # Parse requirements table
        plan.requirements = cls._parse_requirements(content)

        # Parse phases
        plan.phases = cls._parse_phases(content)

        # Parse agent registry
        plan.agents = cls._parse_agent_registry(content)

        # Parse progress tracking
        plan.progress = cls._parse_progress(content)

        # Preserve raw sections for round-trip
        plan._analysis_summary = cls._extract_section(content, "Analysis Summary")
        plan._critical_file_paths = cls._extract_section(content, "Critical File Paths")
        plan._risk_register = cls._extract_section(content, "Risk Register")
        plan._success_criteria = cls._extract_section(content, "Success Criteria")
        plan._quick_resume = cls._extract_section(content, "Quick Resume After Auto-Compact")
        plan._execution_strategy = cls._extract_section(content, "Execution Strategy")

        return plan

    @classmethod
    def _parse_metadata(cls, content: str) -> PlanMetadata:
        """Parse metadata from blockquote header."""
        meta = PlanMetadata()

        # Match: > **Version:** 1.0 | **Status:** PENDING_APPROVAL | **Date:** 2026-01-18
        blockquote_pattern = r'>\s*\*\*Version:\*\*\s*([^\|]+)\|\s*\*\*Status:\*\*\s*([^\|]+)\|\s*\*\*Date:\*\*\s*(\S+)'
        match = re.search(blockquote_pattern, content)

        if match:
            meta.version = match.group(1).strip()
            status_str = match.group(2).strip()
            try:
                meta.status = PlanStatus(status_str)
            except ValueError:
                meta.status = PlanStatus.PENDING_APPROVAL
            meta.date = match.group(3).strip()

        return meta

    @classmethod
    def _parse_overview(cls, content: str) -> Overview:
        """Parse overview table."""
        overview = Overview()

        # Find Overview section
        section = cls._extract_section(content, "Overview")
        if not section:
            return overview

        # Parse table rows
        row_pattern = r'\|\s*(\w+(?:\s+\w+)*)\s*\|\s*(\d+|\w+)\s*\|'
        for match in re.finditer(row_pattern, section):
            key = match.group(1).lower().replace(" ", "_")
            value = match.group(2)

            if key == "complexity":
                overview.complexity = value
            elif key == "total_phases":
                overview.total_phases = int(value)
            elif key == "files_affected":
                overview.files_affected = int(value)
            elif key == "new_files":
                overview.new_files = int(value)
            elif key == "modified_files":
                overview.modified_files = int(value)

        return overview

    @classmethod
    def _parse_requirements(cls, content: str) -> List[Requirement]:
        """Parse requirements table."""
        requirements = []

        section = cls._extract_section(content, "Requirements")
        if not section:
            return requirements

        # Match: | R1 | Description | HIGH |
        row_pattern = r'\|\s*(R\d+)\s*\|\s*([^|]+)\|\s*(\w+)\s*\|'
        for match in re.finditer(row_pattern, section):
            requirements.append(Requirement(
                id=match.group(1).strip(),
                description=match.group(2).strip(),
                priority=match.group(3).strip()
            ))

        return requirements

    @classmethod
    def _parse_phases(cls, content: str) -> List[Phase]:
        """Parse phase sections."""
        phases = []

        # Find all phase headers: ### Phase N: Name
        phase_pattern = r'###\s+Phase\s+(\d+):\s+(.+?)(?=\n)'
        phase_matches = list(re.finditer(phase_pattern, content))

        for i, match in enumerate(phase_matches):
            phase_num = int(match.group(1))
            phase_name = match.group(2).strip()

            # Get phase content (until next phase or section)
            start = match.end()
            if i + 1 < len(phase_matches):
                end = phase_matches[i + 1].start()
            else:
                # Find next ## section
                next_section = re.search(r'\n##\s+[^#]', content[start:])
                end = start + next_section.start() if next_section else len(content)

            phase_content = content[start:end]

            phase = Phase(number=phase_num, name=phase_name)

            # Parse phase table (Goal, Effort, Dependencies)
            goal_match = re.search(r'\|\s*\*\*Goal\*\*\s*\|\s*([^|]+)\|', phase_content)
            if goal_match:
                phase.goal = goal_match.group(1).strip()

            effort_match = re.search(r'\|\s*\*\*Effort\*\*\s*\|\s*(\w+)\s*\|', phase_content)
            if effort_match:
                phase.effort = effort_match.group(1).strip()

            deps_match = re.search(r'\|\s*\*\*Dependencies\*\*\s*\|\s*([^|]+)\|', phase_content)
            if deps_match:
                deps_str = deps_match.group(1).strip()
                if deps_str.lower() != "none":
                    phase.dependencies = [d.strip() for d in deps_str.split(",")]

            # Parse tasks (numbered list)
            tasks_pattern = r'^\d+\.\s+(.+)$'
            for task_match in re.finditer(tasks_pattern, phase_content, re.MULTILINE):
                task_desc = task_match.group(1).strip()
                # Check if task is marked complete (has [x])
                completed = task_desc.startswith("[x]") or task_desc.startswith("[X]")
                if completed:
                    task_desc = task_desc[3:].strip()
                phase.tasks.append(PhaseTask(description=task_desc, completed=completed))

            # Parse files affected
            files_pattern = r'-\s*(?:NEW|MODIFY):\s*`([^`]+)`'
            for file_match in re.finditer(files_pattern, phase_content):
                phase.files_affected.append(file_match.group(1))

            phases.append(phase)

        return phases

    @classmethod
    def _parse_agent_registry(cls, content: str) -> List[AgentEntry]:
        """Parse Agent Registry table."""
        agents = []

        section = cls._extract_section(content, "Agent Registry")
        if not section:
            return agents

        # Match: | Task | agent_id | status | resume_eligible |
        row_pattern = r'\|\s*([^|]+)\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(Yes|No)\s*\|'
        for match in re.finditer(row_pattern, section, re.IGNORECASE):
            task = match.group(1).strip()
            if task.lower() == "task":  # Skip header row
                continue

            status_str = match.group(3).strip().lower()
            try:
                status = AgentStatus(status_str)
            except ValueError:
                status = AgentStatus.PENDING

            agents.append(AgentEntry(
                task=task,
                agent_id=match.group(2).strip(),
                status=status,
                resume_eligible=match.group(4).strip().lower() == "yes"
            ))

        return agents

    @classmethod
    def _parse_progress(cls, content: str) -> List[ProgressEntry]:
        """Parse Progress Tracking table."""
        progress = []

        section = cls._extract_section(content, "Progress Tracking")
        if not section:
            return progress

        # Match: | Phase N: Name | total | completed | STATUS |
        row_pattern = r'\|\s*Phase\s+\d+:\s+([^|]+)\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\w+)\s*\|'
        for match in re.finditer(row_pattern, section):
            status_str = match.group(4).strip().upper()
            try:
                status = PhaseStatus(status_str)
            except ValueError:
                status = PhaseStatus.PENDING

            progress.append(ProgressEntry(
                phase_name=match.group(1).strip(),
                total_tasks=int(match.group(2)),
                completed_tasks=int(match.group(3)),
                status=status
            ))

        return progress

    @classmethod
    def _extract_section(cls, content: str, section_name: str) -> str:
        """Extract content of a section by name."""
        # Find section header (## or ###)
        pattern = rf'(?:^|\n)(##\s*{re.escape(section_name)}[^\n]*)\n([\s\S]*?)(?=\n##\s|$)'
        match = re.search(pattern, content)
        if match:
            return match.group(0)
        return ""

    # ==========================================================================
    # Instance Methods - Serialization
    # ==========================================================================

    def to_markdown(self) -> str:
        """
        Serialize PlanFile to markdown.

        Returns:
            Formatted markdown string
        """
        lines = []

        # Title
        lines.append(f"# {self.title}")
        lines.append("")

        # Metadata blockquote
        lines.append(f"> **Version:** {self.metadata.version} | **Status:** {self.metadata.status.value} | **Date:** {self.metadata.date}")
        if self.metadata.auto_compact_safe:
            lines.append("> **Auto-Compact Safe:** This file persists across context compaction")
        lines.append("")

        # Overview
        lines.append("## Overview")
        lines.append("")
        lines.append("| Item | Value |")
        lines.append("|------|-------|")
        lines.append(f"| Complexity | {self.overview.complexity} |")
        lines.append(f"| Total Phases | {self.overview.total_phases} |")
        lines.append(f"| Files Affected | {self.overview.files_affected} |")
        lines.append(f"| New Files | {self.overview.new_files} |")
        lines.append(f"| Modified Files | {self.overview.modified_files} |")
        lines.append("")

        # Requirements
        if self.requirements:
            lines.append("## Requirements")
            lines.append("")
            lines.append("| # | Requirement | Priority |")
            lines.append("|---|-------------|----------|")
            for req in self.requirements:
                lines.append(f"| {req.id} | {req.description} | {req.priority} |")
            lines.append("")

        # Analysis Summary (preserved)
        if self._analysis_summary:
            lines.append(self._analysis_summary.strip())
            lines.append("")

        # Phases
        if self.phases:
            lines.append("## Phases")
            lines.append("")

            for phase in self.phases:
                lines.append(f"### Phase {phase.number}: {phase.name}")
                lines.append("| Item | Detail |")
                lines.append("|------|--------|")
                lines.append(f"| **Goal** | {phase.goal} |")
                lines.append(f"| **Effort** | {phase.effort} |")
                deps = ", ".join(phase.dependencies) if phase.dependencies else "None"
                lines.append(f"| **Dependencies** | {deps} |")
                lines.append("")

                if phase.tasks:
                    lines.append("**Tasks:**")
                    for i, task in enumerate(phase.tasks, 1):
                        checkbox = "[x]" if task.completed else ""
                        lines.append(f"{i}. {checkbox} {task.description}".strip())
                    lines.append("")

                if phase.files_affected:
                    lines.append("**Files Affected:**")
                    for f in phase.files_affected:
                        lines.append(f"- `{f}`")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # Critical File Paths (preserved)
        if self._critical_file_paths:
            lines.append(self._critical_file_paths.strip())
            lines.append("")

        # Risk Register (preserved)
        if self._risk_register:
            lines.append(self._risk_register.strip())
            lines.append("")

        # Success Criteria (preserved)
        if self._success_criteria:
            lines.append(self._success_criteria.strip())
            lines.append("")

        # Progress Tracking
        lines.append("## Progress Tracking")
        lines.append("")
        lines.append("| Phase | Tasks | Completed | Status |")
        lines.append("|-------|-------|-----------|--------|")
        for phase in self.phases:
            completed = sum(1 for t in phase.tasks if t.completed)
            total = len(phase.tasks)
            lines.append(f"| Phase {phase.number}: {phase.name} | {total} | {completed} | {phase.status.value} |")
        lines.append("")

        # Quick Resume (preserved)
        if self._quick_resume:
            lines.append(self._quick_resume.strip())
            lines.append("")

        # Agent Registry
        lines.append("## Agent Registry (Auto-Compact Resume)")
        lines.append("")
        lines.append("| Task | Agent ID | Status | Resume Eligible |")
        lines.append("|------|----------|--------|-----------------|")
        for agent in self.agents:
            resume = "Yes" if agent.resume_eligible else "No"
            lines.append(f"| {agent.task} | {agent.agent_id} | {agent.status.value} | {resume} |")
        lines.append("")

        # Execution Strategy (preserved)
        if self._execution_strategy:
            lines.append(self._execution_strategy.strip())
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("> **Approval Required:** Proceed with this plan?")
        lines.append("")

        return "\n".join(lines)

    # ==========================================================================
    # Instance Methods - Updates
    # ==========================================================================

    def update_phase_status(self, phase_num: int, status: PhaseStatus) -> None:
        """Update status of a specific phase."""
        for phase in self.phases:
            if phase.number == phase_num:
                phase.status = status
                break

    def complete_task(self, phase_num: int, task_index: int) -> None:
        """Mark a task as completed."""
        for phase in self.phases:
            if phase.number == phase_num:
                if 0 <= task_index < len(phase.tasks):
                    phase.tasks[task_index].completed = True
                break

    def add_agent(
        self,
        agent_id: str,
        task: str,
        status: AgentStatus = AgentStatus.PENDING,
        resume_eligible: bool = True
    ) -> None:
        """Add or update agent entry."""
        # Check if agent already exists
        for agent in self.agents:
            if agent.agent_id == agent_id:
                agent.status = status
                agent.resume_eligible = resume_eligible
                return

        # Add new agent
        self.agents.append(AgentEntry(
            task=task,
            agent_id=agent_id,
            status=status,
            resume_eligible=resume_eligible
        ))

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> None:
        """Update agent status by ID."""
        for agent in self.agents:
            if agent.agent_id == agent_id:
                agent.status = status
                if status == AgentStatus.COMPLETED:
                    agent.resume_eligible = False
                break

    def get_resumable_agents(self) -> List[AgentEntry]:
        """Get list of agents eligible for resume."""
        return [a for a in self.agents if a.resume_eligible and a.status != AgentStatus.COMPLETED]

    def set_status(self, status: PlanStatus) -> None:
        """Update overall plan status."""
        self.metadata.status = status

    def save(self, path: Optional[str] = None) -> None:
        """
        Save plan to file.

        Args:
            path: File path (uses self.path if not provided)
        """
        save_path = path or self.path
        if not save_path:
            raise ValueError("No path specified for save")

        # Atomic write via temp file
        import tempfile
        import shutil

        target = Path(save_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(self.to_markdown())
            tmp_path = tmp.name

        shutil.move(tmp_path, target)

    @classmethod
    def load(cls, path: str) -> "PlanFile":
        """
        Load plan from file.

        Args:
            path: File path to load

        Returns:
            Loaded PlanFile instance
        """
        content = Path(path).read_text()
        return cls.from_markdown(content, path=path)


# =============================================================================
# Convenience Functions
# =============================================================================

def load_plan(path: str) -> PlanFile:
    """Load plan file from path."""
    return PlanFile.load(path)


def create_plan(
    title: str,
    phases: List[Dict[str, Any]],
    requirements: Optional[List[Dict[str, Any]]] = None,
    complexity: str = "medium",
) -> PlanFile:
    """
    Create a new plan file programmatically.

    Args:
        title: Plan title
        phases: List of phase definitions
        requirements: Optional list of requirements
        complexity: Plan complexity

    Returns:
        New PlanFile instance
    """
    plan = PlanFile(title=title)
    plan.overview.complexity = complexity
    plan.overview.total_phases = len(phases)

    if requirements:
        for i, req in enumerate(requirements, 1):
            plan.requirements.append(Requirement(
                id=f"R{i}",
                description=req.get("description", ""),
                priority=req.get("priority", "MEDIUM")
            ))

    for phase_def in phases:
        phase = Phase(
            number=phase_def.get("number", len(plan.phases) + 1),
            name=phase_def.get("name", ""),
            goal=phase_def.get("goal", ""),
            effort=phase_def.get("effort", "medium"),
            dependencies=phase_def.get("dependencies", []),
        )

        for task_desc in phase_def.get("tasks", []):
            phase.tasks.append(PhaseTask(description=task_desc))

        phase.files_affected = phase_def.get("files", [])
        plan.phases.append(phase)

    return plan


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    "PlanStatus",
    "PhaseStatus",
    "AgentStatus",
    # Dataclasses
    "PlanMetadata",
    "Overview",
    "Requirement",
    "PhaseTask",
    "Phase",
    "AgentEntry",
    "ProgressEntry",
    "PlanFile",
    # Functions
    "load_plan",
    "create_plan",
]
