
"""
Orion ODA V3 - API Data Transfer Objects (DTOs)
===============================================
Enforces strict separation between Internal Domain Entities (Proposal) 
and External Wire Format (JSON).

Security Principles:
1. **No Leakage**: Internal fields (audit logs, internal IDs) are stripped.
2. **Strict Validation**: Input data is heavily validated before touching Logic layers.
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

# =============================================================================
# REQUEST MODELS (INPUT)
# =============================================================================

class CreateProposalRequest(BaseModel):
    """
    User intent to potentially hazardous action.
    """
    action_type: str = Field(..., description="API Name of the action", min_length=3)
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action arguments")
    priority: str = Field("medium", description="Execution priority")

class ReviewProposalRequest(BaseModel):
    """
    Governance decision payload.
    """
    reviewer_id: str = Field(..., description="ID of the reviewer")
    decision: str = Field(..., pattern="^(approve|reject)$")
    comment: Optional[str] = Field(None, description="Reasoning for decision")

# =============================================================================
# RESPONSE MODELS (OUTPUT)
# =============================================================================

class ProposalResponse(BaseModel):
    """
    Safe public representation of a Proposal.
    Excludes internal versioning details unless explicitly needed for optimistic locking UIs.
    """
    id: str
    action_type: str
    status: str
    priority: str
    created_at: datetime
    created_by: Optional[str] = None
    
    # We include payload for transparency, but sensitive fields inside payload 
    # should be masked by the domain logic if necessary.
    payload: Dict[str, Any]
    
    # Review status
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    
    # Execution status
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    
    # Optimistic Locking Token (Exposed only for Edit/Approve workflows)
    version: int

    model_config = {
        "from_attributes": True  # Allows mapping from ORM objects
    }

class StandardErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
