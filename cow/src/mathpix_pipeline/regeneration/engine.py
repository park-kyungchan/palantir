"""
Regeneration Engine for Stage F (Regeneration).

Main orchestrator that coordinates all regeneration components:
1. LaTeX generation from semantic graphs
2. SVG/TikZ output generation
3. Delta comparison with original content
4. Quality assessment and validation

This is the primary entry point for Stage F processing.

Module Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..schemas.semantic_graph import SemanticGraph
from ..schemas.regeneration import (
    OutputFormat,
    RegenerationOutput,
    RegenerationSpec,
    RegenerationResult,
    DeltaReport,
    ElementCategory,
    Provenance,
    PipelineStage,
)
from ..schemas.common import PipelineStage as CommonPipelineStage
from .latex_generator import LaTeXGenerator, LaTeXConfig
from .svg_generator import SVGGenerator, SVGConfig
from .delta_comparer import DeltaComparer, DeltaConfig
from .exceptions import RegenerationError

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class RegenerationConfig:
    """Configuration for RegenerationEngine.

    Attributes:
        default_formats: Default output formats to generate
        min_confidence_threshold: Minimum confidence for successful regeneration
        enable_delta_comparison: Whether to compare with original
        latex_config: Configuration for LaTeX generator
        svg_config: Configuration for SVG generator
        delta_config: Configuration for delta comparer
        fail_on_low_confidence: Raise error if confidence below threshold
        include_intermediate_results: Include per-element results in output
    """
    default_formats: List[OutputFormat] = field(default_factory=lambda: [
        OutputFormat.LATEX,
        OutputFormat.SVG,
    ])
    min_confidence_threshold: float = 0.60
    enable_delta_comparison: bool = True
    latex_config: Optional[LaTeXConfig] = None
    svg_config: Optional[SVGConfig] = None
    delta_config: Optional[DeltaConfig] = None
    fail_on_low_confidence: bool = False
    include_intermediate_results: bool = True


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class EngineResult:
    """Result container for regeneration engine.

    Attributes:
        spec: The generated RegenerationSpec
        success: Whether regeneration succeeded
        processing_time_ms: Total processing time
        warnings: List of warnings encountered
        errors: List of errors encountered
    """
    spec: RegenerationSpec
    success: bool
    processing_time_ms: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def overall_confidence(self) -> float:
        """Get overall confidence from spec."""
        return self.spec.overall_confidence

    def summary(self) -> str:
        """Get human-readable summary."""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"EngineResult[{status}]: "
            f"confidence={self.overall_confidence:.2f}, "
            f"formats={len(self.spec.outputs)}, "
            f"time={self.processing_time_ms:.1f}ms"
        )


# =============================================================================
# Regeneration Engine
# =============================================================================

class RegenerationEngine:
    """Main orchestrator for Stage F regeneration.

    Coordinates LaTeX generation, SVG generation, and delta comparison
    to produce complete regeneration specifications.

    Pipeline Steps:
        1. Validate input semantic graph
        2. Generate outputs in requested formats
        3. Compare with original content (if enabled)
        4. Compile results into RegenerationSpec
        5. Apply quality checks and thresholds

    Usage:
        engine = RegenerationEngine()

        # Basic regeneration
        result = await engine.regenerate(semantic_graph)

        # With specific formats
        result = await engine.regenerate(
            semantic_graph,
            output_formats=[OutputFormat.LATEX, OutputFormat.SVG, OutputFormat.TIKZ]
        )

        # With original for comparison
        result = await engine.regenerate(
            semantic_graph,
            original_content="y = mx + b"
        )

        if result.success:
            spec = result.spec
            print(spec.get_latex())
    """

    def __init__(
        self,
        latex_generator: Optional[LaTeXGenerator] = None,
        svg_generator: Optional[SVGGenerator] = None,
        delta_comparer: Optional[DeltaComparer] = None,
        config: Optional[RegenerationConfig] = None,
    ):
        """Initialize RegenerationEngine.

        Args:
            latex_generator: Custom LaTeX generator. Creates default if None.
            svg_generator: Custom SVG generator. Creates default if None.
            delta_comparer: Custom delta comparer. Creates default if None.
            config: Engine configuration. Uses defaults if None.
        """
        self.config = config or RegenerationConfig()

        # Initialize generators
        self.latex_generator = latex_generator or LaTeXGenerator(
            config=self.config.latex_config
        )
        self.svg_generator = svg_generator or SVGGenerator(
            config=self.config.svg_config
        )
        self.delta_comparer = delta_comparer or DeltaComparer(
            config=self.config.delta_config
        )

        self._stats = {
            "regenerations_completed": 0,
            "regenerations_failed": 0,
            "formats_generated": 0,
            "comparisons_performed": 0,
        }

        logger.debug(
            f"RegenerationEngine initialized with "
            f"formats={[f.value for f in self.config.default_formats]}, "
            f"min_confidence={self.config.min_confidence_threshold}"
        )

    @property
    def stats(self) -> Dict[str, int]:
        """Get engine statistics."""
        return self._stats.copy()

    def _validate_input(self, graph: SemanticGraph) -> List[str]:
        """Validate semantic graph input.

        Args:
            graph: SemanticGraph to validate

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        if not graph.nodes:
            warnings.append("Semantic graph has no nodes")

        if graph.overall_confidence < 0.5:
            warnings.append(
                f"Low input confidence: {graph.overall_confidence:.2f}"
            )

        return warnings

    async def regenerate(
        self,
        semantic_graph: SemanticGraph,
        output_formats: Optional[List[OutputFormat]] = None,
        original_content: Optional[str] = None,
        original_graph: Optional[SemanticGraph] = None,
    ) -> EngineResult:
        """Regenerate content from semantic graph.

        Main entry point for Stage F processing.

        Args:
            semantic_graph: Stage E output to regenerate from
            output_formats: List of formats to generate (uses default if None)
            original_content: Original LaTeX/content for delta comparison
            original_graph: Original semantic graph for detailed comparison

        Returns:
            EngineResult with RegenerationSpec and metadata
        """
        start_time = time.time()
        warnings: List[str] = []
        errors: List[str] = []

        # Use default formats if not specified
        formats = output_formats or self.config.default_formats

        logger.info(
            f"Starting regeneration for image: {semantic_graph.image_id}, "
            f"formats: {[f.value for f in formats]}"
        )

        # Validate input
        validation_warnings = self._validate_input(semantic_graph)
        warnings.extend(validation_warnings)

        # Generate outputs
        outputs: List[RegenerationOutput] = []
        element_results: List[RegenerationResult] = []

        for fmt in formats:
            try:
                output = await self._generate_format(semantic_graph, fmt)
                outputs.append(output)
                self._stats["formats_generated"] += 1

                logger.debug(
                    f"Generated {fmt.value}: "
                    f"confidence={output.confidence:.2f}, "
                    f"time={output.generation_time_ms:.1f}ms"
                )

            except Exception as e:
                logger.error(f"Failed to generate {fmt.value}: {e}")
                errors.append(f"{fmt.value} generation failed: {e}")

        # Delta comparison
        delta_report: Optional[DeltaReport] = None

        if self.config.enable_delta_comparison:
            if original_graph:
                try:
                    delta_report = self.delta_comparer.compare(
                        original_graph, semantic_graph
                    )
                    self._stats["comparisons_performed"] += 1
                except Exception as e:
                    warnings.append(f"Delta comparison failed: {e}")

            elif original_content:
                try:
                    delta_report = self.delta_comparer.compare_with_original(
                        semantic_graph,
                        original_latex=original_content,
                    )
                    self._stats["comparisons_performed"] += 1
                except Exception as e:
                    warnings.append(f"Content comparison failed: {e}")

        # Build per-element results if enabled
        if self.config.include_intermediate_results:
            for node in semantic_graph.nodes:
                element_results.append(RegenerationResult(
                    element_id=node.id,
                    category=self._categorize_node(node),
                    success=True,
                    confidence=node.confidence.value,
                ))

        # Calculate overall confidence
        if outputs:
            overall_confidence = sum(o.confidence for o in outputs) / len(outputs)
        else:
            overall_confidence = 0.0

        # Build RegenerationSpec
        spec = RegenerationSpec(
            image_id=semantic_graph.image_id,
            semantic_graph_id=f"graph_{semantic_graph.image_id}",
            outputs=outputs,
            delta_report=delta_report,
            overall_confidence=overall_confidence,
            element_results=element_results if self.config.include_intermediate_results else [],
        )

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        spec.processing_time_ms = processing_time

        # Determine success
        success = (
            len(outputs) > 0 and
            len(errors) == 0 and
            overall_confidence >= self.config.min_confidence_threshold
        )

        if success:
            self._stats["regenerations_completed"] += 1
        else:
            self._stats["regenerations_failed"] += 1

        # Check threshold
        if not success and self.config.fail_on_low_confidence:
            raise RegenerationError(
                f"Regeneration confidence {overall_confidence:.2f} below "
                f"threshold {self.config.min_confidence_threshold}",
                details={
                    "confidence": overall_confidence,
                    "threshold": self.config.min_confidence_threshold,
                    "errors": errors,
                },
            )

        logger.info(
            f"Regeneration {'succeeded' if success else 'completed with issues'}: "
            f"confidence={overall_confidence:.2f}, "
            f"formats={len(outputs)}, "
            f"time={processing_time:.1f}ms"
        )

        return EngineResult(
            spec=spec,
            success=success,
            processing_time_ms=processing_time,
            warnings=warnings,
            errors=errors,
        )

    async def _generate_format(
        self,
        graph: SemanticGraph,
        format: OutputFormat,
    ) -> RegenerationOutput:
        """Generate output in a specific format.

        Args:
            graph: SemanticGraph to regenerate
            format: Output format

        Returns:
            RegenerationOutput for the format
        """
        if format == OutputFormat.LATEX:
            return self.latex_generator.generate_output(graph)

        elif format == OutputFormat.SVG:
            return self.svg_generator.generate_output(graph, OutputFormat.SVG)

        elif format == OutputFormat.TIKZ:
            return self.svg_generator.generate_output(graph, OutputFormat.TIKZ)

        elif format == OutputFormat.MATHML:
            # MathML generation - simplified implementation
            return self._generate_mathml(graph)

        else:
            raise RegenerationError(
                f"Unsupported output format: {format}",
                details={"format": format.value},
            )

    def _generate_mathml(self, graph: SemanticGraph) -> RegenerationOutput:
        """Generate MathML output (simplified).

        Args:
            graph: SemanticGraph

        Returns:
            RegenerationOutput with MathML content
        """
        start_time = time.time()

        # Basic MathML generation
        mathml_parts = ['<math xmlns="http://www.w3.org/1998/Math/MathML">']

        for node in graph.nodes:
            if node.properties.latex:
                # Convert LaTeX to basic MathML (simplified)
                latex = node.properties.latex
                mathml_parts.append(f"  <mi>{latex}</mi>")
            elif node.label:
                mathml_parts.append(f"  <mi>{node.label}</mi>")

        mathml_parts.append("</math>")

        content = "\n".join(mathml_parts)
        generation_time = (time.time() - start_time) * 1000

        return RegenerationOutput(
            format=OutputFormat.MATHML,
            content=content,
            confidence=0.7,  # Lower confidence for simplified implementation
            generation_time_ms=generation_time,
            element_count=len(graph.nodes),
            completeness_score=0.7,
            warnings=["MathML generation uses simplified conversion"],
        )

    def _categorize_node(self, node) -> ElementCategory:
        """Categorize a semantic node.

        Args:
            node: SemanticNode

        Returns:
            ElementCategory
        """
        from ..schemas.semantic_graph import NodeType

        category_map = {
            NodeType.EQUATION: ElementCategory.EQUATION,
            NodeType.EXPRESSION: ElementCategory.EQUATION,
            NodeType.FUNCTION: ElementCategory.EQUATION,
            NodeType.LINE: ElementCategory.GRAPH,
            NodeType.CIRCLE: ElementCategory.GRAPH,
            NodeType.CURVE: ElementCategory.GRAPH,
            NodeType.POINT: ElementCategory.DIAGRAM,
            NodeType.POLYGON: ElementCategory.DIAGRAM,
            NodeType.ANGLE: ElementCategory.DIAGRAM,
            NodeType.LABEL: ElementCategory.TEXT,
            NodeType.ANNOTATION: ElementCategory.ANNOTATION,
            NodeType.VARIABLE: ElementCategory.SYMBOL,
            NodeType.CONSTANT: ElementCategory.SYMBOL,
        }

        return category_map.get(node.node_type, ElementCategory.SYMBOL)

    async def regenerate_batch(
        self,
        graphs: List[SemanticGraph],
        output_formats: Optional[List[OutputFormat]] = None,
    ) -> List[EngineResult]:
        """Regenerate multiple semantic graphs.

        Args:
            graphs: List of SemanticGraphs to process
            output_formats: Output formats for all graphs

        Returns:
            List of EngineResults
        """
        results = []
        for graph in graphs:
            try:
                result = await self.regenerate(graph, output_formats)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch regeneration failed for {graph.image_id}: {e}")
                # Create failed result
                spec = RegenerationSpec(
                    image_id=graph.image_id,
                    semantic_graph_id=f"graph_{graph.image_id}",
                )
                results.append(EngineResult(
                    spec=spec,
                    success=False,
                    processing_time_ms=0.0,
                    errors=[str(e)],
                ))

        return results

    def get_component_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics from all components.

        Returns:
            Dict mapping component name to stats dict.
        """
        return {
            "engine": self._stats,
            "latex_generator": self.latex_generator.stats,
            "svg_generator": self.svg_generator.stats,
            "delta_comparer": self.delta_comparer.stats,
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_regeneration_engine(
    config: Optional[RegenerationConfig] = None,
    **kwargs,
) -> RegenerationEngine:
    """Factory function to create RegenerationEngine.

    Args:
        config: Optional RegenerationConfig
        **kwargs: Config overrides or component instances

    Returns:
        Configured RegenerationEngine instance
    """
    return RegenerationEngine(
        config=config,
        latex_generator=kwargs.get("latex_generator"),
        svg_generator=kwargs.get("svg_generator"),
        delta_comparer=kwargs.get("delta_comparer"),
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "RegenerationEngine",
    "RegenerationConfig",
    "EngineResult",
    "create_regeneration_engine",
]
