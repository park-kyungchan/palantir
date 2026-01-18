"""
Orion ODA v3.0 - Orchestration Action Types
LLM-Agnostic Architecture - Phase 3

This module implements orchestration ActionTypes for the Main Agent layer.
These actions manage the lifecycle of subagent outputs and file proposals.

ActionTypes:
- orchestration.process_subagent_output: Convert subagent output to proposals
- orchestration.execute_batch: Execute approved proposals in batch
- orchestration.rollback: Rollback executed proposals (hazardous)
- orchestration.status: Get current orchestration status
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    AllowedValues,
    ArraySizeValidator,
    CustomValidator,
    EditOperation,
    EditType,
    RequiredField,
    action_registry,
    register_action,
)
from lib.oda.ontology.objects.proposal import (
    Proposal,
    ProposalPriority,
    ProposalStatus,
)
from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.proposal_repository import (
    PaginatedResult,
    ProposalQuery,
    ProposalRepository,
)
from lib.oda.ontology.evidence.quality_checks import StageCEvidence

logger = logging.getLogger(__name__)


# =============================================================================
# RESULT MODELS
# =============================================================================


class OrchestrationResult(OntologyObject):
    """
    Result object for orchestration operations.
    Tracks proposals created, executed, or rolled back.
    """
    operation: str = Field(..., description="Operation type: process|execute|rollback|status")
    proposal_ids: List[str] = Field(default_factory=list, description="Affected proposal IDs")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Operation summary")
    stage_c_evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Stage C verification evidence if applicable"
    )
    success_count: int = Field(default=0, description="Number of successful operations")
    failure_count: int = Field(default=0, description="Number of failed operations")
    error_details: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Details of failures if any"
    )


class FileProposal(BaseModel):
    """
    Represents a single file-level proposal extracted from subagent output.
    Used as intermediate structure before creating Proposal objects.
    """
    file_path: str = Field(..., description="Path to the file to modify")
    operation: str = Field(..., description="Operation: write|modify|delete")
    content: Optional[str] = Field(default=None, description="New content for write/modify")
    old_content: Optional[str] = Field(default=None, description="Expected current content")
    reason: str = Field(..., description="Reason for the change")


# =============================================================================
# VALIDATORS
# =============================================================================


def validate_agent_id(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate agent_id is a non-empty string."""
    agent_id = params.get("agent_id")
    if not agent_id or not isinstance(agent_id, str):
        return False
    return len(agent_id.strip()) > 0


def validate_output_source(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that either output_file or output_data is provided."""
    output_file = params.get("output_file")
    output_data = params.get("output_data")

    if not output_file and not output_data:
        return False
    return True


def validate_proposal_ids_not_empty(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate proposal_ids list is not empty."""
    proposal_ids = params.get("proposal_ids", [])
    return isinstance(proposal_ids, list) and len(proposal_ids) > 0


def validate_rollback_reason(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate reason is provided for rollback."""
    reason = params.get("reason")
    return isinstance(reason, str) and len(reason.strip()) > 0


# =============================================================================
# ORCHESTRATION SERVICE HELPER
# =============================================================================


class OrchestrationService:
    """
    Internal service for orchestration operations.
    Provides shared functionality for orchestration actions.
    """

    def __init__(self, db: Database):
        self.db = db
        self.proposal_repo = ProposalRepository(db)

    async def parse_subagent_output(
        self,
        output_data: Dict[str, Any]
    ) -> List[FileProposal]:
        """
        Parse subagent output and extract file proposals.

        Expected output_data structure:
        {
            "files_to_modify": [
                {
                    "file_path": "/path/to/file.py",
                    "operation": "modify",
                    "new_content": "...",
                    "old_content": "...",
                    "reason": "Add feature X"
                }
            ],
            "files_to_create": [...],
            "files_to_delete": [...]
        }
        """
        proposals = []

        # Handle files_to_modify
        for item in output_data.get("files_to_modify", []):
            proposals.append(FileProposal(
                file_path=item.get("file_path", ""),
                operation="modify",
                content=item.get("new_content"),
                old_content=item.get("old_content"),
                reason=item.get("reason", "No reason provided")
            ))

        # Handle files_to_create
        for item in output_data.get("files_to_create", []):
            proposals.append(FileProposal(
                file_path=item.get("file_path", ""),
                operation="write",
                content=item.get("content"),
                reason=item.get("reason", "No reason provided")
            ))

        # Handle files_to_delete
        for item in output_data.get("files_to_delete", []):
            proposals.append(FileProposal(
                file_path=item.get("file_path", ""),
                operation="delete",
                reason=item.get("reason", "No reason provided")
            ))

        return proposals

    async def create_proposals_from_file_proposals(
        self,
        file_proposals: List[FileProposal],
        agent_id: str,
        priority: ProposalPriority,
        auto_submit: bool = True
    ) -> List[Proposal]:
        """
        Create Proposal objects from FileProposal list.
        """
        created_proposals = []

        for fp in file_proposals:
            # Determine action type based on operation
            if fp.operation == "write":
                action_type = "file.write"
            elif fp.operation == "modify":
                action_type = "file.modify"
            elif fp.operation == "delete":
                action_type = "file.delete"
            else:
                logger.warning(f"Unknown operation: {fp.operation}, skipping")
                continue

            # Build payload
            payload = {
                "file_path": fp.file_path,
                "reason": fp.reason,
            }

            if fp.content is not None:
                if fp.operation == "write":
                    payload["content"] = fp.content
                else:
                    payload["new_content"] = fp.content

            if fp.old_content is not None:
                payload["old_content"] = fp.old_content

            # Create proposal
            proposal = Proposal(
                action_type=action_type,
                payload=payload,
                priority=priority,
                created_by=agent_id,
            )

            if auto_submit:
                proposal.submit(submitter_id=agent_id)

            # Save to repository
            await self.proposal_repo.save(proposal, actor_id=agent_id)
            created_proposals.append(proposal)

        return created_proposals


# =============================================================================
# PROCESS SUBAGENT OUTPUT ACTION
# =============================================================================


@register_action
class ProcessSubagentOutputAction(ActionType[OrchestrationResult]):
    """
    Process subagent output and create file-level proposals.

    This action parses the output from a subagent (Explore, Plan, general-purpose)
    and creates individual Proposal objects for each file modification.

    Parameters:
        agent_id: The subagent ID that produced the output
        output_file: Path to the subagent output file (optional)
        output_data: Direct output data as dict (optional)
        approval_mode: "interactive" | "batch" | "auto"
        priority: Proposal priority level (default: medium)

    Returns:
        OrchestrationResult with proposal_ids and summary

    Note: Either output_file or output_data must be provided.
    """
    api_name: ClassVar[str] = "orchestration.process_subagent_output"
    object_type: ClassVar[Type[OntologyObject]] = OrchestrationResult
    requires_proposal: ClassVar[bool] = False  # Orchestration itself doesn't need proposal

    submission_criteria = [
        RequiredField("agent_id"),
        CustomValidator(
            name="ValidAgentId",
            validator_fn=validate_agent_id,
            error_message="agent_id must be a non-empty string"
        ),
        CustomValidator(
            name="OutputSourceProvided",
            validator_fn=validate_output_source,
            error_message="Either output_file or output_data must be provided"
        ),
        AllowedValues("approval_mode", ["interactive", "batch", "auto"]),
        AllowedValues("priority", ["low", "medium", "high", "critical"]),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Process subagent output and create proposals."""
        agent_id = params["agent_id"]
        output_file = params.get("output_file")
        output_data = params.get("output_data")
        approval_mode = params.get("approval_mode", "interactive")
        priority_str = params.get("priority", "medium")

        priority = ProposalPriority(priority_str)
        auto_submit = approval_mode != "interactive"

        # Load output data from file if needed
        if output_file and not output_data:
            try:
                output_path = Path(output_file)
                if not output_path.exists():
                    return ActionResult(
                        action_type=self.api_name,
                        success=False,
                        error=f"Output file not found: {output_file}",
                        error_details={"output_file": output_file}
                    )

                content = output_path.read_text(encoding="utf-8")
                output_data = json.loads(content)
            except json.JSONDecodeError as e:
                return ActionResult(
                    action_type=self.api_name,
                    success=False,
                    error=f"Invalid JSON in output file: {e}",
                    error_details={"output_file": output_file}
                )
            except Exception as e:
                return ActionResult(
                    action_type=self.api_name,
                    success=False,
                    error=f"Failed to read output file: {e}",
                    error_details={"output_file": output_file}
                )

        if not output_data or not isinstance(output_data, dict):
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error="output_data must be a non-empty dictionary",
            )

        try:
            # Get database from context if available, otherwise use default path
            db_path = params.get("db_path", ".agent/tmp/ontology.db")
            db = Database(db_path)
            await db.init()

            service = OrchestrationService(db)

            # Parse subagent output
            file_proposals = await service.parse_subagent_output(output_data)

            if not file_proposals:
                return ActionResult(
                    action_type=self.api_name,
                    success=True,
                    data=OrchestrationResult(
                        operation="process",
                        proposal_ids=[],
                        summary={"message": "No file proposals found in output"},
                        success_count=0,
                        failure_count=0,
                        created_by=context.actor_id,
                    ),
                    message="No file proposals found in subagent output"
                )

            # Create proposals
            proposals = await service.create_proposals_from_file_proposals(
                file_proposals=file_proposals,
                agent_id=agent_id,
                priority=priority,
                auto_submit=auto_submit
            )

            proposal_ids = [p.id for p in proposals]

            result = OrchestrationResult(
                operation="process",
                proposal_ids=proposal_ids,
                summary={
                    "total_proposals": len(proposals),
                    "approval_mode": approval_mode,
                    "priority": priority_str,
                    "agent_id": agent_id,
                    "proposals_by_type": {
                        "file.write": sum(1 for p in proposals if p.action_type == "file.write"),
                        "file.modify": sum(1 for p in proposals if p.action_type == "file.modify"),
                        "file.delete": sum(1 for p in proposals if p.action_type == "file.delete"),
                    }
                },
                success_count=len(proposals),
                failure_count=0,
                created_by=context.actor_id,
            )

            edit = EditOperation(
                edit_type=EditType.CREATE,
                object_type="OrchestrationResult",
                object_id=result.id,
                changes={
                    "operation": "process",
                    "proposal_count": len(proposals),
                    "agent_id": agent_id,
                    "actor": context.actor_id,
                }
            )

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data=result,
                edits=[edit],
                created_ids=proposal_ids,
                message=f"Created {len(proposals)} proposals from subagent output"
            )

        except Exception as e:
            logger.exception(f"Failed to process subagent output: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__}
            )


# =============================================================================
# EXECUTE PROPOSAL BATCH ACTION
# =============================================================================


@register_action
class ExecuteProposalBatchAction(ActionType[OrchestrationResult]):
    """
    Execute a batch of approved proposals.

    This action executes all approved proposals in the specified list,
    then optionally runs Stage C verification to ensure quality.

    Parameters:
        proposal_ids: List of proposal IDs to execute
        verify_after: Run Stage C verification after execution (default: True)
        stage_c_checks: List of checks to run ["build", "tests", "lint"] (default: all)

    Returns:
        OrchestrationResult with execution results and Stage C evidence
    """
    api_name: ClassVar[str] = "orchestration.execute_batch"
    object_type: ClassVar[Type[OntologyObject]] = OrchestrationResult
    requires_proposal: ClassVar[bool] = False

    submission_criteria = [
        RequiredField("proposal_ids"),
        CustomValidator(
            name="ProposalIdsNotEmpty",
            validator_fn=validate_proposal_ids_not_empty,
            error_message="proposal_ids must be a non-empty list"
        ),
        ArraySizeValidator("proposal_ids", min_size=1, max_size=100),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Execute batch of approved proposals."""
        proposal_ids = params["proposal_ids"]
        verify_after = params.get("verify_after", True)
        stage_c_checks = params.get("stage_c_checks", ["build", "tests", "lint"])

        success_count = 0
        failure_count = 0
        executed_ids = []
        error_details = []

        try:
            db_path = params.get("db_path", ".agent/tmp/ontology.db")
            db = Database(db_path)
            await db.init()

            proposal_repo = ProposalRepository(db)

            for proposal_id in proposal_ids:
                try:
                    # Fetch proposal
                    proposal = await proposal_repo.find_by_id(proposal_id)

                    if not proposal:
                        error_details.append({
                            "proposal_id": proposal_id,
                            "error": "Proposal not found"
                        })
                        failure_count += 1
                        continue

                    if proposal.status != ProposalStatus.APPROVED:
                        error_details.append({
                            "proposal_id": proposal_id,
                            "error": f"Proposal not approved (status: {proposal.status.value})"
                        })
                        failure_count += 1
                        continue

                    # Get the action class
                    action_cls = action_registry.get(proposal.action_type)
                    if not action_cls:
                        error_details.append({
                            "proposal_id": proposal_id,
                            "error": f"Action type not found: {proposal.action_type}"
                        })
                        failure_count += 1
                        continue

                    # Execute the action
                    action = action_cls()
                    action_result = await action.execute(proposal.payload, context)

                    if action_result.success:
                        # Mark proposal as executed
                        await proposal_repo.execute(
                            proposal_id=proposal_id,
                            executor_id=context.actor_id,
                            result=action_result.to_dict()
                        )
                        executed_ids.append(proposal_id)
                        success_count += 1
                    else:
                        error_details.append({
                            "proposal_id": proposal_id,
                            "error": action_result.error or "Execution failed",
                            "details": action_result.error_details
                        })
                        failure_count += 1

                except Exception as e:
                    logger.exception(f"Failed to execute proposal {proposal_id}: {e}")
                    error_details.append({
                        "proposal_id": proposal_id,
                        "error": str(e),
                        "exception_type": type(e).__name__
                    })
                    failure_count += 1

            # Run Stage C verification if requested
            stage_c_evidence = None
            if verify_after and executed_ids:
                try:
                    from lib.oda.ontology.actions.quality_actions import StageCVerifyAction

                    verify_action = StageCVerifyAction()
                    verify_result = await verify_action.execute(
                        {"checks_to_run": stage_c_checks},
                        context
                    )

                    if verify_result.success and verify_result.data:
                        if isinstance(verify_result.data, StageCEvidence):
                            stage_c_evidence = verify_result.data.model_dump()
                        else:
                            stage_c_evidence = verify_result.data

                except Exception as e:
                    logger.warning(f"Stage C verification failed: {e}")
                    stage_c_evidence = {"error": str(e)}

            result = OrchestrationResult(
                operation="execute",
                proposal_ids=executed_ids,
                summary={
                    "requested": len(proposal_ids),
                    "executed": success_count,
                    "failed": failure_count,
                    "verify_after": verify_after,
                },
                stage_c_evidence=stage_c_evidence,
                success_count=success_count,
                failure_count=failure_count,
                error_details=error_details if error_details else None,
                created_by=context.actor_id,
            )

            edit = EditOperation(
                edit_type=EditType.MODIFY,
                object_type="OrchestrationResult",
                object_id=result.id,
                changes={
                    "operation": "execute",
                    "executed_count": success_count,
                    "failed_count": failure_count,
                    "actor": context.actor_id,
                }
            )

            message = f"Executed {success_count}/{len(proposal_ids)} proposals"
            if failure_count > 0:
                message += f" ({failure_count} failed)"

            return ActionResult(
                action_type=self.api_name,
                success=True,  # Action succeeded even if some proposals failed
                data=result,
                edits=[edit],
                modified_ids=executed_ids,
                message=message
            )

        except Exception as e:
            logger.exception(f"Failed to execute proposal batch: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__}
            )


# =============================================================================
# ROLLBACK PROPOSALS ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class RollbackProposalsAction(ActionType[OrchestrationResult]):
    """
    Rollback previously executed file proposals.

    This is a HAZARDOUS action requiring proposal approval.
    It attempts to revert file changes made by previously executed proposals.

    Parameters:
        proposal_ids: List of proposal IDs to rollback
        reason: Reason for rollback (required)

    Returns:
        OrchestrationResult with rollback results

    Warning: Rollback may fail if files have been modified since execution.
    """
    api_name: ClassVar[str] = "orchestration.rollback"
    object_type: ClassVar[Type[OntologyObject]] = OrchestrationResult
    requires_proposal: ClassVar[bool] = True

    submission_criteria = [
        RequiredField("proposal_ids"),
        RequiredField("reason"),
        CustomValidator(
            name="ProposalIdsNotEmpty",
            validator_fn=validate_proposal_ids_not_empty,
            error_message="proposal_ids must be a non-empty list"
        ),
        CustomValidator(
            name="RollbackReasonProvided",
            validator_fn=validate_rollback_reason,
            error_message="reason must be a non-empty string"
        ),
        ArraySizeValidator("proposal_ids", min_size=1, max_size=50),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Rollback executed proposals."""
        proposal_ids = params["proposal_ids"]
        reason = params["reason"]

        success_count = 0
        failure_count = 0
        rolled_back_ids = []
        error_details = []

        try:
            db_path = params.get("db_path", ".agent/tmp/ontology.db")
            db = Database(db_path)
            await db.init()

            proposal_repo = ProposalRepository(db)

            for proposal_id in proposal_ids:
                try:
                    # Fetch proposal with history
                    proposal = await proposal_repo.find_by_id(proposal_id)

                    if not proposal:
                        error_details.append({
                            "proposal_id": proposal_id,
                            "error": "Proposal not found"
                        })
                        failure_count += 1
                        continue

                    if proposal.status != ProposalStatus.EXECUTED:
                        error_details.append({
                            "proposal_id": proposal_id,
                            "error": f"Proposal not executed (status: {proposal.status.value})"
                        })
                        failure_count += 1
                        continue

                    # Attempt to rollback based on action type
                    rollback_success = await self._rollback_proposal(proposal, context)

                    if rollback_success:
                        # Update proposal with rollback info
                        proposal.execution_result = proposal.execution_result or {}
                        proposal.execution_result["rolled_back"] = True
                        proposal.execution_result["rollback_reason"] = reason
                        proposal.execution_result["rollback_at"] = utc_now().isoformat()
                        proposal.execution_result["rollback_by"] = context.actor_id

                        await proposal_repo.save(
                            proposal,
                            actor_id=context.actor_id,
                            comment=f"Rolled back: {reason}"
                        )

                        rolled_back_ids.append(proposal_id)
                        success_count += 1
                    else:
                        error_details.append({
                            "proposal_id": proposal_id,
                            "error": "Rollback failed - file may have been modified"
                        })
                        failure_count += 1

                except Exception as e:
                    logger.exception(f"Failed to rollback proposal {proposal_id}: {e}")
                    error_details.append({
                        "proposal_id": proposal_id,
                        "error": str(e),
                        "exception_type": type(e).__name__
                    })
                    failure_count += 1

            result = OrchestrationResult(
                operation="rollback",
                proposal_ids=rolled_back_ids,
                summary={
                    "requested": len(proposal_ids),
                    "rolled_back": success_count,
                    "failed": failure_count,
                    "reason": reason,
                },
                success_count=success_count,
                failure_count=failure_count,
                error_details=error_details if error_details else None,
                created_by=context.actor_id,
            )

            edit = EditOperation(
                edit_type=EditType.MODIFY,
                object_type="OrchestrationResult",
                object_id=result.id,
                changes={
                    "operation": "rollback",
                    "rolled_back_count": success_count,
                    "failed_count": failure_count,
                    "reason": reason,
                    "actor": context.actor_id,
                }
            )

            message = f"Rolled back {success_count}/{len(proposal_ids)} proposals"
            if failure_count > 0:
                message += f" ({failure_count} failed)"

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data=result,
                edits=[edit],
                modified_ids=rolled_back_ids,
                message=message
            )

        except Exception as e:
            logger.exception(f"Failed to rollback proposals: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__}
            )

    async def _rollback_proposal(
        self,
        proposal: Proposal,
        context: ActionContext
    ) -> bool:
        """
        Attempt to rollback a single proposal.
        Returns True if successful, False otherwise.
        """
        payload = proposal.payload
        file_path = payload.get("file_path")

        if not file_path:
            logger.warning(f"No file_path in proposal {proposal.id}")
            return False

        path = Path(file_path)

        try:
            if proposal.action_type == "file.write":
                # Rollback write = delete file
                if path.exists():
                    path.unlink()
                return True

            elif proposal.action_type == "file.modify":
                # Rollback modify = restore old content
                old_content = payload.get("old_content")
                if old_content is not None:
                    path.write_text(old_content, encoding="utf-8")
                    return True
                else:
                    logger.warning(f"No old_content to restore for {proposal.id}")
                    return False

            elif proposal.action_type == "file.delete":
                # Rollback delete = we cannot restore deleted content
                # This would require storing the content before deletion
                logger.warning(f"Cannot rollback delete for {proposal.id} - content not preserved")
                return False

            else:
                logger.warning(f"Unknown action type for rollback: {proposal.action_type}")
                return False

        except Exception as e:
            logger.exception(f"Rollback failed for {proposal.id}: {e}")
            return False


# =============================================================================
# GET ORCHESTRATION STATUS ACTION
# =============================================================================


@register_action
class GetOrchestrationStatusAction(ActionType[OrchestrationResult]):
    """
    Get current orchestration status.

    Returns pending proposals, executed proposals, and Stage C results.
    Useful for monitoring the orchestration pipeline state.

    Parameters:
        include_executed: Include recently executed proposals (default: True)
        include_pending: Include pending proposals (default: True)
        include_stage_c: Include latest Stage C results (default: True)
        limit: Maximum number of proposals to return per category (default: 20)

    Returns:
        OrchestrationResult with status summary
    """
    api_name: ClassVar[str] = "orchestration.status"
    object_type: ClassVar[Type[OntologyObject]] = OrchestrationResult
    requires_proposal: ClassVar[bool] = False

    submission_criteria = []  # All parameters optional

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> ActionResult:
        """Get orchestration status."""
        include_executed = params.get("include_executed", True)
        include_pending = params.get("include_pending", True)
        include_stage_c = params.get("include_stage_c", True)
        limit = params.get("limit", 20)

        try:
            db_path = params.get("db_path", ".agent/tmp/ontology.db")
            db = Database(db_path)
            await db.init()

            proposal_repo = ProposalRepository(db)

            summary = {}
            all_proposal_ids = []

            # Get status counts
            status_counts = await proposal_repo.count_by_status()
            summary["status_counts"] = status_counts

            # Get pending proposals
            if include_pending:
                pending = await proposal_repo.find_pending(limit=limit)
                summary["pending_proposals"] = [
                    {
                        "id": p.id,
                        "action_type": p.action_type,
                        "priority": p.priority.value,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                        "created_by": p.created_by,
                    }
                    for p in pending
                ]
                all_proposal_ids.extend([p.id for p in pending])

            # Get recently executed proposals
            if include_executed:
                executed = await proposal_repo.find_by_status(
                    ProposalStatus.EXECUTED,
                    limit=limit
                )
                summary["executed_proposals"] = [
                    {
                        "id": p.id,
                        "action_type": p.action_type,
                        "executed_at": p.executed_at.isoformat() if p.executed_at else None,
                        "created_by": p.created_by,
                    }
                    for p in executed
                ]
                all_proposal_ids.extend([p.id for p in executed])

            # Get approved proposals (ready to execute)
            approved = await proposal_repo.find_by_status(
                ProposalStatus.APPROVED,
                limit=limit
            )
            summary["approved_proposals"] = [
                {
                    "id": p.id,
                    "action_type": p.action_type,
                    "priority": p.priority.value,
                    "approved_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
                    "approved_by": p.reviewed_by,
                }
                for p in approved
            ]
            all_proposal_ids.extend([p.id for p in approved])

            # Include Stage C results if requested
            stage_c_evidence = None
            if include_stage_c:
                try:
                    from lib.oda.ontology.actions.quality_actions import StageCVerifyAction

                    # Run a quick status check (skipped checks)
                    verify_action = StageCVerifyAction()
                    verify_result = await verify_action.execute(
                        {"checks_to_run": []},  # Just get structure
                        context
                    )

                    if verify_result.success and verify_result.data:
                        if isinstance(verify_result.data, StageCEvidence):
                            stage_c_evidence = verify_result.data.to_summary()
                except Exception as e:
                    logger.warning(f"Could not get Stage C status: {e}")

            result = OrchestrationResult(
                operation="status",
                proposal_ids=list(set(all_proposal_ids)),  # Deduplicate
                summary=summary,
                stage_c_evidence=stage_c_evidence,
                success_count=len(all_proposal_ids),
                failure_count=0,
                created_by=context.actor_id,
            )

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data=result,
                message=f"Retrieved orchestration status: {len(summary.get('pending_proposals', []))} pending, {len(summary.get('approved_proposals', []))} approved"
            )

        except Exception as e:
            logger.exception(f"Failed to get orchestration status: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__}
            )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Actions
    "ProcessSubagentOutputAction",
    "ExecuteProposalBatchAction",
    "RollbackProposalsAction",
    "GetOrchestrationStatusAction",
    # Models
    "OrchestrationResult",
    "FileProposal",
    # Service
    "OrchestrationService",
]
