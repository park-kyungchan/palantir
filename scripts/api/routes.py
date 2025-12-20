
"""
Orion ODA V3 - API Routes
========================
Implements REST Endpoints mapping DTOs to Domain Logic.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from scripts.api.dtos import (
    CreateProposalRequest, 
    ReviewProposalRequest, 
    ProposalResponse,
    StandardErrorResponse
)
from scripts.api.dependencies import get_repository
from scripts.ontology.storage.proposal_repository import (
    ProposalRepository, 
    ConcurrencyError, 
    ProposalNotFoundError
)
from scripts.ontology.objects.proposal import Proposal, ProposalStatus, ProposalPriority

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
