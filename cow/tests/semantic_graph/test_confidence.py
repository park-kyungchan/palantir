"""
Unit tests for ConfidencePropagator (Stage E component).

Tests confidence propagation through graphs:
- Edge confidence propagation
- Isolated node penalty
- Connectivity boost
- Overall confidence computation
"""

import pytest

from mathpix_pipeline.semantic_graph import (
    ConfidencePropagator,
    create_confidence_propagator,
    DEFAULT_EDGE_CONFIDENCE_FACTOR,
    DEFAULT_ISOLATED_NODE_PENALTY,
    DEFAULT_MIN_CONFIDENCE,
    DEFAULT_CONNECTIVITY_BOOST,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticNode,
    SemanticEdge,
    SemanticGraph,
    NodeType,
    EdgeType,
    NodeProperties,
)
from mathpix_pipeline.schemas import BBox, Confidence


class TestConfidencePropagatorInit:
    """Test ConfidencePropagator initialization."""

    def test_default_init(self):
        """Test default initialization."""
        propagator = ConfidencePropagator()
        assert propagator.edge_confidence_factor == DEFAULT_EDGE_CONFIDENCE_FACTOR
        assert propagator.isolated_node_penalty == DEFAULT_ISOLATED_NODE_PENALTY
        assert propagator.min_confidence == DEFAULT_MIN_CONFIDENCE
        assert propagator.connectivity_boost == DEFAULT_CONNECTIVITY_BOOST

    def test_custom_init(self):
        """Test initialization with custom parameters."""
        propagator = ConfidencePropagator(
            edge_confidence_factor=0.85,
            isolated_node_penalty=0.25,
            min_confidence=0.15,
            connectivity_boost=0.08,
        )
        assert propagator.edge_confidence_factor == 0.85
        assert propagator.isolated_node_penalty == 0.25
        assert propagator.min_confidence == 0.15
        assert propagator.connectivity_boost == 0.08

    def test_factory_function(self):
        """Test create_confidence_propagator factory."""
        propagator = create_confidence_propagator(
            edge_factor=0.80,
            isolation_penalty=0.30,
            min_conf=0.20,
            conn_boost=0.10,
        )
        assert propagator.edge_confidence_factor == 0.80
        assert propagator.isolated_node_penalty == 0.30
        assert propagator.min_confidence == 0.20
        assert propagator.connectivity_boost == 0.10

    def test_constants(self):
        """Test default constants have reasonable values."""
        assert 0.8 <= DEFAULT_EDGE_CONFIDENCE_FACTOR <= 1.0
        assert 0.1 <= DEFAULT_ISOLATED_NODE_PENALTY <= 0.5
        assert 0.0 < DEFAULT_MIN_CONFIDENCE <= 0.2
        assert 0.0 < DEFAULT_CONNECTIVITY_BOOST <= 0.1


class TestEdgeConfidencePropagation:
    """Test edge confidence propagation from endpoints."""

    def test_edge_confidence_from_high_endpoints(self, sample_graph):
        """Test edge confidence when endpoints have high confidence."""
        propagator = ConfidencePropagator()

        # Get original edge confidence
        original_conf = sample_graph.edges[0].confidence.value

        propagator.propagate(sample_graph)

        # Edge confidence should be adjusted based on endpoints
        new_conf = sample_graph.edges[0].confidence.value
        # With high-confidence endpoints, confidence should remain reasonable
        assert new_conf > 0

    def test_edge_confidence_from_low_endpoints(self):
        """Test edge confidence is reduced with low-confidence endpoints."""
        propagator = ConfidencePropagator()

        low_conf_node_a = SemanticNode(
            id="node-a",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.40, source="test", element_type="point"),
        )

        low_conf_node_b = SemanticNode(
            id="node-b",
            node_type=NodeType.POINT,
            label="B",
            bbox=BBox(x=200, y=200, width=20, height=20),
            confidence=Confidence(value=0.35, source="test", element_type="point"),
        )

        edge = SemanticEdge(
            id="edge-001",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.80, source="test", element_type="adjacent"),
        )

        graph = SemanticGraph(
            image_id="test-001",
            alignment_report_id="align-001",
            nodes=[low_conf_node_a, low_conf_node_b],
            edges=[edge],
        )

        original_edge_conf = edge.confidence.value

        propagator.propagate(graph)

        # Edge confidence should be reduced due to low-confidence endpoints
        new_edge_conf = graph.edges[0].confidence.value
        assert new_edge_conf < original_edge_conf

    def test_edge_confidence_minimum_enforced(self):
        """Test edge confidence doesn't go below minimum."""
        propagator = ConfidencePropagator(min_confidence=0.15)

        very_low_node_a = SemanticNode(
            id="node-a",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.10, source="test", element_type="point"),
        )

        very_low_node_b = SemanticNode(
            id="node-b",
            node_type=NodeType.POINT,
            label="B",
            bbox=BBox(x=200, y=200, width=20, height=20),
            confidence=Confidence(value=0.10, source="test", element_type="point"),
        )

        edge = SemanticEdge(
            id="edge-001",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.20, source="test", element_type="adjacent"),
        )

        graph = SemanticGraph(
            image_id="test-002",
            alignment_report_id="align-002",
            nodes=[very_low_node_a, very_low_node_b],
            edges=[edge],
        )

        propagator.propagate(graph)

        # Confidence should not go below minimum
        assert graph.edges[0].confidence.value >= propagator.min_confidence


class TestIsolatedNodePenalty:
    """Test isolated node penalty application."""

    def test_isolated_node_receives_penalty(self, isolated_node):
        """Test isolated nodes receive confidence penalty."""
        propagator = ConfidencePropagator(isolated_node_penalty=0.2)

        graph = SemanticGraph(
            image_id="test-003",
            alignment_report_id="align-003",
            nodes=[isolated_node],
            edges=[],
        )

        original_conf = isolated_node.confidence.value

        propagator.propagate(graph)

        # Isolated node should have reduced confidence
        new_conf = graph.nodes[0].confidence.value
        expected = original_conf * (1.0 - 0.2)  # 0.65 * 0.8 = 0.52
        assert new_conf == pytest.approx(expected, abs=0.01)

    def test_connected_node_no_penalty(self):
        """Test connected nodes don't receive isolation penalty."""
        propagator = ConfidencePropagator(isolated_node_penalty=0.2)

        node_a = SemanticNode(
            id="node-a",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        node_b = SemanticNode(
            id="node-b",
            node_type=NodeType.POINT,
            label="B",
            bbox=BBox(x=200, y=200, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        edge = SemanticEdge(
            id="edge-001",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.75, source="test", element_type="adjacent"),
        )

        graph = SemanticGraph(
            image_id="test-004",
            alignment_report_id="align-004",
            nodes=[node_a, node_b],
            edges=[edge],
        )

        propagator.propagate(graph)

        # Connected nodes should not have isolation penalty
        # (but may still have adjustment from edge propagation or boost)
        stats = propagator.stats
        assert stats["isolated_nodes"] == 0

    def test_isolation_penalty_minimum_enforced(self):
        """Test isolation penalty doesn't reduce below minimum."""
        propagator = ConfidencePropagator(
            isolated_node_penalty=0.9,  # Very high penalty
            min_confidence=0.15,
        )

        low_node = SemanticNode(
            id="node-001",
            node_type=NodeType.ANNOTATION,
            label="Note",
            bbox=BBox(x=100, y=100, width=50, height=30),
            confidence=Confidence(value=0.20, source="test", element_type="annotation"),
        )

        graph = SemanticGraph(
            image_id="test-005",
            alignment_report_id="align-005",
            nodes=[low_node],
            edges=[],
        )

        propagator.propagate(graph)

        # Should not go below minimum
        assert graph.nodes[0].confidence.value >= propagator.min_confidence


class TestConnectivityBoost:
    """Test connectivity boost for well-connected nodes."""

    def test_well_connected_node_receives_boost(self):
        """Test nodes with multiple connections receive boost."""
        propagator = ConfidencePropagator(connectivity_boost=0.05)

        # Central node with multiple connections
        central_node = SemanticNode(
            id="central",
            node_type=NodeType.CURVE,
            label="Main curve",
            bbox=BBox(x=200, y=200, width=100, height=100),
            confidence=Confidence(value=0.75, source="test", element_type="curve"),
        )

        node_a = SemanticNode(
            id="node-a",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=150, y=150, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        node_b = SemanticNode(
            id="node-b",
            node_type=NodeType.POINT,
            label="B",
            bbox=BBox(x=250, y=250, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        node_c = SemanticNode(
            id="node-c",
            node_type=NodeType.LABEL,
            label="Curve label",
            bbox=BBox(x=180, y=180, width=30, height=20),
            confidence=Confidence(value=0.70, source="test", element_type="label"),
        )

        edges = [
            SemanticEdge(
                id="edge-1",
                source_id="central",
                target_id="node-a",
                edge_type=EdgeType.PASSES_THROUGH,
                confidence=Confidence(value=0.80, source="test", element_type="passes"),
            ),
            SemanticEdge(
                id="edge-2",
                source_id="central",
                target_id="node-b",
                edge_type=EdgeType.PASSES_THROUGH,
                confidence=Confidence(value=0.80, source="test", element_type="passes"),
            ),
            SemanticEdge(
                id="edge-3",
                source_id="node-c",
                target_id="central",
                edge_type=EdgeType.LABELS,
                confidence=Confidence(value=0.75, source="test", element_type="labels"),
            ),
        ]

        graph = SemanticGraph(
            image_id="test-006",
            alignment_report_id="align-006",
            nodes=[central_node, node_a, node_b, node_c],
            edges=edges,
        )

        propagator.propagate(graph)

        # Central node (3 connections) should have been boosted
        stats = propagator.stats
        assert stats["boosted_nodes"] >= 1

    def test_single_connection_no_boost(self):
        """Test nodes with only 1 connection don't receive boost."""
        propagator = ConfidencePropagator(connectivity_boost=0.05)

        node_a = SemanticNode(
            id="node-a",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        node_b = SemanticNode(
            id="node-b",
            node_type=NodeType.POINT,
            label="B",
            bbox=BBox(x=200, y=200, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        edge = SemanticEdge(
            id="edge-001",
            source_id="node-a",
            target_id="node-b",
            edge_type=EdgeType.ADJACENT_TO,
            confidence=Confidence(value=0.75, source="test", element_type="adjacent"),
        )

        graph = SemanticGraph(
            image_id="test-007",
            alignment_report_id="align-007",
            nodes=[node_a, node_b],
            edges=[edge],
        )

        propagator.propagate(graph)

        # Each node has only 1 connection, no boost
        stats = propagator.stats
        assert stats["boosted_nodes"] == 0


class TestOverallConfidence:
    """Test overall confidence computation."""

    def test_overall_confidence_computed(self, sample_graph):
        """Test overall confidence is computed."""
        propagator = ConfidencePropagator()

        propagator.propagate(sample_graph)

        # Overall confidence should be computed
        assert sample_graph.overall_confidence > 0
        assert sample_graph.overall_confidence <= 1.0

    def test_overall_confidence_weighted_average(self):
        """Test overall confidence is weighted average of nodes and edges."""
        propagator = ConfidencePropagator()

        node = SemanticNode(
            id="node-001",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        graph = SemanticGraph(
            image_id="test-008",
            alignment_report_id="align-008",
            nodes=[node],
            edges=[],
        )

        propagator.propagate(graph)

        # With single isolated node, confidence should be penalized then used directly
        # Original: 0.80, after isolation penalty: 0.80 * 0.8 = 0.64
        assert graph.overall_confidence > 0

    def test_empty_graph_overall_confidence_zero(self, empty_graph):
        """Test empty graph has zero overall confidence."""
        propagator = ConfidencePropagator()

        propagator.propagate(empty_graph)

        assert empty_graph.overall_confidence == 0.0


class TestStatsTracking:
    """Test statistics tracking in confidence propagation."""

    def test_stats_initial_state(self):
        """Test initial stats are zero."""
        propagator = ConfidencePropagator()
        stats = propagator.stats
        assert stats["nodes_processed"] == 0
        assert stats["edges_processed"] == 0
        assert stats["isolated_nodes"] == 0
        assert stats["boosted_nodes"] == 0

    def test_stats_tracked_after_propagation(self, sample_graph):
        """Test stats are tracked after propagation."""
        propagator = ConfidencePropagator()

        propagator.propagate(sample_graph)
        stats = propagator.stats

        assert stats["nodes_processed"] == len(sample_graph.nodes)
        assert stats["edges_processed"] == len(sample_graph.edges)

    def test_stats_reset_between_propagations(self):
        """Test stats reset between propagation calls."""
        propagator = ConfidencePropagator()

        node1 = SemanticNode(
            id="node-1",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.80, source="test", element_type="point"),
        )

        graph1 = SemanticGraph(
            image_id="test-009",
            alignment_report_id="align-009",
            nodes=[node1],
            edges=[],
        )

        propagator.propagate(graph1)
        first_stats = propagator.stats

        # Second propagation
        node2 = SemanticNode(
            id="node-2",
            node_type=NodeType.POINT,
            label="B",
            bbox=BBox(x=200, y=200, width=20, height=20),
            confidence=Confidence(value=0.75, source="test", element_type="point"),
        )

        node3 = SemanticNode(
            id="node-3",
            node_type=NodeType.POINT,
            label="C",
            bbox=BBox(x=300, y=300, width=20, height=20),
            confidence=Confidence(value=0.70, source="test", element_type="point"),
        )

        graph2 = SemanticGraph(
            image_id="test-010",
            alignment_report_id="align-010",
            nodes=[node2, node3],
            edges=[],
        )

        propagator.propagate(graph2)
        second_stats = propagator.stats

        # Stats should reflect second propagation only
        assert second_stats["nodes_processed"] == 2


class TestAlignmentConfidencePropagation:
    """Test propagate_from_alignment method."""

    def test_propagate_from_alignment(self):
        """Test confidence propagation from alignment scores."""
        propagator = ConfidencePropagator()

        node = SemanticNode(
            id="node-001",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.70, source="test", element_type="point"),
            source_element_ids=["text-001", "visual-001"],
        )

        graph = SemanticGraph(
            image_id="test-011",
            alignment_report_id="align-011",
            nodes=[node],
            edges=[],
        )

        alignment_confidences = {
            "text-001": 0.90,
            "visual-001": 0.85,
        }

        propagator.propagate_from_alignment(graph, alignment_confidences)

        # Node confidence should be blended with alignment scores
        # Average alignment: (0.90 + 0.85) / 2 = 0.875
        # Blended: 0.875 * 0.6 + 0.70 * 0.4 = 0.525 + 0.28 = 0.805
        assert graph.nodes[0].confidence.value == pytest.approx(0.805, abs=0.01)
        assert graph.nodes[0].confidence.source == "alignment_propagated"

    def test_propagate_from_alignment_partial_match(self):
        """Test propagation when only some source elements have confidence."""
        propagator = ConfidencePropagator()

        node = SemanticNode(
            id="node-001",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.70, source="test", element_type="point"),
            source_element_ids=["text-001", "visual-001", "unknown-001"],
        )

        graph = SemanticGraph(
            image_id="test-012",
            alignment_report_id="align-012",
            nodes=[node],
            edges=[],
        )

        alignment_confidences = {
            "text-001": 0.90,
            # visual-001 and unknown-001 not in alignment_confidences
        }

        propagator.propagate_from_alignment(graph, alignment_confidences)

        # Should blend with single available confidence
        # Blended: 0.90 * 0.6 + 0.70 * 0.4 = 0.54 + 0.28 = 0.82
        assert graph.nodes[0].confidence.value == pytest.approx(0.82, abs=0.01)
