"""
COW CLI - Layout/Content Separation Schemas

Pydantic models for Layout parsing data and Content/Problem data separation.
Based on: LAYOUT_CONTENT_SEPARATION_ANALYSIS.yaml
"""
from typing import Optional, Literal, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# SHARED TYPES
# =============================================================================


class Region(BaseModel):
    """Bounding box coordinates."""

    top_left_x: int = Field(..., ge=0, description="X coordinate of top-left corner")
    top_left_y: int = Field(..., ge=0, description="Y coordinate of top-left corner")
    width: int = Field(..., ge=1, description="Width in pixels")
    height: int = Field(..., ge=1, description="Height in pixels")

    @property
    def bottom_right_x(self) -> int:
        """Calculate bottom-right X coordinate."""
        return self.top_left_x + self.width

    @property
    def bottom_right_y(self) -> int:
        """Calculate bottom-right Y coordinate."""
        return self.top_left_y + self.height

    @property
    def area(self) -> int:
        """Calculate area in pixels."""
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        """Calculate center point."""
        return (
            self.top_left_x + self.width / 2,
            self.top_left_y + self.height / 2,
        )


class DataFormat(str, Enum):
    """Available data format types."""

    LATEX = "latex"
    ASCIIMATH = "asciimath"
    MATHML = "mathml"
    SVG = "svg"
    TABLE_HTML = "table_html"
    TSV = "tsv"


class DataObject(BaseModel):
    """Structured data element from data_options."""

    type: DataFormat = Field(..., description="Data format type")
    value: str = Field(..., description="The extracted data content")


class PageInfo(BaseModel):
    """Page metadata."""

    width: int = Field(default=0, ge=0, description="Page width in pixels")
    height: int = Field(default=0, ge=0, description="Page height in pixels")
    page_number: int = Field(default=1, ge=1)
    total_pages: int = Field(default=1, ge=1)
    auto_rotate_degrees: Optional[Literal[0, 90, -90, 180]] = Field(
        default=None,
        description="Rotation applied",
    )


# =============================================================================
# LAYOUT TYPES (36 line_types from Mathpix)
# =============================================================================


class ElementType(str, Enum):
    """Element type classification (36 Mathpix line_types)."""

    # Primary content types
    TEXT = "text"
    MATH = "math"
    TABLE = "table"
    DIAGRAM = "diagram"
    CHART = "chart"
    CODE = "code"
    PSEUDOCODE = "pseudocode"

    # Chart sub-elements
    CHART_INFO = "chart_info"
    X_AXIS_TICK_LABEL = "x_axis_tick_label"
    Y_AXIS_TICK_LABEL = "y_axis_tick_label"
    X_AXIS_LABEL = "x_axis_label"
    Y_AXIS_LABEL = "y_axis_label"
    LEGEND_LABEL = "legend_label"
    MODEL_LABEL = "model_label"

    # Diagram elements
    DIAGRAM_INFO = "diagram_info"

    # Document structure
    TITLE = "title"
    SECTION_HEADER = "section_header"
    QUOTE = "quote"
    AUTHORS = "authors"
    ABSTRACT = "abstract"
    COLUMN = "column"
    ROTATED_CONTAINER = "rotated_container"

    # Table elements
    TABLE_CELL = "table_cell"

    # Figure/table labels
    FIGURE_LABEL = "figure_label"
    EQUATION_NUMBER = "equation_number"

    # Form elements
    FORM_FIELD = "form_field"
    QED_SYMBOL = "qed_symbol"
    MULTIPLE_CHOICE_BLOCK = "multiple_choice_block"
    MULTIPLE_CHOICE_OPTION = "multiple_choice_option"

    # Page elements
    PAGE_INFO = "page_info"
    FOOTNOTE = "footnote"

    # Table of contents
    TABLE_OF_CONTENTS_CONTAINER = "table_of_contents_container"
    TABLE_OF_CONTENTS_ROW = "table_of_contents_row"
    TABLE_OF_CONTENTS_ITEM = "table_of_contents_item"
    TABLE_OF_CONTENTS_NUMBER = "table_of_contents_number"


class ElementSubtype(str, Enum):
    """Element subtype classification."""

    # Text subtypes
    VERTICAL = "vertical"
    BIG_CAPITAL_LETTER = "big_capital_letter"

    # Diagram subtypes
    ALGORITHM = "algorithm"
    CHEMISTRY = "chemistry"
    CHEMISTRY_REACTION = "chemistry_reaction"
    TRIANGLE = "triangle"

    # Chart subtypes
    COLUMN_CHART = "column"
    BAR_CHART = "bar"
    LINE_CHART = "line"
    ANALYTICAL_CHART = "analytical"
    PIE_CHART = "pie"
    SCATTER_CHART = "scatter"
    AREA_CHART = "area"

    # Form field subtypes
    PARENTHESES = "parentheses"
    DOTTED = "dotted"
    DASHED = "dashed"
    BOX = "box"
    CHECKBOX = "checkbox"
    CIRCLE = "circle"

    # Table cell subtypes
    SPLIT = "split"
    SPANNING = "spanning"


# =============================================================================
# LAYOUT SCHEMAS
# =============================================================================


class LayoutElement(BaseModel):
    """
    Layout element with spatial and hierarchical information.

    Contains ONLY layout/structural data, NO content.
    """

    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique element identifier")
    type: ElementType = Field(..., description="Element type classification")
    subtype: Optional[ElementSubtype] = Field(
        default=None,
        description="Fine-grained variant",
    )

    # Spatial information
    region: Optional[Region] = Field(
        default=None,
        description="Bounding box",
    )
    cnt: Optional[list[list[int]]] = Field(
        default=None,
        description="Polygon contour [[x,y], ...]",
    )

    # Position information
    column: Optional[int] = Field(
        default=None,
        ge=0,
        description="Column index (0-based for multi-column)",
    )
    line: Optional[int] = Field(
        default=None,
        ge=0,
        description="Line number within region",
    )

    # Typography
    font_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="Font size in pixels",
    )

    # Hierarchy
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent element ID",
    )
    children_ids: list[str] = Field(
        default_factory=list,
        description="Child element IDs",
    )

    # Flags
    conversion_output: bool = Field(
        default=True,
        description="Included in top-level OCR result",
    )
    error_id: Optional[str] = Field(
        default=None,
        description="Error reason if conversion_output=False",
    )

    # Labels (for chart/diagram elements)
    selected_labels: Optional[list[str]] = Field(
        default=None,
        description="Selected labels for chart/diagram elements",
    )


class LayoutMetadata(BaseModel):
    """Metadata for layout extraction."""

    source: str = Field(default="mathpix", description="Extraction source")
    version: str = Field(default="1.0.0")
    extracted_at: datetime = Field(default_factory=datetime.now)
    element_count: int = Field(default=0, ge=0)
    hierarchy_depth: int = Field(default=0, ge=0)

    # Optional statistics
    column_count: Optional[int] = None
    total_bbox_area: Optional[int] = None


class LayoutData(BaseModel):
    """
    Complete layout data for an image.

    Contains all spatial, hierarchical, and structural information.
    """

    elements: list[LayoutElement] = Field(
        default_factory=list,
        description="Layout elements",
    )
    page: PageInfo = Field(
        default_factory=PageInfo,
        description="Page metadata",
    )
    metadata: LayoutMetadata = Field(
        default_factory=LayoutMetadata,
    )

    def get_element_by_id(self, element_id: str) -> Optional[LayoutElement]:
        """Find element by ID."""
        for elem in self.elements:
            if elem.id == element_id:
                return elem
        return None

    def get_elements_by_type(self, elem_type: ElementType) -> list[LayoutElement]:
        """Get all elements of a specific type."""
        return [e for e in self.elements if e.type == elem_type]

    def get_children(self, parent_id: str) -> list[LayoutElement]:
        """Get child elements of a parent."""
        return [e for e in self.elements if e.parent_id == parent_id]


# =============================================================================
# CONTENT SCHEMAS
# =============================================================================


class QualityMetrics(BaseModel):
    """Quality metrics for content extraction."""

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="100% correctness probability",
    )
    confidence_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Output quality estimate",
    )

    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high (>= 0.95)."""
        return (self.confidence or 0) >= 0.95

    @property
    def needs_review(self) -> bool:
        """Check if confidence is low enough to need review (< 0.75)."""
        conf = self.confidence or self.confidence_rate or 0
        return conf < 0.75


class ContentElement(BaseModel):
    """
    Content element with textual and semantic information.

    Contains ONLY content/problem data, NO spatial info.
    References LayoutElement by ID.
    """

    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique element identifier (matches layout)")
    layout_ref: Optional[str] = Field(
        default=None,
        description="Reference to LayoutElement.id",
    )

    # Text content
    text: Optional[str] = Field(
        default=None,
        description="Mathpix Markdown text",
    )
    text_display: Optional[str] = Field(
        default=None,
        description="Display-formatted text",
    )

    # Math content
    latex: Optional[str] = Field(
        default=None,
        description="Math-mode LaTeX",
    )
    latex_styled: Optional[str] = Field(
        default=None,
        description="Styled LaTeX for equations",
    )

    # Multi-format data
    data: list[DataObject] = Field(
        default_factory=list,
        description="Additional format outputs (asciimath, mathml, svg, etc.)",
    )

    # Quality metrics
    quality: QualityMetrics = Field(
        default_factory=QualityMetrics,
    )

    # Detection flags
    is_printed: Optional[bool] = Field(
        default=None,
        description="Printed content detected",
    )
    is_handwritten: Optional[bool] = Field(
        default=None,
        description="Handwritten content detected",
    )

    # HTML output
    html: Optional[str] = Field(
        default=None,
        description="HTML rendering",
    )

    # Text flow
    after_hyphen: Optional[bool] = Field(
        default=None,
        description="Text continues from hyphenated word on previous line",
    )


class QualitySummary(BaseModel):
    """Summary of content quality across all elements."""

    total_elements: int = Field(default=0, ge=0)
    high_confidence_count: int = Field(default=0, ge=0)
    low_confidence_count: int = Field(default=0, ge=0)
    needs_review_count: int = Field(default=0, ge=0)

    average_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    min_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    @property
    def high_confidence_ratio(self) -> float:
        """Ratio of high-confidence elements."""
        if self.total_elements == 0:
            return 0.0
        return self.high_confidence_count / self.total_elements


class DetectedAlphabets(BaseModel):
    """Writing system detection results."""

    en: Optional[bool] = Field(default=None, description="English/Latin")
    ko: Optional[bool] = Field(default=None, description="Korean")
    zh: Optional[bool] = Field(default=None, description="Chinese")
    ja: Optional[bool] = Field(default=None, description="Japanese")
    ru: Optional[bool] = Field(default=None, description="Russian/Cyrillic")
    hi: Optional[bool] = Field(default=None, description="Hindi")
    th: Optional[bool] = Field(default=None, description="Thai")


class ContentMetadata(BaseModel):
    """Metadata for content extraction."""

    source: str = Field(default="mathpix", description="Extraction source")
    version: str = Field(default="1.0.0")
    extracted_at: datetime = Field(default_factory=datetime.now)
    element_count: int = Field(default=0, ge=0)

    # Language detection
    detected_alphabets: Optional[DetectedAlphabets] = None

    # Request info
    request_id: Optional[str] = None


class ContentData(BaseModel):
    """
    Complete content data for an image.

    Contains all textual, mathematical, and semantic information.
    """

    elements: list[ContentElement] = Field(
        default_factory=list,
        description="Content elements",
    )
    quality_summary: QualitySummary = Field(
        default_factory=QualitySummary,
        description="Aggregated quality metrics",
    )
    metadata: ContentMetadata = Field(
        default_factory=ContentMetadata,
    )

    def get_element_by_id(self, element_id: str) -> Optional[ContentElement]:
        """Find element by ID."""
        for elem in self.elements:
            if elem.id == element_id:
                return elem
        return None

    def get_elements_needing_review(self) -> list[ContentElement]:
        """Get elements that need human review."""
        return [e for e in self.elements if e.quality.needs_review]

    def compute_quality_summary(self) -> None:
        """Compute quality summary from elements."""
        if not self.elements:
            self.quality_summary = QualitySummary()
            return

        confidences = []
        high_conf = 0
        low_conf = 0
        needs_review = 0

        for elem in self.elements:
            conf = elem.quality.confidence or elem.quality.confidence_rate
            if conf is not None:
                confidences.append(conf)
                if conf >= 0.95:
                    high_conf += 1
                elif conf < 0.75:
                    low_conf += 1
                    needs_review += 1

        self.quality_summary = QualitySummary(
            total_elements=len(self.elements),
            high_confidence_count=high_conf,
            low_confidence_count=low_conf,
            needs_review_count=needs_review,
            average_confidence=sum(confidences) / len(confidences) if confidences else None,
            min_confidence=min(confidences) if confidences else None,
        )


# =============================================================================
# COMBINED DOCUMENT
# =============================================================================


class SeparatedDocument(BaseModel):
    """
    Combined document with separated Layout and Content data.

    Represents the full output of the separation process.
    """

    image_path: str = Field(..., description="Source image path")
    layout: LayoutData = Field(default_factory=LayoutData)
    content: ContentData = Field(default_factory=ContentData)

    # Processing info
    processing_version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

    def validate_references(self) -> list[str]:
        """Validate that content elements reference valid layout elements."""
        layout_ids = {e.id for e in self.layout.elements}
        errors = []

        for content_elem in self.content.elements:
            if content_elem.layout_ref and content_elem.layout_ref not in layout_ids:
                errors.append(
                    f"Content element {content_elem.id} references "
                    f"non-existent layout element {content_elem.layout_ref}"
                )

        return errors


__all__ = [
    # Shared types
    "Region",
    "DataFormat",
    "DataObject",
    "PageInfo",
    # Element types
    "ElementType",
    "ElementSubtype",
    # Layout
    "LayoutElement",
    "LayoutMetadata",
    "LayoutData",
    # Content
    "QualityMetrics",
    "ContentElement",
    "QualitySummary",
    "DetectedAlphabets",
    "ContentMetadata",
    "ContentData",
    # Combined
    "SeparatedDocument",
]
