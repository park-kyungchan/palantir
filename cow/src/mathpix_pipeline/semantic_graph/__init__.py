"""
SemanticGraph Builder Module (Stage E).

Builds semantic graphs from AlignmentReport (Stage D output):
- SemanticGraphBuilder: Main orchestrator (primary entry point)
- NodeExtractor: Extract nodes from aligned elements
- EdgeInferrer: Infer relationships between nodes
- ConfidencePropagator: Propagate confidence through graph
- GraphValidator: Validate graph structure

Module Version: 2.0.0

Primary Usage (Recommended):
    from mathpix_pipeline.semantic_graph import SemanticGraphBuilder

    builder = SemanticGraphBuilder()
    result = builder.build(alignment_report)

    if result.is_valid:
        graph = result.graph
        print(f"Built graph: {result.summary()}")
    else:
        for issue in result.validation.issues:
            print(issue)

With Custom Configuration:
    from mathpix_pipeline.semantic_graph import (
        SemanticGraphBuilder,
        GraphBuilderConfig,
    )

    config = GraphBuilderConfig(
        node_threshold=0.70,
        edge_threshold=0.60,
        strict_validation=True,
    )
    builder = SemanticGraphBuilder(config=config)
    result = builder.build(alignment_report)
    result.raise_if_invalid()  # Raises GraphBuildError if invalid

Direct Component Usage (Advanced):
    from mathpix_pipeline.semantic_graph import (
        NodeExtractor,
        EdgeInferrer,
        ConfidencePropagator,
        GraphValidator,
    )

    extractor = NodeExtractor()
    nodes = extractor.extract(alignment_report)

    inferrer = EdgeInferrer()
    edges = inferrer.infer(nodes)

    propagator = ConfidencePropagator()
    propagator.propagate(graph)  # Mutates graph in place

    validator = GraphValidator()
    result = validator.validate(graph)

Factory Functions:
    from mathpix_pipeline.semantic_graph import (
        create_graph_builder,
        create_node_extractor,
        create_edge_inferrer,
    )

    builder = create_graph_builder()
    extractor = create_node_extractor(threshold=0.65)
    inferrer = create_edge_inferrer(proximity_px=60.0)
"""

# Main orchestrator (primary entry point)
from .builder import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    BuildResult,
    GraphBuildError,
    create_graph_builder,
)

# Component modules
from .node_extractor import (
    NodeExtractor,
    create_node_extractor,
    MATCH_TYPE_TO_NODE_TYPE,
    ELEMENT_CLASS_TO_NODE_TYPE,
)
from .edge_inferrer import (
    EdgeInferrer,
    create_edge_inferrer,
    LABEL_TARGET_TYPES,
    GRAPHABLE_TYPES,
    POINT_LIKE_TYPES,
    CURVE_LIKE_TYPES,
)
from .confidence import (
    ConfidencePropagator,
    GraphType,
    GraphTypeConfidenceAdjuster,
    create_confidence_propagator,
    create_graph_type_adjuster,
    DEFAULT_EDGE_CONFIDENCE_FACTOR,
    DEFAULT_ISOLATED_NODE_PENALTY,
    DEFAULT_MIN_CONFIDENCE,
    DEFAULT_CONNECTIVITY_BOOST,
)
from .validators import (
    GraphValidator,
    create_graph_validator,
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    VALID_EDGE_RULES,
)

__version__ = "2.0.0"

__all__ = [
    # Version
    "__version__",

    # === Main Builder (Primary Entry Point) ===
    "SemanticGraphBuilder",
    "GraphBuilderConfig",
    "BuildResult",
    "GraphBuildError",
    "create_graph_builder",

    # === Component Classes ===
    "NodeExtractor",
    "EdgeInferrer",
    "ConfidencePropagator",
    "GraphTypeConfidenceAdjuster",
    "GraphValidator",

    # === Enums ===
    "GraphType",

    # === Component Factories ===
    "create_node_extractor",
    "create_edge_inferrer",
    "create_confidence_propagator",
    "create_graph_type_adjuster",
    "create_graph_validator",

    # === NodeExtractor Constants ===
    "MATCH_TYPE_TO_NODE_TYPE",
    "ELEMENT_CLASS_TO_NODE_TYPE",

    # === EdgeInferrer Constants ===
    "LABEL_TARGET_TYPES",
    "GRAPHABLE_TYPES",
    "POINT_LIKE_TYPES",
    "CURVE_LIKE_TYPES",

    # === ConfidencePropagator Constants ===
    "DEFAULT_EDGE_CONFIDENCE_FACTOR",
    "DEFAULT_ISOLATED_NODE_PENALTY",
    "DEFAULT_MIN_CONFIDENCE",
    "DEFAULT_CONNECTIVITY_BOOST",

    # === GraphValidator Types ===
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "VALID_EDGE_RULES",
]
