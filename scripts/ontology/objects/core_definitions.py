"""
Orion ODA v3.0 - Core Object Definitions
Domain Entities for the Orchestrator.
"""

from __future__ import annotations

from typing import ClassVar, List, Optional, Any, Dict

from pydantic import Field

from scripts.ontology.ontology_types import (
    OntologyObject,
    Link,
    Cardinality,
)
from scripts.ontology.actions import (
    ActionType,
    register_action,
    RequiredField,
    AllowedValues,
    MaxLength,
    EditType,
    EditOperation,
    ActionContext,
    LogSideEffect,
)


# =============================================================================
# OBJECT TYPES
# =============================================================================

class Agent(OntologyObject):
    """
    ObjectType: Agent
    Represents an AI Persona.
    """
    name: str = Field(..., description="Display Name of the Agent")
    model: str = Field(..., description="LLM Model Identity")
    capabilities: List[str] = Field(default_factory=list)
    
    # Links
    # assigned_tasks: Link[Task] - Defined on Task side as Reverse link


class Task(OntologyObject):
    """
    ObjectType: Task
    Represents a unit of work.
    """
    title: str = Field(..., description="Task Title")
    description: str = Field(default="", description="Detailed Description")
    status: str = Field(default="pending", description="Workflow Status")
    priority: str = Field(default="medium", description="Execution Priority")
    
    # Foreign Keys
    assigned_to_id: Optional[str] = Field(None, description="FK to Agent")
    parent_id: Optional[str] = Field(None, description="FK to Parent Task")
    
    # Link Definitions
    assigned_to: ClassVar[Link["Agent"]] = Link(
        target=Agent,
        link_type_id="task_assigned_to_agent",
        cardinality=Cardinality.MANY_TO_ONE,
        description="The agent responsible for this task"
    )
    
    parent_task: ClassVar[Link["Task"]] = Link(
        target="Task",  # Self-reference string
        link_type_id="task_parent",
        cardinality=Cardinality.MANY_TO_ONE,
        description="Parent task"
    )


class Artifact(OntologyObject):
    """
    ObjectType: Artifact
    Represents a File or Document produced by a Task.
    """
    path: str = Field(..., description="Absolute File Path")
    type: str = Field(..., description="File Type (code, doc, log)")
    
    # Foreign Keys
    produced_by_task_id: str = Field(..., description="FK to Task")
    
    # Link Definitions
    produced_by_task: ClassVar[Link[Task]] = Link(
        target=Task,
        link_type_id="artifact_produced_by_task",
        cardinality=Cardinality.MANY_TO_ONE,
        description="The task that produced this artifact"
    )


# =============================================================================
# ACTIONS
# =============================================================================

@register_action
class CreateTaskAction(ActionType[Task]):
    api_name = "create_task"
    object_type = Task
    
    submission_criteria = [
        RequiredField("title"),
        AllowedValues("priority", ["low", "medium", "high"]),
        MaxLength("title", 255),
    ]
    
    side_effects = [LogSideEffect()]
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Task], List[EditOperation]]:
        task = Task(
            title=params["title"],
            description=params.get("description", ""),
            priority=params.get("priority", "medium"),
            created_by=context.actor_id,
        )
        
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Task",
            object_id=task.id,
            changes=params,
        )
        
        return task, [edit]
