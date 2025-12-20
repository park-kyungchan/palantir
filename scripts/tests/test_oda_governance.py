
import asyncio
import sys
from dataclasses import dataclass
from typing import ClassVar, Type

# Add project root to path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.actions import ActionType, ActionRegistry, GovernanceEngine, register_action, ActionContext, EditOperation, ActionResult
from scripts.ontology.ontology_types import OntologyObject

# Mock Ontology Object
class MockObject(OntologyObject):
    pass

# output capture
results = []

# logic test
async def test_governance_engine():
    print("🧪 Test: ODA Governance Engine")
    
    # 1. Register a Safe Action
    @register_action
    class SafeAction(ActionType[MockObject]):
        api_name: ClassVar[str] = "test_safe_action"
        object_type: ClassVar[Type[OntologyObject]] = MockObject
        requires_proposal: ClassVar[bool] = False
        
        async def apply_edits(self, params, context):
            return None, []

    # 2. Register a Hazardous Action
    @register_action(requires_proposal=True)
    class HazardousAction(ActionType[MockObject]):
        api_name: ClassVar[str] = "test_hazardous_action"
        object_type: ClassVar[Type[OntologyObject]] = MockObject
        requires_proposal: ClassVar[bool] = True # Class attr backup
        
        async def apply_edits(self, params, context):
            return None, []

    # 3. Instantiate Engine
    # Note: register_action uses the global `action_registry` imported from actions.py
    # We need to make sure we are checking THAT registry
    from scripts.ontology.actions import action_registry as global_registry
    engine = GovernanceEngine(global_registry)

    # 4. Verify Policy
    policy_safe = engine.check_execution_policy("test_safe_action")
    print(f"   Action 'test_safe_action' -> Policy: {policy_safe}")
    assert policy_safe == "ALLOW_IMMEDIATE", "Safe action should be allowed immediately"

    policy_hzd = engine.check_execution_policy("test_hazardous_action")
    print(f"   Action 'test_hazardous_action' -> Policy: {policy_hzd}")
    assert policy_hzd == "REQUIRE_PROPOSAL", "Hazardous action should require proposal"

    policy_404 = engine.check_execution_policy("non_existent_action")
    print(f"   Action 'non_existent_action' -> Policy: {policy_404}")
    assert policy_404 == "DENY", "Unknown action should be denied"

    print("✅ Governance Engine Verified: Schema is driving Logic.")

if __name__ == "__main__":
    asyncio.run(test_governance_engine())
