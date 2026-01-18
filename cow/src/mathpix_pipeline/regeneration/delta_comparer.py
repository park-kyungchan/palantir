"""
Delta Comparer for Stage F (Regeneration).

Compares original content with regenerated output:
- Structural comparison of elements
- Semantic similarity analysis
- Visual difference detection
- Detailed diff reporting

Module Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

from ..schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
)
from ..schemas.regeneration import (
    DeltaType,
    DeltaElement,
    DeltaReport,
    ElementCategory,
)
from .exceptions import DeltaComparisonError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Node type to element category mapping
NODE_TO_CATEGORY: Dict[NodeType, ElementCategory] = {
    NodeType.EQUATION: ElementCategory.EQUATION,
    NodeType.EXPRESSION: ElementCategory.EQUATION,
    NodeType.FUNCTION: ElementCategory.EQUATION,
    NodeType.LINE: ElementCategory.GRAPH,
    NodeType.CIRCLE: ElementCategory.GRAPH,
    NodeType.CURVE: ElementCategory.GRAPH,
    NodeType.POLYGON: ElementCategory.DIAGRAM,
    NodeType.ANGLE: ElementCategory.DIAGRAM,
    NodeType.POINT: ElementCategory.DIAGRAM,
    NodeType.LINE_SEGMENT: ElementCategory.DIAGRAM,
    NodeType.RAY: ElementCategory.DIAGRAM,
    NodeType.LABEL: ElementCategory.TEXT,
    NodeType.ANNOTATION: ElementCategory.ANNOTATION,
    NodeType.VARIABLE: ElementCategory.SYMBOL,
    NodeType.CONSTANT: ElementCategory.SYMBOL,
}

# Default similarity thresholds
DEFAULT_EXACT_THRESHOLD = 1.0
DEFAULT_SIMILAR_THRESHOLD = 0.8
DEFAULT_MODIFIED_THRESHOLD = 0.5


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class DeltaConfig:
    """Configuration for delta comparison.

    Attributes:
        exact_threshold: Similarity score for exact match
        similar_threshold: Similarity score for similar match
        modified_threshold: Minimum similarity for modified status
        compare_positions: Whether to compare spatial positions
        position_tolerance: Tolerance for position comparison
        compare_latex: Whether to compare LaTeX representations
        compare_labels: Whether to compare labels
        ignore_whitespace: Ignore whitespace in text comparison
    """
    exact_threshold: float = DEFAULT_EXACT_THRESHOLD
    similar_threshold: float = DEFAULT_SIMILAR_THRESHOLD
    modified_threshold: float = DEFAULT_MODIFIED_THRESHOLD
    compare_positions: bool = True
    position_tolerance: float = 0.01  # Normalized tolerance
    compare_latex: bool = True
    compare_labels: bool = True
    ignore_whitespace: bool = True


# =============================================================================
# Delta Comparer
# =============================================================================

class DeltaComparer:
    """Compare original and regenerated content for differences.

    Provides detailed analysis of:
    - Added elements (in regenerated but not original)
    - Removed elements (in original but not regenerated)
    - Modified elements (present in both but different)
    - Unchanged elements

    Usage:
        comparer = DeltaComparer()

        # Compare two graphs
        report = comparer.compare(original_graph, regenerated_graph)

        # Compare with original content string
        report = comparer.compare_with_original(
            regenerated_graph,
            original_latex="y = mx + b"
        )

        print(f"Similarity: {report.similarity_score}")
        print(f"Changes: {report.total_changes}")
    """

    def __init__(self, config: Optional[DeltaConfig] = None):
        """Initialize delta comparer.

        Args:
            config: Comparison configuration. Uses defaults if None.
        """
        self.config = config or DeltaConfig()

        self._stats = {
            "comparisons_performed": 0,
            "elements_compared": 0,
            "added_found": 0,
            "removed_found": 0,
            "modified_found": 0,
        }

        logger.debug(
            f"DeltaComparer initialized: similar_threshold={self.config.similar_threshold}"
        )

    @property
    def stats(self) -> Dict[str, int]:
        """Get comparison statistics."""
        return self._stats.copy()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        if self.config.ignore_whitespace:
            return " ".join(text.split())
        return text

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings.

        Uses SequenceMatcher for fuzzy string comparison.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score 0-1
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        s1_norm = self._normalize_text(s1)
        s2_norm = self._normalize_text(s2)

        return SequenceMatcher(None, s1_norm, s2_norm).ratio()

    def _get_node_signature(self, node: SemanticNode) -> str:
        """Get a unique signature for a node.

        Used for matching nodes between graphs.

        Args:
            node: SemanticNode

        Returns:
            Signature string
        """
        parts = [node.node_type.value, node.label]

        if node.properties.latex:
            parts.append(node.properties.latex)

        if node.properties.coordinates:
            x = node.properties.coordinates.get("x", 0)
            y = node.properties.coordinates.get("y", 0)
            parts.append(f"({x:.2f},{y:.2f})")

        return "|".join(parts)

    def _get_node_content(self, node: SemanticNode) -> str:
        """Get the primary content of a node for comparison.

        Args:
            node: SemanticNode

        Returns:
            Content string
        """
        if node.properties.latex:
            return node.properties.latex
        if node.properties.equation:
            return node.properties.equation
        return node.label

    def _get_node_category(self, node: SemanticNode) -> ElementCategory:
        """Map node type to element category.

        Args:
            node: SemanticNode

        Returns:
            ElementCategory
        """
        return NODE_TO_CATEGORY.get(node.node_type, ElementCategory.SYMBOL)

    def _compare_positions(
        self,
        original: SemanticNode,
        regenerated: SemanticNode,
    ) -> Tuple[bool, float]:
        """Compare spatial positions of two nodes.

        Args:
            original: Original node
            regenerated: Regenerated node

        Returns:
            Tuple of (positions_match, distance)
        """
        if not self.config.compare_positions:
            return True, 0.0

        orig_coords = original.properties.coordinates
        regen_coords = regenerated.properties.coordinates

        if not orig_coords or not regen_coords:
            return True, 0.0

        ox = orig_coords.get("x", 0)
        oy = orig_coords.get("y", 0)
        rx = regen_coords.get("x", 0)
        ry = regen_coords.get("y", 0)

        distance = ((ox - rx) ** 2 + (oy - ry) ** 2) ** 0.5
        matches = distance <= self.config.position_tolerance

        return matches, distance

    def _compare_nodes(
        self,
        original: SemanticNode,
        regenerated: SemanticNode,
    ) -> Tuple[DeltaType, float]:
        """Compare two nodes and determine delta type.

        Args:
            original: Original node
            regenerated: Regenerated node

        Returns:
            Tuple of (delta_type, similarity_score)
        """
        self._stats["elements_compared"] += 1

        # Compare content
        orig_content = self._get_node_content(original)
        regen_content = self._get_node_content(regenerated)

        content_similarity = self._calculate_similarity(orig_content, regen_content)

        # Compare labels if enabled
        if self.config.compare_labels:
            label_similarity = self._calculate_similarity(original.label, regenerated.label)
            content_similarity = (content_similarity + label_similarity) / 2

        # Check position
        if self.config.compare_positions:
            pos_match, distance = self._compare_positions(original, regenerated)
            if not pos_match:
                content_similarity *= 0.9  # Penalize position differences

        # Determine delta type
        if content_similarity >= self.config.exact_threshold:
            return DeltaType.UNCHANGED, content_similarity
        elif content_similarity >= self.config.similar_threshold:
            return DeltaType.MODIFIED, content_similarity
        else:
            return DeltaType.MODIFIED, content_similarity

    def compare(
        self,
        original: SemanticGraph,
        regenerated: SemanticGraph,
    ) -> DeltaReport:
        """Compare original and regenerated semantic graphs.

        Args:
            original: Original SemanticGraph
            regenerated: Regenerated SemanticGraph

        Returns:
            DeltaReport with detailed comparison results
        """
        start_time = time.time()

        added_elements: List[DeltaElement] = []
        removed_elements: List[DeltaElement] = []
        modified_elements: List[DeltaElement] = []
        unchanged_count = 0

        # Build signature maps
        original_by_sig: Dict[str, SemanticNode] = {}
        for node in original.nodes:
            sig = self._get_node_signature(node)
            original_by_sig[sig] = node

        regenerated_by_sig: Dict[str, SemanticNode] = {}
        for node in regenerated.nodes:
            sig = self._get_node_signature(node)
            regenerated_by_sig[sig] = node

        # Find exact matches and modifications
        matched_original: Set[str] = set()
        matched_regenerated: Set[str] = set()

        for orig_sig, orig_node in original_by_sig.items():
            if orig_sig in regenerated_by_sig:
                # Exact signature match
                regen_node = regenerated_by_sig[orig_sig]
                delta_type, similarity = self._compare_nodes(orig_node, regen_node)

                matched_original.add(orig_sig)
                matched_regenerated.add(orig_sig)

                if delta_type == DeltaType.UNCHANGED:
                    unchanged_count += 1
                else:
                    modified_elements.append(DeltaElement(
                        element_id=orig_node.id,
                        delta_type=DeltaType.MODIFIED,
                        category=self._get_node_category(orig_node),
                        original_content=self._get_node_content(orig_node),
                        regenerated_content=self._get_node_content(regen_node),
                        similarity_score=similarity,
                        change_description="Content modified during regeneration",
                    ))
                    self._stats["modified_found"] += 1

        # Find best matches for unmatched nodes
        unmatched_original = [
            original_by_sig[sig]
            for sig in original_by_sig
            if sig not in matched_original
        ]
        unmatched_regenerated = [
            regenerated_by_sig[sig]
            for sig in regenerated_by_sig
            if sig not in matched_regenerated
        ]

        # Try to match by content similarity
        for orig_node in list(unmatched_original):
            best_match = None
            best_similarity = 0.0

            for regen_node in list(unmatched_regenerated):
                if orig_node.node_type == regen_node.node_type:
                    _, similarity = self._compare_nodes(orig_node, regen_node)
                    if similarity > best_similarity and similarity >= self.config.modified_threshold:
                        best_match = regen_node
                        best_similarity = similarity

            if best_match:
                unmatched_original.remove(orig_node)
                unmatched_regenerated.remove(best_match)

                if best_similarity >= self.config.similar_threshold:
                    unchanged_count += 1
                else:
                    modified_elements.append(DeltaElement(
                        element_id=orig_node.id,
                        delta_type=DeltaType.MODIFIED,
                        category=self._get_node_category(orig_node),
                        original_content=self._get_node_content(orig_node),
                        regenerated_content=self._get_node_content(best_match),
                        similarity_score=best_similarity,
                        change_description="Significant content change detected",
                    ))
                    self._stats["modified_found"] += 1

        # Remaining unmatched original -> removed
        for node in unmatched_original:
            removed_elements.append(DeltaElement(
                element_id=node.id,
                delta_type=DeltaType.REMOVED,
                category=self._get_node_category(node),
                original_content=self._get_node_content(node),
                similarity_score=0.0,
                change_description="Element not found in regenerated output",
            ))
            self._stats["removed_found"] += 1

        # Remaining unmatched regenerated -> added
        for node in unmatched_regenerated:
            added_elements.append(DeltaElement(
                element_id=node.id,
                delta_type=DeltaType.ADDED,
                category=self._get_node_category(node),
                regenerated_content=self._get_node_content(node),
                similarity_score=0.0,
                change_description="New element in regenerated output",
            ))
            self._stats["added_found"] += 1

        # Calculate overall similarity
        total_elements = len(original.nodes) + len(regenerated.nodes)
        if total_elements > 0:
            matched_count = unchanged_count + len(modified_elements)
            similarity_score = (2 * matched_count) / total_elements
        else:
            similarity_score = 1.0

        # Determine change flags
        has_structural = len(added_elements) > 0 or len(removed_elements) > 0
        has_semantic = any(e.similarity_score < 0.8 for e in modified_elements)
        has_visual = any(
            e.original_position != e.regenerated_position
            for e in modified_elements
            if e.original_position and e.regenerated_position
        )

        comparison_time = (time.time() - start_time) * 1000
        self._stats["comparisons_performed"] += 1

        return DeltaReport(
            similarity_score=min(1.0, max(0.0, similarity_score)),
            unchanged_count=unchanged_count,
            added_elements=added_elements,
            removed_elements=removed_elements,
            modified_elements=modified_elements,
            has_structural_changes=has_structural,
            has_semantic_changes=has_semantic,
            has_visual_changes=has_visual,
            comparison_method="structural",
            comparison_time_ms=comparison_time,
        )

    def compare_with_original(
        self,
        regenerated: SemanticGraph,
        original_latex: Optional[str] = None,
        original_svg: Optional[str] = None,
    ) -> DeltaReport:
        """Compare regenerated graph with original content string.

        Simplified comparison when original graph is not available.

        Args:
            regenerated: Regenerated SemanticGraph
            original_latex: Original LaTeX content
            original_svg: Original SVG content

        Returns:
            DeltaReport with comparison results
        """
        start_time = time.time()

        modified_elements: List[DeltaElement] = []
        overall_similarity = 1.0

        if original_latex:
            # Compare with LaTeX nodes
            regen_latex_parts = []
            for node in regenerated.nodes:
                if node.properties.latex:
                    regen_latex_parts.append(node.properties.latex)

            combined_regen = " ".join(regen_latex_parts)
            latex_similarity = self._calculate_similarity(original_latex, combined_regen)

            if latex_similarity < self.config.similar_threshold:
                modified_elements.append(DeltaElement(
                    element_id="latex_content",
                    delta_type=DeltaType.MODIFIED,
                    category=ElementCategory.EQUATION,
                    original_content=original_latex[:200],
                    regenerated_content=combined_regen[:200],
                    similarity_score=latex_similarity,
                    change_description="LaTeX content differs from original",
                ))

            overall_similarity = latex_similarity

        comparison_time = (time.time() - start_time) * 1000
        self._stats["comparisons_performed"] += 1

        return DeltaReport(
            similarity_score=overall_similarity,
            unchanged_count=len(regenerated.nodes) - len(modified_elements),
            added_elements=[],
            removed_elements=[],
            modified_elements=modified_elements,
            has_structural_changes=False,
            has_semantic_changes=len(modified_elements) > 0,
            has_visual_changes=False,
            comparison_method="content",
            comparison_time_ms=comparison_time,
        )

    def compute_similarity_matrix(
        self,
        graphs: List[SemanticGraph],
    ) -> List[List[float]]:
        """Compute pairwise similarity matrix for multiple graphs.

        Args:
            graphs: List of SemanticGraphs

        Returns:
            NxN similarity matrix
        """
        n = len(graphs)
        matrix = [[1.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                report = self.compare(graphs[i], graphs[j])
                matrix[i][j] = report.similarity_score
                matrix[j][i] = report.similarity_score

        return matrix


# =============================================================================
# Factory Function
# =============================================================================

def create_delta_comparer(
    config: Optional[DeltaConfig] = None,
    **kwargs,
) -> DeltaComparer:
    """Factory function to create DeltaComparer.

    Args:
        config: Optional DeltaConfig
        **kwargs: Config overrides

    Returns:
        Configured DeltaComparer instance
    """
    if config is None:
        config = DeltaConfig(**kwargs)
    return DeltaComparer(config=config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "DeltaComparer",
    "DeltaConfig",
    "create_delta_comparer",
    "NODE_TO_CATEGORY",
]
