"""
Orion ODA V3.1 - LearnerRepository with OCC
============================================
Persistence layer for Learner objects with Optimistic Concurrency Control.
"""

from typing import Optional, Any
from sqlalchemy import select, update

from scripts.ontology.storage.database import Database, DatabaseManager
from scripts.ontology.storage.models import LearnerModel
from scripts.ontology.storage.exceptions import ConcurrencyError
from scripts.ontology.objects.learning import Learner


class LearnerRepository:
    """
    Persistence layer for Learner objects.
    Handles CRUD operations with OCC (Optimistic Concurrency Control).
    
    V3.1: Added OCC pattern matching ProposalRepository.
    """
    
    def __init__(self, db: Optional[Database] = None):
        # V3.1: Use DatabaseManager instead of deprecated get_database()
        self.db = db or DatabaseManager.get()

    async def get_by_user_id(self, user_id: str) -> Optional[Learner]:
        """Fetch a Learner by User ID."""
        async with self.db.transaction() as session:
            stmt = select(LearnerModel).where(LearnerModel.user_id == user_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return Learner(
                    id=model.id,
                    user_id=model.user_id,
                    theta=model.theta,
                    knowledge_state=model.knowledge_state,
                    last_active=model.last_active,
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                    version=model.version  # Include version for OCC
                )
            return None

    async def save(self, learner: Learner, actor_id: str = "system") -> Learner:
        """
        Save a Learner with OCC (Optimistic Concurrency Control).
        
        For updates, caller must increment version before calling save:
            learner.version += 1
            await repo.save(learner)
        
        Raises:
            ConcurrencyError: If version mismatch detected (concurrent modification)
        """
        async with self.db.transaction() as session:
            # 1. Check existence and version
            stmt = select(LearnerModel.version, LearnerModel.id).where(
                LearnerModel.user_id == learner.user_id
            )
            row = (await session.execute(stmt)).first()
            
            if row is None:
                # CREATE path
                model = LearnerModel(
                    user_id=learner.user_id,
                    theta=learner.theta,
                    knowledge_state=learner.knowledge_state,
                    last_active=learner.last_active or "",
                    version=learner.version or 1
                )
                session.add(model)
                await session.flush()
                learner.id = model.id
                learner.version = model.version
            else:
                db_version, db_id = row
                
                # 2. Version validation
                if learner.version != db_version + 1:
                    raise ConcurrencyError(
                        f"Learner {learner.user_id} version mismatch. "
                        f"DB={db_version}, Obj={learner.version}",
                        expected_version=db_version,
                        actual_version=learner.version
                    )
                
                expected_version = db_version
                
                # 3. Conditional UPDATE with WHERE version check
                stmt = (
                    update(LearnerModel)
                    .where(LearnerModel.user_id == learner.user_id)
                    .where(LearnerModel.version == expected_version)
                    .values(
                        theta=learner.theta,
                        knowledge_state=learner.knowledge_state,
                        last_active=learner.last_active,
                        version=learner.version
                    )
                )
                result = await session.execute(stmt)
                
                # 4. Rowcount check for race condition
                if result.rowcount == 0:
                    raise ConcurrencyError(
                        f"Learner {learner.user_id} modified by another transaction.",
                        expected_version=expected_version,
                        actual_version=None
                    )
                
                learner.id = db_id
        
        return learner

    async def find_by_id(self, learner_id: str) -> Optional[Learner]:
        """Fetch a Learner by ID."""
        async with self.db.transaction() as session:
            stmt = select(LearnerModel).where(LearnerModel.id == learner_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                return Learner(
                    id=model.id,
                    user_id=model.user_id,
                    theta=model.theta,
                    knowledge_state=model.knowledge_state,
                    last_active=model.last_active,
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                    version=model.version
                )
            return None

