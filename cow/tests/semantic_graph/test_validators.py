"""
Unit tests for GraphValidator (Stage E component).

Tests graph validation:
- Valid graph passes
- Invalid edge reference detection
- Duplicate edge detection
- Edge type validation
- Connectivity analysis
"""

import pytest

from mathpix_pipeline.semantic_graph import (
    GraphValidator,
    create_graph_validator,
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    VALID_EDGE_RULES,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticNode,
    SemanticEdge,
    SemanticGraph,
    NodeType,
    EdgeType,
)
from mathpix_pipeline.schemas import BBox, Confidence


class TestGraphValidatorInit:
    """Test GraphValidator initialization."""

    def test_default_init(self):
        """Test default initialization."""
        validator = GraphValidator()
        assert validator.strict_mode is False
        assert validator.connectivity_warning_threshold == 3
        assert validator.isolated_nodes_threshold == 2

    def test_custom_init(self):
        """Test initialization with custom parameters."""
        validator = GraphValidator(
            strict_mode=True,
            connectivity_warning_threshold=5,
            isolated_nodes_threshold=4,
        )
        assert validator.strict_mode is True
        assert validator.connectivity_warning_threshold == 5
        assert validator.isolated_nodes_threshold == 4

    def test_factory_function(self):
        """Test create_graph_validator factory."""
        validator = create_graph_validator(
            strict=True,
            component_threshold=10,
            isolated_threshold=5,
        )
        assert validator.strict_mode is True
        assert validator.connectivity_warning_threshold == 10
        assert validator.isolated_nodes_threshold == 5


class TestValidGraphPasses:
    """Test valid graphs pass validation."""

    def test_valid_graph_passes(self, sample_graph):
        """Test a valid graph passes validation."""
        validator = GraphValidator()

        result = validator.validate(sample_graph)

        # Should pass (no ERROR-level issues)
        assert result.is_valid
        assert result.error_count == 0

    def test_empty_graph_passes(self, empty_graph):
        """Test an empty graph passes validation."""
        validator = GraphValidator()

        result = validator.validate(empty_graph)

        # Empty graph is valid (no errors)
        assert result.is_valid
        assert result.error_count == 0

    def test_valid_result_str(self, sample_graph):
        """Test ValidationResult string representation."""
        validator = GraphValidator()

        result = validator.validate(sample_graph)

        result_str = str(result)
        assert "VALID" in result_str or "INVALID" in result_str


class TestInvalidEdgeReference:
    """Test detection of invalid edge references."""

    def test_invalid_source_reference(self, sample_nodes):
        """Test detection of edge with invalid source reference."""
        validator = GraphValidator()

        invalid_edge = SemanticEdge(
            id="edge-invalid-001",
            source_id="nonexistent-node",
            target_id="node-point-001",
            edge_type=EdgeType.LABELS,
            confidence=Confidence(value=0.80, source="test", element_type="labels"),
        )

        graph = SemanticGraph(
            image_id="test-001",
            alignment_report_id="align-001",
            nodes=sample_nodes,
            edges=[invalid_edge],
        )

        result = validator.validate(graph)

        # Should fail with INVALID_SOURCE_REF error
        assert not result.is_valid
        assert result.error_count >= 1

        error_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.ERROR]
        assert "INVALID_SOURCE_REF" in error_codes

    def test_invalid_target_reference(self, sample_nodes):
        """Test detection of edge with invalid target reference."""
        validator = GraphValidator()

        invalid_edge = SemanticEdge(
            id="edge-invalid-002",
            source_id="node-point-001",
            target_id="nonexistent-node",
            edge_type=EdgeType.LIES_ON,
            confidence=Confidence(value=0.80, source="test", element_type="lies_on"),
        )

        graph = SemanticGraph(
            image_id="test-002",
            alignment_report_id="align-002",
            nodes=sample_nodes,
            edges=[invalid_edge],
        )

        result = validator.validate(graph)

        # Should fail with INVALID_TARGET_REF error
        assert not result.is_valid

        error_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.ERROR]
        assert "INVALID_TARGET_REF" in error_codes

    def test_self_referential_edge_warning(self, sample_nodes):
        """Test detection of self-referential edge."""
        validator = GraphValidator()

        self_edge = SemanticEdge(
            id="edge-self-001",
            source_id="node-point-001",
            target_id="node-point-001",  # Same as source
            edge_type=EdgeType.INTERSECTS,
            confidence=Confidence(value=0.80, source="test", element_type="intersects"),
        )

        graph = SemanticGraph(
            image_id="test-003",
            alignment_report_id="align-003",
            nodes=sample_nodes,
            edges=[self_edge],
        )

        result = validator.validate(graph)

        # Should have WARNING for self-referential edge
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "SELF_REFERENTIAL_EDGE" in warning_codes


class TestDuplicateEdgeWarning:
    """Test detection of duplicate edges."""

    def test_duplicate_edge_warning(self, graph_with_duplicate_edges):
        """Test detection of duplicate edges."""
        validator = GraphValidator()

        result = validator.validate(graph_with_duplicate_edges)

        # Should have WARNING for duplicate edge
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "DUPLICATE_EDGE" in warning_codes

    def test_same_nodes_different_types_not_duplicate(self, sample_nodes):
        """Test edges with same nodes but different types are not duplicates."""
        validator = GraphValidator()

        edge1 = SemanticEdge(
            id="edge-001",
            source_id="node-label-001",
            target_id="node-point-001",
            edge_type=EdgeType.LABELS,
            confidence=Confidence(value=0.80, source="test", element_type="labels"),
        )

        edge2 = SemanticEdge(
            id="edge-002",
            source_id="node-label-001",
            target_id="node-point-001",
            edge_type=EdgeType.ADJACENT_TO,  # Different type
            confidence=Confidence(value=0.75, source="test", element_type="adjacent"),
        )

        graph = SemanticGraph(
            image_id="test-004",
            alignment_report_id="align-004",
            nodes=sample_nodes,
            edges=[edge1, edge2],
        )

        result = validator.validate(graph)

        # Should NOT have duplicate edge warning
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "DUPLICATE_EDGE" not in warning_codes


class TestEdgeTypeValidation:
    """Test edge type validation against node types."""

    def test_valid_edge_rules_constant(self):
        """Test VALID_EDGE_RULES constant has expected entries."""
        # Label -> Point is valid with LABELS
        key = (NodeType.LABEL, NodeType.POINT)
        assert key in VALID_EDGE_RULES
        assert EdgeType.LABELS in VALID_EDGE_RULES[key]

        # Equation -> Curve is valid with GRAPH_OF
        key = (NodeType.EQUATION, NodeType.CURVE)
        assert key in VALID_EDGE_RULES
        assert EdgeType.GRAPH_OF in VALID_EDGE_RULES[key]

    def test_suspicious_edge_type_warning(self, sample_nodes):
        """Test detection of suspicious edge type for node pair."""
        validator = GraphValidator()

        # GRAPH_OF between label and point is unusual
        suspicious_edge = SemanticEdge(
            id="edge-suspicious-001",
            source_id="node-label-001",
            target_id="node-point-001",
            edge_type=EdgeType.GRAPH_OF,  # Unusual for label->point
            confidence=Confidence(value=0.70, source="test", element_type="graph_of"),
        )

        graph = SemanticGraph(
            image_id="test-005",
            alignment_report_id="align-005",
            nodes=sample_nodes,
            edges=[suspicious_edge],
        )

        result = validator.validate(graph)

        # Should have WARNING for suspicious edge type
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "SUSPICIOUS_EDGE_TYPE" in warning_codes

    def test_unknown_node_pair_info(self):
        """Test INFO for node pairs without validation rules."""
        validator = GraphValidator()

        # Create unusual node types
        func_node = SemanticNode(
            id="func-001",
            node_type=NodeType.FUNCTION,
            label="f(x)",
            bbox=BBox(x=100, y=100, width=100, height=50),
            confidence=Confidence(value=0.80, source="test", element_type="function"),
        )

        const_node = SemanticNode(
            id="const-001",
            node_type=NodeType.CONSTANT,
            label="pi",
            bbox=BBox(x=200, y=200, width=30, height=20),
            confidence=Confidence(value=0.85, source="test", element_type="constant"),
        )

        # EQUALS edge between function and constant (may not have rule)
        edge = SemanticEdge(
            id="edge-001",
            source_id="func-001",
            target_id="const-001",
            edge_type=EdgeType.EQUALS,
            confidence=Confidence(value=0.70, source="test", element_type="equals"),
        )

        graph = SemanticGraph(
            image_id="test-006",
            alignment_report_id="align-006",
            nodes=[func_node, const_node],
            edges=[edge],
        )

        result = validator.validate(graph)

        # Should have INFO or WARNING for unknown pair
        info_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.INFO]
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "UNKNOWN_NODE_PAIR" in info_codes or "SUSPICIOUS_EDGE_TYPE" in warning_codes


class TestConnectivityValidation:
    """Test connectivity analysis validation."""

    def test_isolated_nodes_warning(self):
        """Test warning for many isolated nodes."""
        validator = GraphValidator(isolated_nodes_threshold=1)

        # Create multiple isolated nodes
        nodes = [
            SemanticNode(
                id=f"node-{i}",
                node_type=NodeType.POINT,
                label=f"Point {i}",
                bbox=BBox(x=i*100, y=i*100, width=20, height=20),
                confidence=Confidence(value=0.80, source="test", element_type="point"),
            )
            for i in range(3)
        ]

        graph = SemanticGraph(
            image_id="test-007",
            alignment_report_id="align-007",
            nodes=nodes,
            edges=[],  # No edges = all isolated
        )

        result = validator.validate(graph)

        # Should have WARNING for many isolated nodes
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "MANY_ISOLATED_NODES" in warning_codes

    def test_fragmented_graph_warning(self):
        """Test warning for highly fragmented graph."""
        validator = GraphValidator(connectivity_warning_threshold=2)

        # Create nodes in separate components
        nodes = [
            SemanticNode(
                id="node-a1",
                node_type=NodeType.POINT,
                label="A1",
                bbox=BBox(x=100, y=100, width=20, height=20),
                confidence=Confidence(value=0.80, source="test", element_type="point"),
            ),
            SemanticNode(
                id="node-a2",
                node_type=NodeType.POINT,
                label="A2",
                bbox=BBox(x=150, y=150, width=20, height=20),
                confidence=Confidence(value=0.80, source="test", element_type="point"),
            ),
            SemanticNode(
                id="node-b1",
                node_type=NodeType.POINT,
                label="B1",
                bbox=BBox(x=300, y=300, width=20, height=20),
                confidence=Confidence(value=0.80, source="test", element_type="point"),
            ),
            SemanticNode(
                id="node-b2",
                node_type=NodeType.POINT,
                label="B2",
                bbox=BBox(x=350, y=350, width=20, height=20),
                confidence=Confidence(value=0.80, source="test", element_type="point"),
            ),
            SemanticNode(
                id="node-c1",
                node_type=NodeType.POINT,
                label="C1",
                bbox=BBox(x=500, y=500, width=20, height=20),
                confidence=Confidence(value=0.80, source="test", element_type="point"),
            ),
        ]

        edges = [
            SemanticEdge(
                id="edge-a",
                source_id="node-a1",
                target_id="node-a2",
                edge_type=EdgeType.ADJACENT_TO,
                confidence=Confidence(value=0.80, source="test", element_type="adjacent"),
            ),
            SemanticEdge(
                id="edge-b",
                source_id="node-b1",
                target_id="node-b2",
                edge_type=EdgeType.ADJACENT_TO,
                confidence=Confidence(value=0.80, source="test", element_type="adjacent"),
            ),
            # node-c1 is isolated = third component
        ]

        graph = SemanticGraph(
            image_id="test-008",
            alignment_report_id="align-008",
            nodes=nodes,
            edges=edges,
        )

        result = validator.validate(graph)

        # Should have WARNING for fragmented graph (3 components > threshold 2)
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "FRAGMENTED_GRAPH" in warning_codes


class TestConfidenceValidation:
    """Test confidence consistency validation."""

    def test_low_overall_confidence_warning(self):
        """Test warning for low overall confidence."""
        validator = GraphValidator()

        low_conf_node = SemanticNode(
            id="node-001",
            node_type=NodeType.POINT,
            label="A",
            bbox=BBox(x=100, y=100, width=20, height=20),
            confidence=Confidence(value=0.20, source="test", element_type="point"),
        )

        graph = SemanticGraph(
            image_id="test-009",
            alignment_report_id="align-009",
            nodes=[low_conf_node],
            edges=[],
            overall_confidence=0.15,  # Very low
        )

        result = validator.validate(graph)

        # Should have WARNING for low overall confidence
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "LOW_OVERALL_CONFIDENCE" in warning_codes

    def test_many_below_threshold_warning(self):
        """Test warning when many nodes are below threshold."""
        validator = GraphValidator()

        nodes = [
            SemanticNode(
                id=f"node-{i}",
                node_type=NodeType.POINT,
                label=f"Point {i}",
                bbox=BBox(x=i*100, y=i*100, width=20, height=20),
                confidence=Confidence(value=0.40, source="test", element_type="point"),
                applied_threshold=0.60,  # All below threshold
            )
            for i in range(5)
        ]

        graph = SemanticGraph(
            image_id="test-010",
            alignment_report_id="align-010",
            nodes=nodes,
            edges=[],
        )

        result = validator.validate(graph)

        # Should have WARNING for many nodes below threshold
        warning_codes = [i.code for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert "MANY_BELOW_THRESHOLD" in warning_codes


class TestStrictMode:
    """Test strict validation mode."""

    def test_strict_mode_treats_warnings_as_errors(self, sample_nodes):
        """Test strict mode treats warnings as errors."""
        validator = GraphValidator(strict_mode=True)

        # Create an edge that will trigger a warning
        self_edge = SemanticEdge(
            id="edge-self-001",
            source_id="node-point-001",
            target_id="node-point-001",
            edge_type=EdgeType.INTERSECTS,
            confidence=Confidence(value=0.80, source="test", element_type="intersects"),
        )

        graph = SemanticGraph(
            image_id="test-011",
            alignment_report_id="align-011",
            nodes=sample_nodes,
            edges=[self_edge],
        )

        result = validator.validate(graph)

        # In strict mode, warnings count as failures
        assert not result.is_valid

    def test_non_strict_mode_warnings_ok(self, sample_nodes):
        """Test non-strict mode allows warnings."""
        validator = GraphValidator(strict_mode=False)

        # Create an edge that will trigger a warning
        self_edge = SemanticEdge(
            id="edge-self-001",
            source_id="node-point-001",
            target_id="node-point-001",
            edge_type=EdgeType.INTERSECTS,
            confidence=Confidence(value=0.80, source="test", element_type="intersects"),
        )

        graph = SemanticGraph(
            image_id="test-012",
            alignment_report_id="align-012",
            nodes=sample_nodes,
            edges=[self_edge],
        )

        result = validator.validate(graph)

        # In non-strict mode, warnings are OK
        # (is_valid depends on no ERROR-level issues)
        assert result.warning_count >= 1


class TestValidationIssue:
    """Test ValidationIssue dataclass."""

    def test_issue_str_representation(self):
        """Test ValidationIssue string format."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="INVALID_SOURCE_REF",
            message="Edge references non-existent source node",
            element_id="edge-001",
            element_type="edge",
        )

        issue_str = str(issue)
        assert "ERROR" in issue_str
        assert "INVALID_SOURCE_REF" in issue_str
        assert "edge-001" in issue_str

    def test_issue_without_element_id(self):
        """Test ValidationIssue without element_id."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="FRAGMENTED_GRAPH",
            message="Graph has many disconnected components",
        )

        issue_str = str(issue)
        assert "WARNING" in issue_str
        assert "FRAGMENTED_GRAPH" in issue_str


class TestHelperMethods:
    """Test GraphValidator helper methods."""

    def test_has_errors(self, graph_with_invalid_edge):
        """Test has_errors method."""
        validator = GraphValidator()

        result = validator.validate(graph_with_invalid_edge)

        assert validator.has_errors(result)

    def test_get_errors_only(self, graph_with_invalid_edge):
        """Test get_errors_only method."""
        validator = GraphValidator()

        result = validator.validate(graph_with_invalid_edge)
        errors = validator.get_errors_only(result)

        assert all(e.severity == ValidationSeverity.ERROR for e in errors)
        assert len(errors) == result.error_count
