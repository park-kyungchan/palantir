"""
LayoutRegion Value Objects

Provides immutable value objects for representing detected layout regions
with proper coordinate normalization and type safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple, List, Dict, Any
import math


class LayoutLabel(Enum):
    """
    Document layout element labels.

    Based on DocLayout-YOLO's DocStructBench categories plus
    extended labels for comprehensive document understanding.
    """
    # Primary content types
    TEXT = "text"
    TITLE = "title"
    SECTION_HEADER = "section_header"

    # Structured content
    TABLE = "table"
    TABLE_CAPTION = "table_caption"
    FIGURE = "figure"
    FIGURE_CAPTION = "figure_caption"

    # Mathematical content
    EQUATION = "equation"
    EQUATION_INLINE = "equation_inline"
    EQUATION_BLOCK = "equation_block"

    # Lists and structured text
    LIST = "list"
    LIST_ITEM = "list_item"

    # Educational content
    ANSWER_BOX = "answer_box"
    PROBLEM_BOX = "problem_box"

    # Page elements
    PAGE_HEADER = "page_header"
    PAGE_FOOTER = "page_footer"
    PAGE_NUMBER = "page_number"

    # Supplementary content
    FOOTNOTE = "footnote"
    CAPTION = "caption"
    CODE = "code"

    # Catch-all
    UNKNOWN = "unknown"

    @classmethod
    def from_doclayout_yolo(cls, label: str) -> "LayoutLabel":
        """
        Map DocLayout-YOLO detection labels to LayoutLabel enum.

        DocLayout-YOLO labels (DocStructBench):
            0: title, 1: plain text, 2: abandon, 3: figure, 4: figure_caption,
            5: table, 6: table_caption, 7: table_footnote, 8: isolate_formula,
            9: formula_caption, 10: page_header, 11: page_footer, 12: page_number,
            13: header
        """
        label_map = {
            "title": cls.TITLE,
            "plain text": cls.TEXT,
            "text": cls.TEXT,
            "abandon": cls.UNKNOWN,
            "figure": cls.FIGURE,
            "figure_caption": cls.FIGURE_CAPTION,
            "table": cls.TABLE,
            "table_caption": cls.TABLE_CAPTION,
            "table_footnote": cls.FOOTNOTE,
            "isolate_formula": cls.EQUATION_BLOCK,
            "formula_caption": cls.CAPTION,
            "page_header": cls.PAGE_HEADER,
            "page_footer": cls.PAGE_FOOTER,
            "page_number": cls.PAGE_NUMBER,
            "header": cls.SECTION_HEADER,
            "section-header": cls.SECTION_HEADER,
            "list": cls.LIST,
            "list-item": cls.LIST_ITEM,
            "code": cls.CODE,
            "picture": cls.FIGURE,
            "caption": cls.CAPTION,
            "footnote": cls.FOOTNOTE,
        }
        normalized = label.lower().strip()
        return label_map.get(normalized, cls.UNKNOWN)

    @property
    def is_content(self) -> bool:
        """Returns True if this is primary content (text, title, list)."""
        return self in {
            LayoutLabel.TEXT,
            LayoutLabel.TITLE,
            LayoutLabel.SECTION_HEADER,
            LayoutLabel.LIST,
            LayoutLabel.LIST_ITEM,
        }

    @property
    def is_structural(self) -> bool:
        """Returns True if this is structural content (table, figure, equation)."""
        return self in {
            LayoutLabel.TABLE,
            LayoutLabel.FIGURE,
            LayoutLabel.EQUATION,
            LayoutLabel.EQUATION_BLOCK,
            LayoutLabel.CODE,
        }

    @property
    def is_metadata(self) -> bool:
        """Returns True if this is page metadata (header, footer, page number)."""
        return self in {
            LayoutLabel.PAGE_HEADER,
            LayoutLabel.PAGE_FOOTER,
            LayoutLabel.PAGE_NUMBER,
        }


class CoordinateSystem(Enum):
    """
    Coordinate system types for bounding boxes.

    Different sources (PDF, image, model) use different coordinate systems.
    This enum helps track and convert between them.
    """
    # PDF coordinates: origin at bottom-left, Y increases upward
    PDF = auto()

    # Image coordinates: origin at top-left, Y increases downward
    IMAGE = auto()

    # Normalized coordinates: 0-1 range, origin at top-left
    NORMALIZED = auto()

    # Model output: pixel coordinates in processed image (may have padding)
    MODEL_PIXELS = auto()


@dataclass(frozen=True)
class PageDimensions:
    """
    Page dimensions for coordinate transformations.

    Attributes:
        width: Page width in the native unit
        height: Page height in the native unit
        dpi: DPI used for image rendering (for PDF->image conversion)
        coordinate_system: The coordinate system these dimensions are in
    """
    width: float
    height: float
    dpi: int = 72
    coordinate_system: CoordinateSystem = CoordinateSystem.PDF

    def to_image_scale(self, target_dpi: int = 150) -> "PageDimensions":
        """Convert to image pixel dimensions at target DPI."""
        scale = target_dpi / self.dpi
        return PageDimensions(
            width=self.width * scale,
            height=self.height * scale,
            dpi=target_dpi,
            coordinate_system=CoordinateSystem.IMAGE,
        )


@dataclass(frozen=True)
class BoundingBox:
    """
    Immutable bounding box with coordinate system awareness.

    Coordinates follow the convention:
        - (x0, y0): top-left corner
        - (x1, y1): bottom-right corner

    Note: For PDF coordinate system, y0 < y1 means y0 is lower on page.
    """
    x0: float
    y0: float
    x1: float
    y1: float
    coordinate_system: CoordinateSystem = CoordinateSystem.IMAGE

    def __post_init__(self):
        """Validate bounding box coordinates."""
        if self.x0 > self.x1:
            # Swap x coordinates
            new_x0, new_x1 = self.x1, self.x0
            object.__setattr__(self, 'x0', new_x0)
            object.__setattr__(self, 'x1', new_x1)
            
        if self.coordinate_system != CoordinateSystem.PDF:
            # For non-PDF systems, y0 should be <= y1
            if self.y0 > self.y1:
                new_y0, new_y1 = self.y1, self.y0
                object.__setattr__(self, 'y0', new_y0)
                object.__setattr__(self, 'y1', new_y1)

    @property
    def width(self) -> float:
        """Bounding box width."""
        return abs(self.x1 - self.x0)

    @property
    def height(self) -> float:
        """Bounding box height."""
        return abs(self.y1 - self.y0)

    @property
    def area(self) -> float:
        """Bounding box area."""
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        """Center point (cx, cy)."""
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    @property
    def top_left(self) -> Tuple[float, float]:
        """Top-left corner (for image coordinates)."""
        return (self.x0, self.y0)

    @property
    def bottom_right(self) -> Tuple[float, float]:
        """Bottom-right corner (for image coordinates)."""
        return (self.x1, self.y1)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Return as (x0, y0, x1, y1) tuple."""
        return (self.x0, self.y0, self.x1, self.y1)

    def to_xywh(self) -> Tuple[float, float, float, float]:
        """Return as (x, y, width, height) tuple."""
        return (self.x0, self.y0, self.width, self.height)

    def normalize(self, page_dims: PageDimensions) -> "BoundingBox":
        """
        Normalize coordinates to 0-1 range.

        Args:
            page_dims: Page dimensions for normalization

        Returns:
            New BoundingBox with normalized coordinates
        """
        return BoundingBox(
            x0=self.x0 / page_dims.width,
            y0=self.y0 / page_dims.height,
            x1=self.x1 / page_dims.width,
            y1=self.y1 / page_dims.height,
            coordinate_system=CoordinateSystem.NORMALIZED,
        )

    def denormalize(self, page_dims: PageDimensions) -> "BoundingBox":
        """
        Denormalize coordinates from 0-1 range to page dimensions.

        Args:
            page_dims: Target page dimensions

        Returns:
            New BoundingBox with denormalized coordinates
        """
        return BoundingBox(
            x0=self.x0 * page_dims.width,
            y0=self.y0 * page_dims.height,
            x1=self.x1 * page_dims.width,
            y1=self.y1 * page_dims.height,
            coordinate_system=page_dims.coordinate_system,
        )

    def to_pdf_coordinates(self, page_height: float) -> "BoundingBox":
        """
        Convert from image coordinates (top-left origin) to PDF coordinates (bottom-left origin).

        Args:
            page_height: Total page height for Y-axis flip

        Returns:
            New BoundingBox in PDF coordinate system
        """
        if self.coordinate_system == CoordinateSystem.PDF:
            return self

        # Flip Y axis: PDF y = page_height - image_y
        return BoundingBox(
            x0=self.x0,
            y0=page_height - self.y1,  # Image y1 becomes PDF y0
            x1=self.x1,
            y1=page_height - self.y0,  # Image y0 becomes PDF y1
            coordinate_system=CoordinateSystem.PDF,
        )

    def to_image_coordinates(self, page_height: float) -> "BoundingBox":
        """
        Convert from PDF coordinates (bottom-left origin) to image coordinates (top-left origin).

        Args:
            page_height: Total page height for Y-axis flip

        Returns:
            New BoundingBox in image coordinate system
        """
        if self.coordinate_system == CoordinateSystem.IMAGE:
            return self

        # Flip Y axis: image_y = page_height - PDF_y
        return BoundingBox(
            x0=self.x0,
            y0=page_height - self.y1,
            x1=self.x1,
            y1=page_height - self.y0,
            coordinate_system=CoordinateSystem.IMAGE,
        )

    def scale(self, scale_x: float, scale_y: Optional[float] = None) -> "BoundingBox":
        """
        Scale bounding box by given factors.

        Args:
            scale_x: X-axis scale factor
            scale_y: Y-axis scale factor (defaults to scale_x if not provided)

        Returns:
            New scaled BoundingBox
        """
        if scale_y is None:
            scale_y = scale_x
        return BoundingBox(
            x0=self.x0 * scale_x,
            y0=self.y0 * scale_y,
            x1=self.x1 * scale_x,
            y1=self.y1 * scale_y,
            coordinate_system=self.coordinate_system,
        )

    def pad(self, padding: float) -> "BoundingBox":
        """
        Expand bounding box by padding amount on all sides.

        Args:
            padding: Padding amount (can be negative for shrinking)

        Returns:
            New padded BoundingBox
        """
        return BoundingBox(
            x0=self.x0 - padding,
            y0=self.y0 - padding,
            x1=self.x1 + padding,
            y1=self.y1 + padding,
            coordinate_system=self.coordinate_system,
        )

    def iou(self, other: "BoundingBox") -> float:
        """
        Calculate Intersection over Union (IoU) with another bounding box.

        Args:
            other: Another bounding box

        Returns:
            IoU value between 0 and 1
        """
        # Calculate intersection
        inter_x0 = max(self.x0, other.x0)
        inter_y0 = max(self.y0, other.y0)
        inter_x1 = min(self.x1, other.x1)
        inter_y1 = min(self.y1, other.y1)

        if inter_x0 >= inter_x1 or inter_y0 >= inter_y1:
            return 0.0

        inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
        union_area = self.area + other.area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def contains(self, other: "BoundingBox", threshold: float = 0.9) -> bool:
        """
        Check if this bounding box contains another (by area overlap).

        Args:
            other: Another bounding box to check
            threshold: Minimum overlap ratio required

        Returns:
            True if other is contained within this box
        """
        inter_x0 = max(self.x0, other.x0)
        inter_y0 = max(self.y0, other.y0)
        inter_x1 = min(self.x1, other.x1)
        inter_y1 = min(self.y1, other.y1)

        if inter_x0 >= inter_x1 or inter_y0 >= inter_y1:
            return False

        inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
        return (inter_area / other.area) >= threshold if other.area > 0 else False

    def merge(self, other: "BoundingBox") -> "BoundingBox":
        """
        Merge with another bounding box (union).

        Args:
            other: Another bounding box to merge

        Returns:
            New BoundingBox containing both boxes
        """
        return BoundingBox(
            x0=min(self.x0, other.x0),
            y0=min(self.y0, other.y0),
            x1=max(self.x1, other.x1),
            y1=max(self.y1, other.y1),
            coordinate_system=self.coordinate_system,
        )


@dataclass(frozen=True)
class LayoutRegion:
    """
    Detected layout region with label and confidence.

    This is the primary value object returned by layout detection,
    containing all information needed for reading order sorting
    and document reconstruction.

    Attributes:
        bbox: Bounding box coordinates
        label: LayoutLabel
        confidence: Detection confidence score (0-1)
        page_number: Page index (0-based)
        text: Extracted text content (optional)
        region_id: Unique identifier for tracking
        metadata: Additional properties from detector
    """
    bbox: BoundingBox
    label: LayoutLabel
    confidence: float = 1.0
    page_number: int = 0
    text: Optional[str] = None
    region_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence score."""
        if not 0 <= self.confidence <= 1:
            object.__setattr__(self, 'confidence', max(0, min(1, self.confidence)))

    @property
    def center_y(self) -> float:
        """Vertical center (for reading order)."""
        return self.bbox.center[1]

    @property
    def center_x(self) -> float:
        """Horizontal center (for column detection)."""
        return self.bbox.center[0]

    @property
    def top(self) -> float:
        """Top edge Y coordinate."""
        return self.bbox.y0

    @property
    def bottom(self) -> float:
        """Bottom edge Y coordinate."""
        return self.bbox.y1

    @property
    def left(self) -> float:
        """Left edge X coordinate."""
        return self.bbox.x0

    @property
    def right(self) -> float:
        """Right edge X coordinate."""
        return self.bbox.x1

    def with_text(self, text: str) -> "LayoutRegion":
        """Create a copy with updated text content."""
        return LayoutRegion(
            bbox=self.bbox,
            label=self.label,
            confidence=self.confidence,
            page_number=self.page_number,
            text=text,
            region_id=self.region_id,
            metadata=self.metadata,
        )

    def with_label(self, label: LayoutLabel) -> "LayoutRegion":
        """Create a copy with updated label."""
        return LayoutRegion(
            bbox=self.bbox,
            label=label,
            confidence=self.confidence,
            page_number=self.page_number,
            text=self.text,
            region_id=self.region_id,
            metadata=self.metadata,
        )

    def with_bbox(self, bbox: BoundingBox) -> "LayoutRegion":
        """Create a copy with updated bounding box."""
        return LayoutRegion(
            bbox=bbox,
            label=self.label,
            confidence=self.confidence,
            page_number=self.page_number,
            text=self.text,
            region_id=self.region_id,
            metadata=self.metadata,
        )

    def overlaps_vertically(self, other: "LayoutRegion", threshold: float = 0.5) -> bool:
        """
        Check if this region overlaps vertically with another.

        Used for determining if regions are on the same "line" or row.

        Args:
            other: Another layout region
            threshold: Minimum vertical overlap ratio

        Returns:
            True if regions overlap vertically
        """
        overlap_start = max(self.top, other.top)
        overlap_end = min(self.bottom, other.bottom)

        if overlap_start >= overlap_end:
            return False

        overlap_height = overlap_end - overlap_start
        min_height = min(self.bbox.height, other.bbox.height)

        return (overlap_height / min_height) >= threshold if min_height > 0 else False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "bbox": self.bbox.to_tuple(),
            "label": self.label.value,
            "confidence": self.confidence,
            "page_number": self.page_number,
            "text": self.text,
            "region_id": self.region_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutRegion":
        """Deserialize from dictionary."""
        return cls(
            bbox=BoundingBox(*data["bbox"]),
            label=LayoutLabel(data["label"]),
            confidence=data.get("confidence", 1.0),
            page_number=data.get("page_number", 0),
            text=data.get("text"),
            region_id=data.get("region_id"),
            metadata=data.get("metadata", {}),
        )
