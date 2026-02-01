"""
MathpixPipeline: Full Pipeline Orchestrator for Math Image Parsing.

Coordinates all 8 stages of the pipeline:
    A. Ingestion → B. TextParse → C. VisionParse → D. Alignment
                                                        ↓
    H. Export ← G. HumanReview ← F. Regeneration ← E. SemanticGraph

All stages now use BaseStage wrappers (v1.6.0) for standardized:
- Timing and metrics collection
- Input validation
- Error handling and recovery

Module Version: 1.6.0
"""

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..schemas.common import PipelineStage
from ..schemas.pipeline import (
    PipelineOptions,
    PipelineResult,
)
from ..schemas.ingestion import IngestionSpec
from ..schemas.text_spec import TextSpec
from ..schemas.vision_spec import VisionSpec
from ..schemas.alignment import AlignmentReport
from ..schemas.semantic_graph import SemanticGraph
from ..schemas.regeneration import RegenerationSpec
from ..schemas.export import ExportFormat

# Validators
from ..validators import StageTransitionValidator

# Stage A: Ingestion
from ..ingestion import (
    ImageLoader,
    ImageValidator,
    Preprocessor,
    StorageManager,
    IngestionError,
)

# Stage D: Alignment
from ..alignment import AlignmentEngine, AlignmentEngineConfig

# Stage E: Semantic Graph
from ..semantic_graph import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    GraphBuildError,
)

# Stage F: Regeneration
from ..regeneration import (
    RegenerationEngine,
    RegenerationConfig,
)

# Stage H: Export
from ..export import (
    ExportEngine,
    ExportEngineConfig,
)

# Stage B: Text Parse
from ..clients.mathpix import MathpixClient, MathpixConfig, MathpixError

# Configuration (reuse from config.py to avoid duplication)
from ..config import IngestionConfig, SemanticGraphConfig

# Modular Pipeline Components (v1.1.0)
from .exceptions import PipelineError
from .stage_runners import StageRunnerMixin

# Stage C: Vision Parse
# Note: VisionParseStage uses GeminiVisionClient internally (v3.0.0 migration)
# Legacy YOLO/Claude config imports removed - use VisionParseStageConfig

# Modular Stage Implementations (v1.6.0)
from ..stages import (
    StageResult,
    IngestionStage,
    IngestionStageConfig,
    VisionParseStage,
    VisionParseStageConfig,
    SemanticGraphStage,
    SemanticGraphStageConfig,
    # Stage B: Text Parse (v1.6.0)
    TextParseStage,
    TextParseStageConfig,
    # Stage D: Alignment (v1.6.0)
    AlignmentStage,
    AlignmentStageConfig,
    AlignmentInput,
    # Stage F: Regeneration (v1.6.0)
    RegenerationStage,
    RegenerationStageConfig,
    # Stage G: Human Review (v1.6.0)
    HumanReviewStage,
    HumanReviewStageConfig,
    HumanReviewInput,
    ReviewSummary,
    # Stage H: Export (v1.6.0)
    ExportStage,
    ExportStageConfig,
)

logger = logging.getLogger(__name__)


# =============================================================================
# MathpixPipeline
# =============================================================================

class MathpixPipeline(StageRunnerMixin):
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
        vision_config: Optional[VisionParseStageConfig] = None,
    ):
        """Initialize MathpixPipeline.

        Args:
            ingestion_config: Configuration for Stage A
            alignment_config: Configuration for Stage D
            graph_config: Configuration for Stage E
            regeneration_config: Configuration for Stage F
            export_config: Configuration for Stage H
            mathpix_config: Configuration for Stage B (Mathpix API)
            vision_config: Configuration for Stage C (Gemini Vision)
        """
        self.ingestion_config = ingestion_config or IngestionConfig()
        self.alignment_config = alignment_config or AlignmentEngineConfig()
        self.graph_config = graph_config or SemanticGraphConfig()
        self.regeneration_config = regeneration_config or RegenerationConfig()
        self.export_config = export_config or ExportEngineConfig()
        self.mathpix_config = mathpix_config
        self.vision_config = vision_config

        # Initialize stage components
        self._init_components()

        # Initialize validator
        self._validator = StageTransitionValidator()

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

        # =====================================================================
        # Modular Stage Implementations (v1.6.0)
        # These wrap existing components in BaseStage interface for
        # standardized timing, validation, and metrics collection.
        # =====================================================================

        # Stage A: Ingestion (v1.6.0)
        self._ingestion_stage = IngestionStage(
            config=IngestionStageConfig(
                enable_preprocessing=self.ingestion_config.enable_preprocessing,
                preprocessing_operations=self.ingestion_config.preprocessing_operations,
            ),
            image_loader=self._image_loader,
            image_validator=self._image_validator,
            preprocessor=self._preprocessor,
        )

        # Stage B: Text Parse
        self._text_parse_stage = TextParseStage(
            config=TextParseStageConfig(
                mathpix_config=self.mathpix_config,
                require_stored_path=False,  # Allow source_path fallback
            ),
        )

        # Stage D: Alignment
        self._alignment_stage = AlignmentStage(
            config=AlignmentStageConfig(
                base_alignment_threshold=self.alignment_config.base_alignment_threshold,
                base_inconsistency_threshold=self.alignment_config.base_inconsistency_threshold,
                enable_threshold_adjustment=self.alignment_config.enable_threshold_adjustment,
                enable_auto_fix_detection=self.alignment_config.enable_auto_fix_detection,
            ),
            engine=self._alignment_engine,  # Reuse existing engine
        )

        # Stage E: Semantic Graph
        self._semantic_graph_stage = SemanticGraphStage(
            config=SemanticGraphStageConfig(
                node_threshold=self.graph_config.node_threshold,
                edge_threshold=self.graph_config.edge_threshold,
                strict_validation=False,
            ),
            builder=self._graph_builder,  # Reuse existing builder
        )

        # Stage F: Regeneration
        self._regeneration_stage = RegenerationStage(
            config=RegenerationStageConfig(
                output_formats=["latex", "svg"],
                enable_delta_comparison=True,
            ),
            engine=self._regeneration_engine,  # Reuse existing engine
        )

        # Stage C: Vision Parse (v3.0.0 - Gemini-only)
        self._vision_parse_stage = VisionParseStage(
            config=self.vision_config or VisionParseStageConfig(),
        )

        # Stage G: Human Review
        self._human_review_stage = HumanReviewStage(
            config=HumanReviewStageConfig(
                enable_dynamic_thresholds=True,
            ),
        )

        # Stage H: Export
        self._export_stage = ExportStage(
            config=ExportStageConfig(
                parallel_exports=True,
            ),
            engine=self._export_engine,  # Reuse existing engine
        )

    def _apply_stage_result(
        self,
        stage_result: StageResult,
        pipeline_result: PipelineResult,
        stage: PipelineStage,
    ) -> None:
        """Apply StageResult to PipelineResult.

        Helper method for integrating modular stages with pipeline.

        Args:
            stage_result: Result from BaseStage.run_async()
            pipeline_result: Pipeline result to update
            stage: Pipeline stage identifier
        """
        # Copy timing
        if stage_result.timing:
            pipeline_result.stage_timings.append(stage_result.timing)

        # Copy warnings
        for warning in stage_result.warnings:
            pipeline_result.add_warning(warning, stage)

        # Copy errors
        for error in stage_result.errors:
            pipeline_result.add_error(error, stage)

        # Mark complete if successful
        if stage_result.is_valid:
            pipeline_result.mark_stage_complete(stage)

    @property
    def stats(self) -> dict:
        """Get pipeline statistics."""
        return self._stats.copy()

    def _generate_image_id(self) -> str:
        """Generate unique image identifier."""
        return f"img_{uuid.uuid4().hex[:12]}"

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
                self._validator.validate_transition(
                    "A", "B", result.ingestion_spec, result
                )
                result.text_spec = await self._run_stage_b(
                    result.ingestion_spec, result
                )

            # Stage C: Vision Parse (YOLO + Claude with Gemini fallback)
            if not options.should_skip(PipelineStage.VISION_PARSE):
                # Validate A -> C transition
                self._validator.validate_transition(
                    "A", "C", result.ingestion_spec, result
                )
                result.vision_spec = await self._run_stage_c(
                    result.ingestion_spec, result.text_spec, result
                )

            # Stage D: Alignment
            if not options.should_skip(PipelineStage.ALIGNMENT):
                if result.text_spec and result.vision_spec:
                    # Validate B -> D transition (text to alignment)
                    self._validator.validate_transition(
                        "B", "D", result.text_spec, result
                    )
                    # Validate C -> D transition (vision to alignment)
                    self._validator.validate_transition(
                        "C", "D", result.vision_spec, result
                    )
                    result.alignment_report = await self._run_stage_d(
                        result.text_spec, result.vision_spec, result
                    )

            # Stage E: Semantic Graph
            if not options.should_skip(PipelineStage.SEMANTIC_GRAPH):
                if result.alignment_report:
                    # Validate D -> E transition
                    self._validator.validate_transition(
                        "D", "E", result.alignment_report, result
                    )
                    result.semantic_graph = await self._run_stage_e(
                        result.alignment_report, result
                    )

            # Stage F: Regeneration
            if not options.should_skip(PipelineStage.REGENERATION):
                if result.semantic_graph:
                    # Validate E -> F transition
                    self._validator.validate_transition(
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
    vision_config: Optional[VisionParseStageConfig] = None,
) -> MathpixPipeline:
    """Factory function to create MathpixPipeline.

    Args:
        ingestion_config: Configuration for Stage A
        alignment_config: Configuration for Stage D
        graph_config: Configuration for Stage E
        regeneration_config: Configuration for Stage F
        export_config: Configuration for Stage H
        mathpix_config: Configuration for Stage B (Mathpix API)
        vision_config: Configuration for Stage C (Gemini Vision)

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
        vision_config=vision_config,
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
    "VisionParseStageConfig",
    "create_pipeline",
]
