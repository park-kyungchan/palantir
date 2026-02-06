"""
COW CLI - JSON Exporter

Export separated documents to JSON format.
"""
import json
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from cow_cli.export.base import BaseExporter, ExportFormat, ExportOptions, ExportResult
from cow_cli.semantic.schemas import SeparatedDocument


class JSONExporter(BaseExporter):
    """
    JSON format exporter.

    Exports the full document structure or selected fields to JSON.
    """

    format = ExportFormat.JSON

    def __init__(
        self,
        options: Optional[ExportOptions] = None,
        indent: int = 2,
        include_fields: Optional[list[str]] = None,
        exclude_fields: Optional[list[str]] = None,
    ):
        """
        Initialize JSON exporter.

        Args:
            options: Export options
            indent: JSON indentation (None for compact)
            include_fields: Fields to include (None = all)
            exclude_fields: Fields to exclude
        """
        super().__init__(options)
        self.indent = indent
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields or []

    def export(self, document: SeparatedDocument, output_path: Path) -> ExportResult:
        """
        Export document to JSON.

        Args:
            document: The separated document
            output_path: Destination file path

        Returns:
            ExportResult with status
        """
        warnings = []
        output_path = self.ensure_extension(output_path)

        # Validate
        validation_errors = self.validate_document(document)
        if validation_errors:
            warnings.extend(validation_errors)

        try:
            # Build export data
            data = self._build_export_data(document)

            # Serialize
            json_str = json.dumps(
                data,
                indent=self.indent,
                ensure_ascii=False,
                default=self._json_serializer,
            )

            # Write
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_str, encoding="utf-8")

            return ExportResult(
                success=True,
                output_path=output_path,
                format=self.format,
                bytes_written=len(json_str.encode("utf-8")),
                warnings=warnings,
            )

        except Exception as e:
            return ExportResult(
                success=False,
                error=str(e),
                warnings=warnings,
            )

    def _build_export_data(self, document: SeparatedDocument) -> dict[str, Any]:
        """Build the data dictionary for export."""
        data: dict[str, Any] = {
            "version": "1.0.0",
            "export_format": "cow-separated-document",
            "image_path": document.image_path,
            "created_at": document.created_at.isoformat(),
            "processing_version": document.processing_version,
        }

        if document.request_id:
            data["request_id"] = document.request_id

        # Include sections based on options
        if self.options.include_layout and self._should_include("layout"):
            data["layout"] = self._serialize_layout(document)

        if self.options.include_content and self._should_include("content"):
            data["content"] = self._serialize_content(document)

        if self.options.include_metadata and self._should_include("metadata"):
            data["metadata"] = {
                "layout": document.layout.metadata.model_dump() if document.layout.metadata else {},
                "content": document.content.metadata.model_dump() if document.content.metadata else {},
            }

        if self.options.include_quality_metrics and self._should_include("quality"):
            data["quality_summary"] = document.content.quality_summary.model_dump()

        return data

    def _serialize_layout(self, document: SeparatedDocument) -> dict[str, Any]:
        """Serialize layout data."""
        return {
            "elements": [elem.model_dump() for elem in document.layout.elements],
            "page": document.layout.page.model_dump(),
        }

    def _serialize_content(self, document: SeparatedDocument) -> dict[str, Any]:
        """Serialize content data."""
        return {
            "elements": [elem.model_dump() for elem in document.content.elements],
        }

    def _should_include(self, field: str) -> bool:
        """Check if a field should be included."""
        if field in self.exclude_fields:
            return False
        if self.include_fields is not None:
            return field in self.include_fields
        return True

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


__all__ = ["JSONExporter"]
