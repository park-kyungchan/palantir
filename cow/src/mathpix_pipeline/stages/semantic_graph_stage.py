"""
Stage E: Semantic Graph Building Stage.

Wraps SemanticGraphBuilder to convert AlignmentReport into SemanticGraph.
Supports dynamic threshold system (v2.0.0).

Module Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Any, Optional

from ..schemas.common import PipelineStage
from ..schemas.alignment import AlignmentReport
from ..schemas.semantic_graph import SemanticGraph
from ..schemas.threshold import ThresholdContext, FeedbackStats
from ..semantic_graph import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    GraphBuildError,
)
from .base import (
    BaseStage,
    ValidationResult,
    StageMetrics,
    StageExecutionError,
)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class SemanticGraphStageConfig:
    """Configuration for Stage E semantic graph building.

    Attributes:
        node_threshold: Confidence threshold for nodes (default: 0.60)
        edge_threshold: Confidence threshold for edges (default: 0.55)
        strict_validation: Whether to fail on validation errors
        threshold_context: Dynamic threshold context (v2.0.0)
        feedback_stats: Feedback loop statistics (v2.0.0)
    """
    node_threshold: float = 0.60
    edge_threshold: float = 0.55
    strict_validation: bool = False
    threshold_context: Optional[ThresholdContext] = None
    feedback_stats: Optional[FeedbackStats] = None

    def to_builder_config(self) -> GraphBuilderConfig:
        """Convert to GraphBuilderConfig for SemanticGraphBuilder."""
        return GraphBuilderConfig(
            node_threshold=self.node_threshold,
            edge_threshold=self.edge_threshold,
            strict_validation=self.strict_validation,
            threshold_context=self.threshold_context,
            feedback_stats=self.feedback_stats,
        )


# =============================================================================
# Stage Implementation
# =============================================================================

class SemanticGraphStage(BaseStage[AlignmentReport, SemanticGraph]):
    """Stage E: Semantic Graph Building.

    Converts AlignmentReport into SemanticGraph through:
    1. Node extraction from matched pairs
    2. Edge inference from spatial/semantic relationships
    3. Confidence propagation through graph
    4. Validation and thresholding

    Supports v2.0.0 dynamic threshold system:
    - Layer 1: Base thresholds per element type
    - Layer 2: Context modifiers (quality, complexity)
    - Layer 3: Feedback loop adjustments

    Example:
        stage = SemanticGraphStage(config=SemanticGraphStageConfig(
            threshold_context=ThresholdContext(image_quality_score=0.9),
        ))
        result = await stage.run_async(alignment_report)
        if result.is_valid:
            graph = result.output
    """

    def __init__(
        self,
        config: Optional[SemanticGraphStageConfig] = None,
        builder: Optional[SemanticGraphBuilder] = None,
    ):
        """Initialize semantic graph stage.

        Args:
            config: Stage configuration
            builder: Custom builder (created from config if not provided)
        """
        super().__init__(config or SemanticGraphStageConfig())

        if builder:
            self._builder = builder
        else:
            self._builder = SemanticGraphBuilder(
                config=self.config.to_builder_config()
            )

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage E identifier."""
        return PipelineStage.SEMANTIC_GRAPH

    @property
    def config(self) -> SemanticGraphStageConfig:
        """Return typed configuration."""
        return self._config

    @property
    def builder(self) -> SemanticGraphBuilder:
        """Return the underlying builder."""
        return self._builder

    def validate(self, input_data: AlignmentReport) -> ValidationResult:
        """Validate alignment report input.

        Args:
            input_data: AlignmentReport to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        if input_data is None:
            result.add_error("AlignmentReport is required")
            return result

        # Check for matched pairs
        if not input_data.matched_pairs:
            result.add_warning("AlignmentReport has no matched pairs")

        # Check for minimum confidence
        if input_data.statistics:
            if input_data.statistics.matched_pairs == 0:
                result.add_warning("No matches in alignment - graph will be empty")

        return result

    async def _execute_async(
        self,
        input_data: AlignmentReport,
        **kwargs: Any,
    ) -> SemanticGraph:
        """Execute semantic graph building.

        Args:
            input_data: AlignmentReport from Stage D
            **kwargs: Additional parameters

        Returns:
            SemanticGraph with nodes and edges

        Raises:
            StageExecutionError: If building fails
        """
        try:
            # Build graph using the builder
            build_result = self._builder.build(input_data)

            if not build_result.is_valid:
                # Collect validation issues
                issues = []
                if build_result.validation:
                    issues = build_result.validation.issues
                raise GraphBuildError(
                    f"Graph building failed validation: {issues}"
                )

            return build_result.graph

        except GraphBuildError as e:
            raise StageExecutionError(
                message=str(e),
                stage=self.stage_name,
                cause=e,
            )
        except Exception as e:
            raise StageExecutionError(
                message=f"Semantic graph building failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: SemanticGraph) -> StageMetrics:
        """Collect graph building metrics.

        Args:
            output: SemanticGraph from execution

        Returns:
            StageMetrics with graph statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None,
        )

        if output:
            metrics.elements_processed = len(output.nodes)
            metrics.custom_metrics = {
                "node_count": len(output.nodes),
                "edge_count": len(output.edges),
                "image_id": output.image_id,
            }

        return metrics
