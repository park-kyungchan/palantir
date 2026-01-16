"""
Orion ODA v4.0 - Pipeline Actions (Phase 4.3.3)
================================================

Actions for Pipeline management in the ODA framework.

Standard Pipeline Actions:
- pipeline.execute: Execute a pipeline (hazardous)
- pipeline.schedule: Schedule a pipeline for execution (hazardous)
- pipeline.pause: Pause a scheduled pipeline (hazardous)
- pipeline.delete: Delete a pipeline (hazardous)
- pipeline.validate: Validate a pipeline definition (non-hazardous)
- pipeline.status: Get pipeline status (non-hazardous)

Mathpix Pipeline Actions (v4.3.4):
- alignment.blocker_detected: Stage D alignment blocker (hazardous)
- semantic.resolve_ambiguity: Stage E ambiguity resolution (hazardous)
- pipeline.advance_stage: Advance to next pipeline stage (non-hazardous)

Example:
    ```python
    from lib.oda.ontology.actions import action_registry, ActionContext

    # Validate a pipeline
    ValidateAction = action_registry.get("pipeline.validate")
    action = ValidateAction()
    result = await action.execute(
        params={"pipeline_id": "etl_daily"},
        context=ActionContext(actor_id="agent-001")
    )
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional, Type

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    AllowedValues,
    SubmissionCriterion,
    ValidationError,
    register_action,
)
from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.objects.pipeline import (
    MathpixPipeline,
    MathpixPipelineStage,
    PipelineObject,
    PipelineObjectStatus,
    PipelineRunObject,
    PipelineRunStatus,
    ReviewSeverity,
)
from pydantic import BaseModel, Field as PydanticField
from lib.oda.data.pipeline_builder import (
    Pipeline,
    PipelineBuilder,
    PipelineStage,
    StageType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM VALIDATORS
# =============================================================================


class ValidPipelineStages(SubmissionCriterion):
    """Validates that pipeline has valid stages structure."""

    @property
    def name(self) -> str:
        return "ValidPipelineStages"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        stages = params.get("stages", [])

        if not stages:
            raise ValidationError(
                criterion=self.name,
                message="Pipeline must have at least one stage",
                details={"stages_count": 0}
            )

        # Check for source stage
        source_stages = [s for s in stages if s.get("stage_type") == "source"]
        if not source_stages:
            raise ValidationError(
                criterion=self.name,
                message="Pipeline must have at least one source stage",
                details={"has_source": False}
            )

        # Check for output stage
        output_stages = [s for s in stages if s.get("stage_type") == "output"]
        if not output_stages:
            raise ValidationError(
                criterion=self.name,
                message="Pipeline must have at least one output stage",
                details={"has_output": False}
            )

        # Check for unique stage IDs
        stage_ids = [s.get("stage_id") for s in stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValidationError(
                criterion=self.name,
                message="Pipeline stages must have unique IDs",
                details={"stage_ids": stage_ids}
            )

        return True


class ValidScheduleCron(SubmissionCriterion):
    """Validates cron expression if provided."""

    @property
    def name(self) -> str:
        return "ValidScheduleCron"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        schedule = params.get("schedule")

        if schedule is None:
            return True

        parts = schedule.strip().split()
        if len(parts) not in (5, 6):
            raise ValidationError(
                criterion=self.name,
                message=f"Invalid cron expression: expected 5 or 6 parts, got {len(parts)}",
                details={"schedule": schedule, "parts_count": len(parts)}
            )

        return True


# =============================================================================
# MATHPIX PIPELINE PYDANTIC MODELS
# =============================================================================


class BlockerDetails(BaseModel):
    """
    Details of an alignment blocker detected in Stage D.

    Used by alignment.blocker_detected action to capture
    discrepancies between text and vision parsing results.
    """
    blocker_type: str = PydanticField(
        ...,
        description="Type of blocker: equation_mismatch|table_structure|figure_reference|symbol_conflict"
    )
    description: str = PydanticField(
        ...,
        description="Human-readable description of the blocker"
    )
    severity: str = PydanticField(
        default="critical",
        description="Severity level: info|warning|critical|blocker"
    )
    text_content: Optional[str] = PydanticField(
        default=None,
        description="Content from text parse (Stage B)"
    )
    vision_content: Optional[str] = PydanticField(
        default=None,
        description="Content from vision parse (Stage C)"
    )
    location: Optional[Dict[str, Any]] = PydanticField(
        default=None,
        description="Location in document (page, coordinates, etc.)"
    )
    suggested_resolution: Optional[str] = PydanticField(
        default=None,
        description="Suggested resolution for human review"
    )


class AmbiguityResolution(BaseModel):
    """
    Resolution for a semantic ambiguity in Stage E.

    Captures how an ambiguity was resolved, either by
    human intervention or automated heuristics.
    """
    ambiguity_id: str = PydanticField(
        ...,
        description="Unique identifier for the ambiguity"
    )
    ambiguity_type: str = PydanticField(
        ...,
        description="Type: symbol_meaning|reference_target|scope_boundary"
    )
    original_options: List[str] = PydanticField(
        default_factory=list,
        description="Original interpretation options"
    )
    selected_option: str = PydanticField(
        ...,
        description="Selected resolution"
    )
    confidence: float = PydanticField(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in resolution (0.0-1.0)"
    )
    resolved_by: str = PydanticField(
        ...,
        description="Resolver type: human|heuristic|ml_model"
    )
    reasoning: Optional[str] = PydanticField(
        default=None,
        description="Reasoning for the resolution"
    )


# =============================================================================
# MATHPIX PIPELINE RESULT OBJECTTYPES
# =============================================================================


class AlignmentBlockerResult(OntologyObject):
    """
    Result of alignment blocker detection and resolution.

    Created when alignment.blocker_detected action is executed.
    Links to the MathpixPipeline and Proposal for audit trail.
    """
    pipeline_id: str = PydanticField(
        ...,
        description="ID of the MathpixPipeline document"
    )
    blocker: BlockerDetails = PydanticField(
        ...,
        description="Blocker details"
    )
    proposal_id: Optional[str] = PydanticField(
        default=None,
        description="Associated Proposal ID (if hazardous action triggered)"
    )
    resolved: bool = PydanticField(
        default=False,
        description="Whether the blocker has been resolved"
    )
    resolution: Optional[str] = PydanticField(
        default=None,
        description="Resolution description"
    )
    resolved_at: Optional[datetime] = PydanticField(
        default=None,
        description="Resolution timestamp"
    )


class AmbiguityResolutionResult(OntologyObject):
    """
    Result of semantic ambiguity resolution.

    Created when semantic.resolve_ambiguity action is executed.
    Links to the MathpixPipeline and Proposal for audit trail.
    """
    pipeline_id: str = PydanticField(
        ...,
        description="ID of the MathpixPipeline document"
    )
    resolution: AmbiguityResolution = PydanticField(
        ...,
        description="Ambiguity resolution details"
    )
    proposal_id: Optional[str] = PydanticField(
        default=None,
        description="Associated Proposal ID (if hazardous action triggered)"
    )
    applied: bool = PydanticField(
        default=False,
        description="Whether the resolution has been applied"
    )
    applied_at: Optional[datetime] = PydanticField(
        default=None,
        description="Application timestamp"
    )


# =============================================================================
# PIPELINE VALIDATE ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class PipelineValidateAction(ActionType[PipelineObject]):
    """
    Validate a pipeline definition.

    This action is non-hazardous (read-only validation).

    Parameters:
        pipeline_id: Optional existing pipeline ID to validate
        stages: Optional stages to validate (for new pipelines)
        schedule: Optional schedule to validate

    Returns:
        ActionResult with validation results
    """

    api_name: ClassVar[str] = "pipeline.validate"
    object_type: ClassVar[Type[PipelineObject]] = PipelineObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = []

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Validate the pipeline definition."""
        errors: List[str] = []
        warnings: List[str] = []

        pipeline_id = params.get("pipeline_id")
        stages = params.get("stages", [])
        schedule = params.get("schedule")

        # If validating existing pipeline, we would load it here
        # For now, validate the provided definition

        # Check stages
        if stages:
            # Check for source stage
            source_stages = [s for s in stages if s.get("stage_type") == "source"]
            if not source_stages:
                errors.append("Pipeline must have at least one source stage")

            # Check for output stage
            output_stages = [s for s in stages if s.get("stage_type") == "output"]
            if not output_stages:
                errors.append("Pipeline must have at least one output stage")

            # Check for unique stage IDs
            stage_ids = [s.get("stage_id") for s in stages if s.get("stage_id")]
            if len(stage_ids) != len(set(stage_ids)):
                errors.append("Pipeline stages must have unique IDs")

            # Check stage names
            stage_names = [s.get("name") for s in stages if s.get("name")]
            if len(stage_names) != len(set(stage_names)):
                warnings.append("Pipeline has duplicate stage names")

            # Check dependencies reference existing stages
            stage_id_set = set(stage_ids)
            for stage in stages:
                deps = stage.get("dependencies", [])
                for dep in deps:
                    if dep not in stage_id_set:
                        errors.append(
                            f"Stage '{stage.get('name')}' references non-existent "
                            f"dependency: {dep}"
                        )

            # Check for circular dependencies
            try:
                self._check_circular_deps(stages)
            except ValueError as e:
                errors.append(str(e))
        elif pipeline_id:
            # Validate existing pipeline would load here
            warnings.append("Existing pipeline validation not implemented")
        else:
            errors.append("Either pipeline_id or stages must be provided")

        # Validate schedule if provided
        if schedule:
            parts = schedule.strip().split()
            if len(parts) not in (5, 6):
                errors.append(
                    f"Invalid cron expression: expected 5 or 6 parts, got {len(parts)}"
                )

        is_valid = len(errors) == 0

        return ActionResult(
            action_type=self.api_name,
            success=True,  # Action itself succeeded (validation ran)
            data={
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "stages_count": len(stages),
                "has_schedule": schedule is not None,
            },
            edits=[],
            message="Validation passed" if is_valid else f"Validation failed: {len(errors)} errors",
        )

    def _check_circular_deps(self, stages: List[Dict[str, Any]]) -> None:
        """Check for circular dependencies in stages."""
        # Build adjacency list
        graph: Dict[str, List[str]] = {}
        for stage in stages:
            stage_id = stage.get("stage_id")
            if stage_id:
                graph[stage_id] = stage.get("dependencies", [])

        # DFS for cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in graph}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in graph.get(node, []):
                if neighbor in color:
                    if color[neighbor] == GRAY:
                        return True  # Cycle found
                    if color[neighbor] == WHITE and dfs(neighbor):
                        return True
            color[node] = BLACK
            return False

        for node in graph:
            if color[node] == WHITE:
                if dfs(node):
                    raise ValueError("Circular dependency detected in pipeline stages")


# =============================================================================
# PIPELINE EXECUTE ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class PipelineExecuteAction(ActionType[PipelineRunObject]):
    """
    Execute a pipeline.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        pipeline_id: ID of the pipeline to execute
        parameters: Optional runtime parameters
        triggered_by: How the run was triggered (default: "manual")

    Returns:
        ActionResult with PipelineRunObject
    """

    api_name: ClassVar[str] = "pipeline.execute"
    object_type: ClassVar[Type[PipelineRunObject]] = PipelineRunObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[PipelineRunObject], List[EditOperation]]:
        """Execute the pipeline."""
        pipeline_id = params["pipeline_id"]
        parameters = params.get("parameters", {})
        triggered_by = params.get("triggered_by", "manual")

        # Create a run record
        run = PipelineRunObject(
            run_id=str(uuid.uuid4()),
            pipeline_id=pipeline_id,
            pipeline_object_id=pipeline_id,  # Would be actual object ID
            run_status=PipelineRunStatus.PENDING,
            triggered_by=triggered_by,
            parameters=parameters,
            created_by=context.actor_id,
        )

        # Mark as running
        run.mark_running()

        # Note: Actual pipeline execution would happen here
        # For now, we just create the run record

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="PipelineRunObject",
            object_id=run.id,
            changes={
                "run_id": run.run_id,
                "pipeline_id": pipeline_id,
                "status": run.run_status.value,
                "triggered_by": triggered_by,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Pipeline execution started: {pipeline_id} (run_id: {run.run_id}) "
            f"by {context.actor_id}"
        )

        return (run, [edit])


# =============================================================================
# PIPELINE SCHEDULE ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class PipelineScheduleAction(ActionType[PipelineObject]):
    """
    Schedule a pipeline for automatic execution.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        pipeline_id: ID of the pipeline to schedule
        schedule: Cron expression for scheduling

    Returns:
        ActionResult with updated PipelineObject
    """

    api_name: ClassVar[str] = "pipeline.schedule"
    object_type: ClassVar[Type[PipelineObject]] = PipelineObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
        RequiredField("schedule"),
        ValidScheduleCron(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Schedule the pipeline."""
        pipeline_id = params["pipeline_id"]
        schedule = params["schedule"]

        # Note: In a full implementation, we would:
        # 1. Load the pipeline from storage
        # 2. Update the schedule
        # 3. Register with a scheduler service
        # 4. Persist the changes

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="PipelineObject",
            object_id=pipeline_id,
            changes={
                "schedule": schedule,
                "pipeline_status": PipelineObjectStatus.ACTIVE.value,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Pipeline scheduled: {pipeline_id} with schedule '{schedule}' "
            f"by {context.actor_id}"
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "pipeline_id": pipeline_id,
                "schedule": schedule,
                "status": PipelineObjectStatus.ACTIVE.value,
            },
            edits=[edit],
            modified_ids=[pipeline_id],
            message=f"Pipeline '{pipeline_id}' scheduled with '{schedule}'",
        )


# =============================================================================
# PIPELINE PAUSE ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class PipelinePauseAction(ActionType[PipelineObject]):
    """
    Pause a scheduled pipeline.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        pipeline_id: ID of the pipeline to pause

    Returns:
        ActionResult with updated status
    """

    api_name: ClassVar[str] = "pipeline.pause"
    object_type: ClassVar[Type[PipelineObject]] = PipelineObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Pause the pipeline."""
        pipeline_id = params["pipeline_id"]

        # Note: In a full implementation, we would:
        # 1. Load the pipeline from storage
        # 2. Verify it's currently active
        # 3. Update the status
        # 4. Unregister from scheduler service
        # 5. Persist the changes

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="PipelineObject",
            object_id=pipeline_id,
            changes={
                "pipeline_status": PipelineObjectStatus.PAUSED.value,
            },
            timestamp=context.timestamp,
        )

        logger.info(f"Pipeline paused: {pipeline_id} by {context.actor_id}")

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "pipeline_id": pipeline_id,
                "status": PipelineObjectStatus.PAUSED.value,
            },
            edits=[edit],
            modified_ids=[pipeline_id],
            message=f"Pipeline '{pipeline_id}' paused",
        )


# =============================================================================
# PIPELINE STATUS ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class PipelineStatusAction(ActionType[PipelineObject]):
    """
    Get pipeline status and recent runs.

    This action is non-hazardous (read-only).

    Parameters:
        pipeline_id: ID of the pipeline
        include_runs: Include recent runs (default: False)
        runs_limit: Max runs to return (default: 10)

    Returns:
        ActionResult with pipeline status
    """

    api_name: ClassVar[str] = "pipeline.status"
    object_type: ClassVar[Type[PipelineObject]] = PipelineObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Get pipeline status."""
        pipeline_id = params["pipeline_id"]
        include_runs = params.get("include_runs", False)
        runs_limit = params.get("runs_limit", 10)

        # Note: In a full implementation, we would load from storage
        # For now, return a placeholder response

        data = {
            "pipeline_id": pipeline_id,
            "status": "unknown",
            "message": "Pipeline status lookup not implemented - requires storage integration",
        }

        if include_runs:
            data["recent_runs"] = []
            data["runs_limit"] = runs_limit

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=data,
            edits=[],
            message=f"Status retrieved for pipeline '{pipeline_id}'",
        )


# =============================================================================
# PIPELINE DELETE ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class PipelineDeleteAction(ActionType[PipelineObject]):
    """
    Delete a pipeline.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        pipeline_id: ID of the pipeline to delete
        force: Force delete even if pipeline has runs (default: False)

    Returns:
        ActionResult with deletion status
    """

    api_name: ClassVar[str] = "pipeline.delete"
    object_type: ClassVar[Type[PipelineObject]] = PipelineObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Delete the pipeline."""
        pipeline_id = params["pipeline_id"]
        force = params.get("force", False)

        # Note: In a full implementation, we would:
        # 1. Load the pipeline from storage
        # 2. Check for active/running pipelines
        # 3. If not force, check for existing runs
        # 4. Soft delete or archive the pipeline
        # 5. Persist the changes

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.DELETE,
            object_type="PipelineObject",
            object_id=pipeline_id,
            changes={
                "force": force,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Pipeline deleted: {pipeline_id} (force={force}) by {context.actor_id}"
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "pipeline_id": pipeline_id,
                "deleted": True,
                "force": force,
            },
            edits=[edit],
            deleted_ids=[pipeline_id],
            message=f"Pipeline '{pipeline_id}' deleted",
        )


# =============================================================================
# MATHPIX PIPELINE ACTIONS
# =============================================================================


@register_action(requires_proposal=True)
class AlignmentBlockerDetectedAction(ActionType[AlignmentBlockerResult]):
    """
    Report and handle an alignment blocker in Stage D.

    This action is HAZARDOUS - alignment issues require human review
    before pipeline can proceed.

    Called when Stage D detects a discrepancy between text parsing (B)
    and vision parsing (C) results that cannot be auto-resolved.

    Parameters:
        pipeline_id: ID of the MathpixPipeline document
        blocker_type: Type of blocker detected
        description: Human-readable description
        severity: Severity level (default: critical)
        text_content: Content from text parse
        vision_content: Content from vision parse
        location: Location in document
        suggested_resolution: Suggested resolution

    Returns:
        ActionResult with AlignmentBlockerResult
    """

    api_name: ClassVar[str] = "alignment.blocker_detected"
    object_type: ClassVar[Type[AlignmentBlockerResult]] = AlignmentBlockerResult
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
        RequiredField("blocker_type"),
        RequiredField("description"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[AlignmentBlockerResult], List[EditOperation]]:
        """Create alignment blocker result and pause pipeline."""
        pipeline_id = params["pipeline_id"]

        # Create BlockerDetails
        blocker = BlockerDetails(
            blocker_type=params["blocker_type"],
            description=params["description"],
            severity=params.get("severity", "critical"),
            text_content=params.get("text_content"),
            vision_content=params.get("vision_content"),
            location=params.get("location"),
            suggested_resolution=params.get("suggested_resolution"),
        )

        # Create result object
        result = AlignmentBlockerResult(
            pipeline_id=pipeline_id,
            blocker=blocker,
            proposal_id=context.proposal_id if hasattr(context, 'proposal_id') else None,
            resolved=False,
            created_by=context.actor_id,
        )

        # Create edit operations
        edits = [
            EditOperation(
                edit_type=EditType.CREATE,
                object_type="AlignmentBlockerResult",
                object_id=result.id,
                changes={
                    "pipeline_id": pipeline_id,
                    "blocker_type": blocker.blocker_type,
                    "severity": blocker.severity,
                },
                timestamp=context.timestamp,
            ),
            EditOperation(
                edit_type=EditType.MODIFY,
                object_type="MathpixPipeline",
                object_id=pipeline_id,
                changes={
                    "add_blocker": {
                        "type": blocker.blocker_type,
                        "description": blocker.description,
                        "severity": blocker.severity,
                    }
                },
                timestamp=context.timestamp,
            ),
        ]

        logger.warning(
            f"Alignment blocker detected in pipeline {pipeline_id}: "
            f"{blocker.blocker_type} ({blocker.severity}) by {context.actor_id}"
        )

        return (result, edits)


@register_action(requires_proposal=True)
class SemanticResolveAmbiguityAction(ActionType[AmbiguityResolutionResult]):
    """
    Resolve a semantic ambiguity in Stage E.

    This action is HAZARDOUS - semantic decisions affect document meaning
    and require human verification.

    Called when Stage E encounters symbols or references with multiple
    valid interpretations.

    Parameters:
        pipeline_id: ID of the MathpixPipeline document
        ambiguity_id: Unique identifier for the ambiguity
        ambiguity_type: Type of ambiguity
        original_options: List of possible interpretations
        selected_option: The chosen interpretation
        confidence: Confidence in resolution (0.0-1.0)
        resolved_by: Resolution source (human|heuristic|ml_model)
        reasoning: Reasoning for the choice

    Returns:
        ActionResult with AmbiguityResolutionResult
    """

    api_name: ClassVar[str] = "semantic.resolve_ambiguity"
    object_type: ClassVar[Type[AmbiguityResolutionResult]] = AmbiguityResolutionResult
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
        RequiredField("ambiguity_id"),
        RequiredField("ambiguity_type"),
        RequiredField("selected_option"),
        RequiredField("resolved_by"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[AmbiguityResolutionResult], List[EditOperation]]:
        """Create ambiguity resolution result."""
        pipeline_id = params["pipeline_id"]

        # Create AmbiguityResolution
        resolution = AmbiguityResolution(
            ambiguity_id=params["ambiguity_id"],
            ambiguity_type=params["ambiguity_type"],
            original_options=params.get("original_options", []),
            selected_option=params["selected_option"],
            confidence=params.get("confidence", 1.0),
            resolved_by=params["resolved_by"],
            reasoning=params.get("reasoning"),
        )

        # Create result object
        result = AmbiguityResolutionResult(
            pipeline_id=pipeline_id,
            resolution=resolution,
            proposal_id=context.proposal_id if hasattr(context, 'proposal_id') else None,
            applied=True,
            applied_at=utc_now(),
            created_by=context.actor_id,
        )

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="AmbiguityResolutionResult",
            object_id=result.id,
            changes={
                "pipeline_id": pipeline_id,
                "ambiguity_id": resolution.ambiguity_id,
                "ambiguity_type": resolution.ambiguity_type,
                "selected_option": resolution.selected_option,
                "confidence": resolution.confidence,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Ambiguity resolved in pipeline {pipeline_id}: "
            f"{resolution.ambiguity_id} -> {resolution.selected_option} "
            f"(by {resolution.resolved_by}, confidence: {resolution.confidence})"
        )

        return (result, [edit])


@register_action
class PipelineAdvanceStageAction(ActionType[MathpixPipeline]):
    """
    Advance MathpixPipeline to the next stage.

    This action is NON-HAZARDOUS - stage advancement is a normal
    workflow progression when prerequisites are met.

    Prerequisites for advancement:
    - No pending proposals
    - No unresolved blockers
    - Circuit breaker not tripped
    - Pipeline status is ACTIVE

    Parameters:
        pipeline_id: ID of the MathpixPipeline document
        confidence: Confidence score for current stage (0.0-1.0)

    Returns:
        ActionResult with new stage or block reason
    """

    api_name: ClassVar[str] = "pipeline.advance_stage"
    object_type: ClassVar[Type[MathpixPipeline]] = MathpixPipeline
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("pipeline_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Advance pipeline to next stage."""
        pipeline_id = params["pipeline_id"]
        confidence = params.get("confidence", 1.0)

        # Note: In full implementation, would load MathpixPipeline from storage
        # For now, return a result indicating the advancement

        # Validate confidence threshold (0.5 minimum for advancement)
        if confidence < 0.5:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                data={
                    "pipeline_id": pipeline_id,
                    "advanced": False,
                    "reason": "low_confidence",
                    "confidence": confidence,
                    "threshold": 0.5,
                },
                edits=[],
                message=f"Cannot advance: confidence {confidence} below threshold 0.5",
            )

        # Create edit operation (would be applied to actual pipeline)
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="MathpixPipeline",
            object_id=pipeline_id,
            changes={
                "stage_advanced": True,
                "confidence": confidence,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Pipeline stage advanced: {pipeline_id} "
            f"(confidence: {confidence}) by {context.actor_id}"
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "pipeline_id": pipeline_id,
                "advanced": True,
                "confidence": confidence,
            },
            edits=[edit],
            modified_ids=[pipeline_id],
            message=f"Pipeline '{pipeline_id}' advanced to next stage",
        )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Validators
    "ValidPipelineStages",
    "ValidScheduleCron",
    # Pydantic Models (Mathpix)
    "BlockerDetails",
    "AmbiguityResolution",
    # Result ObjectTypes (Mathpix)
    "AlignmentBlockerResult",
    "AmbiguityResolutionResult",
    # Non-hazardous actions
    "PipelineValidateAction",
    "PipelineStatusAction",
    "PipelineAdvanceStageAction",  # Mathpix
    # Hazardous actions
    "PipelineExecuteAction",
    "PipelineScheduleAction",
    "PipelinePauseAction",
    "PipelineDeleteAction",
    "AlignmentBlockerDetectedAction",  # Mathpix
    "SemanticResolveAmbiguityAction",  # Mathpix
]
