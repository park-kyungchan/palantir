"""
Orion Phase 5 - Learning Persistence Layer
Refactored to use ODA Storage (SQLAlchemy/Async)
Acts as an adapter for scripts.ontology.storage.learner_repository
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from lib.oda.ontology.learning.types import LearnerState, KnowledgeComponentState
from lib.oda.ontology.storage.learner_repository import LearnerRepository as ODALearnerRepository
from lib.oda.ontology.objects.learning import Learner
from lib.oda.ontology.storage.database import get_database

logger = logging.getLogger(__name__)

class LearnerRepository:
    """
    Adapter for ODA LearnerRepository to support LearnerState (domain) objects.
    Replaces direct aiosqlite usage with ODA ORM.
    """
    
    def __init__(self, db_path: str = None):
        # db_path is ignored, we use global ODA Database
        self.oda_repo = ODALearnerRepository(get_database())

    async def initialize(self) -> None:
        """
        Initialization is now handled by the generic Database.initialize().
        This method is kept for compatibility.
        """
        # Ensure generic DB is initialized
        await get_database().initialize()

    async def get_learner(self, user_id: str) -> Optional[LearnerState]:
        """
        Fetch LearnerState using ODA repository.
        """
        learner_obj = await self.oda_repo.get_by_user_id(user_id)
        
        if not learner_obj:
            return None
            
        # Map Ontology Object -> LearnerState
        knowledge_components = {}
        if learner_obj.knowledge_state:
            for k, v in learner_obj.knowledge_state.items():
                if isinstance(v, dict):
                    knowledge_components[k] = KnowledgeComponentState(**v)
        
        return LearnerState(
            user_id=learner_obj.user_id,
            theta=learner_obj.theta,
            knowledge_components=knowledge_components
        )

    async def save_learner(self, state: LearnerState) -> None:
        """
        Save LearnerState using ODA repository.
        """
        # Map LearnerState -> Ontology Object
        knowledge_state_dict = {
            k: v.model_dump() for k, v in state.knowledge_components.items()
        }
        
        learner_obj = Learner(
            user_id=state.user_id,
            theta=state.theta,
            knowledge_state=knowledge_state_dict,
            last_active=datetime.now().isoformat()
        )
        # Note: We don't have the original ID here easily if it's an update,
        # but ODALearnerRepository.save handles upsert by user_id lookup.
        
        await self.oda_repo.save(learner_obj)

    async def update_mastery(self, user_id: str, concept_id: str, new_p: float) -> Optional[float]:
        """
        Update a specific mastery record.
        """
        learner = await self.get_learner(user_id)
        if not learner:
            logger.warning(f"Learner {user_id} not found for mastery update")
            return None
            
        learner.update_mastery(concept_id, new_p)
        await self.save_learner(learner)
        return new_p
