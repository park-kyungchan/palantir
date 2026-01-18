"""
EdgeInferrer for SemanticGraphBuilder (Stage E).

Infers SemanticEdges between nodes based on:
1. Spatial relationships (bbox overlap/proximity)
2. Label relationships (text near visual elements)
3. Mathematical relationships (equations, functions, points)

Module Version: 1.0.0
"""

import logging
import math
import re
import uuid
from typing import Dict, List, Optional, Set, Tuple

from ..schemas.semantic_graph import (
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
)
from ..schemas.common import BBox, Confidence

logger = logging.getLogger(__name__)


# =============================================================================
# Edge Relationship Constants
# =============================================================================

# Node type pairs that commonly have label relationships
LABEL_TARGET_TYPES: Set[NodeType] = {
    NodeType.POINT,
    NodeType.LINE,
    NodeType.LINE_SEGMENT,
    NodeType.CURVE,
    NodeType.CIRCLE,
    NodeType.POLYGON,
    NodeType.ANGLE,
    NodeType.AXIS,
    NodeType.INTERCEPT,
    NodeType.REGION,
}

# Node types that can be graph representations of equations
GRAPHABLE_TYPES: Set[NodeType] = {
    NodeType.CURVE,
    NodeType.LINE,
    NodeType.LINE_SEGMENT,
    NodeType.CIRCLE,
}

# Node types that can lie on curves/lines
POINT_LIKE_TYPES: Set[NodeType] = {
    NodeType.POINT,
    NodeType.INTERCEPT,
}

# Node types that are curves/lines
CURVE_LIKE_TYPES: Set[NodeType] = {
    NodeType.LINE,
    NodeType.LINE_SEGMENT,
    NodeType.CURVE,
    NodeType.CIRCLE,
    NodeType.POLYGON,
    NodeType.AXIS,
}


# =============================================================================
# EdgeInferrer Class
# =============================================================================

class EdgeInferrer:
    """Infer edges between SemanticNodes.

    Analyzes nodes to discover relationships:
    - Spatial: Based on bbox geometry (overlap, containment, proximity)
    - Label: Based on label nodes near visual elements
    - Mathematical: Based on semantic content (equations, functions)

    The inferrer processes nodes in multiple passes:
    1. Spatial edge inference from bbox geometry
    2. Label edge inference from label/annotation proximity
    3. Mathematical edge inference from semantic content matching

    Usage:
        inferrer = EdgeInferrer()
        edges = inferrer.infer(nodes)

    Configuration:
        - spatial_overlap_threshold: Minimum IoU for INTERSECTS edge (default: 0.1)
        - proximity_threshold_px: Maximum distance for ADJACENT_TO edge (default: 50.0)
        - default_edge_threshold: Default confidence threshold for edges (default: 0.55)
    """

    def __init__(
        self,
        spatial_overlap_threshold: float = 0.1,
        proximity_threshold_px: float = 50.0,
        default_edge_threshold: float = 0.55,
    ):
        """Initialize EdgeInferrer.

        Args:
            spatial_overlap_threshold: Minimum IoU for INTERSECTS edge.
                Higher values require more overlap. Range: 0.0-1.0
            proximity_threshold_px: Maximum distance in pixels for ADJACENT_TO edge.
                Lower values require closer proximity.
            default_edge_threshold: Default confidence threshold for edges.
                Edges below this threshold are marked for review.
        """
        self.spatial_overlap_threshold = spatial_overlap_threshold
        self.proximity_threshold_px = proximity_threshold_px
        self.default_edge_threshold = default_edge_threshold

        # Internal indexes (populated during inference)
        self._node_index: Dict[str, SemanticNode] = {}
        self._type_index: Dict[NodeType, List[SemanticNode]] = {}

        # Statistics tracking
        self._stats: Dict[str, int] = {
            "total_edges": 0,
            "spatial_edges": 0,
            "label_edges": 0,
            "mathematical_edges": 0,
            "above_threshold": 0,
            "below_threshold": 0,
        }

    @property
    def stats(self) -> Dict[str, int]:
        """Return inference statistics."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset inference statistics."""
        for key in self._stats:
            self._stats[key] = 0

    def infer(self, nodes: List[SemanticNode]) -> List[SemanticEdge]:
        """Infer all edges from nodes.

        Processes nodes through three inference passes:
        1. Spatial edges from bbox geometry
        2. Label edges from proximity to visual elements
        3. Mathematical edges from semantic content

        Args:
            nodes: List of SemanticNodes from NodeExtractor

        Returns:
            List of inferred SemanticEdges
        """
        self.reset_stats()
        edges: List[SemanticEdge] = []

        if not nodes:
            logger.warning("No nodes provided for edge inference")
            return edges

        # Build lookup structures
        self._build_indexes(nodes)

        # Infer different edge types
        spatial_edges = self._infer_spatial_edges(nodes)
        edges.extend(spatial_edges)
        self._stats["spatial_edges"] = len(spatial_edges)

        label_edges = self._infer_label_edges(nodes)
        edges.extend(label_edges)
        self._stats["label_edges"] = len(label_edges)

        math_edges = self._infer_mathematical_edges(nodes)
        edges.extend(math_edges)
        self._stats["mathematical_edges"] = len(math_edges)

        # Deduplicate
        edges = self._deduplicate_edges(edges)
        self._stats["total_edges"] = len(edges)

        # Count threshold statistics
        self._stats["above_threshold"] = len(
            [e for e in edges if e.threshold_passed]
        )
        self._stats["below_threshold"] = len(
            [e for e in edges if not e.threshold_passed]
        )

        logger.info(
            f"Inferred {len(edges)} edges from {len(nodes)} nodes: "
            f"{self._stats['spatial_edges']} spatial, "
            f"{self._stats['label_edges']} label, "
            f"{self._stats['mathematical_edges']} mathematical "
            f"({self._stats['above_threshold']} above threshold)"
        )

        return edges

    # =========================================================================
    # Index Building
    # =========================================================================

    def _build_indexes(self, nodes: List[SemanticNode]) -> None:
        """Build lookup indexes for efficient edge inference.

        Creates:
        - node_index: ID -> Node mapping
        - type_index: NodeType -> List[Node] mapping

        Args:
            nodes: List of nodes to index
        """
        self._node_index = {}
        self._type_index = {}

        for node in nodes:
            # ID index
            self._node_index[node.id] = node

            # Type index
            if node.node_type not in self._type_index:
                self._type_index[node.node_type] = []
            self._type_index[node.node_type].append(node)

    def _get_nodes_by_type(self, node_type: NodeType) -> List[SemanticNode]:
        """Get all nodes of a specific type.

        Args:
            node_type: NodeType to filter by

        Returns:
            List of nodes with matching type
        """
        return self._type_index.get(node_type, [])

    def _get_nodes_by_types(self, node_types: Set[NodeType]) -> List[SemanticNode]:
        """Get all nodes matching any of the specified types.

        Args:
            node_types: Set of NodeTypes to filter by

        Returns:
            List of nodes matching any type
        """
        result = []
        for node_type in node_types:
            result.extend(self._type_index.get(node_type, []))
        return result

    # =========================================================================
    # Spatial Edge Inference
    # =========================================================================

    def _infer_spatial_edges(self, nodes: List[SemanticNode]) -> List[SemanticEdge]:
        """Infer spatial relationships from bbox geometry.

        Checks every pair of nodes for:
        1. Containment: One bbox fully contains another
        2. Intersection: Bboxes overlap with IoU > threshold
        3. Adjacency: Bboxes are within proximity threshold

        Args:
            nodes: List of all nodes

        Returns:
            List of spatial edges
        """
        edges: List[SemanticEdge] = []

        # Only consider nodes with bboxes
        nodes_with_bbox = [n for n in nodes if n.bbox is not None]

        for i, node_a in enumerate(nodes_with_bbox):
            for node_b in nodes_with_bbox[i + 1:]:
                # Skip self-comparison (shouldn't happen but safety check)
                if node_a.id == node_b.id:
                    continue

                # Check containment (order matters)
                if self._bbox_contains(node_a.bbox, node_b.bbox):
                    edges.append(self._create_edge(
                        source_id=node_a.id,
                        target_id=node_b.id,
                        edge_type=EdgeType.CONTAINS,
                        confidence=0.80,
                        description=f"{node_a.label} contains {node_b.label}",
                    ))
                    continue  # Don't add other spatial edges if contained

                elif self._bbox_contains(node_b.bbox, node_a.bbox):
                    edges.append(self._create_edge(
                        source_id=node_b.id,
                        target_id=node_a.id,
                        edge_type=EdgeType.CONTAINS,
                        confidence=0.80,
                        description=f"{node_b.label} contains {node_a.label}",
                    ))
                    continue

                # Check intersection
                iou = self._bbox_overlap_iou(node_a.bbox, node_b.bbox)
                if iou > self.spatial_overlap_threshold:
                    confidence = min(0.70 + (iou * 0.2), 0.90)
                    edges.append(self._create_edge(
                        source_id=node_a.id,
                        target_id=node_b.id,
                        edge_type=EdgeType.INTERSECTS,
                        confidence=confidence,
                        bidirectional=True,
                        description=f"IoU: {iou:.3f}",
                    ))
                    continue

                # Check adjacency
                distance = self._bbox_distance(node_a.bbox, node_b.bbox)
                if distance < self.proximity_threshold_px:
                    confidence = self._proximity_to_confidence(distance)
                    edges.append(self._create_edge(
                        source_id=node_a.id,
                        target_id=node_b.id,
                        edge_type=EdgeType.ADJACENT_TO,
                        confidence=confidence,
                        bidirectional=True,
                        description=f"Distance: {distance:.1f}px",
                    ))

        return edges

    # =========================================================================
    # Label Edge Inference
    # =========================================================================

    def _infer_label_edges(self, nodes: List[SemanticNode]) -> List[SemanticEdge]:
        """Infer labeling relationships.

        Finds label/annotation nodes and connects them to nearby
        visual elements they likely describe.

        Args:
            nodes: List of all nodes

        Returns:
            List of label edges
        """
        edges: List[SemanticEdge] = []

        # Get label nodes
        label_types = {NodeType.LABEL, NodeType.ANNOTATION}
        label_nodes = self._get_nodes_by_types(label_types)

        # Get potential targets (visual elements)
        visual_nodes = self._get_nodes_by_types(LABEL_TARGET_TYPES)

        for label in label_nodes:
            if not label.bbox:
                continue

            # Find nearest visual node
            nearest, distance = self._find_nearest_node(label, visual_nodes)

            if nearest and distance < self.proximity_threshold_px:
                confidence = self._proximity_to_confidence(distance)

                # LABELS edge: label -> visual element
                edges.append(self._create_edge(
                    source_id=label.id,
                    target_id=nearest.id,
                    edge_type=EdgeType.LABELS,
                    confidence=confidence,
                    description=f"'{label.label}' labels {nearest.node_type.value}",
                ))

                # Also create reverse LABELED_BY edge
                edges.append(self._create_edge(
                    source_id=nearest.id,
                    target_id=label.id,
                    edge_type=EdgeType.LABELED_BY,
                    confidence=confidence,
                    description=f"{nearest.node_type.value} labeled by '{label.label}'",
                ))

        return edges

    # =========================================================================
    # Mathematical Edge Inference
    # =========================================================================

    def _infer_mathematical_edges(self, nodes: List[SemanticNode]) -> List[SemanticEdge]:
        """Infer mathematical relationships.

        Discovers relationships between:
        - Equations and their graph representations
        - Points and curves they lie on
        - Functions and their domains/ranges
        - Parallel/perpendicular lines

        Args:
            nodes: List of all nodes

        Returns:
            List of mathematical edges
        """
        edges: List[SemanticEdge] = []

        # Equation -> Curve (GRAPH_OF)
        edges.extend(self._infer_graph_of_edges())

        # Point -> Curve (LIES_ON)
        edges.extend(self._infer_lies_on_edges())

        # Function relationships
        edges.extend(self._infer_function_edges())

        # Parallel/Perpendicular lines
        edges.extend(self._infer_geometric_edges())

        return edges

    def _infer_graph_of_edges(self) -> List[SemanticEdge]:
        """Infer GRAPH_OF edges between equations and curves.

        Returns:
            List of GRAPH_OF edges
        """
        edges: List[SemanticEdge] = []

        equation_types = {NodeType.EQUATION, NodeType.FUNCTION}
        equations = self._get_nodes_by_types(equation_types)
        curves = self._get_nodes_by_types(GRAPHABLE_TYPES)

        for eq in equations:
            for curve in curves:
                confidence = self._equations_match(eq, curve)
                if confidence > 0.5:
                    edges.append(self._create_edge(
                        source_id=eq.id,
                        target_id=curve.id,
                        edge_type=EdgeType.GRAPH_OF,
                        confidence=confidence,
                        description=f"Equation '{eq.label}' graphs to {curve.node_type.value}",
                    ))

        return edges

    def _infer_lies_on_edges(self) -> List[SemanticEdge]:
        """Infer LIES_ON edges between points and curves.

        Returns:
            List of LIES_ON edges
        """
        edges: List[SemanticEdge] = []

        points = self._get_nodes_by_types(POINT_LIKE_TYPES)
        curves = self._get_nodes_by_types(CURVE_LIKE_TYPES)

        for point in points:
            for curve in curves:
                confidence = self._point_on_curve(point, curve)
                if confidence > 0.5:
                    edges.append(self._create_edge(
                        source_id=point.id,
                        target_id=curve.id,
                        edge_type=EdgeType.LIES_ON,
                        confidence=confidence,
                        description=f"Point '{point.label}' lies on {curve.node_type.value}",
                    ))

                    # Add reverse edge
                    edges.append(self._create_edge(
                        source_id=curve.id,
                        target_id=point.id,
                        edge_type=EdgeType.PASSES_THROUGH,
                        confidence=confidence,
                        description=f"{curve.node_type.value} passes through '{point.label}'",
                    ))

        return edges

    def _infer_function_edges(self) -> List[SemanticEdge]:
        """Infer function-related edges (DOMAIN_OF, ASYMPTOTE_OF).

        Returns:
            List of function edges
        """
        edges: List[SemanticEdge] = []

        functions = self._get_nodes_by_type(NodeType.FUNCTION)
        asymptotes = self._get_nodes_by_type(NodeType.ASYMPTOTE)
        axes = self._get_nodes_by_type(NodeType.AXIS)

        # Asymptote -> Function relationships
        for asymptote in asymptotes:
            for func in functions:
                if self._is_asymptote_of(asymptote, func):
                    edges.append(self._create_edge(
                        source_id=asymptote.id,
                        target_id=func.id,
                        edge_type=EdgeType.ASYMPTOTE_OF,
                        confidence=0.70,
                        description=f"Asymptote of function '{func.label}'",
                    ))

        # Axis as domain/range indicator
        for axis in axes:
            for func in functions:
                axis_type = self._get_axis_type(axis)
                if axis_type == "x":
                    edges.append(self._create_edge(
                        source_id=axis.id,
                        target_id=func.id,
                        edge_type=EdgeType.DOMAIN_OF,
                        confidence=0.60,
                        description="X-axis represents domain",
                    ))
                elif axis_type == "y":
                    edges.append(self._create_edge(
                        source_id=axis.id,
                        target_id=func.id,
                        edge_type=EdgeType.RANGE_OF,
                        confidence=0.60,
                        description="Y-axis represents range",
                    ))

        return edges

    def _infer_geometric_edges(self) -> List[SemanticEdge]:
        """Infer geometric relationship edges (PARALLEL_TO, PERPENDICULAR_TO).

        Returns:
            List of geometric edges
        """
        edges: List[SemanticEdge] = []

        line_types = {NodeType.LINE, NodeType.LINE_SEGMENT}
        lines = self._get_nodes_by_types(line_types)

        for i, line_a in enumerate(lines):
            for line_b in lines[i + 1:]:
                # Check parallel
                if self._are_parallel(line_a, line_b):
                    edges.append(self._create_edge(
                        source_id=line_a.id,
                        target_id=line_b.id,
                        edge_type=EdgeType.PARALLEL_TO,
                        confidence=0.75,
                        bidirectional=True,
                        description="Parallel lines",
                    ))

                # Check perpendicular
                elif self._are_perpendicular(line_a, line_b):
                    edges.append(self._create_edge(
                        source_id=line_a.id,
                        target_id=line_b.id,
                        edge_type=EdgeType.PERPENDICULAR_TO,
                        confidence=0.75,
                        bidirectional=True,
                        description="Perpendicular lines",
                    ))

        return edges

    # =========================================================================
    # Geometry Helpers
    # =========================================================================

    def _bbox_overlap_iou(self, a: BBox, b: BBox) -> float:
        """Calculate Intersection over Union of two bboxes.

        Args:
            a: First bounding box
            b: Second bounding box

        Returns:
            IoU score (0.0-1.0)
        """
        # Convert to xyxy format
        a_x1, a_y1 = a.x, a.y
        a_x2, a_y2 = a.x + a.width, a.y + a.height
        b_x1, b_y1 = b.x, b.y
        b_x2, b_y2 = b.x + b.width, b.y + b.height

        # Calculate intersection
        inter_x1 = max(a_x1, b_x1)
        inter_y1 = max(a_y1, b_y1)
        inter_x2 = min(a_x2, b_x2)
        inter_y2 = min(a_y2, b_y2)

        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)

        # Calculate union
        a_area = a.width * a.height
        b_area = b.width * b.height
        union_area = a_area + b_area - inter_area

        if union_area <= 0:
            return 0.0

        return inter_area / union_area

    def _bbox_contains(self, outer: BBox, inner: BBox) -> bool:
        """Check if outer bbox fully contains inner.

        Args:
            outer: Outer bounding box
            inner: Inner bounding box

        Returns:
            True if outer fully contains inner
        """
        outer_x2 = outer.x + outer.width
        outer_y2 = outer.y + outer.height
        inner_x2 = inner.x + inner.width
        inner_y2 = inner.y + inner.height

        return (
            outer.x <= inner.x and
            outer.y <= inner.y and
            outer_x2 >= inner_x2 and
            outer_y2 >= inner_y2
        )

    def _bbox_distance(self, a: BBox, b: BBox) -> float:
        """Calculate minimum distance between two bboxes.

        Returns 0 if bboxes overlap or touch.

        Args:
            a: First bounding box
            b: Second bounding box

        Returns:
            Minimum distance in pixels
        """
        a_x2 = a.x + a.width
        a_y2 = a.y + a.height
        b_x2 = b.x + b.width
        b_y2 = b.y + b.height

        # Calculate horizontal gap
        if a_x2 < b.x:
            dx = b.x - a_x2
        elif b_x2 < a.x:
            dx = a.x - b_x2
        else:
            dx = 0

        # Calculate vertical gap
        if a_y2 < b.y:
            dy = b.y - a_y2
        elif b_y2 < a.y:
            dy = a.y - b_y2
        else:
            dy = 0

        return math.sqrt(dx * dx + dy * dy)

    def _bbox_center(self, bbox: BBox) -> Tuple[float, float]:
        """Get center point of bbox.

        Args:
            bbox: Bounding box

        Returns:
            Tuple of (center_x, center_y)
        """
        return (bbox.x + bbox.width / 2, bbox.y + bbox.height / 2)

    def _find_nearest_node(
        self,
        source: SemanticNode,
        targets: List[SemanticNode],
    ) -> Tuple[Optional[SemanticNode], float]:
        """Find nearest target node to source.

        Uses center-to-center distance.

        Args:
            source: Source node
            targets: List of potential target nodes

        Returns:
            Tuple of (nearest_node, distance) or (None, inf) if no valid target
        """
        if not source.bbox or not targets:
            return None, float("inf")

        source_center = self._bbox_center(source.bbox)
        nearest: Optional[SemanticNode] = None
        min_distance = float("inf")

        for target in targets:
            if not target.bbox or target.id == source.id:
                continue

            target_center = self._bbox_center(target.bbox)
            distance = math.sqrt(
                (target_center[0] - source_center[0]) ** 2 +
                (target_center[1] - source_center[1]) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                nearest = target

        return nearest, min_distance

    def _proximity_to_confidence(self, distance: float) -> float:
        """Convert proximity distance to confidence score.

        Closer distance = higher confidence.

        Args:
            distance: Distance in pixels

        Returns:
            Confidence score (0.5-0.95)
        """
        if distance <= 0:
            return 0.95

        # Exponential decay: closer = higher confidence
        # At threshold distance, confidence is 0.5
        # At 0 distance, confidence is 0.95
        ratio = distance / self.proximity_threshold_px
        confidence = 0.95 * math.exp(-ratio * 1.5)

        # Clamp to reasonable range
        return max(0.5, min(0.95, confidence))

    # =========================================================================
    # Mathematical Relationship Helpers
    # =========================================================================

    def _equations_match(self, eq: SemanticNode, curve: SemanticNode) -> float:
        """Check if equation matches a curve representation.

        Uses multiple heuristics:
        1. LaTeX similarity
        2. Slope matching (if available)
        3. Spatial proximity

        Args:
            eq: Equation node
            curve: Curve node

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.0

        # Check if equation's latex appears in curve's properties
        eq_latex = eq.properties.latex if eq.properties else None
        curve_eq = curve.properties.equation if curve.properties else None

        if eq_latex and curve_eq:
            # Normalize and compare
            eq_norm = self._normalize_latex(eq_latex)
            curve_norm = self._normalize_latex(curve_eq)

            if eq_norm == curve_norm:
                confidence = 0.90
            elif eq_norm in curve_norm or curve_norm in eq_norm:
                confidence = 0.75

        # Check slope matching for linear equations
        if eq.properties and curve.properties:
            eq_slope = eq.properties.slope
            curve_slope = curve.properties.slope

            if eq_slope is not None and curve_slope is not None:
                if abs(eq_slope - curve_slope) < 0.01:
                    confidence = max(confidence, 0.85)
                elif abs(eq_slope - curve_slope) < 0.1:
                    confidence = max(confidence, 0.70)

        # Spatial proximity boost
        if eq.bbox and curve.bbox:
            distance = self._bbox_distance(eq.bbox, curve.bbox)
            if distance < self.proximity_threshold_px:
                proximity_boost = 0.1 * (1 - distance / self.proximity_threshold_px)
                confidence = min(0.95, confidence + proximity_boost)

        return confidence

    def _point_on_curve(self, point: SemanticNode, curve: SemanticNode) -> float:
        """Check if point lies on curve.

        Uses:
        1. Spatial proximity of point bbox to curve bbox
        2. Coordinate matching if available

        Args:
            point: Point node
            curve: Curve node

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.0

        # Spatial check: point bbox should be near or inside curve bbox
        if point.bbox and curve.bbox:
            # Check if point center is on curve edge
            point_center = self._bbox_center(point.bbox)

            # Check distance to curve bbox edge
            distance = self._point_to_bbox_edge_distance(point_center, curve.bbox)

            if distance < 10:  # Very close to curve
                confidence = 0.80
            elif distance < 25:
                confidence = 0.65
            elif distance < self.proximity_threshold_px:
                confidence = 0.55

        # Coordinate-based check if available
        if point.properties and point.properties.coordinates:
            coords = point.properties.coordinates
            point_x = coords.get("x", 0)
            point_y = coords.get("y", 0)

            # If curve has equation, try to evaluate
            if curve.properties and curve.properties.equation:
                on_curve = self._evaluate_point_on_equation(
                    point_x, point_y, curve.properties.equation
                )
                if on_curve:
                    confidence = max(confidence, 0.85)

        return confidence

    def _point_to_bbox_edge_distance(
        self,
        point: Tuple[float, float],
        bbox: BBox,
    ) -> float:
        """Calculate distance from point to nearest bbox edge.

        Args:
            point: (x, y) coordinates
            bbox: Bounding box

        Returns:
            Distance to nearest edge
        """
        px, py = point
        x1, y1 = bbox.x, bbox.y
        x2, y2 = bbox.x + bbox.width, bbox.y + bbox.height

        # Distances to each edge
        distances = []

        # Left edge
        if y1 <= py <= y2:
            distances.append(abs(px - x1))

        # Right edge
        if y1 <= py <= y2:
            distances.append(abs(px - x2))

        # Top edge
        if x1 <= px <= x2:
            distances.append(abs(py - y1))

        # Bottom edge
        if x1 <= px <= x2:
            distances.append(abs(py - y2))

        # If point is outside bbox, calculate corner distances
        if not distances:
            corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
            for cx, cy in corners:
                distances.append(math.sqrt((px - cx) ** 2 + (py - cy) ** 2))

        return min(distances) if distances else float("inf")

    def _evaluate_point_on_equation(
        self,
        x: float,
        y: float,
        equation: str,
    ) -> bool:
        """Check if point satisfies equation.

        Handles simple equation forms:
        - y = mx + b (linear)
        - y = x^2 (parabola)

        Args:
            x: X coordinate
            y: Y coordinate
            equation: Equation string

        Returns:
            True if point approximately satisfies equation
        """
        try:
            # Try linear: y = mx + b
            linear_pattern = r"y\s*=\s*(-?\d*\.?\d*)\s*x\s*([+-]\s*\d+\.?\d*)?"
            match = re.search(linear_pattern, equation, re.IGNORECASE)
            if match:
                slope_str = match.group(1) or "1"
                slope = float(slope_str) if slope_str else 1.0
                intercept = 0.0
                if match.group(2):
                    intercept_str = match.group(2).replace(" ", "")
                    intercept = float(intercept_str)

                expected_y = slope * x + intercept
                return abs(y - expected_y) < 0.5

            # Try parabola: y = x^2 (or variants)
            if "x^2" in equation or "x²" in equation:
                # Simple check
                expected_y = x * x
                return abs(y - expected_y) < 0.5

        except (ValueError, AttributeError):
            pass

        return False

    def _is_asymptote_of(self, asymptote: SemanticNode, func: SemanticNode) -> bool:
        """Check if asymptote node is related to function.

        Args:
            asymptote: Asymptote node
            func: Function node

        Returns:
            True if asymptote appears to be for the function
        """
        # Check spatial proximity
        if asymptote.bbox and func.bbox:
            distance = self._bbox_distance(asymptote.bbox, func.bbox)
            return distance < self.proximity_threshold_px * 2

        return False

    def _get_axis_type(self, axis: SemanticNode) -> Optional[str]:
        """Determine if axis is x-axis or y-axis.

        Args:
            axis: Axis node

        Returns:
            "x", "y", or None
        """
        label = axis.label.lower() if axis.label else ""

        if "x" in label or "horizontal" in label:
            return "x"
        elif "y" in label or "vertical" in label:
            return "y"

        # Check bbox orientation
        if axis.bbox:
            if axis.bbox.width > axis.bbox.height * 2:
                return "x"  # Horizontal
            elif axis.bbox.height > axis.bbox.width * 2:
                return "y"  # Vertical

        return None

    def _are_parallel(self, line_a: SemanticNode, line_b: SemanticNode) -> bool:
        """Check if two lines are parallel.

        Uses slope comparison if available.

        Args:
            line_a: First line node
            line_b: Second line node

        Returns:
            True if lines appear parallel
        """
        slope_a = line_a.properties.slope if line_a.properties else None
        slope_b = line_b.properties.slope if line_b.properties else None

        if slope_a is not None and slope_b is not None:
            # Slopes are equal (with tolerance)
            return abs(slope_a - slope_b) < 0.01

        return False

    def _are_perpendicular(self, line_a: SemanticNode, line_b: SemanticNode) -> bool:
        """Check if two lines are perpendicular.

        Uses slope comparison if available.

        Args:
            line_a: First line node
            line_b: Second line node

        Returns:
            True if lines appear perpendicular
        """
        slope_a = line_a.properties.slope if line_a.properties else None
        slope_b = line_b.properties.slope if line_b.properties else None

        if slope_a is not None and slope_b is not None:
            # Check if slopes are negative reciprocals
            if slope_a == 0:
                return slope_b is None or abs(slope_b) > 100  # Vertical
            if slope_b == 0:
                return slope_a is None or abs(slope_a) > 100  # Vertical

            # m1 * m2 = -1 for perpendicular lines
            product = slope_a * slope_b
            return abs(product + 1) < 0.01

        return False

    def _normalize_latex(self, latex: str) -> str:
        """Normalize LaTeX string for comparison.

        Args:
            latex: Raw LaTeX string

        Returns:
            Normalized string
        """
        if not latex:
            return ""

        # Remove whitespace
        normalized = re.sub(r"\s+", "", latex)
        # Remove common delimiters
        normalized = normalized.replace("$", "").replace("\\(", "").replace("\\)", "")
        # Lowercase
        normalized = normalized.lower()

        return normalized

    # =========================================================================
    # Edge Creation and Deduplication
    # =========================================================================

    def _create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        confidence: float,
        bidirectional: bool = False,
        description: Optional[str] = None,
    ) -> SemanticEdge:
        """Create a SemanticEdge with computed fields.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of edge relationship
            confidence: Confidence score (0.0-1.0)
            bidirectional: Whether edge is bidirectional
            description: Optional description

        Returns:
            Configured SemanticEdge
        """
        return SemanticEdge(
            id=f"edge_{uuid.uuid4().hex[:8]}",
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            confidence=Confidence(
                value=round(confidence, 4),
                source="edge_inference",
                element_type=edge_type.value,
            ),
            bidirectional=bidirectional,
            applied_threshold=self.default_edge_threshold,
            description=description,
        )

    def _deduplicate_edges(self, edges: List[SemanticEdge]) -> List[SemanticEdge]:
        """Remove duplicate edges, keeping highest confidence.

        Duplicates are identified by (source_id, target_id, edge_type) tuple.
        For bidirectional edges, also checks reversed direction.

        Args:
            edges: List of edges that may contain duplicates

        Returns:
            Deduplicated list of edges
        """
        # Key: (source_id, target_id, edge_type) -> Edge
        seen: Dict[Tuple[str, str, EdgeType], SemanticEdge] = {}

        for edge in edges:
            key = (edge.source_id, edge.target_id, edge.edge_type)

            # For bidirectional edges, also check reverse
            reverse_key = (edge.target_id, edge.source_id, edge.edge_type)

            # Check if we've seen this edge
            existing = seen.get(key) or (seen.get(reverse_key) if edge.bidirectional else None)

            if existing:
                # Keep higher confidence
                if edge.confidence.value > existing.confidence.value:
                    seen[key] = edge
            else:
                seen[key] = edge

        return list(seen.values())


# =============================================================================
# Factory Function
# =============================================================================

def create_edge_inferrer(
    overlap_threshold: float = 0.1,
    proximity_px: float = 50.0,
    edge_threshold: float = 0.55,
) -> EdgeInferrer:
    """Factory function to create EdgeInferrer with custom config.

    Args:
        overlap_threshold: Minimum IoU for INTERSECTS edge
        proximity_px: Maximum distance for ADJACENT_TO edge
        edge_threshold: Default confidence threshold for edges

    Returns:
        Configured EdgeInferrer instance
    """
    return EdgeInferrer(
        spatial_overlap_threshold=overlap_threshold,
        proximity_threshold_px=proximity_px,
        default_edge_threshold=edge_threshold,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "EdgeInferrer",
    "create_edge_inferrer",
    "LABEL_TARGET_TYPES",
    "GRAPHABLE_TYPES",
    "POINT_LIKE_TYPES",
    "CURVE_LIKE_TYPES",
]
