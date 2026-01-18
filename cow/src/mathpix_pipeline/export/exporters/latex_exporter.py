"""
LaTeX Exporter for Stage H (Export).

Exports pipeline results to LaTeX format with support for:
- Standalone documents
- Package-ready output
- Custom preambles
- Multiple file bundles

Module Version: 1.0.0
"""

import logging
import time
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

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
class LaTeXExporterConfig(ExporterConfig):
    """Configuration for LaTeX exporter.

    Attributes:
        document_class: LaTeX document class
        default_packages: Packages to always include
        standalone: Generate standalone compilable document
        create_bundle: Create ZIP bundle with all files
        include_tikz: Include TikZ diagrams
    """
    document_class: str = "article"
    default_packages: List[str] = field(default_factory=lambda: [
        "amsmath",
        "amssymb",
        "amsthm",
        "tikz",
        "pgfplots",
    ])
    standalone: bool = True
    create_bundle: bool = False
    include_tikz: bool = True


# =============================================================================
# LaTeX Exporter
# =============================================================================

class LaTeXExporter(BaseExporter[LaTeXExporterConfig]):
    """Export pipeline results to LaTeX format.

    Generates LaTeX documents or standalone .tex files from
    pipeline results. Can create bundles with associated resources.

    Usage:
        exporter = LaTeXExporter()
        spec = exporter.export(regeneration_spec, options, "img_123")

        # Create bundle with resources
        config = LaTeXExporterConfig(create_bundle=True)
        exporter = LaTeXExporter(config)
        spec = exporter.export(data, options, "img_123")
    """

    def _default_config(self) -> LaTeXExporterConfig:
        """Create default configuration."""
        return LaTeXExporterConfig()

    @property
    def format(self) -> ExportFormat:
        """Get export format."""
        return ExportFormat.LATEX

    @property
    def content_type(self) -> str:
        """Get MIME content type."""
        return "text/x-tex"

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        if self.config.create_bundle:
            return ".zip"
        return ".tex"

    def _generate_preamble(self, options: ExportOptions) -> List[str]:
        """Generate LaTeX preamble.

        Args:
            options: Export options

        Returns:
            List of preamble lines
        """
        lines = []

        # Document class
        doc_class = options.latex_options.get("document_class", self.config.document_class)
        lines.append(f"\\documentclass{{{doc_class}}}")
        lines.append("")

        # Packages
        packages = set(self.config.default_packages)
        packages.update(options.latex_options.get("packages", []))

        lines.append("% Required packages")
        for pkg in sorted(packages):
            lines.append(f"\\usepackage{{{pkg}}}")

        # PGFPlots settings
        if "pgfplots" in packages:
            lines.append("")
            lines.append("% PGFPlots settings")
            lines.append("\\pgfplotsset{compat=1.18}")

        # Custom preamble
        custom = options.latex_options.get("custom_preamble", "")
        if custom:
            lines.append("")
            lines.append("% Custom preamble")
            lines.append(custom)

        lines.append("")

        return lines

    def _extract_content(self, data: Any) -> str:
        """Extract LaTeX content from data.

        Args:
            data: Data object

        Returns:
            LaTeX content string
        """
        content_parts = []

        # From RegenerationSpec outputs
        if hasattr(data, "outputs"):
            for output in data.outputs:
                if hasattr(output, "format"):
                    if output.format.value in ("latex", "tikz"):
                        content_parts.append(output.content)

        # From SemanticGraph
        if hasattr(data, "nodes"):
            equations = []
            for node in data.nodes:
                if hasattr(node, "properties") and node.properties.latex:
                    equations.append(node.properties.latex)

            if equations:
                content_parts.append("% Equations from semantic graph")
                content_parts.append("\\begin{align*}")
                for i, eq in enumerate(equations):
                    suffix = " \\\\" if i < len(equations) - 1 else ""
                    content_parts.append(f"  {eq}{suffix}")
                content_parts.append("\\end{align*}")

        # Direct LaTeX content
        if hasattr(data, "get_latex"):
            latex = data.get_latex()
            if latex:
                content_parts.append(latex)

        # Fallback
        if not content_parts:
            content_parts.append("% No LaTeX content extracted")
            content_parts.append("% Data type: " + type(data).__name__)

        return "\n\n".join(content_parts)

    def _generate_document(
        self,
        data: Any,
        options: ExportOptions,
    ) -> str:
        """Generate complete LaTeX document.

        Args:
            data: Data to export
            options: Export options

        Returns:
            Complete LaTeX document string
        """
        lines = []

        # Header comment
        lines.append("% Generated by MathpixPipeline v2.0")
        lines.append("% Schema Version: 2.0.0")
        if hasattr(data, "image_id"):
            lines.append(f"% Source Image: {data.image_id}")
        lines.append("")

        # Preamble (if standalone)
        if self.config.standalone:
            lines.extend(self._generate_preamble(options))
            lines.append("\\begin{document}")
            lines.append("")

            # Title if available
            if hasattr(data, "image_id"):
                lines.append(f"\\section*{{Export: {data.image_id}}}")
                lines.append("")

        # Main content
        content = self._extract_content(data)
        lines.append(content)

        # Metadata section
        if options.include_metadata:
            lines.append("")
            lines.append("% Metadata")
            lines.append("\\vfill")
            lines.append("\\noindent\\rule{\\textwidth}{0.4pt}")
            lines.append("\\footnotesize")
            lines.append("\\textit{Generated by MathpixPipeline v2.0}")

            if hasattr(data, "overall_confidence"):
                lines.append(f"\\\\Confidence: {data.overall_confidence:.2%}")

        # End document
        if self.config.standalone:
            lines.append("")
            lines.append("\\end{document}")

        return "\n".join(lines)

    def _create_bundle(
        self,
        data: Any,
        options: ExportOptions,
        main_content: str,
    ) -> bytes:
        """Create ZIP bundle with LaTeX and resources.

        Args:
            data: Source data
            options: Export options
            main_content: Main .tex content

        Returns:
            ZIP file bytes
        """
        buffer = BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Main document
            zf.writestr("main.tex", main_content)

            # Create Makefile
            makefile = """# Makefile for LaTeX compilation
.PHONY: all clean

all: main.pdf

main.pdf: main.tex
\tpdflatex -interaction=nonstopmode main.tex
\tpdflatex -interaction=nonstopmode main.tex

clean:
\trm -f *.aux *.log *.out *.toc *.pdf
"""
            zf.writestr("Makefile", makefile)

            # README
            readme = """# LaTeX Export Bundle

Generated by MathpixPipeline v2.0

## Files
- main.tex: Main LaTeX document
- Makefile: Build automation

## Compilation
Run `make` to compile, or use:
    pdflatex main.tex

## Requirements
- pdflatex
- amsmath, amssymb packages
- tikz, pgfplots (for diagrams)
"""
            zf.writestr("README.md", readme)

            # Add TikZ externalized figures if available
            if hasattr(data, "outputs") and self.config.include_tikz:
                tikz_count = 0
                for output in data.outputs:
                    if hasattr(output, "format") and output.format.value == "tikz":
                        tikz_count += 1
                        zf.writestr(f"figures/tikz_{tikz_count:03d}.tex", output.content)

        return buffer.getvalue()

    def export_to_bytes(
        self,
        data: Any,
        options: ExportOptions,
    ) -> bytes:
        """Export data to LaTeX bytes.

        Args:
            data: Data to export
            options: Export options

        Returns:
            LaTeX content as bytes (or ZIP bundle)
        """
        main_content = self._generate_document(data, options)

        if self.config.create_bundle:
            return self._create_bundle(data, options, main_content)
        else:
            return main_content.encode("utf-8")

    def export(
        self,
        data: Any,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export data to LaTeX file.

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

        # Generate and write content
        latex_bytes = self.export_to_bytes(data, options)
        checksum = self._calculate_checksum(latex_bytes)
        file_size = self._write_file(latex_bytes, filepath)

        # Count elements
        element_count = 0
        if hasattr(data, "outputs"):
            element_count = len(data.outputs)
        elif hasattr(data, "nodes"):
            element_count = len(data.nodes)

        processing_time = (time.time() - start_time) * 1000

        self._stats["exports_completed"] += 1

        logger.info(
            f"LaTeX export completed: {filepath}, "
            f"size={file_size} bytes, "
            f"bundle={self.config.create_bundle}, "
            f"time={processing_time:.1f}ms"
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
    "LaTeXExporter",
    "LaTeXExporterConfig",
]
