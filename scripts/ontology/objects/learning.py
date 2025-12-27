from __future__ import annotations
from typing import ClassVar, List, Optional, Any, Dict
from pydantic import Field
from scripts.ontology.ontology_types import OntologyObject, Link, Cardinality

class Learner(OntologyObject):
    """
    ObjectType: Learner
    Represents a student in the Adaptive Tutoring system.
    """
    user_id: str = Field(..., description="Unique User Identifier")
    theta: float = Field(default=0.0, description="Global proficiency estimate")
    knowledge_state: Dict[str, Any] = Field(default_factory=dict, description="BKT parameters for KCs")
    last_active: str = Field(default="", description="ISO formatted timestamp")
    
    # We might link to Session history later, but keeping it simple for now.
