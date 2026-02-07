"""
COW CLI - Base Exporter

Abstract base class for all export formats.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from cow_cli.semantic.schemas import SeparatedDocument


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    LATEX = "latex"
    DOCX = "docx"
    PDF = "pdf"


@dataclass
class ExportOptions:
    """Common export options."""
    output_path: Optional[Path] = None
    include_layout: bool = True
    include_content: bool = True
    include_metadata: bool = True
    include_quality_metrics: bool = False

    # Format-specific options (passed to exporters)
    format_options: dict = field(default_factory=dict)


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    output_path: Optional[Path] = None
    format: Optional[ExportFormat] = None
    bytes_written: int = 0
    error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if export was successful and file exists."""
        return self.success and self.output_path is not None and self.output_path.exists()


class BaseExporter(ABC):
    """
    Abstract base class for document exporters.

    Subclasses must implement:
    - export(): Main export method
    - format: Class attribute indicating the format
    """

    format: ExportFormat

    def __init__(self, options: Optional[ExportOptions] = None):
        """
        Initialize exporter.

        Args:
            options: Export options
        """
        self.options = options or ExportOptions()

    @abstractmethod
    def export(self, document: SeparatedDocument, output_path: Path) -> ExportResult:
        """
        Export document to the target format.

        Args:
            document: The separated document to export
            output_path: Destination file path

        Returns:
            ExportResult with success status and details
        """
        pass

    def validate_document(self, document: SeparatedDocument) -> list[str]:
        """
        Validate document before export.

        Args:
            document: Document to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not document.layout.elements and not document.content.elements:
            errors.append("Document has no layout or content elements")

        # Validate references
        ref_errors = document.validate_references()
        errors.extend(ref_errors)

        return errors

    def get_default_extension(self) -> str:
        """Get default file extension for this format."""
        extensions = {
            ExportFormat.JSON: ".json",
            ExportFormat.MARKDOWN: ".md",
            ExportFormat.LATEX: ".tex",
            ExportFormat.DOCX: ".docx",
            ExportFormat.PDF: ".pdf",
        }
        return extensions.get(self.format, ".txt")

    def ensure_extension(self, path: Path) -> Path:
        """Ensure the path has the correct extension."""
        expected = self.get_default_extension()
        if path.suffix != expected:
            return path.with_suffix(expected)
        return path


__all__ = [
    "ExportFormat",
    "ExportOptions",
    "ExportResult",
    "BaseExporter",
]
