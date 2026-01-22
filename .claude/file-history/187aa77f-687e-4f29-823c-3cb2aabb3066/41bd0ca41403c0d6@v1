"""
Orion ODA v3.0 - TodoWrite Tracker (V2.1.8)
============================================

Unified Agent ID tracking for TodoWrite integration.
Enables Auto-Compact survival through consistent state management.

This module bridges the gap between:
- AgentRegistry (internal state tracking)
- PlanFile (persistent plan storage)
- TodoWrite (UI progress display)

Usage:
    tracker = TodoWriteTracker("Feature Implementation Plan")
    tracker.add_phase(1, "Analyze codebase", ["lib/"], "Explore")
    tracker.update_agent_id(1, "a1b2c3d")
    tracker.mark_completed(1)

    todos = tracker.get_todowrite_json()
    # [{"content": "[Phase 1] Analyze codebase | Files: lib/ | Agent: Explore:a1b2c3d (done)", ...}]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AgentLifecycleState(str, Enum):
    """Agent ID lifecycle states for TodoWrite display."""
    PENDING = "pending"
    ACTIVE = "active"  # Has actual agent_id
    DONE = "done"
    FAILED = "failed"


@dataclass
class TrackedTodo:
    """
    A single tracked todo item with Agent ID lifecycle.

    Attributes:
        phase_num: Phase number (1-indexed)
        task: Task description
        files: List of affected files/directories
        subagent_type: Type of subagent (Explore, Plan, general-purpose)
        agent_id: Current agent ID ("pending" | actual_id)
        state: Current lifecycle state
        created_at: When this todo was created
        updated_at: Last update timestamp
    """
    phase_num: int
    task: str
    files: List[str]
    subagent_type: str
    agent_id: str = "pending"
    state: AgentLifecycleState = AgentLifecycleState.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Resume eligibility tracking
    resume_eligible: bool = True
    resume_deadline: Optional[datetime] = None

    def format_agent_display(self) -> str:
        """
        Format agent ID for TodoWrite display.

        Returns:
            Formatted string: "type:id" or "type:id (done)" or "type:id (FAILED)"
        """
        base = f"{self.subagent_type}:{self.agent_id}"

        if self.state == AgentLifecycleState.DONE:
            return f"{base} (done)"
        elif self.state == AgentLifecycleState.FAILED:
            return f"{base} (FAILED)"
        else:
            return base

    def format_todowrite_content(self) -> str:
        """
        Format for TodoWrite content field.

        Format: [Phase N] {task} | Files: {files} | Agent: {type}:{id}
        """
        files_str = ", ".join(self.files) if self.files else "N/A"
        return f"[Phase {self.phase_num}] {self.task} | Files: {files_str} | Agent: {self.format_agent_display()}"

    def format_active_form(self) -> str:
        """
        Format for TodoWrite activeForm field (present continuous).
        """
        # Convert task to present continuous form
        if self.state == AgentLifecycleState.PENDING:
            return f"Preparing {self.task.lower()}"
        elif self.state == AgentLifecycleState.ACTIVE:
            return f"Executing {self.task.lower()}"
        elif self.state == AgentLifecycleState.DONE:
            return f"Completed {self.task.lower()}"
        else:
            return f"Failed {self.task.lower()}"

    def to_todowrite_dict(self) -> Dict[str, Any]:
        """
        Convert to TodoWrite JSON format.

        Returns:
            Dict with content, status, activeForm keys
        """
        # Map lifecycle state to TodoWrite status
        status_map = {
            AgentLifecycleState.PENDING: "pending",
            AgentLifecycleState.ACTIVE: "in_progress",
            AgentLifecycleState.DONE: "completed",
            AgentLifecycleState.FAILED: "in_progress",  # Failed stays in_progress for retry
        }

        return {
            "content": self.format_todowrite_content(),
            "status": status_map[self.state],
            "activeForm": self.format_active_form(),
        }

    def can_resume(self, max_age_hours: float = 1.0) -> bool:
        """
        Check if this todo's agent can be resumed.

        Args:
            max_age_hours: Maximum age in hours for resume eligibility

        Returns:
            True if resume is possible
        """
        if not self.resume_eligible:
            return False

        if self.state not in (AgentLifecycleState.ACTIVE, AgentLifecycleState.FAILED):
            return False

        if self.agent_id == "pending":
            return False

        # Check age
        age = datetime.now() - self.updated_at
        if age > timedelta(hours=max_age_hours):
            return False

        return True


class TodoWriteTracker:
    """
    Unified tracker for TodoWrite + Agent ID integration.

    This class maintains the single source of truth for:
    - Phase progress tracking
    - Agent ID lifecycle management
    - Resume eligibility
    - TodoWrite JSON generation

    Example:
        tracker = TodoWriteTracker("My Plan")

        # Before execution
        tracker.add_phase(1, "Analyze", ["lib/"], "Explore")
        # TodoWrite shows: [Phase 1] Analyze | Files: lib/ | Agent: Explore:pending

        # After Task() returns
        tracker.update_agent_id(1, "a1b2c3d")
        # TodoWrite shows: [Phase 1] Analyze | Files: lib/ | Agent: Explore:a1b2c3d

        # After verification
        tracker.mark_completed(1)
        # TodoWrite shows: [Phase 1] Analyze | Files: lib/ | Agent: Explore:a1b2c3d (done)
    """

    def __init__(
        self,
        plan_title: str,
        session_id: Optional[str] = None,
        orchestrator_header: Optional[str] = None,
    ):
        """
        Initialize TodoWriteTracker.

        Args:
            plan_title: Title of the plan being tracked
            session_id: Optional session identifier
            orchestrator_header: Optional header todo for orchestrator mode
        """
        self.plan_title = plan_title
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self._todos: Dict[int, TrackedTodo] = {}
        self._orchestrator_header = orchestrator_header or (
            "🎯 ORCHESTRATOR: 직접 실행 금지 - Task()로 Subagent에 위임 | 결과 검증 필수"
        )

    def add_phase(
        self,
        phase_num: int,
        task: str,
        files: List[str],
        subagent_type: str,
    ) -> TrackedTodo:
        """
        Add a new phase to tracking.

        Args:
            phase_num: Phase number (1-indexed)
            task: Task description
            files: List of affected files/directories
            subagent_type: Subagent type (Explore, Plan, general-purpose)

        Returns:
            The created TrackedTodo
        """
        todo = TrackedTodo(
            phase_num=phase_num,
            task=task,
            files=files,
            subagent_type=subagent_type,
        )
        self._todos[phase_num] = todo
        return todo

    def update_agent_id(self, phase_num: int, agent_id: str) -> Optional[TrackedTodo]:
        """
        Update agent ID after Task() returns.

        This transitions the todo from PENDING to ACTIVE state.

        Args:
            phase_num: Phase number to update
            agent_id: The actual agent ID from Task() result

        Returns:
            Updated TrackedTodo or None if not found
        """
        if phase_num not in self._todos:
            return None

        todo = self._todos[phase_num]
        todo.agent_id = agent_id
        todo.state = AgentLifecycleState.ACTIVE
        todo.updated_at = datetime.now()

        # Set resume deadline (1 hour from now)
        todo.resume_deadline = datetime.now() + timedelta(hours=1)

        return todo

    def mark_completed(self, phase_num: int) -> Optional[TrackedTodo]:
        """
        Mark phase as completed after successful verification.

        Args:
            phase_num: Phase number to mark complete

        Returns:
            Updated TrackedTodo or None if not found
        """
        if phase_num not in self._todos:
            return None

        todo = self._todos[phase_num]
        todo.state = AgentLifecycleState.DONE
        todo.updated_at = datetime.now()
        todo.resume_eligible = False  # Completed tasks can't be resumed

        return todo

    def mark_failed(self, phase_num: int) -> Optional[TrackedTodo]:
        """
        Mark phase as failed (enables retry/resume).

        Args:
            phase_num: Phase number to mark failed

        Returns:
            Updated TrackedTodo or None if not found
        """
        if phase_num not in self._todos:
            return None

        todo = self._todos[phase_num]
        todo.state = AgentLifecycleState.FAILED
        todo.updated_at = datetime.now()
        todo.resume_eligible = True  # Failed tasks can be resumed

        return todo

    def get_todo(self, phase_num: int) -> Optional[TrackedTodo]:
        """Get a specific todo by phase number."""
        return self._todos.get(phase_num)

    def get_all_todos(self) -> List[TrackedTodo]:
        """Get all todos sorted by phase number."""
        return [self._todos[k] for k in sorted(self._todos.keys())]

    def get_todowrite_json(self, include_header: bool = True) -> List[Dict[str, Any]]:
        """
        Generate TodoWrite-compatible JSON array.

        Args:
            include_header: Whether to include orchestrator header

        Returns:
            List of dicts ready for TodoWrite tool
        """
        todos = []

        # Add orchestrator header if requested
        if include_header:
            # Determine header status based on overall progress
            all_done = all(t.state == AgentLifecycleState.DONE for t in self._todos.values())
            any_active = any(t.state == AgentLifecycleState.ACTIVE for t in self._todos.values())

            if all_done:
                header_status = "completed"
            elif any_active:
                header_status = "in_progress"
            else:
                header_status = "pending"

            todos.append({
                "content": self._orchestrator_header,
                "status": header_status,
                "activeForm": f"Orchestrating {self.plan_title}",
            })

        # Add all phase todos
        for todo in self.get_all_todos():
            todos.append(todo.to_todowrite_dict())

        return todos

    def get_resumable_agents(self) -> List[Tuple[int, str, str]]:
        """
        Get list of agents that can be resumed.

        Returns:
            List of tuples: (phase_num, agent_id, subagent_type)
        """
        resumable = []

        for phase_num, todo in self._todos.items():
            if todo.can_resume():
                resumable.append((phase_num, todo.agent_id, todo.subagent_type))

        return resumable

    def get_next_pending_phase(self) -> Optional[int]:
        """
        Get the next phase that needs execution.

        Returns:
            Phase number or None if all complete
        """
        for phase_num in sorted(self._todos.keys()):
            if self._todos[phase_num].state == AgentLifecycleState.PENDING:
                return phase_num
        return None

    def get_progress_summary(self) -> Dict[str, int]:
        """
        Get progress summary counts.

        Returns:
            Dict with counts: total, pending, active, done, failed
        """
        summary = {
            "total": len(self._todos),
            "pending": 0,
            "active": 0,
            "done": 0,
            "failed": 0,
        }

        for todo in self._todos.values():
            if todo.state == AgentLifecycleState.PENDING:
                summary["pending"] += 1
            elif todo.state == AgentLifecycleState.ACTIVE:
                summary["active"] += 1
            elif todo.state == AgentLifecycleState.DONE:
                summary["done"] += 1
            elif todo.state == AgentLifecycleState.FAILED:
                summary["failed"] += 1

        return summary

    def from_plan_phases(self, phases: List[Dict[str, Any]]) -> "TodoWriteTracker":
        """
        Initialize tracker from plan file phases.

        Args:
            phases: List of phase dicts with keys: number, task, files, subagent_type

        Returns:
            Self for method chaining
        """
        for phase in phases:
            self.add_phase(
                phase_num=phase.get("number", len(self._todos) + 1),
                task=phase.get("task", "Unknown task"),
                files=phase.get("files", []),
                subagent_type=phase.get("subagent_type", "general-purpose"),
            )
        return self

    def to_agent_registry_format(self) -> List[Dict[str, Any]]:
        """
        Export to AgentRegistry-compatible format.

        Returns:
            List of agent entries for AgentRegistry
        """
        entries = []

        for todo in self._todos.values():
            if todo.agent_id != "pending":
                entries.append({
                    "agent_id": todo.agent_id,
                    "subagent_type": todo.subagent_type,
                    "description": todo.task,
                    "phase": todo.phase_num,
                    "status": todo.state.value,
                    "created_at": todo.created_at.isoformat(),
                    "updated_at": todo.updated_at.isoformat(),
                    "resume_eligible": todo.can_resume(),
                })

        return entries


# Convenience functions for quick access
def create_tracker(plan_title: str) -> TodoWriteTracker:
    """Create a new TodoWriteTracker instance."""
    return TodoWriteTracker(plan_title)


def format_phase_todo(
    phase_num: int,
    task: str,
    files: List[str],
    subagent_type: str,
    agent_id: str = "pending",
    done: bool = False,
) -> str:
    """
    Quick format for a phase todo string.

    Args:
        phase_num: Phase number
        task: Task description
        files: Affected files
        subagent_type: Subagent type
        agent_id: Agent ID (default: "pending")
        done: Whether task is complete

    Returns:
        Formatted string for TodoWrite content
    """
    files_str = ", ".join(files) if files else "N/A"
    agent_display = f"{subagent_type}:{agent_id}"
    if done:
        agent_display += " (done)"

    return f"[Phase {phase_num}] {task} | Files: {files_str} | Agent: {agent_display}"
