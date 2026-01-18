"""
JSON Exporter for Stage H (Export).

Exports pipeline results to JSON format with support for:
- Pretty-printed or compact output
- Schema version inclusion
- Pydantic model serialization
- Custom JSON encoders

Module Version: 1.0.0
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel

from ...schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportSpec,
)
from .base import BaseExporter, ExporterConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class JSONExporterConfig(ExporterConfig):
    """Configuration for JSON exporter.

    Attributes:
        indent: Indentation for pretty printing (None for compact)
        sort_keys: Sort dictionary keys alphabetically
        ensure_ascii: Escape non-ASCII characters
        include_schema_version: Add schema version to output
        datetime_format: Format for datetime serialization
    """
    indent: Optional[int] = 2
    sort_keys: bool = False
    ensure_ascii: bool = False
    include_schema_version: bool = True
    datetime_format: str = "iso"  # "iso", "timestamp", "string"


# =============================================================================
# Custom JSON Encoder
# =============================================================================

class PipelineJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for pipeline data types."""

    def __init__(self, *args, datetime_format: str = "iso", **kwargs):
        super().__init__(*args, **kwargs)
        self.datetime_format = datetime_format

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            if self.datetime_format == "iso":
                return obj.isoformat()
            elif self.datetime_format == "timestamp":
                return obj.timestamp()
            else:
                return str(obj)

        if isinstance(obj, BaseModel):
            return obj.model_dump(mode="json")

        if isinstance(obj, Path):
            return str(obj)

        if hasattr(obj, "__dict__"):
            return obj.__dict__

        return super().default(obj)


# =============================================================================
# JSON Exporter
# =============================================================================

class JSONExporter(BaseExporter[JSONExporterConfig]):
    """Export pipeline results to JSON format.

    Supports exporting RegenerationSpec, SemanticGraph, and other
    Pydantic models to well-formatted JSON files.

    Usage:
        exporter = JSONExporter()
        spec = exporter.export(regeneration_spec, options, "img_123")

        # Or export to bytes
        json_bytes = exporter.export_to_bytes(data, options)
    """

    def _default_config(self) -> JSONExporterConfig:
        """Create default configuration."""
        return JSONExporterConfig()

    @property
    def format(self) -> ExportFormat:
        """Get export format."""
        return ExportFormat.JSON

    @property
    def content_type(self) -> str:
        """Get MIME content type."""
        return "application/json"

    def _create_encoder(self) -> PipelineJSONEncoder:
        """Create configured JSON encoder."""
        return PipelineJSONEncoder(datetime_format=self.config.datetime_format)

    def _serialize_data(self, data: Any) -> Dict[str, Any]:
        """Serialize data to JSON-compatible dictionary.

        Args:
            data: Data to serialize

        Returns:
            JSON-compatible dictionary
        """
        if isinstance(data, BaseModel):
            result = data.model_dump(mode="json")
        elif hasattr(data, "to_dict"):
            result = data.to_dict()
        elif isinstance(data, dict):
            result = data
        else:
            result = {"data": data}

        # Add schema version if configured
        if self.config.include_schema_version:
            if isinstance(result, dict):
                result["_export_metadata"] = {
                    "schema_version": "2.0.0",
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "format": "json",
                }

        return result

    def export_to_bytes(
        self,
        data: Any,
        options: ExportOptions,
    ) -> bytes:
        """Export data to JSON bytes.

        Args:
            data: Data to export
            options: Export options

        Returns:
            JSON content as bytes
        """
        serialized = self._serialize_data(data)

        # Determine formatting
        indent = self.config.indent if self.config.pretty_format else None

        json_str = json.dumps(
            serialized,
            cls=type(self._create_encoder()),
            indent=indent,
            sort_keys=self.config.sort_keys,
            ensure_ascii=self.config.ensure_ascii,
        )

        return json_str.encode("utf-8")

    def export(
        self,
        data: Any,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export data to JSON file.

        Args:
            data: Data to export
            options: Export options
            image_id: Source image identifier

        Returns:
            ExportSpec with export metadata
        """
        start_time = time.time()

        # Generate identifiers
        export_id = self._generate_export_id(image_id)
        filename = self._generate_filename(image_id, options)
        filepath = self.config.output_dir / filename

        # Check existing file
        if filepath.exists() and not self.config.overwrite_existing:
            filepath = filepath.with_stem(f"{filepath.stem}_{export_id[:6]}")

        # Serialize and write
        json_bytes = self.export_to_bytes(data, options)
        checksum = self._calculate_checksum(json_bytes)
        file_size = self._write_file(json_bytes, filepath)

        # Count elements
        element_count = 0
        if hasattr(data, "outputs"):
            element_count = len(data.outputs)
        elif hasattr(data, "nodes"):
            element_count = len(data.nodes)

        processing_time = (time.time() - start_time) * 1000

        self._stats["exports_completed"] += 1

        logger.info(
            f"JSON export completed: {filepath}, "
            f"size={file_size} bytes, time={processing_time:.1f}ms"
        )

        return self._create_export_spec(
            export_id=export_id,
            image_id=image_id,
            filepath=filepath,
            file_size=file_size,
            checksum=checksum,
            element_count=element_count,
            processing_time_ms=processing_time,
        )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "JSONExporter",
    "JSONExporterConfig",
    "PipelineJSONEncoder",
]
