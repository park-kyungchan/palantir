"""MMD Merger - Combine layout and content into Mathpix Markdown.

This module provides the MMDMerger class for merging B1 separation outputs
(layout.json and content.json) into Mathpix Markdown (MMD) format.

The MMD output can then be converted to PDF via Mathpix /v3/converter API.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json

from cow_cli.semantic.schemas import (
    LayoutData,
    ContentData,
    LayoutElement,
    ContentElement,
    ElementType,
)


@dataclass
class MergeResult:
    """Result of MMD merge operation.

    Attributes:
        content: The generated Mathpix Markdown content.
        element_count: Number of layout elements processed.
        output_path: Path to saved MMD file (if output_path was provided).
        warnings: List of warnings encountered during merge.
    """

    content: str
    element_count: int
    output_path: Optional[Path]
    warnings: list[str]


class MMDMerger:
    """Merge B1 outputs into Mathpix Markdown format.

    This class combines layout.json (spatial/structural data) and content.json
    (textual/semantic data) from the B1 separation stage into a single MMD
    document suitable for PDF reconstruction.

    Example:
        >>> merger = MMDMerger()
        >>> result = await merger.merge_files(
        ...     layout_path=Path("output/layout.json"),
        ...     content_path=Path("output/content.json"),
        ...     output_path=Path("output/merged.mmd")
        ... )
        >>> print(result.content)
    """

    # Element types that represent math content
    MATH_TYPES = {
        ElementType.MATH,
        ElementType.EQUATION_NUMBER,
    }

    # Element types that represent structural headers
    HEADER_TYPES = {
        ElementType.TITLE,
        ElementType.SECTION_HEADER,
    }

    def __init__(self):
        """Initialize the MMDMerger."""
        self.warnings: list[str] = []

    async def merge_files(
        self,
        layout_path: Path,
        content_path: Path,
        output_path: Optional[Path] = None,
    ) -> MergeResult:
        """Merge layout and content files into MMD.

        Args:
            layout_path: Path to layout.json file from B1 separation.
            content_path: Path to content.json file from B1 separation.
            output_path: Optional path to save the generated MMD file.

        Returns:
            MergeResult containing the merged content and metadata.

        Raises:
            FileNotFoundError: If layout or content file doesn't exist.
            json.JSONDecodeError: If files contain invalid JSON.
            ValidationError: If data doesn't match expected schemas.
        """
        self.warnings = []  # Reset warnings for new merge

        # Load files
        if not layout_path.exists():
            raise FileNotFoundError(f"Layout file not found: {layout_path}")
        if not content_path.exists():
            raise FileNotFoundError(f"Content file not found: {content_path}")

        layout_data = json.loads(layout_path.read_text(encoding="utf-8"))
        content_data = json.loads(content_path.read_text(encoding="utf-8"))

        # Parse into schemas
        layout = LayoutData.model_validate(layout_data)
        content = ContentData.model_validate(content_data)

        # Merge
        mmd = self._merge(layout, content)

        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(mmd, encoding="utf-8")

        return MergeResult(
            content=mmd,
            element_count=len(layout.elements),
            output_path=output_path,
            warnings=self.warnings.copy(),
        )

    def _merge(self, layout: LayoutData, content: ContentData) -> str:
        """Core merge logic.

        Args:
            layout: Parsed layout data with spatial information.
            content: Parsed content data with textual information.

        Returns:
            Merged Mathpix Markdown string.
        """
        # Sort layout elements by position (top-to-bottom, left-to-right)
        sorted_elements = sorted(
            layout.elements,
            key=lambda e: (
                e.line or 0,
                e.column or 0,
                e.region.top_left_y if e.region else 0,
                e.region.top_left_x if e.region else 0,
            ),
        )

        # Build content lookup by layout_ref
        content_map: dict[str, ContentElement] = {}
        for c in content.elements:
            if c.layout_ref:
                content_map[c.layout_ref] = c
            # Also map by id for direct matches
            content_map[c.id] = c

        # Generate MMD
        mmd_parts: list[str] = []
        for elem in sorted_elements:
            # Try to find matching content
            content_elem = content_map.get(elem.id)

            if content_elem is None:
                self.warnings.append(f"No content for layout element: {elem.id}")
                continue

            mmd_part = self._render_element(elem, content_elem)
            if mmd_part:
                mmd_parts.append(mmd_part)

        return "\n\n".join(mmd_parts)

    def _render_element(
        self,
        layout: LayoutElement,
        content: ContentElement,
    ) -> Optional[str]:
        """Render single element to MMD.

        Args:
            layout: Layout element with type and spatial info.
            content: Content element with text/latex data.

        Returns:
            MMD string for the element, or None if no content.
        """
        elem_type = layout.type

        # Handle math elements
        if content.latex:
            return self._render_math(elem_type, content)

        # Handle text elements
        if content.text or content.text_display:
            return self._render_text(elem_type, content)

        # Handle table elements
        if content.html and elem_type == ElementType.TABLE:
            return self._render_table(content)

        return None

    def _render_math(
        self,
        elem_type: ElementType,
        content: ContentElement,
    ) -> str:
        """Render math content to MMD.

        Args:
            elem_type: Type of the element.
            content: Content element with latex data.

        Returns:
            MMD math string with appropriate delimiters.
        """
        latex = content.latex or content.latex_styled or ""

        # Display math for equation types
        if elem_type in self.MATH_TYPES:
            return f"$$\n{latex}\n$$"

        # Inline math for other contexts
        return f"${latex}$"

    def _render_text(
        self,
        elem_type: ElementType,
        content: ContentElement,
    ) -> str:
        """Render text content to MMD.

        Args:
            elem_type: Type of the element.
            content: Content element with text data.

        Returns:
            MMD text string with appropriate formatting.
        """
        text = content.text_display or content.text or ""

        # Apply formatting based on type
        if elem_type == ElementType.TITLE:
            return f"# {text}"
        elif elem_type == ElementType.SECTION_HEADER:
            level = self._get_header_level(content)
            return f"{'#' * level} {text}"
        elif elem_type == ElementType.QUOTE:
            return f"> {text}"
        elif elem_type == ElementType.CODE:
            return f"```\n{text}\n```"
        elif elem_type == ElementType.FOOTNOTE:
            return f"[^footnote]: {text}"
        else:
            return text

    def _render_table(self, content: ContentElement) -> str:
        """Render table content to MMD.

        Args:
            content: Content element with HTML table data.

        Returns:
            HTML table string (MMD supports HTML tables).
        """
        # MMD supports inline HTML for tables
        return content.html or ""

    def _get_header_level(self, content: ContentElement) -> int:
        """Determine header level from content context.

        Args:
            content: Content element to analyze.

        Returns:
            Header level (1-6), defaults to 2.
        """
        # Default to level 2 for section headers
        # Could be enhanced with font_size analysis from layout
        return 2


__all__ = ["MMDMerger", "MergeResult"]
