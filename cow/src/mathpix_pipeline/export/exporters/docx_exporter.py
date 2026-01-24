"""
DOCX Exporter for Stage H (Export).

Exports pipeline results to Microsoft Word format using python-docx.
Supports structured document generation with customizable styling.

Module Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    Document = None
    Inches = None
    Pt = None
    WD_ALIGN_PARAGRAPH = None
    WD_STYLE_TYPE = None

from pydantic import BaseModel

from ...schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportSpec,
)
from .base import BaseExporter, ExporterConfig
from ..exceptions import ExporterError

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class DOCXExporterConfig(ExporterConfig):
    """Configuration for DOCX exporter.

    Attributes:
        page_width_inches: Page width in inches
        page_height_inches: Page height in inches
        margin_inches: Page margin in inches (uniform)
        font_name: Default font name
        font_size_pt: Default font size in points
        heading_font_name: Font for headings
        include_toc: Include table of contents
        include_header: Include document header
        include_footer: Include page numbers in footer
    """
    page_width_inches: float = 8.5
    page_height_inches: float = 11.0
    margin_inches: float = 1.0
    font_name: str = "Times New Roman"
    font_size_pt: int = 11
    heading_font_name: str = "Arial"
    include_toc: bool = False
    include_header: bool = True
    include_footer: bool = True


# =============================================================================
# DOCX Exporter
# =============================================================================

class DOCXExporter(BaseExporter[DOCXExporterConfig]):
    """Export pipeline results to DOCX format.

    Uses python-docx library to generate Microsoft Word documents
    from pipeline results, supporting:
    - Structured content with headings
    - Math equation representation
    - Metadata sections
    - Custom styling

    Usage:
        exporter = DOCXExporter()
        spec = exporter.export(regeneration_spec, options, "img_123")

        # Or export to bytes
        docx_bytes = exporter.export_to_bytes(data, options)

    Requires:
        python-docx>=0.8.11
    """

    def __init__(self, config: Optional[DOCXExporterConfig] = None):
        """Initialize DOCX exporter.

        Args:
            config: Exporter configuration. Uses defaults if None.

        Raises:
            ImportError: If python-docx is not installed.
        """
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docx is required for DOCX export. "
                "Install with: pip install python-docx"
            )
        super().__init__(config)

    def _default_config(self) -> DOCXExporterConfig:
        """Create default configuration."""
        return DOCXExporterConfig()

    @property
    def format(self) -> ExportFormat:
        """Get export format."""
        return ExportFormat.DOCX

    @property
    def content_type(self) -> str:
        """Get MIME content type."""
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return ".docx"

    def _create_document(self) -> Any:
        """Create a new Word document with default styling.

        Returns:
            Document object
        """
        doc = Document()

        # Configure default paragraph style
        style = doc.styles['Normal']
        font = style.font
        font.name = self.config.font_name
        font.size = Pt(self.config.font_size_pt)

        return doc

    def _add_title(self, doc: Any, title: str) -> None:
        """Add document title.

        Args:
            doc: Document object
            title: Title text
        """
        heading = doc.add_heading(title, level=0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_metadata_section(
        self,
        doc: Any,
        data: Any,
        options: ExportOptions,
    ) -> None:
        """Add metadata section to document.

        Args:
            doc: Document object
            data: Source data
            options: Export options
        """
        if not options.include_metadata:
            return

        doc.add_heading("Metadata", level=1)

        # Add timestamp
        doc.add_paragraph(
            f"Generated: {datetime.now(timezone.utc).isoformat()}"
        )

        # Add data attributes
        if hasattr(data, "__dict__"):
            for key, value in data.__dict__.items():
                if key.startswith("_"):
                    continue
                if isinstance(value, (str, int, float, bool)):
                    doc.add_paragraph(f"{key}: {value}")
        elif isinstance(data, BaseModel):
            for key, value in data.model_dump().items():
                if key.startswith("_"):
                    continue
                if isinstance(value, (str, int, float, bool)):
                    doc.add_paragraph(f"{key}: {value}")

    def _add_content_section(
        self,
        doc: Any,
        data: Any,
        options: ExportOptions,
    ) -> int:
        """Add main content section to document.

        Args:
            doc: Document object
            data: Source data
            options: Export options

        Returns:
            Number of elements added
        """
        element_count = 0

        # Handle different data types
        if hasattr(data, "outputs"):
            doc.add_heading("Outputs", level=1)
            for i, output in enumerate(data.outputs):
                element_count += 1
                self._add_output_item(doc, output, i + 1)

        elif hasattr(data, "nodes"):
            doc.add_heading("Graph Nodes", level=1)
            for i, node in enumerate(data.nodes):
                element_count += 1
                self._add_node_item(doc, node, i + 1)

        elif hasattr(data, "equations"):
            doc.add_heading("Equations", level=1)
            for i, equation in enumerate(data.equations):
                element_count += 1
                self._add_equation_item(doc, equation, i + 1)

        elif isinstance(data, dict):
            doc.add_heading("Data", level=1)
            for key, value in data.items():
                element_count += 1
                p = doc.add_paragraph()
                p.add_run(f"{key}: ").bold = True
                p.add_run(str(value))

        elif isinstance(data, list):
            doc.add_heading("Items", level=1)
            for i, item in enumerate(data):
                element_count += 1
                doc.add_paragraph(f"{i + 1}. {item}")

        return element_count

    def _add_output_item(self, doc: Any, output: Any, index: int) -> None:
        """Add an output item to the document.

        Args:
            doc: Document object
            output: Output data
            index: Item index
        """
        # Add subheading
        doc.add_heading(f"Output {index}", level=2)

        # Add content based on output structure
        if hasattr(output, "content"):
            p = doc.add_paragraph()
            p.add_run("Content: ").bold = True
            p.add_run(str(output.content))

        if hasattr(output, "latex"):
            p = doc.add_paragraph()
            p.add_run("LaTeX: ").bold = True
            p.add_run(str(output.latex))

        if hasattr(output, "confidence"):
            p = doc.add_paragraph()
            p.add_run("Confidence: ").bold = True
            p.add_run(f"{output.confidence:.2%}")

    def _add_node_item(self, doc: Any, node: Any, index: int) -> None:
        """Add a graph node to the document.

        Args:
            doc: Document object
            node: Node data
            index: Item index
        """
        node_type = getattr(node, "type", "Unknown")
        doc.add_heading(f"Node {index}: {node_type}", level=2)

        if hasattr(node, "content"):
            doc.add_paragraph(str(node.content))

        if hasattr(node, "attributes"):
            for key, value in node.attributes.items():
                p = doc.add_paragraph()
                p.add_run(f"  {key}: ").italic = True
                p.add_run(str(value))

    def _add_equation_item(self, doc: Any, equation: Any, index: int) -> None:
        """Add an equation to the document.

        Args:
            doc: Document object
            equation: Equation data
            index: Item index
        """
        doc.add_heading(f"Equation {index}", level=2)

        if hasattr(equation, "latex"):
            p = doc.add_paragraph()
            p.add_run("LaTeX: ").bold = True
            # Use monospace-style formatting for LaTeX
            latex_run = p.add_run(str(equation.latex))
            latex_run.font.name = "Courier New"

        if hasattr(equation, "text"):
            p = doc.add_paragraph()
            p.add_run("Text: ").bold = True
            p.add_run(str(equation.text))

    def _add_provenance_section(
        self,
        doc: Any,
        data: Any,
        options: ExportOptions,
    ) -> None:
        """Add provenance chain section.

        Args:
            doc: Document object
            data: Source data
            options: Export options
        """
        if not options.include_provenance:
            return

        if not hasattr(data, "provenance"):
            return

        doc.add_heading("Provenance", level=1)
        provenance = data.provenance

        if hasattr(provenance, "created_at"):
            doc.add_paragraph(f"Created: {provenance.created_at}")

        if hasattr(provenance, "pipeline_version"):
            doc.add_paragraph(f"Pipeline Version: {provenance.pipeline_version}")

        if hasattr(provenance, "stages_completed"):
            doc.add_paragraph(f"Stages: {', '.join(provenance.stages_completed)}")

    def export_to_bytes(
        self,
        data: Any,
        options: ExportOptions,
    ) -> bytes:
        """Export data to DOCX bytes.

        Args:
            data: Data to export
            options: Export options

        Returns:
            DOCX content as bytes
        """
        doc = self._create_document()

        # Add title
        title = "Pipeline Export"
        if hasattr(data, "image_id"):
            title = f"Export: {data.image_id}"
        elif hasattr(data, "export_id"):
            title = f"Export: {data.export_id}"

        self._add_title(doc, title)

        # Add content sections
        self._add_content_section(doc, data, options)

        # Add metadata
        self._add_metadata_section(doc, data, options)

        # Add provenance
        self._add_provenance_section(doc, data, options)

        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue()

    def export(
        self,
        data: Any,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export data to DOCX file.

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

        try:
            # Create document and export
            doc = self._create_document()

            # Add title
            self._add_title(doc, f"Export: {image_id}")

            # Add content and count elements
            element_count = self._add_content_section(doc, data, options)

            # Add metadata
            self._add_metadata_section(doc, data, options)

            # Add provenance
            self._add_provenance_section(doc, data, options)

            # Save to bytes for checksum
            buffer = BytesIO()
            doc.save(buffer)
            docx_bytes = buffer.getvalue()

            checksum = self._calculate_checksum(docx_bytes)
            file_size = self._write_file(docx_bytes, filepath)

            processing_time = (time.time() - start_time) * 1000

            self._stats["exports_completed"] += 1

            logger.info(
                f"DOCX export completed: {filepath}, "
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

        except Exception as e:
            self._stats["exports_failed"] += 1
            logger.error(f"DOCX export failed: {e}")
            raise ExporterError(
                f"DOCX export failed: {e}",
                exporter_type="docx",
                element_id=image_id,
            )

    def validate_data(self, data: Any) -> bool:
        """Validate data before export.

        Args:
            data: Data to validate

        Returns:
            True if valid for DOCX export
        """
        if data is None:
            return False

        # Check for at least one exportable attribute
        exportable_attrs = ["outputs", "nodes", "equations", "content"]
        if any(hasattr(data, attr) for attr in exportable_attrs):
            return True

        # Accept dicts and lists
        if isinstance(data, (dict, list)):
            return True

        # Accept Pydantic models
        if isinstance(data, BaseModel):
            return True

        return False


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "DOCXExporter",
    "DOCXExporterConfig",
]
