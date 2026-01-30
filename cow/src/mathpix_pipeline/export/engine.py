"""
Export Engine for Stage E (Export).

Orchestrates export operations across multiple formats:
- Coordinates format-specific exporters (JSON, DOCX)
- Manages batch exports
- Handles storage and delivery
- AlignmentLayer as primary input type

Module Version: 2.0.0

Note: PDF, LaTeX, SVG formats are deprecated (soft deprecation).
      Files remain for backward compatibility but are not in registry.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Type, Union

from ..schemas.export import (
    BatchExportSpec,
    ExportFormat,
    ExportOptions,
    ExportSpec,
    ExportStatus,
    StorageConfig,
)
from ..schemas.alignment_layer import AlignmentLayer
from .exceptions import ExporterError, ExportPipelineError
from .exporters import (
    BaseExporter,
    DOCXExporter,
    JSONExporter,
)
from .storage import StorageManager, create_storage_manager

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ExportEngineConfig:
    """Configuration for ExportEngine.

    Attributes:
        output_dir: Default output directory
        storage_config: Storage backend configuration
        parallel_exports: Allow parallel format exports
        max_concurrent: Maximum concurrent exports
        default_formats: Default export formats
    """
    output_dir: Path = field(default_factory=lambda: Path("./exports"))
    storage_config: Optional[StorageConfig] = None
    parallel_exports: bool = True
    max_concurrent: int = 4
    default_formats: List[ExportFormat] = field(default_factory=lambda: [
        ExportFormat.JSON,
        ExportFormat.DOCX,
    ])


@dataclass
class BatchExportResult:
    """Result of batch export operation.

    Attributes:
        batch_id: Batch identifier
        exports: Individual export specs
        total_count: Total exports attempted
        success_count: Successful exports
        failure_count: Failed exports
        errors: Error messages by image_id
        processing_time_ms: Total processing time
    """
    batch_id: str
    exports: List[ExportSpec]
    total_count: int
    success_count: int
    failure_count: int
    errors: Dict[str, str]
    processing_time_ms: float


# =============================================================================
# Exporter Registry
# =============================================================================

# Stage E: Only JSON and DOCX formats are supported.
# PDF, LaTeX, SVG exporters are deprecated (soft deprecation).
_EXPORTER_REGISTRY: Dict[ExportFormat, Type[BaseExporter]] = {
    ExportFormat.JSON: JSONExporter,
    ExportFormat.DOCX: DOCXExporter,
}


def register_exporter(
    export_format: ExportFormat,
    exporter_class: Type[BaseExporter],
):
    """Register a custom exporter for a format.

    Args:
        export_format: Format to register for
        exporter_class: Exporter class to use
    """
    _EXPORTER_REGISTRY[export_format] = exporter_class
    logger.info(f"Registered exporter {exporter_class.__name__} for {export_format.value}")


def get_exporter_class(export_format: ExportFormat) -> Type[BaseExporter]:
    """Get exporter class for format.

    Args:
        export_format: Export format

    Returns:
        Exporter class

    Raises:
        ExporterError: If format not supported
    """
    if export_format not in _EXPORTER_REGISTRY:
        raise ExporterError(
            f"Unsupported export format: {export_format.value}",
            exporter_type="registry",
        )
    return _EXPORTER_REGISTRY[export_format]


# =============================================================================
# Export Engine
# =============================================================================

class ExportEngine:
    """Orchestrates export operations.

    Manages format-specific exporters and provides unified
    interface for single and batch exports.

    Usage:
        engine = ExportEngine()

        # Single export
        spec = engine.export(pipeline_result, [ExportFormat.JSON])

        # Batch export
        result = await engine.export_batch(
            results=[result1, result2],
            output_dir=Path("./exports")
        )
    """

    def __init__(self, config: Optional[ExportEngineConfig] = None):
        """Initialize export engine.

        Args:
            config: Engine configuration
        """
        self.config = config or ExportEngineConfig()
        self._exporters: Dict[ExportFormat, BaseExporter] = {}
        self._storage: Optional[StorageManager] = None

        self._stats = {
            "total_exports": 0,
            "successful_exports": 0,
            "failed_exports": 0,
            "total_bytes_exported": 0,
        }

        # Initialize storage if configured
        if self.config.storage_config:
            self._storage = create_storage_manager(self.config.storage_config)

        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"ExportEngine initialized: output_dir={self.config.output_dir}, "
            f"parallel={self.config.parallel_exports}"
        )

    @property
    def stats(self) -> Dict[str, int]:
        """Get engine statistics."""
        return self._stats.copy()

    def _get_exporter(self, export_format: ExportFormat) -> BaseExporter:
        """Get or create exporter for format.

        Args:
            export_format: Export format

        Returns:
            Exporter instance
        """
        if export_format not in self._exporters:
            exporter_class = get_exporter_class(export_format)
            self._exporters[export_format] = exporter_class()

        return self._exporters[export_format]

    def _extract_image_id(self, data: Any) -> str:
        """Extract image ID from data object.

        Args:
            data: Pipeline result data (AlignmentLayer or legacy types)

        Returns:
            Image identifier
        """
        # AlignmentLayer: Use layer ID as primary identifier
        if isinstance(data, AlignmentLayer):
            return data.id

        # Try common attribute names
        for attr in ("image_id", "id", "source_id", "identifier"):
            if hasattr(data, attr):
                value = getattr(data, attr)
                if value:
                    return str(value)

        # Check for nested data
        if hasattr(data, "metadata"):
            metadata = data.metadata
            if hasattr(metadata, "image_id"):
                return str(metadata.image_id)

        # Fallback
        return f"export_{int(time.time() * 1000)}"

    def export(
        self,
        pipeline_result: Any,
        formats: Optional[List[ExportFormat]] = None,
        options: Optional[ExportOptions] = None,
    ) -> List[ExportSpec]:
        """Export pipeline result to specified formats.

        Args:
            pipeline_result: Data to export (RegenerationSpec or similar)
            formats: Export formats (uses defaults if None)
            options: Export options

        Returns:
            List of ExportSpec for each format

        Raises:
            ExportPipelineError: If export fails
        """
        formats = formats or self.config.default_formats
        options = options or ExportOptions()
        image_id = self._extract_image_id(pipeline_result)

        results = []
        errors = []

        for export_format in formats:
            try:
                exporter = self._get_exporter(export_format)
                spec = exporter.export(pipeline_result, options, image_id)
                results.append(spec)

                self._stats["total_exports"] += 1
                self._stats["successful_exports"] += 1
                self._stats["total_bytes_exported"] += spec.file_size

                logger.debug(f"Exported {image_id} to {export_format.value}")

            except ExporterError as e:
                self._stats["total_exports"] += 1
                self._stats["failed_exports"] += 1
                errors.append(f"{export_format.value}: {e}")
                logger.error(f"Export failed for {image_id} to {export_format.value}: {e}")

        if errors and not results:
            raise ExportPipelineError(
                f"All exports failed for {image_id}",
                failed_formats=[f.value for f in formats],
                errors=errors,
            )

        return results

    async def export_async(
        self,
        pipeline_result: Any,
        formats: Optional[List[ExportFormat]] = None,
        options: Optional[ExportOptions] = None,
    ) -> List[ExportSpec]:
        """Async export pipeline result to specified formats.

        Args:
            pipeline_result: Data to export
            formats: Export formats
            options: Export options

        Returns:
            List of ExportSpec for each format
        """
        formats = formats or self.config.default_formats
        options = options or ExportOptions()
        image_id = self._extract_image_id(pipeline_result)

        if self.config.parallel_exports and len(formats) > 1:
            # Parallel export
            tasks = [
                self._export_single_async(pipeline_result, fmt, options, image_id)
                for fmt in formats
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            specs = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self._stats["failed_exports"] += 1
                    logger.error(f"Async export failed: {result}")
                else:
                    specs.append(result)

            return specs

        else:
            # Sequential export
            return self.export(pipeline_result, formats, options)

    async def _export_single_async(
        self,
        data: Any,
        export_format: ExportFormat,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export single format asynchronously.

        Args:
            data: Data to export
            export_format: Target format
            options: Export options
            image_id: Image identifier

        Returns:
            ExportSpec
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        exporter = self._get_exporter(export_format)

        spec = await loop.run_in_executor(
            None,
            exporter.export,
            data,
            options,
            image_id,
        )

        self._stats["total_exports"] += 1
        self._stats["successful_exports"] += 1
        self._stats["total_bytes_exported"] += spec.file_size

        return spec

    async def export_batch(
        self,
        results: Sequence[Any],
        output_dir: Optional[Path] = None,
        formats: Optional[List[ExportFormat]] = None,
        options: Optional[ExportOptions] = None,
    ) -> BatchExportResult:
        """Export multiple pipeline results.

        Args:
            results: List of pipeline results to export
            output_dir: Output directory (uses default if None)
            formats: Export formats for all results
            options: Export options

        Returns:
            BatchExportResult with all exports
        """
        start_time = time.time()
        output_dir = output_dir or self.config.output_dir
        formats = formats or self.config.default_formats
        options = options or ExportOptions()

        # Generate batch ID
        batch_id = f"batch_{int(time.time() * 1000)}"

        exports: List[ExportSpec] = []
        errors: Dict[str, str] = {}

        # Process with semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent)

        async def process_single(data: Any) -> Optional[List[ExportSpec]]:
            async with semaphore:
                image_id = self._extract_image_id(data)
                try:
                    specs = await self.export_async(data, formats, options)
                    return specs
                except Exception as e:
                    errors[image_id] = str(e)
                    return None

        # Run all exports
        tasks = [process_single(data) for data in results]
        all_results = await asyncio.gather(*tasks)

        # Collect successful exports
        for result in all_results:
            if result:
                exports.extend(result)

        processing_time = (time.time() - start_time) * 1000

        success_count = len(exports)
        failure_count = len(errors)

        logger.info(
            f"Batch export {batch_id} completed: "
            f"{success_count} successful, {failure_count} failed, "
            f"time={processing_time:.1f}ms"
        )

        return BatchExportResult(
            batch_id=batch_id,
            exports=exports,
            total_count=len(results) * len(formats),
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
            processing_time_ms=processing_time,
        )

    def export_to_storage(
        self,
        pipeline_result: Any,
        formats: Optional[List[ExportFormat]] = None,
        options: Optional[ExportOptions] = None,
    ) -> List[str]:
        """Export and store in configured storage backend.

        Args:
            pipeline_result: Data to export
            formats: Export formats
            options: Export options

        Returns:
            List of storage URLs

        Raises:
            ExportPipelineError: If storage not configured
        """
        if not self._storage:
            raise ExportPipelineError(
                "Storage not configured",
                failed_formats=[],
            )

        specs = self.export(pipeline_result, formats, options)
        urls = []

        for spec in specs:
            # Read exported file and save to storage
            if spec.file_path:
                content = Path(spec.file_path).read_bytes()
                url = self._storage.save_export(spec, content)
                urls.append(url)

        return urls

    def get_supported_formats(self) -> List[ExportFormat]:
        """Get list of supported export formats.

        Returns:
            List of supported formats
        """
        return list(_EXPORTER_REGISTRY.keys())

    def reset_stats(self):
        """Reset engine statistics."""
        self._stats = {
            "total_exports": 0,
            "successful_exports": 0,
            "failed_exports": 0,
            "total_bytes_exported": 0,
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_export_engine(
    config: Optional[ExportEngineConfig] = None,
    **kwargs,
) -> ExportEngine:
    """Factory function to create ExportEngine.

    Args:
        config: Optional ExportEngineConfig
        **kwargs: Config overrides

    Returns:
        Configured ExportEngine instance
    """
    if config is None and kwargs:
        # Handle Path conversion
        if "output_dir" in kwargs and isinstance(kwargs["output_dir"], str):
            kwargs["output_dir"] = Path(kwargs["output_dir"])
        config = ExportEngineConfig(**kwargs)

    return ExportEngine(config=config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "ExportEngine",
    "ExportEngineConfig",
    "BatchExportResult",
    "create_export_engine",
    "register_exporter",
    "get_exporter_class",
]
