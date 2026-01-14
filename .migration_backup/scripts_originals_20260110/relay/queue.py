import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime, timezone

from lib.oda.ontology.storage.database import DatabaseManager
from lib.oda.ontology.storage.relay_repository import RelayRepository
from lib.oda.ontology.storage.models import RelayTaskModel
# Import domain object if needed, or use dict for compat

logger = logging.getLogger(__name__)

class RelayQueue:
    """
    ODA-Compliant Async Relay Queue.
    Backed by RelayRepository (Postgres/SQLite via SQLAlchemy Async).
    """
    def __init__(self):
        # V3.1: Use DatabaseManager instead of deprecated get_database()
        self.db = DatabaseManager.get()
        self.repo = RelayRepository(self.db)
        # Ensure 'relay_tasks' table exists? Base.metadata.create_all handles it on boot.
        # Ensure 'relay_tasks' table exists? Base.metadata.create_all handles it on boot.

    async def enqueue(self, prompt: str) -> str:
        """
        Enqueue a task asynchronously.
        Returns task_id.
        """
        # Create domain object or use model directly via repo specific methods?
        # RelayRepository relies on RelayTask domain object.
        # Let's import RelayTask from repository file (helper)
        from lib.oda.ontology.storage.relay_repository import RelayTask as RelayTaskDomain
        import uuid
        
        task_id = str(uuid.uuid4())
        task = RelayTaskDomain(
            id=task_id,
            prompt=prompt,
            status="pending",
            created_at=datetime.now(timezone.utc), # Pydantic will handle this? Repo model defaults.
            updated_at=datetime.now(timezone.utc),
            version=1,
            response=None
        )
        
        await self.repo.save(task)
        logger.info(f"[RelayQueue] Enqueued task {task_id}")
        return task_id

    async def dequeue(self) -> Optional[Dict]:
        """
        Atomic Dequeue: Find pending -> Mark processing.
        Returns dict for compatibility.
        """
        task = await self.repo.dequeue_pending()
        if task:
            return task.model_dump()
        return None

    async def complete(self, task_id: str, response: str):
        """
        Mark task as completed.
        """
        # Repo doesn't have partial update easily unless we fetch first.
        # But we can use repo.save() with updated fields.
        task = await self.repo.find_by_id(task_id)
        if task:
            task.status = "completed"
            task.response = response
            task.version += 1
            await self.repo.save(task)
            logger.info(f"[RelayQueue] Completed task {task_id}")
        else:
            logger.warning(f"[RelayQueue] Task {task_id} not found for completion.")

    # =========================================================================
    # ASYNC WRAPPERS (Aliases for Compatibility)
    # =========================================================================
    
    async def enqueue_async(self, prompt: str) -> str:
        return await self.enqueue(prompt)

    async def dequeue_async(self) -> Optional[Dict]:
        return await self.dequeue()

    async def complete_async(self, task_id: str, response: str) -> None:
        await self.complete(task_id, response)
