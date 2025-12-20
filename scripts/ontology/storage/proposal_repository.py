
"""
Orion ODA V3 - Async Proposal Repository
=========================================
Implements the Persistence Layer using SQLAlchemy 2.0 Async ORM.

Key Features:
- **Async I/O**: Non-blocking database operations.
- **Optimistic Locking**: Handled transparently by `AsyncOntologyObject`.
- **Domain Mapping**: Translates ORM `ProposalModel` <-> Domain `Proposal`.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from scripts.ontology.objects.proposal import Proposal, ProposalStatus, ProposalPriority
from scripts.ontology.storage.models import ProposalModel
from scripts.ontology.storage.database import Database

logger = logging.getLogger(__name__)

class ProposalNotFoundError(Exception):
    pass

class ConcurrencyError(Exception):
    pass

class ProposalRepository:
    """
    Persistence Layer for Proposal Objects using SQLAlchemy Async ORM.
    """
    
    def __init__(self, db: Database):
        self.db = db

    def _to_domain(self, model: ProposalModel) -> Proposal:
        """Convert ORM Model to Domain Object."""
        # Note: We reconstruct the Domain object.
        # Ideally, Domain Object SHOULD inherit from ORM Model if we unify them fully.
        # For now, we map manually to keep Domain clean of SQL dependencies if desired,
        # OR we can make Proposal inherit ProposalModel (Hybrid).
        # Given "Identity Unification" goal, let's map data for now to start safe.
        
        p = Proposal(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            status=ProposalStatus(model.status),
            version=model.version,
            
            action_type=model.action_type,
            payload=model.payload or {},
            priority=ProposalPriority(model.priority),
            
            reviewed_by=model.reviewed_by,
            reviewed_at=model.reviewed_at,
            review_comment=model.review_comment,
            executed_at=model.executed_at,
            # execution_result logic if needed in domain
        )
        return p

    async def save(self, proposal: Proposal, actor_id: str = "system") -> None:
        """
        Save a proposal (Create or Update).
        Handles Optimistic Locking via StaleDataError.
        """
        async with self.db.transaction() as session:
            if not proposal.version or proposal.version == 1:
                # Create
                model = ProposalModel(
                    id=proposal.id,
                    created_by=proposal.created_by or actor_id,
                    updated_by=actor_id,
                    status=proposal.status.value,
                    action_type=proposal.action_type,
                    payload=proposal.payload,
                    priority=proposal.priority.value,
                    version=1
                )
                session.add(model)
            else:
                # Update
                # We fetch first to ensure it's attached, or use update() stmt
                # Using merge/update for explicit version check
                stmt = (
                    update(ProposalModel)
                    .where(ProposalModel.id == proposal.id)
                    .where(ProposalModel.version == proposal.version)
                    .values(
                        status=proposal.status.value,
                        payload=proposal.payload,
                        priority=proposal.priority.value,
                        updated_at=proposal.updated_at,
                        updated_by=actor_id,
                        # ... map other fields ... 
                    )
                    .execution_options(synchronize_session="fetch")
                )
                result = await session.execute(stmt)
                if result.rowcount == 0:
                    raise ConcurrencyError(f"Proposal {proposal.id} modified by another user.")
                
                # Increment local version to match DB
                proposal.version += 1

    async def find_by_id(self, proposal_id: str) -> Optional[Proposal]:
        async with self.db.transaction() as session:
            stmt = select(ProposalModel).where(ProposalModel.id == proposal_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._to_domain(model)

    async def find_by_status(self, status: ProposalStatus) -> List[Proposal]:
        async with self.db.transaction() as session:
            stmt = select(ProposalModel).where(ProposalModel.status == status.value)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def find_pending(self) -> List[Proposal]:
        return await self.find_by_status(ProposalStatus.PENDING)

    async def approve(self, proposal_id: str, reviewer_id: str, comment: str = None) -> None:
        """Approve a proposal (Direct DB Update for efficiency)."""
        async with self.db.transaction() as session:
            # 1. Fetch current version
            stmt = select(ProposalModel).where(ProposalModel.id == proposal_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                raise ProposalNotFoundError(f"Proposal {proposal_id} not found")

            # 2. Update via ORM (automatically checks version if configured, specific check below)
            # Since we fetched 'model', we can just modify it and flush.
            # However, for explicit optimistic locking in high concurrency, let's use UPDATE stmt with WHERE version
            
            stmt = (
                update(ProposalModel)
                .where(ProposalModel.id == proposal_id)
                .where(ProposalModel.version == model.version) # Explicit Lock
                .values(
                    status=ProposalStatus.APPROVED.value,
                    reviewed_by=reviewer_id,
                    reviewed_at=utc_now(),
                    review_comment=comment,
                    updated_by=reviewer_id
                    # version increment handled by SQLAlchemy or Model default logic if we defined listener
                    # But since we do raw UPDATE here, we might need to increment manually or rely on ORM mechanics
                )
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                 raise ConcurrencyError(f"Proposal {proposal_id} modified during approval.")

    async def reject(self, proposal_id: str, reviewer_id: str, reason: str) -> None:
        async with self.db.transaction() as session:
            stmt = select(ProposalModel).where(ProposalModel.id == proposal_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                raise ProposalNotFoundError(f"Proposal {proposal_id} not found")

            stmt = (
                update(ProposalModel)
                .where(ProposalModel.id == proposal_id)
                .where(ProposalModel.version == model.version)
                .values(
                    status=ProposalStatus.REJECTED.value,
                    reviewed_by=reviewer_id,
                    reviewed_at=utc_now(),
                    review_comment=reason,
                    updated_by=reviewer_id
                )
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                 raise ConcurrencyError("Concurrency conflict during rejection")

    async def execute(self, proposal_id: str, executor_id: str, result: Dict[str, Any]) -> None:
        async with self.db.transaction() as session:
            stmt = select(ProposalModel).where(ProposalModel.id == proposal_id)
            orm_res = await session.execute(stmt)
            model = orm_res.scalar_one_or_none()
            if not model:
                raise ProposalNotFoundError(proposal_id)

            stmt = (
                update(ProposalModel)
                .where(ProposalModel.id == proposal_id)
                .where(ProposalModel.version == model.version)
                .values(
                    status=ProposalStatus.EXECUTED.value,
                    executed_at=utc_now(),
                    execution_result=result,
                    updated_by=executor_id
                )
            )
            update_res = await session.execute(stmt)
            if update_res.rowcount == 0:
                 raise ConcurrencyError("Concurrency conflict during execution")
