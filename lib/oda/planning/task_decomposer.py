"""
Orion ODA v3.0 - Task Decomposer
================================

Automatic task decomposition for 32K token limit compliance.

This module analyzes task scope and automatically decomposes large tasks
into smaller subtasks that fit within subagent output budgets.

Usage:
    decomposer = TaskDecomposer()

    if decomposer.should_decompose("Analyze entire codebase"):
        subtasks = decomposer.decompose("Analyze entire codebase", scope="/home/project")
        for task in subtasks:
            # Delegate each subtask to appropriate subagent
            Task(subagent_type=task.subagent_type, prompt=task.prompt)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import os


class SubagentType(str, Enum):
    """Subagent types with token budgets."""
    EXPLORE = "Explore"
    PLAN = "Plan"
    GENERAL_PURPOSE = "general-purpose"


@dataclass
class TokenBudget:
    """Token budget configuration per subagent type."""
    explore: int = 5000
    plan: int = 10000
    general_purpose: int = 15000

    def get_budget(self, subagent_type: SubagentType) -> int:
        """Get token budget for subagent type."""
        mapping = {
            SubagentType.EXPLORE: self.explore,
            SubagentType.PLAN: self.plan,
            SubagentType.GENERAL_PURPOSE: self.general_purpose,
        }
        return mapping.get(subagent_type, self.general_purpose)


@dataclass
class SubTask:
    """A decomposed subtask for delegation."""
    description: str
    prompt: str
    subagent_type: SubagentType
    scope: str
    token_budget: int
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    # V2.1.x: Resume parameter support for subagent continuation
    task_id: Optional[str] = None  # Previous task ID to resume from
    should_resume: bool = False    # Whether to resume previous execution

    def to_task_params(self) -> Dict[str, Any]:
        """
        Convert to Task tool parameters.

        V2.1.x Enhancement: Includes 'resume' parameter when task_id is set
        and should_resume is True. This allows continuing subagent work
        after Auto-Compact or session interruption.

        Returns:
            Dict ready for Task tool invocation
        """
        params = {
            "description": self.description,
            "prompt": self.prompt,
            "subagent_type": self.subagent_type.value,
            "run_in_background": True,
        }

        # V2.1.x: Add resume parameter if resuming previous task
        if self.should_resume and self.task_id:
            params["resume"] = self.task_id

        return params

    def mark_for_resume(self, task_id: str) -> "SubTask":
        """
        Mark this subtask for resumption from a previous execution.

        V2.1.x Feature: Enable subagent continuation after interruption.

        Args:
            task_id: The ID of the previous task execution to resume

        Returns:
            Self for method chaining
        """
        self.task_id = task_id
        self.should_resume = True
        return self


class TaskDecomposer:
    """
    Decomposes large tasks into smaller subtasks.

    Analyzes task scope and automatically splits work to comply
    with 32K token output limits for background subagents.
    """

    # Keywords that indicate large scope
    SCOPE_KEYWORDS_KO = ["전체", "모든", "완전한", "전부"]
    SCOPE_KEYWORDS_EN = ["all", "entire", "complete", "whole", "full", "every"]
    SCOPE_KEYWORDS = SCOPE_KEYWORDS_KO + SCOPE_KEYWORDS_EN

    # Thresholds
    FILE_THRESHOLD = 20
    DIRECTORY_THRESHOLD = 5

    def __init__(
        self,
        token_budget: Optional[TokenBudget] = None,
        file_threshold: int = 20,
        directory_threshold: int = 5,
    ):
        """
        Initialize TaskDecomposer.

        Args:
            token_budget: Custom token budgets (uses defaults if None)
            file_threshold: Max files before decomposition required
            directory_threshold: Max directories before decomposition required
        """
        self.token_budget = token_budget or TokenBudget()
        self.file_threshold = file_threshold
        self.directory_threshold = directory_threshold

    def should_decompose(self, task: str, scope: Optional[str] = None) -> bool:
        """
        Check if task should be decomposed.

        Args:
            task: Task description
            scope: Optional scope path to analyze

        Returns:
            True if decomposition is recommended
        """
        # Check for scope keywords
        task_lower = task.lower()
        if any(kw in task_lower for kw in self.SCOPE_KEYWORDS):
            return True

        # Check scope size if provided
        if scope and os.path.exists(scope):
            file_count = self._estimate_file_count(scope)
            if file_count > self.file_threshold:
                return True

            dir_count = self._count_directories(scope)
            if dir_count > self.directory_threshold:
                return True

        return False

    def decompose(
        self,
        task: str,
        scope: str,
        subagent_type: SubagentType = SubagentType.EXPLORE,
    ) -> List[SubTask]:
        """
        Decompose task into subtasks.

        Args:
            task: Original task description
            scope: Root scope path
            subagent_type: Default subagent type for subtasks

        Returns:
            List of SubTask objects
        """
        subtasks: List[SubTask] = []

        if not os.path.exists(scope):
            # Single task if scope doesn't exist
            return [self._create_subtask(task, scope, subagent_type, 0)]

        # Get subdirectories
        subdirs = self._get_major_subdirectories(scope)

        if not subdirs:
            # No subdirs, single task
            return [self._create_subtask(task, scope, subagent_type, 0)]

        # Create subtask for each major subdirectory
        for priority, subdir in enumerate(subdirs):
            subtask_scope = os.path.join(scope, subdir)
            subtask_desc = f"{task} - {subdir}"
            subtask_prompt = self._generate_subtask_prompt(
                task, subtask_scope, subagent_type
            )

            subtasks.append(SubTask(
                description=subtask_desc[:50],  # Limit description length
                prompt=subtask_prompt,
                subagent_type=subagent_type,
                scope=subtask_scope,
                token_budget=self.token_budget.get_budget(subagent_type),
                priority=priority,
            ))

        return subtasks

    def _estimate_file_count(self, path: str, extensions: Optional[List[str]] = None) -> int:
        """Estimate file count in directory."""
        if not os.path.isdir(path):
            return 1

        count = 0
        extensions = extensions or [".py", ".ts", ".js", ".md", ".yaml", ".yml"]

        try:
            for root, dirs, files in os.walk(path):
                # Skip hidden and cache directories
                dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]

                for f in files:
                    if any(f.endswith(ext) for ext in extensions):
                        count += 1

                # Early exit if we've exceeded threshold
                if count > self.file_threshold * 2:
                    break
        except PermissionError:
            pass

        return count

    def _count_directories(self, path: str) -> int:
        """Count immediate subdirectories."""
        if not os.path.isdir(path):
            return 0

        try:
            return len([
                d for d in os.listdir(path)
                if os.path.isdir(os.path.join(path, d))
                and not d.startswith(('.', '__'))
            ])
        except PermissionError:
            return 0

    def _get_major_subdirectories(self, path: str) -> List[str]:
        """Get major subdirectories for decomposition."""
        if not os.path.isdir(path):
            return []

        try:
            subdirs = [
                d for d in os.listdir(path)
                if os.path.isdir(os.path.join(path, d))
                and not d.startswith(('.', '__'))
            ]

            # Sort by file count (largest first)
            subdirs.sort(
                key=lambda d: self._estimate_file_count(os.path.join(path, d)),
                reverse=True
            )

            return subdirs[:10]  # Limit to 10 subtasks max
        except PermissionError:
            return []

    def _create_subtask(
        self,
        task: str,
        scope: str,
        subagent_type: SubagentType,
        priority: int,
    ) -> SubTask:
        """Create a single subtask."""
        return SubTask(
            description=task[:50],
            prompt=self._generate_subtask_prompt(task, scope, subagent_type),
            subagent_type=subagent_type,
            scope=scope,
            token_budget=self.token_budget.get_budget(subagent_type),
            priority=priority,
        )

    def _generate_subtask_prompt(
        self,
        task: str,
        scope: str,
        subagent_type: SubagentType,
    ) -> str:
        """Generate prompt for subtask."""
        budget = self.token_budget.get_budget(subagent_type)

        return f'''## Task
{task}

## Scope
Analyze ONLY: {scope}

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED {budget} TOKENS.
Return ONLY: Key findings, critical paths, summary.
DO NOT include: Full file contents, verbose explanations.
Format: Bullet points with file:line references.

## Evidence Required
- files_viewed: [must populate with actual files read]
- summary: [key findings in bullet points]
'''


# Convenience function for quick decomposition check
def should_decompose_task(task: str, scope: Optional[str] = None) -> bool:
    """Quick check if task should be decomposed."""
    return TaskDecomposer().should_decompose(task, scope)


def decompose_task(
    task: str,
    scope: str,
    subagent_type: str = "Explore",
) -> List[Dict[str, Any]]:
    """
    Quick decomposition returning Task-ready parameters.

    Returns list of dicts ready for Task tool invocation.
    """
    decomposer = TaskDecomposer()
    subtasks = decomposer.decompose(
        task,
        scope,
        SubagentType(subagent_type) if subagent_type != "general-purpose" else SubagentType.GENERAL_PURPOSE,
    )
    return [st.to_task_params() for st in subtasks]
