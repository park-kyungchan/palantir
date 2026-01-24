"""
SemanticGraphBuilder for Stage E (Semantic Graph).

Main orchestrator that builds semantic graphs from AlignmentReport:
1. Extract nodes from matched pairs and unmatched elements
2. Infer edges between nodes
3. Propagate confidence scores
4. Validate graph structure
5. Compute statistics

This is the primary entry point for Stage E processing.

Module Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
import time

from ..schemas import AlignmentReport
from ..schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    Provenance,
    PipelineStage,
)
from ..schemas.threshold import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    compute_effective_threshold,
)
from .node_extractor import NodeExtractor
from .edge_inferrer import EdgeInferrer
from .confidence import ConfidencePropagator
from .validators import GraphValidator, ValidationResult

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class GraphBuilderConfig:
    """Configuration for SemanticGraphBuilder.

    This dataclass holds all configurable parameters for the graph building
    process, including thresholds for node extraction, edge inference,
    confidence propagation, and validation.

    v2.0.0 Enhancement: Dynamic threshold support via ThresholdConfig.
    When threshold_config is provided, thresholds are computed dynamically
    using the 3-layer architecture (base → context → feedback).

    Attributes:
        threshold_config: Optional ThresholdConfig for dynamic thresholds.
            When provided, overrides static node_threshold/edge_threshold.
        threshold_context: Optional context for threshold computation.
            Includes image quality, complexity, element density.
        feedback_stats: Optional feedback statistics for threshold adjustment.

        node_threshold: Default confidence threshold for nodes (fallback).
            Nodes below this threshold are flagged for review.
            Range: 0.0-1.0 (default: 0.60)
        unmatched_penalty: Confidence penalty for unmatched elements.
            Applied as (1.0 - penalty) multiplier to base confidence.
            Range: 0.0-1.0 (default: 0.3)
        spatial_overlap_threshold: Minimum IoU for INTERSECTS edge.
            Higher values require more overlap between bboxes.
            Range: 0.0-1.0 (default: 0.1)
        proximity_threshold_px: Maximum distance for ADJACENT_TO edge.
            Elements closer than this are considered adjacent.
            Range: 0.0-inf (default: 50.0)
        edge_threshold: Default confidence threshold for edges (fallback).
            Edges below this threshold are flagged for review.
            Range: 0.0-1.0 (default: 0.55)
        edge_confidence_factor: Factor for edge confidence propagation.
            Lower values are more conservative.
            Range: 0.0-1.0 (default: 0.9)
        isolated_node_penalty: Penalty for nodes with no connections.
            Range: 0.0-1.0 (default: 0.2)
        strict_validation: If True, treat warnings as errors.
            Range: bool (default: False)
        fail_on_validation_error: If True, raise on validation errors.
            Range: bool (default: True)
        graph_type: Optional classification of graph type.
            Examples: "function_graph", "geometry", "coordinate_plane"
            Range: str or None (default: None)
    """
    # v2.0.0: Dynamic threshold configuration
    threshold_config: Optional[ThresholdConfig] = None
    threshold_context: Optional[ThresholdContext] = None
    feedback_stats: Optional[FeedbackStats] = None

    # Node extraction (fallback when threshold_config is None)
    node_threshold: float = 0.60
    unmatched_penalty: float = 0.3

    # Edge inference (fallback when threshold_config is None)
    spatial_overlap_threshold: float = 0.1
    proximity_threshold_px: float = 50.0
    edge_threshold: float = 0.55

    # Confidence propagation
    edge_confidence_factor: float = 0.9
    isolated_node_penalty: float = 0.2

    # Validation
    strict_validation: bool = False
    fail_on_validation_error: bool = True

    # Graph metadata
    graph_type: Optional[str] = None

    def get_effective_node_threshold(self, element_type: str = "point") -> float:
        """Get effective node threshold using dynamic or static value.

        Args:
            element_type: Type of element (e.g., "point", "equation", "curve")

        Returns:
            Effective threshold for the element type
        """
        if self.threshold_config and self.threshold_context:
            feedback = self.feedback_stats or FeedbackStats()
            return compute_effective_threshold(
                element_type=element_type,
                context=self.threshold_context,
                feedback_stats=feedback,
                config=self.threshold_config,
            )
        return self.node_threshold

    def get_effective_edge_threshold(self, edge_type: str = "spatial") -> float:
        """Get effective edge threshold using dynamic or static value.

        Args:
            edge_type: Type of edge relationship

        Returns:
            Effective threshold for the edge type
        """
        if self.threshold_config and self.threshold_context:
            feedback = self.feedback_stats or FeedbackStats()
            # Map edge types to element types for threshold lookup
            element_type = "labels" if edge_type == "labeling" else "points"
            return compute_effective_threshold(
                element_type=element_type,
                context=self.threshold_context,
                feedback_stats=feedback,
                config=self.threshold_config,
            )
        return self.edge_threshold


# =============================================================================
# Build Result
# =============================================================================

@dataclass
class BuildResult:
    """Result of graph building operation.

    Contains the built graph, validation results, and timing information.

    Attributes:
        graph: The constructed SemanticGraph.
        validation: ValidationResult with all issues found.
        is_valid: True if no ERROR-level validation issues.
        processing_time_ms: Total time to build graph in milliseconds.
    """
    graph: SemanticGraph
    validation: ValidationResult
    is_valid: bool
    processing_time_ms: float

    def raise_if_invalid(self) -> None:
        """Raise exception if validation failed.

        Raises:
            GraphBuildError: If is_valid is False, with details of errors.
        """
        if not self.is_valid:
            errors = [i for i in self.validation.issues if i.severity.value == "error"]
            raise GraphBuildError(
                f"Graph validation failed with {len(errors)} error(s)",
                issues=errors,
            )

    @property
    def node_count(self) -> int:
        """Get number of nodes in the graph."""
        return len(self.graph.nodes)

    @property
    def edge_count(self) -> int:
        """Get number of edges in the graph."""
        return len(self.graph.edges)

    def summary(self) -> str:
        """Get a human-readable summary of the build result.

        Returns:
            String summary of the build result.
        """
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"BuildResult[{status}]: "
            f"{self.node_count} nodes, {self.edge_count} edges, "
            f"confidence={self.graph.overall_confidence:.2f}, "
            f"time={self.processing_time_ms:.1f}ms"
        )


# =============================================================================
# Exception
# =============================================================================

class GraphBuildError(Exception):
    """Exception raised when graph building fails validation.

    Attributes:
        message: Error description.
        issues: List of ValidationIssue objects that caused the failure.
    """
    def __init__(self, message: str, issues: List = None):
        super().__init__(message)
        self.issues = issues or []

    def __str__(self) -> str:
        """Format error with issue details."""
        base = super().__str__()
        if self.issues:
            issue_strs = [str(i) for i in self.issues[:5]]  # Limit to 5
            if len(self.issues) > 5:
                issue_strs.append(f"... and {len(self.issues) - 5} more")
            return f"{base}\nIssues:\n  " + "\n  ".join(issue_strs)
        return base


# =============================================================================
# SemanticGraphBuilder
# =============================================================================

class SemanticGraphBuilder:
    """Build semantic graphs from AlignmentReport.

    Orchestrates the complete Stage E pipeline:
    AlignmentReport -> NodeExtractor -> EdgeInferrer ->
    ConfidencePropagator -> GraphValidator -> SemanticGraph

    The builder is the main entry point for Stage E processing and
    integrates all component modules into a cohesive pipeline.

    Pipeline Steps:
        1. Node Extraction: Extract nodes from matched pairs and unmatched
           elements in the alignment report.
        2. Edge Inference: Infer relationships between nodes based on
           spatial, label, and mathematical relationships.
        3. Graph Assembly: Combine nodes and edges into a SemanticGraph
           with proper metadata and statistics.
        4. Confidence Propagation: Adjust confidences based on graph
           structure (edge endpoints, isolated nodes, connectivity).
        5. Validation: Validate graph structure for errors and warnings.

    Usage:
        # Basic usage
        builder = SemanticGraphBuilder()
        result = builder.build(alignment_report)

        if result.is_valid:
            graph = result.graph
            # Use graph...
        else:
            print(f"Validation failed: {result.validation}")

        # With custom configuration
        config = GraphBuilderConfig(
            node_threshold=0.70,
            strict_validation=True,
        )
        builder = SemanticGraphBuilder(config=config)
        result = builder.build(alignment_report)

        # With custom components
        builder = SemanticGraphBuilder(
            node_extractor=custom_extractor,
            edge_inferrer=custom_inferrer,
        )
        result = builder.build(alignment_report)

        # Raise on invalid
        result.raise_if_invalid()

    Attributes:
        config: GraphBuilderConfig with all parameters.
        node_extractor: NodeExtractor instance for node extraction.
        edge_inferrer: EdgeInferrer instance for edge inference.
        confidence_propagator: ConfidencePropagator for confidence adjustments.
        validator: GraphValidator for structure validation.
    """

    def __init__(
        self,
        node_extractor: Optional[NodeExtractor] = None,
        edge_inferrer: Optional[EdgeInferrer] = None,
        confidence_propagator: Optional[ConfidencePropagator] = None,
        validator: Optional[GraphValidator] = None,
        config: Optional[GraphBuilderConfig] = None,
    ):
        """Initialize SemanticGraphBuilder.

        Args:
            node_extractor: Custom node extractor. If None, creates default
                with config parameters.
            edge_inferrer: Custom edge inferrer. If None, creates default
                with config parameters.
            confidence_propagator: Custom propagator. If None, creates default
                with config parameters.
            validator: Custom validator. If None, creates default
                with config parameters.
            config: Builder configuration. If None, uses defaults.
        """
        self.config = config or GraphBuilderConfig()

        # Initialize components with config values
        self.node_extractor = node_extractor or NodeExtractor(
            default_threshold=self.config.node_threshold,
            unmatched_confidence_penalty=self.config.unmatched_penalty,
        )

        self.edge_inferrer = edge_inferrer or EdgeInferrer(
            spatial_overlap_threshold=self.config.spatial_overlap_threshold,
            proximity_threshold_px=self.config.proximity_threshold_px,
            default_edge_threshold=self.config.edge_threshold,
        )

        self.confidence_propagator = confidence_propagator or ConfidencePropagator(
            edge_confidence_factor=self.config.edge_confidence_factor,
            isolated_node_penalty=self.config.isolated_node_penalty,
        )

        self.validator = validator or GraphValidator(
            strict_mode=self.config.strict_validation,
        )

        logger.debug(
            f"SemanticGraphBuilder initialized with config: "
            f"node_threshold={self.config.node_threshold}, "
            f"edge_threshold={self.config.edge_threshold}, "
            f"strict={self.config.strict_validation}"
        )

    def build(self, alignment_report: AlignmentReport) -> BuildResult:
        """Build semantic graph from alignment report.

        This is the main entry point for graph construction. It orchestrates
        all component modules to transform an AlignmentReport into a
        validated SemanticGraph.

        v2.0.0: Supports dynamic threshold via ThresholdConfig.
        When threshold_config is provided, node/edge thresholds are computed
        dynamically based on element type, context, and feedback stats.

        Args:
            alignment_report: Stage D alignment output containing matched
                pairs, inconsistencies, and unmatched elements.

        Returns:
            BuildResult containing:
            - graph: The constructed SemanticGraph
            - validation: Validation results with any issues
            - is_valid: True if no validation errors
            - processing_time_ms: Build time in milliseconds

        Raises:
            GraphBuildError: If fail_on_validation_error is True and
                validation fails.
        """
        start_time = time.time()

        logger.info(f"Building semantic graph for image: {alignment_report.image_id}")
        logger.debug(
            f"Input: {len(alignment_report.matched_pairs)} matched pairs, "
            f"{len(alignment_report.unmatched_elements)} unmatched elements"
        )

        # Step 1: Extract nodes from alignment data
        logger.debug("Step 1: Extracting nodes...")
        nodes = self.node_extractor.extract(alignment_report)
        logger.info(f"Extracted {len(nodes)} nodes")

        if not nodes:
            logger.warning("No nodes extracted from alignment report")

        # Step 2: Infer edges between nodes
        logger.debug("Step 2: Inferring edges...")
        edges = self.edge_inferrer.infer(nodes)
        logger.info(f"Inferred {len(edges)} edges")

        # Step 3: Build initial graph structure
        logger.debug("Step 3: Building graph structure...")
        graph = self._build_graph(
            alignment_report=alignment_report,
            nodes=nodes,
            edges=edges,
        )

        # Step 3.5 (v2.0.0): Apply dynamic thresholds if configured
        if self.config.threshold_config and self.config.threshold_context:
            logger.debug("Step 3.5: Applying dynamic thresholds...")
            self._apply_dynamic_thresholds(graph)

        # Step 4: Propagate confidence through graph
        logger.debug("Step 4: Propagating confidence...")
        self.confidence_propagator.propagate(graph)

        # Step 5: Validate graph structure
        logger.debug("Step 5: Validating graph...")
        validation_result = self.validator.validate(graph)

        # Calculate total processing time
        processing_time_ms = (time.time() - start_time) * 1000
        graph.processing_time_ms = processing_time_ms

        # Determine validity (no errors)
        is_valid = not self.validator.has_errors(validation_result)

        logger.info(
            f"Graph built in {processing_time_ms:.2f}ms: "
            f"{len(nodes)} nodes, {len(edges)} edges, "
            f"confidence={graph.overall_confidence:.2f}, "
            f"valid={is_valid}"
        )

        result = BuildResult(
            graph=graph,
            validation=validation_result,
            is_valid=is_valid,
            processing_time_ms=processing_time_ms,
        )

        # Optionally raise on validation error
        if self.config.fail_on_validation_error and not is_valid:
            result.raise_if_invalid()

        return result

    def _apply_dynamic_thresholds(self, graph: SemanticGraph) -> None:
        """Apply dynamic thresholds to nodes and edges.

        v2.0.0: When ThresholdConfig is provided, compute per-element
        thresholds using the 3-layer architecture (base → context → feedback).

        This method updates:
        - node.applied_threshold for each node based on its node_type
        - edge.applied_threshold for each edge based on its edge_type

        Args:
            graph: SemanticGraph with nodes and edges to update
        """
        # Map node types to element types for threshold lookup
        node_type_to_element = {
            "point": "points",
            "line": "curves",
            "line_segment": "curves",
            "ray": "curves",
            "curve": "curves",
            "circle": "curves",
            "polygon": "shapes",
            "angle": "shapes",
            "axis": "axes",
            "coordinate_system": "axes",
            "label": "labels",
            "annotation": "labels",
            "equation": "equations",
            "expression": "equations",
            "function": "equations",
            "variable": "labels",
            "constant": "labels",
            "asymptote": "curves",
            "intercept": "points",
            "region": "shapes",
        }

        # Map edge types to element types for threshold lookup
        edge_type_to_element = {
            "labels": "labels",
            "labeled_by": "labels",
            "contains": "shapes",
            "intersects": "curves",
            "adjacent_to": "points",
            "lies_on": "points",
            "passes_through": "curves",
            "graph_of": "equations",
            "parallel_to": "curves",
            "perpendicular_to": "curves",
            "asymptote_of": "curves",
            "domain_of": "axes",
            "range_of": "axes",
        }

        # Update node thresholds
        for node in graph.nodes:
            element_type = node_type_to_element.get(
                node.node_type.value, "points"
            )
            threshold = self.config.get_effective_node_threshold(element_type)
            # Use object.__setattr__ to bypass Pydantic validation
            object.__setattr__(node, "applied_threshold", threshold)
            logger.debug(
                f"Node {node.id} ({node.node_type.value}): "
                f"threshold={threshold:.3f}"
            )

        # Update edge thresholds
        for edge in graph.edges:
            element_type = edge_type_to_element.get(
                edge.edge_type.value, "points"
            )
            threshold = self.config.get_effective_edge_threshold(element_type)
            # Use object.__setattr__ to bypass Pydantic validation
            object.__setattr__(edge, "applied_threshold", threshold)
            logger.debug(
                f"Edge {edge.id} ({edge.edge_type.value}): "
                f"threshold={threshold:.3f}"
            )

        logger.info(
            f"Applied dynamic thresholds to {len(graph.nodes)} nodes "
            f"and {len(graph.edges)} edges"
        )

    def _build_graph(
        self,
        alignment_report: AlignmentReport,
        nodes: List[SemanticNode],
        edges: List[SemanticEdge],
    ) -> SemanticGraph:
        """Construct SemanticGraph from components.

        Creates the graph object with proper metadata, provenance,
        and threshold configuration.

        Args:
            alignment_report: Source alignment report for metadata.
            nodes: List of extracted SemanticNodes.
            edges: List of inferred SemanticEdges.

        Returns:
            Constructed SemanticGraph (statistics computed by validator).
        """
        provenance = Provenance(
            stage=PipelineStage.SEMANTIC_GRAPH,
            model="graph-builder-v2",
        )

        return SemanticGraph(
            image_id=alignment_report.image_id,
            alignment_report_id=f"alignment_{alignment_report.image_id}",
            provenance=provenance,
            nodes=nodes,
            edges=edges,
            graph_type=self.config.graph_type,
            base_node_threshold=self.config.node_threshold,
            base_edge_threshold=self.config.edge_threshold,
        )

    def build_from_components(
        self,
        image_id: str,
        nodes: List[SemanticNode],
        edges: Optional[List[SemanticEdge]] = None,
        infer_edges: bool = True,
    ) -> BuildResult:
        """Build graph from pre-extracted nodes.

        Alternative entry point when nodes are already extracted.
        Useful for custom node extraction or testing.

        v2.0.0: Supports dynamic threshold via ThresholdConfig.

        Args:
            image_id: Identifier for the source image.
            nodes: Pre-extracted SemanticNodes.
            edges: Optional pre-inferred edges. If None and infer_edges
                is True, edges will be inferred from nodes.
            infer_edges: If True and edges is None, infer edges from nodes.

        Returns:
            BuildResult with constructed graph.
        """
        start_time = time.time()

        logger.info(f"Building graph from {len(nodes)} nodes for image: {image_id}")

        # Infer edges if not provided
        if edges is None and infer_edges:
            logger.debug("Inferring edges from nodes...")
            edges = self.edge_inferrer.infer(nodes)
        elif edges is None:
            edges = []

        # Build graph
        provenance = Provenance(
            stage=PipelineStage.SEMANTIC_GRAPH,
            model="graph-builder-v2-components",
        )

        graph = SemanticGraph(
            image_id=image_id,
            alignment_report_id=f"components_{image_id}",
            provenance=provenance,
            nodes=nodes,
            edges=edges,
            graph_type=self.config.graph_type,
            base_node_threshold=self.config.node_threshold,
            base_edge_threshold=self.config.edge_threshold,
        )

        # Apply dynamic thresholds if configured (v2.0.0)
        if self.config.threshold_config and self.config.threshold_context:
            logger.debug("Applying dynamic thresholds...")
            self._apply_dynamic_thresholds(graph)

        # Propagate and validate
        self.confidence_propagator.propagate(graph)
        validation_result = self.validator.validate(graph)

        processing_time_ms = (time.time() - start_time) * 1000
        graph.processing_time_ms = processing_time_ms

        is_valid = not self.validator.has_errors(validation_result)

        return BuildResult(
            graph=graph,
            validation=validation_result,
            is_valid=is_valid,
            processing_time_ms=processing_time_ms,
        )

    def get_component_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics from all components.

        Returns a dictionary with statistics from each component
        (node extractor, edge inferrer, confidence propagator).

        Returns:
            Dict mapping component name to stats dict.
        """
        return {
            "node_extractor": self.node_extractor.stats,
            "edge_inferrer": self.edge_inferrer.stats,
            "confidence_propagator": self.confidence_propagator.stats,
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_graph_builder(
    config: Optional[GraphBuilderConfig] = None,
    **kwargs,
) -> SemanticGraphBuilder:
    """Factory function to create SemanticGraphBuilder.

    Creates a builder with optional configuration. Additional keyword
    arguments are passed to SemanticGraphBuilder constructor.

    Args:
        config: Optional GraphBuilderConfig. If None, uses defaults.
        **kwargs: Additional arguments for SemanticGraphBuilder:
            - node_extractor: Custom NodeExtractor
            - edge_inferrer: Custom EdgeInferrer
            - confidence_propagator: Custom ConfidencePropagator
            - validator: Custom GraphValidator

    Returns:
        Configured SemanticGraphBuilder instance.

    Examples:
        # Default builder
        builder = create_graph_builder()

        # With custom config
        config = GraphBuilderConfig(node_threshold=0.70)
        builder = create_graph_builder(config=config)

        # With custom components
        builder = create_graph_builder(
            node_extractor=my_extractor,
            validator=strict_validator,
        )
    """
    return SemanticGraphBuilder(config=config, **kwargs)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Main class
    "SemanticGraphBuilder",
    # Configuration
    "GraphBuilderConfig",
    # Result types
    "BuildResult",
    # Exceptions
    "GraphBuildError",
    # Factory
    "create_graph_builder",
]
