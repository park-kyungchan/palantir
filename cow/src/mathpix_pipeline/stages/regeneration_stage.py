"""
Stage F: Regeneration Stage.

Wraps RegenerationEngine to convert SemanticGraph into regenerated outputs.
Supports multiple output formats (LaTeX, SVG, TikZ, MathML).

Module Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..schemas.common import PipelineStage
from ..schemas.semantic_graph import SemanticGraph
from ..schemas.regeneration import (
    OutputFormat,
    RegenerationSpec,
)
from ..regeneration.engine import (
    RegenerationEngine,
    RegenerationConfig,
    EngineResult,
)
from ..regeneration.exceptions import RegenerationError
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
class RegenerationStageConfig:
    """Configuration for Stage F regeneration.

    Attributes:
        output_formats: List of formats to generate (default: latex, svg)
        enable_delta_comparison: Whether to compare with original content
        min_confidence_threshold: Minimum confidence for successful regeneration
        fail_on_low_confidence: Raise error if confidence below threshold
        include_intermediate_results: Include per-element results in output
    """
    output_formats: List[str] = field(default_factory=lambda: ["latex", "svg"])
    enable_delta_comparison: bool = True
    min_confidence_threshold: float = 0.60
    fail_on_low_confidence: bool = False
    include_intermediate_results: bool = True

    def to_engine_config(self) -> RegenerationConfig:
        """Convert to RegenerationConfig for RegenerationEngine."""
        # Convert string formats to OutputFormat enum
        formats = []
        for fmt in self.output_formats:
            try:
                formats.append(OutputFormat(fmt.lower()))
            except ValueError:
                # Skip invalid formats with warning
                pass

        return RegenerationConfig(
            default_formats=formats if formats else [OutputFormat.LATEX, OutputFormat.SVG],
            min_confidence_threshold=self.min_confidence_threshold,
            enable_delta_comparison=self.enable_delta_comparison,
            fail_on_low_confidence=self.fail_on_low_confidence,
            include_intermediate_results=self.include_intermediate_results,
        )


# =============================================================================
# Stage Implementation
# =============================================================================

class RegenerationStage(BaseStage[SemanticGraph, RegenerationSpec]):
    """Stage F: LaTeX/SVG Regeneration from semantic graph.

    Converts SemanticGraph into regenerated outputs through:
    1. LaTeX generation from nodes with equations
    2. SVG/TikZ diagram generation from geometric elements
    3. Optional delta comparison with original content
    4. Quality assessment and confidence scoring

    Supports v2.0.0 multi-format output:
    - OutputFormat.LATEX: Mathematical expressions
    - OutputFormat.SVG: Vector graphics
    - OutputFormat.TIKZ: TikZ code for LaTeX
    - OutputFormat.MATHML: MathML markup

    Example:
        stage = RegenerationStage(config=RegenerationStageConfig(
            output_formats=["latex", "svg", "tikz"],
            min_confidence_threshold=0.70,
        ))
        result = await stage.run_async(semantic_graph)
        if result.is_valid:
            spec = result.output
            latex = spec.get_latex()
            svg = spec.get_svg()
    """

    def __init__(
        self,
        config: Optional[RegenerationStageConfig] = None,
        engine: Optional[RegenerationEngine] = None,
    ):
        """Initialize regeneration stage.

        Args:
            config: Stage configuration
            engine: Custom engine (created from config if not provided)
        """
        super().__init__(config or RegenerationStageConfig())

        if engine:
            self._engine = engine
        else:
            self._engine = RegenerationEngine(
                config=self.config.to_engine_config()
            )

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage F identifier."""
        return PipelineStage.REGENERATION

    @property
    def config(self) -> RegenerationStageConfig:
        """Return typed configuration."""
        return self._config

    @property
    def engine(self) -> RegenerationEngine:
        """Return the underlying regeneration engine."""
        return self._engine

    def validate(self, input_data: SemanticGraph) -> ValidationResult:
        """Validate semantic graph input.

        Args:
            input_data: SemanticGraph to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        if input_data is None:
            result.add_error("SemanticGraph is required")
            return result

        # Check for at least one node
        if not input_data.nodes:
            result.add_error("SemanticGraph must have at least one node")
            return result

        # Check for minimum overall confidence
        if input_data.overall_confidence < 0.3:
            result.add_warning(
                f"Low input graph confidence: {input_data.overall_confidence:.2f}"
            )

        # Check for nodes needing review
        if input_data.nodes_needing_review > 0:
            result.add_warning(
                f"{input_data.nodes_needing_review} nodes flagged for review"
            )

        # Check for isolated nodes
        if input_data.statistics.isolated_nodes > 0:
            result.add_warning(
                f"{input_data.statistics.isolated_nodes} isolated nodes detected"
            )

        return result

    async def _execute_async(
        self,
        input_data: SemanticGraph,
        original_content: Optional[str] = None,
        original_graph: Optional[SemanticGraph] = None,
        **kwargs: Any,
    ) -> RegenerationSpec:
        """Execute regeneration from semantic graph.

        Args:
            input_data: SemanticGraph from Stage E
            original_content: Original LaTeX/content for delta comparison
            original_graph: Original semantic graph for detailed comparison
            **kwargs: Additional parameters

        Returns:
            RegenerationSpec with generated outputs

        Raises:
            StageExecutionError: If regeneration fails
        """
        try:
            # Convert string formats to OutputFormat enum
            output_formats = []
            for fmt in self.config.output_formats:
                try:
                    output_formats.append(OutputFormat(fmt.lower()))
                except ValueError:
                    pass

            # Call engine with converted formats
            engine_result: EngineResult = await self._engine.regenerate(
                semantic_graph=input_data,
                output_formats=output_formats if output_formats else None,
                original_content=original_content,
                original_graph=original_graph,
            )

            # Check for success
            if not engine_result.success:
                # Collect errors and warnings
                error_msg = "; ".join(engine_result.errors) if engine_result.errors else "Regeneration failed"
                if self.config.fail_on_low_confidence:
                    raise RegenerationError(
                        error_msg,
                        details={
                            "confidence": engine_result.overall_confidence,
                            "warnings": engine_result.warnings,
                        },
                    )

            return engine_result.spec

        except RegenerationError as e:
            raise StageExecutionError(
                message=str(e),
                stage=self.stage_name,
                cause=e,
            )
        except Exception as e:
            raise StageExecutionError(
                message=f"Regeneration failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: RegenerationSpec) -> StageMetrics:
        """Collect regeneration metrics.

        Args:
            output: RegenerationSpec from execution

        Returns:
            StageMetrics with regeneration statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None,
        )

        if output:
            metrics.elements_processed = output.total_elements_processed
            metrics.custom_metrics = {
                "output_formats": len(output.outputs),
                "overall_confidence": output.overall_confidence,
                "elements_success": output.total_elements_success,
                "elements_failed": output.total_elements_failed,
                "has_delta_report": output.delta_report is not None,
                "image_id": output.image_id,
            }

            # Add per-format confidence if available
            for out in output.outputs:
                metrics.custom_metrics[f"{out.format.value}_confidence"] = out.confidence

            # Add delta metrics if available
            if output.delta_report:
                metrics.custom_metrics["delta_similarity"] = output.delta_report.similarity_score
                metrics.custom_metrics["delta_changes"] = output.delta_report.total_changes

        return metrics


# =============================================================================
# Factory Function
# =============================================================================

def create_regeneration_stage(
    config: Optional[RegenerationStageConfig] = None,
    **kwargs,
) -> RegenerationStage:
    """Factory function to create RegenerationStage.

    Args:
        config: Optional RegenerationStageConfig
        **kwargs: Config overrides or component instances

    Returns:
        Configured RegenerationStage instance
    """
    if config is None:
        # Create config from kwargs
        config_kwargs = {}
        if "output_formats" in kwargs:
            config_kwargs["output_formats"] = kwargs.pop("output_formats")
        if "enable_delta_comparison" in kwargs:
            config_kwargs["enable_delta_comparison"] = kwargs.pop("enable_delta_comparison")
        if "min_confidence_threshold" in kwargs:
            config_kwargs["min_confidence_threshold"] = kwargs.pop("min_confidence_threshold")
        if "fail_on_low_confidence" in kwargs:
            config_kwargs["fail_on_low_confidence"] = kwargs.pop("fail_on_low_confidence")
        if "include_intermediate_results" in kwargs:
            config_kwargs["include_intermediate_results"] = kwargs.pop("include_intermediate_results")

        config = RegenerationStageConfig(**config_kwargs) if config_kwargs else None

    return RegenerationStage(
        config=config,
        engine=kwargs.get("engine"),
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "RegenerationStage",
    "RegenerationStageConfig",
    "create_regeneration_stage",
]
