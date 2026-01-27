"""
Stage H: Export Stage.

Wraps ExportEngine to convert RegenerationSpec into multiple export formats.
Supports parallel and sequential export modes with comprehensive validation.

Module Version: 1.0.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from ..schemas.common import PipelineStage
from ..schemas.regeneration import RegenerationSpec
from ..schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportSpec,
)
from ..export.engine import (
    ExportEngine,
    ExportEngineConfig,
)
from ..export.exceptions import ExporterError, ExportPipelineError
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
class ExportStageConfig:
    """Configuration for Stage H export.

    Attributes:
        export_formats: List of formats to export (default: PDF, JSON)
        output_dir: Output directory for exported files
        parallel_exports: Enable parallel export execution
        max_concurrent: Maximum concurrent exports
        include_metadata: Include pipeline metadata in exports
        compress: Compress output files
    """
    export_formats: List[ExportFormat] = field(default_factory=lambda: [
        ExportFormat.PDF, ExportFormat.JSON
    ])
    output_dir: Optional[Path] = None
    parallel_exports: bool = True
    max_concurrent: int = 4
    include_metadata: bool = True
    compress: bool = False

    def to_engine_config(self) -> ExportEngineConfig:
        """Convert to ExportEngineConfig for ExportEngine."""
        return ExportEngineConfig(
            output_dir=self.output_dir or Path("./exports"),
            parallel_exports=self.parallel_exports,
            max_concurrent=self.max_concurrent,
            default_formats=self.export_formats,
        )


# =============================================================================
# Stage Implementation
# =============================================================================

class ExportStage(BaseStage[RegenerationSpec, List[ExportSpec]]):
    """Stage H: Multi-format Export.

    Converts RegenerationSpec into multiple export formats through:
    1. Format validation and selection
    2. Parallel or sequential export execution
    3. File storage and checksum generation
    4. Export specification generation

    Supports v2.0.0 multi-format output:
    - ExportFormat.PDF: PDF document export
    - ExportFormat.JSON: JSON data export
    - ExportFormat.LATEX: LaTeX source export
    - ExportFormat.SVG: SVG vector graphics export
    - ExportFormat.DOCX: Word document export
    - ExportFormat.PNG: PNG image export

    Example:
        stage = ExportStage(config=ExportStageConfig(
            export_formats=[ExportFormat.PDF, ExportFormat.JSON],
            parallel_exports=True,
        ))
        result = await stage.run_async(regeneration_spec)
        if result.is_valid:
            specs = result.output
            for spec in specs:
                print(f"Exported: {spec.file_path} ({spec.format.value})")
    """

    def __init__(
        self,
        config: Optional[ExportStageConfig] = None,
        engine: Optional[ExportEngine] = None,
    ):
        """Initialize export stage.

        Args:
            config: Stage configuration
            engine: Custom engine (created from config if not provided)
        """
        super().__init__(config or ExportStageConfig())

        if engine:
            self._engine = engine
        else:
            self._engine = ExportEngine(
                config=self.config.to_engine_config()
            )

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage H identifier."""
        return PipelineStage.EXPORT

    @property
    def config(self) -> ExportStageConfig:
        """Return typed configuration."""
        return self._config

    @property
    def engine(self) -> ExportEngine:
        """Return the underlying export engine."""
        return self._engine

    def validate(self, input_data: RegenerationSpec) -> ValidationResult:
        """Validate regeneration spec input.

        Args:
            input_data: RegenerationSpec to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        if input_data is None:
            result.add_error("RegenerationSpec is required")
            return result

        # Check for image_id
        if not input_data.image_id:
            result.add_error("RegenerationSpec must have an image_id")
            return result

        # Check for outputs to export
        if not input_data.outputs:
            result.add_error("RegenerationSpec must have at least one output to export")
            return result

        # Check for minimum overall confidence
        if input_data.overall_confidence < 0.3:
            result.add_warning(
                f"Low regeneration confidence: {input_data.overall_confidence:.2f}"
            )

        # Check for failed elements
        if input_data.total_elements_failed > 0:
            result.add_warning(
                f"{input_data.total_elements_failed} elements failed regeneration"
            )

        # Check for review required
        if input_data.review.review_required:
            result.add_warning(
                f"Regeneration flagged for review: {input_data.review.review_reason}"
            )

        # Validate export formats
        supported_formats = self._engine.get_supported_formats()
        for fmt in self.config.export_formats:
            if fmt not in supported_formats:
                result.add_warning(
                    f"Export format '{fmt.value}' may not be fully supported"
                )

        return result

    async def _execute_async(
        self,
        input_data: RegenerationSpec,
        export_options: Optional[ExportOptions] = None,
        **kwargs: Any,
    ) -> List[ExportSpec]:
        """Execute export from regeneration spec.

        Args:
            input_data: RegenerationSpec from Stage F
            export_options: Optional export configuration
            **kwargs: Additional parameters

        Returns:
            List of ExportSpec for each format

        Raises:
            StageExecutionError: If export fails
        """
        try:
            # Create export options with config settings
            if export_options is None:
                export_options = ExportOptions(
                    include_metadata=self.config.include_metadata,
                    compress=self.config.compress,
                )

            # Choose export method based on parallel setting
            if self.config.parallel_exports and len(self.config.export_formats) > 1:
                # Parallel export
                export_specs = await self._engine.export_async(
                    pipeline_result=input_data,
                    formats=self.config.export_formats,
                    options=export_options,
                )
            else:
                # Sequential export
                export_specs = self._engine.export(
                    pipeline_result=input_data,
                    formats=self.config.export_formats,
                    options=export_options,
                )

            return export_specs

        except ExportPipelineError as e:
            raise StageExecutionError(
                message=str(e),
                stage=self.stage_name,
                cause=e,
            )
        except ExporterError as e:
            raise StageExecutionError(
                message=f"Exporter error: {e}",
                stage=self.stage_name,
                cause=e,
            )
        except Exception as e:
            raise StageExecutionError(
                message=f"Export failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: List[ExportSpec]) -> StageMetrics:
        """Collect export metrics.

        Args:
            output: List of ExportSpec from execution

        Returns:
            StageMetrics with export statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None and len(output) > 0,
        )

        if output:
            metrics.elements_processed = len(output)

            # Calculate total file size
            total_size = sum(spec.file_size for spec in output)

            # Collect format-specific metrics
            formats_exported = [spec.format.value for spec in output]
            avg_confidence = sum(spec.confidence for spec in output) / len(output)

            metrics.custom_metrics = {
                "formats_exported": formats_exported,
                "format_count": len(output),
                "total_file_size_bytes": total_size,
                "average_confidence": avg_confidence,
                "parallel_mode": self.config.parallel_exports,
            }

            # Add per-format metrics
            for spec in output:
                metrics.custom_metrics[f"{spec.format.value}_size_bytes"] = spec.file_size
                metrics.custom_metrics[f"{spec.format.value}_confidence"] = spec.confidence

            # Check for compressed exports
            compressed_count = sum(1 for spec in output if spec.compressed)
            if compressed_count > 0:
                metrics.custom_metrics["compressed_exports"] = compressed_count

        return metrics


# =============================================================================
# Factory Function
# =============================================================================

def create_export_stage(
    config: Optional[ExportStageConfig] = None,
    **kwargs,
) -> ExportStage:
    """Factory function to create ExportStage.

    Args:
        config: Optional ExportStageConfig
        **kwargs: Config overrides or component instances

    Returns:
        Configured ExportStage instance
    """
    if config is None:
        # Create config from kwargs
        config_kwargs = {}

        if "export_formats" in kwargs:
            formats = kwargs.pop("export_formats")
            # Convert string formats to ExportFormat enum
            if formats and isinstance(formats[0], str):
                config_kwargs["export_formats"] = [
                    ExportFormat(f.lower()) for f in formats
                ]
            else:
                config_kwargs["export_formats"] = formats

        if "output_dir" in kwargs:
            output_dir = kwargs.pop("output_dir")
            if isinstance(output_dir, str):
                config_kwargs["output_dir"] = Path(output_dir)
            else:
                config_kwargs["output_dir"] = output_dir

        if "parallel_exports" in kwargs:
            config_kwargs["parallel_exports"] = kwargs.pop("parallel_exports")

        if "max_concurrent" in kwargs:
            config_kwargs["max_concurrent"] = kwargs.pop("max_concurrent")

        if "include_metadata" in kwargs:
            config_kwargs["include_metadata"] = kwargs.pop("include_metadata")

        if "compress" in kwargs:
            config_kwargs["compress"] = kwargs.pop("compress")

        config = ExportStageConfig(**config_kwargs) if config_kwargs else None

    return ExportStage(
        config=config,
        engine=kwargs.get("engine"),
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "ExportStage",
    "ExportStageConfig",
    "create_export_stage",
]
