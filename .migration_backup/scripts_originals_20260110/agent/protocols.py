"""
Orion ODA v3.0 - Agent Execution Protocols
==========================================

This module defines standardized protocols for agent task execution.
All LLM agents MUST follow these protocols exactly.

The protocols provide:
1. Unambiguous task structures
2. Step-by-step execution flows
3. Error handling patterns
4. Success/failure criteria
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from lib.oda.ontology.ontology_types import utc_now


class TaskStatus(str, Enum):
    """Task execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class StepType(str, Enum):
    """Types of execution steps."""
    VALIDATE = "validate"           # Validate inputs
    EXECUTE = "execute"             # Execute action
    VERIFY = "verify"               # Verify result
    ROLLBACK = "rollback"           # Rollback on failure
    NOTIFY = "notify"               # Send notification


@dataclass
class ExecutionStep:
    """
    A single step in an execution protocol.

    Each step has:
    - step_id: Unique identifier (e.g., "S1", "S2")
    - step_type: Type of operation
    - description: What this step does
    - action: The action to execute (if any)
    - params: Parameters for the action
    - success_criteria: How to determine success
    - failure_action: What to do on failure
    """
    step_id: str
    step_type: StepType
    description: str
    action: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    success_criteria: str = ""
    failure_action: str = "abort"
    depends_on: List[str] = field(default_factory=list)


@dataclass
class ExecutionProtocol:
    """
    A complete execution protocol for a task.

    This is the ONLY structure agents should use for task execution.
    It provides an unambiguous, step-by-step execution plan.
    """
    protocol_id: str
    name: str
    description: str
    steps: List[ExecutionStep]
    created_at: datetime = field(default_factory=utc_now)

    # Execution state
    current_step: int = 0
    status: TaskStatus = TaskStatus.NOT_STARTED
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def get_next_step(self) -> Optional[ExecutionStep]:
        """Get the next step to execute."""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def mark_step_complete(self, step_id: str, result: Any = None) -> None:
        """Mark a step as complete and store result."""
        self.results[step_id] = result
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self.status = TaskStatus.COMPLETED

    def mark_step_failed(self, step_id: str, error: str) -> None:
        """Mark a step as failed."""
        self.errors.append(f"[{step_id}] {error}")
        self.status = TaskStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_type": s.step_type.value,
                    "description": s.description,
                    "action": s.action,
                    "params": s.params,
                    "success_criteria": s.success_criteria,
                    "failure_action": s.failure_action,
                }
                for s in self.steps
            ],
            "status": self.status.value,
            "current_step": self.current_step,
            "results": self.results,
            "errors": self.errors,
        }


# =============================================================================
# PRE-DEFINED PROTOCOLS
# =============================================================================

def create_task_protocol(title: str, description: str = "", priority: str = "medium") -> ExecutionProtocol:
    """
    Protocol for creating a new task.

    Steps:
    1. VALIDATE: Check parameters
    2. EXECUTE: Create task via action
    3. VERIFY: Confirm task was created
    """
    return ExecutionProtocol(
        protocol_id=f"create_task_{utc_now().timestamp()}",
        name="Create Task Protocol",
        description=f"Create task: {title}",
        steps=[
            ExecutionStep(
                step_id="S1",
                step_type=StepType.VALIDATE,
                description="Validate task parameters",
                success_criteria="title is non-empty string, priority is valid",
                failure_action="abort with validation error"
            ),
            ExecutionStep(
                step_id="S2",
                step_type=StepType.EXECUTE,
                description="Execute create_task action",
                action="create_task",
                params={
                    "title": title,
                    "description": description,
                    "priority": priority,
                },
                success_criteria="ActionResult.success == True",
                failure_action="abort with execution error",
                depends_on=["S1"]
            ),
            ExecutionStep(
                step_id="S3",
                step_type=StepType.VERIFY,
                description="Verify task was created",
                success_criteria="created_ids contains new task ID",
                failure_action="log warning, mark as partial success",
                depends_on=["S2"]
            ),
        ]
    )


def assign_task_protocol(task_id: str, agent_id: str) -> ExecutionProtocol:
    """
    Protocol for assigning a task to an agent.

    Steps:
    1. VALIDATE: Check task and agent exist
    2. EXECUTE: Assign task via action
    3. VERIFY: Confirm assignment
    4. NOTIFY: Notify agent of assignment
    """
    return ExecutionProtocol(
        protocol_id=f"assign_task_{utc_now().timestamp()}",
        name="Assign Task Protocol",
        description=f"Assign task {task_id[:8]}... to agent {agent_id[:8]}...",
        steps=[
            ExecutionStep(
                step_id="S1",
                step_type=StepType.VALIDATE,
                description="Validate task_id and agent_id are valid UUIDs",
                success_criteria="Both IDs are non-empty strings",
                failure_action="abort with validation error"
            ),
            ExecutionStep(
                step_id="S2",
                step_type=StepType.EXECUTE,
                description="Execute assign_task action",
                action="assign_task",
                params={
                    "task_id": task_id,
                    "agent_id": agent_id,
                },
                success_criteria="ActionResult.success == True",
                failure_action="abort with execution error",
                depends_on=["S1"]
            ),
            ExecutionStep(
                step_id="S3",
                step_type=StepType.VERIFY,
                description="Verify assignment was recorded",
                success_criteria="modified_ids contains task_id",
                failure_action="log warning",
                depends_on=["S2"]
            ),
            ExecutionStep(
                step_id="S4",
                step_type=StepType.NOTIFY,
                description="Notify agent of new assignment",
                success_criteria="Notification sent (or skipped if not configured)",
                failure_action="log warning, continue",
                depends_on=["S3"]
            ),
        ]
    )


def delete_task_protocol(task_id: str, reason: str) -> ExecutionProtocol:
    """
    Protocol for deleting a task (HAZARDOUS - creates proposal).

    Steps:
    1. VALIDATE: Check task exists and reason provided
    2. EXECUTE: Create delete proposal
    3. VERIFY: Confirm proposal created
    """
    return ExecutionProtocol(
        protocol_id=f"delete_task_{utc_now().timestamp()}",
        name="Delete Task Protocol (HAZARDOUS)",
        description=f"Delete task {task_id[:8]}...",
        steps=[
            ExecutionStep(
                step_id="S1",
                step_type=StepType.VALIDATE,
                description="Validate task_id exists and reason is provided",
                success_criteria="task_id is valid, reason is non-empty",
                failure_action="abort with validation error"
            ),
            ExecutionStep(
                step_id="S2",
                step_type=StepType.EXECUTE,
                description="Create deletion proposal (requires human approval)",
                action="delete_task",
                params={
                    "task_id": task_id,
                    "reason": reason,
                },
                success_criteria="Proposal created with proposal_id",
                failure_action="abort with execution error",
                depends_on=["S1"]
            ),
            ExecutionStep(
                step_id="S3",
                step_type=StepType.VERIFY,
                description="Verify proposal is in PENDING status",
                success_criteria="proposal_id is returned, status is pending",
                failure_action="log error",
                depends_on=["S2"]
            ),
        ]
    )


def bulk_create_tasks_protocol(tasks: List[Dict[str, Any]]) -> ExecutionProtocol:
    """
    Protocol for bulk creating tasks (HAZARDOUS - creates proposal).

    Steps:
    1. VALIDATE: Check all tasks have required fields
    2. EXECUTE: Create bulk creation proposal
    3. VERIFY: Confirm proposal created
    """
    return ExecutionProtocol(
        protocol_id=f"bulk_create_tasks_{utc_now().timestamp()}",
        name="Bulk Create Tasks Protocol (HAZARDOUS)",
        description=f"Create {len(tasks)} tasks in bulk",
        steps=[
            ExecutionStep(
                step_id="S1",
                step_type=StepType.VALIDATE,
                description="Validate all tasks have title, count <= 100",
                success_criteria="All tasks have title, count <= 100",
                failure_action="abort with validation error"
            ),
            ExecutionStep(
                step_id="S2",
                step_type=StepType.EXECUTE,
                description="Create bulk creation proposal (requires human approval)",
                action="bulk_create_tasks",
                params={"tasks": tasks},
                success_criteria="Proposal created with proposal_id",
                failure_action="abort with execution error",
                depends_on=["S1"]
            ),
            ExecutionStep(
                step_id="S3",
                step_type=StepType.VERIFY,
                description="Verify proposal is in PENDING status",
                success_criteria="proposal_id is returned",
                failure_action="log error",
                depends_on=["S2"]
            ),
        ]
    )


# =============================================================================
# TASK RESULT (Re-exported for convenience)
# =============================================================================

from lib.oda.agent.executor import TaskResult

__all__ = [
    "TaskStatus",
    "StepType",
    "ExecutionStep",
    "ExecutionProtocol",
    "TaskResult",
    "create_task_protocol",
    "assign_task_protocol",
    "delete_task_protocol",
    "bulk_create_tasks_protocol",
]
