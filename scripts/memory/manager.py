
import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional

# --- ODA Integration ---
from scripts.ontology.storage.database import initialize_database, get_database, Database
from scripts.ontology.storage.repositories import InsightRepository, PatternRepository
from scripts.ontology.actions.memory_actions import SaveInsightAction, SavePatternAction
from scripts.simulation.core import ActionRunner, ActionContext

logger = logging.getLogger("HybridMemoryManager")

class MemoryManager:
    """
    ODA-Compliant Memory Manager.
    Delegates persistence to ActionType and Repositories.
    """
    
    def __init__(self):
        # We assume database will be initialized by the caller or lazily
        self._db: Optional[Database] = None
        
    async def initialize(self):
        """Async initialization of database connection."""
        self._db = await initialize_database()
        
    def _ensure_manager_facade(self):
        """Temporary shim to provide ObjectManager to ActionRunner."""
        from scripts.ontology.manager import ObjectManager
        return ObjectManager()

    async def save_object(self, obj_type: str, data: Dict[str, Any]) -> str:
        """
        Persist object via ODA Action.
        Returns the ID of the saved object.
        """
        if self._db is None:
            await self.initialize()
            
        # Instantiate ActionRunner with the shim
        runner = ActionRunner(self._ensure_manager_facade(), session=None)
        
        # Select Action
        if obj_type == "insight":
            action = SaveInsightAction()
        elif obj_type == "pattern":
            action = SavePatternAction()
        else:
            raise ValueError(f"Unknown object type: {obj_type}")
            
        # Context
        # We need a dummy actor_id for now, or trace context
        ctx = ActionContext(
            actor_id="memory_manager",
            correlation_id=f"mem-save-{os.urandom(4).hex()}",
            metadata={"params": data}
        )
        ctx.parameters = data # Legacy compatibility for some validators
        
        # Execute
        result = await runner.execute(action, ctx)
        
        if not result.success:
            raise RuntimeError(f"Memory Save Failed: {result.error}")
        
        # Return ID (assuming 1 item created)
        if result.changes and "created" in result.changes:
            return result.changes["created"][0]
            
        return data.get("id")

    async def search(self, query: str, limit: int = 5, mode: str = "hybrid") -> List[Dict[str, Any]]:
        """
        Unified Search accessing InsightRepository and PatternRepository.
        Note: Vector search is temporarily disabled in Phase 2 migration.
        """
        if self._db is None:
            await self.initialize()
            
        insights_repo = InsightRepository(self._db)
        patterns_repo = PatternRepository(self._db)
        
        # Parallel Search
        # ODA Repositories currently implement .search() (SQL LIKE)
        # We run both and merge
        
        t1 = asyncio.create_task(insights_repo.search(query, limit=limit))
        # PatternRepo might not have 'search' method exposed in generic interface?
        # Checking GenericRepository... NO search method in base.
        # Checking Repositories.py... InsightRepository HAS search. PatternRepository DOES NOT.
        # So we can only search Insights for now via text.
        
        insights = await t1
        
        # Convert to dicts for compatibility
        results = []
        for i in insights:
            # Simple scoring based on simple match (Repository search uses LIKE)
            results.append({
                "id": i.id,
                "type": "insight",
                "score": 1.0, # Dummy score
                "content": i.model_dump()
            })
            
        # TODO: Implement Pattern Search in PatternRepository
        
        return results[:limit]

