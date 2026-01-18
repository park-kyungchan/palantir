"""
Base Exporter for Stage H (Export).

Defines the abstract base class for all exporters and
common utilities shared across export formats.

Module Version: 1.0.0
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generic, Optional, TypeVar

from ...schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportSpec,
)
from ..exceptions import ExportError

logger = logging.getLogger(__name__)


# Type variable for config
ConfigT = TypeVar("ConfigT", bound="ExporterConfig")


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ExporterConfig:
    """Base configuration for all exporters.

    Attributes:
        output_dir: Directory for output files
        include_metadata: Include metadata in export
        pretty_format: Format output for readability
        overwrite_existing: Overwrite existing files
    """
    output_dir: Path = field(default_factory=lambda: Path("./exports"))
    include_metadata: bool = True
    pretty_format: bool = True
    overwrite_existing: bool = True


# =============================================================================
# Base Exporter
# =============================================================================

class BaseExporter(ABC, Generic[ConfigT]):
    """Abstract base class for all exporters.

    All format-specific exporters must inherit from this class
    and implement the required abstract methods.

    Type Parameters:
        ConfigT: Configuration type for this exporter

    Usage:
        class MyExporter(BaseExporter[MyConfig]):
            @property
            def format(self) -> ExportFormat:
                return ExportFormat.JSON

            def export(self, data: Any, options: ExportOptions) -> ExportSpec:
                # Implementation
                pass
    """

    def __init__(self, config: Optional[ConfigT] = None):
        """Initialize exporter.

        Args:
            config: Exporter configuration. Uses defaults if None.
        """
        self.config = config or self._default_config()
        self._stats = {
            "exports_completed": 0,
            "exports_failed": 0,
            "bytes_written": 0,
        }

        # Ensure output directory exists
        if hasattr(self.config, "output_dir"):
            self.config.output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"{self.__class__.__name__} initialized")

    @property
    def stats(self) -> Dict[str, int]:
        """Get exporter statistics."""
        return self._stats.copy()

    @abstractmethod
    def _default_config(self) -> ConfigT:
        """Create default configuration.

        Returns:
            Default configuration instance
        """
        pass

    @property
    @abstractmethod
    def format(self) -> ExportFormat:
        """Get the export format handled by this exporter.

        Returns:
            ExportFormat enum value
        """
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Get the MIME content type for exports.

        Returns:
            MIME type string
        """
        pass

    @property
    def file_extension(self) -> str:
        """Get the file extension for exports.

        Returns:
            File extension including dot (e.g., '.json')
        """
        return f".{self.format.value}"

    @abstractmethod
    def export(
        self,
        data: Any,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export data to the target format.

        Args:
            data: Data to export (RegenerationSpec, SemanticGraph, etc.)
            options: Export options
            image_id: Source image identifier

        Returns:
            ExportSpec with export metadata

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_to_bytes(
        self,
        data: Any,
        options: ExportOptions,
    ) -> bytes:
        """Export data to bytes without writing to file.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Exported content as bytes
        """
        pass

    def _generate_export_id(self, image_id: str) -> str:
        """Generate unique export identifier.

        Args:
            image_id: Source image ID

        Returns:
            Unique export ID
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        content = f"{image_id}_{self.format.value}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def _generate_filename(
        self,
        image_id: str,
        options: ExportOptions,
    ) -> str:
        """Generate output filename from template.

        Args:
            image_id: Source image ID
            options: Export options with filename template

        Returns:
            Generated filename
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        filename = options.filename_template.format(
            image_id=image_id,
            format=self.format.value,
            timestamp=timestamp,
        )

        if not filename.endswith(self.file_extension):
            filename += self.file_extension

        return filename

    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum of data.

        Args:
            data: Data bytes

        Returns:
            Hex digest of checksum
        """
        return hashlib.sha256(data).hexdigest()

    def _write_file(
        self,
        data: bytes,
        filepath: Path,
    ) -> int:
        """Write data to file.

        Args:
            data: Data to write
            filepath: Destination path

        Returns:
            Number of bytes written

        Raises:
            ExportError: If write fails
        """
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(data)
            self._stats["bytes_written"] += len(data)
            return len(data)

        except Exception as e:
            raise ExportError(
                f"Failed to write export file: {e}",
                details={"path": str(filepath)},
            )

    def _create_export_spec(
        self,
        export_id: str,
        image_id: str,
        filepath: Path,
        file_size: int,
        checksum: str,
        element_count: int = 0,
        confidence: float = 1.0,
        processing_time_ms: float = 0.0,
    ) -> ExportSpec:
        """Create ExportSpec from export results.

        Args:
            export_id: Export identifier
            image_id: Source image ID
            filepath: Output file path
            file_size: Size in bytes
            checksum: SHA256 checksum
            element_count: Number of elements
            confidence: Export confidence
            processing_time_ms: Processing time

        Returns:
            ExportSpec instance
        """
        return ExportSpec(
            export_id=export_id,
            image_id=image_id,
            format=self.format,
            content_type=self.content_type,
            file_path=str(filepath.absolute()),
            file_size=file_size,
            checksum=checksum,
            element_count=element_count,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
        )

    def validate_data(self, data: Any) -> bool:
        """Validate data before export.

        Override in subclasses for format-specific validation.

        Args:
            data: Data to validate

        Returns:
            True if valid
        """
        return data is not None


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "BaseExporter",
    "ExporterConfig",
]
