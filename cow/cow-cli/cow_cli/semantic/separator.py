"""
COW CLI - Layout/Content Separator

Separates Mathpix API output into Layout and Content data.
Supports both raw API dict and UnifiedResponse input.
"""
from typing import Optional, Any, Dict, List, Union
from pathlib import Path
import json
import logging
from datetime import datetime

from cow_cli.semantic.schemas import (
    Region,
    DataFormat,
    DataObject,
    PageInfo,
    ElementType,
    ElementSubtype,
    LayoutElement,
    LayoutMetadata,
    LayoutData,
    QualityMetrics,
    ContentElement,
    ContentMetadata,
    ContentData,
    SeparatedDocument,
)
from cow_cli.mathpix.schemas import UnifiedResponse, PdfLineData

logger = logging.getLogger("cow-cli.semantic")


class SeparationError(Exception):
    """Error during layout/content separation."""

    pass


class LayoutContentSeparator:
    """
    Separates Mathpix API output into Layout and Content data.

    Takes word_data or line_data from Stage B output and produces:
    - LayoutData: Spatial, hierarchical, and structural information
    - ContentData: Textual, mathematical, and semantic information
    """

    # Fields that belong to Layout (spatial/structural)
    LAYOUT_FIELDS = {
        "id",
        "type",
        "subtype",
        "region",
        "cnt",
        "column",
        "line",
        "font_size",
        "parent_id",
        "children_ids",
        "conversion_output",
        "error_id",
    }

    # Fields that belong to Content (textual/semantic)
    CONTENT_FIELDS = {
        "id",
        "text",
        "text_display",
        "latex",
        "html",
        "data",
        "confidence",
        "confidence_rate",
        "is_printed",
        "is_handwritten",
    }

    def __init__(self, strict: bool = False):
        """
        Initialize separator.

        Args:
            strict: If True, raise errors on validation failures
        """
        self.strict = strict

    def separate(
        self,
        stage_b_output: dict,
        image_path: Optional[str] = None,
    ) -> SeparatedDocument:
        """
        Separate Stage B output into Layout and Content data.

        Args:
            stage_b_output: Raw Mathpix API response
            image_path: Optional source image path

        Returns:
            SeparatedDocument with layout and content

        Raises:
            SeparationError: If separation fails
        """
        request_id = stage_b_output.get("request_id")
        word_data = stage_b_output.get("word_data") or []
        line_data = stage_b_output.get("line_data") or []

        # Use word_data preferentially (COW pipeline uses word_data)
        elements_data = word_data if word_data else line_data

        if not elements_data:
            logger.warning("No word_data or line_data found in output")

        # Extract page info
        page_info = self._extract_page_info(stage_b_output)

        # Process elements
        layout_elements = []
        content_elements = []

        for idx, elem_data in enumerate(elements_data):
            elem_id = elem_data.get("id", f"elem-{idx}")

            # Create layout element
            layout_elem = self._create_layout_element(elem_id, elem_data)
            layout_elements.append(layout_elem)

            # Create content element
            content_elem = self._create_content_element(elem_id, elem_data)
            content_elements.append(content_elem)

        # Build LayoutData
        layout = LayoutData(
            elements=layout_elements,
            page=page_info,
            metadata=LayoutMetadata(
                source="mathpix",
                extracted_at=datetime.now(),
                element_count=len(layout_elements),
            ),
        )

        # Build ContentData
        content = ContentData(
            elements=content_elements,
            metadata=ContentMetadata(
                source="mathpix",
                extracted_at=datetime.now(),
                element_count=len(content_elements),
                request_id=request_id,
            ),
        )

        # Compute quality summary
        content.compute_quality_summary()

        # Create document
        doc = SeparatedDocument(
            image_path=image_path or "unknown",
            layout=layout,
            content=content,
            request_id=request_id,
        )

        # Validate if strict mode
        if self.strict:
            errors = self.validate_separation(doc)
            if errors:
                raise SeparationError(f"Validation failed: {errors}")

        return doc

    def _extract_page_info(self, output: dict) -> PageInfo:
        """Extract page information from output."""
        # Handle None values by defaulting to 0
        width = output.get("image_width")
        height = output.get("image_height")
        return PageInfo(
            width=width if width is not None else 0,
            height=height if height is not None else 0,
            auto_rotate_degrees=output.get("auto_rotate_degrees"),
        )

    def _create_layout_element(
        self,
        elem_id: str,
        data: dict,
    ) -> LayoutElement:
        """Create LayoutElement from raw data."""
        # Parse type
        elem_type = self._parse_element_type(data.get("type", "text"))

        # Parse subtype
        elem_subtype = self._parse_element_subtype(data.get("subtype"))

        # Parse region from cnt if present
        region = None
        cnt = data.get("cnt")
        if cnt:
            region = self._cnt_to_region(cnt)

        # Parse children_ids
        children_ids = data.get("children_ids", [])
        if children_ids is None:
            children_ids = []

        return LayoutElement(
            id=elem_id,
            type=elem_type,
            subtype=elem_subtype,
            region=region,
            cnt=cnt,
            column=data.get("column"),
            line=data.get("line"),
            font_size=data.get("font_size"),
            parent_id=data.get("parent_id"),
            children_ids=children_ids,
            conversion_output=data.get("conversion_output", True),
            error_id=data.get("error_id"),
            selected_labels=data.get("selected_labels"),  # Preserve labels for chart/diagram
        )

    def _create_content_element(
        self,
        elem_id: str,
        data: dict,
    ) -> ContentElement:
        """Create ContentElement from raw data."""
        # Parse data array (multi-format outputs)
        data_objects = []
        raw_data = data.get("data", [])
        if raw_data:
            for d in raw_data:
                try:
                    data_objects.append(
                        DataObject(
                            type=DataFormat(d.get("type", "latex")),
                            value=d.get("value", ""),
                        )
                    )
                except ValueError:
                    logger.warning(f"Unknown data format: {d.get('type')}")

        # Parse quality metrics
        quality = QualityMetrics(
            confidence=data.get("confidence"),
            confidence_rate=data.get("confidence_rate"),
        )

        return ContentElement(
            id=elem_id,
            layout_ref=elem_id,  # Same ID links to layout
            text=data.get("text"),
            text_display=data.get("text_display"),
            latex=data.get("latex"),
            latex_styled=data.get("latex_styled"),  # Preserve styled latex
            html=data.get("html"),
            data=data_objects,
            quality=quality,
            is_printed=data.get("is_printed"),
            is_handwritten=data.get("is_handwritten"),
            after_hyphen=data.get("after_hyphen"),  # Preserve hyphen connection info
        )

    def _parse_element_type(self, type_str: str) -> ElementType:
        """Parse element type string to enum."""
        try:
            return ElementType(type_str.lower())
        except ValueError:
            logger.warning(f"Unknown element type: {type_str}, defaulting to TEXT")
            return ElementType.TEXT

    def _parse_element_subtype(
        self,
        subtype_str: Optional[str],
    ) -> Optional[ElementSubtype]:
        """Parse element subtype string to enum."""
        if not subtype_str:
            return None
        try:
            return ElementSubtype(subtype_str.lower())
        except ValueError:
            logger.warning(f"Unknown element subtype: {subtype_str}")
            return None

    def _cnt_to_region(self, cnt: list[list[int]]) -> Optional[Region]:
        """
        Convert polygon contour to bounding box region.

        Args:
            cnt: List of [x, y] coordinate pairs

        Returns:
            Region bounding box or None if invalid
        """
        if not cnt or len(cnt) < 2:
            return None

        try:
            xs = [p[0] for p in cnt]
            ys = [p[1] for p in cnt]

            min_x = min(xs)
            min_y = min(ys)
            max_x = max(xs)
            max_y = max(ys)

            width = max_x - min_x
            height = max_y - min_y

            # Ensure minimum dimensions
            if width < 1:
                width = 1
            if height < 1:
                height = 1

            return Region(
                top_left_x=max(0, min_x),
                top_left_y=max(0, min_y),
                width=width,
                height=height,
            )
        except (IndexError, TypeError) as e:
            logger.warning(f"Invalid contour data: {e}")
            return None

    def separate_unified(
        self,
        unified: UnifiedResponse,
        source_path: Optional[str] = None,
    ) -> SeparatedDocument:
        """
        Separate UnifiedResponse into Layout and Content data.

        This method handles both PDF and Image API responses through
        the normalized UnifiedResponse interface.

        Args:
            unified: UnifiedResponse from MathpixClient
            source_path: Optional source file path

        Returns:
            SeparatedDocument with layout and content

        Raises:
            SeparationError: If separation fails
        """
        request_id = unified.metadata.request_id

        # Collect all lines from all pages
        all_lines: List[PdfLineData] = unified.get_all_lines()

        if not all_lines:
            logger.warning("No lines found in UnifiedResponse")

        # Build hierarchy map for quick lookups
        hierarchy: Dict[str, List[str]] = {}  # parent_id -> children_ids
        root_elements: List[str] = []

        for line in all_lines:
            if line.parent_id:
                if line.parent_id not in hierarchy:
                    hierarchy[line.parent_id] = []
                hierarchy[line.parent_id].append(line.id)
            else:
                root_elements.append(line.id)

        # Process elements
        layout_elements = []
        content_elements = []

        for idx, line in enumerate(all_lines):
            elem_id = line.id or f"elem-{idx}"

            # Create layout element from PdfLineData
            layout_elem = self._create_layout_element_from_line(elem_id, line)
            layout_elements.append(layout_elem)

            # Create content element from PdfLineData
            content_elem = self._create_content_element_from_line(elem_id, line)
            content_elements.append(content_elem)

        # Extract page info from first page (or use defaults)
        page_info = PageInfo(
            width=unified.pages[0].page_width if unified.pages else 0,
            height=unified.pages[0].page_height if unified.pages else 0,
            page_number=1,
            total_pages=unified.total_pages,
        )

        # Build LayoutData with hierarchy info
        layout = LayoutData(
            elements=layout_elements,
            page=page_info,
            metadata=LayoutMetadata(
                source=f"mathpix_{unified.metadata.source_type}",
                extracted_at=datetime.now(),
                element_count=len(layout_elements),
            ),
        )

        # Build ContentData
        content = ContentData(
            elements=content_elements,
            metadata=ContentMetadata(
                source=f"mathpix_{unified.metadata.source_type}",
                extracted_at=datetime.now(),
                element_count=len(content_elements),
                request_id=request_id,
            ),
        )

        # Compute quality summary
        content.compute_quality_summary()

        # Create document
        doc = SeparatedDocument(
            image_path=source_path or "unknown",
            layout=layout,
            content=content,
            request_id=request_id,
        )

        # Validate if strict mode
        if self.strict:
            errors = self.validate_separation(doc)
            if errors:
                raise SeparationError(f"Validation failed: {errors}")

        return doc

    def _create_layout_element_from_line(
        self,
        elem_id: str,
        line: PdfLineData,
    ) -> LayoutElement:
        """Create LayoutElement from PdfLineData."""
        elem_type = self._parse_element_type(line.type or "text")
        elem_subtype = self._parse_element_subtype(line.subtype)

        # Parse region from cnt or region field
        region = None
        if line.region:
            region = Region(
                top_left_x=line.region.top_left_x,
                top_left_y=line.region.top_left_y,
                width=line.region.width,
                height=line.region.height,
            )
        elif line.cnt:
            region = self._cnt_to_region(line.cnt)

        children_ids = line.children_ids or []

        return LayoutElement(
            id=elem_id,
            type=elem_type,
            subtype=elem_subtype,
            region=region,
            cnt=line.cnt,
            column=line.column,
            line=line.line,
            font_size=line.font_size,
            parent_id=line.parent_id,
            children_ids=children_ids,
            conversion_output=line.conversion_output if line.conversion_output is not None else True,
            error_id=line.error_id,
            selected_labels=line.selected_labels,  # Preserve labels for chart/diagram
        )

    def _create_content_element_from_line(
        self,
        elem_id: str,
        line: PdfLineData,
    ) -> ContentElement:
        """Create ContentElement from PdfLineData."""
        # Parse data array
        data_objects = []
        if line.data:
            for d in line.data:
                try:
                    data_objects.append(
                        DataObject(
                            type=DataFormat(d.type),
                            value=d.value,
                        )
                    )
                except ValueError:
                    logger.warning(f"Unknown data format: {d.type}")

        # Parse quality metrics
        quality = QualityMetrics(
            confidence=line.confidence,
            confidence_rate=line.confidence_rate,
        )

        return ContentElement(
            id=elem_id,
            layout_ref=elem_id,
            text=line.text or "",
            text_display=line.text_display or line.text or "",
            latex=line.latex,  # Preserve latex from Mathpix API
            latex_styled=line.latex_styled,  # Preserve styled latex
            html=line.html,
            data=data_objects,
            quality=quality,
            is_printed=line.is_printed if line.is_printed is not None else True,
            is_handwritten=line.is_handwritten if line.is_handwritten is not None else False,
            after_hyphen=line.after_hyphen,  # Preserve hyphen connection info
        )

    def get_hierarchy(self, layout: LayoutData) -> Dict[str, List[str]]:
        """
        Build hierarchy map from layout elements.

        Returns:
            Dict mapping parent_id to list of children_ids
        """
        hierarchy: Dict[str, List[str]] = {}
        for elem in layout.elements:
            if elem.children_ids:
                hierarchy[elem.id] = list(elem.children_ids)
        return hierarchy

    def get_root_elements(self, layout: LayoutData) -> List[str]:
        """
        Get IDs of root elements (no parent).

        Returns:
            List of element IDs with no parent_id
        """
        return [elem.id for elem in layout.elements if not elem.parent_id]

    def get_subtree(self, layout: LayoutData, element_id: str) -> List[LayoutElement]:
        """
        Get element and all its descendants.

        Args:
            layout: LayoutData containing elements
            element_id: ID of root element for subtree

        Returns:
            List of elements in subtree (depth-first order)
        """
        elements_by_id = {e.id: e for e in layout.elements}
        result = []

        def traverse(eid: str):
            if eid in elements_by_id:
                elem = elements_by_id[eid]
                result.append(elem)
                for child_id in (elem.children_ids or []):
                    traverse(child_id)

        traverse(element_id)
        return result

    def validate_separation(self, doc: SeparatedDocument) -> list[str]:
        """
        Validate separation consistency.

        Checks:
        - Element count matches
        - ID consistency
        - Reference validity

        Args:
            doc: SeparatedDocument to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check element count matches
        layout_count = len(doc.layout.elements)
        content_count = len(doc.content.elements)

        if layout_count != content_count:
            errors.append(
                f"Element count mismatch: layout={layout_count}, content={content_count}"
            )

        # Check ID consistency
        layout_ids = {e.id for e in doc.layout.elements}
        content_ids = {e.id for e in doc.content.elements}

        missing_in_content = layout_ids - content_ids
        if missing_in_content:
            errors.append(f"Layout IDs missing in content: {missing_in_content}")

        missing_in_layout = content_ids - layout_ids
        if missing_in_layout:
            errors.append(f"Content IDs missing in layout: {missing_in_layout}")

        # Validate references
        ref_errors = doc.validate_references()
        errors.extend(ref_errors)

        return errors

    def save_layout(
        self,
        layout: LayoutData,
        path: Path,
        indent: int = 2,
    ) -> None:
        """
        Save layout data to JSON file.

        Args:
            layout: LayoutData to save
            path: Output file path
            indent: JSON indentation
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(layout.model_dump_json(indent=indent))
        logger.info(f"Saved layout to {path}")

    def save_content(
        self,
        content: ContentData,
        path: Path,
        indent: int = 2,
    ) -> None:
        """
        Save content data to JSON file.

        Args:
            content: ContentData to save
            path: Output file path
            indent: JSON indentation
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.model_dump_json(indent=indent))
        logger.info(f"Saved content to {path}")

    def save_document(
        self,
        doc: SeparatedDocument,
        output_dir: Path,
        layout_filename: str = "layout.json",
        content_filename: str = "content.json",
        combined_filename: Optional[str] = "separated.json",
    ) -> dict[str, Path]:
        """
        Save separated document to multiple files.

        Args:
            doc: SeparatedDocument to save
            output_dir: Output directory
            layout_filename: Layout file name
            content_filename: Content file name
            combined_filename: Combined file name (None to skip)

        Returns:
            Dict of saved file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved = {}

        # Save layout
        layout_path = output_dir / layout_filename
        self.save_layout(doc.layout, layout_path)
        saved["layout"] = layout_path

        # Save content
        content_path = output_dir / content_filename
        self.save_content(doc.content, content_path)
        saved["content"] = content_path

        # Save combined (optional)
        if combined_filename:
            combined_path = output_dir / combined_filename
            with open(combined_path, "w", encoding="utf-8") as f:
                f.write(doc.model_dump_json(indent=2))
            saved["combined"] = combined_path
            logger.info(f"Saved combined document to {combined_path}")

        return saved


def separate_mathpix_output(
    stage_b_output: dict,
    image_path: Optional[str] = None,
    strict: bool = False,
) -> SeparatedDocument:
    """
    Convenience function for separating Mathpix output.

    Args:
        stage_b_output: Raw Mathpix API response
        image_path: Optional source image path
        strict: If True, raise errors on validation failures

    Returns:
        SeparatedDocument with layout and content
    """
    separator = LayoutContentSeparator(strict=strict)
    return separator.separate(stage_b_output, image_path)


__all__ = [
    "SeparationError",
    "LayoutContentSeparator",
    "separate_mathpix_output",
]
