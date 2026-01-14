"""
Consolidation Miner: Turns Action History into Wisdom.

Migrated to ODA V3.0 (Async Repository Pattern).
"""

import asyncio
import logging
from typing import Optional

from lib.oda.ontology.storage import (
    initialize_database,
    ActionLogRepository,
    InsightRepository,
    Database,
)
from lib.oda.ontology.schemas.memory import OrionInsight, InsightContent, InsightProvenance

logger = logging.getLogger("ConsolidationEngine")
logging.basicConfig(level=logging.INFO)


class ConsolidationMiner:
    """
    Phase 5 Engine: Turns Action History into Wisdom.
    
    ODA V3.0 Migration: Uses async Repository pattern instead of ObjectManager.
    """
    
    def __init__(self, db: Database):
        self._db = db
        self._action_log_repo = ActionLogRepository(db)
        self._insight_repo = InsightRepository(db)
        
    async def mine_failures(self) -> None:
        """
        Scan for repeated failures to generate Anti-Patterns.
        """
        # Fetch all action logs via repository
        logs = await self._action_log_repo.find_all()
        
        failures = []
        for log in logs:
            if log.status == "FAILURE":
                failures.append(log)
                
        logger.info(f"[Miner] Found {len(failures)} failed actions.")
        
        # Cluster by Error Message
        error_clusters: dict[str, int] = {}
        for f in failures:
            msg = f.error or "Unknown"
            action = f.action_type or "Unknown"
            key = f"{action}::{msg}"
            error_clusters[key] = error_clusters.get(key, 0) + 1
            
        # Generate Insights for clusters > threshold
        THRESHOLD = 2
        for key, count in error_clusters.items():
            if count >= THRESHOLD:
                await self._generate_anti_pattern(key, count)

    async def _generate_anti_pattern(self, key: str, count: int) -> None:
        action, error = key.split("::", 1)
        
        # Deterministic ID for de-duplication
        insight_id = f"INSIGHT-FAIL-{abs(hash(key))}"
        
        # Check if Insight already exists
        existing = await self._insight_repo.find_by_id(insight_id)
        if existing:
            logger.info(f"[Miner] Insight {insight_id} already exists. Skipping.")
            return

        logger.info(f"[Miner] Creating NEW Insight for repeated failure: {key} (Count: {count})")
        
        insight = OrionInsight(
            id=insight_id,
            confidence_score=0.9,
            content=InsightContent(
                domain="governance",
                summary=f"Anti-Pattern Detected: Action '{action}' reliably fails with '{error}'",
                tags=["anti-pattern", "auto-generated", action]
            ),
            provenance=InsightProvenance(
                method="mining",
                source_episodic_ids=[]
            )
        )
        await self._insight_repo.save(insight, actor_id="consolidation-engine")


async def main() -> None:
    """Entry point for consolidation mining."""
    db = await initialize_database()
    miner = ConsolidationMiner(db)
    await miner.mine_failures()


if __name__ == "__main__":
    asyncio.run(main())
