"""
Orion ODA v3.0 - Task Actions

Defines ActionTypes for Task lifecycle operations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from lib.oda.ontology.actions import (
    ActionContext,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    register_action,
)
from lib.oda.ontology.objects.task_types import Task, TaskPriority


@register_action
class CreateTaskAction(ActionType[Task]):
    """
    Create a new Task object.

    Parameters:
        title: Task title (required)
        priority: low|medium|high|critical (optional)
    """

    api_name = "task.create"
    object_type = Task
    requires_proposal = False

    submission_criteria = [
        RequiredField("title"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[Task], List[EditOperation]]:
        """Instantiate a Task and emit a CREATE EditOperation."""

        priority = params.get("priority", TaskPriority.MEDIUM)
        task = Task(
            title=str(params["title"]),
            priority=priority,
            created_by=context.actor_id,
        )

        edits = [
            EditOperation(
                edit_type=EditType.CREATE,
                object_type="Task",
                object_id=task.id,
                changes={
                    "title": task.title,
                    "priority": task.priority,
                    "created_by": task.created_by,
                    "status": task.status,
                    "version": task.version,
                },
            )
        ]

        return task, edits

