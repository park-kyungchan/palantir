"""
ConfidencePropagator for SemanticGraphBuilder (Stage E).

Propagates and adjusts confidence scores across the graph:
- Node confidence from alignment sources
- Edge confidence based on endpoint nodes
- Overall graph confidence aggregation
- Graph-type-specific confidence adjustments

Module Version: 1.1.0
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..schemas.semantic_graph import (
    SemanticNode,
    SemanticEdge,
    SemanticGraph,
)
from ..schemas.common import Confidence

logger = logging.getLogger(__name__)


# =============================================================================
# Propagation Constants
# =============================================================================

# Default propagation parameters
DEFAULT_EDGE_CONFIDENCE_FACTOR = 0.9
DEFAULT_ISOLATED_NODE_PENALTY = 0.2
DEFAULT_MIN_CONFIDENCE = 0.1
DEFAULT_CONNECTIVITY_BOOST = 0.05


# =============================================================================
# ConfidencePropagator Class
# =============================================================================

class ConfidencePropagator:
    """Propagate confidence through semantic graph.

    Adjusts confidence values based on:
    - Source element confidences (from Stage C/D)
    - Edge endpoint confidence (min of source/target)
    - Connectivity analysis (isolated nodes penalized)
    - Graph-level aggregation

    The propagator implements a multi-pass confidence adjustment:
    1. Edge propagation: Adjust edge confidence based on endpoint nodes
    2. Isolation penalty: Reduce confidence of nodes with no connections
    3. Connectivity boost: Slightly boost well-connected nodes
    4. Overall computation: Aggregate to graph-level confidence

    Usage:
        propagator = ConfidencePropagator()
        propagator.propagate(graph)  # Mutates graph in place

    Configuration:
        - edge_confidence_factor: Factor applied to edge confidence (default: 0.9)
        - isolated_node_penalty: Penalty for nodes with no edges (default: 0.2)
        - min_confidence: Minimum confidence floor (default: 0.1)
        - connectivity_boost: Bonus for well-connected nodes (default: 0.05)
    """

    def __init__(
        self,
        edge_confidence_factor: float = DEFAULT_EDGE_CONFIDENCE_FACTOR,
        isolated_node_penalty: float = DEFAULT_ISOLATED_NODE_PENALTY,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        connectivity_boost: float = DEFAULT_CONNECTIVITY_BOOST,
    ):
        """Initialize ConfidencePropagator.

        Args:
            edge_confidence_factor: Factor applied to edge confidence based
                on endpoint node confidences. Lower values are more conservative.
                Range: 0.0-1.0 (default: 0.9)
            isolated_node_penalty: Confidence reduction for nodes with no
                connections. Higher values penalize isolation more.
                Range: 0.0-1.0 (default: 0.2)
            min_confidence: Minimum confidence value to prevent zero confidence.
                All confidences are clamped to this minimum.
                Range: 0.0-1.0 (default: 0.1)
            connectivity_boost: Small bonus for nodes with multiple connections.
                Applied per additional connection beyond the first.
                Range: 0.0-1.0 (default: 0.05)
        """
        self.edge_confidence_factor = edge_confidence_factor
        self.isolated_node_penalty = isolated_node_penalty
        self.min_confidence = min_confidence
        self.connectivity_boost = connectivity_boost

        # Statistics tracking
        self._stats: Dict[str, int] = {
            "nodes_processed": 0,
            "edges_processed": 0,
            "isolated_nodes": 0,
            "boosted_nodes": 0,
        }

    @property
    def stats(self) -> Dict[str, int]:
        """Return propagation statistics."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset propagation statistics."""
        for key in self._stats:
            self._stats[key] = 0

    def propagate(self, graph: SemanticGraph) -> None:
        """Propagate confidence through graph (mutates in place).

        Performs multi-pass confidence adjustment:
        1. Build node lookup for efficient access
        2. Propagate confidence to edges from endpoint nodes
        3. Penalize isolated nodes
        4. Boost well-connected nodes
        5. Compute overall graph confidence

        Args:
            graph: SemanticGraph to propagate confidence through.
                The graph is modified in place.
        """
        self.reset_stats()

        if not graph.nodes:
            logger.warning("No nodes in graph, skipping propagation")
            return

        # Build node lookup
        node_map: Dict[str, SemanticNode] = {n.id: n for n in graph.nodes}
        self._stats["nodes_processed"] = len(graph.nodes)
        self._stats["edges_processed"] = len(graph.edges)

        # Build connectivity map
        connectivity: Dict[str, Set[str]] = self._build_connectivity_map(graph)

        # Pass 1: Propagate to edges based on endpoint nodes
        self._propagate_to_edges(graph.edges, node_map)

        # Pass 2: Penalize isolated nodes
        self._penalize_isolated_nodes(graph.nodes, connectivity)

        # Pass 3: Boost well-connected nodes
        self._boost_connected_nodes(graph.nodes, connectivity)

        # Pass 4: Compute overall confidence
        self._compute_overall_confidence(graph)

        logger.info(
            f"Confidence propagation complete: "
            f"{self._stats['nodes_processed']} nodes, "
            f"{self._stats['edges_processed']} edges, "
            f"{self._stats['isolated_nodes']} isolated, "
            f"{self._stats['boosted_nodes']} boosted"
        )

    def _build_connectivity_map(self, graph: SemanticGraph) -> Dict[str, Set[str]]:
        """Build a map of node connectivity.

        Args:
            graph: SemanticGraph to analyze

        Returns:
            Dict mapping node IDs to sets of connected node IDs
        """
        connectivity: Dict[str, Set[str]] = {n.id: set() for n in graph.nodes}

        for edge in graph.edges:
            if edge.source_id in connectivity:
                connectivity[edge.source_id].add(edge.target_id)
            if edge.target_id in connectivity:
                connectivity[edge.target_id].add(edge.source_id)

        return connectivity

    def _propagate_to_edges(
        self,
        edges: List[SemanticEdge],
        node_map: Dict[str, SemanticNode],
    ) -> None:
        """Adjust edge confidence based on endpoint nodes.

        Edge confidence is adjusted by:
        edge_conf = edge_conf * min(source_conf, target_conf) * factor

        This ensures edges between low-confidence nodes have
        proportionally lower confidence.

        Args:
            edges: List of edges to adjust
            node_map: Mapping of node ID to SemanticNode
        """
        for edge in edges:
            source = node_map.get(edge.source_id)
            target = node_map.get(edge.target_id)

            if source and target:
                # Edge confidence = current * min(endpoint confidences) * factor
                endpoint_min = min(
                    source.confidence.value,
                    target.confidence.value
                )
                current_conf = edge.confidence.value
                adjusted = current_conf * endpoint_min * self.edge_confidence_factor

                # Clamp to minimum
                adjusted = max(self.min_confidence, adjusted)

                # Update edge confidence
                edge.confidence = Confidence(
                    value=round(adjusted, 4),
                    source="propagated_from_endpoints",
                    element_type=edge.edge_type.value,
                )

                # Update threshold check (model validator would handle this
                # but we update manually since we're mutating)
                if adjusted < edge.applied_threshold:
                    edge.threshold_passed = False
                    edge.review.review_required = True
            else:
                # Missing endpoint - heavily penalize
                adjusted = edge.confidence.value * 0.5
                edge.confidence = Confidence(
                    value=max(self.min_confidence, adjusted),
                    source="propagated_missing_endpoint",
                    element_type=edge.edge_type.value,
                )
                edge.threshold_passed = False
                edge.review.review_required = True

    def _penalize_isolated_nodes(
        self,
        nodes: List[SemanticNode],
        connectivity: Dict[str, Set[str]],
    ) -> None:
        """Apply penalty to nodes with no connections.

        Isolated nodes (no edges) get reduced confidence since
        they couldn't be validated through relationships.

        Args:
            nodes: List of nodes to check
            connectivity: Node connectivity map
        """
        for node in nodes:
            if node.id in connectivity and len(connectivity[node.id]) == 0:
                # Node is isolated
                self._stats["isolated_nodes"] += 1

                current_conf = node.confidence.value
                adjusted = current_conf * (1.0 - self.isolated_node_penalty)

                node.confidence = Confidence(
                    value=max(self.min_confidence, round(adjusted, 4)),
                    source="isolated_penalty_applied",
                    element_type=node.node_type.value,
                )

                # Update threshold check
                if adjusted < node.applied_threshold:
                    node.threshold_passed = False
                    node.review.review_required = True
                    if not node.review.review_reason:
                        node.review.review_reason = "Isolated node with reduced confidence"

    def _boost_connected_nodes(
        self,
        nodes: List[SemanticNode],
        connectivity: Dict[str, Set[str]],
    ) -> None:
        """Apply small boost to well-connected nodes.

        Nodes with multiple connections get slightly increased
        confidence as they've been validated through relationships.

        Args:
            nodes: List of nodes to check
            connectivity: Node connectivity map
        """
        for node in nodes:
            if node.id in connectivity:
                connection_count = len(connectivity[node.id])

                # Only boost nodes with 2+ connections
                if connection_count >= 2:
                    self._stats["boosted_nodes"] += 1

                    # Diminishing returns on boost
                    extra_connections = connection_count - 1
                    boost = min(
                        self.connectivity_boost * extra_connections,
                        0.15  # Cap total boost at 0.15
                    )

                    current_conf = node.confidence.value
                    adjusted = min(1.0, current_conf + boost)

                    node.confidence = Confidence(
                        value=round(adjusted, 4),
                        source="connectivity_boost_applied",
                        element_type=node.node_type.value,
                    )

    def _compute_overall_confidence(self, graph: SemanticGraph) -> None:
        """Compute graph-level overall confidence.

        Overall confidence is a weighted average:
        - Node confidences (weight: 0.6)
        - Edge confidences (weight: 0.4)

        The weighting prioritizes node confidence since nodes
        represent the primary semantic content.

        Args:
            graph: SemanticGraph to update
        """
        node_values = [n.confidence.value for n in graph.nodes]
        edge_values = [e.confidence.value for e in graph.edges]

        if not node_values and not edge_values:
            graph.overall_confidence = 0.0
            return

        # Weighted average: nodes 60%, edges 40%
        node_avg = sum(node_values) / len(node_values) if node_values else 0.0
        edge_avg = sum(edge_values) / len(edge_values) if edge_values else 0.0

        if node_values and edge_values:
            overall = (node_avg * 0.6) + (edge_avg * 0.4)
        elif node_values:
            overall = node_avg
        else:
            overall = edge_avg

        graph.overall_confidence = round(overall, 4)

    def propagate_from_alignment(
        self,
        graph: SemanticGraph,
        alignment_confidences: Dict[str, float],
    ) -> None:
        """Propagate confidence from Stage D alignment scores.

        Updates node confidence based on alignment report scores.
        Call this before the main propagate() method.

        Args:
            graph: SemanticGraph to update
            alignment_confidences: Mapping of source element IDs to
                their alignment confidence scores
        """
        for node in graph.nodes:
            # Check if any source element has alignment confidence
            source_confidences = []
            for source_id in node.source_element_ids:
                if source_id in alignment_confidences:
                    source_confidences.append(alignment_confidences[source_id])

            if source_confidences:
                # Use average of source confidences
                avg_source = sum(source_confidences) / len(source_confidences)

                # Blend with current confidence (60% alignment, 40% current)
                current = node.confidence.value
                blended = (avg_source * 0.6) + (current * 0.4)

                node.confidence = Confidence(
                    value=round(blended, 4),
                    source="alignment_propagated",
                    element_type=node.node_type.value,
                )


# =============================================================================
# Factory Function
# =============================================================================

def create_confidence_propagator(
    edge_factor: float = DEFAULT_EDGE_CONFIDENCE_FACTOR,
    isolation_penalty: float = DEFAULT_ISOLATED_NODE_PENALTY,
    min_conf: float = DEFAULT_MIN_CONFIDENCE,
    conn_boost: float = DEFAULT_CONNECTIVITY_BOOST,
) -> ConfidencePropagator:
    """Factory function to create ConfidencePropagator with custom config.

    Args:
        edge_factor: Factor applied to edge confidence from endpoints
        isolation_penalty: Penalty for isolated nodes
        min_conf: Minimum confidence floor
        conn_boost: Boost for well-connected nodes

    Returns:
        Configured ConfidencePropagator instance
    """
    return ConfidencePropagator(
        edge_confidence_factor=edge_factor,
        isolated_node_penalty=isolation_penalty,
        min_confidence=min_conf,
        connectivity_boost=conn_boost,
    )


# =============================================================================
# GraphType Enum
# =============================================================================

class GraphType(str, Enum):
    """Types of mathematical graphs for confidence adjustment."""
    FUNCTION_PLOT = "function_plot"
    GEOMETRY = "geometry"
    COORDINATE_SYSTEM = "coordinate_system"
    DIAGRAM = "diagram"
    DATA_VISUALIZATION = "data_visualization"
    UNKNOWN = "unknown"


# =============================================================================
# GraphTypeConfidenceAdjuster Class
# =============================================================================

class GraphTypeConfidenceAdjuster:
    """Adjust confidence based on graph type characteristics.

    Different graph types have different inherent complexity and
    reliability characteristics. This adjuster applies type-specific
    factors to node and edge confidence values.

    Factor interpretation:
    - Higher factor (e.g., 0.95) = minor adjustment, high baseline confidence
    - Lower factor (e.g., 0.80) = significant adjustment, more uncertainty

    Usage:
        adjuster = GraphTypeConfidenceAdjuster()
        adjuster.adjust_for_graph_type(graph)  # Mutates graph in place

    Configuration:
        - GRAPH_TYPE_FACTORS: Dict mapping GraphType to node/edge factors
        - Can be customized by passing custom_factors to constructor
    """

    # Default confidence adjustment factors per graph type
    GRAPH_TYPE_FACTORS: Dict[GraphType, Dict[str, float]] = {
        GraphType.FUNCTION_PLOT: {"node": 0.95, "edge": 0.90},
        GraphType.GEOMETRY: {"node": 0.90, "edge": 0.85},
        GraphType.COORDINATE_SYSTEM: {"node": 0.92, "edge": 0.88},
        GraphType.DIAGRAM: {"node": 0.85, "edge": 0.80},
        GraphType.DATA_VISUALIZATION: {"node": 0.88, "edge": 0.85},
        GraphType.UNKNOWN: {"node": 0.80, "edge": 0.75},
    }

    def __init__(
        self,
        custom_factors: Optional[Dict[GraphType, Dict[str, float]]] = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ):
        """Initialize GraphTypeConfidenceAdjuster.

        Args:
            custom_factors: Optional custom factors to override defaults.
                Format: {GraphType: {"node": float, "edge": float}}
            min_confidence: Minimum confidence floor after adjustment.
                All confidences are clamped to this minimum.
                Range: 0.0-1.0 (default: 0.1)
        """
        self.factors = dict(self.GRAPH_TYPE_FACTORS)
        if custom_factors:
            self.factors.update(custom_factors)

        self.min_confidence = min_confidence

        # Statistics tracking
        self._stats: Dict[str, Any] = {
            "nodes_adjusted": 0,
            "edges_adjusted": 0,
            "graph_type": None,
            "factors_applied": None,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """Return adjustment statistics."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset adjustment statistics."""
        self._stats = {
            "nodes_adjusted": 0,
            "edges_adjusted": 0,
            "graph_type": None,
            "factors_applied": None,
        }

    def _parse_graph_type(self, graph: SemanticGraph) -> GraphType:
        """Parse graph_type string field to GraphType enum.

        Args:
            graph: SemanticGraph with optional graph_type field

        Returns:
            GraphType enum value
        """
        if not graph.graph_type:
            return GraphType.UNKNOWN

        graph_type_str = graph.graph_type.lower().replace("-", "_").replace(" ", "_")

        # Try direct enum match
        for gt in GraphType:
            if gt.value == graph_type_str:
                return gt

        # Try partial match
        if "function" in graph_type_str or "plot" in graph_type_str:
            return GraphType.FUNCTION_PLOT
        elif "geometry" in graph_type_str or "geometric" in graph_type_str:
            return GraphType.GEOMETRY
        elif "coordinate" in graph_type_str or "axis" in graph_type_str:
            return GraphType.COORDINATE_SYSTEM
        elif "diagram" in graph_type_str or "flowchart" in graph_type_str:
            return GraphType.DIAGRAM
        elif "data" in graph_type_str or "chart" in graph_type_str or "bar" in graph_type_str:
            return GraphType.DATA_VISUALIZATION

        return GraphType.UNKNOWN

    def adjust_for_graph_type(self, graph: SemanticGraph) -> None:
        """Apply graph-type-specific confidence adjustments.

        Adjusts node and edge confidence values based on the graph type.
        Function plots typically have higher confidence than diagrams
        because mathematical functions have more deterministic properties.

        Args:
            graph: SemanticGraph to adjust. The graph is modified in place.
        """
        self.reset_stats()

        # Determine graph type
        graph_type = self._parse_graph_type(graph)
        self._stats["graph_type"] = graph_type.value

        # Get factors for this graph type
        factors = self.factors.get(graph_type, self.factors[GraphType.UNKNOWN])
        self._stats["factors_applied"] = factors

        node_factor = factors["node"]
        edge_factor = factors["edge"]

        # Adjust node confidence
        for node in graph.nodes:
            current_conf = node.confidence.value
            adjusted = current_conf * node_factor

            # Clamp to minimum
            adjusted = max(self.min_confidence, adjusted)

            node.confidence = Confidence(
                value=round(adjusted, 4),
                source=f"graph_type_adjusted_{graph_type.value}",
                element_type=node.node_type.value,
            )

            # Update threshold check if necessary
            if adjusted < node.applied_threshold:
                node.threshold_passed = False
                node.review.review_required = True
                if not node.review.review_reason:
                    node.review.review_reason = (
                        f"Graph-type adjustment reduced confidence to {adjusted:.2f}"
                    )

            self._stats["nodes_adjusted"] += 1

        # Adjust edge confidence
        for edge in graph.edges:
            current_conf = edge.confidence.value
            adjusted = current_conf * edge_factor

            # Clamp to minimum
            adjusted = max(self.min_confidence, adjusted)

            edge.confidence = Confidence(
                value=round(adjusted, 4),
                source=f"graph_type_adjusted_{graph_type.value}",
                element_type=edge.edge_type.value,
            )

            # Update threshold check if necessary
            if adjusted < edge.applied_threshold:
                edge.threshold_passed = False
                edge.review.review_required = True
                if not edge.review.review_reason:
                    edge.review.review_reason = (
                        f"Graph-type adjustment reduced confidence to {adjusted:.2f}"
                    )

            self._stats["edges_adjusted"] += 1

        logger.info(
            f"Graph-type confidence adjustment complete: "
            f"type={graph_type.value}, "
            f"factors=node:{node_factor}/edge:{edge_factor}, "
            f"adjusted {self._stats['nodes_adjusted']} nodes, "
            f"{self._stats['edges_adjusted']} edges"
        )

    def get_factors_for_type(self, graph_type: GraphType) -> Dict[str, float]:
        """Get confidence factors for a specific graph type.

        Args:
            graph_type: The GraphType to get factors for

        Returns:
            Dict with 'node' and 'edge' factor values
        """
        return self.factors.get(graph_type, self.factors[GraphType.UNKNOWN]).copy()


# =============================================================================
# Factory Functions
# =============================================================================

def create_graph_type_adjuster(
    custom_factors: Optional[Dict[GraphType, Dict[str, float]]] = None,
    min_conf: float = DEFAULT_MIN_CONFIDENCE,
) -> GraphTypeConfidenceAdjuster:
    """Factory function to create GraphTypeConfidenceAdjuster with custom config.

    Args:
        custom_factors: Optional custom factors to override defaults
        min_conf: Minimum confidence floor

    Returns:
        Configured GraphTypeConfidenceAdjuster instance
    """
    return GraphTypeConfidenceAdjuster(
        custom_factors=custom_factors,
        min_confidence=min_conf,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "GraphType",
    # Classes
    "ConfidencePropagator",
    "GraphTypeConfidenceAdjuster",
    # Factory functions
    "create_confidence_propagator",
    "create_graph_type_adjuster",
    # Constants
    "DEFAULT_EDGE_CONFIDENCE_FACTOR",
    "DEFAULT_ISOLATED_NODE_PENALTY",
    "DEFAULT_MIN_CONFIDENCE",
    "DEFAULT_CONNECTIVITY_BOOST",
]
