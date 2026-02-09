"""VisionResult for Stage 3→4 transition. Merges Mathpix + Gemini data."""

from pydantic import BaseModel, Field
from typing import Optional, Literal

from cow_mcp.models.common import BBox, RegionSource
from cow_mcp.models.ocr import OcrResult


class DiagramElement(BaseModel):
    """An internal element within a diagram (detected by Gemini)."""
    id: str
    type: Literal["axis", "label", "data_point", "line", "shape", "arrow", "text", "legend"]
    bbox: BBox
    content: Optional[str] = None


class DiagramInternals(BaseModel):
    """Internal structure of a diagram detected by Gemini vision."""
    diagram_id: str
    elements: list[DiagramElement] = Field(default_factory=list)
    bbox: BBox


class SpatialRelation(BaseModel):
    """Spatial relationship between two regions."""
    source_id: str
    target_id: str
    relation: Literal["above", "below", "left_of", "right_of", "contains", "adjacent"]


class LayoutAnalysis(BaseModel):
    """Layout analysis from Gemini vision."""
    columns: int = Field(1, ge=1, description="Detected column count")
    reading_order: list[str] = Field(default_factory=list, description="Region IDs in reading order")
    spatial_relations: list[SpatialRelation] = Field(default_factory=list)


class CombinedRegion(BaseModel):
    """A region with source attribution (Mathpix, Gemini, or merged)."""
    id: str
    type: str
    bbox: BBox
    source: RegionSource
    confidence: Optional[float] = None
    content: Optional[str] = None


class VisionResult(BaseModel):
    """Output of VISION stage. Input to VERIFY stage."""
    ocr_result: OcrResult
    diagram_internals: list[DiagramInternals] = Field(default_factory=list)
    layout_analysis: LayoutAnalysis = Field(default_factory=LayoutAnalysis)
    combined_regions: list[CombinedRegion] = Field(default_factory=list)
