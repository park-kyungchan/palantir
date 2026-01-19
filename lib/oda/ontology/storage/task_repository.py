"""
ODA Storage - TaskRepository
============================

Minimal persistence layer for `Task` objects, used by Claude TodoWrite sync.

This repository is intentionally small and focused on the methods exercised by
`lib.oda.claude.todo_sync.TodoTaskSync`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select

from lib.oda.ontology.objects.task_types import Task
from lib.oda.ontology.storage.base_repository import TransactionalRepository
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.models import TaskModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _json_loads(value: Optional[str], default):
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


class TaskRepository(TransactionalRepository):
    def __init__(self, db: Database):
        super().__init__(db)

    def _to_model(self, task: Task, model: Optional[TaskModel] = None) -> TaskModel:
        m = model or TaskModel(id=task.id)

        m.title = task.title
        m.description = task.description
        m.priority = task.priority.value if hasattr(task.priority, "value") else str(task.priority)
        m.task_status = task.task_status.value if hasattr(task.task_status, "value") else str(task.task_status)

        m.assigned_to_id = task.assigned_to_id
        m.parent_task_id = task.parent_task_id

        m.tags = _json_dumps(task.tags)
        m.estimated_hours = task.estimated_hours
        m.actual_hours = task.actual_hours
        m.due_date = task.due_date
        m.completed_at = task.completed_at

        m.status = task.status.value if hasattr(task.status, "value") else str(task.status)
        m.created_by = task.created_by
        m.updated_by = task.updated_by
        m.created_at = task.created_at
        m.updated_at = task.updated_at
        m.version = task.version

        return m

    def _to_domain(self, model: TaskModel) -> Task:
        return Task(
            id=model.id,
            title=model.title,
            description=model.description,
            priority=model.priority,
            task_status=model.task_status,
            assigned_to_id=model.assigned_to_id,
            parent_task_id=model.parent_task_id,
            tags=_json_loads(model.tags, default=[]),
            estimated_hours=model.estimated_hours,
            actual_hours=model.actual_hours,
            due_date=model.due_date,
            completed_at=model.completed_at,
            status=model.status,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )

    async def save(self, task: Task, actor_id: str = "system") -> Task:
        async with self.session() as session:
            existing = await session.get(TaskModel, task.id)
            if existing is None:
                task.updated_by = actor_id
                task.updated_at = _utc_now()
                session.add(self._to_model(task))
            else:
                # OCC-lite: require client version == db_version + 1 when updating
                if task.version != existing.version + 1:
                    raise ValueError("Optimistic lock failure for task update")
                task.updated_by = actor_id
                task.updated_at = _utc_now()
                self._to_model(task, model=existing)

            await session.flush()
        return task

    async def get(self, task_id: str) -> Optional[Task]:
        async with self.session() as session:
            model = await session.get(TaskModel, task_id)
            if model is None:
                return None
        return self._to_domain(model)

    async def update(self, task: Task, actor_id: str = "system") -> Task:
        # For now, update is equivalent to save but requires existing row.
        async with self.session() as session:
            existing = await session.get(TaskModel, task.id)
            if existing is None:
                raise ValueError(f"Task not found: {task.id}")

            if task.version != existing.version + 1:
                raise ValueError("Optimistic lock failure for task update")

            task.updated_by = actor_id
            task.updated_at = _utc_now()
            self._to_model(task, model=existing)
            await session.flush()
        return task

    async def find_by_title(self, title: str) -> Optional[Task]:
        async with self.session() as session:
            stmt = select(TaskModel).where(TaskModel.title == title).limit(1)
            model = (await session.execute(stmt)).scalars().first()
            if model is None:
                return None
        return self._to_domain(model)

    async def list(
        self,
        tags: Optional[List[str]] = None,
        limit: int = 10_000,
        offset: int = 0,
    ) -> List[Task]:
        async with self.session() as session:
            stmt = select(TaskModel).order_by(TaskModel.created_at.desc())

            if tags:
                # Simple LIKE-based tag filtering for JSON-encoded tags.
                for tag in tags:
                    stmt = stmt.where(TaskModel.tags.like(f'%\"{tag}\"%'))

            stmt = stmt.offset(offset).limit(limit)
            models = (await session.execute(stmt)).scalars().all()

        return [self._to_domain(m) for m in models]


__all__ = ["TaskRepository"]

