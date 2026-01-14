"""
TodoWrite ↔ ODA Task Synchronization

Synchronizes Claude Code's native TodoWrite tool with ODA Task objects,
enabling persistent task tracking across sessions.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ODA imports (schema-first)
from lib.oda.ontology.objects.task_types import Task, TaskStatus, TaskPriority
from lib.oda.ontology.storage.database import DatabaseManager
from lib.oda.ontology.storage.task_repository import TaskRepository


class TodoStatus(str, Enum):
    """Claude Code TodoWrite status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Status mapping: TodoWrite → ODA TaskStatus
TODO_TO_TASK_STATUS: Dict[TodoStatus, TaskStatus] = {
    TodoStatus.PENDING: TaskStatus.PENDING,
    TodoStatus.IN_PROGRESS: TaskStatus.IN_PROGRESS,
    TodoStatus.COMPLETED: TaskStatus.COMPLETED,
}

# Reverse mapping: ODA TaskStatus → TodoWrite
TASK_TO_TODO_STATUS: Dict[TaskStatus, TodoStatus] = {
    TaskStatus.PENDING: TodoStatus.PENDING,
    TaskStatus.IN_PROGRESS: TodoStatus.IN_PROGRESS,
    TaskStatus.COMPLETED: TodoStatus.COMPLETED,
    TaskStatus.BLOCKED: TodoStatus.PENDING,  # Map BLOCKED to pending
    TaskStatus.CANCELLED: TodoStatus.COMPLETED,  # Map CANCELLED to completed
}


@dataclass
class TodoItem:
    """Represents a TodoWrite item."""
    content: str
    status: TodoStatus
    active_form: str
    task_id: Optional[str] = None  # Link to ODA Task


class TodoTaskSync:
    """
    Synchronizes Claude Code TodoWrite with ODA Task objects.

    Usage:
        sync = TodoTaskSync()

        # Create task from todo
        task = await sync.create_task_from_todo(
            content="Implement feature X",
            status=TodoStatus.PENDING
        )

        # Update task when todo changes
        await sync.update_task_status(task.id, TodoStatus.COMPLETED)

        # Load todos from existing tasks
        todos = await sync.load_todos_from_tasks(trace_id="plan-123")
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path(".agent/tmp/ontology.db")
        self._repository: Optional[TaskRepository] = None

    async def _get_repository(self) -> TaskRepository:
        """Get or initialize TaskRepository."""
        if self._repository is None:
            await DatabaseManager.initialize(self.db_path)
            self._repository = TaskRepository()
        return self._repository

    async def create_task_from_todo(
        self,
        content: str,
        status: TodoStatus,
        priority: TaskPriority = TaskPriority.MEDIUM,
        trace_id: Optional[str] = None,
        actor_id: str = "claude_code_agent",
    ) -> Task:
        """
        Create an ODA Task from a TodoWrite item.

        Args:
            content: Todo content (becomes task title)
            status: TodoWrite status
            priority: Task priority (default MEDIUM)
            trace_id: Optional trace ID for correlation
            actor_id: ID of creating agent

        Returns:
            Created Task object
        """
        repository = await self._get_repository()

        task = Task(
            title=content,
            description=f"Created from TodoWrite at {datetime.utcnow().isoformat()}",
            priority=priority,
            task_status=TODO_TO_TASK_STATUS[status],
            tags=["todowrite", "claude_code"],
        )

        if trace_id:
            task.tags.append(f"trace:{trace_id}")

        saved_task = await repository.save(task, actor_id=actor_id)
        return saved_task

    async def update_task_status(
        self,
        task_id: str,
        new_status: TodoStatus,
        actor_id: str = "claude_code_agent",
    ) -> Optional[Task]:
        """
        Update ODA Task status when TodoWrite status changes.

        Args:
            task_id: ODA Task ID
            new_status: New TodoWrite status
            actor_id: ID of updating agent

        Returns:
            Updated Task or None if not found
        """
        repository = await self._get_repository()

        task = await repository.get(task_id)
        if not task:
            return None

        task.task_status = TODO_TO_TASK_STATUS[new_status]

        if new_status == TodoStatus.COMPLETED:
            task.completed_at = datetime.utcnow()

        task.touch(updated_by=actor_id)
        return await repository.update(task)

    async def load_todos_from_tasks(
        self,
        trace_id: Optional[str] = None,
        status_filter: Optional[List[TaskStatus]] = None,
    ) -> List[TodoItem]:
        """
        Load TodoWrite items from existing ODA Tasks.

        Args:
            trace_id: Filter by trace ID (plan/job correlation)
            status_filter: Filter by task statuses

        Returns:
            List of TodoItem objects
        """
        repository = await self._get_repository()

        # Build filters
        filters = {"tags": ["todowrite"]}
        if trace_id:
            filters["tags"].append(f"trace:{trace_id}")

        tasks = await repository.list(**filters)

        # Apply status filter
        if status_filter:
            tasks = [t for t in tasks if t.task_status in status_filter]

        # Convert to TodoItems
        todos = []
        for task in tasks:
            todo_status = TASK_TO_TODO_STATUS.get(
                task.task_status, TodoStatus.PENDING
            )
            todos.append(TodoItem(
                content=task.title,
                status=todo_status,
                active_form=self._generate_active_form(task.title),
                task_id=task.id,
            ))

        return todos

    async def sync_todos(
        self,
        todos: List[Dict[str, Any]],
        trace_id: Optional[str] = None,
        actor_id: str = "claude_code_agent",
    ) -> Dict[str, Any]:
        """
        Synchronize a list of TodoWrite items with ODA Tasks.

        Args:
            todos: List of todo dicts from TodoWrite
            trace_id: Correlation ID for this sync
            actor_id: Agent performing sync

        Returns:
            Sync result with created/updated/skipped counts
        """
        repository = await self._get_repository()

        result = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "tasks": [],
        }

        for todo in todos:
            content = todo.get("content", "")
            status = TodoStatus(todo.get("status", "pending"))

            # Check if task exists with same title
            existing = await repository.find_by_title(content)

            if existing:
                # Update existing task
                existing.task_status = TODO_TO_TASK_STATUS[status]
                if status == TodoStatus.COMPLETED:
                    existing.completed_at = datetime.utcnow()
                existing.touch(updated_by=actor_id)
                await repository.update(existing)
                result["updated"] += 1
                result["tasks"].append(existing.id)
            else:
                # Create new task
                task = await self.create_task_from_todo(
                    content=content,
                    status=status,
                    trace_id=trace_id,
                    actor_id=actor_id,
                )
                result["created"] += 1
                result["tasks"].append(task.id)

        return result

    def _generate_active_form(self, content: str) -> str:
        """Generate active form of todo content."""
        # Simple heuristic: add "중" suffix for Korean or "ing" for English
        if any('\uac00' <= c <= '\ud7a3' for c in content):
            return f"{content} 중"
        else:
            # Try to convert to -ing form
            words = content.split()
            if words:
                first_word = words[0].lower()
                if first_word.endswith('e'):
                    words[0] = first_word[:-1] + 'ing'
                else:
                    words[0] = first_word + 'ing'
            return ' '.join(words)

    def generate_todowrite_payload(
        self,
        tasks: List[Task],
    ) -> List[Dict[str, Any]]:
        """
        Generate TodoWrite payload from ODA Tasks.

        Args:
            tasks: List of ODA Task objects

        Returns:
            TodoWrite-compatible payload
        """
        return [
            {
                "content": task.title,
                "status": TASK_TO_TODO_STATUS.get(
                    task.task_status, TodoStatus.PENDING
                ).value,
                "activeForm": self._generate_active_form(task.title),
            }
            for task in tasks
        ]


# CLI interface for hook integration
if __name__ == "__main__":
    import sys

    async def main():
        sync = TodoTaskSync()

        if len(sys.argv) < 2:
            print("Usage: python todo_sync.py <command> [args]")
            print("Commands: create, update, load, sync")
            sys.exit(1)

        command = sys.argv[1]

        if command == "create":
            content = sys.argv[2] if len(sys.argv) > 2 else "New Task"
            task = await sync.create_task_from_todo(
                content=content,
                status=TodoStatus.PENDING,
            )
            print(json.dumps({"task_id": task.id, "title": task.title}))

        elif command == "update":
            task_id = sys.argv[2]
            status = TodoStatus(sys.argv[3])
            task = await sync.update_task_status(task_id, status)
            if task:
                print(json.dumps({"task_id": task.id, "status": task.task_status.value}))

        elif command == "load":
            trace_id = sys.argv[2] if len(sys.argv) > 2 else None
            todos = await sync.load_todos_from_tasks(trace_id=trace_id)
            print(json.dumps([
                {"content": t.content, "status": t.status.value, "task_id": t.task_id}
                for t in todos
            ]))

        elif command == "sync":
            todos_json = sys.stdin.read()
            todos = json.loads(todos_json)
            result = await sync.sync_todos(todos)
            print(json.dumps(result))

    asyncio.run(main())
