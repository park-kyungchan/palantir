"""
VisionSpec Schema for Stage C (Vision Parse) Output.

Stage C implements YOLO + Claude Hybrid Architecture (v2.0.0) OR
Gemini 3 Pro Single Model Architecture (v3.0.0):

v2.0.0 (Legacy):
- Detection Layer: YOLO26 for bbox detection
- Interpretation Layer: Claude Opus 4.5 for semantic understanding
- Merged Output: Combined results with provenance tracking

v3.0.0 (New):
- Gemini Layer: Gemini 3 Pro unified detection + interpretation
- Compatibility Layer: Auto-generates merged_output for Stage D

Schema Version: 3.0.0
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

# Forward reference for AlignmentLayer (circular import prevention)
# Actual import happens at runtime via TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .alignment_layer import AlignmentLayer


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


class ThinkingLevel(str, Enum):
    """Gemini 3 Pro Thinking Mode levels (C4)."""
    MINIMAL = "minimal"
    LOW = "low"
    HIGH = "high"


class MediaResolution(str, Enum):
    """Gemini 3 Pro Media Resolution settings (C3)."""
    HIGH = "media_resolution_high"           # 1120 tokens, Global
    ULTRA_HIGH = "media_resolution_ultra_high"  # Per-part only


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
# Gemini Vision Layer (v3.0.0)
# =============================================================================

class GeminiElement(MathpixBaseModel):
    """Single element detected by Gemini 3 Pro.

    Unified detection + interpretation in single model call.
    box_2d format: [ymin, xmin, ymax, xmax] in 0-1000 range.
    """
    id: str = Field(..., description="Unique element identifier")

    # Gemini native format
    box_2d: List[int] = Field(
        ...,
        description="Bounding box [ymin, xmin, ymax, xmax] in 0-1000 range"
    )
    label: str = Field(..., description="Raw label from Gemini")

    # Normalized for Stage D compatibility
    element_class: ElementClass = Field(..., description="Normalized ElementClass")
    semantic_label: str = Field(..., description="Normalized semantic label")

    # Confidence (raw and calibrated)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Raw Gemini confidence")
    calibrated_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Calibrated confidence for Stage D thresholds"
    )

    # Optional C2: Pointing coordinates
    pointing_coords: Optional[List[int]] = Field(
        default=None,
        description="Precise point coordinates [x, y] in 0-1000 range"
    )

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeminiRelation(MathpixBaseModel):
    """Relationship between elements identified by Gemini 3 Pro."""
    id: str = Field(..., description="Unique relation identifier")
    source_id: str = Field(..., description="Source element ID")
    target_id: str = Field(..., description="Target element ID")
    relation_type: RelationType
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: Optional[str] = Field(default=None)


class DiagramAnalysis(MathpixBaseModel):
    """Diagram-level analysis from Gemini 3 Pro."""
    diagram_type: DiagramType = Field(default=DiagramType.UNKNOWN)
    coordinate_system: Optional[str] = Field(
        default=None,
        description="e.g., 'cartesian', 'polar'"
    )
    description: Optional[str] = Field(default=None)
    key_elements: List[str] = Field(
        default_factory=list,
        description="IDs of key elements in the diagram"
    )


class ThinkingContext(MathpixBaseModel):
    """C4 Thinking Mode output for Stage D reasoning context.

    Captures Gemini's reasoning process for downstream alignment.
    """
    thinking_level: ThinkingLevel = Field(default=ThinkingLevel.HIGH)
    reasoning_summary: Optional[str] = Field(
        default=None,
        description="Summary of reasoning process"
    )
    thought_signature: Optional[str] = Field(
        default=None,
        description="Hash for multi-turn consistency"
    )
    key_insights: List[str] = Field(
        default_factory=list,
        description="Key insights from reasoning"
    )


class GeminiVisionLayer(MathpixBaseModel):
    """Gemini 3 Pro unified vision layer (v3.0.0).

    Replaces separate detection + interpretation layers with single model.
    """
    model: str = Field(default="gemini-3-pro", description="Gemini model identifier")
    model_version: str = Field(default="3.0.0")

    # Core outputs
    elements: List[GeminiElement] = Field(default_factory=list)
    relations: List[GeminiRelation] = Field(default_factory=list)

    # Diagram analysis
    diagram_analysis: DiagramAnalysis = Field(default_factory=DiagramAnalysis)

    # C4: Thinking context
    thinking_context: Optional[ThinkingContext] = Field(default=None)

    # C3: Media resolution used
    media_resolution: MediaResolution = Field(default=MediaResolution.HIGH)

    # Processing metadata
    inference_time_ms: Optional[float] = Field(default=None)
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)

    @property
    def element_count(self) -> int:
        """Count of detected elements."""
        return len(self.elements)


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

    Supports two architectures:
    - v2.x: YOLO + Claude Hybrid (detection_layer + interpretation_layer)
    - v3.x: Gemini 3 Pro Single Model (gemini_layer)

    Both produce merged_output for Stage D compatibility.

    Schema Version: 3.0.0
    """
    # Metadata
    schema_version: str = Field(default="3.0.0")
    image_id: str = Field(..., description="Source image identifier")
    text_spec_id: Optional[str] = Field(default=None, description="Reference to Stage B output")
    provenance: Provenance = Field(default_factory=lambda: Provenance(
        stage=PipelineStage.VISION_PARSE,
        model="hybrid-yolo26-claude"
    ))

    # v3.0.0: Gemini unified layer (primary)
    gemini_layer: Optional[GeminiVisionLayer] = Field(
        default=None,
        description="Gemini 3 Pro unified vision output (v3.0.0)"
    )

    # v2.0.0: Hybrid layers (deprecated but maintained for compatibility)
    detection_layer: Optional[DetectionLayer] = Field(
        default_factory=DetectionLayer,
        description="YOLO detection layer (v2.0.0, deprecated in v3.0.0)"
    )
    interpretation_layer: Optional[InterpretationLayer] = Field(
        default_factory=InterpretationLayer,
        description="Claude interpretation layer (v2.0.0, deprecated in v3.0.0)"
    )

    # Stage D interface (always populated)
    merged_output: MergedOutput = Field(default_factory=MergedOutput)

    # Fallback tracking
    fallback_used: bool = Field(default=False, description="Whether fallback model was used")
    fallback_model: Optional[str] = Field(default=None, description="e.g., 'gemini-2.5-pro'")
    fallback_reason: Optional[str] = Field(default=None)

    # Review
    review: ReviewMetadata = Field(default_factory=ReviewMetadata)

    # Stage D: AlignmentLayer (LaTeX ↔ Visual 정렬)
    alignment_layer: Optional["AlignmentLayer"] = Field(
        default=None,
        description="Stage D AlignmentLayer for LaTeX-Visual alignment (populated after Stage D processing)"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    total_processing_time_ms: Optional[float] = Field(default=None)

    @property
    def elements(self) -> List[MergedElement]:
        """Backward compatibility alias for merged_output.elements.

        Stage D and legacy code may access vision_spec.elements directly.
        This property ensures they get merged_output.elements.
        """
        return self.merged_output.elements

    @property
    def relations(self) -> List[InterpretedRelation]:
        """Backward compatibility alias for merged_output.relations."""
        return self.merged_output.relations

    @property
    def uses_gemini(self) -> bool:
        """Check if Gemini 3 Pro layer is used."""
        return self.gemini_layer is not None and len(self.gemini_layer.elements) > 0

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
    "ThinkingLevel",
    "MediaResolution",
    # Detection Layer (v2.0.0)
    "DetectionElement",
    "DetectionLayer",
    # Interpretation Layer (v2.0.0)
    "InterpretedElement",
    "InterpretedRelation",
    "InterpretationLayer",
    # Gemini Vision Layer (v3.0.0)
    "GeminiElement",
    "GeminiRelation",
    "DiagramAnalysis",
    "ThinkingContext",
    "GeminiVisionLayer",
    # Merged Output
    "MergedElement",
    "MergedOutput",
    # Main Schema
    "VisionSpec",
    # Functions
    "calculate_combined_confidence",
]
