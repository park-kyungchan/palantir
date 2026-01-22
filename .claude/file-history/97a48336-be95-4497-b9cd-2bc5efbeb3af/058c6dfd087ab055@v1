"""
TextSpec Schema for Stage B (Text Parse) Output.

Stage B processes Mathpix API responses and extracts:
- Equations and text content
- Content flags for downstream processing
- Vision parse triggers
- Line segments with bbox and confidence

Schema Version: 2.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from .common import (
    BBox,
    Confidence,
    MathpixBaseModel,
    Provenance,
    ReviewMetadata,
    ReviewSeverity,
    WritingStyle,
    utc_now,
)


# =============================================================================
# Enums
# =============================================================================

class VisionParseTrigger(str, Enum):
    """Reasons to trigger Stage C (Vision Parse)."""
    DIAGRAM_EXTRACTION = "DIAGRAM_EXTRACTION"
    GRAPH_ANALYSIS = "GRAPH_ANALYSIS"
    GEOMETRY_DETECTION = "GEOMETRY_DETECTION"
    COORDINATE_SYSTEM = "COORDINATE_SYSTEM"
    FUNCTION_GRAPH = "FUNCTION_GRAPH"
    TABLE_STRUCTURE = "TABLE_STRUCTURE"
    LOW_CONFIDENCE_REGION = "LOW_CONFIDENCE_REGION"


class ContentType(str, Enum):
    """Types of content detected in the image."""
    EQUATION = "equation"
    TEXT = "text"
    DIAGRAM = "diagram"
    GRAPH = "graph"
    TABLE = "table"
    GEOMETRY = "geometry"
    MIXED = "mixed"


# =============================================================================
# Sub-Models
# =============================================================================

class ContentFlags(MathpixBaseModel):
    """Flags indicating content types present in the image.

    Used to determine which processing paths to activate.
    """
    contains_equation: bool = Field(default=False)
    contains_text: bool = Field(default=False)
    contains_diagram: bool = Field(default=False)
    contains_graph: bool = Field(default=False)
    contains_geometry: bool = Field(default=False)
    contains_table: bool = Field(default=False)
    contains_handwriting: bool = Field(default=False)

    def should_trigger_vision_parse(self) -> bool:
        """Determine if Stage C should be triggered."""
        return (
            self.contains_diagram or
            self.contains_graph or
            self.contains_geometry
        )


class DetectionMapEntry(MathpixBaseModel):
    """Single entry from Mathpix detection_map.

    Represents a detected region with its type and confidence.
    """
    type: str = Field(..., description="Detection type from Mathpix")
    bbox: BBox = Field(..., description="Bounding box of detected region")
    confidence: float = Field(..., ge=0.0, le=1.0)
    content: Optional[str] = Field(default=None, description="Extracted content if available")


class LineSegment(MathpixBaseModel):
    """A line segment from Mathpix line_data.

    Represents a single line of text/math with its properties.
    """
    id: str = Field(..., description="Unique identifier for this line")
    bbox: BBox = Field(..., description="Bounding box of the line")
    text: str = Field(..., description="Extracted text content")
    latex: Optional[str] = Field(default=None, description="LaTeX representation if math")
    confidence: Confidence = Field(..., description="Confidence score")
    writing_style: WritingStyle = Field(default=WritingStyle.PRINTED)
    content_type: ContentType = Field(default=ContentType.TEXT)

    # Hierarchy
    line_number: int = Field(..., ge=0, description="Line number in sequence")
    parent_region_id: Optional[str] = Field(default=None)


class EquationElement(MathpixBaseModel):
    """A detected equation element."""
    id: str = Field(..., description="Unique identifier")
    bbox: BBox = Field(..., description="Bounding box")
    latex: str = Field(..., description="LaTeX representation")
    latex_styled: Optional[str] = Field(default=None, description="Styled LaTeX")
    confidence: Confidence
    asciimath: Optional[str] = Field(default=None, description="AsciiMath conversion")
    mathml: Optional[str] = Field(default=None, description="MathML conversion")

    # Review
    review: ReviewMetadata = Field(default_factory=ReviewMetadata)


# =============================================================================
# Main Schema
# =============================================================================

class TextSpec(MathpixBaseModel):
    """Stage B output: Text Parse specification.

    Contains all text/equation content extracted from the image
    plus metadata for downstream processing.

    v2.0.0 Additions:
    - content_flags: Structured content type detection
    - vision_parse_triggers: Explicit Stage C triggers
    - line_segments: Full line data with hierarchy
    - detection_map: Raw Mathpix detection regions
    """
    # Metadata
    schema_version: str = Field(default="2.0.0")
    image_id: str = Field(..., description="Source image identifier")
    provenance: Provenance = Field(default_factory=lambda: Provenance(
        stage="B",
        model="mathpix-api-v3"
    ))

    # Content flags (v2.0.0)
    content_flags: ContentFlags = Field(default_factory=ContentFlags)

    # Stage C triggers (v2.0.0)
    vision_parse_triggers: List[VisionParseTrigger] = Field(
        default_factory=list,
        description="Reasons to invoke Stage C"
    )

    # Global writing style
    writing_style: WritingStyle = Field(default=WritingStyle.PRINTED)

    # Mathpix raw outputs
    text: str = Field(default="", description="Full extracted text")
    latex: Optional[str] = Field(default=None, description="Full LaTeX content")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")

    # Structured elements (v2.0.0)
    line_segments: List[LineSegment] = Field(
        default_factory=list,
        description="Line-by-line content with hierarchy"
    )
    equations: List[EquationElement] = Field(
        default_factory=list,
        description="Detected equations"
    )
    detection_map: List[DetectionMapEntry] = Field(
        default_factory=list,
        description="Mathpix detection regions"
    )

    # Raw Mathpix response (for debugging)
    raw_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Original Mathpix API response"
    )

    # Review
    review: ReviewMetadata = Field(default_factory=ReviewMetadata)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    processing_time_ms: Optional[float] = Field(default=None)

    def should_trigger_vision_parse(self) -> bool:
        """Check if Stage C should be triggered."""
        return (
            self.content_flags.should_trigger_vision_parse() or
            len(self.vision_parse_triggers) > 0
        )

    def get_trigger_reasons(self) -> List[str]:
        """Get human-readable trigger reasons."""
        reasons = []
        if self.content_flags.contains_diagram:
            reasons.append("Contains diagram")
        if self.content_flags.contains_graph:
            reasons.append("Contains graph")
        if self.content_flags.contains_geometry:
            reasons.append("Contains geometry")
        for trigger in self.vision_parse_triggers:
            reasons.append(trigger.value)
        return reasons


# =============================================================================
# Factory Functions
# =============================================================================

def create_text_spec_from_mathpix(
    image_id: str,
    mathpix_response: Dict[str, Any],
    processing_time_ms: Optional[float] = None,
) -> TextSpec:
    """Create TextSpec from Mathpix API response.

    Args:
        image_id: Source image identifier
        mathpix_response: Raw Mathpix API response
        processing_time_ms: Time taken for API call

    Returns:
        TextSpec with extracted content
    """
    # Extract content flags from detection_map
    content_flags = ContentFlags()
    detection_map_raw = mathpix_response.get("detection_map", {})

    # Parse detection_map entries
    detection_entries = []
    for det_type, regions in detection_map_raw.items():
        if det_type == "contains_diagram":
            content_flags.contains_diagram = True
        elif det_type == "contains_graph":
            content_flags.contains_graph = True
        # Add more mappings as needed

    # Determine triggers
    triggers = []
    if content_flags.contains_diagram:
        triggers.append(VisionParseTrigger.DIAGRAM_EXTRACTION)
    if content_flags.contains_graph:
        triggers.append(VisionParseTrigger.GRAPH_ANALYSIS)

    # Build TextSpec
    return TextSpec(
        image_id=image_id,
        content_flags=content_flags,
        vision_parse_triggers=triggers,
        text=mathpix_response.get("text", ""),
        latex=mathpix_response.get("latex", None),
        confidence=mathpix_response.get("confidence", 0.0),
        raw_response=mathpix_response,
        processing_time_ms=processing_time_ms,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "VisionParseTrigger",
    "ContentType",
    # Models
    "ContentFlags",
    "DetectionMapEntry",
    "LineSegment",
    "EquationElement",
    "TextSpec",
    # Functions
    "create_text_spec_from_mathpix",
]
