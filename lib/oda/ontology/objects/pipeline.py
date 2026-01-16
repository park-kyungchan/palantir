"""
Orion ODA v4.0 - Pipeline ObjectTypes (Phase 4.3.2)
====================================================

OntologyObjects for Pipeline management - Palantir-style data pipeline
definitions that integrate with the ODA governance framework.

These ObjectTypes complement the PipelineBuilder DSL by providing:
- Persistent pipeline definitions in the ontology
- Full audit trail via OntologyObject base
- Integration with the Action/Proposal system
- Version tracking for pipeline changes

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class PipelineObjectStatus(str, Enum):
    """Pipeline lifecycle status (OntologyObject level)."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    ERROR = "error"


class PipelineRunStatus(str, Enum):
    """Pipeline execution run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StageTypeEnum(str, Enum):
    """Types of pipeline stages."""
    SOURCE = "source"
    TRANSFORM = "transform"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    JOIN = "join"
    OUTPUT = "output"


# =============================================================================
# PIPELINE STAGE OBJECT
# =============================================================================


@register_object_type
class PipelineStageObject(OntologyObject):
    """
    OntologyObject representing a single stage in a data pipeline.

    A stage is a unit of work that performs a specific operation on data.
    Stages can have dependencies on other stages, forming a DAG (directed
    acyclic graph) of data transformations.

    Attributes:
        stage_id: Unique identifier within the pipeline
        name: Human-readable stage name
        stage_type: Type of operation (source, transform, filter, etc.)
        config: Stage-specific configuration
        dependencies: List of stage_ids this stage depends on
        pipeline_id: ID of the parent pipeline
        description: Optional description
        position: Order position in the pipeline (0-indexed)
    """

    stage_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique identifier within the pipeline"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable stage name"
    )
    stage_type: StageTypeEnum = Field(
        ...,
        description="Type of pipeline stage"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific configuration"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of stage_ids this stage depends on"
    )
    pipeline_id: str = Field(
        ...,
        description="ID of the parent Pipeline object"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional stage description"
    )
    position: int = Field(
        default=0,
        ge=0,
        description="Order position in the pipeline"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is properly formatted."""
        normalized = v.strip()
        if not normalized:
            raise ValueError("Stage name cannot be empty or whitespace")
        return normalized

    @property
    def is_source(self) -> bool:
        """Check if this is a source stage."""
        return self.stage_type == StageTypeEnum.SOURCE

    @property
    def is_output(self) -> bool:
        """Check if this is an output stage."""
        return self.stage_type == StageTypeEnum.OUTPUT

    @property
    def has_dependencies(self) -> bool:
        """Check if stage has dependencies."""
        return len(self.dependencies) > 0

    def to_execution_config(self) -> Dict[str, Any]:
        """
        Export configuration for stage execution.

        Returns:
            Dictionary with execution-ready configuration
        """
        return {
            "stage_id": self.stage_id,
            "name": self.name,
            "stage_type": self.stage_type.value,
            "config": self.config,
            "dependencies": self.dependencies,
        }


# =============================================================================
# PIPELINE OBJECT
# =============================================================================


@register_object_type
class PipelineObject(OntologyObject):
    """
    OntologyObject representing a complete data pipeline definition.

    A Pipeline is a collection of stages that define a data transformation
    workflow. Pipelines can be scheduled, validated, and executed through
    the ODA Action system.

    Attributes:
        pipeline_id: Unique pipeline identifier (user-defined)
        name: Human-readable pipeline name
        description: Pipeline description
        stages: Embedded list of stage definitions
        schedule: Optional cron expression for scheduling
        pipeline_status: Current pipeline lifecycle status
        owner: ID of the pipeline owner
        last_run_at: Timestamp of last execution
        last_run_status: Status of last run
        next_run_at: Scheduled next execution time
        pipeline_version: Version number for tracking changes
        tags: Tags for categorization
        metadata: Additional metadata
    """

    pipeline_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique pipeline identifier"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable pipeline name"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Pipeline description"
    )
    stages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Embedded list of stage definitions"
    )
    schedule: Optional[str] = Field(
        default=None,
        description="Cron expression for scheduling"
    )
    pipeline_status: PipelineObjectStatus = Field(
        default=PipelineObjectStatus.DRAFT,
        description="Current pipeline lifecycle status"
    )
    owner: str = Field(
        ...,
        description="ID of the pipeline owner"
    )
    last_run_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last execution"
    )
    last_run_status: Optional[PipelineRunStatus] = Field(
        default=None,
        description="Status of last run"
    )
    next_run_at: Optional[datetime] = Field(
        default=None,
        description="Scheduled next execution time"
    )
    pipeline_version: int = Field(
        default=1,
        ge=1,
        description="Pipeline version number"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: Optional[str]) -> Optional[str]:
        """Basic cron expression validation."""
        if v is None:
            return None
        parts = v.strip().split()
        if len(parts) not in (5, 6):
            raise ValueError(
                f"Invalid cron expression: expected 5 or 6 parts, got {len(parts)}"
            )
        return v.strip()

    @property
    def is_scheduled(self) -> bool:
        """Check if pipeline has a schedule."""
        return self.schedule is not None

    @property
    def is_active(self) -> bool:
        """Check if pipeline is active."""
        return self.pipeline_status == PipelineObjectStatus.ACTIVE

    @property
    def stage_count(self) -> int:
        """Get number of stages."""
        return len(self.stages)

    def get_stage(self, stage_id: str) -> Optional[Dict[str, Any]]:
        """Get a stage by ID."""
        for stage in self.stages:
            if stage.get("stage_id") == stage_id:
                return stage
        return None

    def activate(self) -> None:
        """Activate the pipeline."""
        if self.pipeline_status == PipelineObjectStatus.ARCHIVED:
            raise ValueError("Cannot activate an archived pipeline")
        self.pipeline_status = PipelineObjectStatus.ACTIVE
        self.touch()

    def pause(self) -> None:
        """Pause the pipeline."""
        if self.pipeline_status != PipelineObjectStatus.ACTIVE:
            raise ValueError("Can only pause an active pipeline")
        self.pipeline_status = PipelineObjectStatus.PAUSED
        self.touch()

    def archive(self, archived_by: Optional[str] = None) -> None:
        """Archive the pipeline."""
        self.pipeline_status = PipelineObjectStatus.ARCHIVED
        self.touch(updated_by=archived_by)

    def record_run(
        self,
        status: PipelineRunStatus,
        run_at: Optional[datetime] = None
    ) -> None:
        """Record a pipeline run."""
        self.last_run_at = run_at or utc_now()
        self.last_run_status = status
        self.touch()

    def increment_version(self) -> None:
        """Increment the pipeline version."""
        self.pipeline_version += 1
        self.touch()

    def to_execution_manifest(self) -> Dict[str, Any]:
        """
        Export manifest for pipeline execution.

        Returns:
            Dictionary with execution-ready pipeline definition
        """
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "version": self.pipeline_version,
            "stages": self.stages,
            "schedule": self.schedule,
            "owner": self.owner,
            "tags": self.tags,
        }


# =============================================================================
# PIPELINE RUN OBJECT
# =============================================================================


@register_object_type
class PipelineRunObject(OntologyObject):
    """
    OntologyObject representing a single execution of a pipeline.

    Tracks the status and results of each stage during execution,
    providing full audit trail and debugging information.

    Attributes:
        run_id: Unique identifier for this run
        pipeline_id: ID of the pipeline being executed
        pipeline_object_id: ID of the PipelineObject (ontology ID)
        run_status: Current run status
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
        stage_results: Results from each stage
        error: Error message if failed
        error_stage_id: ID of the stage that failed
        triggered_by: How the run was triggered
        parameters: Runtime parameters for this run
        metrics: Execution metrics (timing, row counts, etc.)
    """

    run_id: str = Field(
        ...,
        description="Unique identifier for this run"
    )
    pipeline_id: str = Field(
        ...,
        description="Pipeline identifier (user-defined ID)"
    )
    pipeline_object_id: str = Field(
        ...,
        description="ID of the PipelineObject in ontology"
    )
    run_status: PipelineRunStatus = Field(
        default=PipelineRunStatus.PENDING,
        description="Current run status"
    )
    started_at: datetime = Field(
        default_factory=utc_now,
        description="Execution start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Execution completion timestamp"
    )
    stage_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from each stage (stage_id -> result)"
    )
    error: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Error message if run failed"
    )
    error_stage_id: Optional[str] = Field(
        default=None,
        description="ID of the stage that failed"
    )
    triggered_by: str = Field(
        default="manual",
        description="How the run was triggered (manual, schedule, api)"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime parameters for this run"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics (timing, row counts, etc.)"
    )

    def mark_running(self) -> None:
        """Mark the run as started."""
        self.run_status = PipelineRunStatus.RUNNING
        self.started_at = utc_now()
        self.touch()

    def mark_completed(self) -> None:
        """Mark the run as successfully completed."""
        self.run_status = PipelineRunStatus.COMPLETED
        self.completed_at = utc_now()
        self.touch()

    def mark_failed(self, error: str, stage_id: Optional[str] = None) -> None:
        """Mark the run as failed."""
        self.run_status = PipelineRunStatus.FAILED
        self.completed_at = utc_now()
        self.error = error
        self.error_stage_id = stage_id
        self.touch()

    def mark_cancelled(self) -> None:
        """Mark the run as cancelled."""
        self.run_status = PipelineRunStatus.CANCELLED
        self.completed_at = utc_now()
        self.touch()

    def mark_timeout(self) -> None:
        """Mark the run as timed out."""
        self.run_status = PipelineRunStatus.TIMEOUT
        self.completed_at = utc_now()
        self.error = "Pipeline execution timed out"
        self.touch()

    def set_stage_result(
        self,
        stage_id: str,
        result: Any,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record the result of a stage execution."""
        self.stage_results[stage_id] = {
            "result": result,
            "completed_at": utc_now().isoformat(),
            "metrics": metrics or {},
        }
        self.touch()

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate run duration in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def is_terminal(self) -> bool:
        """Check if run is in a terminal state."""
        return self.run_status in (
            PipelineRunStatus.COMPLETED,
            PipelineRunStatus.FAILED,
            PipelineRunStatus.CANCELLED,
            PipelineRunStatus.TIMEOUT,
        )

    @property
    def is_success(self) -> bool:
        """Check if run completed successfully."""
        return self.run_status == PipelineRunStatus.COMPLETED

    def to_summary(self) -> Dict[str, Any]:
        """
        Export run summary for reporting.

        Returns:
            Dictionary with run summary
        """
        return {
            "run_id": self.run_id,
            "pipeline_id": self.pipeline_id,
            "status": self.run_status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "triggered_by": self.triggered_by,
            "error": self.error,
            "error_stage_id": self.error_stage_id,
            "stage_count": len(self.stage_results),
        }


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "PipelineObjectStatus",
    "PipelineRunStatus",
    "StageTypeEnum",
    # ObjectTypes
    "PipelineStageObject",
    "PipelineObject",
    "PipelineRunObject",
]
