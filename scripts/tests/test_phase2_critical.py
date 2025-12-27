
import pytest
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure Path
WORKSPACE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(WORKSPACE_ROOT)

# Imports for Phase 2.1 (Memory)
from scripts.ontology.actions.memory_actions import SaveInsightAction, SavePatternAction

from scripts.ontology.actions import ActionContext
from scripts.simulation.core import ActionRunner
from scripts.ontology.manager import ObjectManager # Shim

# Imports for Phase 2.2 (LLM)
from scripts.ontology.actions.llm_actions import GeneratePlanAction
from scripts.llm.instructor_client import InstructorClient

# Imports for Phase 2.3 (Preprocessing)
from scripts.ontology.learning.algorithms.preprocessing import tokenize, flatten_json

# Imports for Phase 2.4 (Governance CLI)
from scripts.governance import list_proposals, approve_proposal

@pytest.mark.asyncio
async def test_memory_actions_persistence():
    """Verify Phase 2.1: SaveInsightAction works with ActionRunner."""
    from scripts.ontology.storage import initialize_database
    await initialize_database()
    
    action = SaveInsightAction()
    
    ctx = ActionContext(
        actor_id="test_user",
        correlation_id="test_corr_id",
        metadata={}
    )
    ctx.parameters = {
        "content": "Test Insight Phase 2",
        "provenance": {"method": "UnitTest"}, 
        "confidence": 0.9
    }
    
    # Use ActionRunner
    runner = ActionRunner(ObjectManager(), session=None)
    result = await runner.execute(action, ctx)
    
    assert result.success
    assert len(result.created_ids) == 1
    assert result.created_ids[0].startswith("INS-")

@pytest.mark.asyncio
async def test_llm_action_audit():
    """Verify Phase 2.2: GeneratePlanAction returns a Plan."""
    # Mock InstructorClient to avoid real API call
    with patch('scripts.llm.instructor_client.InstructorClient') as MockClient:
        mock_instance = MockClient.return_value
        # Mock generate return
        from scripts.ontology.plan import Plan
        mock_plan = Plan(
            id="test-plan-1", 
            plan_id="test-plan-1", 
            objective="Test Objective",
            goal="Test Goal", 
            jobs=[]
        )
        mock_instance.generate.return_value = mock_plan
        
        action = GeneratePlanAction()
        ctx = ActionContext(actor_id="test_llm", correlation_id="c1", metadata={})
        ctx.parameters = {"goal": "Test Goal", "model": "mock-model"}
        
        # We need to ensure lazy import inside apply_edits uses OUR mock?
        # Typically mocking at sys.modules or patch target is needed.
        # But 'scripts.ontology.actions.llm_actions.InstructorClient' is local import.
        # Patching 'scripts.llm.instructor_client.InstructorClient' should work if patched before import logic runs?
        # Actually, llm_actions imports 'scripts.llm.instructor_client'.
        
        runner = ActionRunner(ObjectManager(), session=None)
        result = await runner.execute(action, ctx)
        
        assert result.success
        # Plan is returned in edits?
        # My implementation returned (Plan, [edit]).
        assert result.edits[0].object_type == "Plan"

@pytest.mark.asyncio
async def test_preprocessing_move():
    """Verify Phase 2.3: Preprocessing functions import and work."""
    text = "Hello World! This is a test."
    tokens = tokenize(text)
    assert tokens == ["hello", "world", "this", "is", "a", "test"]
    
    nested = {"a": 1, "b": {"c": 2}, "d": [3, 4]}
    flat = flatten_json(nested)
    assert flat["a"] == 1
    assert flat["b.c"] == 2
    assert flat["d.0"] == 3
    assert flat["d.1"] == 4

@pytest.mark.asyncio
async def test_governance_cli():
    """Verify Phase 2.4: Governance functions definition."""
    # Just checking they run without error (dry run / smoke test).
    # Since they use DB, we'd need a mock DB or ensure env is clean.
    # We'll rely on import success and basic invocation catching exception.
    try:
        await list_proposals()
    except Exception as e:
        # It handles DB init internally?
        # If DB fails to init (e.g. strict permissions), catch it.
        # But generally in test env it should be fine.
        pytest.fail(f"Governance list_proposals failed: {e}")

