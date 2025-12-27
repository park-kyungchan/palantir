from typing import Optional, Any
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert

from scripts.ontology.storage.database import Database, get_database
from scripts.ontology.storage.models import LearnerModel
from scripts.ontology.objects.learning import Learner

class LearnerRepository:
    """
    Persistence layer for Learner objects.
    Handles CRUD operations against the generic 'learners' table.
    """
    
    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_database()

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
                    updated_at=model.updated_at
                    # version handled by base?
                )
            return None

    async def save(self, learner: Learner, session: Optional[Any] = None) -> Learner:
        """Upsert a Learner object."""
        if session:
             return await self._save_internal(session, learner)
             
        async with self.db.transaction() as new_session:
            return await self._save_internal(new_session, learner)

    async def _save_internal(self, session, learner: Learner) -> Learner:
        # Check for existing by user_id
        stmt = select(LearnerModel).where(LearnerModel.user_id == learner.user_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            existing.theta = learner.theta
            existing.knowledge_state = learner.knowledge_state
            existing.last_active = learner.last_active
            await session.merge(existing)
            learner.id = existing.id
        else:
            # Create
            model = LearnerModel(
                user_id=learner.user_id,
                theta=learner.theta,
                knowledge_state=learner.knowledge_state,
                last_active=learner.last_active or ""
            )
            session.add(model)
            await session.flush() # To get ID
            learner.id = model.id
            
        return learner
