# Pipeline API Reference

Math Image Parsing Pipeline v2.0 - Complete API documentation for the `MathpixPipeline` class and related components.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [From Environment Variables](#from-environment-variables)
  - [From Config File](#from-config-file)
  - [Config File Example](#config-file-example)
- [Pipeline Options](#pipeline-options)
- [Pipeline Result](#pipeline-result)
- [Stage Outputs](#stage-outputs)
  - [TextSpec (Stage B)](#textspec-stage-b)
  - [VisionSpec (Stage C)](#visionspec-stage-c)
  - [SemanticGraph (Stage E)](#semanticgraph-stage-e)
- [Error Handling](#error-handling)
- [Logging Configuration](#logging-configuration)
- [Advanced Usage](#advanced-usage)

---

## Quick Start

Basic usage with async/await:

```python
import asyncio
from mathpix_pipeline import PipelineConfig, load_config
from mathpix_pipeline.pipeline import MathpixPipeline, PipelineOptions
from mathpix_pipeline.logging_config import configure_logging

# Configure logging
configure_logging(level="INFO")

async def process_image():
    # Load configuration from environment
    config = PipelineConfig.from_env()

    # Validate configuration
    warnings = config.validate()
    if warnings:
        print(f"Config warnings: {warnings}")

    # Create pipeline
    pipeline = MathpixPipeline()

    # Process single image
    result = await pipeline.process("path/to/math_image.png")

    if result.success:
        print(f"Processed: {result.summary()}")
        print(f"Stages completed: {result.stages_completed}")
        print(f"Overall confidence: {result.overall_confidence:.2f}")

        # Access stage outputs
        if result.semantic_graph:
            print(f"Graph nodes: {len(result.semantic_graph.nodes)}")
    else:
        for error in result.errors:
            print(f"Error: {error}")

    return result

# Run
result = asyncio.run(process_image())
```

### Batch Processing

```python
async def process_batch():
    pipeline = MathpixPipeline()

    images = [
        "image1.png",
        "image2.png",
        "image3.png",
    ]

    # Process with concurrency limit
    results = await pipeline.process_batch(
        images,
        max_concurrent=4,
        options=PipelineOptions(
            export_formats=["json", "latex"],
            enable_human_review=False,
        )
    )

    for result in results:
        print(f"{result.image_id}: {result.success}")

    return results
```

---

## Configuration

### From Environment Variables

Load configuration directly from environment variables:

```python
from mathpix_pipeline import PipelineConfig

# Load from environment
config = PipelineConfig.from_env()

# Validate
warnings = config.validate()
for warning in warnings:
    print(f"Warning: {warning}")
```

**Environment Variable Mapping:**

| Environment Variable | Config Field | Description |
|---------------------|--------------|-------------|
| `MATHPIX_APP_ID` | `mathpix_app_id` | Mathpix API application ID |
| `MATHPIX_APP_KEY` | `mathpix_app_key` | Mathpix API application key |
| `ANTHROPIC_API_KEY` | `anthropic_api_key` | Anthropic API key for Claude |
| `GEMINI_API_KEY` | `gemini_api_key` | Google Gemini API key |
| `PIPELINE_LOG_LEVEL` | `logging.log_level` | Logging level (DEBUG, INFO, etc.) |
| `PIPELINE_USE_STRUCTLOG` | `logging.use_structlog` | Enable structlog (true/false) |
| `PIPELINE_JSON_LOGS` | `logging.json_logs` | JSON log output (true/false) |
| `PIPELINE_DEBUG` | `debug_mode` | Enable debug mode |
| `PIPELINE_STRICT` | `strict_mode` | Enable strict mode |
| `PIPELINE_CACHE_DIR` | `ingestion.cache_dir` | Cache directory path |
| `PIPELINE_OUTPUT_DIR` | `export.output_directory` | Export output directory |
| `PIPELINE_ALIGNMENT_THRESHOLD` | `alignment.base_alignment_threshold` | Alignment threshold (0.0-1.0) |
| `PIPELINE_NODE_THRESHOLD` | `semantic_graph.node_threshold` | Node confidence threshold |
| `PIPELINE_EDGE_THRESHOLD` | `semantic_graph.edge_threshold` | Edge confidence threshold |
| `PIPELINE_EXPORT_FORMATS` | `export.default_export_formats` | Comma-separated formats |

### From Config File

Load from YAML or JSON configuration file:

```python
from mathpix_pipeline import PipelineConfig, load_config

# Load from YAML file
config = PipelineConfig.from_file("config.yaml")

# Or use the convenience function (merges env vars)
config = load_config(
    path="config.yaml",
    use_env=True  # Overlay environment variables
)

# Save configuration
config.save("config_backup.yaml")
```

### Config File Example

**config.yaml:**

```yaml
# API Keys (prefer environment variables for secrets)
# mathpix_app_id: "your-app-id"
# mathpix_app_key: "your-app-key"

# Global settings
pipeline_version: "2.0.0"
strict_mode: false
debug_mode: false

# Stage A: Ingestion
ingestion:
  enable_preprocessing: true
  preprocessing_operations:
    - normalize
    - denoise
    - deskew
  storage_enabled: true
  cache_dir: "/tmp/mathpix_cache"
  max_image_size_mb: 10.0
  supported_formats:
    - png
    - jpg
    - jpeg
    - webp

# Stage D: Alignment
alignment:
  base_alignment_threshold: 0.60
  base_inconsistency_threshold: 0.80
  enable_threshold_adjustment: true
  enable_auto_fix_detection: true
  max_unmatched_ratio: 0.3

# Stage E: Semantic Graph
semantic_graph:
  node_threshold: 0.60
  edge_threshold: 0.55
  strict_validation: false
  spatial_overlap_threshold: 0.1
  proximity_threshold_px: 50.0
  edge_confidence_factor: 0.9
  isolated_node_penalty: 0.2

# Stage F: Regeneration
regeneration:
  enable_latex_regeneration: true
  enable_svg_regeneration: true
  latex_template: "default"
  svg_width: 800
  svg_height: 600
  include_tikz: true
  delta_comparison_enabled: true

# Stage G: Human Review
human_review:
  enable_human_review: true
  review_threshold: 0.70
  auto_approve_threshold: 0.95
  max_queue_size: 1000
  session_timeout_minutes: 30
  require_multiple_reviewers: false
  critical_item_threshold: 0.40

# Stage H: Export
export:
  default_export_formats:
    - json
    - latex
  output_directory: "./output"
  include_metadata: true
  compress_output: false
  pdf_page_size: "letter"
  pdf_margins_pt: 72

# Logging
logging:
  log_level: "INFO"
  use_structlog: false
  json_logs: false
  log_file: null
  log_timing: true
  log_api_calls: false
```

---

## Pipeline Options

Control pipeline execution behavior with `PipelineOptions`:

```python
from mathpix_pipeline.schemas.pipeline import PipelineOptions
from mathpix_pipeline.schemas.common import PipelineStage

options = PipelineOptions(
    skip_stages=[PipelineStage.HUMAN_REVIEW],
    export_formats=["json", "latex", "svg"],
    enable_human_review=False,
    timeout_seconds=300,
    enable_parallel_processing=True,
    enable_caching=True,
    strict_validation=False,
    min_confidence_threshold=0.60,
)
```

**Options Reference:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `skip_stages` | `List[PipelineStage]` | `[]` | Stages to skip during execution |
| `export_formats` | `List[str]` | `["json"]` | Export formats to generate |
| `enable_human_review` | `bool` | `False` | Enable Stage G human review |
| `timeout_seconds` | `int` | `300` | Maximum execution time (1-3600) |
| `enable_parallel_processing` | `bool` | `True` | Enable parallel stage execution |
| `enable_caching` | `bool` | `True` | Cache intermediate results |
| `strict_validation` | `bool` | `False` | Fail on validation warnings |
| `min_confidence_threshold` | `float` | `0.60` | Minimum confidence (0.0-1.0) |

**Available Pipeline Stages:**

```python
from mathpix_pipeline.schemas.common import PipelineStage

# All stages
PipelineStage.INGESTION       # Stage A
PipelineStage.TEXT_PARSE      # Stage B
PipelineStage.VISION_PARSE    # Stage C
PipelineStage.ALIGNMENT       # Stage D
PipelineStage.SEMANTIC_GRAPH  # Stage E
PipelineStage.REGENERATION    # Stage F
PipelineStage.HUMAN_REVIEW    # Stage G
PipelineStage.EXPORT          # Stage H
```

---

## Pipeline Result

The `PipelineResult` object contains all outputs from pipeline processing:

```python
result = await pipeline.process("image.png", options)

# Check success
if result.success:
    print("Pipeline completed successfully")

# Access stage outputs
ingestion = result.ingestion_spec      # Stage A
text_spec = result.text_spec           # Stage B
vision_spec = result.vision_spec       # Stage C
alignment = result.alignment_report    # Stage D
graph = result.semantic_graph          # Stage E
regen = result.regeneration_spec       # Stage F
review = result.review_result          # Stage G
exports = result.export_result         # Stage H
```

**Result Fields Reference:**

| Field | Type | Description |
|-------|------|-------------|
| `image_id` | `str` | Unique identifier for processed image |
| `success` | `bool` | Whether pipeline completed successfully |
| `stages_completed` | `List[PipelineStage]` | List of completed stages |
| `ingestion_spec` | `Optional[IngestionSpec]` | Stage A output |
| `text_spec` | `Optional[TextSpec]` | Stage B output |
| `vision_spec` | `Optional[VisionSpec]` | Stage C output |
| `alignment_report` | `Optional[AlignmentReport]` | Stage D output |
| `semantic_graph` | `Optional[SemanticGraph]` | Stage E output |
| `regeneration_spec` | `Optional[RegenerationSpec]` | Stage F output |
| `review_result` | `Optional[Any]` | Stage G output |
| `export_result` | `Optional[List[ExportSpec]]` | Stage H outputs |
| `errors` | `List[str]` | Error messages |
| `warnings` | `List[str]` | Warning messages |
| `processing_time_ms` | `float` | Total processing time in ms |
| `stage_timings` | `List[StageTiming]` | Per-stage timing details |
| `overall_confidence` | `float` | Aggregate confidence (0.0-1.0) |
| `created_at` | `datetime` | Result creation timestamp |
| `options_used` | `Optional[PipelineOptions]` | Options used for this run |

**Result Methods:**

```python
# Get human-readable summary
print(result.summary())
# Output: "PipelineResult[SUCCESS]: stages=7/8, confidence=0.85, errors=0, time=1234.5ms"

# Check completion status
if result.is_complete:
    print("All stages completed")

# Check for errors
if result.has_errors:
    for error in result.errors:
        print(f"Error: {error}")

# Get timing for specific stage
timing = result.get_stage_timing(PipelineStage.ALIGNMENT)
if timing:
    print(f"Alignment took {timing.duration_ms}ms")
```

---

## Stage Outputs

### TextSpec (Stage B)

Stage B extracts text and equations using the Mathpix API:

```python
text_spec = result.text_spec

if text_spec:
    # Access raw content
    print(f"Full text: {text_spec.text}")
    print(f"LaTeX: {text_spec.latex}")
    print(f"Confidence: {text_spec.confidence}")

    # Check content flags
    flags = text_spec.content_flags
    print(f"Contains equation: {flags.contains_equation}")
    print(f"Contains diagram: {flags.contains_diagram}")
    print(f"Contains graph: {flags.contains_graph}")

    # Access equations
    for eq in text_spec.equations:
        print(f"Equation: {eq.latex}")
        print(f"  Confidence: {eq.confidence.value}")
        print(f"  BBox: {eq.bbox}")

    # Access line segments
    for line in text_spec.line_segments:
        print(f"Line {line.line_number}: {line.text}")
        print(f"  Content type: {line.content_type}")
        print(f"  Writing style: {line.writing_style}")

    # Check if vision parse should be triggered
    if text_spec.should_trigger_vision_parse():
        reasons = text_spec.get_trigger_reasons()
        print(f"Vision parse triggers: {reasons}")
```

**TextSpec Structure:**

```python
TextSpec:
    image_id: str
    content_flags: ContentFlags
        contains_equation: bool
        contains_text: bool
        contains_diagram: bool
        contains_graph: bool
        contains_geometry: bool
        contains_table: bool
        contains_handwriting: bool
    vision_parse_triggers: List[VisionParseTrigger]
    text: str
    latex: Optional[str]
    confidence: float
    equations: List[EquationElement]
        id: str
        bbox: BBox
        latex: str
        confidence: Confidence
    line_segments: List[LineSegment]
        id: str
        bbox: BBox
        text: str
        latex: Optional[str]
        confidence: Confidence
        line_number: int
```

### VisionSpec (Stage C)

Stage C implements YOLO + Claude hybrid architecture:

```python
vision_spec = result.vision_spec

if vision_spec:
    # Check diagram type
    diagram_type = vision_spec.merged_output.diagram_type
    print(f"Diagram type: {diagram_type}")

    # Access detection layer (YOLO results)
    detection = vision_spec.detection_layer
    print(f"YOLO detected {len(detection.elements)} elements")
    for elem in detection.elements:
        print(f"  {elem.element_class}: conf={elem.detection_confidence:.2f}")

    # Access interpretation layer (Claude results)
    interpretation = vision_spec.interpretation_layer
    print(f"Claude interpreted {len(interpretation.elements)} elements")
    for elem in interpretation.elements:
        print(f"  {elem.semantic_label}: {elem.description}")

    # Access merged output
    merged = vision_spec.merged_output
    for elem in merged.elements:
        print(f"Merged element: {elem.semantic_label}")
        print(f"  Class: {elem.element_class}")
        print(f"  BBox: {elem.bbox}")
        print(f"  Combined confidence: {elem.combined_confidence.combined_value:.2f}")
        if elem.equation:
            print(f"  Equation: {elem.equation}")

    # Access relations
    for rel in merged.relations:
        print(f"Relation: {rel.source_id} --{rel.relation_type}--> {rel.target_id}")

    # Check if fallback was used
    if vision_spec.fallback_used:
        print(f"Fallback model used: {vision_spec.fallback_model}")
        print(f"Reason: {vision_spec.fallback_reason}")
```

**VisionSpec Structure:**

```python
VisionSpec:
    image_id: str
    detection_layer: DetectionLayer
        model: str  # "yolo26-math-v1"
        elements: List[DetectionElement]
            id: str
            element_class: ElementClass
            bbox: BBox
            detection_confidence: float
    interpretation_layer: InterpretationLayer
        model: str  # "claude-opus-4-5"
        elements: List[InterpretedElement]
            id: str
            semantic_label: str
            description: Optional[str]
            latex_representation: Optional[str]
            equation: Optional[str]
            coordinates: Optional[Dict[str, float]]
        relations: List[InterpretedRelation]
        diagram_type: DiagramType
    merged_output: MergedOutput
        elements: List[MergedElement]
            id: str
            element_class: ElementClass
            bbox: BBox
            semantic_label: str
            combined_confidence: CombinedConfidence
        relations: List[InterpretedRelation]
        diagram_type: DiagramType
    fallback_used: bool
    fallback_model: Optional[str]
```

### SemanticGraph (Stage E)

Stage E builds a semantic graph from aligned elements:

```python
graph = result.semantic_graph

if graph:
    # Access graph metadata
    print(f"Graph confidence: {graph.overall_confidence:.2f}")
    print(f"Nodes: {len(graph.nodes)}")
    print(f"Edges: {len(graph.edges)}")

    # Access nodes
    for node in graph.nodes:
        print(f"Node: {node.id}")
        print(f"  Type: {node.node_type}")
        print(f"  Label: {node.label}")
        print(f"  Confidence: {node.confidence.value:.2f}")
        print(f"  Threshold passed: {node.threshold_passed}")

        # Access type-specific properties
        props = node.properties
        if props.coordinates:
            print(f"  Coordinates: {props.coordinates}")
        if props.equation:
            print(f"  Equation: {props.equation}")

    # Access edges
    for edge in graph.edges:
        print(f"Edge: {edge.source_id} --{edge.edge_type}--> {edge.target_id}")
        print(f"  Confidence: {edge.confidence.value:.2f}")

    # Graph statistics
    stats = graph.statistics
    print(f"Statistics:")
    print(f"  Total nodes: {stats.total_nodes}")
    print(f"  Total edges: {stats.total_edges}")
    print(f"  Isolated nodes: {stats.isolated_nodes}")
    print(f"  Nodes below threshold: {stats.nodes_below_threshold}")

    # Check review requirements
    print(f"Nodes needing review: {graph.nodes_needing_review}")
    print(f"Edges needing review: {graph.edges_needing_review}")
```

**SemanticGraph Structure:**

```python
SemanticGraph:
    image_id: str
    nodes: List[SemanticNode]
        id: str
        node_type: NodeType
        label: str
        bbox: Optional[BBox]
        confidence: Confidence
        threshold_passed: bool
        properties: NodeProperties
            coordinates: Optional[Dict[str, float]]
            equation: Optional[str]
            slope: Optional[float]
            center: Optional[Dict[str, float]]
            radius: Optional[float]
            latex: Optional[str]
    edges: List[SemanticEdge]
        id: str
        source_id: str
        target_id: str
        edge_type: EdgeType
        confidence: Confidence
    statistics: GraphStatistics
        total_nodes: int
        total_edges: int
        isolated_nodes: int
        nodes_below_threshold: int
        edges_below_threshold: int
    overall_confidence: float
```

---

## Error Handling

The pipeline provides structured error handling through exceptions and result objects:

### Exception Types

```python
from mathpix_pipeline.pipeline import PipelineError
from mathpix_pipeline.ingestion import IngestionError
from mathpix_pipeline.semantic_graph import GraphBuildError
from mathpix_pipeline.clients.mathpix import MathpixError
from mathpix_pipeline.config import ConfigurationError

# PipelineError - General pipeline errors
try:
    result = await pipeline.process("image.png")
except PipelineError as e:
    print(f"Pipeline error at stage {e.stage}: {e}")
    print(f"Details: {e.details}")

# ConfigurationError - Configuration issues
try:
    config = PipelineConfig.from_file("invalid.yaml")
except ConfigurationError as e:
    print(f"Config error: {e}")

# IngestionError - Image loading/validation errors
try:
    # Handled internally, appears in result.errors
    pass
except IngestionError as e:
    print(f"Ingestion error: {e}")

# GraphBuildError - Semantic graph construction errors
try:
    # Handled internally, appears in result.errors
    pass
except GraphBuildError as e:
    print(f"Graph build error: {e}")

# MathpixError - Mathpix API errors
try:
    # Handled internally, appears in result.errors
    pass
except MathpixError as e:
    print(f"Mathpix API error: {e}")
```

### Result-Based Error Handling

```python
async def safe_process(image_path: str) -> Optional[PipelineResult]:
    pipeline = MathpixPipeline()

    try:
        result = await pipeline.process(image_path)

        # Check for errors
        if not result.success:
            print(f"Pipeline failed for {image_path}")
            for error in result.errors:
                print(f"  Error: {error}")
            return None

        # Check for warnings
        if result.warnings:
            print(f"Warnings for {image_path}:")
            for warning in result.warnings:
                print(f"  Warning: {warning}")

        # Check confidence threshold
        if result.overall_confidence < 0.60:
            print(f"Low confidence: {result.overall_confidence:.2f}")

        return result

    except PipelineError as e:
        print(f"Critical error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### Stage-Specific Error Checking

```python
result = await pipeline.process("image.png")

# Check individual stage status
for timing in result.stage_timings:
    if not timing.success:
        print(f"Stage {timing.stage} failed: {timing.error_message}")
    else:
        print(f"Stage {timing.stage}: {timing.duration_ms:.1f}ms")

# Check for missing stage outputs
if result.text_spec is None:
    print("Warning: TextSpec not generated")
if result.vision_spec is None:
    print("Warning: VisionSpec not generated")
if result.semantic_graph is None:
    print("Warning: SemanticGraph not generated")
```

---

## Logging Configuration

Configure logging with optional structured logging support:

### Basic Logging

```python
from mathpix_pipeline.logging_config import configure_logging, get_logger

# Development setup
configure_logging(level="DEBUG")

# Production setup
configure_logging(level="INFO")

# Get logger
logger = get_logger(__name__)
logger.info("Processing started")
logger.debug("Debug information")
```

### Structured Logging with structlog

```python
from mathpix_pipeline.logging_config import (
    configure_logging,
    get_adapted_logger,
)

# Enable structlog with JSON output
configure_logging(
    level="INFO",
    use_structlog=True,
    json_output=True
)

# Use adapted logger for consistent interface
logger = get_adapted_logger(__name__)
logger = logger.bind(request_id="abc123")
logger.info("Processing image", image_id="img_001", stage="ingestion")
```

### Logging Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | `str` | `"INFO"` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `use_structlog` | `bool` | `False` | Enable structlog for structured logging |
| `json_output` | `bool` | `False` | Output logs as JSON (requires structlog) |
| `stream` | `Any` | `sys.stdout` | Output stream for logs |

### Reset Logging

```python
from mathpix_pipeline.logging_config import reset_logging

# Reset to unconfigured state (useful for testing)
reset_logging()
```

---

## Advanced Usage

### Custom Stage Configuration

```python
from mathpix_pipeline.pipeline import (
    MathpixPipeline,
    IngestionConfig,
    SemanticGraphConfig,
)
from mathpix_pipeline.alignment import AlignmentEngineConfig
from mathpix_pipeline.clients.mathpix import MathpixConfig

# Create with custom configurations
pipeline = MathpixPipeline(
    ingestion_config=IngestionConfig(
        enable_preprocessing=True,
        preprocessing_operations=["normalize", "denoise", "deskew"],
    ),
    alignment_config=AlignmentEngineConfig(
        base_alignment_threshold=0.70,
        enable_auto_fix_detection=True,
    ),
    graph_config=SemanticGraphConfig(
        node_threshold=0.65,
        edge_threshold=0.60,
        strict_validation=True,
    ),
    mathpix_config=MathpixConfig(
        app_id="your-app-id",
        app_key="your-app-key",
    ),
)
```

### Pipeline Statistics

```python
pipeline = MathpixPipeline()

# Process multiple images
for image in images:
    await pipeline.process(image)

# Get statistics
stats = pipeline.stats
print(f"Total processed: {stats['total_processed']}")
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
print(f"Total time: {stats['total_time_ms']:.1f}ms")

# Reset statistics
pipeline.reset_stats()
```

### Factory Function

```python
from mathpix_pipeline.pipeline import create_pipeline

# Use factory function for configuration
pipeline = create_pipeline(
    ingestion_config=IngestionConfig(),
    alignment_config=AlignmentEngineConfig(),
    graph_config=SemanticGraphConfig(),
)
```

### Selective Stage Execution

```python
from mathpix_pipeline.schemas.pipeline import PipelineOptions
from mathpix_pipeline.schemas.common import PipelineStage

# Skip human review and export
options = PipelineOptions(
    skip_stages=[
        PipelineStage.HUMAN_REVIEW,
        PipelineStage.EXPORT,
    ]
)

result = await pipeline.process("image.png", options)
```

### Accessing Raw API Responses

```python
result = await pipeline.process("image.png")

if result.text_spec:
    # Access raw Mathpix response for debugging
    raw = result.text_spec.raw_response
    if raw:
        print(f"Raw Mathpix response: {raw}")
```

---

## API Version

- **Pipeline Version:** 2.0.0
- **Schema Version:** 2.0.0
- **Module Version:** 1.0.0

For more information, see the [project README](../../README.md) or contact the development team.
