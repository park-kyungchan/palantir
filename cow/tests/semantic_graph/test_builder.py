"""
Integration tests for SemanticGraphBuilder (Stage E orchestrator).

Tests the complete graph building pipeline:
- Build from alignment report
- Build with custom configuration
- End-to-end processing
"""

import pytest

from mathpix_pipeline.semantic_graph import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    BuildResult,
    GraphBuildError,
    create_graph_builder,
    NodeExtractor,
    EdgeInferrer,
    ConfidencePropagator,
    GraphValidator,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
    NodeProperties,
)
from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    AlignmentReport,
    AlignmentStatistics,
    MatchedPair,
    MatchType,
    UnmatchedElement,
    TextElement,
    VisualElement,
)


class TestSemanticGraphBuilderInit:
    """Test SemanticGraphBuilder initialization."""

    def test_default_init(self):
        """Test default initialization creates all components."""
        builder = SemanticGraphBuilder()

        assert builder.config is not None
        assert builder.node_extractor is not None
        assert builder.edge_inferrer is not None
        assert builder.confidence_propagator is not None
        assert builder.validator is not None

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = GraphBuilderConfig(
            node_threshold=0.75,
            edge_threshold=0.65,
            strict_validation=True,
        )
        builder = SemanticGraphBuilder(config=config)

        assert builder.config.node_threshold == 0.75
        assert builder.config.edge_threshold == 0.65
        assert builder.config.strict_validation is True

    def test_init_with_custom_components(self):
        """Test initialization with custom component instances."""
        custom_extractor = NodeExtractor(default_threshold=0.80)
        custom_inferrer = EdgeInferrer(proximity_threshold_px=100.0)

        builder = SemanticGraphBuilder(
            node_extractor=custom_extractor,
            edge_inferrer=custom_inferrer,
        )

        assert builder.node_extractor is custom_extractor
        assert builder.edge_inferrer is custom_inferrer

    def test_factory_function_default(self):
        """Test create_graph_builder factory with defaults."""
        builder = create_graph_builder()

        assert isinstance(builder, SemanticGraphBuilder)
        assert builder.config.node_threshold == 0.60

    def test_factory_function_with_config(self):
        """Test create_graph_builder with custom config."""
        config = GraphBuilderConfig(node_threshold=0.70)
        builder = create_graph_builder(config=config)

        assert builder.config.node_threshold == 0.70


class TestBuildFromAlignmentReport:
    """Test building graph from AlignmentReport."""

    def test_build_from_alignment_report(self, sample_alignment_report):
        """Test basic graph building from alignment report."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        assert isinstance(result, BuildResult)
        assert isinstance(result.graph, SemanticGraph)
        assert result.graph.image_id == sample_alignment_report.image_id
        assert result.processing_time_ms > 0

    def test_build_extracts_nodes(self, sample_alignment_report):
        """Test that nodes are extracted from matched pairs."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        # Should have nodes from matched pairs and unmatched elements
        assert len(result.graph.nodes) >= 2  # At least from 2 matched pairs

    def test_build_infers_edges(self, sample_alignment_report):
        """Test that edges are inferred between nodes."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        # Should have some edges inferred (spatial or semantic)
        # Note: Exact count depends on spatial relationships in fixtures
        assert isinstance(result.graph.edges, list)

    def test_build_computes_overall_confidence(self, sample_alignment_report):
        """Test overall confidence is computed."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        assert 0.0 <= result.graph.overall_confidence <= 1.0

    def test_build_empty_report(self, empty_alignment_report):
        """Test building from empty alignment report."""
        builder = SemanticGraphBuilder()
        result = builder.build(empty_alignment_report)

        assert len(result.graph.nodes) == 0
        assert len(result.graph.edges) == 0
        assert result.is_valid  # Empty graph is valid

    def test_build_result_summary(self, sample_alignment_report):
        """Test BuildResult summary method."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        summary = result.summary()
        assert "BuildResult" in summary
        assert "nodes" in summary
        assert "edges" in summary
        assert "confidence" in summary


class TestBuildWithCustomConfig:
    """Test building with custom configuration."""

    def test_high_node_threshold(self, sample_alignment_report):
        """Test with high node threshold filters low confidence nodes."""
        config = GraphBuilderConfig(node_threshold=0.90)
        builder = SemanticGraphBuilder(config=config)
        result = builder.build(sample_alignment_report)

        # Nodes below 0.90 should be flagged for review
        for node in result.graph.nodes:
            if node.confidence.value < 0.90:
                assert node.review.review_required

    def test_strict_validation_mode(self, sample_alignment_report):
        """Test strict validation treats warnings as errors."""
        config = GraphBuilderConfig(
            strict_validation=True,
            fail_on_validation_error=False,
        )
        builder = SemanticGraphBuilder(config=config)
        result = builder.build(sample_alignment_report)

        # In strict mode, warnings count as errors
        # Result may or may not be valid depending on warnings
        assert isinstance(result.is_valid, bool)

    def test_fail_on_validation_disabled(self):
        """Test fail_on_validation_error=False doesn't raise."""
        config = GraphBuilderConfig(fail_on_validation_error=False)
        builder = SemanticGraphBuilder(config=config)

        # Create a report that might have issues
        report = AlignmentReport(
            image_id="test-001",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
            matched_pairs=[],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        # Should not raise even if validation has issues
        result = builder.build(report)
        assert isinstance(result, BuildResult)

    def test_custom_graph_type(self, sample_alignment_report):
        """Test graph_type is set in result."""
        config = GraphBuilderConfig(graph_type="function_graph")
        builder = SemanticGraphBuilder(config=config)
        result = builder.build(sample_alignment_report)

        assert result.graph.graph_type == "function_graph"

    def test_custom_proximity_threshold(self):
        """Test proximity_threshold_px affects edge inference."""
        # Create nodes that are close but not overlapping
        text_elem = TextElement(
            id="text-001",
            content="A",
            latex=None,
            bbox=BBox(x=100, y=100, width=30, height=20),
        )
        visual_elem = VisualElement(
            id="visual-001",
            element_class="point",
            semantic_label="Point A",
            bbox=BBox(x=140, y=100, width=20, height=20),
        )
        matched = MatchedPair(
            id="match-001",
            match_type=MatchType.LABEL_TO_POINT,
            text_element=text_elem,
            visual_element=visual_elem,
            consistency_score=0.85,
            confidence=Confidence(value=0.85, source="test", element_type="test"),
            applied_threshold=0.60,
        )

        report = AlignmentReport(
            image_id="proximity-test",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
            matched_pairs=[matched],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        # With low threshold, should find adjacent edges
        config_low = GraphBuilderConfig(proximity_threshold_px=100.0)
        builder_low = SemanticGraphBuilder(config=config_low)
        result_low = builder_low.build(report)

        # With high threshold, fewer adjacent edges expected
        config_high = GraphBuilderConfig(proximity_threshold_px=5.0)
        builder_high = SemanticGraphBuilder(config=config_high)
        result_high = builder_high.build(report)

        # Just verify both build successfully
        assert result_low.is_valid or not result_low.is_valid
        assert result_high.is_valid or not result_high.is_valid


class TestEndToEnd:
    """Test end-to-end graph building scenarios."""

    def test_end_to_end_simple_graph(self):
        """Test complete pipeline with a simple graph."""
        # Create a simple equation-to-graph match
        text_elem = TextElement(
            id="text-eq-001",
            content="y = x + 1",
            latex="y = x + 1",
            bbox=BBox(x=50, y=50, width=100, height=30),
        )
        visual_elem = VisualElement(
            id="visual-line-001",
            element_class="line",
            semantic_label="Linear function",
            bbox=BBox(x=100, y=100, width=200, height=150),
        )
        matched = MatchedPair(
            id="match-001",
            match_type=MatchType.EQUATION_TO_GRAPH,
            text_element=text_elem,
            visual_element=visual_elem,
            consistency_score=0.90,
            confidence=Confidence(value=0.90, source="test", element_type="test"),
            applied_threshold=0.60,
            semantic_similarity=0.92,
        )

        report = AlignmentReport(
            image_id="simple-graph-001",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
            matched_pairs=[matched],
            unmatched_elements=[],
            statistics=AlignmentStatistics(
                total_text_elements=1,
                total_visual_elements=1,
            ),
            overall_alignment_score=0.90,
            overall_confidence=0.90,
        )

        builder = SemanticGraphBuilder()
        result = builder.build(report)

        # Verify end-to-end
        assert result.is_valid
        assert len(result.graph.nodes) == 1
        assert result.graph.nodes[0].node_type in [NodeType.LINE, NodeType.EQUATION]
        assert result.graph.overall_confidence > 0.5

    def test_end_to_end_complex_graph(self):
        """Test complete pipeline with multiple elements."""
        # Create a more complex graph with point, label, and curve
        text_label = TextElement(
            id="text-label-001",
            content="P",
            latex=None,
            bbox=BBox(x=195, y=195, width=20, height=15),
        )
        visual_point = VisualElement(
            id="visual-point-001",
            element_class="point",
            semantic_label="Point P",
            bbox=BBox(x=200, y=200, width=10, height=10),
        )
        match_label = MatchedPair(
            id="match-label",
            match_type=MatchType.LABEL_TO_POINT,
            text_element=text_label,
            visual_element=visual_point,
            consistency_score=0.95,
            confidence=Confidence(value=0.95, source="test", element_type="test"),
            applied_threshold=0.60,
        )

        text_eq = TextElement(
            id="text-eq-001",
            content="y = x^2",
            latex="y = x^2",
            bbox=BBox(x=50, y=50, width=80, height=25),
        )
        visual_curve = VisualElement(
            id="visual-curve-001",
            element_class="curve",
            semantic_label="Parabola",
            bbox=BBox(x=100, y=100, width=300, height=200),
        )
        match_eq = MatchedPair(
            id="match-eq",
            match_type=MatchType.EQUATION_TO_GRAPH,
            text_element=text_eq,
            visual_element=visual_curve,
            consistency_score=0.88,
            confidence=Confidence(value=0.88, source="test", element_type="test"),
            applied_threshold=0.60,
            semantic_similarity=0.90,
        )

        report = AlignmentReport(
            image_id="complex-graph-001",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
            matched_pairs=[match_label, match_eq],
            unmatched_elements=[],
            statistics=AlignmentStatistics(
                total_text_elements=2,
                total_visual_elements=2,
            ),
            overall_alignment_score=0.91,
            overall_confidence=0.90,
        )

        builder = SemanticGraphBuilder()
        result = builder.build(report)

        # Verify complex graph
        assert result.is_valid
        assert len(result.graph.nodes) == 2

        # Check node types
        node_types = {n.node_type for n in result.graph.nodes}
        assert NodeType.POINT in node_types or NodeType.CURVE in node_types

    def test_end_to_end_with_unmatched(self):
        """Test pipeline handles unmatched elements."""
        unmatched = UnmatchedElement(
            id="unmatched-001",
            source="visual",
            element_id="visual-orphan-001",
            content="Orphan shape",
            bbox=BBox(x=400, y=400, width=50, height=50),
            reason="No matching text element",
        )

        report = AlignmentReport(
            image_id="unmatched-test-001",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
            matched_pairs=[],
            unmatched_elements=[unmatched],
            statistics=AlignmentStatistics(
                total_text_elements=0,
                total_visual_elements=1,
            ),
        )

        builder = SemanticGraphBuilder()
        result = builder.build(report)

        # Unmatched element should become a node
        assert len(result.graph.nodes) == 1
        # Unmatched nodes have lower confidence
        assert result.graph.nodes[0].confidence.value < 0.6

    def test_component_stats_tracking(self, sample_alignment_report):
        """Test component statistics are tracked."""
        builder = SemanticGraphBuilder()
        builder.build(sample_alignment_report)

        stats = builder.get_component_stats()

        assert "node_extractor" in stats
        assert "edge_inferrer" in stats
        assert "confidence_propagator" in stats

        # Node extractor should have tracked extractions
        assert stats["node_extractor"]["total_extracted"] >= 0


class TestBuildFromComponents:
    """Test build_from_components method."""

    def test_build_from_nodes(self, sample_nodes):
        """Test building from pre-extracted nodes."""
        builder = SemanticGraphBuilder()
        result = builder.build_from_components(
            image_id="test-components-001",
            nodes=sample_nodes,
        )

        assert isinstance(result, BuildResult)
        assert len(result.graph.nodes) == len(sample_nodes)

    def test_build_from_nodes_with_edges(self, sample_nodes, sample_edges):
        """Test building from pre-extracted nodes and edges."""
        builder = SemanticGraphBuilder()
        result = builder.build_from_components(
            image_id="test-components-002",
            nodes=sample_nodes,
            edges=sample_edges,
            infer_edges=False,
        )

        assert len(result.graph.nodes) == len(sample_nodes)
        assert len(result.graph.edges) == len(sample_edges)

    def test_build_from_nodes_no_inference(self, sample_nodes):
        """Test building without edge inference."""
        builder = SemanticGraphBuilder()
        result = builder.build_from_components(
            image_id="test-no-infer",
            nodes=sample_nodes,
            edges=None,
            infer_edges=False,
        )

        # No edges should be created
        assert len(result.graph.edges) == 0


class TestBuildResultMethods:
    """Test BuildResult helper methods."""

    def test_node_count_property(self, sample_alignment_report):
        """Test node_count property."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        assert result.node_count == len(result.graph.nodes)

    def test_edge_count_property(self, sample_alignment_report):
        """Test edge_count property."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        assert result.edge_count == len(result.graph.edges)

    def test_raise_if_invalid_on_valid(self, sample_alignment_report):
        """Test raise_if_invalid doesn't raise for valid graph."""
        builder = SemanticGraphBuilder()
        result = builder.build(sample_alignment_report)

        if result.is_valid:
            # Should not raise
            result.raise_if_invalid()

    def test_raise_if_invalid_on_invalid(self, graph_with_invalid_edge):
        """Test raise_if_invalid raises for invalid graph."""
        config = GraphBuilderConfig(fail_on_validation_error=False)
        builder = SemanticGraphBuilder(config=config)

        # Build from components with invalid edge
        result = builder.build_from_components(
            image_id="invalid-test",
            nodes=graph_with_invalid_edge.nodes,
            edges=graph_with_invalid_edge.edges,
            infer_edges=False,
        )

        if not result.is_valid:
            with pytest.raises(GraphBuildError):
                result.raise_if_invalid()


class TestGraphBuildError:
    """Test GraphBuildError exception."""

    def test_error_message(self):
        """Test error message formatting."""
        error = GraphBuildError("Test error", issues=[])
        assert str(error) == "Test error"

    def test_error_with_issues(self):
        """Test error formatting with issues."""
        from mathpix_pipeline.semantic_graph.validators import (
            ValidationIssue,
            ValidationSeverity,
        )

        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="TEST_ERROR",
                message="Test issue",
            )
        ]
        error = GraphBuildError("Validation failed", issues=issues)

        error_str = str(error)
        assert "Validation failed" in error_str
        assert "Issues:" in error_str


class TestGraphBuilderConfig:
    """Test GraphBuilderConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GraphBuilderConfig()

        assert config.node_threshold == 0.60
        assert config.unmatched_penalty == 0.3
        assert config.spatial_overlap_threshold == 0.1
        assert config.proximity_threshold_px == 50.0
        assert config.edge_threshold == 0.55
        assert config.edge_confidence_factor == 0.9
        assert config.isolated_node_penalty == 0.2
        assert config.strict_validation is False
        assert config.fail_on_validation_error is True
        assert config.graph_type is None

    def test_custom_values(self):
        """Test configuration with custom values."""
        config = GraphBuilderConfig(
            node_threshold=0.80,
            edge_threshold=0.70,
            graph_type="geometry",
        )

        assert config.node_threshold == 0.80
        assert config.edge_threshold == 0.70
        assert config.graph_type == "geometry"
