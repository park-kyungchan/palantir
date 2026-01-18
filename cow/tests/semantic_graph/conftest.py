"""
Pytest fixtures for Stage E (Semantic Graph) tests.

Provides sample data for testing:
- Nodes, edges, and graphs
- Alignment report data
- Configuration fixtures
"""

import pytest
from typing import List

from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    CombinedConfidence,
    Provenance,
    PipelineStage,
    AlignmentReport,
    AlignmentStatistics,
    TextElement,
    VisualElement,
    MatchedPair,
    MatchType,
    UnmatchedElement,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticNode,
    SemanticEdge,
    SemanticGraph,
    NodeType,
    EdgeType,
    NodeProperties,
)


# =============================================================================
# BBox Fixtures
# =============================================================================

@pytest.fixture
def sample_bbox():
    """Standard bounding box."""
    return BBox(x=100.0, y=100.0, width=50.0, height=30.0)


@pytest.fixture
def adjacent_bbox():
    """BBox adjacent to sample_bbox (within proximity threshold)."""
    return BBox(x=160.0, y=100.0, width=50.0, height=30.0)


@pytest.fixture
def overlapping_bbox():
    """BBox overlapping with sample_bbox."""
    return BBox(x=120.0, y=110.0, width=50.0, height=30.0)


@pytest.fixture
def containing_bbox():
    """BBox that contains sample_bbox."""
    return BBox(x=50.0, y=50.0, width=200.0, height=150.0)


@pytest.fixture
def distant_bbox():
    """BBox far from sample_bbox (beyond proximity threshold)."""
    return BBox(x=500.0, y=500.0, width=50.0, height=30.0)


# =============================================================================
# Element Fixtures
# =============================================================================

@pytest.fixture
def sample_text_element():
    """Sample text element for alignment."""
    return TextElement(
        id="text-eq-001",
        content="y = 2x + 1",
        latex="y = 2x + 1",
        bbox=BBox(x=100, y=50, width=150, height=40),
        source_line_id=None,
    )


@pytest.fixture
def sample_visual_element():
    """Sample visual element for alignment."""
    return VisualElement(
        id="visual-curve-001",
        element_class="curve",
        semantic_label="Linear function",
        bbox=BBox(x=100, y=100, width=300, height=200),
        source_merged_id="merged-001",
    )


@pytest.fixture
def point_visual_element():
    """Visual element representing a point."""
    return VisualElement(
        id="visual-point-001",
        element_class="point",
        semantic_label="Point A",
        bbox=BBox(x=200, y=150, width=20, height=20),
        source_merged_id="merged-002",
    )


@pytest.fixture
def label_text_element():
    """Text element representing a label."""
    return TextElement(
        id="text-label-001",
        content="A",
        latex=None,
        bbox=BBox(x=195, y=145, width=30, height=25),
        source_line_id="line-001",
    )


# =============================================================================
# Matched Pair Fixtures
# =============================================================================

@pytest.fixture
def sample_matched_pair(sample_text_element, sample_visual_element):
    """Sample matched pair: equation to curve."""
    return MatchedPair(
        id="match-001",
        match_type=MatchType.EQUATION_TO_GRAPH,
        text_element=sample_text_element,
        visual_element=sample_visual_element,
        consistency_score=0.85,
        confidence=Confidence(
            value=0.85,
            source="alignment-matcher",
            element_type="matched_pair"
        ),
        applied_threshold=0.60,
        spatial_overlap=0.70,
        semantic_similarity=0.88,
    )


@pytest.fixture
def label_matched_pair(label_text_element, point_visual_element):
    """Sample matched pair: label to point."""
    return MatchedPair(
        id="match-002",
        match_type=MatchType.LABEL_TO_POINT,
        text_element=label_text_element,
        visual_element=point_visual_element,
        consistency_score=0.92,
        confidence=Confidence(
            value=0.90,
            source="alignment-matcher",
            element_type="matched_pair"
        ),
        applied_threshold=0.60,
        spatial_overlap=0.80,
        semantic_similarity=0.95,
    )


@pytest.fixture
def low_confidence_matched_pair():
    """Matched pair with low confidence (below threshold)."""
    return MatchedPair(
        id="match-003",
        match_type=MatchType.DESCRIPTION_TO_ELEMENT,
        text_element=TextElement(
            id="text-desc-001",
            content="some curve",
            latex=None,
            bbox=BBox(x=400, y=400, width=100, height=30),
        ),
        visual_element=VisualElement(
            id="visual-unknown-001",
            element_class="curve",
            semantic_label="Unknown curve",
            bbox=BBox(x=300, y=300, width=150, height=100),
        ),
        consistency_score=0.45,
        confidence=Confidence(
            value=0.45,
            source="alignment-matcher",
            element_type="matched_pair"
        ),
        applied_threshold=0.60,
        spatial_overlap=0.20,
        semantic_similarity=0.50,
    )


# =============================================================================
# Alignment Report Fixtures
# =============================================================================

@pytest.fixture
def sample_alignment_report(sample_matched_pair, label_matched_pair):
    """Complete alignment report for testing."""
    return AlignmentReport(
        image_id="test-image-001",
        text_spec_id="text-spec-001",
        vision_spec_id="vision-spec-001",
        matched_pairs=[sample_matched_pair, label_matched_pair],
        inconsistencies=[],
        unmatched_elements=[
            UnmatchedElement(
                id="unmatched-001",
                source="visual",
                element_id="visual-extra-001",
                content="Axis line",
                bbox=BBox(x=50, y=250, width=400, height=5),
                reason="No matching text element",
            ),
        ],
        statistics=AlignmentStatistics(
            total_text_elements=5,
            total_visual_elements=4,
        ),
        overall_alignment_score=0.88,
        overall_confidence=0.85,
    )


@pytest.fixture
def empty_alignment_report():
    """Alignment report with no matches."""
    return AlignmentReport(
        image_id="empty-image-001",
        text_spec_id="text-spec-empty",
        vision_spec_id="vision-spec-empty",
        matched_pairs=[],
        inconsistencies=[],
        unmatched_elements=[],
        statistics=AlignmentStatistics(
            total_text_elements=0,
            total_visual_elements=0,
        ),
        overall_alignment_score=0.0,
        overall_confidence=0.0,
    )


# =============================================================================
# Node Fixtures
# =============================================================================

@pytest.fixture
def sample_point_node():
    """Sample POINT node."""
    return SemanticNode(
        id="node-point-001",
        node_type=NodeType.POINT,
        label="A",
        bbox=BBox(x=200, y=150, width=20, height=20),
        confidence=Confidence(
            value=0.85,
            source="alignment_propagation",
            element_type="point"
        ),
        applied_threshold=0.60,
        properties=NodeProperties(
            coordinates={"x": 2.0, "y": 4.0},
            point_label="A",
        ),
        source_element_ids=["text-001", "visual-001"],
    )


@pytest.fixture
def sample_curve_node():
    """Sample CURVE node."""
    return SemanticNode(
        id="node-curve-001",
        node_type=NodeType.CURVE,
        label="y = 2x + 1",
        bbox=BBox(x=100, y=100, width=300, height=200),
        confidence=Confidence(
            value=0.90,
            source="alignment_propagation",
            element_type="curve"
        ),
        applied_threshold=0.60,
        properties=NodeProperties(
            equation="y = 2x + 1",
            slope=2.0,
            y_intercept=1.0,
        ),
        source_element_ids=["text-eq-001", "visual-curve-001"],
    )


@pytest.fixture
def sample_equation_node():
    """Sample EQUATION node."""
    return SemanticNode(
        id="node-eq-001",
        node_type=NodeType.EQUATION,
        label="y = 2x + 1",
        bbox=BBox(x=100, y=50, width=150, height=40),
        confidence=Confidence(
            value=0.88,
            source="alignment_propagation",
            element_type="equation"
        ),
        applied_threshold=0.60,
        properties=NodeProperties(
            latex="y = 2x + 1",
            equation="y = 2x + 1",
        ),
        source_element_ids=["text-eq-001"],
    )


@pytest.fixture
def sample_label_node():
    """Sample LABEL node."""
    return SemanticNode(
        id="node-label-001",
        node_type=NodeType.LABEL,
        label="A",
        bbox=BBox(x=195, y=145, width=30, height=25),
        confidence=Confidence(
            value=0.75,
            source="alignment_propagation",
            element_type="label"
        ),
        applied_threshold=0.60,
        properties=NodeProperties(description="Label for point A"),
        source_element_ids=["text-label-001"],
    )


@pytest.fixture
def sample_axis_node():
    """Sample AXIS node."""
    return SemanticNode(
        id="node-axis-x",
        node_type=NodeType.AXIS,
        label="x-axis",
        bbox=BBox(x=50, y=250, width=400, height=5),
        confidence=Confidence(
            value=0.70,
            source="unmatched_element",
            element_type="axis"
        ),
        applied_threshold=0.60,
        properties=NodeProperties(description="Horizontal axis"),
        source_element_ids=["visual-axis-001"],
    )


@pytest.fixture
def isolated_node():
    """Node with no edges (for isolation penalty testing)."""
    return SemanticNode(
        id="node-isolated-001",
        node_type=NodeType.ANNOTATION,
        label="Note: check this",
        bbox=BBox(x=500, y=500, width=100, height=30),
        confidence=Confidence(
            value=0.65,
            source="unmatched_element",
            element_type="annotation"
        ),
        applied_threshold=0.60,
        properties=NodeProperties(description="Annotation text"),
        source_element_ids=["text-note-001"],
    )


@pytest.fixture
def low_confidence_node():
    """Node below confidence threshold."""
    return SemanticNode(
        id="node-low-001",
        node_type=NodeType.ANNOTATION,
        label="uncertain element",
        bbox=BBox(x=600, y=600, width=50, height=20),
        confidence=Confidence(
            value=0.35,
            source="unmatched_element",
            element_type="annotation"
        ),
        applied_threshold=0.60,
        properties=NodeProperties(),
        source_element_ids=["unknown-001"],
    )


@pytest.fixture
def sample_nodes(sample_point_node, sample_curve_node, sample_label_node, sample_axis_node):
    """List of sample nodes for graph building."""
    return [sample_point_node, sample_curve_node, sample_label_node, sample_axis_node]


# =============================================================================
# Edge Fixtures
# =============================================================================

@pytest.fixture
def sample_labels_edge():
    """Sample LABELS edge (label -> point)."""
    return SemanticEdge(
        id="edge-labels-001",
        source_id="node-label-001",
        target_id="node-point-001",
        edge_type=EdgeType.LABELS,
        confidence=Confidence(
            value=0.85,
            source="edge_inference",
            element_type="labels"
        ),
        applied_threshold=0.55,
        description="'A' labels point",
    )


@pytest.fixture
def sample_lies_on_edge():
    """Sample LIES_ON edge (point -> curve)."""
    return SemanticEdge(
        id="edge-lies-on-001",
        source_id="node-point-001",
        target_id="node-curve-001",
        edge_type=EdgeType.LIES_ON,
        confidence=Confidence(
            value=0.78,
            source="edge_inference",
            element_type="lies_on"
        ),
        applied_threshold=0.55,
        description="Point A lies on curve",
    )


@pytest.fixture
def sample_adjacent_edge():
    """Sample ADJACENT_TO edge."""
    return SemanticEdge(
        id="edge-adjacent-001",
        source_id="node-label-001",
        target_id="node-point-001",
        edge_type=EdgeType.ADJACENT_TO,
        confidence=Confidence(
            value=0.70,
            source="edge_inference",
            element_type="adjacent_to"
        ),
        applied_threshold=0.55,
        bidirectional=True,
        description="Distance: 15.0px",
    )


@pytest.fixture
def low_confidence_edge():
    """Edge below confidence threshold."""
    return SemanticEdge(
        id="edge-low-001",
        source_id="node-point-001",
        target_id="node-axis-x",
        edge_type=EdgeType.INTERSECTS,
        confidence=Confidence(
            value=0.40,
            source="edge_inference",
            element_type="intersects"
        ),
        applied_threshold=0.55,
        description="Low confidence intersection",
    )


@pytest.fixture
def sample_edges(sample_labels_edge, sample_lies_on_edge, sample_adjacent_edge):
    """List of sample edges for graph building."""
    return [sample_labels_edge, sample_lies_on_edge, sample_adjacent_edge]


# =============================================================================
# Graph Fixtures
# =============================================================================

@pytest.fixture
def sample_graph(sample_nodes, sample_edges):
    """Complete sample graph."""
    return SemanticGraph(
        image_id="test-image-001",
        alignment_report_id="alignment-001",
        nodes=sample_nodes,
        edges=sample_edges,
        overall_confidence=0.80,
    )


@pytest.fixture
def empty_graph():
    """Empty graph with no nodes or edges."""
    return SemanticGraph(
        image_id="empty-image-001",
        alignment_report_id="alignment-empty",
        nodes=[],
        edges=[],
        overall_confidence=0.0,
    )


@pytest.fixture
def graph_with_invalid_edge(sample_nodes):
    """Graph with edge referencing non-existent node."""
    invalid_edge = SemanticEdge(
        id="edge-invalid-001",
        source_id="node-nonexistent",
        target_id="node-point-001",
        edge_type=EdgeType.LABELS,
        confidence=Confidence(
            value=0.80,
            source="edge_inference",
            element_type="labels"
        ),
        applied_threshold=0.55,
    )
    return SemanticGraph(
        image_id="invalid-image-001",
        alignment_report_id="alignment-invalid",
        nodes=sample_nodes,
        edges=[invalid_edge],
    )


@pytest.fixture
def graph_with_duplicate_edges(sample_nodes, sample_labels_edge):
    """Graph with duplicate edges."""
    duplicate_edge = SemanticEdge(
        id="edge-labels-002",
        source_id="node-label-001",
        target_id="node-point-001",
        edge_type=EdgeType.LABELS,
        confidence=Confidence(
            value=0.82,
            source="edge_inference",
            element_type="labels"
        ),
        applied_threshold=0.55,
        description="Duplicate labels edge",
    )
    return SemanticGraph(
        image_id="dup-image-001",
        alignment_report_id="alignment-dup",
        nodes=sample_nodes,
        edges=[sample_labels_edge, duplicate_edge],
    )
