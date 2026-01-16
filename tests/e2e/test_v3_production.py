
import unittest
import sys
import os
import asyncio
from typing import Dict, Any

# Add project root to path
sys.path.append("/home/palantir/park-kyungchan/palantir")

from lib.oda.ontology.objects.core_definitions import Task, Agent
from lib.oda.ontology.actions.task_actions import CreateTaskAction
from lib.oda.ontology.objects.proposal import Proposal, ProposalStatus
from lib.oda.ontology.actions import ActionContext
from lib.oda.llm.ollama_client import HybridRouter, OllamaClient, RouterConfig
from lib.oda.relay.queue import RelayQueue

class TestV3Migration(unittest.TestCase):
    
    def test_foundation_ontology(self):
        """Phase 1: Validate Object Registry and Types"""
        # Test Object Creation
        my_task = Task(title="Refactor Orion", priority="high")
        self.assertEqual(my_task.title, "Refactor Orion")
        self.assertEqual(my_task.priority, "high")
        self.assertTrue(len(my_task.id) == 36)
        
        print("\n[Pass] Foundation Layer (Ontology Objects) Verified")

    def test_hybrid_intelligence(self):
        """Phase 2: Validate Router and Client"""
        config = RouterConfig()
        router = HybridRouter(config)
        
        # Simple task -> Local
        d1 = router.route("fix typo")
        self.assertEqual(d1.target.value, "LOCAL")
        
        # Complex task -> Relay
        d2 = router.route("architect a new cloud system with load balancing "*10)
        self.assertEqual(d2.target.value, "RELAY")
        
        # Mock Client (Async)
        client = OllamaClient(config)
        # We expect this to fail connection if server down, which is fine, 
        # or succeed if mocked. The key is import matches.
        # Check attributes
        self.assertTrue(hasattr(client, 'generate'))
        
        print("[Pass] Intelligence Layer (Router/Client) Verified")

    def test_relay_queue(self):
        """Phase 2.5: Relay Queue Persistence"""
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
        """Phase 3: Validate ActionType"""
        action = CreateTaskAction()
        
        async def run_action():
            ctx = ActionContext.system()
            # Success
            res = await action.execute({'title': 'Critical Bug', 'priority': 'high'}, ctx)
            self.assertTrue(res.success)
            self.assertTrue(len(res.created_ids) > 0)
            
            # Failure
            res2 = await action.execute({'title': ''}, ctx)
            self.assertFalse(res2.success)
            
        asyncio.run(run_action())
        print("[Pass] Semantic Action Layer Verified")

    def test_proposal_workflow(self):
        """Phase 4: Validate Proposal Object for HITL"""
        # 1. Draft Proposal
        prop = Proposal(
            action_type="deploy_to_production",
            payload={"version": "1.0.0"},
            created_by="agent-007",
            status=ProposalStatus.DRAFT
        )
        self.assertEqual(prop.status, ProposalStatus.DRAFT)
        
        # 2. Submit
        prop.submit()
        self.assertEqual(prop.status, ProposalStatus.PENDING)
        
        # 3. Approve
        prop.approve(reviewer_id="human-admin", comment="LGTM")
        self.assertEqual(prop.status, ProposalStatus.APPROVED)
        self.assertEqual(prop.reviewed_by, "human-admin")
        
        print("[Pass] Proposal Workflow (HITL) Verified")

    def test_kernel_boot(self):
        """Phase 5: Verify Kernel Import"""
        try:
            from lib.oda.runtime.kernel import OrionRuntime
            print("[Pass] Kernel V3 Import Successful")
        except ImportError as e:
            self.fail(f"Kernel Move Failed: {e}")

if __name__ == '__main__':
    unittest.main()
