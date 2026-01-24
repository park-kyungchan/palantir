"""
MathpixPipeline: Full Pipeline Orchestrator for Math Image Parsing.

Coordinates all 8 stages of the pipeline:
    A. Ingestion → B. TextParse → C. VisionParse → D. Alignment
                                                        ↓
    H. Export ← G. HumanReview ← F. Regeneration ← E. SemanticGraph

Module Version: 1.0.0
"""

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .schemas.common import PipelineStage
from .schemas.pipeline import (
    PipelineOptions,
    PipelineResult,
    StageTiming,
)
from .schemas.ingestion import IngestionSpec
from .schemas.text_spec import TextSpec
from .schemas.vision_spec import VisionSpec
from .schemas.alignment import AlignmentReport
from .schemas.semantic_graph import SemanticGraph
from .schemas.regeneration import RegenerationSpec
from .schemas.export import ExportFormat

# Stage A: Ingestion
from .ingestion import (
    ImageLoader,
    ImageValidator,
    Preprocessor,
    StorageManager,
    IngestionError,
)

# Stage D: Alignment
from .alignment import AlignmentEngine, AlignmentEngineConfig

# Stage E: Semantic Graph
from .semantic_graph import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    GraphBuildError,
)

# Stage F: Regeneration
from .regeneration import (
    RegenerationEngine,
    RegenerationConfig,
)

# Stage H: Export
from .export import (
    ExportEngine,
    ExportEngineConfig,
)

# Stage B: Text Parse
from .clients.mathpix import MathpixClient, MathpixConfig, MathpixError

# Stage C: Vision Parse
from .vision import (
    YOLODetector,
    YOLOConfig,
    HybridMerger,
    MergerConfig,
)
from .vision.interpretation_layer import DiagramInterpreter, InterpretationConfig
from .vision.gemini_client import GeminiVisionClient

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class IngestionConfig:
    """Configuration for Stage A ingestion.

    Attributes:
        enable_preprocessing: Whether to apply preprocessing
        preprocessing_operations: List of operations to apply
        storage_enabled: Whether to store processed images
        cache_dir: Directory for caching
    """

    def __init__(
        self,
        enable_preprocessing: bool = True,
        preprocessing_operations: Optional[List[str]] = None,
        storage_enabled: bool = True,
        cache_dir: Optional[str] = None,
    ):
        self.enable_preprocessing = enable_preprocessing
        self.preprocessing_operations = preprocessing_operations or [
            "normalize",
            "denoise",
        ]
        self.storage_enabled = storage_enabled
        self.cache_dir = cache_dir


class SemanticGraphConfig:
    """Configuration for Stage E semantic graph building.

    Attributes:
        node_threshold: Confidence threshold for nodes
        edge_threshold: Confidence threshold for edges
        strict_validation: Whether to fail on validation errors
    """

    def __init__(
        self,
        node_threshold: float = 0.60,
        edge_threshold: float = 0.55,
        strict_validation: bool = False,
    ):
        self.node_threshold = node_threshold
        self.edge_threshold = edge_threshold
        self.strict_validation = strict_validation

    def to_builder_config(self) -> GraphBuilderConfig:
        """Convert to GraphBuilderConfig."""
        return GraphBuilderConfig(
            node_threshold=self.node_threshold,
            edge_threshold=self.edge_threshold,
            strict_validation=self.strict_validation,
        )


# =============================================================================
# Pipeline Exception
# =============================================================================

class PipelineError(Exception):
    """Exception raised during pipeline execution.

    Attributes:
        message: Error description
        stage: Stage where error occurred
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        stage: Optional[PipelineStage] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}

    def __str__(self) -> str:
        if self.stage:
            return f"[Stage {self.stage.value}] {super().__str__()}"
        return super().__str__()


# =============================================================================
# MathpixPipeline
# =============================================================================

class MathpixPipeline:
    """Full pipeline orchestrator for Math Image Parsing.

    Coordinates all 8 stages of the pipeline to process math images
    and produce various output formats.

    Usage:
        pipeline = MathpixPipeline()

        # Process single image
        result = await pipeline.process("path/to/image.png")

        if result.success:
            print(f"Processed: {result.summary()}")
            latex = result.regeneration_spec.get_latex()
        else:
            for error in result.errors:
                print(f"Error: {error}")

        # Process batch
        results = await pipeline.process_batch([
            "image1.png",
            "image2.png",
        ])

    With custom configuration:
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
            alignment_config=AlignmentEngineConfig(base_alignment_threshold=0.70),
            graph_config=SemanticGraphConfig(strict_validation=True),
        )
    """

    def __init__(
        self,
        ingestion_config: Optional[IngestionConfig] = None,
        alignment_config: Optional[AlignmentEngineConfig] = None,
        graph_config: Optional[SemanticGraphConfig] = None,
        regeneration_config: Optional[RegenerationConfig] = None,
        export_config: Optional[ExportEngineConfig] = None,
        mathpix_config: Optional[MathpixConfig] = None,
        yolo_config: Optional[YOLOConfig] = None,
        interpretation_config: Optional[InterpretationConfig] = None,
        merger_config: Optional[MergerConfig] = None,
    ):
        """Initialize MathpixPipeline.

        Args:
            ingestion_config: Configuration for Stage A
            alignment_config: Configuration for Stage D
            graph_config: Configuration for Stage E
            regeneration_config: Configuration for Stage F
            export_config: Configuration for Stage H
            mathpix_config: Configuration for Stage B (Mathpix API)
            yolo_config: Configuration for Stage C YOLO detection
            interpretation_config: Configuration for Stage C Claude interpretation
            merger_config: Configuration for Stage C hybrid merging
        """
        self.ingestion_config = ingestion_config or IngestionConfig()
        self.alignment_config = alignment_config or AlignmentEngineConfig()
        self.graph_config = graph_config or SemanticGraphConfig()
        self.regeneration_config = regeneration_config or RegenerationConfig()
        self.export_config = export_config or ExportEngineConfig()
        self.mathpix_config = mathpix_config
        self.yolo_config = yolo_config
        self.interpretation_config = interpretation_config
        self.merger_config = merger_config

        # Initialize stage components
        self._init_components()

        # Statistics
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_time_ms": 0.0,
        }

        logger.info("MathpixPipeline initialized")

    def _init_components(self) -> None:
        """Initialize pipeline stage components."""
        # Stage A: Ingestion components
        self._image_loader = ImageLoader()
        self._image_validator = ImageValidator()
        self._preprocessor = Preprocessor()
        self._storage_manager = StorageManager()

        # Stage D: Alignment
        self._alignment_engine = AlignmentEngine(self.alignment_config)

        # Stage E: Semantic Graph
        self._graph_builder = SemanticGraphBuilder(
            config=self.graph_config.to_builder_config()
        )

        # Stage F: Regeneration
        self._regeneration_engine = RegenerationEngine(
            config=self.regeneration_config
        )

        # Stage H: Export
        self._export_engine = ExportEngine(config=self.export_config)

    @property
    def stats(self) -> dict:
        """Get pipeline statistics."""
        return self._stats.copy()

    def _generate_image_id(self) -> str:
        """Generate unique image identifier."""
        return f"img_{uuid.uuid4().hex[:12]}"

    # =========================================================================
    # Stage Boundary Validation Methods
    # =========================================================================

    def _validate_stage_transition(
        self,
        from_stage: str,
        to_stage: str,
        data: Any,
        result: "PipelineResult",
    ) -> Tuple[bool, List[str]]:
        """Validate data between pipeline stages.

        Args:
            from_stage: Source stage name
            to_stage: Target stage name
            data: Data to validate
            result: Pipeline result for logging warnings

        Returns:
            Tuple of (is_valid, warnings_list)
        """
        validation_map = {
            ("A", "B"): lambda d: self._validate_ingestion_to_text(d),
            ("A", "C"): lambda d: self._validate_ingestion_to_vision(d),
            ("B", "D"): lambda d: self._validate_text_to_alignment(d),
            ("C", "D"): lambda d: self._validate_vision_to_alignment(d),
            ("D", "E"): lambda d: self._validate_alignment_to_graph(d),
            ("E", "F"): lambda d: self._validate_graph_to_regen(d),
        }

        key = (from_stage, to_stage)
        if key not in validation_map:
            logger.debug(f"No validation defined for {from_stage} -> {to_stage}")
            return True, []

        is_valid, warnings = validation_map[key](data)

        # Log warnings but don't block execution
        for warning in warnings:
            logger.warning(f"Stage transition {from_stage}->{to_stage}: {warning}")
            result.add_warning(warning)

        return is_valid, warnings

    def _validate_ingestion_to_text(
        self,
        spec: Optional[IngestionSpec],
    ) -> Tuple[bool, List[str]]:
        """Validate IngestionSpec before Stage B (Text Parse).

        Checks:
        - image_id is present
        - metadata is populated
        - validation passed

        Args:
            spec: IngestionSpec from Stage A

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings: List[str] = []

        if spec is None:
            return False, ["IngestionSpec is None - Stage A may have failed"]

        # Check required fields
        if not spec.image_id:
            warnings.append("Missing image_id in IngestionSpec")

        # Check metadata
        if spec.metadata is None:
            warnings.append("Missing metadata in IngestionSpec")
        else:
            if spec.metadata.width <= 0 or spec.metadata.height <= 0:
                warnings.append(
                    f"Invalid image dimensions: {spec.metadata.width}x{spec.metadata.height}"
                )

        # Check validation result
        if not spec.validation.is_valid:
            warnings.append(
                f"Image validation failed: {spec.validation.checks_failed}"
            )

        # Low math content confidence warning
        if spec.math_content_confidence < 0.3:
            warnings.append(
                f"Low math content confidence: {spec.math_content_confidence:.2f}"
            )

        is_valid = len(warnings) == 0 or (
            spec.image_id and spec.metadata is not None
        )
        return is_valid, warnings

    def _validate_ingestion_to_vision(
        self,
        spec: Optional[IngestionSpec],
    ) -> Tuple[bool, List[str]]:
        """Validate IngestionSpec before Stage C (Vision Parse).

        Same validation as ingestion_to_text since both need IngestionSpec.

        Args:
            spec: IngestionSpec from Stage A

        Returns:
            Tuple of (is_valid, warnings)
        """
        # Same validation logic as text parse
        return self._validate_ingestion_to_text(spec)

    def _validate_text_to_alignment(
        self,
        spec: Optional[TextSpec],
    ) -> Tuple[bool, List[str]]:
        """Validate TextSpec before Stage D (Alignment).

        Checks:
        - image_id is present
        - At least some content extracted (equations, lines, or text)
        - Confidence thresholds

        Args:
            spec: TextSpec from Stage B

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings: List[str] = []

        if spec is None:
            return False, ["TextSpec is None - Stage B may have failed"]

        # Check required fields
        if not spec.image_id:
            warnings.append("Missing image_id in TextSpec")

        # Check for empty data
        has_content = (
            len(spec.equations) > 0 or
            len(spec.line_segments) > 0 or
            (spec.text and len(spec.text.strip()) > 0)
        )

        if not has_content:
            warnings.append(
                "TextSpec has no content (no equations, lines, or text)"
            )

        # Check confidence threshold
        if spec.confidence < 0.3:
            warnings.append(
                f"Low TextSpec confidence: {spec.confidence:.2f} (threshold: 0.3)"
            )

        # Check for low-confidence equations
        low_conf_equations = [
            eq for eq in spec.equations
            if eq.confidence.value < 0.3
        ]
        if low_conf_equations:
            warnings.append(
                f"{len(low_conf_equations)} equations have confidence < 0.3"
            )

        is_valid = spec.image_id is not None and spec.image_id != ""
        return is_valid, warnings

    def _validate_vision_to_alignment(
        self,
        spec: Optional[VisionSpec],
    ) -> Tuple[bool, List[str]]:
        """Validate VisionSpec before Stage D (Alignment).

        Checks:
        - image_id is present
        - Merged output has elements
        - Confidence thresholds

        Args:
            spec: VisionSpec from Stage C

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings: List[str] = []

        if spec is None:
            return False, ["VisionSpec is None - Stage C may have failed"]

        # Check required fields
        if not spec.image_id:
            warnings.append("Missing image_id in VisionSpec")

        # Check for empty data
        if not spec.merged_output or len(spec.merged_output.elements) == 0:
            warnings.append(
                "VisionSpec has no merged elements"
            )

        # Check detection layer
        if spec.detection_layer and len(spec.detection_layer.elements) == 0:
            warnings.append("Detection layer has no elements")

        # Check interpretation layer
        if spec.interpretation_layer and len(spec.interpretation_layer.elements) == 0:
            warnings.append("Interpretation layer has no elements")

        # Check overall confidence
        if hasattr(spec, 'overall_confidence') and spec.overall_confidence < 0.3:
            warnings.append(
                f"Low VisionSpec overall confidence: {spec.overall_confidence:.2f}"
            )

        # Check fallback usage
        if spec.fallback_used:
            warnings.append(
                f"VisionSpec used fallback model: {spec.fallback_model}"
            )

        is_valid = spec.image_id is not None and spec.image_id != ""
        return is_valid, warnings

    def _validate_alignment_to_graph(
        self,
        report: Optional[AlignmentReport],
    ) -> Tuple[bool, List[str]]:
        """Validate AlignmentReport before Stage E (Semantic Graph).

        Checks:
        - image_id is present
        - Has matched pairs
        - Consistency scores above thresholds
        - No critical inconsistencies

        Args:
            report: AlignmentReport from Stage D

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings: List[str] = []

        if report is None:
            return False, ["AlignmentReport is None - Stage D may have failed"]

        # Check required fields
        if not report.image_id:
            warnings.append("Missing image_id in AlignmentReport")

        # Check for empty matched pairs
        if len(report.matched_pairs) == 0:
            warnings.append(
                "AlignmentReport has no matched pairs - nothing to build graph from"
            )

        # Check alignment score threshold (warn if < 0.3)
        if report.overall_alignment_score < 0.3:
            warnings.append(
                f"Low alignment score: {report.overall_alignment_score:.2f} (threshold: 0.3)"
            )

        # Check for pairs below threshold
        pairs_below = report.pairs_below_threshold
        if pairs_below > 0:
            total_pairs = len(report.matched_pairs)
            pct = (pairs_below / total_pairs * 100) if total_pairs > 0 else 0
            warnings.append(
                f"{pairs_below}/{total_pairs} pairs ({pct:.1f}%) below confidence threshold"
            )

        # Check for critical inconsistencies
        if report.has_blockers():
            warnings.append(
                f"AlignmentReport has {report.blocker_count} blocker inconsistencies"
            )

        # Check for high-severity issues
        if report.high_severity_count > 0:
            warnings.append(
                f"AlignmentReport has {report.high_severity_count} high-severity issues"
            )

        # Check overall confidence threshold
        if report.overall_confidence < 0.3:
            warnings.append(
                f"Low overall confidence: {report.overall_confidence:.2f}"
            )

        is_valid = (
            report.image_id is not None and
            report.image_id != "" and
            len(report.matched_pairs) > 0
        )
        return is_valid, warnings

    def _validate_graph_to_regen(
        self,
        graph: Optional[SemanticGraph],
    ) -> Tuple[bool, List[str]]:
        """Validate SemanticGraph before Stage F (Regeneration).

        Checks:
        - image_id is present
        - Has nodes
        - Node/edge confidence thresholds
        - Graph connectivity

        Args:
            graph: SemanticGraph from Stage E

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings: List[str] = []

        if graph is None:
            return False, ["SemanticGraph is None - Stage E may have failed"]

        # Check required fields
        if not graph.image_id:
            warnings.append("Missing image_id in SemanticGraph")

        # Check for empty graph
        if len(graph.nodes) == 0:
            warnings.append(
                "SemanticGraph has no nodes - nothing to regenerate"
            )

        # Check overall confidence threshold (warn if < 0.5)
        if graph.overall_confidence < 0.5:
            warnings.append(
                f"Low graph confidence: {graph.overall_confidence:.2f} (threshold: 0.5)"
            )

        # Check nodes below threshold
        if graph.statistics.nodes_below_threshold > 0:
            total = graph.statistics.total_nodes
            below = graph.statistics.nodes_below_threshold
            pct = (below / total * 100) if total > 0 else 0
            warnings.append(
                f"{below}/{total} nodes ({pct:.1f}%) below confidence threshold"
            )

        # Check edges below threshold
        if graph.statistics.edges_below_threshold > 0:
            total = graph.statistics.total_edges
            below = graph.statistics.edges_below_threshold
            pct = (below / total * 100) if total > 0 else 0
            warnings.append(
                f"{below}/{total} edges ({pct:.1f}%) below confidence threshold"
            )

        # Check for isolated nodes
        if graph.statistics.isolated_nodes > 0:
            warnings.append(
                f"Graph has {graph.statistics.isolated_nodes} isolated nodes"
            )

        # Check review requirements
        if graph.nodes_needing_review > 0:
            warnings.append(
                f"{graph.nodes_needing_review} nodes need human review"
            )
        if graph.edges_needing_review > 0:
            warnings.append(
                f"{graph.edges_needing_review} edges need human review"
            )

        is_valid = (
            graph.image_id is not None and
            graph.image_id != "" and
            len(graph.nodes) > 0
        )
        return is_valid, warnings

    async def process(
        self,
        image: Union[str, Path, bytes],
        options: Optional[PipelineOptions] = None,
    ) -> PipelineResult:
        """Process a single image through the pipeline.

        Args:
            image: Image to process (path, URL, or bytes)
            options: Pipeline execution options

        Returns:
            PipelineResult with all stage outputs
        """
        start_time = time.perf_counter()
        options = options or PipelineOptions()
        image_id = self._generate_image_id()

        # Initialize result
        result = PipelineResult(
            image_id=image_id,
            options_used=options,
        )

        logger.info(f"Starting pipeline for image: {image_id}")

        try:
            # Stage A: Ingestion
            if not options.should_skip(PipelineStage.INGESTION):
                result.ingestion_spec = await self._run_stage_a(
                    image, image_id, result
                )

            # Stage B: Text Parse (placeholder - requires Mathpix API)
            if not options.should_skip(PipelineStage.TEXT_PARSE):
                # Validate A -> B transition
                self._validate_stage_transition(
                    "A", "B", result.ingestion_spec, result
                )
                result.text_spec = await self._run_stage_b(
                    result.ingestion_spec, result
                )

            # Stage C: Vision Parse (YOLO + Claude with Gemini fallback)
            if not options.should_skip(PipelineStage.VISION_PARSE):
                # Validate A -> C transition
                self._validate_stage_transition(
                    "A", "C", result.ingestion_spec, result
                )
                result.vision_spec = await self._run_stage_c(
                    result.ingestion_spec, result.text_spec, result
                )

            # Stage D: Alignment
            if not options.should_skip(PipelineStage.ALIGNMENT):
                if result.text_spec and result.vision_spec:
                    # Validate B -> D transition (text to alignment)
                    self._validate_stage_transition(
                        "B", "D", result.text_spec, result
                    )
                    # Validate C -> D transition (vision to alignment)
                    self._validate_stage_transition(
                        "C", "D", result.vision_spec, result
                    )
                    result.alignment_report = await self._run_stage_d(
                        result.text_spec, result.vision_spec, result
                    )

            # Stage E: Semantic Graph
            if not options.should_skip(PipelineStage.SEMANTIC_GRAPH):
                if result.alignment_report:
                    # Validate D -> E transition
                    self._validate_stage_transition(
                        "D", "E", result.alignment_report, result
                    )
                    result.semantic_graph = await self._run_stage_e(
                        result.alignment_report, result
                    )

            # Stage F: Regeneration
            if not options.should_skip(PipelineStage.REGENERATION):
                if result.semantic_graph:
                    # Validate E -> F transition
                    self._validate_stage_transition(
                        "E", "F", result.semantic_graph, result
                    )
                    result.regeneration_spec = await self._run_stage_f(
                        result.semantic_graph, result
                    )

            # Stage G: Human Review (optional)
            if options.enable_human_review and not options.should_skip(
                PipelineStage.HUMAN_REVIEW
            ):
                result.review_result = await self._run_stage_g(result, options)

            # Stage H: Export
            if not options.should_skip(PipelineStage.EXPORT):
                result.export_result = await self._run_stage_h(
                    result, options.export_formats
                )

            # Mark success if no errors
            result.success = not result.has_errors

        except PipelineError as e:
            logger.error(f"Pipeline error: {e}")
            result.add_error(str(e), e.stage)
            result.success = False

        except Exception as e:
            logger.exception(f"Unexpected error in pipeline: {e}")
            result.add_error(f"Unexpected error: {e}")
            result.success = False

        # Calculate total time
        result.processing_time_ms = (time.perf_counter() - start_time) * 1000

        # Update statistics
        self._stats["total_processed"] += 1
        if result.success:
            self._stats["successful"] += 1
        else:
            self._stats["failed"] += 1
        self._stats["total_time_ms"] += result.processing_time_ms

        logger.info(f"Pipeline completed: {result.summary()}")

        return result

    async def process_batch(
        self,
        images: List[Union[str, Path, bytes]],
        options: Optional[PipelineOptions] = None,
        max_concurrent: int = 4,
    ) -> List[PipelineResult]:
        """Process multiple images through the pipeline.

        Args:
            images: List of images to process
            options: Pipeline execution options (applied to all)
            max_concurrent: Maximum concurrent processing

        Returns:
            List of PipelineResult for each image
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(
            image: Union[str, Path, bytes]
        ) -> PipelineResult:
            async with semaphore:
                return await self.process(image, options)

        tasks = [process_with_semaphore(img) for img in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_result = PipelineResult(
                    image_id=f"batch_{i}",
                    success=False,
                    errors=[str(result)],
                )
                final_results.append(failed_result)
            else:
                final_results.append(result)

        return final_results

    # =========================================================================
    # Stage Implementations
    # =========================================================================

    async def _run_stage_a(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
        result: PipelineResult,
    ) -> IngestionSpec:
        """Run Stage A: Ingestion.

        Args:
            image: Image input
            image_id: Image identifier
            result: Pipeline result to update

        Returns:
            IngestionSpec
        """
        timing = StageTiming(stage=PipelineStage.INGESTION)
        result.stage_timings.append(timing)

        try:
            # Load image
            if isinstance(image, bytes):
                loaded = await self._image_loader.load_from_bytes(image)
            elif isinstance(image, (str, Path)):
                path = Path(image)
                if path.exists():
                    loaded = await self._image_loader.load_from_path(str(path))
                elif str(image).startswith(("http://", "https://")):
                    loaded = await self._image_loader.load_from_url(str(image))
                else:
                    raise IngestionError(f"Image not found: {image}")
            else:
                raise IngestionError(f"Unsupported image type: {type(image)}")

            # Validate
            validation = self._image_validator.validate(loaded)
            if not validation.is_valid:
                result.add_warning(
                    f"Image validation warnings: {validation.warnings}",
                    PipelineStage.INGESTION,
                )

            # Preprocess
            if self.ingestion_config.enable_preprocessing:
                processed = self._preprocessor.process(loaded)
            else:
                processed = loaded

            # Create spec
            spec = IngestionSpec(
                image_id=image_id,
                source_path=str(image) if isinstance(image, (str, Path)) else None,
                metadata=loaded.metadata,
                validation=validation,
                preprocessing_applied=(
                    self.ingestion_config.preprocessing_operations
                    if self.ingestion_config.enable_preprocessing
                    else []
                ),
            )

            result.mark_stage_complete(PipelineStage.INGESTION)
            timing.complete(success=True)

            return spec

        except Exception as e:
            timing.complete(success=False, error=str(e))
            raise PipelineError(
                f"Ingestion failed: {e}",
                stage=PipelineStage.INGESTION,
            )

    async def _run_stage_b(
        self,
        ingestion_spec: Optional[IngestionSpec],
        result: PipelineResult,
    ) -> Optional[TextSpec]:
        """Run Stage B: Text Parse using Mathpix API.

        Calls Mathpix API to extract:
        - LaTeX equations
        - Line segments with positions
        - Content flags (has_diagram, has_graph, etc.)

        Args:
            ingestion_spec: Stage A output with image data
            result: Pipeline result to update

        Returns:
            TextSpec with extracted text elements
        """
        timing = StageTiming(stage=PipelineStage.TEXT_PARSE)
        result.stage_timings.append(timing)

        try:
            if not ingestion_spec:
                result.add_warning(
                    "Skipping text parse: no ingestion spec",
                    PipelineStage.TEXT_PARSE,
                )
                timing.complete(success=True)
                return None

            # Initialize Mathpix client if not exists
            if not hasattr(self, '_mathpix_client'):
                if self.mathpix_config is None:
                    # FAIL-FAST: Stage B requires valid Mathpix credentials
                    error_msg = (
                        "Mathpix config not provided. Stage B (TextParse) requires "
                        "valid Mathpix credentials. Set MATHPIX_APP_ID and MATHPIX_APP_KEY "
                        "environment variables or provide MathpixConfig."
                    )
                    result.add_error(error_msg, PipelineStage.TEXT_PARSE)
                    timing.complete(success=False, error=error_msg)
                    return None  # Return None with ERROR, not warning with empty spec

                self._mathpix_client = MathpixClient(
                    config=self.mathpix_config
                )

            # Get image bytes from storage
            image_bytes = await self._storage_manager.get_image_bytes(
                ingestion_spec.image_id
            )

            if not image_bytes:
                result.add_error(
                    f"Could not load image bytes for {ingestion_spec.image_id}",
                    PipelineStage.TEXT_PARSE,
                )
                timing.complete(success=False, error="Image not found")
                return None

            # Call Mathpix API
            async with self._mathpix_client:
                text_spec = await self._mathpix_client.process_image(
                    image_bytes,
                    image_id=ingestion_spec.image_id,
                )

            # Log extraction stats
            logger.info(
                f"Stage B completed: {len(text_spec.equations)} equations, "
                f"{len(text_spec.line_segments)} line segments"
            )

            result.mark_stage_complete(PipelineStage.TEXT_PARSE)
            timing.complete(success=True)

            return text_spec

        except MathpixError as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Mathpix API error: {e}", PipelineStage.TEXT_PARSE)
            return None

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Text parse failed: {e}", PipelineStage.TEXT_PARSE)
            return None

    async def _run_stage_c(
        self,
        ingestion_spec: Optional[IngestionSpec],
        text_spec: Optional[TextSpec],
        result: PipelineResult,
    ) -> Optional[VisionSpec]:
        """Run Stage C: Vision Parse using YOLO + Claude with fallback.

        Runs multi-layer detection:
        1. YOLO for object detection (fast, local)
        2. Claude/Gemini for semantic interpretation (accurate, API)
        3. Hybrid merger to combine results
        4. Fallback chain if primary path fails

        Args:
            ingestion_spec: Stage A output with image data
            text_spec: Stage B output (may contain vision_parse_triggers)
            result: Pipeline result to update

        Returns:
            VisionSpec with visual elements and relations
        """
        from .schemas.vision_spec import (
            DetectionLayer,
            InterpretationLayer,
            MergedOutput,
        )

        timing = StageTiming(stage=PipelineStage.VISION_PARSE)
        result.stage_timings.append(timing)

        try:
            if not ingestion_spec:
                result.add_warning(
                    "Skipping vision parse: no ingestion spec",
                    PipelineStage.VISION_PARSE,
                )
                timing.complete(success=True)
                return None

            # Check if vision parse is needed based on Stage B triggers
            if text_spec and hasattr(text_spec, 'vision_parse_triggers'):
                if not text_spec.vision_parse_triggers:
                    logger.info("Stage C skipped: no vision parse triggers from Stage B")
                    timing.complete(success=True)
                    return None

            # Get image bytes
            image_bytes = await self._storage_manager.get_image_bytes(
                ingestion_spec.image_id
            )

            if not image_bytes:
                result.add_error(
                    f"Could not load image bytes for {ingestion_spec.image_id}",
                    PipelineStage.VISION_PARSE,
                )
                timing.complete(success=False, error="Image not found")
                return None

            # Initialize vision components if needed
            if not hasattr(self, '_yolo_detector'):
                self._yolo_detector = YOLODetector(
                    config=self.yolo_config or YOLOConfig()
                )
            if not hasattr(self, '_diagram_interpreter'):
                self._diagram_interpreter = DiagramInterpreter(
                    config=self.interpretation_config or InterpretationConfig()
                )
            if not hasattr(self, '_hybrid_merger'):
                self._hybrid_merger = HybridMerger(
                    config=self.merger_config or MergerConfig()
                )

            # Layer 1: YOLO detection with fallback
            detection_layer: Optional[DetectionLayer] = None
            try:
                detection_layer = self._yolo_detector.detect(
                    image_bytes,
                    image_id=ingestion_spec.image_id,
                )
                logger.info(f"YOLO detected {len(detection_layer.elements)} elements")
            except Exception as yolo_error:
                logger.warning(f"YOLO detection failed, using empty layer: {yolo_error}")
                detection_layer = DetectionLayer(
                    elements=[],
                )

            # Layer 2: Claude interpretation with fallback
            interpretation_layer: Optional[InterpretationLayer] = None
            try:
                interpretation_layer = await self._diagram_interpreter.interpret(
                    image_bytes,
                    detection_layer,
                    image_id=ingestion_spec.image_id,
                )
                logger.info(f"Interpretation found {len(interpretation_layer.elements)} semantic elements")
            except Exception as interp_error:
                logger.warning(f"Interpretation failed, trying Gemini fallback: {interp_error}")

                # Try Gemini fallback
                try:
                    if not hasattr(self, '_gemini_client'):
                        self._gemini_client = GeminiVisionClient()

                    fallback_spec = await self._gemini_client.detect_and_interpret(
                        image_bytes,
                        image_id=ingestion_spec.image_id,
                    )

                    if fallback_spec:
                        logger.info("Gemini fallback successful")
                        result.mark_stage_complete(PipelineStage.VISION_PARSE)
                        timing.complete(success=True)
                        return fallback_spec

                except Exception as gemini_error:
                    logger.warning(f"Gemini fallback also failed: {gemini_error}")

                # Create empty interpretation layer as last resort
                interpretation_layer = InterpretationLayer(
                    elements=[],
                    relations=[],
                )

            # Merge results
            merged_output = self._hybrid_merger.merge(
                detection_layer,
                interpretation_layer,
                image_id=ingestion_spec.image_id,
            )

            # Build VisionSpec
            vision_spec = VisionSpec(
                image_id=ingestion_spec.image_id,
                detection_layer=detection_layer,
                interpretation_layer=interpretation_layer,
                merged_output=merged_output,
            )

            logger.info(
                f"Stage C completed: {len(merged_output.elements)} merged elements"
            )

            result.mark_stage_complete(PipelineStage.VISION_PARSE)
            timing.complete(success=True)

            return vision_spec

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Vision parse failed: {e}", PipelineStage.VISION_PARSE)
            return None

    async def _run_stage_d(
        self,
        text_spec: TextSpec,
        vision_spec: VisionSpec,
        result: PipelineResult,
    ) -> Optional[AlignmentReport]:
        """Run Stage D: Alignment.

        Args:
            text_spec: Stage B output
            vision_spec: Stage C output
            result: Pipeline result to update

        Returns:
            AlignmentReport or None
        """
        timing = StageTiming(stage=PipelineStage.ALIGNMENT)
        result.stage_timings.append(timing)

        try:
            report = self._alignment_engine.align(text_spec, vision_spec)

            result.mark_stage_complete(PipelineStage.ALIGNMENT)
            timing.complete(success=True)

            return report

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Alignment failed: {e}", PipelineStage.ALIGNMENT)
            return None

    async def _run_stage_e(
        self,
        alignment_report: AlignmentReport,
        result: PipelineResult,
    ) -> Optional[SemanticGraph]:
        """Run Stage E: Semantic Graph.

        Args:
            alignment_report: Stage D output
            result: Pipeline result to update

        Returns:
            SemanticGraph or None
        """
        timing = StageTiming(stage=PipelineStage.SEMANTIC_GRAPH)
        result.stage_timings.append(timing)

        try:
            build_result = self._graph_builder.build(alignment_report)

            if not build_result.is_valid:
                result.add_warning(
                    f"Graph validation issues: {len(build_result.validation.issues)}",
                    PipelineStage.SEMANTIC_GRAPH,
                )

            result.mark_stage_complete(PipelineStage.SEMANTIC_GRAPH)
            timing.complete(success=True)

            return build_result.graph

        except GraphBuildError as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Graph build failed: {e}", PipelineStage.SEMANTIC_GRAPH)
            return None

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Semantic graph failed: {e}", PipelineStage.SEMANTIC_GRAPH)
            return None

    async def _run_stage_f(
        self,
        semantic_graph: SemanticGraph,
        result: PipelineResult,
    ) -> Optional[RegenerationSpec]:
        """Run Stage F: Regeneration.

        Args:
            semantic_graph: Stage E output
            result: Pipeline result to update

        Returns:
            RegenerationSpec or None
        """
        timing = StageTiming(stage=PipelineStage.REGENERATION)
        result.stage_timings.append(timing)

        try:
            engine_result = await self._regeneration_engine.regenerate(
                semantic_graph
            )

            if not engine_result.success:
                result.add_warning(
                    f"Regeneration warnings: {engine_result.warnings}",
                    PipelineStage.REGENERATION,
                )

            result.mark_stage_complete(PipelineStage.REGENERATION)
            timing.complete(success=True)

            return engine_result.spec

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Regeneration failed: {e}", PipelineStage.REGENERATION)
            return None

    async def _run_stage_g(
        self,
        result: PipelineResult,
        options: PipelineOptions,
    ) -> Optional[Any]:
        """Run Stage G: Human Review.

        Creates review tasks for items flagged during pipeline stages
        based on confidence thresholds.

        Args:
            result: Pipeline result
            options: Pipeline options with review configuration

        Returns:
            Review summary dict or None
        """
        timing = StageTiming(stage=PipelineStage.HUMAN_REVIEW)
        result.stage_timings.append(timing)

        try:
            # Check if human review is enabled
            if not options.enable_human_review:
                result.add_warning(
                    "Human review disabled, auto-approving",
                    PipelineStage.HUMAN_REVIEW,
                )
                result.mark_stage_complete(PipelineStage.HUMAN_REVIEW)
                timing.complete(success=True)
                return None

            # Collect items needing review from semantic graph
            review_threshold = options.min_confidence_threshold
            items_for_review = self._collect_review_items(result, review_threshold)

            if not items_for_review:
                # All items passed confidence thresholds
                logger.info(
                    f"No items below threshold {review_threshold:.2f} for image {result.image_id}"
                )
                result.mark_stage_complete(PipelineStage.HUMAN_REVIEW)
                timing.complete(success=True)
                return None

            # Create and return review summary (actual queue integration is optional)
            review_summary = {
                "image_id": result.image_id,
                "items_flagged": len(items_for_review),
                "items": items_for_review,
                "threshold": review_threshold,
                "review_required": True,
            }

            logger.info(
                f"Stage G flagged {len(items_for_review)} items for review "
                f"(threshold: {review_threshold:.2f})"
            )

            result.mark_stage_complete(PipelineStage.HUMAN_REVIEW)
            timing.complete(success=True)

            return review_summary

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Human review failed: {e}", PipelineStage.HUMAN_REVIEW)
            return None

    def _collect_review_items(
        self,
        result: PipelineResult,
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """Collect items from pipeline stages that need human review.

        Args:
            result: Pipeline result containing stage outputs
            threshold: Confidence threshold below which items need review

        Returns:
            List of items requiring review with metadata
        """
        items: List[Dict[str, Any]] = []

        # Check semantic graph nodes if available
        if result.semantic_graph and result.semantic_graph.nodes:
            for node in result.semantic_graph.nodes:
                if node.confidence and node.confidence.value < threshold:
                    items.append({
                        "element_type": "semantic_node",
                        "element_id": node.id,
                        "node_type": node.node_type.value if node.node_type else "unknown",
                        "label": node.label,
                        "confidence": node.confidence.value,
                        "reason": (
                            f"Node confidence {node.confidence.value:.2f} "
                            f"below threshold {threshold:.2f}"
                        ),
                        "stage": PipelineStage.SEMANTIC_GRAPH.value,
                    })

        # Check semantic graph edges if available
        if result.semantic_graph and result.semantic_graph.edges:
            for edge in result.semantic_graph.edges:
                if edge.confidence and edge.confidence.value < threshold:
                    items.append({
                        "element_type": "semantic_edge",
                        "element_id": edge.id,
                        "edge_type": edge.edge_type.value if edge.edge_type else "unknown",
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "confidence": edge.confidence.value,
                        "reason": (
                            f"Edge confidence {edge.confidence.value:.2f} "
                            f"below threshold {threshold:.2f}"
                        ),
                        "stage": PipelineStage.SEMANTIC_GRAPH.value,
                    })

        # Check alignment report matched pairs if available
        if result.alignment_report and result.alignment_report.matched_pairs:
            for pair in result.alignment_report.matched_pairs:
                pair_confidence = getattr(pair, 'confidence', None)
                if pair_confidence:
                    conf_value = (
                        pair_confidence.value
                        if hasattr(pair_confidence, 'value')
                        else pair_confidence
                    )
                    if conf_value < threshold:
                        items.append({
                            "element_type": "aligned_pair",
                            "element_id": getattr(pair, 'id', 'unknown'),
                            "confidence": conf_value,
                            "reason": (
                                f"Alignment confidence {conf_value:.2f} "
                                f"below threshold {threshold:.2f}"
                            ),
                            "stage": PipelineStage.ALIGNMENT.value,
                        })

        return items

    async def _run_stage_h(
        self,
        result: PipelineResult,
        export_formats: List[str],
    ) -> Optional[List[Any]]:
        """Run Stage H: Export.

        Args:
            result: Pipeline result
            export_formats: List of format names

        Returns:
            List of export specs or None
        """
        timing = StageTiming(stage=PipelineStage.EXPORT)
        result.stage_timings.append(timing)

        try:
            # Convert format strings to ExportFormat enums
            formats = []
            for fmt in export_formats:
                try:
                    formats.append(ExportFormat(fmt.lower()))
                except ValueError:
                    result.add_warning(
                        f"Unknown export format: {fmt}",
                        PipelineStage.EXPORT,
                    )

            if not formats:
                formats = [ExportFormat.JSON]

            # Export regeneration spec if available
            if result.regeneration_spec:
                exports = await self._export_engine.export_async(
                    result.regeneration_spec,
                    formats,
                )
            else:
                # Export what we have
                exports = []

            result.mark_stage_complete(PipelineStage.EXPORT)
            timing.complete(success=True)

            return exports

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Export failed: {e}", PipelineStage.EXPORT)
            return None

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def reset_stats(self) -> None:
        """Reset pipeline statistics."""
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_time_ms": 0.0,
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_pipeline(
    ingestion_config: Optional[IngestionConfig] = None,
    alignment_config: Optional[AlignmentEngineConfig] = None,
    graph_config: Optional[SemanticGraphConfig] = None,
    regeneration_config: Optional[RegenerationConfig] = None,
    export_config: Optional[ExportEngineConfig] = None,
    mathpix_config: Optional[MathpixConfig] = None,
    yolo_config: Optional[YOLOConfig] = None,
    interpretation_config: Optional[InterpretationConfig] = None,
    merger_config: Optional[MergerConfig] = None,
) -> MathpixPipeline:
    """Factory function to create MathpixPipeline.

    Args:
        ingestion_config: Configuration for Stage A
        alignment_config: Configuration for Stage D
        graph_config: Configuration for Stage E
        regeneration_config: Configuration for Stage F
        export_config: Configuration for Stage H
        mathpix_config: Configuration for Stage B (Mathpix API)
        yolo_config: Configuration for Stage C YOLO detection
        interpretation_config: Configuration for Stage C Claude interpretation
        merger_config: Configuration for Stage C hybrid merging

    Returns:
        Configured MathpixPipeline instance
    """
    return MathpixPipeline(
        ingestion_config=ingestion_config,
        alignment_config=alignment_config,
        graph_config=graph_config,
        regeneration_config=regeneration_config,
        export_config=export_config,
        mathpix_config=mathpix_config,
        yolo_config=yolo_config,
        interpretation_config=interpretation_config,
        merger_config=merger_config,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "MathpixPipeline",
    "PipelineError",
    "IngestionConfig",
    "SemanticGraphConfig",
    "MathpixConfig",
    "YOLOConfig",
    "InterpretationConfig",
    "MergerConfig",
    "create_pipeline",
]
