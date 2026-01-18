"""
VisionSpec Schema for Stage C (Vision Parse) Output.

Stage C implements YOLO + Claude Hybrid Architecture:
- Detection Layer: YOLO26 for bbox detection
- Interpretation Layer: Claude Opus 4.5 for semantic understanding
- Merged Output: Combined results with provenance tracking

Schema Version: 2.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, computed_field

from .common import (
    BBox,
    BBoxYOLO,
    CombinedConfidence,
    Confidence,
    MathpixBaseModel,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    utc_now,
)


# =============================================================================
# Enums
# =============================================================================

class DiagramType(str, Enum):
    """Types of diagrams that can be detected."""
    FUNCTION_GRAPH = "function_graph"
    COORDINATE_SYSTEM = "coordinate_system"
    GEOMETRY = "geometry"
    NUMBER_LINE = "number_line"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    VENN_DIAGRAM = "venn_diagram"
    FLOWCHART = "flowchart"
    TABLE = "table"
    UNKNOWN = "unknown"


class ElementClass(str, Enum):
    """YOLO detection classes for math elements."""
    AXIS = "axis"
    CURVE = "curve"
    POINT = "point"
    LABEL = "label"
    GRID = "grid"
    ARROW = "arrow"
    LINE_SEGMENT = "line_segment"
    CIRCLE = "circle"
    POLYGON = "polygon"
    ANGLE = "angle"
    EQUATION_REGION = "equation_region"
    TEXT_REGION = "text_region"
    UNKNOWN = "unknown"


class RelationType(str, Enum):
    """Relationship types between visual elements."""
    LABEL_OF = "label_of"
    POINT_ON = "point_on"
    INTERSECTS = "intersects"
    PARALLEL_TO = "parallel_to"
    PERPENDICULAR_TO = "perpendicular_to"
    PASSES_THROUGH = "passes_through"
    BOUNDED_BY = "bounded_by"
    CONTAINS = "contains"


# =============================================================================
# Detection Layer (YOLO)
# =============================================================================

class DetectionElement(MathpixBaseModel):
    """Single element detected by YOLO.

    Contains bbox, class, and detection confidence.
    """
    id: str = Field(..., description="Unique element identifier")
    element_class: ElementClass = Field(..., description="Detected class")
    bbox: BBox = Field(..., description="Bounding box (xywh format)")
    bbox_yolo: Optional[BBoxYOLO] = Field(default=None, description="Original YOLO bbox")
    detection_confidence: float = Field(..., ge=0.0, le=1.0)

    # Optional raw data
    raw_scores: Optional[Dict[str, float]] = Field(
        default=None,
        description="Per-class confidence scores"
    )


class DetectionLayer(MathpixBaseModel):
    """YOLO detection layer output.

    Contains all detected elements from YOLO26 model.
    """
    model: str = Field(default="yolo26-math-v1", description="YOLO model identifier")
    model_version: str = Field(default="1.0.0")
    elements: List[DetectionElement] = Field(default_factory=list)

    # Detection metadata
    inference_time_ms: Optional[float] = Field(default=None)
    image_size: Optional[tuple] = Field(default=None, description="(width, height)")
    confidence_threshold: float = Field(default=0.25)
    nms_threshold: float = Field(default=0.45)

    @property
    def element_count(self) -> int:
        """Count of detected elements."""
        return len(self.elements)

    def get_elements_by_class(self, element_class: ElementClass) -> List[DetectionElement]:
        """Filter elements by class."""
        return [e for e in self.elements if e.element_class == element_class]


# =============================================================================
# Interpretation Layer (Claude)
# =============================================================================

class InterpretedElement(MathpixBaseModel):
    """Element with semantic interpretation from Claude.

    Maps to a detection element and adds semantic understanding.
    """
    id: str = Field(..., description="Unique element identifier")
    detection_element_id: Optional[str] = Field(
        default=None,
        description="Reference to DetectionElement.id"
    )

    # Semantic interpretation
    semantic_label: str = Field(..., description="Human-readable label")
    description: Optional[str] = Field(default=None)
    latex_representation: Optional[str] = Field(default=None)

    # For curves/functions
    function_type: Optional[str] = Field(default=None, description="e.g., 'linear', 'quadratic'")
    equation: Optional[str] = Field(default=None, description="Equation if identified")

    # For points
    coordinates: Optional[Dict[str, float]] = Field(default=None, description="{'x': 1, 'y': 2}")
    point_label: Optional[str] = Field(default=None)

    # Confidence
    interpretation_confidence: float = Field(..., ge=0.0, le=1.0)


class InterpretedRelation(MathpixBaseModel):
    """Relationship between elements identified by Claude."""
    id: str = Field(..., description="Unique relation identifier")
    source_id: str = Field(..., description="Source element ID")
    target_id: str = Field(..., description="Target element ID")
    relation_type: RelationType
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: Optional[str] = Field(default=None)


class InterpretationLayer(MathpixBaseModel):
    """Claude interpretation layer output.

    Contains semantic understanding of visual elements.
    """
    model: str = Field(default="claude-opus-4-5", description="Claude model identifier")
    elements: List[InterpretedElement] = Field(default_factory=list)
    relations: List[InterpretedRelation] = Field(default_factory=list)

    # Diagram-level interpretation
    diagram_type: DiagramType = Field(default=DiagramType.UNKNOWN)
    diagram_description: Optional[str] = Field(default=None)
    coordinate_system: Optional[str] = Field(default=None, description="e.g., 'cartesian', 'polar'")

    # Processing metadata
    inference_time_ms: Optional[float] = Field(default=None)
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)


# =============================================================================
# Merged Output
# =============================================================================

class MergedElement(MathpixBaseModel):
    """Element combining YOLO detection and Claude interpretation.

    bbox comes from YOLO (accurate localization)
    semantic info comes from Claude (accurate understanding)
    """
    id: str = Field(..., description="Unique merged element identifier")

    # Source tracking
    detection_id: Optional[str] = Field(default=None)
    interpretation_id: Optional[str] = Field(default=None)
    bbox_source: str = Field(default="yolo26", description="Source of bbox")
    label_source: str = Field(default="claude-opus-4-5", description="Source of labels")

    # Merged data
    element_class: ElementClass
    bbox: BBox
    semantic_label: str
    description: Optional[str] = Field(default=None)

    # Combined confidence
    combined_confidence: CombinedConfidence

    # Additional semantic data (from Claude)
    latex_representation: Optional[str] = Field(default=None)
    equation: Optional[str] = Field(default=None)
    coordinates: Optional[Dict[str, float]] = Field(default=None)

    # Review
    review: ReviewMetadata = Field(default_factory=ReviewMetadata)


class MergedOutput(MathpixBaseModel):
    """Combined output from detection and interpretation layers."""
    elements: List[MergedElement] = Field(default_factory=list)
    relations: List[InterpretedRelation] = Field(default_factory=list)

    # Diagram-level info (from interpretation)
    diagram_type: DiagramType = Field(default=DiagramType.UNKNOWN)
    diagram_description: Optional[str] = Field(default=None)
    coordinate_system: Optional[str] = Field(default=None)

    # Merge statistics
    matched_count: int = Field(default=0, description="Elements matched between layers")
    detection_only_count: int = Field(default=0, description="Elements only in detection")
    interpretation_only_count: int = Field(default=0, description="Elements only in interpretation")


# =============================================================================
# Main Schema
# =============================================================================

class VisionSpec(MathpixBaseModel):
    """Stage C output: Vision Parse specification.

    Implements YOLO + Claude Hybrid Architecture:
    - detection_layer: YOLO26 bbox detection
    - interpretation_layer: Claude semantic understanding
    - merged_output: Combined with source tracking

    Schema Version: 2.0.0
    """
    # Metadata
    schema_version: str = Field(default="2.0.0")
    image_id: str = Field(..., description="Source image identifier")
    text_spec_id: Optional[str] = Field(default=None, description="Reference to Stage B output")
    provenance: Provenance = Field(default_factory=lambda: Provenance(
        stage=PipelineStage.VISION_PARSE,
        model="hybrid-yolo26-claude"
    ))

    # Hybrid layers (v2.0.0)
    detection_layer: DetectionLayer = Field(default_factory=DetectionLayer)
    interpretation_layer: InterpretationLayer = Field(default_factory=InterpretationLayer)
    merged_output: MergedOutput = Field(default_factory=MergedOutput)

    # Fallback tracking
    fallback_used: bool = Field(default=False, description="Whether fallback model was used")
    fallback_model: Optional[str] = Field(default=None, description="e.g., 'gemini-2.5-pro'")
    fallback_reason: Optional[str] = Field(default=None)

    # Review
    review: ReviewMetadata = Field(default_factory=ReviewMetadata)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    total_processing_time_ms: Optional[float] = Field(default=None)

    @computed_field
    @property
    def overall_confidence(self) -> float:
        """Computed overall confidence from merged elements."""
        if not self.merged_output.elements:
            return 0.0
        confidences = [
            e.combined_confidence.combined_value
            for e in self.merged_output.elements
        ]
        return sum(confidences) / len(confidences)


# =============================================================================
# Hybrid Merger
# =============================================================================

def calculate_combined_confidence(
    detection_conf: float,
    interpretation_conf: float,
    detection_weight: float = 0.6,
    interpretation_weight: float = 0.4,
) -> CombinedConfidence:
    """Calculate combined confidence from detection and interpretation.

    Default weights favor detection (0.6) over interpretation (0.4)
    because bbox accuracy is more verifiable.

    Args:
        detection_conf: YOLO detection confidence
        interpretation_conf: Claude interpretation confidence
        detection_weight: Weight for detection (default 0.6)
        interpretation_weight: Weight for interpretation (default 0.4)

    Returns:
        CombinedConfidence with all tracking info
    """
    combined = (detection_conf * detection_weight +
                interpretation_conf * interpretation_weight)

    return CombinedConfidence(
        detection_confidence=detection_conf,
        interpretation_confidence=interpretation_conf,
        combined_value=round(combined, 4),
        bbox_source="yolo26",
        label_source="claude-opus-4-5",
        detection_weight=detection_weight,
        interpretation_weight=interpretation_weight,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "DiagramType",
    "ElementClass",
    "RelationType",
    # Detection Layer
    "DetectionElement",
    "DetectionLayer",
    # Interpretation Layer
    "InterpretedElement",
    "InterpretedRelation",
    "InterpretationLayer",
    # Merged Output
    "MergedElement",
    "MergedOutput",
    # Main Schema
    "VisionSpec",
    # Functions
    "calculate_combined_confidence",
]
