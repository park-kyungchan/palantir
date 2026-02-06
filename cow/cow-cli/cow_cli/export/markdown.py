"""
COW CLI - Markdown Exporter

Export separated documents to Markdown format.
Supports multiple flavors: GFM, MMD (Mathpix), Standard.
"""
from pathlib import Path
from typing import Optional
from enum import Enum
from io import StringIO

from cow_cli.export.base import BaseExporter, ExportFormat, ExportOptions, ExportResult
from cow_cli.semantic.schemas import (
    SeparatedDocument,
    ContentElement,
    LayoutElement,
    ElementType,
)


class MarkdownFlavor(str, Enum):
    """Markdown flavor variants."""
    STANDARD = "standard"
    GFM = "gfm"  # GitHub Flavored Markdown
    MMD = "mmd"  # Mathpix Markdown


class MarkdownExporter(BaseExporter):
    """
    Markdown format exporter.

    Supports multiple flavors with different math rendering styles.
    """

    format = ExportFormat.MARKDOWN

    def __init__(
        self,
        options: Optional[ExportOptions] = None,
        flavor: MarkdownFlavor = MarkdownFlavor.GFM,
        include_frontmatter: bool = True,
        include_toc: bool = False,
    ):
        """
        Initialize Markdown exporter.

        Args:
            options: Export options
            flavor: Markdown flavor (standard, gfm, mmd)
            include_frontmatter: Include YAML frontmatter
            include_toc: Include table of contents
        """
        super().__init__(options)
        self.flavor = flavor
        self.include_frontmatter = include_frontmatter
        self.include_toc = include_toc

    def export(self, document: SeparatedDocument, output_path: Path) -> ExportResult:
        """
        Export document to Markdown.

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
            # Build markdown content
            md_content = self._build_markdown(document)

            # Write
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(md_content, encoding="utf-8")

            return ExportResult(
                success=True,
                output_path=output_path,
                format=self.format,
                bytes_written=len(md_content.encode("utf-8")),
                warnings=warnings,
            )

        except Exception as e:
            return ExportResult(
                success=False,
                error=str(e),
                warnings=warnings,
            )

    def _build_markdown(self, document: SeparatedDocument) -> str:
        """Build the Markdown content."""
        output = StringIO()

        # Frontmatter
        if self.include_frontmatter:
            output.write(self._build_frontmatter(document))
            output.write("\n")

        # Title
        title = Path(document.image_path).stem.replace("_", " ").title()
        output.write(f"# {title}\n\n")

        # TOC
        if self.include_toc:
            output.write(self._build_toc(document))
            output.write("\n")

        # Content sections
        output.write(self._build_content_sections(document))

        # Quality summary
        if self.options.include_quality_metrics:
            output.write(self._build_quality_section(document))

        return output.getvalue()

    def _build_frontmatter(self, document: SeparatedDocument) -> str:
        """Build YAML frontmatter."""
        lines = [
            "---",
            f"source: {document.image_path}",
            f"created: {document.created_at.isoformat()}",
            f"version: {document.processing_version}",
        ]

        if document.request_id:
            lines.append(f"request_id: {document.request_id}")

        lines.append(f"elements: {len(document.content.elements)}")
        lines.append("---")

        return "\n".join(lines) + "\n"

    def _build_toc(self, document: SeparatedDocument) -> str:
        """Build table of contents."""
        lines = ["## Table of Contents\n"]

        # Group by type
        type_counts: dict[str, int] = {}
        for elem in document.content.elements:
            layout_elem = document.layout.get_element_by_id(elem.layout_ref or elem.id)
            if layout_elem:
                elem_type = layout_elem.type
                type_counts[elem_type] = type_counts.get(elem_type, 0) + 1

        for elem_type, count in sorted(type_counts.items()):
            anchor = elem_type.lower().replace("_", "-")
            lines.append(f"- [{elem_type.replace('_', ' ').title()}](#{anchor}) ({count})")

        return "\n".join(lines) + "\n"

    def _build_content_sections(self, document: SeparatedDocument) -> str:
        """Build the main content sections."""
        output = StringIO()

        for i, content_elem in enumerate(document.content.elements):
            layout_elem = document.layout.get_element_by_id(
                content_elem.layout_ref or content_elem.id
            )

            elem_type = layout_elem.type if layout_elem else "unknown"

            # Section header for grouping
            if i == 0 or self._should_show_type_header(document, i):
                output.write(f"\n## {elem_type.replace('_', ' ').title()}\n\n")

            # Render element
            output.write(self._render_element(content_elem, layout_elem))
            output.write("\n\n")

        return output.getvalue()

    def _should_show_type_header(self, document: SeparatedDocument, index: int) -> bool:
        """Check if we should show a type header at this index."""
        if index == 0:
            return True

        current = document.content.elements[index]
        previous = document.content.elements[index - 1]

        current_layout = document.layout.get_element_by_id(current.layout_ref or current.id)
        previous_layout = document.layout.get_element_by_id(previous.layout_ref or previous.id)

        if current_layout and previous_layout:
            return current_layout.type != previous_layout.type

        return False

    def _render_element(
        self,
        content: ContentElement,
        layout: Optional[LayoutElement],
    ) -> str:
        """Render a single element to Markdown."""
        elem_type = layout.type if layout else ElementType.TEXT

        # Math elements
        if elem_type == ElementType.MATH:
            return self._render_math(content)

        # Table elements
        if elem_type == ElementType.TABLE:
            return self._render_table(content)

        # Code elements
        if elem_type in (ElementType.CODE, ElementType.PSEUDOCODE):
            return self._render_code(content)

        # Default: text
        return self._render_text(content)

    def _render_math(self, content: ContentElement) -> str:
        """Render math element."""
        latex = content.latex or content.latex_styled or ""

        if not latex:
            return content.text or ""

        if self.flavor == MarkdownFlavor.MMD:
            # Mathpix Markdown uses $$ for display math
            return f"$$\n{latex}\n$$"
        elif self.flavor == MarkdownFlavor.GFM:
            # GFM uses ```math code blocks (GitHub)
            return f"```math\n{latex}\n```"
        else:
            # Standard uses $$
            return f"$$\n{latex}\n$$"

    def _render_table(self, content: ContentElement) -> str:
        """Render table element."""
        # Check for HTML table data
        if content.html:
            return f"<div class=\"table-container\">\n{content.html}\n</div>"

        # Try to find TSV data
        for data in content.data:
            if data.type.value == "tsv":
                return self._tsv_to_markdown_table(data.value)
            if data.type.value == "table_html":
                return f"<div class=\"table-container\">\n{data.value}\n</div>"

        # Fallback to text
        return content.text or ""

    def _tsv_to_markdown_table(self, tsv: str) -> str:
        """Convert TSV to Markdown table."""
        lines = tsv.strip().split("\n")
        if not lines:
            return ""

        output = []
        for i, line in enumerate(lines):
            cells = line.split("\t")
            row = "| " + " | ".join(cells) + " |"
            output.append(row)

            if i == 0:
                # Header separator
                separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                output.append(separator)

        return "\n".join(output)

    def _render_code(self, content: ContentElement) -> str:
        """Render code element."""
        code = content.text or ""
        return f"```\n{code}\n```"

    def _render_text(self, content: ContentElement) -> str:
        """Render text element."""
        text = content.text or content.text_display or ""

        # Include inline math if present
        if content.latex and not text:
            return f"${content.latex}$"

        return text

    def _build_quality_section(self, document: SeparatedDocument) -> str:
        """Build quality metrics section."""
        summary = document.content.quality_summary
        lines = [
            "\n---\n",
            "## Quality Metrics\n",
            f"- **Total Elements:** {summary.total_elements}",
            f"- **High Confidence:** {summary.high_confidence_count}",
            f"- **Needs Review:** {summary.needs_review_count}",
        ]

        if summary.average_confidence is not None:
            lines.append(f"- **Average Confidence:** {summary.average_confidence:.1%}")

        return "\n".join(lines) + "\n"


__all__ = ["MarkdownExporter", "MarkdownFlavor"]
