
import logging
from sqlalchemy import select, func
from scripts.ontology.manager import ObjectManager
from scripts.ontology.db import objects_table
from scripts.ontology.schemas.governance import OrionActionLog
from scripts.ontology.schemas.memory import OrionInsight, InsightContent, InsightProvenance

logger = logging.getLogger("ConsolidationEngine")
logging.basicConfig(level=logging.INFO)

class ConsolidationMiner:
    """
    Phase 5 Engine: Turns Action History into Wisdom.
    """
    def __init__(self, manager: ObjectManager):
        self.manager = manager
        
    def mine_failures(self):
        """
        Scan for repeated failures to generate Anti-Patterns.
        """
        session = self.manager.default_session
        
        # SQL: Select error, count(*) from objects where type='OrionActionLog' and status='FAILURE' group by error
        # Since 'data' is JSON, querying detailed stats is hard in pure SQL without JSON extension enabled properly.
        # But we can query all FAILURE logs and process in memory for MVP.
        
        # 1. Fetch all Failure Logs
        # Limitation: This fetches ALL rows. V4 needs pagination/filtering by timestamp.
        stmt = select(objects_table).where(
            objects_table.c.type == "OrionActionLog"
        )
        rows = session.execute(stmt).fetchall()
        
        failures = []
        for row in rows:
            data = row.data
            if data.get("status") == "FAILURE":
                failures.append(data)
                
        logger.info(f"[Miner] Found {len(failures)} failed actions.")
        
        # 2. Cluster by Error Message
        error_clusters = {}
        for f in failures:
            msg = f.get("error")
            action = f.get("action_type")
            key = f"{action}::{msg}"
            error_clusters[key] = error_clusters.get(key, 0) + 1
            
        # 3. Generate Insights for clusters > threshold
        THRESHOLD = 2
        for key, count in error_clusters.items():
            if count >= THRESHOLD:
                self._generate_anti_pattern(key, count)

    def _generate_anti_pattern(self, key: str, count: int):
        action, error = key.split("::", 1)
        
        # Check if Insight already exists? (De-duplication)
        # For MVP, we'll just create one and let the user merge/dedupe later or use a deterministic ID.
        insight_id = f"INSIGHT-FAIL-{abs(hash(key))}"
        
        existing = self.manager.get(OrionInsight, insight_id)
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
                source_episodic_ids=[] # We could link the ActionLog IDs here
            )
        )
        self.manager.save(insight)

if __name__ == "__main__":
    om = ObjectManager()
    miner = ConsolidationMiner(om)
    miner.mine_failures()
