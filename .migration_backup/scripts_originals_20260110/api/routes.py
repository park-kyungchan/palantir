
"""
Orion ODA V3 - API Routes
========================
Implements REST Endpoints mapping DTOs to Domain Logic.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from lib.oda.api.dtos import (
    CreateProposalRequest, 
    ReviewProposalRequest, 
    ProposalResponse,
    StandardErrorResponse,
    ExecuteActionRequest,
    ActionResultResponse
)
from lib.oda.api.dependencies import get_repository
from lib.oda.ontology.storage.proposal_repository import (
    ProposalRepository, 
    ConcurrencyError, 
    ProposalNotFoundError
)
from lib.oda.ontology.objects.proposal import Proposal, ProposalStatus, ProposalPriority

logger = logging.getLogger("API")
router = APIRouter(prefix="/api/v1/proposals", tags=["Proposals"])

@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    req: CreateProposalRequest,
    repo: ProposalRepository = Depends(get_repository)
):
    """Submit a new Action Proposal."""
    # Convert DTO -> Domain
    proposal = Proposal(
        action_type=req.action_type,
        payload=req.payload,
        priority=ProposalPriority(req.priority),
        created_by="api_user" # Real auth would provide this
    )
    
    await repo.save(proposal, actor_id="api_user")
    logger.info(f"API: Proposal Created {proposal.id}")
    
    return proposal

@router.get("", response_model=List[ProposalResponse])
async def list_pending_proposals(
    repo: ProposalRepository = Depends(get_repository)
):
    """List all Proposals waiting for review."""
    proposals = await repo.find_pending()
    return proposals

@router.post("/{proposal_id}/review", response_model=StandardErrorResponse)
async def review_proposal(
    proposal_id: str,
    req: ReviewProposalRequest,
    repo: ProposalRepository = Depends(get_repository)
):
    """Approve or Reject a Proposal."""
    try:
        if req.decision == "approve":
            await repo.approve(proposal_id, req.reviewer_id, req.comment)
        elif req.decision == "reject":
            await repo.reject(proposal_id, req.reviewer_id, req.comment or "No reason provided")
            
        return StandardErrorResponse(
            code="SUCCESS", 
            message=f"Proposal {proposal_id} {req.decision}d successfully."
        )
        
    except ConcurrencyError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ProposalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found."
        )
@router.post("/execute", response_model=ActionResultResponse, status_code=status.HTTP_200_OK)
async def execute_action_endpoint(
    req: ExecuteActionRequest,
    # In a real app, we'd inject marshaler. For simplified DI here:
):
    """
    Directly execute a non-hazardous Action.
    """
    from lib.oda.runtime.marshaler import ToolMarshaler
    from lib.oda.ontology.actions import action_registry, ActionContext
    from datetime import datetime
    
    # 1. Governance Check
    meta = action_registry.get_metadata(req.action_type)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action '{req.action_type}' not found."
        )
        
    if meta.requires_proposal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Action '{req.action_type}' is hazardous and requires a Proposal. Use POST /proposals instead."
        )

    # 2. Execute via Marshaler
    marshaler = ToolMarshaler()
    context = ActionContext(actor_id="api_user", metadata={"source": "api"})
    
    result = await marshaler.execute_action(
        action_name=req.action_type,
        params=req.params,
        context=context
    )
    
    if result.success:
        # Wrap data if needed
        res_data = result.data
        if res_data is not None and not isinstance(res_data, dict):
            res_data = {"value": res_data}
            
        return ActionResultResponse(
            action_type=result.action_type,
            success=True,
            result=res_data,
            trace_id=context.correlation_id,
            timestamp=datetime.now()
        )
    else:
        # Action failed business logic
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Action failed: {result.error}",
        )
