"""
Workflow Actions - ODA ActionType for executing .agent/workflows/

This module bridges .agent/workflows/ with the ODA ActionRegistry,
allowing workflows to be executed as governed Actions.
"""
from typing import Dict, Any, List, Optional, ClassVar
from dataclasses import dataclass, field
from datetime import datetime, timezone

from lib.oda.ontology.actions import (
    ActionType,
    ActionResult,
    ActionContext,
    EditType,
    EditOperation,
    RequiredField,
    AllowedValues,
)
from lib.oda.workflow_runner import execute_workflow, list_workflows


# =============================================================================
# WORKFLOW ACTION
# =============================================================================

@dataclass
class WorkflowExecution:
    """Represents a workflow execution result."""
    workflow_name: str
    commands_executed: int
    success_count: int
    failure_count: int
    details: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ExecuteWorkflowAction(ActionType[WorkflowExecution]):
    """
    ActionType for executing .agent/workflows/*.md files.
    
    Parameters:
        workflow_name: Name of workflow (e.g., "01_plan", "07_memory_sync")
        turbo_only: If True, only execute // turbo marked commands
        dry_run: If True, parse but don't execute commands
    
    Example:
        await registry.execute(
            "execute_workflow",
            {"workflow_name": "07_memory_sync", "turbo_only": True},
            context
        )
    """
    
    api_name: ClassVar[str] = "execute_workflow"
    object_type: ClassVar[type] = WorkflowExecution
    
    submission_criteria = [
        RequiredField("workflow_name"),
        AllowedValues("workflow_name", list_workflows()),
    ]
    
    side_effects = []  # Workflows may have their own side effects
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        validate_only: bool = False,
        return_edits: bool = False,
    ) -> ActionResult:
        """Execute the workflow and return results."""
        workflow_name = params["workflow_name"]
        turbo_only = params.get("turbo_only", False)
        dry_run = params.get("dry_run", False)
        
        workflow_params = params.get("workflow_params", {})

        # Execute workflow (dry_run avoids command execution)
        result = execute_workflow(
            workflow_name,
            turbo_only=turbo_only,
            params=workflow_params,
            dry_run=dry_run or validate_only,
        )
        
        # Parse results
        commands = result.get("commands", [])
        success_count = sum(1 for c in commands if c.get("returncode") == 0)
        failure_count = len(commands) - success_count
        
        execution = WorkflowExecution(
            workflow_name=workflow_name,
            commands_executed=len(commands),
            success_count=success_count,
            failure_count=failure_count,
            details=commands,
        )

        if failure_count > 0 and not (dry_run or validate_only):
            first_failure = next((c for c in commands if c.get("returncode") != 0), {})
            raise RuntimeError(
                f"Workflow '{workflow_name}' failed ({failure_count} failures). "
                f"First failure: {first_failure.get('command')}"
            )
        
        # Create edit operation for audit trail
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="WorkflowExecution",
            object_id=f"wf_{workflow_name}_{execution.timestamp.isoformat()}",
            changes={
                "workflow_name": workflow_name,
                "turbo_only": turbo_only,
                "commands_executed": len(commands),
                "success_count": success_count,
                "dry_run": dry_run,
            }
        )
        
        return execution, [edit] if return_edits else []


# =============================================================================
# LIST WORKFLOWS ACTION
# =============================================================================

class ListWorkflowsAction(ActionType[List[str]]):
    """
    ActionType for listing available workflows.
    
    Example:
        result = await registry.execute("list_workflows", {}, context)
        print(result.data)  # ["00_start", "01_plan", ...]
    """
    
    api_name: ClassVar[str] = "list_workflows"
    object_type: ClassVar[str] = "WorkflowList"
    
    submission_criteria = []
    side_effects = []
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        validate_only: bool = False,
        return_edits: bool = False,
    ) -> ActionResult:
        """List all available workflows."""
        workflows = list_workflows()
        
        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=workflows,
            message=f"Found {len(workflows)} workflows",
        )


# =============================================================================
# REGISTRATION
# =============================================================================

# Export for ActionRegistry auto-discovery
WORKFLOW_ACTIONS = [
    ExecuteWorkflowAction,
    ListWorkflowsAction,
]
