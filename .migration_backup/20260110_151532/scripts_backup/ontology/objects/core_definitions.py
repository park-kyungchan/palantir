"""
Orion ODA v3.0 - Core Object Definitions
Domain Entities for the Orchestrator.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from scripts.ontology.ontology_types import OntologyObject, Link, Cardinality
from scripts.ontology.registry import register_object_type


# =============================================================================
# OBJECT TYPES
# =============================================================================

@register_object_type
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
    produced_by_task: ClassVar[Link["Task"]] = Link(
        target="Task",
        link_type_id="artifact_produced_by_task",
        cardinality=Cardinality.MANY_TO_ONE,
        description="The task that produced this artifact"
    )
