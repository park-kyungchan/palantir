"""
COW CLI - Mathpix API Schemas

Pydantic models for Mathpix API request/response validation.
Based on: Mathpix API Documentation (context7:/websites/mathpix)

Schema Design:
- PdfLineData: PDF API lines.json 응답의 각 라인 (기존 LineData 확장)
- PdfPageData: PDF API pages 배열의 각 페이지
- UnifiedResponse: PDF와 Image API 응답을 통합하는 정규화된 응답
"""
from typing import Optional, Literal, Any, List
from pydantic import BaseModel, Field


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class DataOptions(BaseModel):
    """Nested data options for structured output."""

    include_latex: bool = Field(default=True, description="Math-mode LaTeX in outputs")
    include_asciimath: bool = Field(default=True, description="AsciiMath notation")
    include_mathml: bool = Field(default=True, description="MathML format")
    include_svg: bool = Field(default=True, description="Math SVG in html and data")
    include_table_html: bool = Field(default=True, description="Table HTML")
    include_tsv: bool = Field(default=True, description="Tab-separated values for tables")


class AlphabetsAllowed(BaseModel):
    """Restrict output to specific alphabets."""

    en: bool = True
    ko: bool = True
    zh: bool = False
    ja: bool = False
    ru: bool = False
    hi: bool = False
    th: bool = False
    ta: bool = False
    te: bool = False
    gu: bool = False
    bn: bool = False
    vi: bool = False


class FormatOptions(BaseModel):
    """
    LaTeX format customization options.

    Allows customization of output format transforms and delimiters.
    Keys are format names, values are option objects.
    """

    transforms: Optional[list[str]] = Field(
        default=None,
        description="Array of transformation names: rm_spaces, rm_newlines, rm_fonts, rm_style_syms, rm_text, long_frac",
    )
    math_delims: Optional[list[str]] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="[begin, end] delimiters for math mode",
    )
    displaymath_delims: Optional[list[str]] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="[begin, end] delimiters for displaymath mode",
    )


class CallbackObject(BaseModel):
    """Callback configuration for async requests."""

    post: str = Field(description="URL to POST results to")
    headers: Optional[dict[str, str]] = Field(
        default=None,
        description="Additional headers for callback request",
    )


class Region(BaseModel):
    """Bounding box for image region processing."""

    top_left_x: int = Field(..., description="X coordinate of top-left corner")
    top_left_y: int = Field(..., description="Y coordinate of top-left corner")
    width: int = Field(..., ge=1, description="Width in pixels")
    height: int = Field(..., ge=1, description="Height in pixels")


class MathpixRequest(BaseModel):
    """
    Request model for Mathpix /v3/text endpoint.

    Note: src or file must be provided, but not in this model
    as file upload is handled separately.

    NEW in v2.0: Added metadata, tags, async_mode, callback, enable_blue_hsv_filter,
    confidence_threshold, format_options for complete Mathpix API coverage.
    (비용은 요청당 과금이며, 옵션 On/Off와 무관)
    """

    # Input (src is set separately for base64/URL)
    src: Optional[str] = Field(default=None, description="Image URL or base64 data")
    region: Optional[Region] = Field(default=None, description="Image region to process")

    # Metadata & Tags (NEW)
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Custom key-value metadata attached to request",
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Tags for identifying/filtering results in ocr-results",
    )

    # Async processing (NEW)
    async_mode: Optional[bool] = Field(
        default=None,
        alias="async",
        description="Enable async processing for non-interactive requests",
    )
    callback: Optional[CallbackObject] = Field(
        default=None,
        description="Callback URL for async result delivery",
    )

    # Output formats
    formats: list[str] = Field(
        default=["text", "data", "html", "latex_styled"],  # All formats enabled by default
        description="Output format types",
    )
    data_options: DataOptions = Field(
        default_factory=DataOptions,
        description="Structured data extraction options",
    )
    format_options: Optional[dict[str, FormatOptions]] = Field(
        default=None,
        description="Per-format customization options (transforms, delimiters)",
    )

    # Segmentation (TOP-LEVEL)
    include_line_data: bool = Field(
        default=False,
        description="DISABLED - mutually exclusive with word_data",
    )
    include_word_data: bool = Field(
        default=True,
        description="Word-level segmentation with bbox",
    )
    include_diagram_text: bool = Field(default=True, description="Diagram text extraction")
    include_geometry_data: bool = Field(default=True, description="Geometry extraction")
    include_detected_alphabets: bool = Field(default=True, description="Alphabet detection")
    include_page_info: bool = Field(default=True, description="Page metadata")

    # Math delimiters
    math_inline_delimiters: list[str] = Field(
        default=["$", "$"],
        min_length=2,
        max_length=2,
    )
    math_display_delimiters: list[str] = Field(
        default=["$$", "$$"],
        min_length=2,
        max_length=2,
    )

    # LaTeX style (TOP-LEVEL)
    rm_spaces: bool = Field(default=True, description="Remove excess whitespace")
    rm_fonts: bool = Field(default=False, description="Remove font commands")
    idiomatic_eqn_arrays: bool = Field(default=True, description="Use aligned/gathered/cases")
    idiomatic_braces: bool = Field(default=True, description="Omit unnecessary braces")
    include_equation_tags: bool = Field(default=True, description="Add \\tag{} to equations")
    numbers_default_to_math: bool = Field(default=False)
    math_fonts_default_to_math: bool = Field(default=False)

    # Chemistry (disabled for COW)
    include_smiles: bool = Field(default=False, description="Chemistry SMILES notation")
    include_inchi: bool = Field(default=False, description="Chemistry InChI data")

    # Language
    alphabets_allowed: AlphabetsAllowed = Field(default_factory=AlphabetsAllowed)
    fullwidth_punctuation: Optional[bool] = Field(
        default=None,
        description="null=auto-detect",
    )

    # Image processing (NEW)
    enable_blue_hsv_filter: bool = Field(
        default=False,
        description="Enable OCR for blue hue text exclusively",
    )

    # Confidence thresholds
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Threshold for triggering confidence errors (document-level)",
    )
    confidence_rate_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Threshold for triggering confidence errors (symbol-level)",
    )
    auto_rotate_confidence_threshold: float = Field(
        default=0.99,
        ge=0.0,
        le=1.0,
    )

    # Tables
    enable_tables_fallback: bool = Field(default=True, description="Advanced table processing")

    def to_api_dict(self) -> dict:
        """Convert to API request format with proper nesting."""
        data = self.model_dump(exclude_none=True, by_alias=True)

        # Handle async_mode → async rename (async is Python keyword)
        if "async_mode" in data:
            data["async"] = data.pop("async_mode")

        # Convert nested AlphabetsAllowed to dict
        if isinstance(data.get("alphabets_allowed"), dict):
            pass  # Already a dict from model_dump

        # Convert FormatOptions to dict
        if "format_options" in data and data["format_options"]:
            format_opts = {}
            for fmt_name, opts in data["format_options"].items():
                if isinstance(opts, dict):
                    format_opts[fmt_name] = {k: v for k, v in opts.items() if v is not None}
            data["format_options"] = format_opts

        return data


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class DataObject(BaseModel):
    """Structured data element from data_options."""

    type: Literal["latex", "asciimath", "mathml", "svg", "table_html", "tsv"]
    value: str


class WordData(BaseModel):
    """Word-level segmentation data."""

    type: Literal["text", "math", "table", "diagram", "equation_number", "chart_info"]
    subtype: Optional[str] = None
    text: Optional[str] = None
    latex: Optional[str] = None
    cnt: list[list[int]] = Field(description="Contour coordinates [[x,y], ...]")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class LineData(BaseModel):
    """Line-level segmentation data (if include_line_data=true)."""

    id: str
    parent_id: Optional[str] = None
    children_ids: Optional[list[str]] = None
    type: str
    subtype: Optional[str] = None
    text: Optional[str] = None
    text_display: Optional[str] = None
    latex: Optional[str] = None  # Math-mode LaTeX
    latex_styled: Optional[str] = None  # Styled LaTeX for equations
    cnt: list[list[int]]
    region: Optional[Region] = None
    conversion_output: bool = True
    is_printed: Optional[bool] = None
    is_handwritten: Optional[bool] = None
    confidence: Optional[float] = None
    confidence_rate: Optional[float] = None
    font_size: Optional[int] = None
    line: Optional[int] = None
    column: Optional[int] = None
    after_hyphen: Optional[bool] = None
    html: Optional[str] = None
    data: Optional[list[DataObject]] = None
    error_id: Optional[str] = None
    selected_labels: Optional[list[str]] = None


class DetectedAlphabets(BaseModel):
    """Detected writing systems."""

    en: Optional[bool] = None
    ko: Optional[bool] = None
    zh: Optional[bool] = None
    ja: Optional[bool] = None
    ru: Optional[bool] = None
    hi: Optional[bool] = None
    th: Optional[bool] = None


class ErrorInfo(BaseModel):
    """Structured error details."""

    id: str
    error: str


class MathpixResponse(BaseModel):
    """Response model for Mathpix /v3/text endpoint."""

    request_id: str = Field(description="Unique request identifier")

    # Main content
    text: Optional[str] = Field(default=None, description="Mathpix Markdown output")
    latex_styled: Optional[str] = Field(default=None, description="Styled LaTeX")
    html: Optional[str] = Field(default=None, description="HTML output")
    data: Optional[list[DataObject]] = Field(default=None, description="Structured data")

    # Segmentation
    word_data: Optional[list[WordData]] = Field(default=None)
    line_data: Optional[list[LineData]] = Field(default=None)

    # Confidence
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Detection flags
    is_printed: Optional[bool] = None
    is_handwritten: Optional[bool] = None
    detected_alphabets: Optional[DetectedAlphabets] = None

    # Auto-rotation
    auto_rotate_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    auto_rotate_degrees: Optional[Literal[0, 90, -90, 180]] = None

    # Geometry
    geometry_data: Optional[list[dict]] = None

    # Image info
    image_width: Optional[int] = None
    image_height: Optional[int] = None

    # Version
    version: Optional[str] = None

    # Error
    error: Optional[str] = None
    error_info: Optional[ErrorInfo] = None

    def has_error(self) -> bool:
        """Check if response contains an error."""
        return self.error is not None or self.error_info is not None

    def get_confidence(self) -> float:
        """Get overall confidence score."""
        return self.confidence or self.confidence_rate or 0.0


# =============================================================================
# PDF API SCHEMAS (lines.json response)
# =============================================================================

# PdfLineData is an alias for LineData (same structure)
PdfLineData = LineData


class PdfPageData(BaseModel):
    """
    PDF API pages 배열의 각 페이지 데이터.

    GET /v3/pdf/{pdf_id}.lines.json 응답의 pages[] 요소
    """

    image_id: str = Field(description="PDF ID + '-' + page number (e.g., 'abc123-1')")
    page: int = Field(ge=1, description="Page number (1-indexed)")
    lines: List[PdfLineData] = Field(default_factory=list, description="Line data for this page")
    page_height: int = Field(default=0, ge=0, description="Page height in pixels")
    page_width: int = Field(default=0, ge=0, description="Page width in pixels")


class ResponseMetadata(BaseModel):
    """Unified response metadata."""

    request_id: str = Field(description="Unique request/PDF ID")
    source_type: Literal["pdf", "image"] = Field(description="Source type")
    version: Optional[str] = Field(default=None, description="API version")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = Field(default=None, ge=0)


class UnifiedResponse(BaseModel):
    """
    PDF와 Image API 응답을 통합하는 정규화된 응답 모델.

    - PDF API: pages[] 구조 그대로 사용
    - Image API: line_data[]를 pages[0].lines[]로 정규화

    이를 통해 LayoutContentSeparator가 동일한 인터페이스로 처리 가능
    """

    metadata: ResponseMetadata
    pages: List[PdfPageData] = Field(default_factory=list)
    raw_response: Optional[dict] = Field(default=None, description="Original API response")

    # Convenience properties
    @property
    def total_lines(self) -> int:
        """Get total number of lines across all pages."""
        return sum(len(page.lines) for page in self.pages)

    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        return len(self.pages)

    def get_all_lines(self) -> List[PdfLineData]:
        """Flatten all lines from all pages into a single list."""
        lines = []
        for page in self.pages:
            lines.extend(page.lines)
        return lines

    @classmethod
    def from_pdf_response(
        cls,
        pdf_id: str,
        lines_data: dict,
        status_data: Optional[dict] = None,
    ) -> "UnifiedResponse":
        """
        PDF API 응답에서 UnifiedResponse 생성.

        Args:
            pdf_id: PDF processing ID
            lines_data: /v3/pdf/{id}.lines.json response
            status_data: /v3/pdf/{id} status response (optional)
        """
        status_data = status_data or {}
        pages = []

        for page_data in lines_data.get("pages", []):
            lines = []
            for line in page_data.get("lines", []):
                # Ensure required fields have defaults
                line_obj = PdfLineData(
                    id=line.get("id", ""),
                    type=line.get("type", "text"),
                    subtype=line.get("subtype"),
                    text=line.get("text"),
                    text_display=line.get("text_display"),
                    latex=line.get("latex"),  # Preserve latex
                    latex_styled=line.get("latex_styled"),  # Preserve styled latex
                    cnt=line.get("cnt", []),
                    region=line.get("region"),
                    parent_id=line.get("parent_id"),
                    children_ids=line.get("children_ids"),
                    conversion_output=line.get("conversion_output", True),
                    is_printed=line.get("is_printed"),
                    is_handwritten=line.get("is_handwritten"),
                    confidence=line.get("confidence"),
                    confidence_rate=line.get("confidence_rate"),
                    font_size=line.get("font_size"),
                    line=line.get("line"),
                    column=line.get("column"),
                    after_hyphen=line.get("after_hyphen"),  # Preserve hyphen info
                    html=line.get("html"),  # Preserve HTML
                    data=line.get("data"),  # Preserve data array
                    error_id=line.get("error_id"),  # Preserve error info
                    selected_labels=line.get("selected_labels"),  # Preserve labels
                )
                lines.append(line_obj)

            pages.append(PdfPageData(
                image_id=page_data.get("image_id", f"{pdf_id}-{page_data.get('page', 1)}"),
                page=page_data.get("page", 1),
                lines=lines,
                page_height=page_data.get("page_height", 0),
                page_width=page_data.get("page_width", 0),
            ))

        return cls(
            metadata=ResponseMetadata(
                request_id=pdf_id,
                source_type="pdf",
                confidence=status_data.get("confidence"),
                confidence_rate=status_data.get("confidence_rate"),
            ),
            pages=pages,
            raw_response={"lines": lines_data, "status": status_data},
        )

    @classmethod
    def from_image_response(cls, response_data: dict) -> "UnifiedResponse":
        """
        Image API 응답에서 UnifiedResponse 생성.

        line_data[]를 pages[0].lines[]로 정규화하여 PDF와 동일한 인터페이스 제공.

        Args:
            response_data: /v3/text response
        """
        line_data = response_data.get("line_data", [])
        lines = []

        for i, line in enumerate(line_data):
            line_obj = PdfLineData(
                id=line.get("id", str(i)),
                type=line.get("type", "text"),
                subtype=line.get("subtype"),
                text=line.get("text"),
                text_display=line.get("text_display") or line.get("text"),  # Fallback to text
                latex=line.get("latex"),  # Preserve latex
                latex_styled=line.get("latex_styled"),  # Preserve styled latex
                cnt=line.get("cnt", []),
                region=line.get("region"),
                parent_id=line.get("parent_id"),
                children_ids=line.get("children_ids"),
                conversion_output=line.get("conversion_output", True),
                is_printed=line.get("is_printed"),
                is_handwritten=line.get("is_handwritten"),
                confidence=line.get("confidence"),
                confidence_rate=line.get("confidence_rate"),
                font_size=line.get("font_size"),  # Preserve font size
                line=line.get("line"),  # Preserve line number
                column=line.get("column"),  # Preserve column
                after_hyphen=line.get("after_hyphen"),  # Preserve hyphen info
                html=line.get("html"),  # Preserve HTML
                data=line.get("data"),  # Preserve data array
                error_id=line.get("error_id"),  # Preserve error info
                selected_labels=line.get("selected_labels"),  # Preserve labels
            )
            lines.append(line_obj)

        request_id = response_data.get("request_id", "")

        return cls(
            metadata=ResponseMetadata(
                request_id=request_id,
                source_type="image",
                version=response_data.get("version"),
                confidence=response_data.get("confidence"),
                confidence_rate=response_data.get("confidence_rate"),
            ),
            pages=[PdfPageData(
                image_id=f"{request_id}-1",
                page=1,
                lines=lines,
                page_height=response_data.get("image_height", 0),
                page_width=response_data.get("image_width", 0),
            )],
            raw_response=response_data,
        )


__all__ = [
    # Request schemas
    "DataOptions",
    "AlphabetsAllowed",
    "FormatOptions",  # NEW
    "CallbackObject",  # NEW
    "Region",
    "MathpixRequest",
    # Response schemas (Image API)
    "DataObject",
    "WordData",
    "LineData",
    "DetectedAlphabets",
    "ErrorInfo",
    "MathpixResponse",
    # PDF API schemas
    "PdfLineData",
    "PdfPageData",
    # Unified schemas
    "ResponseMetadata",
    "UnifiedResponse",
]
