"""
Ontology Proposal Workflow for Governance.

Provides proposal workflow management for ontology schema changes with
review and approval process.

This module provides:
    - ProposalStatus: Workflow states (DRAFT, REVIEW, APPROVED, MERGED)
    - ProposalTask: Individual review task for a resource
    - OntologyProposal: Complete proposal definition

Reference: docs/Ontology.md Section 11 - Versioning & Governance
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProposalStatus(str, Enum):
    """
    Proposal workflow status.

    Workflow progression:
    DRAFT → IN_REVIEW → APPROVED → MERGED

    - DRAFT: Proposal created, changes in progress
    - IN_REVIEW: Submitted for review, reviewers assigned
    - APPROVED: All tasks approved, ready to merge
    - MERGED: Integrated into main ontology
    - REJECTED: Proposal rejected, changes discarded
    - REBASING: Incorporating changes from main branch
    """

    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    MERGED = "MERGED"
    REJECTED = "REJECTED"
    REBASING = "REBASING"

    @property
    def is_terminal(self) -> bool:
        """Return True if this is a terminal status (workflow complete)."""
        return self in {ProposalStatus.MERGED, ProposalStatus.REJECTED}

    @property
    def allows_edits(self) -> bool:
        """Return True if proposal can still be edited."""
        return self in {ProposalStatus.DRAFT, ProposalStatus.REBASING}


class TaskStatus(str, Enum):
    """
    Individual task status within a proposal.

    - PENDING: Awaiting review
    - APPROVED: Task approved by reviewer
    - REJECTED: Task rejected, requires changes
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ProposalTask(BaseModel):
    """
    Individual review task for a resource in a proposal.

    Each resource change (ObjectType, LinkType, etc.) gets its own task:
    - task_id: Unique task identifier
    - resource_type: Type of resource (ObjectType, LinkType, etc.)
    - resource_name: apiName of the resource
    - status: PENDING, APPROVED, or REJECTED
    - assigned_reviewer: User assigned to review
    - review_comments: Reviewer feedback

    Example:
        ProposalTask(
            task_id="task-001",
            resource_type="ObjectType",
            resource_name="Employee",
            status=TaskStatus.PENDING,
            assigned_reviewer="alice@company.com"
        )
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier.",
        alias="taskId",
    )

    resource_type: str = Field(
        ...,
        description="Type of resource: ObjectType, LinkType, ActionType, etc.",
        alias="resourceType",
    )

    resource_name: str = Field(
        ...,
        description="apiName of the resource being changed.",
        alias="resourceName",
    )

    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current status of this task.",
    )

    assigned_reviewer: Optional[str] = Field(
        default=None,
        description="User assigned to review this task.",
        alias="assignedReviewer",
    )

    review_comments: Optional[str] = Field(
        default=None,
        description="Reviewer feedback and comments.",
        alias="reviewComments",
    )

    approved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when task was approved.",
        alias="approvedAt",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "taskId": self.task_id,
            "resourceType": self.resource_type,
            "resourceName": self.resource_name,
            "status": self.status.value,
        }

        if self.assigned_reviewer:
            result["assignedReviewer"] = self.assigned_reviewer

        if self.review_comments:
            result["reviewComments"] = self.review_comments

        if self.approved_at:
            result["approvedAt"] = self.approved_at.isoformat()

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "ProposalTask":
        """Create from Foundry JSON format."""
        approved_at = None
        if data.get("approvedAt"):
            approved_at = datetime.fromisoformat(data["approvedAt"].replace("Z", "+00:00"))

        return cls(
            task_id=data["taskId"],
            resource_type=data["resourceType"],
            resource_name=data["resourceName"],
            status=TaskStatus(data.get("status", "PENDING")),
            assigned_reviewer=data.get("assignedReviewer"),
            review_comments=data.get("reviewComments"),
            approved_at=approved_at,
        )


class OntologyProposal(BaseModel):
    """
    Complete ontology proposal definition.

    Represents a proposal for ontology schema changes with review workflow:
    - proposal_id: Unique proposal identifier
    - branch_name: Ontology branch for this proposal
    - title: Human-readable title
    - description: Detailed description of changes
    - status: Current workflow status
    - tasks: List of review tasks (one per resource)
    - created_by: Proposal creator
    - created_at: Creation timestamp
    - merged_at: Merge timestamp (if merged)

    Workflow stages:
    1. Branch creation: Derived from main version, isolated experimentation
    2. Proposal: Contains reviews and metadata, each resource = separate task
    3. Rebase: Manual incorporation of main changes, conflict resolution
    4. Review: Reviewer assignment, individual task approval
    5. Merge: Integration into main ontology

    Example:
        OntologyProposal(
            proposal_id="prop-2024-001",
            branch_name="feature/employee-v2",
            title="Update Employee schema",
            description="Add new fields for HR integration",
            status=ProposalStatus.DRAFT,
            tasks=[
                ProposalTask(...),
                ProposalTask(...),
            ],
            created_by="alice@company.com"
        )
    """

    proposal_id: str = Field(
        ...,
        description="Unique proposal identifier.",
        alias="proposalId",
    )

    branch_name: str = Field(
        ...,
        description="Ontology branch name for this proposal.",
        alias="branchName",
    )

    title: str = Field(
        ...,
        description="Human-readable title for this proposal.",
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        ...,
        description="Detailed description of the proposed changes.",
    )

    status: ProposalStatus = Field(
        default=ProposalStatus.DRAFT,
        description="Current workflow status.",
    )

    tasks: list[ProposalTask] = Field(
        default_factory=list,
        description="List of review tasks (one per resource).",
    )

    created_by: str = Field(
        ...,
        description="User who created this proposal.",
        alias="createdBy",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Proposal creation timestamp.",
        alias="createdAt",
    )

    submitted_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when submitted for review.",
        alias="submittedAt",
    )

    approved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when all tasks were approved.",
        alias="approvedAt",
    )

    merged_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when merged into main.",
        alias="mergedAt",
    )

    merged_by: Optional[str] = Field(
        default=None,
        description="User who merged this proposal.",
        alias="mergedBy",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def can_submit(self) -> bool:
        """Check if proposal can be submitted for review."""
        return self.status == ProposalStatus.DRAFT and len(self.tasks) > 0

    def can_approve(self) -> bool:
        """Check if proposal can be approved (all tasks approved)."""
        if self.status != ProposalStatus.IN_REVIEW:
            return False

        return all(task.status == TaskStatus.APPROVED for task in self.tasks)

    def can_merge(self) -> bool:
        """Check if proposal can be merged."""
        return self.status == ProposalStatus.APPROVED

    def get_pending_tasks(self) -> list[ProposalTask]:
        """Get all tasks still pending review."""
        return [task for task in self.tasks if task.status == TaskStatus.PENDING]

    def get_approval_progress(self) -> tuple[int, int]:
        """
        Get approval progress.

        Returns:
            (approved_count, total_count) tuple
        """
        approved = sum(1 for task in self.tasks if task.status == TaskStatus.APPROVED)
        total = len(self.tasks)
        return (approved, total)

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "proposalId": self.proposal_id,
            "branchName": self.branch_name,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "tasks": [task.to_foundry_dict() for task in self.tasks],
            "createdBy": self.created_by,
            "createdAt": self.created_at.isoformat(),
        }

        if self.submitted_at:
            result["submittedAt"] = self.submitted_at.isoformat()

        if self.approved_at:
            result["approvedAt"] = self.approved_at.isoformat()

        if self.merged_at:
            result["mergedAt"] = self.merged_at.isoformat()

        if self.merged_by:
            result["mergedBy"] = self.merged_by

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "OntologyProposal":
        """Create from Foundry JSON format."""
        created_at = datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))

        submitted_at = None
        if data.get("submittedAt"):
            submitted_at = datetime.fromisoformat(
                data["submittedAt"].replace("Z", "+00:00")
            )

        approved_at = None
        if data.get("approvedAt"):
            approved_at = datetime.fromisoformat(
                data["approvedAt"].replace("Z", "+00:00")
            )

        merged_at = None
        if data.get("mergedAt"):
            merged_at = datetime.fromisoformat(data["mergedAt"].replace("Z", "+00:00"))

        tasks = [ProposalTask.from_foundry_dict(t) for t in data.get("tasks", [])]

        return cls(
            proposal_id=data["proposalId"],
            branch_name=data["branchName"],
            title=data["title"],
            description=data["description"],
            status=ProposalStatus(data.get("status", "DRAFT")),
            tasks=tasks,
            created_by=data["createdBy"],
            created_at=created_at,
            submitted_at=submitted_at,
            approved_at=approved_at,
            merged_at=merged_at,
            merged_by=data.get("mergedBy"),
        )
