"""
GraphValidator for SemanticGraphBuilder (Stage E).

Validates semantic graph structure:
- Node/edge existence and references
- Graph connectivity analysis
- Edge type validity for node types
- Consistency checks

Module Version: 1.0.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import logging

from ..schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Validation Enums and Types
# =============================================================================

class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Must fix before proceeding
    WARNING = "warning"  # Should review
    INFO = "info"        # Informational


@dataclass
class ValidationIssue:
    """A validation issue found in the graph.

    Attributes:
        severity: Severity level of the issue
        code: Machine-readable issue code
        message: Human-readable description
        element_id: ID of the affected element (if applicable)
        element_type: Type of the affected element (node/edge)
        details: Additional context about the issue
    """
    severity: ValidationSeverity
    code: str
    message: str
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    details: Dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Format issue as string."""
        prefix = f"[{self.severity.value.upper()}] {self.code}"
        if self.element_id:
            prefix += f" ({self.element_type}:{self.element_id})"
        return f"{prefix}: {self.message}"


@dataclass
class ValidationResult:
    """Complete validation result for a graph.

    Attributes:
        is_valid: True if no ERROR-level issues found
        issues: List of all validation issues
        error_count: Number of ERROR-level issues
        warning_count: Number of WARNING-level issues
        info_count: Number of INFO-level issues
    """
    is_valid: bool
    issues: List[ValidationIssue]
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def __str__(self) -> str:
        """Format result as summary string."""
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"Validation {status}: "
            f"{self.error_count} errors, "
            f"{self.warning_count} warnings, "
            f"{self.info_count} info"
        )


# =============================================================================
# Edge Type Validation Rules
# =============================================================================

# Valid edge types between node type pairs
# Key: (source_type, target_type) -> Set of valid EdgeTypes
VALID_EDGE_RULES: Dict[tuple, Set[EdgeType]] = {
    # Label relationships
    (NodeType.LABEL, NodeType.POINT): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.LINE): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.LINE_SEGMENT): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.CURVE): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.CIRCLE): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.POLYGON): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.ANGLE): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.AXIS): {EdgeType.LABELS},
    (NodeType.LABEL, NodeType.REGION): {EdgeType.LABELS},
    (NodeType.ANNOTATION, NodeType.POINT): {EdgeType.LABELS},
    (NodeType.ANNOTATION, NodeType.CURVE): {EdgeType.LABELS},

    # Equation to graph relationships
    (NodeType.EQUATION, NodeType.CURVE): {EdgeType.GRAPH_OF, EdgeType.DEFINED_BY},
    (NodeType.EQUATION, NodeType.LINE): {EdgeType.GRAPH_OF, EdgeType.DEFINED_BY},
    (NodeType.EQUATION, NodeType.CIRCLE): {EdgeType.GRAPH_OF, EdgeType.DEFINED_BY},
    (NodeType.FUNCTION, NodeType.CURVE): {EdgeType.GRAPH_OF, EdgeType.DEFINED_BY},
    (NodeType.FUNCTION, NodeType.LINE): {EdgeType.GRAPH_OF, EdgeType.DEFINED_BY},

    # Point on curve relationships
    (NodeType.POINT, NodeType.LINE): {EdgeType.LIES_ON},
    (NodeType.POINT, NodeType.LINE_SEGMENT): {EdgeType.LIES_ON},
    (NodeType.POINT, NodeType.CURVE): {EdgeType.LIES_ON},
    (NodeType.POINT, NodeType.CIRCLE): {EdgeType.LIES_ON},
    (NodeType.POINT, NodeType.POLYGON): {EdgeType.LIES_ON, EdgeType.CONTAINED_BY},
    (NodeType.INTERCEPT, NodeType.LINE): {EdgeType.LIES_ON},
    (NodeType.INTERCEPT, NodeType.CURVE): {EdgeType.LIES_ON},
    (NodeType.INTERCEPT, NodeType.AXIS): {EdgeType.LIES_ON},

    # Line relationships
    (NodeType.LINE, NodeType.LINE): {
        EdgeType.INTERSECTS,
        EdgeType.PARALLEL_TO,
        EdgeType.PERPENDICULAR_TO
    },
    (NodeType.LINE_SEGMENT, NodeType.LINE_SEGMENT): {
        EdgeType.INTERSECTS,
        EdgeType.PARALLEL_TO,
        EdgeType.PERPENDICULAR_TO
    },
    (NodeType.LINE, NodeType.LINE_SEGMENT): {
        EdgeType.INTERSECTS,
        EdgeType.PARALLEL_TO,
        EdgeType.PERPENDICULAR_TO
    },

    # Containment relationships
    (NodeType.REGION, NodeType.POINT): {EdgeType.CONTAINS},
    (NodeType.REGION, NodeType.LINE_SEGMENT): {EdgeType.CONTAINS},
    (NodeType.POLYGON, NodeType.POINT): {EdgeType.CONTAINS},
    (NodeType.CIRCLE, NodeType.POINT): {EdgeType.CONTAINS},
    (NodeType.COORDINATE_SYSTEM, NodeType.AXIS): {EdgeType.CONTAINS},
    (NodeType.COORDINATE_SYSTEM, NodeType.CURVE): {EdgeType.CONTAINS},
    (NodeType.COORDINATE_SYSTEM, NodeType.POINT): {EdgeType.CONTAINS},

    # Function relationships
    (NodeType.ASYMPTOTE, NodeType.FUNCTION): {EdgeType.ASYMPTOTE_OF},
    (NodeType.ASYMPTOTE, NodeType.CURVE): {EdgeType.ASYMPTOTE_OF},
    (NodeType.AXIS, NodeType.FUNCTION): {EdgeType.DOMAIN_OF, EdgeType.RANGE_OF},

    # Curve intersections
    (NodeType.CURVE, NodeType.CURVE): {EdgeType.INTERSECTS},
    (NodeType.CURVE, NodeType.LINE): {EdgeType.INTERSECTS},
    (NodeType.CIRCLE, NodeType.LINE): {EdgeType.INTERSECTS},
    (NodeType.CIRCLE, NodeType.CIRCLE): {EdgeType.INTERSECTS, EdgeType.CONTAINS, EdgeType.CONTAINED_BY},
}


# =============================================================================
# GraphValidator Class
# =============================================================================

class GraphValidator:
    """Validate semantic graph structure.

    Performs comprehensive validation:
    1. Reference integrity: All edge references point to existing nodes
    2. Duplicate detection: No duplicate edges
    3. Type compatibility: Edge types are valid for connected node types
    4. Connectivity analysis: Warn about fragmented or isolated components
    5. Confidence consistency: Flag unusual confidence patterns

    The validator supports strict mode which treats warnings as errors.

    Usage:
        validator = GraphValidator()
        result = validator.validate(graph)
        if not result.is_valid:
            for issue in result.issues:
                print(issue)

    Configuration:
        - strict_mode: If True, treat warnings as errors (default: False)
        - connectivity_warning_threshold: Warn if components exceed this (default: 3)
        - isolated_nodes_threshold: Warn if isolated nodes exceed this (default: 2)
    """

    def __init__(
        self,
        strict_mode: bool = False,
        connectivity_warning_threshold: int = 3,
        isolated_nodes_threshold: int = 2,
    ):
        """Initialize GraphValidator.

        Args:
            strict_mode: If True, treat warnings as errors. Useful for
                production pipelines requiring strict validation.
            connectivity_warning_threshold: Warn if number of connected
                components exceeds this value. More components suggest
                a fragmented graph that may need review.
            isolated_nodes_threshold: Warn if number of isolated nodes
                exceeds this value. Isolated nodes often indicate
                missing relationships.
        """
        self.strict_mode = strict_mode
        self.connectivity_warning_threshold = connectivity_warning_threshold
        self.isolated_nodes_threshold = isolated_nodes_threshold

    def validate(self, graph: SemanticGraph) -> ValidationResult:
        """Validate graph and return comprehensive result.

        Runs all validation checks and aggregates results into
        a ValidationResult object.

        Args:
            graph: SemanticGraph to validate

        Returns:
            ValidationResult with all issues found
        """
        issues: List[ValidationIssue] = []

        # Build node lookup
        node_map: Dict[str, SemanticNode] = {n.id: n for n in graph.nodes}

        # Run validation checks
        issues.extend(self._validate_edge_references(graph.edges, node_map))
        issues.extend(self._validate_no_duplicate_edges(graph.edges))
        issues.extend(self._validate_edge_types(graph.edges, node_map))
        issues.extend(self._validate_connectivity(graph, node_map))
        issues.extend(self._validate_confidence_consistency(graph))
        issues.extend(self._validate_node_properties(graph.nodes))

        # Count by severity
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        info_count = len([i for i in issues if i.severity == ValidationSeverity.INFO])

        # In strict mode, warnings count as errors for validity
        if self.strict_mode:
            is_valid = (error_count + warning_count) == 0
        else:
            is_valid = error_count == 0

        result = ValidationResult(
            is_valid=is_valid,
            issues=issues,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
        )

        # Log summary
        logger.info(str(result))

        return result

    def _validate_edge_references(
        self,
        edges: List[SemanticEdge],
        node_map: Dict[str, SemanticNode],
    ) -> List[ValidationIssue]:
        """Check all edge references point to existing nodes.

        Args:
            edges: List of edges to validate
            node_map: Mapping of node ID to SemanticNode

        Returns:
            List of validation issues for invalid references
        """
        issues = []

        for edge in edges:
            if edge.source_id not in node_map:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="INVALID_SOURCE_REF",
                    message=f"Edge references non-existent source node: {edge.source_id}",
                    element_id=edge.id,
                    element_type="edge",
                    details={"missing_node_id": edge.source_id},
                ))

            if edge.target_id not in node_map:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="INVALID_TARGET_REF",
                    message=f"Edge references non-existent target node: {edge.target_id}",
                    element_id=edge.id,
                    element_type="edge",
                    details={"missing_node_id": edge.target_id},
                ))

            # Check for self-referential edges
            if edge.source_id == edge.target_id:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="SELF_REFERENTIAL_EDGE",
                    message=f"Edge references same node as source and target: {edge.source_id}",
                    element_id=edge.id,
                    element_type="edge",
                ))

        return issues

    def _validate_no_duplicate_edges(
        self,
        edges: List[SemanticEdge],
    ) -> List[ValidationIssue]:
        """Check for duplicate edges.

        Duplicates are identified by (source_id, target_id, edge_type) tuple.

        Args:
            edges: List of edges to check

        Returns:
            List of validation issues for duplicate edges
        """
        issues = []
        seen: Dict[tuple, str] = {}  # Key -> first edge ID with that key

        for edge in edges:
            key = (edge.source_id, edge.target_id, edge.edge_type)

            if key in seen:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="DUPLICATE_EDGE",
                    message=(
                        f"Duplicate edge: {edge.source_id} "
                        f"--{edge.edge_type.value}--> {edge.target_id}"
                    ),
                    element_id=edge.id,
                    element_type="edge",
                    details={
                        "original_edge_id": seen[key],
                        "edge_type": edge.edge_type.value,
                    },
                ))
            else:
                seen[key] = edge.id

        return issues

    def _validate_edge_types(
        self,
        edges: List[SemanticEdge],
        node_map: Dict[str, SemanticNode],
    ) -> List[ValidationIssue]:
        """Check edge types are valid for connected node types.

        Uses VALID_EDGE_RULES to determine which edge types are
        appropriate between different node type pairs.

        Args:
            edges: List of edges to validate
            node_map: Mapping of node ID to SemanticNode

        Returns:
            List of validation issues for suspicious edge types
        """
        issues = []

        for edge in edges:
            source = node_map.get(edge.source_id)
            target = node_map.get(edge.target_id)

            if not source or not target:
                # Already reported as INVALID_*_REF
                continue

            # Look up valid edge types for this node pair
            key = (source.node_type, target.node_type)
            valid_types = VALID_EDGE_RULES.get(key, set())

            # Also check reverse key for bidirectional relationships
            reverse_key = (target.node_type, source.node_type)
            valid_types = valid_types.union(VALID_EDGE_RULES.get(reverse_key, set()))

            # If no rules defined for this pair, it's suspicious but allowed
            if not valid_types:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    code="UNKNOWN_NODE_PAIR",
                    message=(
                        f"No validation rules for node pair: "
                        f"{source.node_type.value} -> {target.node_type.value}"
                    ),
                    element_id=edge.id,
                    element_type="edge",
                    details={
                        "source_type": source.node_type.value,
                        "target_type": target.node_type.value,
                        "edge_type": edge.edge_type.value,
                    },
                ))
            elif edge.edge_type not in valid_types:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="SUSPICIOUS_EDGE_TYPE",
                    message=(
                        f"Edge type {edge.edge_type.value} unusual between "
                        f"{source.node_type.value} and {target.node_type.value}"
                    ),
                    element_id=edge.id,
                    element_type="edge",
                    details={
                        "source_type": source.node_type.value,
                        "target_type": target.node_type.value,
                        "edge_type": edge.edge_type.value,
                        "valid_types": [t.value for t in valid_types],
                    },
                ))

        return issues

    def _validate_connectivity(
        self,
        graph: SemanticGraph,
        node_map: Dict[str, SemanticNode],
    ) -> List[ValidationIssue]:
        """Check graph connectivity for fragmentation issues.

        Args:
            graph: SemanticGraph to analyze
            node_map: Mapping of node ID to SemanticNode

        Returns:
            List of connectivity-related validation issues
        """
        issues = []

        # Use pre-computed statistics from graph
        isolated_count = graph.statistics.isolated_nodes
        component_count = graph.statistics.connected_components

        if isolated_count > self.isolated_nodes_threshold:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="MANY_ISOLATED_NODES",
                message=(
                    f"{isolated_count} isolated node(s) with no connections "
                    f"(threshold: {self.isolated_nodes_threshold})"
                ),
                details={
                    "isolated_count": isolated_count,
                    "threshold": self.isolated_nodes_threshold,
                },
            ))
        elif isolated_count > 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                code="ISOLATED_NODES",
                message=f"{isolated_count} isolated node(s) with no connections",
                details={"isolated_count": isolated_count},
            ))

        if component_count > self.connectivity_warning_threshold:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="FRAGMENTED_GRAPH",
                message=(
                    f"Graph has {component_count} disconnected components "
                    f"(threshold: {self.connectivity_warning_threshold})"
                ),
                details={
                    "component_count": component_count,
                    "threshold": self.connectivity_warning_threshold,
                },
            ))
        elif component_count > 1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                code="MULTIPLE_COMPONENTS",
                message=f"Graph has {component_count} disconnected components",
                details={"component_count": component_count},
            ))

        return issues

    def _validate_confidence_consistency(
        self,
        graph: SemanticGraph,
    ) -> List[ValidationIssue]:
        """Check for unusual confidence patterns.

        Args:
            graph: SemanticGraph to analyze

        Returns:
            List of confidence-related validation issues
        """
        issues = []

        # Check for very low overall confidence
        if graph.overall_confidence < 0.3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="LOW_OVERALL_CONFIDENCE",
                message=(
                    f"Overall graph confidence is very low: "
                    f"{graph.overall_confidence:.2f}"
                ),
                details={"overall_confidence": graph.overall_confidence},
            ))

        # Check for high variance in node confidences
        if graph.nodes:
            confidences = [n.confidence.value for n in graph.nodes]
            if len(confidences) > 2:
                avg = sum(confidences) / len(confidences)
                variance = sum((c - avg) ** 2 for c in confidences) / len(confidences)

                if variance > 0.1:  # High variance threshold
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        code="HIGH_CONFIDENCE_VARIANCE",
                        message=(
                            f"High variance in node confidences "
                            f"(variance: {variance:.3f})"
                        ),
                        details={
                            "variance": variance,
                            "min_confidence": min(confidences),
                            "max_confidence": max(confidences),
                            "avg_confidence": avg,
                        },
                    ))

        # Check for many nodes below threshold
        below_threshold_ratio = (
            graph.statistics.nodes_below_threshold / graph.statistics.total_nodes
            if graph.statistics.total_nodes > 0 else 0
        )

        if below_threshold_ratio > 0.5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="MANY_BELOW_THRESHOLD",
                message=(
                    f"{graph.statistics.nodes_below_threshold} of "
                    f"{graph.statistics.total_nodes} nodes below confidence threshold "
                    f"({below_threshold_ratio:.0%})"
                ),
                details={
                    "below_threshold": graph.statistics.nodes_below_threshold,
                    "total_nodes": graph.statistics.total_nodes,
                    "ratio": below_threshold_ratio,
                },
            ))

        return issues

    def _validate_node_properties(
        self,
        nodes: List[SemanticNode],
    ) -> List[ValidationIssue]:
        """Validate node-specific properties.

        Checks that nodes have appropriate properties for their type.

        Args:
            nodes: List of nodes to validate

        Returns:
            List of property-related validation issues
        """
        issues = []

        for node in nodes:
            # Check for empty labels
            if not node.label or node.label.strip() == "":
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="EMPTY_NODE_LABEL",
                    message=f"Node has empty label",
                    element_id=node.id,
                    element_type="node",
                ))

            # Type-specific property checks
            if node.node_type == NodeType.POINT:
                # Points should ideally have coordinates
                if not node.properties.coordinates:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        code="POINT_WITHOUT_COORDS",
                        message=f"Point node '{node.label}' has no coordinates",
                        element_id=node.id,
                        element_type="node",
                    ))

            elif node.node_type in (NodeType.LINE, NodeType.CURVE):
                # Lines/curves should have equation
                if not node.properties.equation and not node.properties.latex:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        code="CURVE_WITHOUT_EQUATION",
                        message=f"{node.node_type.value} node '{node.label}' has no equation",
                        element_id=node.id,
                        element_type="node",
                    ))

            elif node.node_type == NodeType.ANGLE:
                # Angles should have measure
                if node.properties.measure is None:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        code="ANGLE_WITHOUT_MEASURE",
                        message=f"Angle node '{node.label}' has no measure",
                        element_id=node.id,
                        element_type="node",
                    ))

        return issues

    def has_errors(self, result: ValidationResult) -> bool:
        """Check if validation result has any errors.

        Args:
            result: ValidationResult to check

        Returns:
            True if any ERROR-level issues exist
        """
        return result.error_count > 0

    def get_errors_only(self, result: ValidationResult) -> List[ValidationIssue]:
        """Filter validation result to only ERROR-level issues.

        Args:
            result: ValidationResult to filter

        Returns:
            List of ERROR-level issues only
        """
        return [i for i in result.issues if i.severity == ValidationSeverity.ERROR]


# =============================================================================
# Factory Function
# =============================================================================

def create_graph_validator(
    strict: bool = False,
    component_threshold: int = 3,
    isolated_threshold: int = 2,
) -> GraphValidator:
    """Factory function to create GraphValidator with custom config.

    Args:
        strict: If True, treat warnings as errors
        component_threshold: Warn if components exceed this
        isolated_threshold: Warn if isolated nodes exceed this

    Returns:
        Configured GraphValidator instance
    """
    return GraphValidator(
        strict_mode=strict,
        connectivity_warning_threshold=component_threshold,
        isolated_nodes_threshold=isolated_threshold,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Main class
    "GraphValidator",
    "create_graph_validator",
    # Types
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    # Constants
    "VALID_EDGE_RULES",
]
