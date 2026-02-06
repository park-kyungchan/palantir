"""
COW CLI - Pipeline Processor

Integrates Mathpix API client, preprocessing, and Layout/Content separation.

Pipeline Stages:
- Stage A: Image preprocessing (validation, deduplication)
- Stage B: Mathpix API processing (OCR)
- Stage C0: Layout/Content separation
"""
from typing import Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio

from cow_cli.mathpix.client import MathpixClient
from cow_cli.mathpix.schemas import MathpixRequest, MathpixResponse
from cow_cli.mathpix.exceptions import MathpixError
from cow_cli.preprocessing.validator import ImageValidator, ValidationResult
from cow_cli.preprocessing.deduplicator import ImageDeduplicator, DeduplicationResult
from cow_cli.semantic.separator import LayoutContentSeparator, SeparationError
from cow_cli.semantic.schemas import SeparatedDocument

logger = logging.getLogger("cow-cli.pipeline")


class PipelineError(Exception):
    """Error during pipeline processing."""

    def __init__(
        self,
        message: str,
        stage: str,
        image_path: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.stage = stage
        self.image_path = image_path
        self.cause = cause


@dataclass
class StageResult:
    """Result of a single pipeline stage."""

    stage: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class PipelineResult:
    """Complete pipeline processing result."""

    image_path: str
    success: bool
    document: Optional[SeparatedDocument] = None
    mathpix_response: Optional[MathpixResponse] = None
    stages: list[StageResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    error: Optional[str] = None

    @property
    def stage_a_result(self) -> Optional[StageResult]:
        """Get Stage A (preprocessing) result."""
        return next((s for s in self.stages if s.stage == "A"), None)

    @property
    def stage_b_result(self) -> Optional[StageResult]:
        """Get Stage B (Mathpix) result."""
        return next((s for s in self.stages if s.stage == "B"), None)

    @property
    def stage_c0_result(self) -> Optional[StageResult]:
        """Get Stage C0 (separation) result."""
        return next((s for s in self.stages if s.stage == "C0"), None)


class PipelineProcessor:
    """
    Main pipeline processor for COW CLI.

    Orchestrates the full processing pipeline:
    Stage A → Stage B → Stage C0

    Example:
        processor = PipelineProcessor()
        result = await processor.process("image.png")

        if result.success:
            doc = result.document
            print(f"Layout elements: {len(doc.layout.elements)}")
            print(f"Content elements: {len(doc.content.elements)}")
    """

    def __init__(
        self,
        mathpix_client: Optional[MathpixClient] = None,
        validator: Optional[ImageValidator] = None,
        deduplicator: Optional[ImageDeduplicator] = None,
        separator: Optional[LayoutContentSeparator] = None,
        skip_validation: bool = False,
        skip_deduplication: bool = False,
        strict_separation: bool = False,
    ):
        """
        Initialize pipeline processor.

        Args:
            mathpix_client: Optional custom Mathpix client
            validator: Optional custom image validator
            deduplicator: Optional custom deduplicator
            separator: Optional custom separator
            skip_validation: Skip Stage A validation
            skip_deduplication: Skip Stage A deduplication
            strict_separation: Enable strict mode in separator
        """
        self.mathpix_client = mathpix_client
        self.validator = validator or ImageValidator()
        self.deduplicator = deduplicator or ImageDeduplicator()
        self.separator = separator or LayoutContentSeparator(strict=strict_separation)

        self.skip_validation = skip_validation
        self.skip_deduplication = skip_deduplication

    async def process(
        self,
        image_path: str | Path,
        mathpix_options: Optional[dict] = None,
        output_dir: Optional[Path] = None,
    ) -> PipelineResult:
        """
        Process a single image through the full pipeline.

        Args:
            image_path: Path to the image file
            mathpix_options: Optional Mathpix API options override
            output_dir: Optional directory to save outputs

        Returns:
            PipelineResult with separated document
        """
        image_path = Path(image_path)
        start_time = datetime.now()
        stages: list[StageResult] = []

        try:
            # Stage A: Preprocessing
            stage_a = await self._stage_a_preprocess(image_path)
            stages.append(stage_a)

            if not stage_a.success:
                return PipelineResult(
                    image_path=str(image_path),
                    success=False,
                    stages=stages,
                    error=f"Stage A failed: {stage_a.error}",
                )

            # Stage B: Mathpix API
            stage_b = await self._stage_b_mathpix(
                image_path, mathpix_options or {}
            )
            stages.append(stage_b)

            if not stage_b.success:
                return PipelineResult(
                    image_path=str(image_path),
                    success=False,
                    stages=stages,
                    error=f"Stage B failed: {stage_b.error}",
                )

            mathpix_response: MathpixResponse = stage_b.data

            # Stage C0: Layout/Content Separation
            stage_c0 = self._stage_c0_separate(
                mathpix_response, str(image_path)
            )
            stages.append(stage_c0)

            if not stage_c0.success:
                return PipelineResult(
                    image_path=str(image_path),
                    success=False,
                    mathpix_response=mathpix_response,
                    stages=stages,
                    error=f"Stage C0 failed: {stage_c0.error}",
                )

            document: SeparatedDocument = stage_c0.data

            # Save outputs if requested
            if output_dir:
                self._save_outputs(document, output_dir)

            total_duration = (datetime.now() - start_time).total_seconds() * 1000

            return PipelineResult(
                image_path=str(image_path),
                success=True,
                document=document,
                mathpix_response=mathpix_response,
                stages=stages,
                total_duration_ms=total_duration,
            )

        except Exception as e:
            logger.exception(f"Pipeline error for {image_path}")
            total_duration = (datetime.now() - start_time).total_seconds() * 1000

            return PipelineResult(
                image_path=str(image_path),
                success=False,
                stages=stages,
                total_duration_ms=total_duration,
                error=str(e),
            )

    async def _stage_a_preprocess(self, image_path: Path) -> StageResult:
        """Stage A: Image preprocessing and validation."""
        start_time = datetime.now()

        try:
            if not self.skip_validation:
                validation = self.validator.validate(image_path)
                if not validation.valid:
                    return StageResult(
                        stage="A",
                        success=False,
                        error=f"Validation failed: {validation.errors}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return StageResult(
                stage="A",
                success=True,
                data={"validated": True},
                duration_ms=duration_ms,
            )

        except Exception as e:
            return StageResult(
                stage="A",
                success=False,
                error=str(e),
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    async def _stage_b_mathpix(
        self,
        image_path: Path,
        options: dict,
    ) -> StageResult:
        """Stage B: Mathpix API processing."""
        start_time = datetime.now()

        try:
            if not self.mathpix_client:
                # Create default client
                self.mathpix_client = MathpixClient()

            response = await self.mathpix_client.process_image(
                image=image_path,
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return StageResult(
                stage="B",
                success=True,
                data=response,
                duration_ms=duration_ms,
            )

        except MathpixError as e:
            return StageResult(
                stage="B",
                success=False,
                error=str(e),
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )
        except Exception as e:
            return StageResult(
                stage="B",
                success=False,
                error=f"Mathpix error: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    def _stage_c0_separate(
        self,
        mathpix_response: MathpixResponse,
        image_path: str,
    ) -> StageResult:
        """Stage C0: Layout/Content separation."""
        start_time = datetime.now()

        try:
            # Convert MathpixResponse to dict for separator
            response_dict = mathpix_response.model_dump()

            document = self.separator.separate(
                stage_b_output=response_dict,
                image_path=image_path,
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return StageResult(
                stage="C0",
                success=True,
                data=document,
                duration_ms=duration_ms,
            )

        except SeparationError as e:
            return StageResult(
                stage="C0",
                success=False,
                error=str(e),
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )
        except Exception as e:
            return StageResult(
                stage="C0",
                success=False,
                error=f"Separation error: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    def _save_outputs(self, document: SeparatedDocument, output_dir: Path) -> None:
        """Save separated document to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        self.separator.save_document(document, output_dir)
        logger.info(f"Saved outputs to {output_dir}")


async def process_image(
    image_path: str | Path,
    mathpix_options: Optional[dict] = None,
    output_dir: Optional[Path] = None,
    skip_validation: bool = False,
) -> PipelineResult:
    """
    Convenience function to process a single image.

    Args:
        image_path: Path to image file
        mathpix_options: Optional Mathpix API options
        output_dir: Optional output directory
        skip_validation: Skip image validation

    Returns:
        PipelineResult with separated document
    """
    processor = PipelineProcessor(skip_validation=skip_validation)
    return await processor.process(image_path, mathpix_options, output_dir)


async def process_batch(
    image_paths: list[str | Path],
    mathpix_options: Optional[dict] = None,
    output_dir: Optional[Path] = None,
    skip_validation: bool = False,
    skip_deduplication: bool = False,
    max_concurrent: int = 5,
) -> list[PipelineResult]:
    """
    Process multiple images in batch with optional deduplication.

    Args:
        image_paths: List of image paths
        mathpix_options: Optional Mathpix API options
        output_dir: Optional output directory (per-image subdirs created)
        skip_validation: Skip image validation
        skip_deduplication: Skip deduplication check
        max_concurrent: Maximum concurrent API calls

    Returns:
        List of PipelineResult for each image
    """
    processor = PipelineProcessor(
        skip_validation=skip_validation,
        skip_deduplication=skip_deduplication,
    )

    # Deduplication check
    paths_to_process = image_paths
    if not skip_deduplication:
        dedup_result = processor.deduplicator.find_duplicates(
            [Path(p) for p in image_paths]
        )
        paths_to_process = [str(p) for p in dedup_result.unique_images]
        if dedup_result.duplicates:
            logger.info(f"Skipping {len(dedup_result.duplicates)} duplicate images")

    # Process with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(path: str) -> PipelineResult:
        async with semaphore:
            img_output_dir = None
            if output_dir:
                img_output_dir = output_dir / Path(path).stem
            return await processor.process(path, mathpix_options, img_output_dir)

    tasks = [process_with_limit(p) for p in paths_to_process]
    results = await asyncio.gather(*tasks)

    return list(results)


__all__ = [
    "PipelineProcessor",
    "PipelineResult",
    "PipelineError",
    "StageResult",
    "process_image",
    "process_batch",
]
