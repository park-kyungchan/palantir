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


class MathpixPipelineStage(str, Enum):
    """
    8-stage Mathpix document processing pipeline.

    Each stage represents a distinct processing phase:
    - A-C: Extraction phases (text, vision)
    - D: Critical alignment phase (blocker detection)
    - E-F: Semantic processing
    - G-H: Human review and export
    """
    A_INGESTION = "A"
    B_TEXTPARSE = "B"
    C_VISIONPARSE = "C"
    D_ALIGNMENT = "D"
    E_SEMANTICGRAPH = "E"
    F_REGENERATION = "F"
    G_HUMANREVIEW = "G"
    H_EXPORT = "H"


class ReviewSeverity(str, Enum):
    """
    Severity levels for human review items.

    Used by Stage D alignment blocker detection and Stage G review.
    """
    INFO = "info"           # Informational, no action required
    WARNING = "warning"     # May need attention
    CRITICAL = "critical"   # Blocks pipeline progression
    BLOCKER = "blocker"     # Requires immediate human intervention


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
# MATHPIX PIPELINE OBJECT
# =============================================================================


@register_object_type
class MathpixPipeline(OntologyObject):
    """
    OntologyObject for Mathpix document processing pipeline.

    Implements 8-stage document processing with ODA governance:
    - Stages A-C: Extraction (text, vision parsing)
    - Stage D: Alignment with blocker detection (triggers Proposals)
    - Stage E-F: Semantic processing
    - Stage G: Human review
    - Stage H: Export

    Circuit Breaker Pattern:
        auto_trigger_count tracks automatic proposal generations.
        If count exceeds MAX_AUTO_TRIGGERS (5), pipeline halts to prevent
        infinite proposal loops.

    Attributes:
        document_id: Unique document identifier
        current_stage: Current processing stage (A-H)
        stage_confidences: Confidence scores per stage
        pending_proposals: IDs of pending Proposal objects
        auto_trigger_count: Circuit breaker counter for auto-proposals
        blockers: List of detected alignment blockers
        ambiguities: List of detected semantic ambiguities
        source_path: Original document path
        output_path: Generated output path
    """

    MAX_AUTO_TRIGGERS: int = 5  # Circuit breaker threshold

    document_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique document identifier"
    )
    current_stage: MathpixPipelineStage = Field(
        default=MathpixPipelineStage.A_INGESTION,
        description="Current processing stage"
    )
    stage_confidences: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores per stage (stage_id -> 0.0-1.0)"
    )
    pending_proposals: List[str] = Field(
        default_factory=list,
        description="IDs of pending Proposal objects"
    )
    auto_trigger_count: int = Field(
        default=0,
        ge=0,
        description="Circuit breaker counter for auto-proposals"
    )
    blockers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detected alignment blockers"
    )
    ambiguities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detected semantic ambiguities"
    )
    source_path: Optional[str] = Field(
        default=None,
        description="Original document path"
    )
    output_path: Optional[str] = Field(
        default=None,
        description="Generated output path"
    )
    pipeline_status: PipelineObjectStatus = Field(
        default=PipelineObjectStatus.DRAFT,
        description="Pipeline lifecycle status"
    )

    @property
    def is_circuit_breaker_tripped(self) -> bool:
        """Check if circuit breaker is tripped (too many auto-proposals)."""
        return self.auto_trigger_count >= self.MAX_AUTO_TRIGGERS

    @property
    def is_blocked(self) -> bool:
        """Check if pipeline is blocked by pending proposals or blockers."""
        return len(self.pending_proposals) > 0 or len(self.blockers) > 0

    @property
    def can_advance(self) -> bool:
        """Check if pipeline can advance to next stage."""
        return (
            not self.is_blocked
            and not self.is_circuit_breaker_tripped
            and self.pipeline_status == PipelineObjectStatus.ACTIVE
        )

    def increment_auto_trigger(self) -> bool:
        """
        Increment auto-trigger counter and check circuit breaker.

        Returns:
            True if still under threshold, False if circuit breaker tripped
        """
        self.auto_trigger_count += 1
        self.touch()
        return not self.is_circuit_breaker_tripped

    def reset_auto_trigger(self) -> None:
        """Reset auto-trigger counter (after human intervention)."""
        self.auto_trigger_count = 0
        self.touch()

    def add_blocker(
        self,
        blocker_type: str,
        description: str,
        severity: str = "critical",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an alignment blocker."""
        self.blockers.append({
            "type": blocker_type,
            "description": description,
            "severity": severity,
            "detected_at": utc_now().isoformat(),
            "metadata": metadata or {},
        })
        self.touch()

    def resolve_blocker(self, blocker_index: int, resolution: str) -> None:
        """Mark a blocker as resolved."""
        if 0 <= blocker_index < len(self.blockers):
            self.blockers[blocker_index]["resolved"] = True
            self.blockers[blocker_index]["resolution"] = resolution
            self.blockers[blocker_index]["resolved_at"] = utc_now().isoformat()
            self.touch()

    def set_stage_confidence(self, stage: MathpixPipelineStage, confidence: float) -> None:
        """Set confidence score for a stage."""
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
        self.stage_confidences[stage.value] = confidence
        self.touch()

    def advance_stage(self) -> Optional[MathpixPipelineStage]:
        """
        Advance to next stage if allowed.

        Returns:
            New stage if advanced, None if blocked or at final stage
        """
        if not self.can_advance:
            return None

        stage_order = list(MathpixPipelineStage)
        current_idx = stage_order.index(self.current_stage)

        if current_idx >= len(stage_order) - 1:
            return None  # Already at final stage

        self.current_stage = stage_order[current_idx + 1]
        self.touch()
        return self.current_stage

    def add_pending_proposal(self, proposal_id: str) -> None:
        """Add a pending proposal ID."""
        if proposal_id not in self.pending_proposals:
            self.pending_proposals.append(proposal_id)
            self.touch()

    def remove_pending_proposal(self, proposal_id: str) -> None:
        """Remove a resolved proposal ID."""
        if proposal_id in self.pending_proposals:
            self.pending_proposals.remove(proposal_id)
            self.touch()

    def to_status_summary(self) -> Dict[str, Any]:
        """Export current pipeline status for monitoring."""
        return {
            "document_id": self.document_id,
            "current_stage": self.current_stage.value,
            "stage_confidences": self.stage_confidences,
            "pending_proposals_count": len(self.pending_proposals),
            "blockers_count": len(self.blockers),
            "auto_trigger_count": self.auto_trigger_count,
            "circuit_breaker_tripped": self.is_circuit_breaker_tripped,
            "can_advance": self.can_advance,
            "pipeline_status": self.pipeline_status.value,
        }


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "PipelineObjectStatus",
    "PipelineRunStatus",
    "StageTypeEnum",
    "MathpixPipelineStage",
    "ReviewSeverity",
    # ObjectTypes
    "PipelineStageObject",
    "PipelineObject",
    "PipelineRunObject",
    "MathpixPipeline",
]
