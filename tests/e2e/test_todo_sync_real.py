from __future__ import annotations

from datetime import datetime

import pytest

from lib.oda.claude.protocol_adapter import TodoWriteManager
from lib.oda.claude.todo_sync import TodoTaskSync, TodoStatus
from lib.oda.ontology.storage.database import Database, DatabaseManager
from lib.oda.ontology.storage.task_repository import TaskRepository


@pytest.mark.asyncio
async def test_todo_task_sync_persists_and_updates_real(tmp_path) -> None:
    db = Database(tmp_path / "e2e_todo_sync.db")
    await db.initialize()
    token = DatabaseManager.set_context(db)

    try:
        sync = TodoTaskSync()
        task = await sync.create_task_from_todo(
            content="Test todo item",
            status=TodoStatus.PENDING,
            trace_id="trace-1",
            actor_id="tester",
        )
        assert task.id

        repo = TaskRepository(db)
        saved = await repo.find_by_id(task.id)
        assert saved is not None
        assert "todowrite" in (saved.tags or [])
        assert "trace:trace-1" in (saved.tags or [])

        timestamp_str = saved.description.rsplit(" ", 1)[-1]
        assert datetime.fromisoformat(timestamp_str).tzinfo is not None

        updated = await sync.update_task_status(
            task_id=task.id,
            new_status=TodoStatus.COMPLETED,
            actor_id="tester",
        )
        assert updated is not None
        assert updated.completed_at is not None

        loaded = await repo.find_by_id(task.id)
        assert loaded is not None
        assert loaded.completed_at is not None

        todos = await sync.load_todos_from_tasks(trace_id="trace-1")
        assert any(t.task_id == task.id for t in todos)

    finally:
        DatabaseManager.reset_context(token)
        await db.dispose()


@pytest.mark.asyncio
async def test_todo_write_manager_initializes_stages_real(tmp_path) -> None:
    db = Database(tmp_path / "e2e_todo_write_manager.db")
    await db.initialize()
    token = DatabaseManager.set_context(db)

    try:
        manager = TodoWriteManager()
        todos_payload = await manager.initialize_stages(trace_id="trace-2")
        assert len(todos_payload) == 3

        stage_todos = manager.get_stage_todos()
        assert stage_todos
        assert all(not tid.startswith("local_") for tid in stage_todos.values())

        repo = TaskRepository(db)
        for task_id in stage_todos.values():
            saved = await repo.find_by_id(task_id)
            assert saved is not None
            assert "todowrite" in (saved.tags or [])
            assert "trace:trace-2" in (saved.tags or [])

    finally:
        DatabaseManager.reset_context(token)
        await db.dispose()

