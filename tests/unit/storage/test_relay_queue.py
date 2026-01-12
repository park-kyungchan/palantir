import pytest

from lib.oda.ontology.storage.database import Database, DatabaseManager
from lib.oda.relay.queue import RelayQueue


@pytest.mark.asyncio
async def test_relay_queue_persists_and_dequeues(tmp_path) -> None:
    db = Database(tmp_path / "test_relay.db")
    await db.initialize()

    token = DatabaseManager.set_context(db)
    try:
        queue = RelayQueue()
        task_id = await queue.enqueue("Complex Prompt")

        task = await queue.dequeue()
        assert task is not None
        assert task["id"] == task_id
        assert task["status"] == "processing"

        await queue.complete(task_id, "Response from Human")
        task2 = await queue.dequeue()
        assert task2 is None
    finally:
        DatabaseManager.reset_context(token)
        await db.dispose()

