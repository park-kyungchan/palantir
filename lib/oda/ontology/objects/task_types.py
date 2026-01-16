from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, List, Optional

from pydantic import Field

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


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


@register_object_type
class Agent(OntologyObject):
    """
    Represents an AI Agent or Human User in the system.
    
    Agents can be assigned to tasks and execute actions.
    """
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="agent", max_length=50)
    agent_active: bool = Field(default=True)  # Avoid shadowing OntologyObject.is_active
    capabilities: List[str] = Field(default_factory=list)

    # Reverse link: Tasks assigned to this agent (1:N from Agent's perspective)
    assigned_tasks: ClassVar[Link["Task"]] = Link(
        target="Task",
        link_type_id="agent_assigned_tasks",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="task_assigned_to_agent",
        description="Tasks currently assigned to this agent",
    )

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.role})"


@register_object_type
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
        description="The agent responsible for this task",
    )
    
    depends_on: ClassVar[Link["Task"]] = Link(
        target="Task",  # Self-referential
        link_type_id="task_depends_on_task",
        cardinality=Cardinality.MANY_TO_MANY,
        reverse_link_id="task_blocks",
        description="Tasks that must be completed before this task",
        backing_table_name="task_dependencies",
        is_materialized=True,
    )
    
    subtasks: ClassVar[Link["Task"]] = Link(
        target="Task",
        link_type_id="task_has_subtask",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="subtask_of",
        description="Child tasks of this task",
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
