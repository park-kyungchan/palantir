
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import Field
from scripts.ontology.core import OrionObject

class OrionActionLog(OrionObject):
    """
    Immutable Audit Record for Kinetic Actions.
    """
    # Context
    agent_id: str = "Orion-Kernel" # Default Identity
    trace_id: Optional[str] = None # Job ID / Plan ID
    
    # Intent
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Outcome
    status: str # SUCCESS, FAILURE, ROLLED_BACK
    error: Optional[str] = None
    
    # Impact
    affected_ids: List[str] = Field(default_factory=list)
    
    # Meta
    duration_ms: int = 0
    
    def get_searchable_text(self) -> str:
        return f"{self.action_type} {self.status} {self.error or ''}"
