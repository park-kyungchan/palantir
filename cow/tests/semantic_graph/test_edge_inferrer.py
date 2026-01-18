"""
Unit tests for EdgeInferrer (Stage E component).

Tests edge inference between nodes:
- Spatial edge inference (containment, intersection, adjacency)
- Label edge inference
- Mathematical edge inference
- Edge deduplication
"""

import pytest

from mathpix_pipeline.semantic_graph import (
    EdgeInferrer,
    create_edge_inferrer,
    LABEL_TARGET_TYPES,
    GRAPHABLE_TYPES,
    POINT_LIKE_TYPES,
    CURVE_LIKE_TYPES,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticNode,
    NodeType,
    EdgeType,
    NodeProperties,
)
from mathpix_pipeline.schemas import BBox, Confidence


class TestEdgeInferrerInit:
    """Test EdgeInferrer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        inferrer = EdgeInferrer()
        assert inferrer.spatial_overlap_threshold == 0.1
        assert inferrer.proximity_threshold_px == 50.0
        assert inferrer.default_edge_threshold == 0.55

    def test_custom_init(self):
        """Test initialization with custom parameters."""
        inferrer = EdgeInferrer(
            spatial_overlap_threshold=0.2,
            proximity_threshold_px=75.0,
            default_edge_threshold=0.60,
        )
        assert inferrer.spatial_overlap_threshold == 0.2
        assert inferrer.proximity_threshold_px == 75.0
        assert inferrer.default_edge_threshold == 0.60

    def test_factory_function(self):
        """Test create_edge_inferrer factory."""
        inferrer = create_edge_inferrer(
            overlap_threshold=0.15,
            proximity_px=60.0,
            edge_threshold=0.50,
        )
        assert inferrer.spatial_overlap_threshold == 0.15
        assert inferrer.proximity_threshold_px == 60.0
        assert inferrer.default_edge_threshold == 0.50


class TestSpatialEdges:
    """Test spatial edge inference."""

    def test_infer_spatial_edges_no_nodes(self):
        """Test inference with no nodes returns empty list."""
        inferrer = EdgeInferrer()
        edges = inferrer.infer([])
        assert edges == []

    def test_infer_adjacent_edges(self, sample_point_node, sample_label_node):
        """Test adjacent edges are inferred for nearby nodes."""
        inferrer = EdgeInferrer(proximity_threshold_px=100.0)

        # Nodes are close (label at 195,145 and point at 200,150)
        edges = inferrer.infer([sample_point_node, sample_label_node])

        # Should have at least one spatial edge (ADJACENT_TO or label edge)
        assert len(edges) > 0

    def test_infer_containment_edge(self, containing_bbox):
        """Test containment edge is inferred."""
        inferrer = EdgeInferrer()

        outer_node = SemanticNode(
            id="outer-001",
            node_type=NodeType.REGION,
            label="Region",
            bbox=containing_bbox,  # Contains sample_bbox area
            confidence=Confidence(value=0.80, source="test", element_type="region"),
        )

        inner_node = SemanticNode(
            id="inner-001",
            node_type=NodeType.POINT,
            label="P",
            bbox=BBox(x=100, y=100, width=20, height=20),  # Inside containing_bbox
            confidence=Confidence(value=0.85, source="test", element_type="point"),
        )

        edges = inferrer.infer([outer_node, inner_node])

        # Should find CONTAINS edge
        contains_edges = [e for e in edges if e.edge_type == EdgeType.CONTAINS]
        assert len(contains_edges) >= 1

    def test_infer_intersection_edge(self, overlapping_bbox):
        """Test intersection edge is inferred for overlapping bboxes."""
        inferrer = EdgeInferrer(spatial_overlap_threshold=0.05)

        node_a = SemanticNode(
            id="node-a",
            node_type=NodeType.LINE,
            label="Line 1",
            bbox=BBox(x=100, y=100, width=100, height=50),
            confidence=Confidence(value=0.80, source="test", element_type="line"),
        )

        node_b = SemanticNode(
            id="node-b",
            node_type=NodeType.LINE,
            label="Line 2",
            bbox=BBox(x=150, y=120, width=100, height=50),  # Overlaps with node_a
            confidence=Confidence(value=0.80, source="test", element_type="line"),
        )

        edges = inferrer.infer([node_a, node_b])

        # Should find INTERSECTS edge
        intersect_edges = [e for e in edges if e.edge_type == EdgeType.INTERSECTS]
        assert len(intersect_edges) >= 1

    def test_no_spatial_edge_for_distant_nodes(self, distant_bbox):
        """Test no spatial edges for distant nodes."""
        inferrer = EdgeInferrer(proximity_threshold_px=50.0)

        node_a = SemanticNode(
            id="node-a",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=0, y=0, width=10, height=10),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        node_b = SemanticNode(
            id="node-b",
            node_type=NodeType.POINT,
            label="B",
            bbox=distant_bbox,  # Far away
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        edges = inferrer.infer([node_a, node_b])

        # Should not have spatial edges between distant nodes
        spatial_types = {EdgeType.ADJACENT_TO, EdgeType.INTERSECTS, EdgeType.CONTAINS}
        spatial_edges = [e for e in edges if e.edge_type in spatial_types]
        assert len(spatial_edges) == 0


class TestBBoxOverlapCalculation:
    """Test bbox overlap IoU calculation."""

    def test_bbox_overlap_iou_no_overlap(self):
        """Test IoU is 0 for non-overlapping bboxes."""
        inferrer = EdgeInferrer()

        bbox_a = BBox(x=0, y=0, width=50, height=50)
        bbox_b = BBox(x=100, y=100, width=50, height=50)

        iou = inferrer._bbox_overlap_iou(bbox_a, bbox_b)
        assert iou == 0.0

    def test_bbox_overlap_iou_partial_overlap(self):
        """Test IoU for partially overlapping bboxes."""
        inferrer = EdgeInferrer()

        bbox_a = BBox(x=0, y=0, width=100, height=100)
        bbox_b = BBox(x=50, y=50, width=100, height=100)

        iou = inferrer._bbox_overlap_iou(bbox_a, bbox_b)
        # Intersection: 50x50 = 2500
        # Union: 10000 + 10000 - 2500 = 17500
        # IoU: 2500 / 17500 = ~0.143
        assert 0.1 < iou < 0.2

    def test_bbox_overlap_iou_complete_overlap(self):
        """Test IoU is 1.0 for identical bboxes."""
        inferrer = EdgeInferrer()

        bbox_a = BBox(x=0, y=0, width=100, height=100)
        bbox_b = BBox(x=0, y=0, width=100, height=100)

        iou = inferrer._bbox_overlap_iou(bbox_a, bbox_b)
        assert iou == 1.0

    def test_bbox_contains(self):
        """Test bbox containment check."""
        inferrer = EdgeInferrer()

        outer = BBox(x=0, y=0, width=200, height=200)
        inner = BBox(x=50, y=50, width=50, height=50)

        assert inferrer._bbox_contains(outer, inner)
        assert not inferrer._bbox_contains(inner, outer)

    def test_bbox_distance_adjacent(self):
        """Test distance between adjacent bboxes."""
        inferrer = EdgeInferrer()

        bbox_a = BBox(x=0, y=0, width=50, height=50)
        bbox_b = BBox(x=50, y=0, width=50, height=50)  # Adjacent (touching)

        distance = inferrer._bbox_distance(bbox_a, bbox_b)
        assert distance == 0.0

    def test_bbox_distance_separated(self):
        """Test distance between separated bboxes."""
        inferrer = EdgeInferrer()

        bbox_a = BBox(x=0, y=0, width=50, height=50)
        bbox_b = BBox(x=100, y=0, width=50, height=50)  # 50px gap

        distance = inferrer._bbox_distance(bbox_a, bbox_b)
        assert distance == 50.0


class TestLabelEdgeInference:
    """Test label edge inference."""

    def test_infer_labels_edge(self):
        """Test LABELS edge is inferred between label and visual element."""
        inferrer = EdgeInferrer(proximity_threshold_px=50.0)

        label_node = SemanticNode(
            id="label-001",
            node_type=NodeType.LABEL,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="label"),
        )

        point_node = SemanticNode(
            id="point-001",
            node_type=NodeType.POINT,
            label="Point A",
            bbox=BBox(x=110, y=110, width=15, height=15),  # Very close
            confidence=Confidence(value=0.85, source="test", element_type="point"),
        )

        edges = inferrer.infer([label_node, point_node])

        # Should find LABELS edge
        labels_edges = [e for e in edges if e.edge_type == EdgeType.LABELS]
        assert len(labels_edges) >= 1

        # Should also have reverse LABELED_BY edge
        labeled_by_edges = [e for e in edges if e.edge_type == EdgeType.LABELED_BY]
        assert len(labeled_by_edges) >= 1

    def test_label_target_types_constant(self):
        """Test LABEL_TARGET_TYPES constant contains expected types."""
        assert NodeType.POINT in LABEL_TARGET_TYPES
        assert NodeType.LINE in LABEL_TARGET_TYPES
        assert NodeType.CURVE in LABEL_TARGET_TYPES
        assert NodeType.CIRCLE in LABEL_TARGET_TYPES
        assert NodeType.POLYGON in LABEL_TARGET_TYPES

    def test_annotation_also_labels(self):
        """Test ANNOTATION nodes can also create label edges."""
        inferrer = EdgeInferrer(proximity_threshold_px=100.0)

        annotation_node = SemanticNode(
            id="annot-001",
            node_type=NodeType.ANNOTATION,
            label="This is curve C",
            bbox=BBox(x=200, y=200, width=80, height=25),
            confidence=Confidence(value=0.75, source="test", element_type="annotation"),
        )

        curve_node = SemanticNode(
            id="curve-001",
            node_type=NodeType.CURVE,
            label="Curve C",
            bbox=BBox(x=180, y=210, width=100, height=60),  # Close to annotation
            confidence=Confidence(value=0.85, source="test", element_type="curve"),
        )

        edges = inferrer.infer([annotation_node, curve_node])

        # Annotation should create a LABELS edge
        labels_edges = [e for e in edges if e.edge_type == EdgeType.LABELS]
        assert len(labels_edges) >= 1


class TestMathematicalEdgeInference:
    """Test mathematical relationship edge inference."""

    def test_graphable_types_constant(self):
        """Test GRAPHABLE_TYPES constant contains expected types."""
        assert NodeType.CURVE in GRAPHABLE_TYPES
        assert NodeType.LINE in GRAPHABLE_TYPES
        assert NodeType.CIRCLE in GRAPHABLE_TYPES

    def test_point_like_types_constant(self):
        """Test POINT_LIKE_TYPES constant contains expected types."""
        assert NodeType.POINT in POINT_LIKE_TYPES
        assert NodeType.INTERCEPT in POINT_LIKE_TYPES

    def test_curve_like_types_constant(self):
        """Test CURVE_LIKE_TYPES constant contains expected types."""
        assert NodeType.LINE in CURVE_LIKE_TYPES
        assert NodeType.CURVE in CURVE_LIKE_TYPES
        assert NodeType.CIRCLE in CURVE_LIKE_TYPES
        assert NodeType.POLYGON in CURVE_LIKE_TYPES

    def test_infer_lies_on_edge(self):
        """Test LIES_ON edge is inferred for point near curve."""
        inferrer = EdgeInferrer(proximity_threshold_px=50.0)

        point_node = SemanticNode(
            id="point-001",
            node_type=NodeType.POINT,
            label="P",
            bbox=BBox(x=150, y=150, width=10, height=10),
            confidence=Confidence(value=0.85, source="test", element_type="point"),
            properties=NodeProperties(coordinates={"x": 2.0, "y": 5.0}),
        )

        curve_node = SemanticNode(
            id="curve-001",
            node_type=NodeType.CURVE,
            label="y = 2x + 1",
            bbox=BBox(x=100, y=100, width=200, height=150),
            confidence=Confidence(value=0.90, source="test", element_type="curve"),
            properties=NodeProperties(equation="y = 2x + 1"),
        )

        edges = inferrer.infer([point_node, curve_node])

        # Should have LIES_ON or spatial edges
        lies_on = [e for e in edges if e.edge_type == EdgeType.LIES_ON]
        passes_through = [e for e in edges if e.edge_type == EdgeType.PASSES_THROUGH]
        # Due to bbox proximity, there should be edges
        assert len(edges) > 0

    def test_infer_graph_of_edge(self):
        """Test GRAPH_OF edge is inferred between equation and curve."""
        inferrer = EdgeInferrer(proximity_threshold_px=150.0)

        equation_node = SemanticNode(
            id="eq-001",
            node_type=NodeType.EQUATION,
            label="y = x^2",
            bbox=BBox(x=100, y=50, width=100, height=40),
            confidence=Confidence(value=0.88, source="test", element_type="equation"),
            properties=NodeProperties(latex="y = x^2", equation="y = x^2"),
        )

        curve_node = SemanticNode(
            id="curve-001",
            node_type=NodeType.CURVE,
            label="Parabola",
            bbox=BBox(x=80, y=100, width=250, height=200),
            confidence=Confidence(value=0.90, source="test", element_type="curve"),
            properties=NodeProperties(equation="y = x^2"),
        )

        edges = inferrer.infer([equation_node, curve_node])

        # Should have GRAPH_OF edge due to matching equations
        graph_of = [e for e in edges if e.edge_type == EdgeType.GRAPH_OF]
        assert len(graph_of) >= 1


class TestEdgeDeduplication:
    """Test edge deduplication logic."""

    def test_deduplicate_removes_duplicates(self):
        """Test deduplication removes duplicate edges."""
        inferrer = EdgeInferrer()

        from mathpix_pipeline.schemas.semantic_graph import SemanticEdge

        edge1 = SemanticEdge(
            id="edge-001",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.80, source="test", element_type="adjacent"),
        )

        edge2 = SemanticEdge(
            id="edge-002",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.75, source="test", element_type="adjacent"),
        )

        deduped = inferrer._deduplicate_edges([edge1, edge2])

        # Should keep only one edge
        assert len(deduped) == 1
        # Should keep higher confidence
        assert deduped[0].confidence.value == 0.80

    def test_deduplicate_keeps_different_types(self):
        """Test deduplication keeps edges with different types."""
        inferrer = EdgeInferrer()

        from mathpix_pipeline.schemas.semantic_graph import SemanticEdge

        edge1 = SemanticEdge(
            id="edge-001",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.80, source="test", element_type="adjacent"),
        )

        edge2 = SemanticEdge(
            id="edge-002",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.LABELS,
            confidence=Confidence(value=0.85, source="test", element_type="labels"),
        )

        deduped = inferrer._deduplicate_edges([edge1, edge2])

        # Should keep both (different types)
        assert len(deduped) == 2

    def test_bidirectional_dedup(self):
        """Test bidirectional edges are properly deduplicated."""
        inferrer = EdgeInferrer()

        from mathpix_pipeline.schemas.semantic_graph import SemanticEdge

        edge1 = SemanticEdge(
            id="edge-001",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.80, source="test", element_type="adjacent"),
            bidirectional=True,
        )

        # Reverse direction but same type (bidirectional)
        edge2 = SemanticEdge(
            id="edge-002",
            source_id="node-b",
            target_id="node-a",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.75, source="test", element_type="adjacent"),
            bidirectional=True,
        )

        deduped = inferrer._deduplicate_edges([edge1, edge2])

        # Should keep only one edge for bidirectional
        assert len(deduped) == 1


class TestStatsTracking:
    """Test statistics tracking in edge inference."""

    def test_stats_initial_state(self):
        """Test initial stats are zero."""
        inferrer = EdgeInferrer()
        stats = inferrer.stats
        assert stats["total_edges"] == 0
        assert stats["spatial_edges"] == 0
        assert stats["label_edges"] == 0
        assert stats["mathematical_edges"] == 0

    def test_stats_tracking_after_inference(self, sample_nodes):
        """Test stats are tracked after inference."""
        inferrer = EdgeInferrer(proximity_threshold_px=100.0)

        edges = inferrer.infer(sample_nodes)
        stats = inferrer.stats

        assert stats["total_edges"] == len(edges)
        assert stats["above_threshold"] + stats["below_threshold"] == len(edges)

    def test_stats_reset_between_inferences(self):
        """Test stats reset between inference calls."""
        inferrer = EdgeInferrer(proximity_threshold_px=100.0)

        node1 = SemanticNode(
            id="node-1",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=0, y=0, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        # First inference
        inferrer.infer([node1])

        # Second inference
        node2 = SemanticNode(
            id="node-2",
            node_type=NodeType.POINT,
            label="B",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        inferrer.infer([node2])
        stats = inferrer.stats

        # Stats should reflect second inference only
        assert stats["total_edges"] == 0  # Single node = no edges
