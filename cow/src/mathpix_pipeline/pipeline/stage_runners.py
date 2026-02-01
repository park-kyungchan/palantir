"""
Stage Runners - Modular Stage Execution Methods.

Extracted from pipeline.py to improve modularity.
Contains all 8 stage runner methods (A-H) as a mixin class.

Module Version: 1.0.0
"""

import logging
from pathlib import Path
from typing import Any, List, Optional, Union

from ..schemas.common import PipelineStage
from ..schemas.pipeline import PipelineResult
from ..schemas.ingestion import IngestionSpec
from ..schemas.text_spec import TextSpec
from ..schemas.vision_spec import VisionSpec
from ..schemas.alignment import AlignmentReport
from ..schemas.semantic_graph import SemanticGraph
from ..schemas.regeneration import RegenerationSpec
from ..schemas.export import ExportFormat

from ..stages import (
    StageResult,
    AlignmentInput,
    HumanReviewInput,
    ReviewSummary,
)

from .exceptions import PipelineError

logger = logging.getLogger(__name__)


class StageRunnerMixin:
    """Mixin class providing stage runner methods for MathpixPipeline.

    This mixin contains all 8 stage runner methods (_run_stage_a through _run_stage_h)
    extracted from the main pipeline class for better modularity.

    Note: This mixin requires the following attributes on the host class:
        - _ingestion_stage: IngestionStage instance
        - _text_parse_stage: TextParseStage instance
        - _vision_parse_stage: VisionParseStage instance
        - _alignment_stage: AlignmentStage instance
        - _semantic_graph_stage: SemanticGraphStage instance
        - _regeneration_stage: RegenerationStage instance
        - _human_review_stage: HumanReviewStage instance
        - _export_stage: ExportStage instance
        - _apply_stage_result: Method to apply StageResult to PipelineResult
    """

    # =========================================================================
    # Stage A: Ingestion
    # =========================================================================

    async def _run_stage_a(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
        result: PipelineResult,
    ) -> Optional[IngestionSpec]:
        """Run Stage A: Ingestion.

        Uses modular IngestionStage (v1.6.0) for standardized
        timing, validation, and metrics collection.

        Args:
            image: Image input (path, URL, or bytes)
            image_id: Image identifier
            result: Pipeline result to update

        Returns:
            IngestionSpec or None if ingestion fails
        """
        # Use modular stage implementation
        stage_result = await self._ingestion_stage.run_async(
            image,
            image_id=image_id,
        )

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.INGESTION,
        )

        if not stage_result.is_valid:
            raise PipelineError(
                f"Ingestion failed: {stage_result.errors}",
                stage=PipelineStage.INGESTION,
            )

        if stage_result.output:
            logger.info(
                f"Stage A completed: image_id={stage_result.output.image_id}"
            )

        return stage_result.output

    # =========================================================================
    # Stage B: Text Parse
    # =========================================================================

    async def _run_stage_b(
        self,
        ingestion_spec: Optional[IngestionSpec],
        result: PipelineResult,
    ) -> Optional[TextSpec]:
        """Run Stage B: Text Parse using Mathpix API.

        Uses modular TextParseStage (v1.6.0) for standardized
        timing, validation, and metrics collection.

        Args:
            ingestion_spec: Stage A output with image data
            result: Pipeline result to update

        Returns:
            TextSpec with extracted text elements
        """
        if not ingestion_spec:
            result.add_warning(
                "Skipping text parse: no ingestion spec",
                PipelineStage.TEXT_PARSE,
            )
            return None

        # Use modular stage implementation
        stage_result = await self._text_parse_stage.run_async(ingestion_spec)

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.TEXT_PARSE,
        )

        if stage_result.output:
            logger.info(
                f"Stage B completed: {len(stage_result.output.equations)} equations, "
                f"{len(stage_result.output.line_segments)} line segments"
            )

        return stage_result.output

    # =========================================================================
    # Stage C: Vision Parse
    # =========================================================================

    async def _run_stage_c(
        self,
        ingestion_spec: Optional[IngestionSpec],
        text_spec: Optional[TextSpec],
        result: PipelineResult,
    ) -> Optional[VisionSpec]:
        """Run Stage C: Vision Parse.

        Uses modular VisionParseStage (v1.6.0) for standardized
        timing, validation, and metrics collection.

        The VisionParseStage handles:
        - 3-tier fallback chain (YOLO+Claude -> Gemini -> Manual)
        - Image source resolution from IngestionSpec
        - Detection + interpretation + merging

        Args:
            ingestion_spec: Stage A output with image data
            text_spec: Stage B output (may contain vision_parse_triggers)
            result: Pipeline result to update

        Returns:
            VisionSpec with visual elements and relations
        """
        if not ingestion_spec:
            result.add_warning(
                "Skipping vision parse: no ingestion spec",
                PipelineStage.VISION_PARSE,
            )
            return None

        # Check if vision parse is needed based on Stage B triggers
        if text_spec and hasattr(text_spec, 'vision_parse_triggers'):
            if not text_spec.vision_parse_triggers:
                logger.info("Stage C skipped: no vision parse triggers from Stage B")
                result.mark_stage_complete(PipelineStage.VISION_PARSE)
                return None

        # Use modular stage implementation
        stage_result = await self._vision_parse_stage.run_async(ingestion_spec)

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.VISION_PARSE,
        )

        if stage_result.output:
            merged_count = 0
            if stage_result.output.merged_output:
                merged_count = len(stage_result.output.merged_output.elements)
            logger.info(f"Stage C completed: {merged_count} merged elements")

        return stage_result.output

    # =========================================================================
    # Stage D: Alignment
    # =========================================================================

    async def _run_stage_d(
        self,
        text_spec: TextSpec,
        vision_spec: VisionSpec,
        result: PipelineResult,
    ) -> Optional[AlignmentReport]:
        """Run Stage D: Alignment.

        Uses modular AlignmentStage (v1.6.0) for standardized
        timing, validation, and metrics collection.

        Args:
            text_spec: Stage B output
            vision_spec: Stage C output
            result: Pipeline result to update

        Returns:
            AlignmentReport or None
        """
        # Create composite input for alignment stage
        alignment_input = AlignmentInput(
            text_spec=text_spec,
            vision_spec=vision_spec,
        )

        # Use modular stage implementation
        stage_result = await self._alignment_stage.run_async(alignment_input)

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.ALIGNMENT,
        )

        return stage_result.output

    # =========================================================================
    # Stage E: Semantic Graph
    # =========================================================================

    async def _run_stage_e(
        self,
        alignment_report: AlignmentReport,
        result: PipelineResult,
    ) -> Optional[SemanticGraph]:
        """Run Stage E: Semantic Graph.

        Uses modular SemanticGraphStage (v1.1.0) for standardized
        timing, validation, and metrics collection.

        Args:
            alignment_report: Stage D output
            result: Pipeline result to update

        Returns:
            SemanticGraph or None
        """
        # Use modular stage implementation
        stage_result = await self._semantic_graph_stage.run_async(alignment_report)

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.SEMANTIC_GRAPH,
        )

        return stage_result.output

    # =========================================================================
    # Stage F: Regeneration
    # =========================================================================

    async def _run_stage_f(
        self,
        semantic_graph: SemanticGraph,
        result: PipelineResult,
    ) -> Optional[RegenerationSpec]:
        """Run Stage F: Regeneration.

        Uses modular RegenerationStage (v1.6.0) for standardized
        timing, validation, and metrics collection.

        Args:
            semantic_graph: Stage E output
            result: Pipeline result to update

        Returns:
            RegenerationSpec or None
        """
        # Use modular stage implementation
        stage_result = await self._regeneration_stage.run_async(semantic_graph)

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.REGENERATION,
        )

        return stage_result.output

    # =========================================================================
    # Stage G: Human Review
    # =========================================================================

    async def _run_stage_g(
        self,
        result: PipelineResult,
        options: "PipelineOptions",
    ) -> Optional[ReviewSummary]:
        """Run Stage G: Human Review.

        Uses modular HumanReviewStage (v1.6.0) for standardized
        timing, validation, and metrics collection.

        Args:
            result: Pipeline result
            options: Pipeline options with review configuration

        Returns:
            ReviewSummary or None
        """
        # Check if human review is enabled
        if not options.enable_human_review:
            result.add_warning(
                "Human review disabled, auto-approving",
                PipelineStage.HUMAN_REVIEW,
            )
            result.mark_stage_complete(PipelineStage.HUMAN_REVIEW)
            return None

        # Create composite input for human review stage
        review_input = HumanReviewInput(
            pipeline_result=result,
        )

        # Use modular stage implementation
        stage_result = await self._human_review_stage.run_async(review_input)

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.HUMAN_REVIEW,
        )

        if stage_result.output:
            logger.info(
                f"Stage G flagged {stage_result.output.tasks_created} items for review"
            )

        return stage_result.output

    # =========================================================================
    # Stage H: Export
    # =========================================================================

    async def _run_stage_h(
        self,
        result: PipelineResult,
        export_formats: List[str],
    ) -> Optional[List[Any]]:
        """Run Stage H: Export.

        Uses modular ExportStage (v1.6.0) for standardized
        timing, validation, and metrics collection.

        Args:
            result: Pipeline result
            export_formats: List of format names

        Returns:
            List of export specs or None
        """
        if not result.regeneration_spec:
            result.add_warning(
                "Skipping export: no regeneration spec",
                PipelineStage.EXPORT,
            )
            return None

        # Update export stage config with requested formats
        formats = []
        for fmt in export_formats:
            try:
                formats.append(ExportFormat(fmt.lower()))
            except ValueError:
                result.add_warning(
                    f"Unknown export format: {fmt}",
                    PipelineStage.EXPORT,
                )

        if formats:
            self._export_stage.config.export_formats = formats

        # Use modular stage implementation
        stage_result = await self._export_stage.run_async(result.regeneration_spec)

        # Apply stage result to pipeline result
        self._apply_stage_result(
            stage_result,
            result,
            PipelineStage.EXPORT,
        )

        return stage_result.output
