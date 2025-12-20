
from typing import List, Optional, Dict, Any
from pydantic import Field
from scripts.ontology.ontology_types import BaseObject, Link

class Proposal(BaseObject):
    """
    ObjectType: Proposal
    Represents a staged Action waiting for Human Review.
    """
    action_type: str = Field(..., description="The API Name of the Action to execute")
    parameters_json: str = Field(..., description="Serialized JSON of Action Parameters")
    status: str = Field(default="pending", description="pending | approved | rejected | executed")
    
    # Link: Proposal -> Agent (Creator)
    created_by_id: str = Field(..., description="FK to Agent who proposed this")
    
    # Link: Proposal -> Agent (Reviewer)
    reviewed_by_id: Optional[str] = Field(None, description="FK to Agent who reviewed")

    _title_key = "action_type"
