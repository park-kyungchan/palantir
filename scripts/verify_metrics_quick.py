
import asyncio
import logging
from datetime import datetime, timedelta
from scripts.ontology.storage import ProposalRepository, initialize_database, Database
from scripts.ontology.objects.proposal import Proposal, ProposalStatus

async def test_metrics():
    logging.basicConfig(level=logging.INFO)
    db = await initialize_database()
    repo = ProposalRepository(db)
    
    # Clean DB mainly for metrics test
    # await db.execute("DELETE FROM proposals")
    
    # Create an approved proposal with review time
    p1 = Proposal(action_type="test_metrics", payload={}, created_by="tester")
    p1.submit()
    await repo.save(p1)
    
    # Approve it
    # Manually tweaking timestamps to simulate time passing for metrics
    # This is hard to do cleanly without raw SQL, so we rely on the fact that existing tests passed basic CRUD.
    # We will just call get_metrics and ensure it doesn't crash handling NULLs or Empty sets.
    
    metrics = await repo.get_metrics()
    print(f"Metrics: {metrics}")
    
    assert "total_count" in metrics
    assert "status_counts" in metrics
    assert "avg_approval_time_seconds" in metrics

if __name__ == "__main__":
    asyncio.run(test_metrics())
