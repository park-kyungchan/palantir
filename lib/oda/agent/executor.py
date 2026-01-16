"""
Orion ODA v3.0 - Agent Executor
================================

This module provides the AgentExecutor class - the ONLY entry point
for LLM agents to interact with the Ontology.

CRITICAL: All agent operations MUST go through this executor.
Direct database access or file manipulation is FORBIDDEN.

Usage:
    executor = AgentExecutor()
    result = await executor.execute_action("create_task", {"title": "Test"})
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Type

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    action_registry,
    GovernanceEngine,
)
from lib.oda.ontology.objects.proposal import Proposal, ProposalPriority
from lib.oda.ontology.storage import ProposalRepository, initialize_database
from lib.oda.ontology.ontology_types import utc_now

logger = logging.getLogger(__name__)


class ExecutionPolicy(str, Enum):
    """Execution policy returned by governance check."""
    ALLOW_IMMEDIATE = "ALLOW_IMMEDIATE"
    REQUIRE_PROPOSAL = "REQUIRE_PROPOSAL"
    DENY = "DENY"


@dataclass
class TaskResult:
    """
    Standardized result for all agent operations.

    This is the ONLY format agents should expect from the executor.
    """
    success: bool
    action_type: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    proposal_id: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "action_type": self.action_type,
            "message": self.message,
            "data": self.data,
            "proposal_id": self.proposal_id,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentExecutor:
    """
    The ONLY entry point for LLM agents to interact with the Ontology.

    This class provides:
    1. Action discovery - list available actions
    2. Action execution - run actions with validation
    3. Proposal management - create/query proposals for hazardous actions
    4. Query interface - read Ontology data (future)

    CRITICAL RULES:
    - All operations return TaskResult
    - All errors are caught and returned as TaskResult with success=False
    - No exceptions should propagate to the agent

    Example:
        executor = AgentExecutor()
        await executor.initialize()

        # Execute an action
        result = await executor.execute_action(
            action_type="create_task",
            params={"title": "My Task", "priority": "high"},
            actor_id="agent-001"
        )

        if result.success:
            task_id = result.data.get("created_ids", [])[0]
            print(f"Created task: {task_id}")
        else:
            print(f"Error: {result.message}")
    """

    def __init__(self):
        self._initialized = False
        self._db = None
        self._repo: Optional[ProposalRepository] = None
        self._governance = GovernanceEngine(action_registry)

    async def initialize(self) -> TaskResult:
        """
        Initialize the executor. MUST be called before any operation.

        Returns:
            TaskResult indicating success or failure
        """
        try:
            self._db = await initialize_database()
            self._repo = ProposalRepository(self._db)
            self._initialized = True
            return TaskResult(
                success=True,
                action_type="initialize",
                message="AgentExecutor initialized successfully",
                data={"status": "ready"}
            )
        except Exception as e:
            logger.exception("Failed to initialize AgentExecutor")
            return TaskResult(
                success=False,
                action_type="initialize",
                message=f"Initialization failed: {str(e)}",
                error_code="INIT_FAILED"
            )

    def _ensure_initialized(self) -> Optional[TaskResult]:
        """Check if executor is initialized. Returns error TaskResult if not."""
        if not self._initialized:
            return TaskResult(
                success=False,
                action_type="unknown",
                message="AgentExecutor not initialized. Call initialize() first.",
                error_code="NOT_INITIALIZED"
            )
        return None

    # =========================================================================
    # ACTION DISCOVERY
    # =========================================================================

    def list_actions(self) -> TaskResult:
        """
        List all available actions in the registry.

        Returns:
            TaskResult with data containing:
            - actions: List of action names
            - hazardous: List of actions requiring proposal
        """
        actions = action_registry.list_actions()
        hazardous = action_registry.get_hazardous_actions()

        return TaskResult(
            success=True,
            action_type="list_actions",
            message=f"Found {len(actions)} registered actions",
            data={
                "actions": actions,
                "hazardous": hazardous,
                "safe": [a for a in actions if a not in hazardous]
            }
        )

    def get_action_schema(self, action_type: str) -> TaskResult:
        """
        Get the schema (required/optional params) for an action.

        Args:
            action_type: The action API name

        Returns:
            TaskResult with data containing action schema
        """
        action_cls = action_registry.get(action_type)
        if not action_cls:
            return TaskResult(
                success=False,
                action_type=action_type,
                message=f"Action '{action_type}' not found in registry",
                error_code="ACTION_NOT_FOUND"
            )

        # Extract schema from submission_criteria
        criteria = getattr(action_cls, "submission_criteria", [])
        required_fields = []
        optional_fields = []
        validators = []

        for criterion in criteria:
            if hasattr(criterion, "field_name"):
                if criterion.__class__.__name__ == "RequiredField":
                    required_fields.append(criterion.field_name)
                else:
                    optional_fields.append(criterion.field_name)
            validators.append(criterion.name if hasattr(criterion, "name") else str(criterion))

        metadata = action_registry.get_metadata(action_type)

        return TaskResult(
            success=True,
            action_type=action_type,
            message=f"Schema for '{action_type}'",
            data={
                "api_name": action_type,
                "requires_proposal": metadata.requires_proposal if metadata else False,
                "required_fields": required_fields,
                "validators": validators,
                "description": metadata.description if metadata else "",
            }
        )

    # =========================================================================
    # ACTION EXECUTION
    # =========================================================================

    async def execute_action(
        self,
        action_type: str,
        params: Dict[str, Any],
        actor_id: str = "agent",
        priority: str = "medium"
    ) -> TaskResult:
        """
        Execute an action. This is the PRIMARY method for agents.

        Execution Flow:
        1. Validate action exists
        2. Check governance policy
        3. If ALLOW_IMMEDIATE -> execute directly
        4. If REQUIRE_PROPOSAL -> create proposal and return proposal_id
        5. If DENY -> return error

        Args:
            action_type: The action API name (e.g., "create_task")
            params: Action parameters as a dictionary
            actor_id: ID of the agent/user executing the action
            priority: Priority for proposal if needed ("low", "medium", "high", "critical")

        Returns:
            TaskResult with execution outcome
        """
        # Check initialization
        init_error = self._ensure_initialized()
        if init_error:
            init_error.action_type = action_type
            return init_error

        # 1. Validate action exists
        action_cls = action_registry.get(action_type)
        if not action_cls:
            return TaskResult(
                success=False,
                action_type=action_type,
                message=f"Action '{action_type}' not found. Use list_actions() to see available actions.",
                error_code="ACTION_NOT_FOUND"
            )

        # 2. Check governance policy
        policy = self._governance.check_execution_policy(action_type)

        # 3. Handle based on policy
        if policy == "DENY":
            return TaskResult(
                success=False,
                action_type=action_type,
                message=f"Action '{action_type}' is denied by governance policy",
                error_code="GOVERNANCE_DENIED"
            )

        if policy == "REQUIRE_PROPOSAL":
            # Create a proposal instead of executing
            return await self._create_proposal(
                action_type=action_type,
                params=params,
                actor_id=actor_id,
                priority=priority
            )

        # 4. ALLOW_IMMEDIATE - Execute directly
        return await self._execute_immediate(
            action_cls=action_cls,
            action_type=action_type,
            params=params,
            actor_id=actor_id
        )

    async def _execute_immediate(
        self,
        action_cls: Type[ActionType],
        action_type: str,
        params: Dict[str, Any],
        actor_id: str
    ) -> TaskResult:
        """Execute an action immediately (no proposal required)."""
        try:
            action = action_cls()
            context = ActionContext(actor_id=actor_id)

            # Execute
            result: ActionResult = await action.execute(params, context)

            if result.success:
                return TaskResult(
                    success=True,
                    action_type=action_type,
                    message=f"Action '{action_type}' executed successfully",
                    data={
                        "created_ids": result.created_ids,
                        "modified_ids": result.modified_ids,
                        "deleted_ids": result.deleted_ids,
                        "edits_count": len(result.edits),
                    }
                )
            else:
                return TaskResult(
                    success=False,
                    action_type=action_type,
                    message=result.error or "Action execution failed",
                    error_code="EXECUTION_FAILED",
                    data=result.error_details or {}
                )
        except Exception as e:
            logger.exception(f"Action execution failed: {action_type}")
            return TaskResult(
                success=False,
                action_type=action_type,
                message=f"Execution error: {str(e)}",
                error_code="EXECUTION_ERROR"
            )

    async def _create_proposal(
        self,
        action_type: str,
        params: Dict[str, Any],
        actor_id: str,
        priority: str
    ) -> TaskResult:
        """Create a proposal for a hazardous action."""
        try:
            action_cls = action_registry.get(action_type)
            if action_cls:
                try:
                    validation_errors = action_cls().validate(params, ActionContext(actor_id=actor_id))
                except Exception as e:
                    validation_errors = [f"Validation exception: {type(e).__name__}: {e}"]

                if validation_errors:
                    return TaskResult(
                        success=False,
                        action_type=action_type,
                        message="Action parameters failed validation; proposal not created.",
                        error_code="INVALID_PARAMS",
                        data={"validation_errors": validation_errors},
                    )

            # Map priority string to enum
            priority_map = {
                "low": ProposalPriority.LOW,
                "medium": ProposalPriority.MEDIUM,
                "high": ProposalPriority.HIGH,
                "critical": ProposalPriority.CRITICAL,
            }
            proposal_priority = priority_map.get(priority, ProposalPriority.MEDIUM)

            # Create proposal
            proposal = Proposal(
                action_type=action_type,
                payload=params,
                priority=proposal_priority,
                created_by=actor_id,
            )

            # Submit for review
            proposal.submit(submitter_id=actor_id)

            # Save to database
            await self._repo.save(proposal, actor_id=actor_id)

            return TaskResult(
                success=True,
                action_type=action_type,
                message=f"Proposal created for hazardous action '{action_type}'. Awaiting approval.",
                proposal_id=proposal.id,
                data={
                    "status": "pending",
                    "requires_approval": True,
                    "priority": priority,
                }
            )
        except Exception as e:
            logger.exception(f"Failed to create proposal: {action_type}")
            return TaskResult(
                success=False,
                action_type=action_type,
                message=f"Failed to create proposal: {str(e)}",
                error_code="PROPOSAL_CREATION_FAILED"
            )

    # =========================================================================
    # PROPOSAL MANAGEMENT
    # =========================================================================

    async def get_pending_proposals(self) -> TaskResult:
        """Get all pending proposals awaiting review."""
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            proposals = await self._repo.find_pending()
            return TaskResult(
                success=True,
                action_type="get_pending_proposals",
                message=f"Found {len(proposals)} pending proposals",
                data={
                    "proposals": [
                        {
                            "id": p.id,
                            "action_type": p.action_type,
                            "priority": p.priority.value,
                            "created_by": p.created_by,
                            "created_at": p.created_at.isoformat(),
                        }
                        for p in proposals
                    ]
                }
            )
        except Exception as e:
            logger.exception("Failed to get pending proposals")
            return TaskResult(
                success=False,
                action_type="get_pending_proposals",
                message=f"Query failed: {str(e)}",
                error_code="QUERY_FAILED"
            )

    async def get_proposal(self, proposal_id: str) -> TaskResult:
        """Get details of a specific proposal."""
        init_error = self._ensure_initialized()
        if init_error:
            return init_error

        try:
            proposal = await self._repo.find_by_id(proposal_id)
            if not proposal:
                return TaskResult(
                    success=False,
                    action_type="get_proposal",
                    message=f"Proposal '{proposal_id}' not found",
                    error_code="PROPOSAL_NOT_FOUND"
                )

            return TaskResult(
                success=True,
                action_type="get_proposal",
                message="Proposal found",
                proposal_id=proposal_id,
                data={
                    "id": proposal.id,
                    "action_type": proposal.action_type,
                    "payload": proposal.payload,
                    "status": proposal.status.value,
                    "priority": proposal.priority.value,
                    "created_by": proposal.created_by,
                    "reviewed_by": proposal.reviewed_by,
                    "review_comment": proposal.review_comment,
                }
            )
        except Exception as e:
            logger.exception(f"Failed to get proposal: {proposal_id}")
            return TaskResult(
                success=False,
                action_type="get_proposal",
                message=f"Query failed: {str(e)}",
                error_code="QUERY_FAILED"
            )


# =============================================================================
# CONVENIENCE FUNCTIONS FOR AGENTS
# =============================================================================

_executor: Optional[AgentExecutor] = None


async def get_executor() -> AgentExecutor:
    """Get or create the global AgentExecutor instance."""
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
        await _executor.initialize()
    return _executor


async def execute(action_type: str, params: Dict[str, Any], actor_id: str = "agent") -> TaskResult:
    """
    Convenience function to execute an action.

    Args:
        action_type: The action API name
        params: Action parameters
        actor_id: ID of the executing agent

    Returns:
        TaskResult with execution outcome
    """
    executor = await get_executor()
    return await executor.execute_action(action_type, params, actor_id)
