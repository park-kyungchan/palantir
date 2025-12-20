
from typing import List, Optional
from pydantic import Field
from scripts.ontology.ontology_types import BaseObject, Link

class Agent(BaseObject):
    """
    ObjectType: Agent
    Represents an AI Persona.
    """
    name: str = Field(..., description="Display Name of the Agent")
    model: str = Field(..., description="LLM Model Identity")
    capabilities: List[str] = Field(default_factory=list)
    
    _title_key = "name"

class Task(BaseObject):
    """
    ObjectType: Task
    Represents a unit of work.
    """
    title: str = Field(..., description="Task Title")
    status: str = Field(default="pending", description="Workflow Status")
    priority: str = Field(default="medium", description="Execution Priority")
    content: str = Field(default="", description="Detailed Description")
    
    # LinkType: Task -> Agent (Assignee) [Many-to-One]
    assignee_id: Optional[str] = Field(None, description="FK to Agent")
    
    # LinkType: Task -> Task (Subtasks) [One-to-Many Emulation via Parent]
    parent_id: Optional[str] = Field(None, description="FK to Parent Task")

    _title_key = "title"

class Artifact(BaseObject):
    """
    ObjectType: Artifact
    Represents a File or Document produced by a Task.
    """
    path: str = Field(..., description="Absolute File Path")
    type: str = Field(..., description="File Type (code, doc, log)")
    
    # LinkType: Artifact -> Task (Produced By)
    produced_by_task_id: str = Field(..., description="FK to Task")
