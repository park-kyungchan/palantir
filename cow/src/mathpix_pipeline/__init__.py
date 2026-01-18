"""
Math Image Parsing Pipeline v2.0

A pipeline for converting math problem images to Desmos/GeoGebra compatible data.

8-Stage Pipeline:
    A. Ingestion -> B. TextParse -> C. VisionParse -> D. Alignment
                                                          |
    H. Export <- G. HumanReview <- F. Regeneration <- E. SemanticGraph

Configuration Usage:
    from mathpix_pipeline import PipelineConfig, load_config

    # Load from environment
    config = PipelineConfig.from_env()

    # Load from file
    config = PipelineConfig.from_file("config.yaml")

    # Validate
    warnings = config.validate()

Stage E Usage:
    from mathpix_pipeline import SemanticGraphBuilder

    builder = SemanticGraphBuilder()
    result = builder.build(alignment_report)

    if result.is_valid:
        graph = result.graph
"""

from .schemas import __version__

# Configuration (unified config loader)
from .config import (
    PipelineConfig,
    IngestionConfig,
    AlignmentConfig,
    SemanticGraphConfig,
    RegenerationConfig,
    HumanReviewConfig,
    ExportConfig,
    LoggingConfig,
    ConfigurationError,
    load_config,
)

# Stage E: Semantic Graph Builder (primary entry point for Stage E)
from .semantic_graph import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    BuildResult,
    GraphBuildError,
    create_graph_builder,
)

__all__ = [
    # Version
    "__version__",

    # Configuration
    "PipelineConfig",
    "IngestionConfig",
    "AlignmentConfig",
    "SemanticGraphConfig",
    "RegenerationConfig",
    "HumanReviewConfig",
    "ExportConfig",
    "LoggingConfig",
    "ConfigurationError",
    "load_config",

    # Stage E: SemanticGraph Builder
    "SemanticGraphBuilder",
    "GraphBuilderConfig",
    "BuildResult",
    "GraphBuildError",
    "create_graph_builder",
]
