from __future__ import annotations

from typing import Optional, List, Any
from lib.oda.ontology.storage.base_repository import GenericRepository
from lib.oda.ontology.storage.models import RelayTaskModel
# We might need a generic Pydantic object for RelayTask if we want full DTO separation, 
# strictly speaking ODA uses Pydantic between Repos and Managers.
# For RelayQueue legacy compat, we might return dicts or the Model itself if acceptable for now.
# However, ODA V3 emphasizes Repos returning Domain Objects.
# Let's define a simple Pydantic model here or reusing one? 
# I'll stick to returning the Model for now or Dict to match RelayQueue expectations, 
# but ideally we should define a Schema.
# Let's define it inline or use a dict for phase 3 transition.
# Actually, GenericRepository expects T (Domain Object) and M (Model).
# I need a Domain Object.

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone

class RelayTask(BaseModel):
    id: str
    prompt: str
    status: str
    response: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)

class RelayRepository(GenericRepository[RelayTask, RelayTaskModel]):
    """
    Repository for Relay Tasks.
    """
    model_class = RelayTaskModel
    domain_class = RelayTask

    def __init__(self, db_instance=None, publish_events: bool = True):
        super().__init__(db_instance, publish_events)

    def _to_domain(self, model: RelayTaskModel) -> RelayTask:
        return RelayTask.model_validate(model)

    def _create_model(self, entity: RelayTask, actor_id: str) -> RelayTaskModel:
        return RelayTaskModel(
            id=entity.id,
            version=1,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=actor_id,
            updated_by=actor_id,
            prompt=entity.prompt,
            response=entity.response,
            status=entity.status
        )

    def _get_update_values(
        self,
        entity: RelayTask,
        actor_id: str,
        new_version: int
    ) -> Dict[str, Any]:
        return {
            "prompt": entity.prompt,
            "response": entity.response,
            "status": entity.status,
            "version": new_version,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": actor_id
        }

    # Specialized methods for Queue semantics
    async def dequeue_pending(self) -> Optional[RelayTask]:
        """
        Atomic dequeue (find pending limit 1).
        Note: GenericRepository doesn't strictly support atomic 'select for update skip locked' easily 
        across generic backends, but with Postgres/SQLite we can try.
        For SQLite (current), simple find and update is okay given single-writer usually.
        """
        # We need a transaction.
        # We need a transaction.
        async with self.db.transaction() as session:
            # 1. Find one pending
            # Using raw select for speed/simplicity or sqlalchemy select
            from sqlalchemy import select
            stmt = select(RelayTaskModel).where(RelayTaskModel.status == "pending").limit(1).with_for_update()
            
            result = await session.execute(stmt)
            task_model = result.scalar_one_or_none()
            
            if task_model:
                # 2. Mark processing
                task_model.status = "processing"
                task_model.touch() # update timestamp
                # session commit happens on exit of transaction block
                return self._to_domain(task_model)
        
        return None
