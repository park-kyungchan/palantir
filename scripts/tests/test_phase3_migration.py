import pytest
import asyncio
import os
import json
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from scripts.ontology.actions.learning_actions import SaveLearnerStateAction
from scripts.simulation.core import ActionContext, ActionRunner
from scripts.ontology.manager import ObjectManager, ConcurrencyError
from scripts.ontology.storage import get_database, initialize_database
from scripts.cognitive.types import LearnerState
from scripts.cognitive.learner import LearnerManager

# Mock Traces for Consolidation
MOCK_TRACE = {
    "trace": {"id": "trace-1", "status": "FAILED"},
    "events": [
        {
            "event_type": "ERROR",
            "component": "Executor",
            "details": {"error": "ImportError: No module named 'foo'"}
        },
        {
            "event_type": "ActionFailed",
            "details": {"error": "ImportError: No module named 'bar'"}
        }
    ]
}

@pytest.mark.asyncio
async def test_save_learner_state_action():
    """Verify ODA compliance for Learner State persistence."""
    await initialize_database()
    
    action = SaveLearnerStateAction()
    user_id = f"user-{uuid.uuid4()}"
    params = {
        "user_id": user_id,
        "theta": 1.5,
        "knowledge_state": {"concept_A": {"id": "concept_A", "name": "A", "mastery_probability": 0.8}}
    }
    
    ctx = ActionContext(actor_id="system_test")
    # ODA pattern: params passed to execute, which calls validate
    
    # Use Runner for full lifecycle (Audit Log integration check)
    runner = ActionRunner(get_database())
    # runner.execute reads params from ctx.parameters or ctx.metadata["params"]
    ctx.parameters = params
    
    result = await runner.execute(action, ctx)
    
    assert result.success
    assert len(result.created_ids) > 0 or len(result.modified_ids) > 0
    assert "saved" in result.message

@pytest.mark.asyncio
async def test_learner_manager_persistence():
    """Verify LearnerManager uses ActionRunner correctly."""
    await initialize_database()
    
    manager = LearnerManager()
    user_id = f"student-{uuid.uuid4()}"
    
    # 1. Update Mastery (trigger save)
    # We need to mock _save_state or test the whole flow?
    # Actual flow uses DB.
    
    new_state = await manager.update_concept_mastery(user_id, "recursion", True)
    
    assert new_state.knowledge_components["recursion"].mastery_probability > 0.1
    
    # 2. Verify Persistence via Repo directly to confirm Action worked
    repo = manager.repo
    saved_obj = await repo.get_by_user_id(user_id)
    assert saved_obj is not None
    assert saved_obj.theta > 0.0 # BKT increases theta on success

@pytest.mark.asyncio
async def test_consolidation_logic():
    """Verify Consolidation Engine logic (mocked traces)."""
    # We verify the transform logic without running full consolidate loop on FS.
    from scripts.consolidate import transform_to_transactions
    
    traces = [MOCK_TRACE, MOCK_TRACE] # Need >1 for mining
    transactions = transform_to_transactions(traces)
    
    assert len(transactions) == 2
    assert "status=FAILED" in transactions[0]
    assert "error_type=ImportError" in transactions[0]

@pytest.mark.asyncio
async def test_relay_queue_persistence():
    """Verify RelayQueue uses ODA persistence (Async)."""
    await initialize_database()
    from scripts.relay.queue import RelayQueue
    
    queue = RelayQueue()
    
    # Clean up table to ensure isolation
    from sqlalchemy import text
    async with get_database().transaction() as session:
         await session.execute(text("DELETE FROM relay_tasks"))
    
    # 1. Enqueue
    prompt = "Test ODA Queue"
    task_id = await queue.enqueue(prompt)
    assert task_id is not None
    
    # 2. Dequeue
    task = await queue.dequeue()
    assert task is not None
    assert task['id'] == task_id
    assert task['prompt'] == prompt
    assert task['status'] == 'processing' # Dequeue marks it processing
    
    # 3. Complete
    await queue.complete(task_id, "Done")
    
    # Verify in DB directly
    db = get_database()
    repo = queue.repo
    stored_task = await repo.find_by_id(task_id)
    assert stored_task.status == 'completed'
    assert stored_task.response == "Done"

@pytest.mark.asyncio
async def test_execute_logic_action():
    """Verify ExecuteLogicAction integration."""
    from scripts.ontology.actions.logic_actions import ExecuteLogicAction
    
    action = ExecuteLogicAction()
    # Mock Engine to avoid real LLM calls
    action.engine = MagicMock()
    # action.engine.analyze = AsyncMock(return_value={"result": "mock"}) # If needed
    
    ctx = ActionContext(actor_id="logic_tester")
    params = {"function_name": "TestLogic", "input_data": {"foo": "bar"}}
    
    # Test apply_edits directly
    result, edits = await action.apply_edits(params, ctx)
    
    assert result["status"] == "executed"
    assert result["function"] == "TestLogic"
    assert edits == [] # No side effects

if __name__ == "__main__":
    asyncio.run(test_save_learner_state_action())
    asyncio.run(test_learner_manager_persistence())
    asyncio.run(test_consolidation_logic())
    asyncio.run(test_relay_queue_persistence())
    asyncio.run(test_execute_logic_action())
