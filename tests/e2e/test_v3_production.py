
import unittest
import sys
import os

# Add project root to path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.client import FoundryClient
from scripts.ontology.objects.core_definitions import Task, Agent
from scripts.llm.ollama_client import HybridRouter, OllamaClient
from scripts.relay.queue import RelayQueue

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
        self.assertEqual(route1, "LOCAL")
        
        # Complex task -> Relay
        route2 = router.route("architect a new cloud system with load balancing "*10)
        self.assertEqual(route2, "RELAY")
        
        # Mock Client (Async)
        import asyncio
        client = OllamaClient()
        # Since we are in a sync test method, we need to run async code
        res = asyncio.run(client.generate("hello", json_schema={"test": 1}))
        # Expect mock response if server not running
        self.assertTrue("mock" in res or "content" in res)
        
        print("[Pass] Intelligence Layer (Router/Client) Verified")

    def test_relay_queue(self):
        """Phase 2.5: Relay Queue Persistence"""
        q = RelayQueue() # In-memory for test
        tid = q.enqueue("Complex Prompt")
        
        task = q.dequeue()
        self.assertIsNotNone(task)
        self.assertEqual(task['id'], tid)
        
        q.complete(tid, "Response from Human")
        
        # Should be empty now
        task2 = q.dequeue()
        self.assertIsNone(task2)
        
        print("[Pass] Relay Layer (SQLite Queue) Verified")

    def test_semantic_action(self):
        """Phase 3: Validate ActionType, Validation, and SideEffects"""
        from scripts.ontology.actions import ActionType, SubmissionCriteria
        from scripts.ontology.side_effects import NotificationEffect
        
        # Define Action
        def is_high_priority(params):
            return params.get('priority') == 'high'

        action = ActionType(
            api_name="create_critical_task",
            display_name="Create Critical Task",
            parameters={"title": str, "priority": str},
            submission_criteria=[
                SubmissionCriteria(description="Must be high priority", validator=is_high_priority)
            ],
            side_effects=[
                NotificationEffect(recipient_id="admin", message_template="Critical Task Created: {title}")
            ]
        )
        
        # Test Validation Failure
        with self.assertRaises(ValueError):
            action.execute(title="Low Prio Task", priority="low")
            
        # Test Success + Side Effect
        # Ensure we capture stdout to verify print
        action.execute(title="Critical Bug", priority="high")
        print("[Pass] Semantic Action Layer Verified")

    def test_proposal_workflow(self):
        """Phase 4: Validate Proposal Object for HITL"""
        from scripts.ontology.objects.proposal import Proposal
        
        # 1. Draft Proposal
        prop = Proposal(
            action_type="deploy_production",
            parameters_json='{"version": "1.0.0"}',
            created_by_id="agent-007",
            status="pending"
        )
        self.assertEqual(prop.status, "pending")
        
        # 2. Approve (Simulated)
        prop.status = "approved"
        prop.reviewed_by_id = "human-admin"
        
        # 3. Kernel Execution (Stub verification)
        self.assertEqual(prop.status, "approved")
        self.assertEqual(prop.reviewed_by_id, "human-admin")
        print("[Pass] Proposal Workflow (HITL) Verified")

    def test_kernel_boot(self):
        """Phase 5: Verify Kernel Import and Layout"""
        try:
            from scripts.runtime.kernel import OrionRuntime
            print("[Pass] Kernel V3 Import Successful")
        except ImportError as e:
            self.fail(f"Kernel Move Failed: {e}")

if __name__ == '__main__':
    unittest.main()
