"""
Pytest configuration and shared fixtures for Math Image Parsing Pipeline tests.

Schema Version: 2.0.0
"""

import pytest
from datetime import datetime, timezone
from typing import List

# Import schemas
from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    CombinedConfidence,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    ReviewSeverity,
    # Stage B
    TextSpec,
    ContentFlags,
    ContentType,
    LineSegment,
    EquationElement,
    WritingStyle,
    VisionParseTrigger,
    # Stage C
    VisionSpec,
    DetectionLayer,
    InterpretationLayer,
    MergedOutput,
    DetectionElement,
    InterpretedElement,
    MergedElement,
    ElementClass,
    DiagramType,
    # Stage D
    TextElement,
    VisualElement,
    MatchedPair,
    MatchType,
)


# =============================================================================
# BBox Fixtures
# =============================================================================

@pytest.fixture
def sample_bbox():
    """Standard bounding box."""
    return BBox(x=100.0, y=100.0, width=50.0, height=30.0)


@pytest.fixture
def overlapping_bbox():
    """BBox overlapping with sample_bbox."""
    return BBox(x=120.0, y=110.0, width=50.0, height=30.0)


@pytest.fixture
def non_overlapping_bbox():
    """BBox not overlapping with sample_bbox."""
    return BBox(x=500.0, y=500.0, width=50.0, height=30.0)


# =============================================================================
# Stage B: TextSpec Fixtures
# =============================================================================

@pytest.fixture
def sample_equation_element():
    """Sample equation element."""
    return EquationElement(
        id="eq-001",
        latex="y = x^2 + 2x + 1",
        confidence=Confidence(
            value=0.95,
            source="mathpix-api",
            element_type="equation"
        ),
        bbox=BBox(x=100, y=200, width=200, height=50),
    )


@pytest.fixture
def sample_line_segment():
    """Sample line segment with text."""
    return LineSegment(
        id="line-001",
        text="Point A is located at (2, 4)",
        latex=None,
        bbox=BBox(x=50, y=100, width=300, height=20),
        confidence=Confidence(
            value=0.90,
            source="mathpix-api",
            element_type="text"
        ),
        line_number=0,
    )


@pytest.fixture
def sample_text_spec(sample_equation_element, sample_line_segment):
    """Complete TextSpec for testing."""
    return TextSpec(
        image_id="test-image-001",
        provenance=Provenance(
            stage=PipelineStage.TEXT_PARSE,
            model="mathpix-v1",
            processing_time_ms=150.0,
        ),
        writing_style=WritingStyle.PRINTED,
        content_flags=ContentFlags(
            contains_equation=True,
            contains_diagram=True,
            contains_text=True,
        ),
        vision_parse_triggers=[VisionParseTrigger.DIAGRAM_EXTRACTION],
        equations=[sample_equation_element],
        line_segments=[sample_line_segment],
    )


@pytest.fixture
def text_spec_with_labels():
    """TextSpec with point labels for matching tests."""
    return TextSpec(
        image_id="test-labels-001",
        provenance=Provenance(
            stage=PipelineStage.TEXT_PARSE,
            model="mathpix-v1",
            processing_time_ms=100.0,
        ),
        writing_style=WritingStyle.PRINTED,
        content_flags=ContentFlags(
            contains_equation=True,
            contains_diagram=True,
            contains_text=True,
        ),
        vision_parse_triggers=[VisionParseTrigger.DIAGRAM_EXTRACTION],
        equations=[
            EquationElement(
                id="eq-linear-001",
                latex="y = 2x + 1",
                confidence=Confidence(
                    value=0.92,
                    source="mathpix-api",
                    element_type="equation"
                ),
                bbox=BBox(x=100, y=50, width=150, height=40),
            ),
        ],
        line_segments=[
            LineSegment(
                id="label-A",
                text="A",
                bbox=BBox(x=200, y=300, width=20, height=20),
                confidence=Confidence(
                    value=0.88,
                    source="mathpix-api",
                    element_type="text"
                ),
                line_number=0,
            ),
            LineSegment(
                id="label-B",
                text="B",
                bbox=BBox(x=400, y=150, width=20, height=20),
                confidence=Confidence(
                    value=0.87,
                    source="mathpix-api",
                    element_type="text"
                ),
                line_number=1,
            ),
            LineSegment(
                id="desc-001",
                text="The graph shows a linear function",
                bbox=BBox(x=50, y=450, width=300, height=25),
                confidence=Confidence(
                    value=0.91,
                    source="mathpix-api",
                    element_type="text"
                ),
                line_number=2,
            ),
        ],
    )


# =============================================================================
# Stage C: VisionSpec Fixtures
# =============================================================================

@pytest.fixture
def sample_detection_element():
    """Sample YOLO detection element."""
    return DetectionElement(
        id="det-001",
        element_class=ElementClass.CURVE,
        bbox=BBox(x=80, y=180, width=220, height=80),
        detection_confidence=0.89,
    )


@pytest.fixture
def sample_interpreted_element():
    """Sample Claude interpreted element."""
    return InterpretedElement(
        id="interp-001",
        detection_element_id="det-001",
        semantic_label="Parabola (quadratic function)",
        description="A U-shaped curve representing y = x² + 2x + 1",
        interpretation_confidence=0.92,
    )


@pytest.fixture
def sample_merged_element(sample_detection_element, sample_interpreted_element):
    """Sample merged element."""
    return MergedElement(
        id="merged-001",
        element_class=ElementClass.CURVE,
        semantic_label="Parabola (quadratic function)",
        description="A U-shaped curve representing y = x² + 2x + 1",
        bbox=BBox(x=80, y=180, width=220, height=80),
        detection_id="det-001",
        interpretation_id="interp-001",
        combined_confidence=CombinedConfidence(
            detection_confidence=0.89,
            interpretation_confidence=0.92,
            combined_value=0.90,
            bbox_source="yolo26",
            label_source="claude-opus-4-5",
        ),
    )


@pytest.fixture
def sample_vision_spec(sample_detection_element, sample_interpreted_element, sample_merged_element):
    """Complete VisionSpec for testing."""
    return VisionSpec(
        image_id="test-image-001",
        provenance=Provenance(
            stage=PipelineStage.VISION_PARSE,
            model="yolo26-claude-hybrid",
            processing_time_ms=250.0,
        ),
        detection_layer=DetectionLayer(
            model="yolo26-v1",
            elements=[sample_detection_element],
        ),
        interpretation_layer=InterpretationLayer(
            model="claude-opus-4-5",
            elements=[sample_interpreted_element],
            relations=[],
            diagram_type=DiagramType.FUNCTION_GRAPH,
        ),
        merged_output=MergedOutput(
            diagram_type=DiagramType.FUNCTION_GRAPH,
            elements=[sample_merged_element],
        ),
    )


@pytest.fixture
def vision_spec_with_points():
    """VisionSpec with point labels for matching tests."""
    return VisionSpec(
        image_id="test-labels-001",
        provenance=Provenance(
            stage=PipelineStage.VISION_PARSE,
            model="yolo26-claude-hybrid",
            processing_time_ms=200.0,
        ),
        detection_layer=DetectionLayer(
            model="yolo26-v1",
            elements=[
                DetectionElement(
                    id="det-curve-001",
                    element_class=ElementClass.CURVE,
                    bbox=BBox(x=100, y=100, width=300, height=200),
                    detection_confidence=0.91,
                ),
                DetectionElement(
                    id="det-point-A",
                    element_class=ElementClass.POINT,
                    bbox=BBox(x=195, y=295, width=30, height=30),
                    detection_confidence=0.88,
                ),
                DetectionElement(
                    id="det-point-B",
                    element_class=ElementClass.POINT,
                    bbox=BBox(x=395, y=145, width=30, height=30),
                    detection_confidence=0.85,
                ),
            ],
        ),
        interpretation_layer=InterpretationLayer(
            model="claude-opus-4-5",
            elements=[
                InterpretedElement(
                    id="interp-curve-001",
                    detection_element_id="det-curve-001",
                    semantic_label="Linear function",
                    description="A straight line representing y = 2x + 1",
                    interpretation_confidence=0.93,
                ),
                InterpretedElement(
                    id="interp-point-A",
                    detection_element_id="det-point-A",
                    semantic_label="A",
                    description="Point labeled A",
                    interpretation_confidence=0.90,
                ),
                InterpretedElement(
                    id="interp-point-B",
                    detection_element_id="det-point-B",
                    semantic_label="B",
                    description="Point labeled B",
                    interpretation_confidence=0.87,
                ),
            ],
            relations=[],
            diagram_type=DiagramType.FUNCTION_GRAPH,
        ),
        merged_output=MergedOutput(
            diagram_type=DiagramType.FUNCTION_GRAPH,
            elements=[
                MergedElement(
                    id="merged-curve-001",
                    element_class=ElementClass.CURVE,
                    semantic_label="Linear function",
                    description="A straight line representing y = 2x + 1",
                    bbox=BBox(x=100, y=100, width=300, height=200),
                    detection_id="det-curve-001",
                    interpretation_id="interp-curve-001",
                    combined_confidence=CombinedConfidence(
                        detection_confidence=0.91,
                        interpretation_confidence=0.93,
                        combined_value=0.92,
                        bbox_source="yolo26",
                        label_source="claude-opus-4-5",
                    ),
                ),
                MergedElement(
                    id="merged-point-A",
                    element_class=ElementClass.POINT,
                    semantic_label="A",
                    description="Point labeled A",
                    bbox=BBox(x=195, y=295, width=30, height=30),
                    detection_id="det-point-A",
                    interpretation_id="interp-point-A",
                    combined_confidence=CombinedConfidence(
                        detection_confidence=0.88,
                        interpretation_confidence=0.90,
                        combined_value=0.89,
                        bbox_source="yolo26",
                        label_source="claude-opus-4-5",
                    ),
                ),
                MergedElement(
                    id="merged-point-B",
                    element_class=ElementClass.POINT,
                    semantic_label="B",
                    description="Point labeled B",
                    bbox=BBox(x=395, y=145, width=30, height=30),
                    detection_id="det-point-B",
                    interpretation_id="interp-point-B",
                    combined_confidence=CombinedConfidence(
                        detection_confidence=0.85,
                        interpretation_confidence=0.87,
                        combined_value=0.86,
                        bbox_source="yolo26",
                        label_source="claude-opus-4-5",
                    ),
                ),
            ],
        ),
    )


# =============================================================================
# Stage D: Alignment Fixtures
# =============================================================================

@pytest.fixture
def sample_text_element():
    """Sample text element for alignment."""
    return TextElement(
        id="text-eq-001",
        content="y = x^2 + 2x + 1",
        latex="y = x^2 + 2x + 1",
        bbox=BBox(x=100, y=200, width=200, height=50),
        source_line_id=None,
    )


@pytest.fixture
def sample_visual_element():
    """Sample visual element for alignment."""
    return VisualElement(
        id="visual-curve-001",
        element_class="curve",
        semantic_label="Parabola (quadratic function)",
        bbox=BBox(x=80, y=180, width=220, height=80),
        source_merged_id="merged-001",
    )


@pytest.fixture
def sample_matched_pair(sample_text_element, sample_visual_element):
    """Sample matched pair."""
    return MatchedPair(
        id="test-image-001-match-001",
        match_type=MatchType.EQUATION_TO_GRAPH,
        text_element=sample_text_element,
        visual_element=sample_visual_element,
        consistency_score=0.85,
        confidence=Confidence(
            value=0.85,
            source="alignment-matcher",
            element_type="matched_pair"
        ),
        applied_threshold=0.6,
        spatial_overlap=0.65,
        semantic_similarity=0.90,
    )
