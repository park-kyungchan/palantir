"""
ODA Hybrid Execution Model
==========================

V2.1.11 Feature: Dependency-aware parallel execution with L2 Synthesis.

This module provides:
1. DependencyAnalyzer - Analyzes phase dependencies to identify parallel groups
2. HybridExecutor - Executes phases in optimized parallel groups with L2 synthesis
3. ExecutionGroup - Represents a group of independent phases for parallel execution

The Hybrid Execution Model combines:
- Sequential execution (for dependent phases)
- Parallel execution (for independent phases)
- L2 Synthesizer (for context-efficient result aggregation)

Usage:
    from lib.oda.planning.hybrid_execution import (
        HybridExecutor,
        DependencyAnalyzer,
        analyze_dependencies,
    )

    # Quick analysis
    groups = analyze_dependencies(phases)

    # Full executor
    executor = HybridExecutor()
    result = executor.execute(phases)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import re


class ExecutionMode(str, Enum):
    """Execution mode for phases."""
    PARALLEL = "parallel"     # Independent phases, run with run_in_background=True
    SEQUENTIAL = "sequential" # Dependent phases, run one at a time


@dataclass
class Phase:
    """
    Represents an execution phase.

    Attributes:
        id: Unique phase identifier
        description: Human-readable description
        subagent_type: Type of subagent to use
        dependencies: List of phase IDs this phase depends on
        files: Files affected by this phase
        keywords: Keywords for dependency detection
    """
    id: str
    description: str
    subagent_type: str
    dependencies: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    budget: int = 5000

    @classmethod
    def from_plan_task(cls, task: Dict[str, Any], index: int) -> "Phase":
        """
        Create Phase from plan file task dict.

        Args:
            task: Task dictionary from plan file
            index: Task index for ID generation

        Returns:
            Phase instance
        """
        return cls(
            id=f"phase_{index + 1}",
            description=task.get("description", task.get("name", f"Phase {index + 1}")),
            subagent_type=task.get("subagent", "general-purpose"),
            dependencies=task.get("dependencies", []),
            files=task.get("files", task.get("files_affected", [])),
            keywords=cls._extract_keywords(task.get("description", "")),
            budget=task.get("budget", 5000),
        )

    @staticmethod
    def _extract_keywords(description: str) -> List[str]:
        """Extract keywords for dependency detection."""
        keywords = []
        # Extract words after common verbs
        patterns = [
            r"(?:analyze|create|modify|update|implement|test)\s+(\w+)",
            r"(\w+)\s+(?:module|component|service|class|function)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, description.lower())
            keywords.extend(matches)
        return keywords


@dataclass
class ExecutionGroup:
    """
    A group of phases that can be executed together.

    Parallel groups have independent phases that can run with run_in_background=True.
    Sequential groups have a single phase that must complete before others start.
    """
    mode: ExecutionMode
    phases: List[Phase]
    group_id: int

    @property
    def is_parallel(self) -> bool:
        """Check if this group can be executed in parallel."""
        return self.mode == ExecutionMode.PARALLEL and len(self.phases) > 1

    @property
    def phase_ids(self) -> List[str]:
        """Get list of phase IDs in this group."""
        return [p.id for p in self.phases]

    def get_task_params(self) -> List[Dict[str, Any]]:
        """
        Generate Task() parameters for each phase.

        Returns:
            List of dicts ready for Task tool invocation
        """
        params_list = []
        for phase in self.phases:
            params = {
                "subagent_type": phase.subagent_type,
                "prompt": self._generate_prompt(phase),
                "description": f"[Group {self.group_id}] {phase.description[:30]}",
                "run_in_background": self.is_parallel,
            }
            params_list.append(params)
        return params_list

    def _generate_prompt(self, phase: Phase) -> str:
        """Generate execution prompt for phase."""
        return f'''## Task
{phase.description}

## Scope
Files: {", ".join(phase.files) if phase.files else "As determined by analysis"}

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED {phase.budget} TOKENS.

## Required Output
- files_viewed: [list of examined files]
- changes_made: [modifications performed] OR findings: [analysis results]
- evidence: [specific file:line references]

## Format
Return structured JSON for L2 synthesis compatibility.
'''


class DependencyAnalyzer:
    """
    Analyzes phase dependencies to create optimal execution groups.

    Uses multiple strategies to detect dependencies:
    1. Explicit dependencies in phase definition
    2. File overlap detection
    3. Keyword matching (e.g., "implement X" depends on "design X")

    Attributes:
        phases: List of phases to analyze
        dependency_graph: Computed dependency relationships
    """

    # Keywords that indicate creation (other phases may depend on these)
    CREATION_KEYWORDS = ["create", "design", "plan", "define", "setup", "initialize"]

    # Keywords that indicate consumption (depends on creation phases)
    CONSUMPTION_KEYWORDS = ["implement", "use", "integrate", "test", "verify", "update"]

    def __init__(self, phases: Optional[List[Phase]] = None):
        """
        Initialize dependency analyzer.

        Args:
            phases: Optional list of phases to analyze
        """
        self.phases = phases or []
        self.dependency_graph: Dict[str, Set[str]] = {}

    def analyze(self, phases: Optional[List[Phase]] = None) -> List[ExecutionGroup]:
        """
        Analyze dependencies and create execution groups.

        Args:
            phases: List of phases to analyze (uses stored phases if None)

        Returns:
            List of ExecutionGroups in execution order
        """
        if phases:
            self.phases = phases

        if not self.phases:
            return []

        # Build dependency graph
        self._build_dependency_graph()

        # Create execution groups using topological sort
        groups = self._create_execution_groups()

        return groups

    def _build_dependency_graph(self) -> None:
        """Build dependency graph from phases."""
        self.dependency_graph = {p.id: set(p.dependencies) for p in self.phases}

        # Detect implicit dependencies
        for phase in self.phases:
            implicit = self._detect_implicit_dependencies(phase)
            self.dependency_graph[phase.id].update(implicit)

    def _detect_implicit_dependencies(self, phase: Phase) -> Set[str]:
        """
        Detect implicit dependencies based on keywords and files.

        Args:
            phase: Phase to analyze

        Returns:
            Set of phase IDs that this phase implicitly depends on
        """
        implicit: Set[str] = set()
        desc_lower = phase.description.lower()

        # Check if this phase consumes something
        is_consumer = any(kw in desc_lower for kw in self.CONSUMPTION_KEYWORDS)

        if is_consumer:
            for other in self.phases:
                if other.id == phase.id:
                    continue

                other_desc_lower = other.description.lower()
                is_creator = any(kw in other_desc_lower for kw in self.CREATION_KEYWORDS)

                if is_creator:
                    # Check for keyword overlap
                    if self._keywords_overlap(phase, other):
                        implicit.add(other.id)

                    # Check for file overlap
                    if self._files_overlap(phase, other):
                        implicit.add(other.id)

        return implicit

    def _keywords_overlap(self, phase1: Phase, phase2: Phase) -> bool:
        """Check if two phases have overlapping keywords."""
        kw1 = set(phase1.keywords)
        kw2 = set(phase2.keywords)

        # Also extract from description
        for word in phase1.description.lower().split():
            if len(word) > 4:  # Skip short words
                kw1.add(word)
        for word in phase2.description.lower().split():
            if len(word) > 4:
                kw2.add(word)

        return bool(kw1 & kw2)

    def _files_overlap(self, phase1: Phase, phase2: Phase) -> bool:
        """Check if two phases affect the same files."""
        files1 = set(phase1.files)
        files2 = set(phase2.files)
        return bool(files1 & files2)

    def _create_execution_groups(self) -> List[ExecutionGroup]:
        """
        Create execution groups using modified topological sort.

        Phases with no dependencies OR all dependencies in previous groups
        can be executed in parallel within the same group.
        """
        groups: List[ExecutionGroup] = []
        completed: Set[str] = set()
        remaining = {p.id for p in self.phases}
        phase_map = {p.id: p for p in self.phases}
        group_id = 1

        while remaining:
            # Find phases whose dependencies are all completed
            ready: List[Phase] = []
            for phase_id in remaining:
                deps = self.dependency_graph.get(phase_id, set())
                if deps <= completed:  # All dependencies satisfied
                    ready.append(phase_map[phase_id])

            if not ready:
                # Circular dependency or error - take first remaining
                first_id = next(iter(remaining))
                ready = [phase_map[first_id]]

            # Create group based on number of ready phases
            if len(ready) > 1:
                mode = ExecutionMode.PARALLEL
            else:
                mode = ExecutionMode.SEQUENTIAL

            group = ExecutionGroup(
                mode=mode,
                phases=ready,
                group_id=group_id,
            )
            groups.append(group)

            # Mark as completed
            for phase in ready:
                completed.add(phase.id)
                remaining.discard(phase.id)

            group_id += 1

        return groups

    def get_dependency_summary(self) -> Dict[str, Any]:
        """
        Get human-readable dependency summary.

        Returns:
            Dict with dependency analysis results
        """
        return {
            "total_phases": len(self.phases),
            "dependency_graph": {
                k: list(v) for k, v in self.dependency_graph.items()
            },
            "independent_phases": [
                p.id for p in self.phases
                if not self.dependency_graph.get(p.id)
            ],
            "dependent_phases": [
                p.id for p in self.phases
                if self.dependency_graph.get(p.id)
            ],
        }


class HybridExecutor:
    """
    Executes phases using the Hybrid Execution Model.

    Combines:
    1. Dependency analysis to identify parallel opportunities
    2. Parallel execution for independent phases
    3. L2 Synthesizer for context-efficient result aggregation

    Usage:
        executor = HybridExecutor()

        # Get execution plan
        plan = executor.plan(phases)

        # Generate Task params for a group
        task_params = executor.get_group_task_params(group)

        # After group completion, get synthesis config
        synthesis = executor.get_synthesis_config(group, agent_ids)
    """

    def __init__(self):
        """Initialize Hybrid Executor."""
        self.analyzer = DependencyAnalyzer()
        self.groups: List[ExecutionGroup] = []
        self.agent_registry: Dict[str, Dict[str, Any]] = {}

    def plan(self, phases: List[Phase]) -> List[ExecutionGroup]:
        """
        Create execution plan from phases.

        Args:
            phases: List of phases to execute

        Returns:
            List of ExecutionGroups in optimal order
        """
        self.groups = self.analyzer.analyze(phases)
        return self.groups

    def get_group_task_params(self, group: ExecutionGroup) -> List[Dict[str, Any]]:
        """
        Get Task() parameters for all phases in a group.

        Args:
            group: Execution group to process

        Returns:
            List of Task parameter dicts
        """
        return group.get_task_params()

    def register_agent(
        self,
        phase_id: str,
        agent_id: str,
        agent_type: str,
        group_id: int,
    ) -> None:
        """
        Register deployed agent for tracking and synthesis.

        Args:
            phase_id: Phase identifier
            agent_id: Deployed agent ID
            agent_type: Subagent type
            group_id: Execution group ID
        """
        self.agent_registry[phase_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "group_id": group_id,
            "status": "running",
            "l2_path": None,
        }

    def mark_completed(self, phase_id: str, l2_path: str) -> None:
        """
        Mark agent as completed with L2 path.

        Args:
            phase_id: Phase identifier
            l2_path: Path to L2 structured report
        """
        if phase_id in self.agent_registry:
            self.agent_registry[phase_id]["status"] = "completed"
            self.agent_registry[phase_id]["l2_path"] = l2_path

    def get_synthesis_config(
        self,
        group: ExecutionGroup,
        synthesis_goal: str = "implementation priorities and critical findings",
    ) -> Dict[str, Any]:
        """
        Get L2 Synthesizer configuration for completed group.

        Args:
            group: Completed execution group
            synthesis_goal: What to extract from L2 files

        Returns:
            Config dict for L2Synthesizer
        """
        l2_paths: List[str] = []

        for phase in group.phases:
            reg = self.agent_registry.get(phase.id)
            if reg and reg.get("l2_path"):
                l2_paths.append(reg["l2_path"])

        return {
            "l2_paths": l2_paths,
            "synthesis_goal": synthesis_goal,
            "max_output_tokens": 500,
            "group_id": group.group_id,
            "phase_count": len(group.phases),
        }

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get execution summary with parallel opportunities.

        Returns:
            Dict with execution statistics
        """
        parallel_count = sum(1 for g in self.groups if g.is_parallel)
        sequential_count = len(self.groups) - parallel_count

        parallel_phases = sum(
            len(g.phases) for g in self.groups if g.is_parallel
        )

        return {
            "total_groups": len(self.groups),
            "parallel_groups": parallel_count,
            "sequential_groups": sequential_count,
            "parallel_phases": parallel_phases,
            "total_phases": sum(len(g.phases) for g in self.groups),
            "optimization": f"{parallel_phases} phases parallelized across {parallel_count} groups",
        }


# Convenience functions

def analyze_dependencies(phases: List[Phase]) -> List[ExecutionGroup]:
    """
    Quick dependency analysis returning execution groups.

    Args:
        phases: List of phases to analyze

    Returns:
        List of ExecutionGroups in execution order
    """
    return DependencyAnalyzer(phases).analyze()


def phases_from_plan(plan_tasks: List[Dict[str, Any]]) -> List[Phase]:
    """
    Convert plan file tasks to Phase objects.

    Args:
        plan_tasks: List of task dicts from plan file

    Returns:
        List of Phase objects
    """
    return [Phase.from_plan_task(task, i) for i, task in enumerate(plan_tasks)]


def get_parallel_groups(phases: List[Phase]) -> List[ExecutionGroup]:
    """
    Get only the parallel execution groups.

    Args:
        phases: List of phases

    Returns:
        List of parallel ExecutionGroups
    """
    groups = analyze_dependencies(phases)
    return [g for g in groups if g.is_parallel]


def create_execution_plan(
    phases: List[Phase],
) -> Tuple[List[ExecutionGroup], Dict[str, Any]]:
    """
    Create complete execution plan with summary.

    Args:
        phases: List of phases to execute

    Returns:
        Tuple of (groups, summary_dict)
    """
    executor = HybridExecutor()
    groups = executor.plan(phases)
    summary = executor.get_execution_summary()

    # Add dependency summary
    summary["dependencies"] = executor.analyzer.get_dependency_summary()

    return groups, summary


# Export all public symbols
__all__ = [
    # Enums
    "ExecutionMode",
    # Data classes
    "Phase",
    "ExecutionGroup",
    # Main classes
    "DependencyAnalyzer",
    "HybridExecutor",
    # Convenience functions
    "analyze_dependencies",
    "phases_from_plan",
    "get_parallel_groups",
    "create_execution_plan",
]
