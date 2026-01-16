"""
Task Repository - Persistence layer for Task objects.
Follows ProposalRepository pattern.
"""
from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from lib.oda.ontology.objects.task_types import Task, TaskStatus, TaskPriority
from lib.oda.ontology.storage.models import TaskModel
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.actions import EditOperation, EditType

logger = logging.getLogger(__name__)

class TaskRepository:
    """Repository for Task CRUD operations with ORM mapping."""

    def __init__(self, db: Database):
        self.db = db

    def _to_domain(self, model: TaskModel) -> Task:
        """Convert ORM Model to Pydantic Domain Object."""
        return Task(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            version=model.version,
            title=model.title,
            description=model.description or "",
            priority=TaskPriority(model.priority),
            task_status=TaskStatus(model.task_status),
            assigned_to_id=model.assigned_to_id,
            parent_task_id=model.parent_task_id,
            tags=model.tags or [],
            estimated_hours=model.estimated_hours,
            due_date=model.due_date,
            completed_at=model.completed_at,
        )

    def _to_model(self, task: Task, actor_id: str) -> TaskModel:
        """Convert Pydantic Domain Object to ORM Model."""
        return TaskModel(
            id=task.id,
            created_by=task.created_by or actor_id,
            updated_by=actor_id,
            title=task.title,
            description=task.description,
            priority=task.priority.value if hasattr(task.priority, 'value') else task.priority,
            task_status=task.task_status.value if hasattr(task.task_status, 'value') else task.task_status,
            assigned_to_id=task.assigned_to_id,
            parent_task_id=task.parent_task_id,
            tags=task.tags,
            estimated_hours=task.estimated_hours,
            due_date=task.due_date,
            completed_at=task.completed_at,
            version=task.version,
        )

    async def save(self, task: Task, actor_id: str = "system") -> None:
        """Save a Task (Create or Update)."""
        async with self.db.transaction() as session:
            stmt = select(TaskModel.version).where(TaskModel.id == task.id)
            row = (await session.execute(stmt)).first()

            if row is None:
                # Create
                model = self._to_model(task, actor_id)
                session.add(model)
                logger.info(f"Created Task: {task.id}")
            else:
                # Update with version check
                db_version = row[0]
                if task.version != db_version + 1:
                    raise ValueError(f"Version mismatch: expected {db_version + 1}, got {task.version}")

                stmt = (
                    update(TaskModel)
                    .where(TaskModel.id == task.id)
                    .where(TaskModel.version == db_version)
                    .values(
                        title=task.title,
                        description=task.description,
                        priority=task.priority.value if hasattr(task.priority, 'value') else task.priority,
                        task_status=task.task_status.value if hasattr(task.task_status, 'value') else task.task_status,
                        assigned_to_id=task.assigned_to_id,
                        tags=task.tags,
                        updated_by=actor_id,
                        version=task.version,
                    )
                )
                await session.execute(stmt)
                logger.info(f"Updated Task: {task.id}")

    async def find_by_id(self, task_id: str) -> Optional[Task]:
        """Find Task by ID."""
        async with self.db.transaction() as session:
            stmt = select(TaskModel).where(TaskModel.id == task_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def find_by_status(self, status: TaskStatus) -> List[Task]:
        """Find all Tasks with given status."""
        async with self.db.transaction() as session:
            stmt = select(TaskModel).where(TaskModel.task_status == status.value)
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def apply_edit_operation(self, edit: EditOperation, actor_id: str) -> None:
        """
        Apply an EditOperation to Task storage.
        This is the key method for Kernel integration.
        """
        async with self.db.transaction() as session:
            if edit.edit_type == EditType.CREATE:
                changes = edit.changes
                priority = changes.get("priority", "medium")
                if hasattr(priority, 'value'):
                    priority = priority.value

                model = TaskModel(
                    id=edit.object_id,
                    title=changes["title"],
                    description=changes.get("description", ""),
                    priority=priority,
                    task_status="pending",
                    tags=changes.get("tags", []),
                    created_by=actor_id,
                    updated_by=actor_id,
                    version=1,
                )
                session.add(model)

            elif edit.edit_type == EditType.MODIFY:
                stmt = (
                    update(TaskModel)
                    .where(TaskModel.id == edit.object_id)
                    .values(**edit.changes, updated_by=actor_id)
                )
                await session.execute(stmt)

            elif edit.edit_type == EditType.DELETE:
                stmt = (
                    update(TaskModel)
                    .where(TaskModel.id == edit.object_id)
                    .values(status="deleted", updated_by=actor_id)
                )
                await session.execute(stmt)
