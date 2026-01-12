"""
ODA PAI Algorithm - ISC Manager
================================

Ideal State Contract (ISC) management for THE ALGORITHM.

The ISC is a structured table that defines success criteria for a task:
- Current State: Where we are now
- Ideal State: Where we need to be
- Success Criteria: Measurable conditions for completion

ObjectTypes:
    - ISCTable: Container for ISC rows (the contract)
    - ISCRow: Individual success criterion

ActionTypes:
    - CreateISCAction: Create a new ISC table
    - AddISCRowAction: Add a row to an ISC table
    - UpdateISCStatusAction: Update status of an ISC row
    - SetISCPhaseAction: Update the current phase of an ISC table

Migrated from: PAI TypeScript ISC patterns
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type
from lib.oda.ontology.actions import (
    ActionContext,
    ActionType,
    EditOperation,
    EditType,
    LogSideEffect,
    RequiredField,
    AllowedValues,
    MaxLength,
    CustomValidator,
    register_action,
)

from .effort_levels import EffortLevel


# =============================================================================
# ENUMS
# =============================================================================


class ISCRowStatus(str, Enum):
    """Status of an ISC row (success criterion)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class ISCPhase(str, Enum):
    """
    Execution phase of an ISC.

    Phases:
        DEFINITION: Initial contract creation
        ANALYSIS: Understanding current state
        PLANNING: Designing approach to reach ideal state
        EXECUTION: Implementing changes
        VERIFICATION: Validating success criteria
        COMPLETE: All criteria met
    """

    DEFINITION = "definition"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    COMPLETE = "complete"


# =============================================================================
# OBJECT TYPES
# =============================================================================


@register_object_type
class ISCRow(OntologyObject):
    """
    A single row in an Ideal State Contract.

    Each row represents a measurable success criterion that must be
    satisfied to complete the overall task.

    Attributes:
        isc_table_id: Foreign key to parent ISCTable
        criterion: Description of what needs to be achieved
        current_state: Description of the current situation
        ideal_state: Description of the desired outcome
        row_status: Current status of this criterion
        can_parallel: Whether this can be executed in parallel with others
        dependencies: List of ISCRow IDs that must complete before this
        assigned_capability: Capability assigned to execute this row
        evidence: List of evidence items proving completion
        notes: Additional notes or context
        completed_at: Timestamp when marked complete
    """

    isc_table_id: str = Field(
        ...,
        description="Foreign key to parent ISCTable"
    )
    criterion: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Description of the success criterion"
    )
    current_state: str = Field(
        default="",
        max_length=2000,
        description="Description of the current situation"
    )
    ideal_state: str = Field(
        default="",
        max_length=2000,
        description="Description of the desired outcome"
    )
    row_status: ISCRowStatus = Field(
        default=ISCRowStatus.PENDING,
        description="Current status of this criterion"
    )
    can_parallel: bool = Field(
        default=True,
        description="Whether this can be executed in parallel with others"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of ISCRow IDs that must complete before this"
    )
    assigned_capability: Optional[str] = Field(
        default=None,
        description="Capability assigned to execute this row"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence items proving completion"
    )
    notes: str = Field(
        default="",
        max_length=5000,
        description="Additional notes or context"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when marked complete"
    )

    @property
    def is_ready(self) -> bool:
        """Check if all dependencies are satisfied."""
        # Implementation would check dependency status in practice
        return self.row_status == ISCRowStatus.PENDING

    @property
    def is_complete(self) -> bool:
        """Check if this row is completed or skipped."""
        return self.row_status in (ISCRowStatus.COMPLETED, ISCRowStatus.SKIPPED)


@register_object_type
class ISCTable(OntologyObject):
    """
    An Ideal State Contract table.

    The ISC is the central planning artifact for THE ALGORITHM.
    It captures the gap between current and ideal states through
    measurable success criteria.

    Attributes:
        title: Brief title for this ISC
        description: Detailed description of the task/goal
        current_phase: Current execution phase
        effort_level: Assigned effort level for this ISC
        row_ids: List of ISCRow IDs belonging to this table
        total_rows: Total number of rows (denormalized for efficiency)
        completed_rows: Number of completed rows
        blocked_rows: Number of blocked rows
        task_id: Optional link to a Task object
        parent_isc_id: Optional parent ISC for hierarchical decomposition
        metadata: Additional structured metadata
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Brief title for this ISC"
    )
    description: str = Field(
        default="",
        max_length=5000,
        description="Detailed description of the task/goal"
    )
    current_phase: ISCPhase = Field(
        default=ISCPhase.DEFINITION,
        description="Current execution phase"
    )
    effort_level: EffortLevel = Field(
        default=EffortLevel.STANDARD,
        description="Assigned effort level for this ISC"
    )
    row_ids: List[str] = Field(
        default_factory=list,
        description="List of ISCRow IDs belonging to this table"
    )
    total_rows: int = Field(
        default=0,
        ge=0,
        description="Total number of rows"
    )
    completed_rows: int = Field(
        default=0,
        ge=0,
        description="Number of completed rows"
    )
    blocked_rows: int = Field(
        default=0,
        ge=0,
        description="Number of blocked rows"
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Optional link to a Task object"
    )
    parent_isc_id: Optional[str] = Field(
        default=None,
        description="Optional parent ISC for hierarchical decomposition"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured metadata"
    )

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.completed_rows / self.total_rows) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if all rows are complete."""
        return self.total_rows > 0 and self.completed_rows >= self.total_rows

    @property
    def is_blocked(self) -> bool:
        """Check if any rows are blocked."""
        return self.blocked_rows > 0

    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary dict for display."""
        return {
            "id": self.id,
            "title": self.title,
            "phase": self.current_phase.value,
            "effort": self.effort_level.value,
            "progress": f"{self.completed_rows}/{self.total_rows}",
            "completion": f"{self.completion_percentage:.1f}%",
            "blocked": self.blocked_rows > 0,
        }


# =============================================================================
# ACTION TYPES
# =============================================================================


@register_action
class CreateISCAction(ActionType[ISCTable]):
    """
    Create a new Ideal State Contract table.

    Required params:
        - title: str (1-255 chars)

    Optional params:
        - description: str (max 5000 chars)
        - effort_level: EffortLevel string
        - task_id: str (link to Task)
        - parent_isc_id: str (parent ISC for decomposition)
        - metadata: Dict[str, Any]
    """

    api_name: ClassVar[str] = "pai.create_isc"
    object_type: ClassVar[Type[ISCTable]] = ISCTable
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("title"),
        MaxLength("title", 255),
        MaxLength("description", 5000),
        AllowedValues("effort_level", [e.value for e in EffortLevel]),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[ISCTable, List[EditOperation]]:
        """Create a new ISCTable."""
        # Parse effort level
        effort = params.get("effort_level", EffortLevel.STANDARD.value)
        if isinstance(effort, str):
            effort = EffortLevel.from_string(effort)

        isc = ISCTable(
            title=params["title"],
            description=params.get("description", ""),
            effort_level=effort,
            task_id=params.get("task_id"),
            parent_isc_id=params.get("parent_isc_id"),
            metadata=params.get("metadata", {}),
            created_by=context.actor_id,
        )

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="ISCTable",
            object_id=isc.id,
            changes=params,
        )

        return isc, [edit]


@register_action
class AddISCRowAction(ActionType[ISCRow]):
    """
    Add a row to an existing ISC table.

    Required params:
        - isc_table_id: str (existing ISCTable ID)
        - criterion: str (success criterion description)

    Optional params:
        - current_state: str
        - ideal_state: str
        - can_parallel: bool (default True)
        - dependencies: List[str] (ISCRow IDs)
        - assigned_capability: str
        - notes: str
    """

    api_name: ClassVar[str] = "pai.add_isc_row"
    object_type: ClassVar[Type[ISCRow]] = ISCRow
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("isc_table_id"),
        RequiredField("criterion"),
        MaxLength("criterion", 500),
        MaxLength("current_state", 2000),
        MaxLength("ideal_state", 2000),
        MaxLength("notes", 5000),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[ISCRow, List[EditOperation]]:
        """Create a new ISCRow and link to ISCTable."""
        row = ISCRow(
            isc_table_id=params["isc_table_id"],
            criterion=params["criterion"],
            current_state=params.get("current_state", ""),
            ideal_state=params.get("ideal_state", ""),
            can_parallel=params.get("can_parallel", True),
            dependencies=params.get("dependencies", []),
            assigned_capability=params.get("assigned_capability"),
            notes=params.get("notes", ""),
            created_by=context.actor_id,
        )

        edits = [
            # Create the row
            EditOperation(
                edit_type=EditType.CREATE,
                object_type="ISCRow",
                object_id=row.id,
                changes=params,
            ),
            # Link to parent table (update row_ids and total_rows)
            EditOperation(
                edit_type=EditType.LINK,
                object_type="ISCTable",
                object_id=params["isc_table_id"],
                changes={
                    "add_row_id": row.id,
                    "increment_total_rows": 1,
                },
            ),
        ]

        return row, edits


@register_action
class UpdateISCStatusAction(ActionType[ISCRow]):
    """
    Update the status of an ISC row.

    Required params:
        - row_id: str (existing ISCRow ID)
        - row_status: ISCRowStatus string

    Optional params:
        - evidence: List[str] (evidence items for completion)
        - notes: str (additional notes)
    """

    api_name: ClassVar[str] = "pai.update_isc_status"
    object_type: ClassVar[Type[ISCRow]] = ISCRow
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("row_id"),
        RequiredField("row_status"),
        AllowedValues("row_status", [s.value for s in ISCRowStatus]),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Update ISCRow status."""
        changes: Dict[str, Any] = {
            "row_status": params["row_status"],
            "updated_by": context.actor_id,
        }

        # Add completion timestamp if marking complete
        if params["row_status"] in (ISCRowStatus.COMPLETED.value, "completed"):
            changes["completed_at"] = utc_now().isoformat()

        # Add evidence if provided
        if "evidence" in params:
            changes["evidence"] = params["evidence"]

        # Add notes if provided
        if "notes" in params:
            changes["notes"] = params["notes"]

        edits = [
            EditOperation(
                edit_type=EditType.MODIFY,
                object_type="ISCRow",
                object_id=params["row_id"],
                changes=changes,
            ),
        ]

        # If completing, we should also update parent ISCTable
        # This would typically be done via a separate action or event
        if params["row_status"] in (ISCRowStatus.COMPLETED.value, "completed"):
            edits.append(
                EditOperation(
                    edit_type=EditType.MODIFY,
                    object_type="ISCTable",
                    object_id="<parent_lookup>",  # Would be resolved at execution
                    changes={"increment_completed_rows": 1},
                )
            )

        return None, edits


@register_action
class SetISCPhaseAction(ActionType[ISCTable]):
    """
    Update the current phase of an ISC table.

    Required params:
        - isc_table_id: str (existing ISCTable ID)
        - phase: ISCPhase string

    Optional params:
        - notes: str (phase transition notes)
    """

    api_name: ClassVar[str] = "pai.set_isc_phase"
    object_type: ClassVar[Type[ISCTable]] = ISCTable
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("isc_table_id"),
        RequiredField("phase"),
        AllowedValues("phase", [p.value for p in ISCPhase]),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Update ISCTable phase."""
        changes: Dict[str, Any] = {
            "current_phase": params["phase"],
            "updated_by": context.actor_id,
        }

        # Add notes to metadata if provided
        if "notes" in params:
            changes["metadata"] = {
                f"phase_{params['phase']}_notes": params["notes"],
                f"phase_{params['phase']}_at": utc_now().isoformat(),
            }

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="ISCTable",
            object_id=params["isc_table_id"],
            changes=changes,
        )

        return None, [edit]
