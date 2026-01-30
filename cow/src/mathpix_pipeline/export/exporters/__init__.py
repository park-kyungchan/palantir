"""
Exporters package for Stage E (Export).

Contains format-specific exporters:
- JSONExporter: JSON format export (Structured Outputs)
- DOCXExporter: Microsoft Word format export (python-docx)

Deprecated exporters (soft deprecation - files retained):
- PDFExporter: PDF generation
- LaTeXExporter: LaTeX package export
- SVGExporter: SVG bundle export

All exporters inherit from BaseExporter.

Schema Version: 3.0.0
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
