"""
Orion ODA v3.0 - Workflow ObjectTypes
PAI Prompting Skill Migration - Phase 4

This module defines workflow execution ObjectTypes:
- Workflow: A sequence of steps that execute a skill
- WorkflowStep: A single step in a workflow

Workflows provide structured, auditable skill execution with
validation, error handling, and rollback capabilities.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import Field, field_validator, model_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# ENUMS
# =============================================================================

class WorkflowStatus(str, Enum):
    """Workflow lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class StepStatus(str, Enum):
    """Step execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Type of workflow step."""
    ACTION = "action"          # Execute an ActionType
    CONDITION = "condition"    # Conditional branching
    LOOP = "loop"              # Iterate over collection
    PARALLEL = "parallel"      # Execute steps in parallel
    WAIT = "wait"              # Wait for external event
    TRANSFORM = "transform"    # Data transformation
    VALIDATE = "validate"      # Validation check


class ValidationMode(str, Enum):
    """How to handle validation failures."""
    STRICT = "strict"          # Fail immediately on any error
    LENIENT = "lenient"        # Continue with warnings
    SKIP = "skip"              # Skip validation entirely


# =============================================================================
# VALID STATE TRANSITIONS
# =============================================================================

VALID_STEP_TRANSITIONS: Dict[StepStatus, Set[StepStatus]] = {
    StepStatus.PENDING: {
        StepStatus.IN_PROGRESS,
        StepStatus.SKIPPED,
        StepStatus.CANCELLED,
    },
    StepStatus.IN_PROGRESS: {
        StepStatus.COMPLETED,
        StepStatus.FAILED,
        StepStatus.CANCELLED,
    },
    StepStatus.COMPLETED: set(),  # Terminal
    StepStatus.FAILED: set(),     # Terminal
    StepStatus.SKIPPED: set(),    # Terminal
    StepStatus.CANCELLED: set(),  # Terminal
}


# =============================================================================
# WORKFLOW STEP OBJECTTYPE
# =============================================================================

@register_object_type
class WorkflowStep(OntologyObject):
    """
    Represents a single step in a workflow.

    A WorkflowStep defines:
    - What action to execute (action_type + params)
    - When to execute (order, conditions)
    - How to validate success (success_criteria)
    - What to do on failure (error_handling)

    Steps are executed in order within a workflow, with support
    for conditional execution, error handling, and retry logic.

    Attributes:
        name: Human-readable step name
        order: Execution order (0-based)
        step_type: Type of step (action, condition, etc.)
        action_type: The ActionType API name to execute
        params: Parameters for the action
        success_criteria: Conditions for step success
        error_handling: How to handle errors
        retry_config: Retry configuration
        timeout_seconds: Step timeout
        condition: Optional condition for step execution
        workflow_id: FK to parent Workflow
        depends_on_step_ids: IDs of steps this depends on
        step_status: Current execution status
        output: Step output data

    Example:
        ```python
        step = WorkflowStep(
            name="Read source files",
            order=0,
            action_type="read_file",
            params={"path": "/src/main.py"},
            success_criteria={"file_exists": True},
            timeout_seconds=30
        )
        ```
    """

    # Identity
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable step name"
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="Step description"
    )

    # Execution order
    order: int = Field(
        default=0,
        ge=0,
        description="Execution order (0-based)"
    )

    # Step type
    step_type: StepType = Field(
        default=StepType.ACTION,
        description="Type of step"
    )

    # Action configuration
    action_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="The ActionType API name to execute"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the action"
    )

    # Success criteria
    success_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conditions for step success"
    )

    # Error handling
    error_handling: Dict[str, Any] = Field(
        default_factory=lambda: {
            "on_error": "fail",  # fail, skip, retry, continue
            "fallback_action": None,
            "max_retries": 0,
        },
        description="How to handle errors"
    )

    # Retry configuration
    retry_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_attempts": 1,
            "delay_seconds": 1,
            "backoff_multiplier": 2.0,
            "max_delay_seconds": 60,
        },
        description="Retry configuration"
    )

    # Timeout
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Step timeout in seconds"
    )

    # Conditional execution
    condition: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Condition expression for step execution"
    )

    # Relationships
    workflow_id: Optional[str] = Field(
        default=None,
        description="FK to parent Workflow"
    )
    depends_on_step_ids: List[str] = Field(
        default_factory=list,
        description="IDs of steps this depends on"
    )

    # Runtime state
    step_status: StepStatus = Field(
        default=StepStatus.PENDING,
        description="Current execution status"
    )
    output: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step output data"
    )
    error_message: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Error message if failed"
    )

    # Timing
    started_at: Optional[datetime] = Field(
        default=None,
        description="Step start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Step completion timestamp"
    )
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Step duration in milliseconds"
    )

    # Retry tracking
    attempt_count: int = Field(
        default=0,
        ge=0,
        description="Number of execution attempts"
    )

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        """Ensure action_type follows snake_case convention."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                f"action_type must be snake_case alphanumeric: {v}"
            )
        return v.lower()

    @property
    def is_terminal(self) -> bool:
        """Check if step is in a terminal state."""
        return self.step_status in {
            StepStatus.COMPLETED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
            StepStatus.CANCELLED,
        }

    @property
    def is_pending(self) -> bool:
        """Check if step is pending execution."""
        return self.step_status == StepStatus.PENDING

    @property
    def is_running(self) -> bool:
        """Check if step is currently running."""
        return self.step_status == StepStatus.IN_PROGRESS

    @property
    def is_success(self) -> bool:
        """Check if step completed successfully."""
        return self.step_status == StepStatus.COMPLETED

    @property
    def has_dependencies(self) -> bool:
        """Check if step has dependencies."""
        return len(self.depends_on_step_ids) > 0

    def can_retry(self) -> bool:
        """Check if step can be retried."""
        max_attempts = self.retry_config.get("max_attempts", 1)
        return self.attempt_count < max_attempts

    def start(self) -> "WorkflowStep":
        """Mark step as started."""
        if self.step_status != StepStatus.PENDING:
            raise ValueError(f"Cannot start step in state: {self.step_status.value}")
        self.step_status = StepStatus.IN_PROGRESS
        self.started_at = utc_now()
        self.attempt_count += 1
        self.touch()
        return self

    def complete(
        self,
        output: Optional[Dict[str, Any]] = None
    ) -> "WorkflowStep":
        """Mark step as completed."""
        if self.step_status != StepStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete step in state: {self.step_status.value}")
        self.step_status = StepStatus.COMPLETED
        self.completed_at = utc_now()
        if output:
            self.output = output
        self._calculate_duration()
        self.touch()
        return self

    def fail(
        self,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> "WorkflowStep":
        """Mark step as failed."""
        if self.step_status != StepStatus.IN_PROGRESS:
            raise ValueError(f"Cannot fail step in state: {self.step_status.value}")
        self.step_status = StepStatus.FAILED
        self.completed_at = utc_now()
        self.error_message = error_message
        if error_details:
            self.output["error_details"] = error_details
        self._calculate_duration()
        self.touch()
        return self

    def skip(self, reason: Optional[str] = None) -> "WorkflowStep":
        """Skip step execution."""
        if self.step_status != StepStatus.PENDING:
            raise ValueError(f"Cannot skip step in state: {self.step_status.value}")
        self.step_status = StepStatus.SKIPPED
        if reason:
            self.output["skip_reason"] = reason
        self.touch()
        return self

    def cancel(self) -> "WorkflowStep":
        """Cancel step execution."""
        if self.is_terminal:
            raise ValueError(f"Cannot cancel step in state: {self.step_status.value}")
        self.step_status = StepStatus.CANCELLED
        if self.started_at:
            self.completed_at = utc_now()
            self._calculate_duration()
        self.touch()
        return self

    def reset(self) -> "WorkflowStep":
        """Reset step to pending state."""
        self.step_status = StepStatus.PENDING
        self.output = {}
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        self.duration_ms = 0
        # Note: attempt_count is preserved for retry tracking
        self.touch()
        return self

    def _calculate_duration(self) -> None:
        """Calculate step duration."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def to_audit_log(self) -> Dict[str, Any]:
        """Generate an audit log entry."""
        return {
            "step_id": self.id,
            "step_name": self.name,
            "order": self.order,
            "action_type": self.action_type,
            "status": self.step_status.value,
            "attempt_count": self.attempt_count,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }

    def __repr__(self) -> str:
        return (
            f"WorkflowStep(name='{self.name}', "
            f"order={self.order}, "
            f"action='{self.action_type}', "
            f"status={self.step_status.value})"
        )


# =============================================================================
# WORKFLOW OBJECTTYPE
# =============================================================================

@register_object_type
class Workflow(OntologyObject):
    """
    Represents a workflow - a sequence of steps that execute a skill.

    A Workflow provides:
    - Step orchestration with dependency management
    - Input/output validation
    - Error handling and recovery
    - Execution state tracking
    - Audit logging

    Workflows are the execution unit for skills. When a skill is triggered,
    its associated workflow is instantiated and executed.

    Attributes:
        name: Unique workflow identifier
        display_name: Human-readable name
        description: Workflow description
        step_ids: Ordered list of step IDs
        validation_mode: How to handle validation failures
        input_schema: JSON Schema for workflow input
        output_schema: JSON Schema for workflow output
        workflow_status: Lifecycle status
        skill_definition_id: FK to parent SkillDefinition
        input_data: Workflow input data
        output_data: Workflow output data
        execution_context: Runtime context
        error_details: Error information if failed

    Example:
        ```python
        workflow = Workflow(
            name="code_review_workflow",
            display_name="Code Review",
            validation_mode=ValidationMode.STRICT,
            input_schema={"type": "object", "required": ["file_path"]}
        )
        ```
    """

    # Identity
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique workflow identifier (snake_case)"
    )
    display_name: str = Field(
        default="",
        max_length=200,
        description="Human-readable name"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Workflow description"
    )
    version: str = Field(
        default="1.0.0",
        max_length=20,
        description="Semantic version"
    )

    # Steps
    step_ids: List[str] = Field(
        default_factory=list,
        description="Ordered list of step IDs"
    )

    # Validation
    validation_mode: ValidationMode = Field(
        default=ValidationMode.STRICT,
        description="How to handle validation failures"
    )
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for workflow input"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for workflow output"
    )

    # Lifecycle
    workflow_status: WorkflowStatus = Field(
        default=WorkflowStatus.DRAFT,
        description="Lifecycle status"
    )

    # Relationships
    skill_definition_id: Optional[str] = Field(
        default=None,
        description="FK to parent SkillDefinition"
    )

    # Execution state
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow input data"
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow output data"
    )
    execution_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime context (shared between steps)"
    )

    # Error handling
    error_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Error information if failed"
    )

    # Timeout
    timeout_seconds: int = Field(
        default=600,
        ge=1,
        le=7200,
        description="Total workflow timeout in seconds"
    )

    # Execution tracking
    current_step_index: int = Field(
        default=0,
        ge=0,
        description="Index of currently executing step"
    )
    completed_step_count: int = Field(
        default=0,
        ge=0,
        description="Number of completed steps"
    )

    # Timing
    started_at: Optional[datetime] = Field(
        default=None,
        description="Workflow start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Workflow completion timestamp"
    )
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Total duration in milliseconds"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name follows snake_case convention."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"name must be alphanumeric with underscores/hyphens: {v}"
            )
        return v.lower()

    @property
    def is_enabled(self) -> bool:
        """Check if workflow is enabled."""
        return self.workflow_status == WorkflowStatus.ACTIVE

    @property
    def step_count(self) -> int:
        """Get number of steps."""
        return len(self.step_ids)

    @property
    def progress_percent(self) -> float:
        """Get execution progress percentage."""
        if not self.step_ids:
            return 100.0
        return (self.completed_step_count / len(self.step_ids)) * 100

    @property
    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return self.completed_step_count >= len(self.step_ids)

    def add_step(self, step: WorkflowStep) -> "Workflow":
        """
        Add a step to the workflow.

        Args:
            step: WorkflowStep to add

        Returns:
            self for method chaining
        """
        step.workflow_id = self.id
        step.order = len(self.step_ids)
        self.step_ids.append(step.id)
        self.touch()
        return self

    def remove_step(self, step_id: str) -> "Workflow":
        """
        Remove a step from the workflow.

        Args:
            step_id: ID of step to remove

        Returns:
            self for method chaining
        """
        if step_id in self.step_ids:
            self.step_ids.remove(step_id)
            self.touch()
        return self

    def start(self, input_data: Optional[Dict[str, Any]] = None) -> "Workflow":
        """
        Start workflow execution.

        Args:
            input_data: Input data for the workflow

        Returns:
            self for method chaining
        """
        if input_data:
            self.input_data = input_data
        self.started_at = utc_now()
        self.current_step_index = 0
        self.completed_step_count = 0
        self.execution_context = {"workflow_id": self.id}
        self.touch()
        return self

    def complete(
        self,
        output_data: Optional[Dict[str, Any]] = None
    ) -> "Workflow":
        """
        Mark workflow as complete.

        Args:
            output_data: Output data from the workflow

        Returns:
            self for method chaining
        """
        self.completed_at = utc_now()
        if output_data:
            self.output_data = output_data
        self._calculate_duration()
        self.touch()
        return self

    def fail(
        self,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> "Workflow":
        """
        Mark workflow as failed.

        Args:
            error_message: Error message
            error_details: Additional error details

        Returns:
            self for method chaining
        """
        self.completed_at = utc_now()
        self.error_details = {
            "message": error_message,
            "details": error_details or {},
            "failed_at_step": self.current_step_index,
        }
        self._calculate_duration()
        self.touch()
        return self

    def step_completed(self, step_output: Optional[Dict[str, Any]] = None) -> "Workflow":
        """
        Mark current step as completed and advance.

        Args:
            step_output: Output from the completed step

        Returns:
            self for method chaining
        """
        self.completed_step_count += 1
        self.current_step_index += 1

        # Store step output in context
        if step_output:
            step_key = f"step_{self.current_step_index - 1}_output"
            self.execution_context[step_key] = step_output

        self.touch()
        return self

    def activate(self) -> "Workflow":
        """Activate the workflow."""
        self.workflow_status = WorkflowStatus.ACTIVE
        self.touch()
        return self

    def deprecate(self) -> "Workflow":
        """Mark workflow as deprecated."""
        self.workflow_status = WorkflowStatus.DEPRECATED
        self.touch()
        return self

    def disable(self) -> "Workflow":
        """Disable the workflow."""
        self.workflow_status = WorkflowStatus.DISABLED
        self.touch()
        return self

    def _calculate_duration(self) -> None:
        """Calculate workflow duration."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validate input data against schema.

        Args:
            input_data: Input to validate

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.input_schema:
            return []

        errors = []

        # Simple validation - check required fields
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in input_data:
                errors.append(f"Missing required field: {field}")

        return errors

    def to_audit_log(self) -> Dict[str, Any]:
        """Generate an audit log entry."""
        return {
            "workflow_id": self.id,
            "workflow_name": self.name,
            "status": self.workflow_status.value,
            "step_count": self.step_count,
            "completed_steps": self.completed_step_count,
            "progress_percent": self.progress_percent,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_details": self.error_details,
        }

    def __repr__(self) -> str:
        return (
            f"Workflow(name='{self.name}', "
            f"steps={self.step_count}, "
            f"status={self.workflow_status.value}, "
            f"progress={self.progress_percent:.1f}%)"
        )
