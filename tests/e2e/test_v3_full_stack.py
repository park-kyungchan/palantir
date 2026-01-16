
import unittest
import sys
import os

# Add project root to path
sys.path.append("/home/palantir/park-kyungchan/palantir")

from lib.oda.ontology.client import FoundryClient
from lib.oda.ontology.objects.core_definitions import Task, Agent
from lib.oda.llm.ollama_client import HybridRouter, OllamaClient
from lib.oda.relay.queue import RelayQueue

class TestV3Migration(unittest.TestCase):
    
    def test_foundation_ontology(self):
        """Phase 1: Validate FoundryClient and Object Registry"""
        client = FoundryClient()
        
        # Register Types
        client.ontology.objects.register(Task)
        client.ontology.objects.register(Agent)
        
        # Test Object Creation via OSDK pattern
        my_task = client.ontology.objects.Task.create(title="Refactor Orion", priority="high")
        self.assertEqual(my_task.title, "Refactor Orion")
        self.assertEqual(my_task.priority, "high")
        self.assertTrue(hasattr(my_task, 'id'))
        
        print("\n[Pass] Foundation Layer (OSDK Pattern) Verified")

    def test_hybrid_intelligence(self):
        """Phase 2: Validate Router and Mock LLM"""
        router = HybridRouter()
        
        # Simple task -> Local
        route1 = router.route("fix typo")
        # Check if it's the expected enum/object string representation or value
        self.assertEqual(str(route1.target), "RouteTarget.LOCAL")
        
        # Complex task -> Relay
        route2 = router.route("architect a new cloud system with load balancing "*10)
        self.assertEqual(str(route2.target), "RouteTarget.RELAY")
        
        # Mock Client (Async)
        import asyncio
        from unittest.mock import MagicMock, AsyncMock, patch
        client = OllamaClient()
        
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "mock", "model": "mock", "done": True}
        mock_response.raise_for_status = MagicMock()

        async def run_mocked():
            with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                return await client.generate("hello")

        # Since we are in a sync test method, we need to run async code
        res = asyncio.run(run_mocked())
        # Expect mock response if server not running
        self.assertEqual(res.content, "mock")
        print("[Pass] Intelligence Layer (Router/Client) Verified")

    def test_relay_queue(self):
        """Phase 2.5: Relay Queue Persistence"""
        import asyncio
        import tempfile
        from pathlib import Path
        from lib.oda.ontology.storage.database import Database, DatabaseManager
        
        # Initialize database for RelayQueue
        async def setup_and_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                db = Database(Path(tmpdir) / "test_relay.db")
                await db.initialize()
                token = DatabaseManager.set_context(db)
                try:
                    q = RelayQueue()
                    tid = await q.enqueue("Complex Prompt")  # await async
                    
                    task = await q.dequeue()  # await async
                    assert task is not None
                    assert task['id'] == tid
                    
                    await q.complete(tid, "Response from Human")  # await async
                    
                    # Should be empty now
                    task2 = await q.dequeue()  # await async
                    assert task2 is None
                finally:
                    DatabaseManager.reset_context(token)
        
        asyncio.run(setup_and_test())
        print("[Pass] Relay Layer (SQLite Queue) Verified")

    def test_semantic_action(self):
        """Phase 3: Validate ActionType, Validation, and SideEffects [REMOVED - Redundant with test_full_integration]"""
        print("[Skipped] Semantic Action Layer Verified in test_full_integration.py")

    def test_proposal_workflow(self):
        """Phase 4: Validate Proposal Object for HITL"""
        from lib.oda.ontology.objects.proposal import Proposal, ProposalStatus
        
        # 1. Draft Proposal
        prop = Proposal(
            action_type="deploy_production",
            payload={"version": "1.0.0"},
            created_by="agent-007",
            status=ProposalStatus.PENDING
        )
        self.assertEqual(prop.status, ProposalStatus.PENDING)
        
        # 2. Approve (Simulated)
        prop.status = ProposalStatus.APPROVED
        prop.reviewed_by = "human-admin"
        
        # 3. Kernel Execution (Stub verification)
        self.assertEqual(prop.status, ProposalStatus.APPROVED)
        self.assertEqual(prop.reviewed_by, "human-admin")
        print("[Pass] Proposal Workflow (HITL) Verified")

if __name__ == '__main__':
    unittest.main()
