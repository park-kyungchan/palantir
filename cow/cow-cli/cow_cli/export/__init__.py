"""
COW CLI - Export Module

Export separated documents to various formats.
"""
from cow_cli.export.base import (
    ExportFormat,
    ExportOptions,
    ExportResult,
    BaseExporter,
)
from cow_cli.export.json_exporter import JSONExporter
from cow_cli.export.markdown import MarkdownExporter, MarkdownFlavor
from cow_cli.export.latex import LaTeXExporter, DocumentClass
from cow_cli.export.docx import DocxExporter, DOCX_AVAILABLE


def get_exporter(format: ExportFormat, **kwargs) -> BaseExporter:
    """
    Factory function to get an exporter by format.

    Args:
        format: Export format
        **kwargs: Exporter-specific options

    Returns:
        Configured exporter instance

    Raises:
        ValueError: If format is not supported
    """
    exporters = {
        ExportFormat.JSON: JSONExporter,
        ExportFormat.MARKDOWN: MarkdownExporter,
        ExportFormat.LATEX: LaTeXExporter,
        ExportFormat.DOCX: DocxExporter,
    }

    exporter_class = exporters.get(format)
    if exporter_class is None:
        raise ValueError(f"Unsupported export format: {format}")

    return exporter_class(**kwargs)


__all__ = [
    # Base
    "ExportFormat",
    "ExportOptions",
    "ExportResult",
    "BaseExporter",
    # Exporters
    "JSONExporter",
    "MarkdownExporter",
    "MarkdownFlavor",
    "LaTeXExporter",
    "DocumentClass",
    "DocxExporter",
    "DOCX_AVAILABLE",
    # Factory
    "get_exporter",
]
