"""
Exporters package for Stage H (Export).

Contains format-specific exporters:
- JSONExporter: JSON format export
- PDFExporter: PDF generation
- LaTeXExporter: LaTeX package export
- SVGExporter: SVG bundle export
- DOCXExporter: Microsoft Word format export

All exporters inherit from BaseExporter.

Schema Version: 2.0.0
"""

from .base import BaseExporter, ExporterConfig
from .json_exporter import JSONExporter, JSONExporterConfig
from .pdf_exporter import PDFExporter, PDFExporterConfig
from .latex_exporter import LaTeXExporter, LaTeXExporterConfig
from .svg_exporter import SVGExporter, SVGExporterConfig
from .docx_exporter import DOCXExporter, DOCXExporterConfig


__all__ = [
    # Base
    "BaseExporter",
    "ExporterConfig",
    # JSON
    "JSONExporter",
    "JSONExporterConfig",
    # PDF
    "PDFExporter",
    "PDFExporterConfig",
    # LaTeX
    "LaTeXExporter",
    "LaTeXExporterConfig",
    # SVG
    "SVGExporter",
    "SVGExporterConfig",
    # DOCX
    "DOCXExporter",
    "DOCXExporterConfig",
]
