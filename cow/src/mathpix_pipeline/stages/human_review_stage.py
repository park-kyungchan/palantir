"""
Stage G: Human Review Stage.

Wraps human review system components (PriorityScorer, ReviewQueueManager)
as a BaseStage for consistent pipeline integration.

Supports dynamic threshold system (v2.0.0) for priority scoring.

This is a COMPOSITE INPUT stage - it takes PipelineResult and optional
threshold context as input.

Module Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from ..schemas.common import (
    MathpixBaseModel,
    PipelineStage,
    ReviewSeverity,
    Provenance,
)
from ..schemas.pipeline import PipelineResult
from ..schemas.threshold import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    compute_effective_threshold,
)
from ..human_review.priority_scorer import (
    PriorityScorer,
    PriorityScorerConfig,
)
from ..human_review.queue_manager import (
    ReviewQueueManager,
    QueueConfig,
    QueueStats,
)
from ..human_review.models.task import (
    ReviewTask,
    TaskContext,
    TaskMetrics,
    ReviewStatus,
    ReviewPriority,
)
from .base import (
    BaseStage,
    ValidationResult,
    StageMetrics,
    StageExecutionError,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Review Summary (Output Type)
# =============================================================================

class ReviewSummary(MathpixBaseModel):
    """Summary of human review stage processing.

    Contains statistics about tasks created, queue state,
    and threshold information used.

    Attributes:
        image_id: Source image identifier
        tasks_created: Number of review tasks created
        tasks_by_priority: Breakdown by priority level
        tasks_by_severity: Breakdown by severity level
        queue_stats: Current queue statistics
        threshold_info: Information about thresholds applied
        provenance: Audit trail information
    """
    image_id: str
    tasks_created: int = 0
    tasks_by_priority: Dict[str, int] = field(default_factory=dict)
    tasks_by_severity: Dict[str, int] = field(default_factory=dict)
    task_ids: List[str] = field(default_factory=list)
    queue_stats: Optional[QueueStats] = None
    threshold_info: Dict[str, Any] = field(default_factory=dict)
    dynamic_thresholds_enabled: bool = False
    processing_time_ms: float = 0.0
    provenance: Provenance = field(default_factory=lambda: Provenance(
        stage=PipelineStage.HUMAN_REVIEW,
        model="human-review-stage-v1",
    ))

    @property
    def has_tasks(self) -> bool:
        """Check if any tasks were created."""
        return self.tasks_created > 0

    @property
    def critical_count(self) -> int:
        """Get count of critical priority tasks."""
        return self.tasks_by_priority.get(ReviewPriority.CRITICAL.value, 0)

    @property
    def high_count(self) -> int:
        """Get count of high priority tasks."""
        return self.tasks_by_priority.get(ReviewPriority.HIGH.value, 0)


# =============================================================================
# Composite Input
# =============================================================================

@dataclass
class HumanReviewInput:
    """Composite input for Stage G human review.

    Stage G takes the complete pipeline result and extracts
    elements that need human review based on confidence thresholds.

    Attributes:
        pipeline_result: Complete PipelineResult from previous stages
        threshold_context: Optional context for dynamic threshold computation
        feedback_stats: Optional feedback statistics for threshold adjustment
    """
    pipeline_result: PipelineResult
    threshold_context: Optional[ThresholdContext] = None
    feedback_stats: Optional[FeedbackStats] = None

    @property
    def image_id(self) -> str:
        """Get image ID from pipeline result."""
        return self.pipeline_result.image_id

    def needs_review(self) -> bool:
        """Check if pipeline result requires human review."""
        return (
            self.pipeline_result.review.review_required or
            self.pipeline_result.overall_confidence < 0.70
        )


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class HumanReviewStageConfig:
    """Configuration for Stage G human review.

    Attributes:
        threshold_config: Full threshold calibration config (v2.0.0)
        threshold_context: Default threshold context
        feedback_stats: Default feedback statistics
        enable_dynamic_thresholds: Enable dynamic threshold computation
        scorer_config: PriorityScorer configuration
        queue_config: ReviewQueueManager configuration
        default_queue_name: Default queue for tasks
        min_confidence_for_auto_approve: Confidence above which auto-approval is considered
        max_tasks_per_image: Maximum tasks to create per image
    """
    threshold_config: Optional[ThresholdConfig] = None
    threshold_context: Optional[ThresholdContext] = None
    feedback_stats: Optional[FeedbackStats] = None
    enable_dynamic_thresholds: bool = True
    scorer_config: Optional[PriorityScorerConfig] = None
    queue_config: Optional[QueueConfig] = None
    default_queue_name: str = "default"
    min_confidence_for_auto_approve: float = 0.90
    max_tasks_per_image: int = 50

    def get_scorer_config(self) -> PriorityScorerConfig:
        """Get scorer config, creating one with dynamic thresholds if enabled."""
        if self.scorer_config:
            # Update with dynamic threshold config if enabled
            if self.enable_dynamic_thresholds and self.threshold_config:
                self.scorer_config.threshold_config = self.threshold_config
                self.scorer_config.threshold_context = self.threshold_context
                self.scorer_config.feedback_stats = self.feedback_stats
            return self.scorer_config

        # Create new config with dynamic thresholds
        return PriorityScorerConfig(
            threshold_config=self.threshold_config if self.enable_dynamic_thresholds else None,
            threshold_context=self.threshold_context,
            feedback_stats=self.feedback_stats,
        )


# =============================================================================
# Stage Implementation
# =============================================================================

class HumanReviewStage(BaseStage[HumanReviewInput, ReviewSummary]):
    """Stage G: Human Review with dynamic thresholds.

    Processes pipeline results to identify elements requiring human review:
    1. Extract low-confidence elements from alignment, semantic graph, etc.
    2. Apply dynamic thresholds to determine review necessity
    3. Score and prioritize tasks using PriorityScorer
    4. Enqueue tasks to ReviewQueueManager

    Supports v2.0.0 dynamic threshold system:
    - Layer 1: Base thresholds per element type
    - Layer 2: Context modifiers (quality, complexity)
    - Layer 3: Feedback loop adjustments

    Example:
        config = HumanReviewStageConfig(
            threshold_context=ThresholdContext(image_quality_score=0.9),
            enable_dynamic_thresholds=True,
        )
        stage = HumanReviewStage(config=config)

        input_data = HumanReviewInput(
            pipeline_result=pipeline_result,  # from previous stages
        )

        result = await stage.run_async(input_data)
        if result.is_valid:
            review_summary = result.output
            print(f"Created {review_summary.tasks_created} review tasks")
    """

    def __init__(
        self,
        config: Optional[HumanReviewStageConfig] = None,
        scorer: Optional[PriorityScorer] = None,
        queue_manager: Optional[ReviewQueueManager] = None,
    ):
        """Initialize human review stage.

        Args:
            config: Stage configuration
            scorer: Custom PriorityScorer (created from config if not provided)
            queue_manager: Custom ReviewQueueManager (created from config if not provided)
        """
        super().__init__(config or HumanReviewStageConfig())

        # Initialize PriorityScorer
        if scorer:
            self._scorer = scorer
        else:
            self._scorer = PriorityScorer(self.config.get_scorer_config())

        # Initialize QueueManager
        if queue_manager:
            self._queue_manager = queue_manager
        else:
            self._queue_manager = ReviewQueueManager(self.config.queue_config)

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage G identifier."""
        return PipelineStage.HUMAN_REVIEW

    @property
    def config(self) -> HumanReviewStageConfig:
        """Return typed configuration."""
        return self._config

    @property
    def scorer(self) -> PriorityScorer:
        """Return the priority scorer."""
        return self._scorer

    @property
    def queue_manager(self) -> ReviewQueueManager:
        """Return the queue manager."""
        return self._queue_manager

    def validate(self, input_data: HumanReviewInput) -> ValidationResult:
        """Validate human review input.

        Validates:
        - Input is not None
        - PipelineResult is present
        - PipelineResult has valid image_id

        Args:
            input_data: HumanReviewInput to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        if input_data is None:
            result.add_error("HumanReviewInput is required")
            return result

        # Validate pipeline result
        if input_data.pipeline_result is None:
            result.add_error("PipelineResult is required")
            return result

        if not input_data.pipeline_result.image_id:
            result.add_error("PipelineResult.image_id is required")
            return result

        # Check for reviewable content
        if not input_data.needs_review():
            result.add_warning(
                f"Pipeline result has high confidence ({input_data.pipeline_result.overall_confidence:.2f}) "
                "and may not require human review"
            )

        # Validate threshold context if provided
        if input_data.threshold_context:
            if input_data.threshold_context.image_quality_score < 0.3:
                result.add_warning(
                    f"Low image quality score ({input_data.threshold_context.image_quality_score:.2f}) "
                    "may affect threshold computation"
                )

        return result

    def _get_effective_threshold(
        self,
        element_type: str,
        context: Optional[ThresholdContext] = None,
        feedback_stats: Optional[FeedbackStats] = None,
    ) -> float:
        """Get effective threshold using dynamic threshold system.

        Args:
            element_type: Type of element (e.g., 'equation', 'point', 'label')
            context: Optional threshold context
            feedback_stats: Optional feedback statistics

        Returns:
            Effective threshold value
        """
        # Use config values if not provided
        ctx = context or self.config.threshold_context or ThresholdContext()
        stats = feedback_stats or self.config.feedback_stats or FeedbackStats()

        # If dynamic thresholds disabled or no config, use static defaults
        if not self.config.enable_dynamic_thresholds or self.config.threshold_config is None:
            # Return static defaults based on element type
            static_defaults = {
                "equation": 0.55,
                "point": 0.50,
                "label": 0.45,
                "curve": 0.55,
                "matched_pair": 0.60,
            }
            return static_defaults.get(element_type.lower(), 0.55)

        # Check if element_type exists in config
        if element_type not in self.config.threshold_config.element_thresholds:
            return 0.55  # Default threshold

        return compute_effective_threshold(
            element_type=element_type,
            context=ctx,
            feedback_stats=stats,
            config=self.config.threshold_config,
        )

    def _extract_review_items(
        self,
        pipeline_result: PipelineResult,
        context: Optional[ThresholdContext] = None,
        feedback_stats: Optional[FeedbackStats] = None,
    ) -> List[Dict[str, Any]]:
        """Extract items needing review from pipeline result.

        Args:
            pipeline_result: Pipeline result to analyze
            context: Threshold context
            feedback_stats: Feedback statistics

        Returns:
            List of review item dicts with element info
        """
        review_items = []

        # Extract from alignment report
        if pipeline_result.alignment_report:
            report = pipeline_result.alignment_report
            threshold = self._get_effective_threshold("matched_pair", context, feedback_stats)

            for pair in report.matched_pairs:
                if pair.confidence.value < threshold:
                    review_items.append({
                        "element_type": "matched_pair",
                        "element_id": pair.id,
                        "element_content": f"{pair.text_element.content} -> {pair.visual_element.semantic_label}",
                        "original_confidence": pair.confidence.value,
                        "applied_threshold": threshold,
                        "review_reason": f"Below threshold ({pair.confidence.value:.2f} < {threshold:.2f})",
                        "pipeline_stage": PipelineStage.ALIGNMENT,
                        "bbox": pair.text_element.bbox,
                        "severity": ReviewSeverity.MEDIUM if pair.confidence.value > 0.4 else ReviewSeverity.HIGH,
                    })

            # Check for inconsistencies
            for inconsistency in report.inconsistencies:
                review_items.append({
                    "element_type": "inconsistency",
                    "element_id": inconsistency.id,
                    "element_content": inconsistency.description,
                    "original_confidence": 1.0 - inconsistency.severity_score,
                    "applied_threshold": 0.80,  # Inconsistency threshold
                    "review_reason": f"Inconsistency detected: {inconsistency.inconsistency_type.value}",
                    "pipeline_stage": PipelineStage.ALIGNMENT,
                    "bbox": None,
                    "severity": ReviewSeverity.HIGH if inconsistency.severity_score > 0.7 else ReviewSeverity.MEDIUM,
                })

        # Extract from semantic graph
        if pipeline_result.semantic_graph:
            graph = pipeline_result.semantic_graph

            for node in graph.nodes:
                threshold = self._get_effective_threshold(node.element_type, context, feedback_stats)
                if node.confidence.value < threshold:
                    review_items.append({
                        "element_type": node.element_type,
                        "element_id": node.id,
                        "element_content": node.semantic_label,
                        "original_confidence": node.confidence.value,
                        "applied_threshold": threshold,
                        "review_reason": f"Low confidence node ({node.confidence.value:.2f} < {threshold:.2f})",
                        "pipeline_stage": PipelineStage.SEMANTIC_GRAPH,
                        "bbox": node.bbox,
                        "severity": ReviewSeverity.MEDIUM,
                    })

        # Extract from regeneration spec
        if pipeline_result.regeneration_spec:
            regen = pipeline_result.regeneration_spec

            for output in regen.outputs:
                if output.confidence.value < self._get_effective_threshold("regeneration", context, feedback_stats):
                    review_items.append({
                        "element_type": "regeneration",
                        "element_id": output.id,
                        "element_content": output.output_type.value,
                        "original_confidence": output.confidence.value,
                        "applied_threshold": self._get_effective_threshold("regeneration", context, feedback_stats),
                        "review_reason": f"Low confidence regeneration output",
                        "pipeline_stage": PipelineStage.REGENERATION,
                        "bbox": None,
                        "severity": ReviewSeverity.MEDIUM,
                    })

        return review_items[:self.config.max_tasks_per_image]

    def _create_review_task(
        self,
        item: Dict[str, Any],
        image_id: str,
    ) -> ReviewTask:
        """Create a ReviewTask from an extracted item.

        Args:
            item: Review item dict
            image_id: Source image ID

        Returns:
            ReviewTask ready for scoring and enqueueing
        """
        task_id = f"task-{image_id[:8]}-{uuid.uuid4().hex[:8]}"

        context = TaskContext(
            image_id=image_id,
            pipeline_stage=item["pipeline_stage"],
            element_type=item["element_type"],
            element_id=item["element_id"],
            element_content=item.get("element_content"),
            element_bbox=item.get("bbox"),
            original_confidence=item["original_confidence"],
            applied_threshold=item["applied_threshold"],
            review_reason=item["review_reason"],
            related_elements=[],
        )

        task = ReviewTask(
            task_id=task_id,
            image_id=image_id,
            priority=ReviewPriority.MEDIUM,  # Will be scored later
            severity=item.get("severity", ReviewSeverity.MEDIUM),
            context=context,
        )

        return task

    async def _execute_async(
        self,
        input_data: HumanReviewInput,
        **kwargs: Any,
    ) -> ReviewSummary:
        """Execute human review processing.

        Args:
            input_data: HumanReviewInput with pipeline result
            **kwargs: Additional parameters (threshold_context, feedback_stats)

        Returns:
            ReviewSummary with processing results

        Raises:
            StageExecutionError: If processing fails
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Get threshold context from kwargs or input
            context = kwargs.pop('threshold_context', None) or input_data.threshold_context or self.config.threshold_context
            feedback_stats = kwargs.pop('feedback_stats', None) or input_data.feedback_stats or self.config.feedback_stats

            # Update scorer config if dynamic thresholds enabled
            if self.config.enable_dynamic_thresholds and self.config.threshold_config:
                self._scorer.config.threshold_context = context
                self._scorer.config.feedback_stats = feedback_stats

            # Extract items needing review
            review_items = self._extract_review_items(
                input_data.pipeline_result,
                context,
                feedback_stats,
            )

            # Initialize counters
            priority_counts: Dict[str, int] = {
                ReviewPriority.CRITICAL.value: 0,
                ReviewPriority.HIGH.value: 0,
                ReviewPriority.MEDIUM.value: 0,
                ReviewPriority.LOW.value: 0,
            }
            severity_counts: Dict[str, int] = {
                ReviewSeverity.BLOCKER.value: 0,
                ReviewSeverity.HIGH.value: 0,
                ReviewSeverity.MEDIUM.value: 0,
                ReviewSeverity.LOW.value: 0,
            }
            task_ids: List[str] = []

            # Create and enqueue tasks
            for item in review_items:
                task = self._create_review_task(item, input_data.image_id)

                # Score priority using dynamic thresholds
                task.priority = self._scorer.score(task)

                # Enqueue task
                await self._queue_manager.enqueue(
                    task,
                    queue_name=self.config.default_queue_name,
                )

                # Update counts
                task_ids.append(task.task_id)
                priority_counts[task.priority.value] += 1
                severity_counts[task.severity.value] += 1

            # Get queue stats
            queue_stats = await self._queue_manager.get_queue_stats(
                self.config.default_queue_name
            )

            # Calculate processing time
            end_time = datetime.now(timezone.utc)
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            # Build threshold info
            threshold_info = {
                "dynamic_enabled": self.config.enable_dynamic_thresholds,
                "config_provided": self.config.threshold_config is not None,
            }
            if context:
                threshold_info["image_quality_score"] = context.image_quality_score
                threshold_info["problem_level"] = context.problem_level.value
                threshold_info["element_count"] = context.element_count
            if feedback_stats:
                threshold_info["false_negative_rate"] = feedback_stats.false_negative_rate
                threshold_info["false_positive_rate"] = feedback_stats.false_positive_rate

            # Create summary
            summary = ReviewSummary(
                image_id=input_data.image_id,
                tasks_created=len(task_ids),
                tasks_by_priority=priority_counts,
                tasks_by_severity=severity_counts,
                task_ids=task_ids,
                queue_stats=queue_stats,
                threshold_info=threshold_info,
                dynamic_thresholds_enabled=self.config.enable_dynamic_thresholds,
                processing_time_ms=processing_time_ms,
                provenance=Provenance(
                    stage=PipelineStage.HUMAN_REVIEW,
                    model="human-review-stage-v1",
                    processing_time_ms=processing_time_ms,
                ),
            )

            logger.info(
                f"Human review stage completed for {input_data.image_id}: "
                f"{summary.tasks_created} tasks created, "
                f"{summary.critical_count} critical, "
                f"{summary.high_count} high priority"
            )

            return summary

        except Exception as e:
            raise StageExecutionError(
                message=f"Human review processing failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: ReviewSummary) -> StageMetrics:
        """Collect human review metrics.

        Args:
            output: ReviewSummary from execution

        Returns:
            StageMetrics with processing statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None,
        )

        if output:
            metrics.elements_processed = output.tasks_created
            metrics.duration_ms = output.processing_time_ms
            metrics.custom_metrics = {
                "tasks_created": output.tasks_created,
                "critical_count": output.critical_count,
                "high_count": output.high_count,
                "tasks_by_priority": output.tasks_by_priority,
                "tasks_by_severity": output.tasks_by_severity,
                "dynamic_thresholds_enabled": output.dynamic_thresholds_enabled,
                "image_id": output.image_id,
            }
            if output.queue_stats:
                metrics.custom_metrics["queue_depth"] = output.queue_stats.pending_tasks

        return metrics


# =============================================================================
# Convenience Functions
# =============================================================================

def create_human_review_stage(
    config: Optional[HumanReviewStageConfig] = None,
    threshold_config: Optional[ThresholdConfig] = None,
    enable_dynamic_thresholds: bool = True,
) -> HumanReviewStage:
    """Factory function to create human review stage.

    Args:
        config: Optional stage configuration
        threshold_config: Optional threshold configuration
        enable_dynamic_thresholds: Whether to enable dynamic thresholds

    Returns:
        Configured HumanReviewStage instance
    """
    if config is None:
        config = HumanReviewStageConfig()

    if threshold_config is not None:
        config.threshold_config = threshold_config

    config.enable_dynamic_thresholds = enable_dynamic_thresholds

    return HumanReviewStage(config=config)


def create_human_review_input(
    pipeline_result: PipelineResult,
    threshold_context: Optional[ThresholdContext] = None,
    feedback_stats: Optional[FeedbackStats] = None,
) -> HumanReviewInput:
    """Factory function to create human review input.

    Args:
        pipeline_result: Pipeline result to process
        threshold_context: Optional threshold context
        feedback_stats: Optional feedback statistics

    Returns:
        HumanReviewInput for stage processing
    """
    return HumanReviewInput(
        pipeline_result=pipeline_result,
        threshold_context=threshold_context,
        feedback_stats=feedback_stats,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Output type
    "ReviewSummary",
    # Composite Input
    "HumanReviewInput",
    # Configuration
    "HumanReviewStageConfig",
    # Stage Implementation
    "HumanReviewStage",
    # Convenience Functions
    "create_human_review_stage",
    "create_human_review_input",
]
