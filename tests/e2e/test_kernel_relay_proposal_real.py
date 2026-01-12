import json
import os
import asyncio

import pytest

from lib.oda.ontology.objects.proposal import ProposalStatus
from lib.oda.ontology.storage.database import Database, DatabaseManager
from lib.oda.ontology.storage.proposal_repository import ProposalRepository
from lib.oda.ontology.storage.repositories import ActionLogRepository
from lib.oda.ontology.storage.learner_repository import LearnerRepository
from lib.oda.relay.queue import RelayQueue
from lib.oda.runtime.kernel import OrionRuntime


@pytest.mark.asyncio
async def test_kernel_relay_to_proposal_to_execution_real(tmp_path) -> None:
    prev_plan_mode = os.environ.get("ORION_PLAN_MODE")
    os.environ["ORION_PLAN_MODE"] = "deterministic"

    db = Database(tmp_path / "e2e_kernel.db")
    await db.initialize()
    token = DatabaseManager.set_context(db)

    try:
        q = RelayQueue()

        kernel = OrionRuntime()
        kernel.relay = q
        kernel.repo = ProposalRepository(db)
        kernel._proposal_semaphore = asyncio.Semaphore(1)

        prompt = "\n".join(
            [
                "OBJECTIVE: Deterministic E2E kernel test",
                'ACTION learning.save_state {"user_id":"u1","theta":0.1}',
                'ACTION learning.update_kb {"kb_id":"01","section":"Practice Exercise","content":"test"}',
            ]
        )

        task_id = await q.enqueue(prompt)
        task_payload = await q.dequeue()
        assert task_payload is not None
        assert task_payload["id"] == task_id

        response = await kernel._process_task_cognitive(task_payload)
        parsed = json.loads(response)
        assert parsed["task_id"] == task_id
        assert parsed["proposals_created"] == 1
        assert parsed["immediate_success"] == 1

        relay_task = await q.repo.find_by_id(task_id)
        assert relay_task is not None
        assert relay_task.status == "completed"
        assert relay_task.response

        learners = LearnerRepository(db)
        learner = await learners.get_by_user_id("u1")
        assert learner is not None
        assert learner.theta == 0.1

        pending = await kernel.repo.find_by_status(ProposalStatus.PENDING, limit=10)
        assert len(pending) == 1
        proposal = pending[0]
        assert proposal.action_type == "learning.update_kb"

        await kernel.repo.approve(proposal.id, reviewer_id="admin")
        await kernel._process_approved_proposals()

        executed = await kernel.repo.find_by_id(proposal.id)
        assert executed is not None
        assert executed.status == ProposalStatus.EXECUTED

        logs = await ActionLogRepository(db, publish_events=False).find_by_trace_id(task_id)
        assert {l.action_type for l in logs} >= {"learning.save_state", "learning.update_kb"}
        assert all(l.status == "SUCCESS" for l in logs)

    finally:
        if prev_plan_mode is None:
            os.environ.pop("ORION_PLAN_MODE", None)
        else:
            os.environ["ORION_PLAN_MODE"] = prev_plan_mode
        DatabaseManager.reset_context(token)
        await db.dispose()
