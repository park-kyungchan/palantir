"""OcrResult for Stage 2→3 transition. Most complex model — carries Mathpix output."""

from pydantic import BaseModel, Field
from typing import Optional, Literal

from cow_mcp.models.common import BBox


class MathElement(BaseModel):
    """A detected mathematical expression."""
    id: str
    latex: str = Field(..., description="LaTeX representation")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Optional[BBox] = None
    is_inline: bool = Field(True, description="Inline vs display math")


class OcrRegion(BaseModel):
    """A detected content region with bounding box."""
    id: str
    type: Literal["text", "math", "table", "diagram", "chart", "figure", "equation_number"]
    bbox: BBox
    content: Optional[str] = Field(None, description="Text content if applicable")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    parent_id: Optional[str] = None
    children_ids: list[str] = Field(default_factory=list)


class Diagram(BaseModel):
    """A detected diagram or chart."""
    id: str
    type: Literal["chart", "figure", "table", "geometry", "graph", "flowchart", "other"]
    subtype: Optional[str] = Field(None, description="e.g., bar_chart, pie_chart")
    bbox: BBox
    caption: Optional[str] = None
    text_content: Optional[str] = Field(None, description="Extracted text from diagram")


class OcrResult(BaseModel):
    """Output of OCR stage. Input to VISION stage."""
    text: str = Field(..., description="Full text in MMD format")
    math_elements: list[MathElement] = Field(default_factory=list)
    regions: list[OcrRegion] = Field(default_factory=list)
    diagrams: list[Diagram] = Field(default_factory=list)
    raw_response: dict = Field(default_factory=dict, description="Mathpix raw JSON")
    page_dimensions: Optional[dict] = Field(None, description="{width, height} in pixels")
    detected_languages: list[str] = Field(default_factory=list)
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
