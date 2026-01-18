"""
Unit tests for NodeExtractor (Stage E component).

Tests node extraction from AlignmentReport:
- Matched pair extraction
- Unmatched element extraction
- Node type classification
- Confidence propagation
"""

import pytest

from mathpix_pipeline.semantic_graph import (
    NodeExtractor,
    create_node_extractor,
    MATCH_TYPE_TO_NODE_TYPE,
    ELEMENT_CLASS_TO_NODE_TYPE,
)
from mathpix_pipeline.schemas.semantic_graph import NodeType
from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    MatchType,
    TextElement,
    VisualElement,
    MatchedPair,
    UnmatchedElement,
    AlignmentReport,
    AlignmentStatistics,
)


class TestNodeExtractorInit:
    """Test NodeExtractor initialization."""

    def test_default_init(self):
        """Test default initialization."""
        extractor = NodeExtractor()
        assert extractor.default_threshold == 0.60
        assert extractor.unmatched_confidence_penalty == 0.3

    def test_custom_init(self):
        """Test initialization with custom parameters."""
        extractor = NodeExtractor(
            default_threshold=0.75,
            unmatched_confidence_penalty=0.5,
        )
        assert extractor.default_threshold == 0.75
        assert extractor.unmatched_confidence_penalty == 0.5

    def test_factory_function(self):
        """Test create_node_extractor factory."""
        extractor = create_node_extractor(threshold=0.70, penalty=0.4)
        assert extractor.default_threshold == 0.70
        assert extractor.unmatched_confidence_penalty == 0.4

    def test_stats_initial_state(self):
        """Test initial stats are zero."""
        extractor = NodeExtractor()
        stats = extractor.stats
        assert stats["total_extracted"] == 0
        assert stats["from_matched"] == 0
        assert stats["from_unmatched"] == 0


class TestExtractFromMatchedPair:
    """Test node extraction from matched pairs."""

    def test_extract_from_matched_pair(self, sample_matched_pair):
        """Test extraction from a matched pair."""
        extractor = NodeExtractor()

        # Create alignment report with single matched pair
        report = AlignmentReport(
            image_id="test-001",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
            matched_pairs=[sample_matched_pair],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        node = nodes[0]
        assert node.id.startswith("matched_")
        assert node.label == "y = 2x + 1"
        assert node.confidence.value > 0
        assert len(node.source_element_ids) == 2

    def test_extract_label_to_point(self, label_matched_pair):
        """Test extraction from label-to-point match."""
        extractor = NodeExtractor()

        report = AlignmentReport(
            image_id="test-002",
            text_spec_id="text-002",
            vision_spec_id="vision-002",
            matched_pairs=[label_matched_pair],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        node = nodes[0]
        assert node.node_type == NodeType.POINT
        assert node.label == "A"

    def test_matched_pair_confidence_propagation(self, sample_matched_pair):
        """Test confidence is propagated from matched pair."""
        extractor = NodeExtractor()

        report = AlignmentReport(
            image_id="test-003",
            text_spec_id="text-003",
            vision_spec_id="vision-003",
            matched_pairs=[sample_matched_pair],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        node = nodes[0]
        # Confidence should be derived from consistency and semantic similarity
        assert 0.0 <= node.confidence.value <= 1.0
        assert node.confidence.source == "alignment_propagation"

    def test_low_confidence_pair_marked_for_review(self, low_confidence_matched_pair):
        """Test low confidence pairs are marked for review."""
        extractor = NodeExtractor()

        report = AlignmentReport(
            image_id="test-004",
            text_spec_id="text-004",
            vision_spec_id="vision-004",
            matched_pairs=[low_confidence_matched_pair],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        node = nodes[0]
        # Node should be below threshold due to low consistency score
        assert not node.threshold_passed
        assert node.review.review_required


class TestExtractFromUnmatched:
    """Test node extraction from unmatched elements."""

    def test_extract_from_unmatched(self, sample_alignment_report):
        """Test extraction includes unmatched elements."""
        extractor = NodeExtractor()

        nodes = extractor.extract(sample_alignment_report)

        # Should have nodes from both matched and unmatched
        stats = extractor.stats
        assert stats["from_matched"] == 2  # Two matched pairs in fixture
        assert stats["from_unmatched"] == 1  # One unmatched element

    def test_unmatched_confidence_penalty(self):
        """Test unmatched elements receive confidence penalty."""
        extractor = NodeExtractor(unmatched_confidence_penalty=0.3)

        unmatched = UnmatchedElement(
            id="unmatched-001",
            source="visual",
            element_id="visual-001",
            content="Unknown shape",
            bbox=BBox(x=100, y=100, width=50, height=50),
            reason="No matching text",
        )

        report = AlignmentReport(
            image_id="test-005",
            text_spec_id="text-005",
            vision_spec_id="vision-005",
            matched_pairs=[],
            unmatched_elements=[unmatched],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        node = nodes[0]
        # Base confidence is 0.5, penalty is 0.3, so result = 0.5 * 0.7 = 0.35
        assert node.confidence.value == pytest.approx(0.35, abs=0.01)
        assert node.confidence.source == "unmatched_element"


class TestNodeTypeClassification:
    """Test node type classification logic."""

    def test_match_type_to_node_type_mapping(self):
        """Test MATCH_TYPE_TO_NODE_TYPE mapping."""
        assert MATCH_TYPE_TO_NODE_TYPE[MatchType.LABEL_TO_POINT] == NodeType.POINT
        assert MATCH_TYPE_TO_NODE_TYPE[MatchType.LABEL_TO_CURVE] == NodeType.CURVE
        assert MATCH_TYPE_TO_NODE_TYPE[MatchType.EQUATION_TO_GRAPH] == NodeType.EQUATION
        assert MATCH_TYPE_TO_NODE_TYPE[MatchType.AXIS_LABEL] == NodeType.AXIS

    def test_element_class_to_node_type_mapping(self):
        """Test ELEMENT_CLASS_TO_NODE_TYPE mapping."""
        assert ELEMENT_CLASS_TO_NODE_TYPE["point"] == NodeType.POINT
        assert ELEMENT_CLASS_TO_NODE_TYPE["line"] == NodeType.LINE
        assert ELEMENT_CLASS_TO_NODE_TYPE["curve"] == NodeType.CURVE
        assert ELEMENT_CLASS_TO_NODE_TYPE["circle"] == NodeType.CIRCLE
        assert ELEMENT_CLASS_TO_NODE_TYPE["polygon"] == NodeType.POLYGON
        assert ELEMENT_CLASS_TO_NODE_TYPE["angle"] == NodeType.ANGLE

    def test_classification_from_visual_element_class(self):
        """Test classification prioritizes visual element class."""
        extractor = NodeExtractor()

        text_elem = TextElement(
            id="text-001",
            content="Shape",
            latex=None,
            bbox=BBox(x=100, y=100, width=50, height=30),
        )

        visual_elem = VisualElement(
            id="visual-001",
            element_class="circle",
            semantic_label="Circle shape",
            bbox=BBox(x=100, y=100, width=100, height=100),
        )

        matched = MatchedPair(
            id="match-001",
            match_type=MatchType.DESCRIPTION_TO_ELEMENT,
            text_element=text_elem,
            visual_element=visual_elem,
            consistency_score=0.80,
            confidence=Confidence(value=0.80, source="test", element_type="test"),
            applied_threshold=0.60,
        )

        report = AlignmentReport(
            image_id="test-006",
            text_spec_id="text-006",
            vision_spec_id="vision-006",
            matched_pairs=[matched],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        assert nodes[0].node_type == NodeType.CIRCLE

    def test_latex_pattern_detection_equation(self):
        """Test LaTeX pattern detection for equations."""
        extractor = NodeExtractor()

        text_elem = TextElement(
            id="text-001",
            content="",
            latex="y = x^2 + 2x + 1",
            bbox=BBox(x=100, y=100, width=200, height=50),
        )

        visual_elem = VisualElement(
            id="visual-001",
            element_class="text",  # Generic class
            semantic_label="Math expression",
            bbox=BBox(x=100, y=100, width=200, height=50),
        )

        matched = MatchedPair(
            id="match-001",
            match_type=MatchType.DESCRIPTION_TO_ELEMENT,
            text_element=text_elem,
            visual_element=visual_elem,
            consistency_score=0.85,
            confidence=Confidence(value=0.85, source="test", element_type="test"),
            applied_threshold=0.60,
        )

        report = AlignmentReport(
            image_id="test-007",
            text_spec_id="text-007",
            vision_spec_id="vision-007",
            matched_pairs=[matched],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        assert nodes[0].node_type == NodeType.EQUATION

    def test_coordinate_pattern_detection(self):
        """Test coordinate pattern detection for points."""
        extractor = NodeExtractor()

        text_elem = TextElement(
            id="text-001",
            content="(2, 4)",
            latex="(2, 4)",
            bbox=BBox(x=200, y=150, width=40, height=20),
        )

        visual_elem = VisualElement(
            id="visual-001",
            element_class="label",
            semantic_label="Coordinate label",
            bbox=BBox(x=200, y=150, width=40, height=20),
        )

        matched = MatchedPair(
            id="match-001",
            match_type=MatchType.COORDINATE_TO_POINT,
            text_element=text_elem,
            visual_element=visual_elem,
            consistency_score=0.90,
            confidence=Confidence(value=0.90, source="test", element_type="test"),
            applied_threshold=0.60,
        )

        report = AlignmentReport(
            image_id="test-008",
            text_spec_id="text-008",
            vision_spec_id="vision-008",
            matched_pairs=[matched],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        assert nodes[0].node_type == NodeType.POINT
        # Coordinates should be extracted into properties
        assert nodes[0].properties.coordinates == {"x": 2.0, "y": 4.0}


class TestConfidencePropagation:
    """Test confidence propagation in node extraction."""

    def test_high_consistency_high_confidence(self, sample_matched_pair):
        """Test high consistency score results in high confidence."""
        extractor = NodeExtractor()

        report = AlignmentReport(
            image_id="test-009",
            text_spec_id="text-009",
            vision_spec_id="vision-009",
            matched_pairs=[sample_matched_pair],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        node = nodes[0]
        # With consistency 0.85 and semantic similarity 0.88, confidence should be good
        assert node.confidence.value > 0.70

    def test_stats_tracking(self, sample_alignment_report):
        """Test statistics are tracked correctly."""
        extractor = NodeExtractor()
        extractor.extract(sample_alignment_report)

        stats = extractor.stats
        assert stats["total_extracted"] == 3  # 2 matched + 1 unmatched
        assert stats["from_matched"] == 2
        assert stats["from_unmatched"] == 1
        assert stats["above_threshold"] >= 0
        assert stats["below_threshold"] >= 0
        assert stats["above_threshold"] + stats["below_threshold"] == stats["total_extracted"]

    def test_stats_reset(self):
        """Test stats reset between extractions."""
        extractor = NodeExtractor()

        # First extraction
        report1 = AlignmentReport(
            image_id="test-010",
            text_spec_id="text-010",
            vision_spec_id="vision-010",
            matched_pairs=[],
            unmatched_elements=[
                UnmatchedElement(
                    id="u1", source="text", element_id="t1",
                    content="A", bbox=None, reason="test"
                )
            ],
            statistics=AlignmentStatistics(),
        )
        extractor.extract(report1)
        assert extractor.stats["total_extracted"] == 1

        # Second extraction should reset stats
        report2 = AlignmentReport(
            image_id="test-011",
            text_spec_id="text-011",
            vision_spec_id="vision-011",
            matched_pairs=[],
            unmatched_elements=[
                UnmatchedElement(
                    id="u2", source="text", element_id="t2",
                    content="B", bbox=None, reason="test"
                ),
                UnmatchedElement(
                    id="u3", source="text", element_id="t3",
                    content="C", bbox=None, reason="test"
                ),
            ],
            statistics=AlignmentStatistics(),
        )
        extractor.extract(report2)
        assert extractor.stats["total_extracted"] == 2


class TestPropertyExtraction:
    """Test property extraction for different node types."""

    def test_point_coordinate_extraction(self):
        """Test coordinates are extracted for point nodes."""
        extractor = NodeExtractor()

        text_elem = TextElement(
            id="text-001",
            content="Point P at (-3, 5)",
            latex="(-3, 5)",
            bbox=BBox(x=100, y=100, width=80, height=25),
        )

        visual_elem = VisualElement(
            id="visual-001",
            element_class="point",
            semantic_label="Point P",
            bbox=BBox(x=150, y=200, width=20, height=20),
        )

        matched = MatchedPair(
            id="match-001",
            match_type=MatchType.LABEL_TO_POINT,
            text_element=text_elem,
            visual_element=visual_elem,
            consistency_score=0.88,
            confidence=Confidence(value=0.88, source="test", element_type="test"),
            applied_threshold=0.60,
        )

        report = AlignmentReport(
            image_id="test-012",
            text_spec_id="text-012",
            vision_spec_id="vision-012",
            matched_pairs=[matched],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        props = nodes[0].properties
        assert props.coordinates == {"x": -3.0, "y": 5.0}

    def test_equation_latex_extraction(self):
        """Test LaTeX is extracted for equation nodes."""
        extractor = NodeExtractor()

        text_elem = TextElement(
            id="text-001",
            content="",
            latex="f(x) = \\sin(x)",
            bbox=BBox(x=100, y=100, width=150, height=40),
        )

        visual_elem = VisualElement(
            id="visual-001",
            element_class="equation",
            semantic_label="Sine function",
            bbox=BBox(x=100, y=100, width=150, height=40),
        )

        matched = MatchedPair(
            id="match-001",
            match_type=MatchType.EQUATION_TO_GRAPH,
            text_element=text_elem,
            visual_element=visual_elem,
            consistency_score=0.90,
            confidence=Confidence(value=0.90, source="test", element_type="test"),
            applied_threshold=0.60,
        )

        report = AlignmentReport(
            image_id="test-013",
            text_spec_id="text-013",
            vision_spec_id="vision-013",
            matched_pairs=[matched],
            unmatched_elements=[],
            statistics=AlignmentStatistics(),
        )

        nodes = extractor.extract(report)

        assert len(nodes) == 1
        props = nodes[0].properties
        assert props.latex == "f(x) = \\sin(x)"
