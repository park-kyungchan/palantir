# ODA V3.0 ActionType Implementations

> **Target Agent**: Antigravity IDE (Gemini 3.0 Pro)
> **Date**: 2025-12-20
> **Purpose**: Complete CRUD ActionTypes for Task and Agent domain objects

---

## Instruction for Antigravity Agent

You are tasked with implementing the following ActionTypes.
Leverage your **structured code generation**, **type inference**, and 
**docstring synthesis** capabilities for production-quality output.

Create/update the file at: `scripts/ontology/objects/task_actions.py`

---

## Complete Implementation

```python
"""
ODA V3.0 - Task Domain ActionTypes
==================================

This module defines all ActionTypes for Task object operations:
- CreateTaskAction: Create new tasks
- UpdateTaskAction: Modify existing tasks
- DeleteTaskAction: Soft-delete tasks (requires proposal)
- AssignTaskAction: Assign tasks to agents
- UnassignTaskAction: Remove task assignments
- CompleteTaskAction: Mark tasks as completed
- ArchiveTaskAction: Archive completed tasks
- BulkCreateTasksAction: Create multiple tasks atomically

All hazardous operations (Delete, BulkCreate) require Proposal approval.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from scripts.ontology.ontology_types import (
    Cardinality,
    Link,
    ObjectStatus,
    OntologyObject,
    utc_now,
)
from scripts.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    AllowedValues,
    CustomValidator,
    EditOperation,
    EditType,
    LogSideEffect,
    MaxLength,
    RequiredField,
    SlackNotification,
    ValidationError,
    WebhookSideEffect,
    register_action,
)


# =============================================================================
# DOMAIN ENUMS
# =============================================================================

class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task lifecycle status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# =============================================================================
# DOMAIN OBJECTS
# =============================================================================

class Agent(OntologyObject):
    """
    Represents an AI Agent or Human User in the system.
    
    Agents can be assigned to tasks and execute actions.
    """
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="agent", max_length=50)
    is_active: bool = Field(default=True)
    capabilities: List[str] = Field(default_factory=list)
    
    # Computed property for display
    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.role})"


class Task(OntologyObject):
    """
    Represents a unit of work in the system.
    
    Tasks can be assigned to agents, have priorities, and track progress.
    Links:
    - assigned_to: Agent (Many-to-One)
    - depends_on: Task[] (Many-to-Many, self-referential)
    - subtasks: Task[] (One-to-Many, self-referential)
    """
    # Required fields
    title: str = Field(..., min_length=1, max_length=255)
    
    # Optional fields
    description: str = Field(default="", max_length=5000)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    task_status: TaskStatus = Field(default=TaskStatus.PENDING)
    
    # Foreign keys (stored as IDs)
    assigned_to_id: Optional[str] = Field(default=None)
    parent_task_id: Optional[str] = Field(default=None)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)
    due_date: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Link definitions (class-level)
    assigned_to: ClassVar[Link[Agent]] = Link(
        target=Agent,
        link_type_id="task_assigned_to_agent",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="agent_assigned_tasks",
        description="The agent responsible for this task"
    )
    
    depends_on: ClassVar[Link["Task"]] = Link(
        target="Task",  # Self-referential
        link_type_id="task_depends_on_task",
        cardinality=Cardinality.MANY_TO_MANY,
        reverse_link_id="task_blocks",
        description="Tasks that must be completed before this task"
    )
    
    subtasks: ClassVar[Link["Task"]] = Link(
        target="Task",
        link_type_id="task_has_subtask",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="subtask_of",
        description="Child tasks of this task"
    )
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is past due date."""
        if self.due_date and self.task_status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            return datetime.now(timezone.utc) > self.due_date
        return False
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.task_status == TaskStatus.COMPLETED


# =============================================================================
# CUSTOM VALIDATORS
# =============================================================================

def validate_semver(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate semantic version format (X.Y.Z)."""
    version = params.get("version", "")
    return bool(re.match(r"^\d+\.\d+\.\d+$", version))


def validate_email(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate email format."""
    email = params.get("email")
    if email is None:
        return True  # Optional field
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email))


def validate_future_date(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate due_date is in the future."""
    due_date = params.get("due_date")
    if due_date is None:
        return True
    if isinstance(due_date, str):
        due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
    return due_date > datetime.now(timezone.utc)


def validate_positive_hours(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate estimated_hours is positive if provided."""
    hours = params.get("estimated_hours")
    if hours is None:
        return True
    return hours > 0


# =============================================================================
# TASK ACTIONS
# =============================================================================

@register_action
class CreateTaskAction(ActionType[Task]):
    """
    Create a new Task object.
    
    Required params:
    - title: str (1-255 chars)
    
    Optional params:
    - description: str (max 5000 chars)
    - priority: "low" | "medium" | "high" | "critical"
    - assigned_to_id: str (Agent ID)
    - tags: List[str]
    - estimated_hours: float (positive)
    - due_date: datetime (ISO format, must be future)
    """
    api_name: ClassVar[str] = "create_task"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = False
    
    submission_criteria: ClassVar[list] = [
        RequiredField("title"),
        MaxLength("title", 255),
        MaxLength("description", 5000),
        AllowedValues("priority", ["low", "medium", "high", "critical"]),
        CustomValidator(
            name="FutureDueDate",
            validator_fn=validate_future_date,
            error_message="due_date must be in the future"
        ),
        CustomValidator(
            name="PositiveHours",
            validator_fn=validate_positive_hours,
            error_message="estimated_hours must be positive"
        ),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Task, List[EditOperation]]:
        """Create a new Task with the provided parameters."""
        # Parse priority enum
        priority = params.get("priority", "medium")
        if isinstance(priority, str):
            priority = TaskPriority(priority)
        
        # Parse due_date if string
        due_date = params.get("due_date")
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        
        task = Task(
            title=params["title"],
            description=params.get("description", ""),
            priority=priority,
            assigned_to_id=params.get("assigned_to_id"),
            tags=params.get("tags", []),
            estimated_hours=params.get("estimated_hours"),
            due_date=due_date,
            created_by=context.actor_id,
        )
        
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Task",
            object_id=task.id,
            changes=params,
        )
        
        return task, [edit]


@register_action
class UpdateTaskAction(ActionType[Task]):
    """
    Update an existing Task.
    
    Required params:
    - task_id: str (existing Task ID)
    
    Optional params (at least one required):
    - title: str
    - description: str
    - priority: str
    - tags: List[str]
    - estimated_hours: float
    - due_date: datetime
    """
    api_name: ClassVar[str] = "update_task"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = False
    
    submission_criteria: ClassVar[list] = [
        RequiredField("task_id"),
        MaxLength("title", 255),
        MaxLength("description", 5000),
        AllowedValues("priority", ["low", "medium", "high", "critical"]),
        CustomValidator(
            name="HasChanges",
            validator_fn=lambda p, c: any(
                k in p for k in ["title", "description", "priority", "tags", "estimated_hours", "due_date"]
            ),
            error_message="At least one field must be updated"
        ),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Apply updates to an existing Task."""
        task_id = params["task_id"]
        
        # Build changes dict (only provided fields)
        changes = {}
        for field in ["title", "description", "priority", "tags", "estimated_hours", "due_date"]:
            if field in params:
                changes[field] = params[field]
        
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Task",
            object_id=task_id,
            changes=changes,
        )
        
        return None, [edit]


@register_action
class DeleteTaskAction(ActionType[Task]):
    """
    Soft-delete a Task (HAZARDOUS - requires Proposal).
    
    Required params:
    - task_id: str (existing Task ID)
    - reason: str (deletion reason for audit)
    """
    api_name: ClassVar[str] = "delete_task"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = True  # ⚠️ HAZARDOUS
    
    submission_criteria: ClassVar[list] = [
        RequiredField("task_id"),
        RequiredField("reason"),
        MaxLength("reason", 500),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
        SlackNotification(channel="#task-deletions"),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Soft-delete the Task."""
        edit = EditOperation(
            edit_type=EditType.DELETE,
            object_type="Task",
            object_id=params["task_id"],
            changes={
                "status": ObjectStatus.DELETED.value,
                "deletion_reason": params["reason"],
                "deleted_by": context.actor_id,
            },
        )
        
        return None, [edit]


@register_action
class AssignTaskAction(ActionType[Task]):
    """
    Assign a Task to an Agent.
    
    Required params:
    - task_id: str
    - agent_id: str
    """
    api_name: ClassVar[str] = "assign_task"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = False
    
    submission_criteria: ClassVar[list] = [
        RequiredField("task_id"),
        RequiredField("agent_id"),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
        SlackNotification(channel="#task-assignments"),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Assign the Task to an Agent."""
        edits = [
            # Update Task's assigned_to_id
            EditOperation(
                edit_type=EditType.MODIFY,
                object_type="Task",
                object_id=params["task_id"],
                changes={"assigned_to_id": params["agent_id"]},
            ),
            # Create Link record
            EditOperation(
                edit_type=EditType.LINK,
                object_type="TaskAgentLink",
                object_id=f"{params['task_id']}_{params['agent_id']}",
                changes={
                    "source_id": params["task_id"],
                    "target_id": params["agent_id"],
                    "link_type": "task_assigned_to_agent",
                },
            ),
        ]
        
        return None, edits


@register_action
class UnassignTaskAction(ActionType[Task]):
    """
    Remove Agent assignment from a Task.
    
    Required params:
    - task_id: str
    """
    api_name: ClassVar[str] = "unassign_task"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = False
    
    submission_criteria: ClassVar[list] = [
        RequiredField("task_id"),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Remove assignment from Task."""
        edits = [
            EditOperation(
                edit_type=EditType.MODIFY,
                object_type="Task",
                object_id=params["task_id"],
                changes={"assigned_to_id": None},
            ),
            EditOperation(
                edit_type=EditType.UNLINK,
                object_type="TaskAgentLink",
                object_id=params["task_id"],
                changes={"link_type": "task_assigned_to_agent"},
            ),
        ]
        
        return None, edits


@register_action
class CompleteTaskAction(ActionType[Task]):
    """
    Mark a Task as completed.
    
    Required params:
    - task_id: str
    
    Optional params:
    - actual_hours: float (time spent)
    - completion_notes: str
    """
    api_name: ClassVar[str] = "complete_task"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = False
    
    submission_criteria: ClassVar[list] = [
        RequiredField("task_id"),
        CustomValidator(
            name="PositiveActualHours",
            validator_fn=lambda p, c: p.get("actual_hours", 1) > 0,
            error_message="actual_hours must be positive"
        ),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
        SlackNotification(channel="#task-completions"),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Mark Task as completed."""
        changes = {
            "task_status": TaskStatus.COMPLETED.value,
            "completed_at": utc_now().isoformat(),
            "completed_by": context.actor_id,
        }
        
        if "actual_hours" in params:
            changes["actual_hours"] = params["actual_hours"]
        if "completion_notes" in params:
            changes["completion_notes"] = params["completion_notes"]
        
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Task",
            object_id=params["task_id"],
            changes=changes,
        )
        
        return None, [edit]


@register_action
class ArchiveTaskAction(ActionType[Task]):
    """
    Archive a completed Task.
    
    Required params:
    - task_id: str
    """
    api_name: ClassVar[str] = "archive_task"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = False
    
    submission_criteria: ClassVar[list] = [
        RequiredField("task_id"),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Archive the Task."""
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Task",
            object_id=params["task_id"],
            changes={
                "status": ObjectStatus.ARCHIVED.value,
                "archived_at": utc_now().isoformat(),
                "archived_by": context.actor_id,
            },
        )
        
        return None, [edit]


@register_action
class BulkCreateTasksAction(ActionType[Task]):
    """
    Create multiple Tasks atomically (HAZARDOUS - requires Proposal).
    
    Required params:
    - tasks: List[Dict] - each dict must have "title"
    
    Optional per-task params:
    - description, priority, tags, etc.
    """
    api_name: ClassVar[str] = "bulk_create_tasks"
    object_type: ClassVar[Type[Task]] = Task
    requires_proposal: ClassVar[bool] = True  # ⚠️ HAZARDOUS
    
    submission_criteria: ClassVar[list] = [
        RequiredField("tasks"),
        CustomValidator(
            name="TasksNotEmpty",
            validator_fn=lambda p, c: len(p.get("tasks", [])) > 0,
            error_message="tasks list cannot be empty"
        ),
        CustomValidator(
            name="MaxBulkSize",
            validator_fn=lambda p, c: len(p.get("tasks", [])) <= 100,
            error_message="Cannot create more than 100 tasks at once"
        ),
        CustomValidator(
            name="AllTasksHaveTitle",
            validator_fn=lambda p, c: all(
                t.get("title") for t in p.get("tasks", [])
            ),
            error_message="All tasks must have a title"
        ),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
        SlackNotification(channel="#bulk-operations"),
        WebhookSideEffect(url="https://analytics.example.com/bulk-create"),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Create multiple Tasks."""
        edits = []
        
        for task_data in params["tasks"]:
            priority = task_data.get("priority", "medium")
            if isinstance(priority, str):
                priority = TaskPriority(priority)
            
            task = Task(
                title=task_data["title"],
                description=task_data.get("description", ""),
                priority=priority,
                tags=task_data.get("tags", []),
                created_by=context.actor_id,
            )
            
            edits.append(EditOperation(
                edit_type=EditType.CREATE,
                object_type="Task",
                object_id=task.id,
                changes=task_data,
            ))
        
        return None, edits


# =============================================================================
# AGENT ACTIONS
# =============================================================================

@register_action
class CreateAgentAction(ActionType[Agent]):
    """
    Create a new Agent.
    
    Required params:
    - name: str (1-100 chars)
    
    Optional params:
    - email: str (valid email format)
    - role: str (default: "agent")
    - capabilities: List[str]
    """
    api_name: ClassVar[str] = "create_agent"
    object_type: ClassVar[Type[Agent]] = Agent
    requires_proposal: ClassVar[bool] = False
    
    submission_criteria: ClassVar[list] = [
        RequiredField("name"),
        MaxLength("name", 100),
        MaxLength("email", 255),
        CustomValidator(
            name="ValidEmail",
            validator_fn=validate_email,
            error_message="Invalid email format"
        ),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Agent, List[EditOperation]]:
        """Create a new Agent."""
        agent = Agent(
            name=params["name"],
            email=params.get("email"),
            role=params.get("role", "agent"),
            capabilities=params.get("capabilities", []),
            created_by=context.actor_id,
        )
        
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Agent",
            object_id=agent.id,
            changes=params,
        )
        
        return agent, [edit]


@register_action
class DeactivateAgentAction(ActionType[Agent]):
    """
    Deactivate an Agent (HAZARDOUS - requires Proposal).
    
    Required params:
    - agent_id: str
    - reason: str
    """
    api_name: ClassVar[str] = "deactivate_agent"
    object_type: ClassVar[Type[Agent]] = Agent
    requires_proposal: ClassVar[bool] = True  # ⚠️ HAZARDOUS
    
    submission_criteria: ClassVar[list] = [
        RequiredField("agent_id"),
        RequiredField("reason"),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
        SlackNotification(channel="#agent-management"),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Deactivate the Agent."""
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Agent",
            object_id=params["agent_id"],
            changes={
                "is_active": False,
                "deactivated_at": utc_now().isoformat(),
                "deactivation_reason": params["reason"],
                "deactivated_by": context.actor_id,
            },
        )
        
        return None, [edit]


# =============================================================================
# DEPLOYMENT ACTIONS (INFRASTRUCTURE)
# =============================================================================

@register_action
class DeployServiceAction(ActionType[OntologyObject]):
    """
    Deploy a service to production (HAZARDOUS - requires Proposal).
    
    Required params:
    - service_name: str
    - version: str (semver format: X.Y.Z)
    - environment: "staging" | "production"
    
    Optional params:
    - rollback_version: str (version to rollback to on failure)
    - notify_channels: List[str]
    """
    api_name: ClassVar[str] = "deploy_service"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = True  # ⚠️ HAZARDOUS
    
    submission_criteria: ClassVar[list] = [
        RequiredField("service_name"),
        RequiredField("version"),
        RequiredField("environment"),
        AllowedValues("environment", ["staging", "production"]),
        CustomValidator(
            name="SemverFormat",
            validator_fn=validate_semver,
            error_message="version must be semver format (X.Y.Z)"
        ),
    ]
    
    side_effects: ClassVar[list] = [
        LogSideEffect(),
        SlackNotification(channel="#deployments"),
        WebhookSideEffect(url="https://deploy.example.com/webhook"),
    ]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Record the deployment."""
        deployment_id = f"deploy-{params['service_name']}-{params['version']}"
        
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Deployment",
            object_id=deployment_id,
            changes={
                "service_name": params["service_name"],
                "version": params["version"],
                "environment": params["environment"],
                "deployed_by": context.actor_id,
                "deployed_at": utc_now().isoformat(),
                "rollback_version": params.get("rollback_version"),
            },
        )
        
        return None, [edit]


# =============================================================================
# ACTION CATALOG
# =============================================================================

"""
Summary of Registered Actions:

| API Name              | Object Type | Requires Proposal | Description                    |
|:----------------------|:------------|:-----------------:|:-------------------------------|
| create_task           | Task        | ❌                 | Create a new task              |
| update_task           | Task        | ❌                 | Update existing task           |
| delete_task           | Task        | ✅                 | Soft-delete a task             |
| assign_task           | Task        | ❌                 | Assign task to agent           |
| unassign_task         | Task        | ❌                 | Remove task assignment         |
| complete_task         | Task        | ❌                 | Mark task as completed         |
| archive_task          | Task        | ❌                 | Archive completed task         |
| bulk_create_tasks     | Task        | ✅                 | Create multiple tasks          |
| create_agent          | Agent       | ❌                 | Create a new agent             |
| deactivate_agent      | Agent       | ✅                 | Deactivate an agent            |
| deploy_service        | Deployment  | ✅                 | Deploy service to environment  |

Hazardous Actions (require Proposal approval):
- delete_task
- bulk_create_tasks
- deactivate_agent
- deploy_service
"""
```

---

## Usage Examples

```python
# Example 1: Create a task
from scripts.ontology.objects.task_actions import CreateTaskAction
from scripts.ontology.actions import ActionContext

context = ActionContext(actor_id="user-001")
action = CreateTaskAction()

result = await action.execute(
    params={
        "title": "Implement user authentication",
        "description": "Add OAuth2 support for the API",
        "priority": "high",
        "tags": ["security", "api"],
        "estimated_hours": 8.0,
    },
    context=context
)

print(result.success)  # True
print(result.created_ids)  # ['<uuid>']


# Example 2: Hazardous action (requires proposal)
from scripts.ontology.objects.task_actions import DeleteTaskAction
from scripts.ontology.objects.proposal import Proposal

# Check if action requires proposal
if DeleteTaskAction.requires_proposal:
    # Create proposal instead of direct execution
    proposal = Proposal(
        action_type="delete_task",
        payload={"task_id": "task-123", "reason": "Duplicate task"},
        created_by=context.actor_id,
    )
    proposal.submit()
    # Wait for admin approval...
```

---

## Verification Commands

```bash
# Verify all actions are registered
python -c "
from scripts.ontology.actions import action_registry
from scripts.ontology.objects import task_actions  # Import to register

actions = action_registry.list_actions()
print(f'Registered actions: {len(actions)}')
for a in sorted(actions):
    print(f'  - {a}')

hazardous = action_registry.get_hazardous_actions()
print(f'\nHazardous actions: {hazardous}')
"
```

Expected output:
```
Registered actions: 11
  - archive_task
  - assign_task
  - bulk_create_tasks
  - complete_task
  - create_agent
  - create_task
  - deactivate_agent
  - delete_task
  - deploy_service
  - unassign_task
  - update_task

Hazardous actions: ['delete_task', 'bulk_create_tasks', 'deactivate_agent', 'deploy_service']
```
