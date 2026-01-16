"""
ODA v3.0 - Proposal Manager for LLM-Agnostic Orchestration
==========================================================

Converts subagent file change outputs to ODA Proposals for governance.
Provides the bridge between execution subagents and the ODA governance layer.

Key Features:
- Standardized SubagentOutput schema for file operations
- File-level proposal creation (one proposal per file)
- Batch approval with human-readable summaries
- Multiple approval modes (interactive, batch, auto)

Usage:
    ```python
    from lib.oda.claude.proposal_manager import ProposalManager, SubagentOutput

    # Parse subagent output
    output = SubagentOutput(
        files_to_modify=[
            FileModification(
                file_path="/path/to/file.py",
                old_content="...",
                new_content="...",
                reason="Fix bug in authentication"
            )
        ],
        stage_a_evidence={"files_viewed": ["auth.py", "config.py"]}
    )

    # Create proposals
    manager = ProposalManager()
    proposal_ids = await manager.create_proposals_from_output(output, context)

    # Approve and execute
    results = await manager.approve_and_execute_proposals(proposal_ids)
    ```
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from lib.oda.ontology.actions import ActionContext, ActionResult, action_registry
from lib.oda.ontology.objects.proposal import (
    Proposal,
    ProposalPriority,
    ProposalStatus,
)
from lib.oda.ontology.storage.database import initialize_database
from lib.oda.ontology.storage.proposal_repository import (
    ProposalRepository,
    ProposalNotFoundError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SUBAGENT OUTPUT SCHEMAS
# =============================================================================


class FileModification(BaseModel):
    """Schema for a file modification operation."""

    file_path: str = Field(
        ...,
        description="Absolute path to the file to modify"
    )
    old_content: Optional[str] = Field(
        default=None,
        description="Expected current content (for verification)"
    )
    new_content: str = Field(
        ...,
        description="New content to write to the file"
    )
    reason: str = Field(
        ...,
        description="Human-readable reason for the modification"
    )

    @field_validator("file_path")
    @classmethod
    def validate_absolute_path(cls, v: str) -> str:
        """Ensure file path is absolute."""
        if not v.startswith("/"):
            raise ValueError(f"file_path must be absolute, got: {v}")
        return v


class FileCreation(BaseModel):
    """Schema for a file creation operation."""

    file_path: str = Field(
        ...,
        description="Absolute path for the new file"
    )
    content: str = Field(
        ...,
        description="Content to write to the new file"
    )
    reason: str = Field(
        ...,
        description="Human-readable reason for creating the file"
    )

    @field_validator("file_path")
    @classmethod
    def validate_absolute_path(cls, v: str) -> str:
        """Ensure file path is absolute."""
        if not v.startswith("/"):
            raise ValueError(f"file_path must be absolute, got: {v}")
        return v


class FileDeletion(BaseModel):
    """Schema for a file deletion operation."""

    file_path: str = Field(
        ...,
        description="Absolute path to the file to delete"
    )
    reason: str = Field(
        ...,
        description="Human-readable reason for deletion"
    )

    @field_validator("file_path")
    @classmethod
    def validate_absolute_path(cls, v: str) -> str:
        """Ensure file path is absolute."""
        if not v.startswith("/"):
            raise ValueError(f"file_path must be absolute, got: {v}")
        return v


class SubagentOutput(BaseModel):
    """
    Standard output format from execution subagents.

    Contains:
    - Stage evidence from 3-Stage Protocol
    - File operations to perform
    - Verification commands for Stage C
    """

    # Stage Evidence (optional, for audit trail)
    stage_a_evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Stage A (SCAN) evidence: files_viewed, requirements, complexity"
    )
    stage_b_evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Stage B (TRACE) evidence: imports_verified, signatures_matched"
    )

    # File Operations
    files_to_modify: List[FileModification] = Field(
        default_factory=list,
        description="List of file modifications to perform"
    )
    files_to_create: List[FileCreation] = Field(
        default_factory=list,
        description="List of new files to create"
    )
    files_to_delete: List[str] = Field(
        default_factory=list,
        description="List of file paths to delete"
    )

    # Verification Commands (for Stage C)
    verification_commands: List[str] = Field(
        default_factory=list,
        description="Commands to run for verification (tests, lint, typecheck)"
    )

    @property
    def has_changes(self) -> bool:
        """Check if there are any file operations."""
        return bool(
            self.files_to_modify or
            self.files_to_create or
            self.files_to_delete
        )

    @property
    def total_operations(self) -> int:
        """Total number of file operations."""
        return (
            len(self.files_to_modify) +
            len(self.files_to_create) +
            len(self.files_to_delete)
        )


# =============================================================================
# APPROVAL MODES
# =============================================================================


class ApprovalMode(str, Enum):
    """Modes for proposal approval."""

    INTERACTIVE = "interactive"  # Ask user for each proposal
    BATCH = "batch"              # Present summary, approve all at once
    AUTO = "auto"                # Auto-approve with audit logging


# =============================================================================
# PROPOSAL MANAGER
# =============================================================================


class ProposalManager:
    """
    Convert subagent outputs to ODA Proposals for governance.

    Provides the orchestration interface between execution subagents
    and the ODA governance layer. Each file operation becomes a
    separate proposal for fine-grained approval control.
    """

    def __init__(
        self,
        default_actor_id: str = "main-agent",
        default_priority: ProposalPriority = ProposalPriority.MEDIUM,
    ):
        """
        Initialize the ProposalManager.

        Args:
            default_actor_id: Default actor ID for proposal creation
            default_priority: Default priority for proposals
        """
        self.default_actor_id = default_actor_id
        self.default_priority = default_priority
        self._repo: Optional[ProposalRepository] = None

    async def _get_repo(self) -> ProposalRepository:
        """Get or create the repository instance."""
        if self._repo is None:
            db = await initialize_database()
            self._repo = ProposalRepository(db)
        return self._repo

    # =========================================================================
    # PROPOSAL CREATION
    # =========================================================================

    async def create_proposals_from_output(
        self,
        output: SubagentOutput,
        context: ActionContext,
        priority: Optional[ProposalPriority] = None,
        auto_submit: bool = True,
    ) -> List[str]:
        """
        Create file-level Proposals from subagent output.

        Each file operation (modify, create, delete) becomes a separate
        proposal. This allows fine-grained approval and rollback.

        Args:
            output: The SubagentOutput containing file operations
            context: ActionContext with actor information
            priority: Optional priority override
            auto_submit: If True, automatically submit proposals for review

        Returns:
            List of created proposal IDs
        """
        if not output.has_changes:
            logger.info("No file changes in subagent output")
            return []

        repo = await self._get_repo()
        proposal_ids: List[str] = []
        effective_priority = priority or self.default_priority

        # Build combined stage evidence
        stage_evidence = self._build_stage_evidence(output)

        # Create proposals for modifications
        for file_mod in output.files_to_modify:
            proposal = await self._create_modify_proposal(
                file_mod=file_mod,
                stage_evidence=stage_evidence,
                context=context,
                priority=effective_priority,
            )
            if auto_submit:
                proposal.submit(submitter_id=context.actor_id)
            await repo.save(proposal, actor_id=context.actor_id)
            proposal_ids.append(proposal.id)
            logger.debug(f"Created modify proposal: {proposal.id} for {file_mod.file_path}")

        # Create proposals for new files
        for file_create in output.files_to_create:
            proposal = await self._create_write_proposal(
                file_create=file_create,
                stage_evidence=stage_evidence,
                context=context,
                priority=effective_priority,
            )
            if auto_submit:
                proposal.submit(submitter_id=context.actor_id)
            await repo.save(proposal, actor_id=context.actor_id)
            proposal_ids.append(proposal.id)
            logger.debug(f"Created write proposal: {proposal.id} for {file_create.file_path}")

        # Create proposals for deletions
        for file_path in output.files_to_delete:
            proposal = await self._create_delete_proposal(
                file_path=file_path,
                reason="Subagent requested deletion",
                stage_evidence=stage_evidence,
                context=context,
                priority=effective_priority,
            )
            if auto_submit:
                proposal.submit(submitter_id=context.actor_id)
            await repo.save(proposal, actor_id=context.actor_id)
            proposal_ids.append(proposal.id)
            logger.debug(f"Created delete proposal: {proposal.id} for {file_path}")

        logger.info(f"Created {len(proposal_ids)} proposals from subagent output")
        return proposal_ids

    async def _create_modify_proposal(
        self,
        file_mod: FileModification,
        stage_evidence: Dict[str, Any],
        context: ActionContext,
        priority: ProposalPriority,
    ) -> Proposal:
        """Create a proposal for file modification."""
        return Proposal(
            action_type="file.modify",
            payload={
                "file_path": file_mod.file_path,
                "old_content": file_mod.old_content,
                "new_content": file_mod.new_content,
                "reason": file_mod.reason,
                "stage_evidence": stage_evidence,
            },
            priority=priority,
            created_by=context.actor_id,
        )

    async def _create_write_proposal(
        self,
        file_create: FileCreation,
        stage_evidence: Dict[str, Any],
        context: ActionContext,
        priority: ProposalPriority,
    ) -> Proposal:
        """Create a proposal for file creation."""
        return Proposal(
            action_type="file.write",
            payload={
                "file_path": file_create.file_path,
                "content": file_create.content,
                "reason": file_create.reason,
                "stage_evidence": stage_evidence,
            },
            priority=priority,
            created_by=context.actor_id,
        )

    async def _create_delete_proposal(
        self,
        file_path: str,
        reason: str,
        stage_evidence: Dict[str, Any],
        context: ActionContext,
        priority: ProposalPriority,
    ) -> Proposal:
        """Create a proposal for file deletion."""
        return Proposal(
            action_type="file.delete",
            payload={
                "file_path": file_path,
                "reason": reason,
                "stage_evidence": stage_evidence,
            },
            priority=priority,
            created_by=context.actor_id,
        )

    def _build_stage_evidence(self, output: SubagentOutput) -> Dict[str, Any]:
        """Build combined stage evidence from output."""
        evidence = {}
        if output.stage_a_evidence:
            evidence["stage_a"] = output.stage_a_evidence
        if output.stage_b_evidence:
            evidence["stage_b"] = output.stage_b_evidence
        if output.verification_commands:
            evidence["verification_commands"] = output.verification_commands
        return evidence

    # =========================================================================
    # APPROVAL & EXECUTION
    # =========================================================================

    async def approve_and_execute_proposals(
        self,
        proposal_ids: List[str],
        approver_id: str = "main-agent",
        executor_id: Optional[str] = None,
        approval_comment: Optional[str] = None,
    ) -> Dict[str, ActionResult]:
        """
        Approve and execute all proposals.

        Args:
            proposal_ids: List of proposal IDs to approve and execute
            approver_id: ID of the approver
            executor_id: ID of the executor (defaults to approver_id)
            approval_comment: Optional comment for approval

        Returns:
            Mapping of proposal_id -> execution result
        """
        repo = await self._get_repo()
        executor = executor_id or approver_id
        results: Dict[str, ActionResult] = {}

        for proposal_id in proposal_ids:
            try:
                # Approve the proposal
                proposal = await repo.approve(
                    proposal_id,
                    reviewer_id=approver_id,
                    comment=approval_comment,
                )

                # Execute the underlying action
                action_cls = action_registry.get(proposal.action_type)
                if action_cls is None:
                    results[proposal_id] = ActionResult(
                        action_type=proposal.action_type,
                        success=False,
                        error=f"Action '{proposal.action_type}' not found in registry",
                    )
                    continue

                action = action_cls()
                context = ActionContext(actor_id=executor)

                # Validate before execution
                validation_errors = action.validate(proposal.payload, context)
                if validation_errors:
                    results[proposal_id] = ActionResult(
                        action_type=proposal.action_type,
                        success=False,
                        error="Validation failed",
                        error_details={"validation_errors": validation_errors},
                    )
                    continue

                # Execute the action
                action_result = await action.execute(proposal.payload, context)

                # Mark proposal as executed
                await repo.execute(
                    proposal_id,
                    executor_id=executor,
                    result=action_result.to_dict(),
                )

                results[proposal_id] = action_result
                logger.debug(f"Executed proposal {proposal_id}: success={action_result.success}")

            except ProposalNotFoundError:
                results[proposal_id] = ActionResult(
                    action_type="unknown",
                    success=False,
                    error=f"Proposal '{proposal_id}' not found",
                )
            except Exception as e:
                logger.exception(f"Failed to execute proposal {proposal_id}")
                results[proposal_id] = ActionResult(
                    action_type="unknown",
                    success=False,
                    error=str(e),
                    error_details={"exception_type": type(e).__name__},
                )

        return results

    async def approve_proposals(
        self,
        proposal_ids: List[str],
        approver_id: str = "main-agent",
        comment: Optional[str] = None,
    ) -> List[Tuple[str, bool, Optional[str]]]:
        """
        Approve proposals without executing them.

        Args:
            proposal_ids: List of proposal IDs to approve
            approver_id: ID of the approver
            comment: Optional approval comment

        Returns:
            List of (proposal_id, success, error_message) tuples
        """
        repo = await self._get_repo()
        results: List[Tuple[str, bool, Optional[str]]] = []

        for proposal_id in proposal_ids:
            try:
                await repo.approve(proposal_id, reviewer_id=approver_id, comment=comment)
                results.append((proposal_id, True, None))
            except ProposalNotFoundError:
                results.append((proposal_id, False, "Proposal not found"))
            except Exception as e:
                results.append((proposal_id, False, str(e)))

        return results

    async def execute_approved_proposals(
        self,
        proposal_ids: List[str],
        executor_id: str = "main-agent",
    ) -> Dict[str, ActionResult]:
        """
        Execute already-approved proposals.

        Args:
            proposal_ids: List of approved proposal IDs to execute
            executor_id: ID of the executor

        Returns:
            Mapping of proposal_id -> execution result
        """
        repo = await self._get_repo()
        results: Dict[str, ActionResult] = {}

        for proposal_id in proposal_ids:
            try:
                proposal = await repo.find_by_id(proposal_id)
                if proposal is None:
                    results[proposal_id] = ActionResult(
                        action_type="unknown",
                        success=False,
                        error=f"Proposal '{proposal_id}' not found",
                    )
                    continue

                if proposal.status != ProposalStatus.APPROVED:
                    results[proposal_id] = ActionResult(
                        action_type=proposal.action_type,
                        success=False,
                        error=f"Proposal is not approved (status: {proposal.status.value})",
                    )
                    continue

                # Execute the action
                action_cls = action_registry.get(proposal.action_type)
                if action_cls is None:
                    results[proposal_id] = ActionResult(
                        action_type=proposal.action_type,
                        success=False,
                        error=f"Action '{proposal.action_type}' not found",
                    )
                    continue

                action = action_cls()
                context = ActionContext(actor_id=executor_id)
                action_result = await action.execute(proposal.payload, context)

                # Mark as executed
                await repo.execute(
                    proposal_id,
                    executor_id=executor_id,
                    result=action_result.to_dict(),
                )

                results[proposal_id] = action_result

            except Exception as e:
                logger.exception(f"Failed to execute proposal {proposal_id}")
                results[proposal_id] = ActionResult(
                    action_type="unknown",
                    success=False,
                    error=str(e),
                )

        return results

    # =========================================================================
    # BATCH SUMMARY
    # =========================================================================

    async def batch_approval_summary(
        self,
        proposal_ids: List[str],
    ) -> str:
        """
        Generate human-readable summary for batch approval.

        Args:
            proposal_ids: List of proposal IDs to summarize

        Returns:
            Formatted summary string
        """
        repo = await self._get_repo()

        lines = [
            "=" * 60,
            "PROPOSAL BATCH SUMMARY",
            "=" * 60,
            f"Total proposals: {len(proposal_ids)}",
            "",
        ]

        # Group by action type
        by_action: Dict[str, List[Proposal]] = {}
        missing_ids: List[str] = []

        for proposal_id in proposal_ids:
            proposal = await repo.find_by_id(proposal_id)
            if proposal is None:
                missing_ids.append(proposal_id)
                continue

            action_type = proposal.action_type
            if action_type not in by_action:
                by_action[action_type] = []
            by_action[action_type].append(proposal)

        # Format by action type
        for action_type, proposals in sorted(by_action.items()):
            lines.append(f"## {action_type.upper()} ({len(proposals)} operations)")
            lines.append("-" * 40)

            for p in proposals:
                file_path = p.payload.get("file_path", "unknown")
                reason = p.payload.get("reason", "No reason provided")
                status_indicator = "[ ]" if p.status == ProposalStatus.PENDING else f"[{p.status.value[0].upper()}]"

                lines.append(f"  {status_indicator} {file_path}")
                lines.append(f"      Reason: {reason[:60]}{'...' if len(reason) > 60 else ''}")
                lines.append(f"      ID: {p.id}")
                lines.append("")

        if missing_ids:
            lines.append("")
            lines.append("WARNING: Missing proposals")
            for pid in missing_ids:
                lines.append(f"  - {pid}")

        lines.append("=" * 60)
        lines.append("")
        lines.append("Commands:")
        lines.append("  approve_all: Approve and execute all proposals")
        lines.append("  reject_all: Reject all proposals")
        lines.append("  review: Review each proposal individually")

        return "\n".join(lines)

    async def get_proposal_details(
        self,
        proposal_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a proposal.

        Args:
            proposal_id: The proposal ID

        Returns:
            Proposal details as dictionary, or None if not found
        """
        repo = await self._get_repo()
        proposal, history = await repo.get_with_history(proposal_id)

        if proposal is None:
            return None

        return {
            "id": proposal.id,
            "action_type": proposal.action_type,
            "payload": proposal.payload,
            "status": proposal.status.value,
            "priority": proposal.priority.value,
            "created_by": proposal.created_by,
            "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
            "reviewed_by": proposal.reviewed_by,
            "reviewed_at": proposal.reviewed_at.isoformat() if proposal.reviewed_at else None,
            "review_comment": proposal.review_comment,
            "executed_at": proposal.executed_at.isoformat() if proposal.executed_at else None,
            "execution_result": proposal.execution_result,
            "version": proposal.version,
            "history": [
                {
                    "action": h.action,
                    "actor_id": h.actor_id,
                    "timestamp": h.timestamp.isoformat(),
                    "previous_status": h.previous_status,
                    "new_status": h.new_status,
                    "comment": h.comment,
                }
                for h in history
            ],
        }

    # =========================================================================
    # REJECTION
    # =========================================================================

    async def reject_proposals(
        self,
        proposal_ids: List[str],
        reviewer_id: str = "main-agent",
        reason: str = "Rejected by orchestrator",
    ) -> List[Tuple[str, bool, Optional[str]]]:
        """
        Reject proposals.

        Args:
            proposal_ids: List of proposal IDs to reject
            reviewer_id: ID of the reviewer
            reason: Rejection reason

        Returns:
            List of (proposal_id, success, error_message) tuples
        """
        repo = await self._get_repo()
        results: List[Tuple[str, bool, Optional[str]]] = []

        for proposal_id in proposal_ids:
            try:
                await repo.reject(proposal_id, reviewer_id=reviewer_id, reason=reason)
                results.append((proposal_id, True, None))
            except ProposalNotFoundError:
                results.append((proposal_id, False, "Proposal not found"))
            except Exception as e:
                results.append((proposal_id, False, str(e)))

        return results


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Main class
    "ProposalManager",
    # Schemas
    "SubagentOutput",
    "FileModification",
    "FileCreation",
    "FileDeletion",
    # Enums
    "ApprovalMode",
]
