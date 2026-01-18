"""
SVG Exporter for Stage H (Export).

Exports pipeline results to SVG format with support for:
- Single SVG files
- SVG bundles (ZIP)
- Embedded styles
- Font embedding

Module Version: 1.0.0
"""

import logging
import time
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, List, Optional

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
class SVGExporterConfig(ExporterConfig):
    """Configuration for SVG exporter.

    Attributes:
        width: Default SVG width
        height: Default SVG height
        embed_styles: Embed CSS styles inline
        embed_fonts: Embed font definitions
        create_bundle: Create ZIP bundle for multiple SVGs
        optimize: Optimize SVG output (remove unnecessary whitespace)
    """
    width: int = 800
    height: int = 600
    embed_styles: bool = True
    embed_fonts: bool = False
    create_bundle: bool = False
    optimize: bool = True


# =============================================================================
# SVG Exporter
# =============================================================================

class SVGExporter(BaseExporter[SVGExporterConfig]):
    """Export pipeline results to SVG format.

    Generates SVG graphics from pipeline outputs. Handles both
    single SVG files and bundled multi-SVG exports.

    Usage:
        exporter = SVGExporter()
        spec = exporter.export(regeneration_spec, options, "img_123")

        # Create bundle
        config = SVGExporterConfig(create_bundle=True)
        exporter = SVGExporter(config)
        spec = exporter.export(data, options, "img_123")
    """

    def _default_config(self) -> SVGExporterConfig:
        """Create default configuration."""
        return SVGExporterConfig()

    @property
    def format(self) -> ExportFormat:
        """Get export format."""
        return ExportFormat.SVG

    @property
    def content_type(self) -> str:
        """Get MIME content type."""
        return "image/svg+xml"

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        if self.config.create_bundle:
            return ".zip"
        return ".svg"

    def _extract_svg_content(self, data: Any) -> List[str]:
        """Extract SVG content from data.

        Args:
            data: Data object

        Returns:
            List of SVG content strings
        """
        svg_contents = []

        # From RegenerationSpec outputs
        if hasattr(data, "outputs"):
            for output in data.outputs:
                if hasattr(output, "format") and output.format.value == "svg":
                    svg_contents.append(output.content)

        return svg_contents

    def _generate_svg_wrapper(
        self,
        content: str,
        options: ExportOptions,
    ) -> str:
        """Generate complete SVG document from content.

        Args:
            content: Inner SVG content
            options: Export options

        Returns:
            Complete SVG string
        """
        svg_options = options.svg_options
        width = svg_options.get("width", self.config.width)
        height = svg_options.get("height", self.config.height)

        # Check if content is already a complete SVG
        if content.strip().startswith("<svg"):
            if self.config.optimize:
                return self._optimize_svg(content)
            return content

        # Wrap content in SVG element
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">',
        ]

        # Add styles if embedding
        if self.config.embed_styles:
            lines.append("  <style>")
            lines.append("    .content { font-family: Arial, sans-serif; }")
            lines.append("    .math { font-family: 'Times New Roman', serif; }")
            lines.append("  </style>")

        # Add content
        lines.append(f"  <g class=\"content\">{content}</g>")
        lines.append("</svg>")

        result = "\n".join(lines)

        if self.config.optimize:
            result = self._optimize_svg(result)

        return result

    def _optimize_svg(self, svg: str) -> str:
        """Optimize SVG by removing unnecessary content.

        Args:
            svg: SVG string

        Returns:
            Optimized SVG string
        """
        # Basic optimization - remove excess whitespace
        import re

        # Remove comments
        svg = re.sub(r"<!--.*?-->", "", svg, flags=re.DOTALL)

        # Collapse multiple spaces
        svg = re.sub(r"\s+", " ", svg)

        # Remove spaces around tags
        svg = re.sub(r">\s+<", "><", svg)

        # But keep some readability
        svg = svg.replace("><", ">\n<")

        return svg.strip()

    def _generate_placeholder_svg(
        self,
        data: Any,
        options: ExportOptions,
    ) -> str:
        """Generate placeholder SVG when no content available.

        Args:
            data: Source data
            options: Export options

        Returns:
            Placeholder SVG string
        """
        svg_options = options.svg_options
        width = svg_options.get("width", self.config.width)
        height = svg_options.get("height", self.config.height)

        image_id = getattr(data, "image_id", "unknown")

        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8f9fa"/>
  <text x="50%" y="45%" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#6c757d">
    No SVG content available
  </text>
  <text x="50%" y="55%" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#adb5bd">
    Image: {image_id}
  </text>
</svg>'''

    def _create_bundle(
        self,
        svg_contents: List[str],
        options: ExportOptions,
        image_id: str,
    ) -> bytes:
        """Create ZIP bundle with multiple SVGs.

        Args:
            svg_contents: List of SVG strings
            options: Export options
            image_id: Source image ID

        Returns:
            ZIP file bytes
        """
        buffer = BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add each SVG
            for i, content in enumerate(svg_contents, 1):
                svg = self._generate_svg_wrapper(content, options)
                zf.writestr(f"svg_{i:03d}.svg", svg)

            # Create index HTML
            html_parts = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                f"  <title>SVG Bundle: {image_id}</title>",
                "  <style>",
                "    body { font-family: Arial, sans-serif; padding: 20px; }",
                "    .svg-container { margin: 20px 0; border: 1px solid #ddd; padding: 10px; }",
                "    h1 { color: #333; }",
                "  </style>",
                "</head>",
                "<body>",
                f"  <h1>SVG Bundle: {image_id}</h1>",
                f"  <p>Contains {len(svg_contents)} SVG files</p>",
            ]

            for i in range(1, len(svg_contents) + 1):
                html_parts.append(f"  <div class=\"svg-container\">")
                html_parts.append(f"    <h3>SVG {i}</h3>")
                html_parts.append(f"    <img src=\"svg_{i:03d}.svg\" alt=\"SVG {i}\">")
                html_parts.append(f"  </div>")

            html_parts.extend([
                "</body>",
                "</html>",
            ])

            zf.writestr("index.html", "\n".join(html_parts))

            # README
            readme = f"""# SVG Export Bundle

Generated by MathpixPipeline v2.0

## Contents
- {len(svg_contents)} SVG files
- index.html: Preview page

## Source
Image ID: {image_id}
"""
            zf.writestr("README.md", readme)

        return buffer.getvalue()

    def export_to_bytes(
        self,
        data: Any,
        options: ExportOptions,
    ) -> bytes:
        """Export data to SVG bytes.

        Args:
            data: Data to export
            options: Export options

        Returns:
            SVG content as bytes (or ZIP bundle)
        """
        svg_contents = self._extract_svg_content(data)

        if not svg_contents:
            # Generate placeholder
            svg = self._generate_placeholder_svg(data, options)
            svg_contents = [svg]

        if self.config.create_bundle and len(svg_contents) > 1:
            image_id = getattr(data, "image_id", "export")
            return self._create_bundle(svg_contents, options, image_id)
        else:
            # Single SVG
            svg = self._generate_svg_wrapper(svg_contents[0], options)
            return svg.encode("utf-8")

    def export(
        self,
        data: Any,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export data to SVG file.

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
        svg_bytes = self.export_to_bytes(data, options)
        checksum = self._calculate_checksum(svg_bytes)
        file_size = self._write_file(svg_bytes, filepath)

        # Count SVGs
        svg_count = len(self._extract_svg_content(data)) or 1

        processing_time = (time.time() - start_time) * 1000

        self._stats["exports_completed"] += 1

        logger.info(
            f"SVG export completed: {filepath}, "
            f"size={file_size} bytes, "
            f"svgs={svg_count}, "
            f"time={processing_time:.1f}ms"
        )

        return self._create_export_spec(
            export_id=export_id,
            image_id=image_id,
            filepath=filepath,
            file_size=file_size,
            checksum=checksum,
            element_count=svg_count,
            processing_time_ms=processing_time,
        )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "SVGExporter",
    "SVGExporterConfig",
]
