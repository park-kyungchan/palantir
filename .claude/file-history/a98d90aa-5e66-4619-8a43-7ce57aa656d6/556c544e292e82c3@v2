"""
NodeExtractor for SemanticGraphBuilder (Stage E).

Extracts SemanticNodes from AlignmentReport matched pairs and unmatched elements.
Converts Stage D alignment results into graph nodes with proper type classification
and confidence propagation.

Module Version: 1.0.0
"""

import logging
import re
import uuid
from typing import Dict, List, Optional, Tuple

from ..schemas import (
    AlignmentReport,
    MatchedPair,
    UnmatchedElement,
    TextElement,
    VisualElement,
    MatchType,
    BBox,
)
from ..schemas.semantic_graph import (
    SemanticNode,
    NodeType,
    NodeProperties,
)
from ..schemas.common import Confidence

logger = logging.getLogger(__name__)


# =============================================================================
# Type Mapping Constants
# =============================================================================

# MatchType -> NodeType mapping
MATCH_TYPE_TO_NODE_TYPE: Dict[MatchType, NodeType] = {
    MatchType.LABEL_TO_POINT: NodeType.POINT,
    MatchType.LABEL_TO_CURVE: NodeType.CURVE,
    MatchType.EQUATION_TO_GRAPH: NodeType.EQUATION,
    MatchType.COORDINATE_TO_POINT: NodeType.POINT,
    MatchType.AXIS_LABEL: NodeType.AXIS,
    MatchType.DESCRIPTION_TO_ELEMENT: NodeType.ANNOTATION,
}

# Visual element class -> NodeType mapping
ELEMENT_CLASS_TO_NODE_TYPE: Dict[str, NodeType] = {
    # Geometric primitives
    "point": NodeType.POINT,
    "line": NodeType.LINE,
    "segment": NodeType.LINE_SEGMENT,
    "line_segment": NodeType.LINE_SEGMENT,
    "ray": NodeType.RAY,
    "circle": NodeType.CIRCLE,
    "ellipse": NodeType.CIRCLE,  # Treat ellipse as circle variant
    "curve": NodeType.CURVE,
    "arc": NodeType.CURVE,
    "polygon": NodeType.POLYGON,
    "triangle": NodeType.POLYGON,
    "quadrilateral": NodeType.POLYGON,
    "rectangle": NodeType.POLYGON,
    "square": NodeType.POLYGON,
    "angle": NodeType.ANGLE,
    # Graph elements
    "axis": NodeType.AXIS,
    "x_axis": NodeType.AXIS,
    "y_axis": NodeType.AXIS,
    "grid": NodeType.COORDINATE_SYSTEM,
    "coordinate_system": NodeType.COORDINATE_SYSTEM,
    "asymptote": NodeType.ASYMPTOTE,
    "intercept": NodeType.INTERCEPT,
    # Text/annotation
    "label": NodeType.LABEL,
    "text": NodeType.ANNOTATION,
    "annotation": NodeType.ANNOTATION,
    # Algebraic
    "equation": NodeType.EQUATION,
    "expression": NodeType.EXPRESSION,
    "function": NodeType.FUNCTION,
    "variable": NodeType.VARIABLE,
    "constant": NodeType.CONSTANT,
    # Region
    "region": NodeType.REGION,
    "shaded_region": NodeType.REGION,
}

# Generic element classes that should defer to content-based detection
# These are fallback categories, not specific geometric or algebraic types
GENERIC_ELEMENT_CLASSES: set = {"text", "annotation", "label"}


# =============================================================================
# NodeExtractor Class
# =============================================================================

class NodeExtractor:
    """Extract SemanticNodes from AlignmentReport.

    Converts Stage D alignment results into graph nodes:
    1. Matched pairs -> HIGH confidence nodes (alignment verified)
    2. Unmatched elements -> LOW confidence nodes (need review)

    The extractor handles:
    - Type classification based on match type and element class
    - Confidence propagation from alignment scores
    - Property extraction from text and visual elements
    - Unique ID generation for graph nodes

    Usage:
        extractor = NodeExtractor()
        nodes = extractor.extract(alignment_report)

    Configuration:
        - default_threshold: Confidence threshold for nodes (default: 0.60)
        - unmatched_confidence_penalty: Penalty for unmatched elements (default: 0.3)
    """

    def __init__(
        self,
        default_threshold: float = 0.60,
        unmatched_confidence_penalty: float = 0.3,
    ):
        """Initialize NodeExtractor.

        Args:
            default_threshold: Default confidence threshold for nodes.
                Nodes below this threshold are marked for review.
            unmatched_confidence_penalty: Confidence penalty applied to
                unmatched elements. Reduces base confidence by this factor.
        """
        self.default_threshold = default_threshold
        self.unmatched_confidence_penalty = unmatched_confidence_penalty

        # Statistics tracking
        self._stats: Dict[str, int] = {
            "total_extracted": 0,
            "from_matched": 0,
            "from_unmatched": 0,
            "above_threshold": 0,
            "below_threshold": 0,
        }

    @property
    def stats(self) -> Dict[str, int]:
        """Return extraction statistics."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset extraction statistics."""
        for key in self._stats:
            self._stats[key] = 0

    def extract(self, alignment_report: AlignmentReport) -> List[SemanticNode]:
        """Extract all nodes from alignment report.

        Processes matched pairs first (higher confidence), then unmatched
        elements (lower confidence). Each element is converted to a
        SemanticNode with appropriate type, confidence, and properties.

        Args:
            alignment_report: Stage D alignment output containing
                matched_pairs, inconsistencies, and unmatched_elements.

        Returns:
            List of SemanticNodes ready for graph construction.
        """
        self.reset_stats()
        nodes: List[SemanticNode] = []

        # Extract from matched pairs (high confidence)
        for pair in alignment_report.matched_pairs:
            node = self._extract_from_matched(pair)
            if node:
                nodes.append(node)
                self._stats["from_matched"] += 1
                if node.threshold_passed:
                    self._stats["above_threshold"] += 1
                else:
                    self._stats["below_threshold"] += 1

        # Extract from unmatched elements (low confidence)
        for element in alignment_report.unmatched_elements:
            node = self._extract_from_unmatched(element)
            if node:
                nodes.append(node)
                self._stats["from_unmatched"] += 1
                if node.threshold_passed:
                    self._stats["above_threshold"] += 1
                else:
                    self._stats["below_threshold"] += 1

        self._stats["total_extracted"] = len(nodes)

        logger.info(
            f"Extracted {len(nodes)} nodes: "
            f"{self._stats['from_matched']} from matched pairs, "
            f"{self._stats['from_unmatched']} from unmatched elements "
            f"({self._stats['above_threshold']} above threshold, "
            f"{self._stats['below_threshold']} below)"
        )

        return nodes

    def _extract_from_matched(self, pair: MatchedPair) -> Optional[SemanticNode]:
        """Create SemanticNode from a matched pair.

        Matched pairs represent elements where text and visual content
        align, resulting in higher confidence nodes.

        Args:
            pair: A MatchedPair from AlignmentReport containing
                text_element, visual_element, and alignment scores.

        Returns:
            SemanticNode if extraction succeeds, None otherwise.
        """
        try:
            # Determine node type from match type and elements
            node_type = self._classify_node_type(
                text_element=pair.text_element,
                visual_element=pair.visual_element,
                match_type=pair.match_type,
            )

            # Generate label from available content
            label = self._generate_label(
                text_element=pair.text_element,
                visual_element=pair.visual_element,
                node_type=node_type,
            )

            # Compute confidence from alignment scores
            confidence = self._compute_matched_confidence(pair)

            # Extract type-specific properties
            properties = self._extract_properties(
                text_element=pair.text_element,
                visual_element=pair.visual_element,
                node_type=node_type,
            )

            # Get bounding box (prefer visual element's bbox)
            bbox = pair.visual_element.bbox

            # Collect source element IDs for provenance
            source_ids = [pair.text_element.id, pair.visual_element.id]

            return SemanticNode(
                id=self._generate_node_id("matched"),
                node_type=node_type,
                label=label,
                bbox=bbox,
                confidence=confidence,
                applied_threshold=self.default_threshold,
                properties=properties,
                source_element_ids=source_ids,
            )

        except Exception as e:
            logger.warning(f"Failed to extract node from matched pair {pair.id}: {e}")
            return None

    def _extract_from_unmatched(self, element: UnmatchedElement) -> Optional[SemanticNode]:
        """Create SemanticNode from an unmatched element.

        Unmatched elements have lower confidence since they couldn't be
        verified through text-visual alignment.

        Args:
            element: An UnmatchedElement from AlignmentReport containing
                source (text/visual), content, and reason for not matching.

        Returns:
            SemanticNode if extraction succeeds, None otherwise.
        """
        try:
            # Determine node type from element content
            node_type = self._classify_unmatched_type(element)

            # Use element content as label
            label = element.content or f"unmatched_{element.source}"

            # Apply confidence penalty for unmatched elements
            base_confidence = 0.5  # Default medium confidence
            penalized = base_confidence * (1.0 - self.unmatched_confidence_penalty)

            confidence = Confidence(
                value=max(0.1, penalized),  # Minimum 0.1 confidence
                source="unmatched_element",
                element_type=node_type.value,
            )

            # Extract properties from content
            properties = self._extract_unmatched_properties(element, node_type)

            return SemanticNode(
                id=self._generate_node_id("unmatched"),
                node_type=node_type,
                label=label,
                bbox=element.bbox,
                confidence=confidence,
                applied_threshold=self.default_threshold,
                properties=properties,
                source_element_ids=[element.element_id],
            )

        except Exception as e:
            logger.warning(
                f"Failed to extract node from unmatched element {element.id}: {e}"
            )
            return None

    def _classify_node_type(
        self,
        text_element: Optional[TextElement],
        visual_element: Optional[VisualElement],
        match_type: Optional[MatchType] = None,
    ) -> NodeType:
        """Determine NodeType based on element properties.

        Classification priority:
        1. Match type (most specific, excludes DESCRIPTION_TO_ELEMENT)
        2. Specific visual element class (excludes generic classes)
        3. LaTeX pattern detection from text
        4. Content-based detection
        5. Generic element class fallback (text, annotation, label)
        6. DESCRIPTION_TO_ELEMENT fallback
        7. Final fallback to ANNOTATION

        Args:
            text_element: TextElement from alignment (may be None)
            visual_element: VisualElement from alignment (may be None)
            match_type: MatchType from the pair (may be None)

        Returns:
            Classified NodeType
        """
        # Priority 1: Specific match types (not DESCRIPTION_TO_ELEMENT which is generic)
        if (match_type and match_type in MATCH_TYPE_TO_NODE_TYPE
                and match_type != MatchType.DESCRIPTION_TO_ELEMENT):
            return MATCH_TYPE_TO_NODE_TYPE[match_type]

        # Priority 2: Specific visual element class (not generic classes like "text")
        # Generic classes defer to content-based detection for more accurate typing
        element_class = None
        if visual_element:
            element_class = visual_element.element_class.lower()
            if (element_class in ELEMENT_CLASS_TO_NODE_TYPE
                    and element_class not in GENERIC_ELEMENT_CLASSES):
                return ELEMENT_CLASS_TO_NODE_TYPE[element_class]

        # Priority 3: LaTeX pattern detection from text
        if text_element and text_element.latex:
            detected = self._detect_type_from_latex(text_element.latex)
            if detected:
                return detected

        # Priority 4: Content-based detection
        if text_element and text_element.content:
            detected = self._detect_type_from_content(text_element.content)
            if detected:
                return detected

        # Priority 5: Generic element class fallback (text, annotation, label)
        # Only used when content-based detection doesn't find a more specific type
        if element_class and element_class in GENERIC_ELEMENT_CLASSES:
            return ELEMENT_CLASS_TO_NODE_TYPE[element_class]

        # Priority 6: DESCRIPTION_TO_ELEMENT fallback when no specific type found
        if match_type == MatchType.DESCRIPTION_TO_ELEMENT:
            return MATCH_TYPE_TO_NODE_TYPE[match_type]

        # Priority 7: Final fallback to ANNOTATION for unclassified
        return NodeType.ANNOTATION

    def _classify_unmatched_type(self, element: UnmatchedElement) -> NodeType:
        """Classify NodeType for an unmatched element.

        Args:
            element: UnmatchedElement to classify

        Returns:
            Classified NodeType
        """
        content = element.content.lower() if element.content else ""

        # Check for element class patterns in content
        for class_name, node_type in ELEMENT_CLASS_TO_NODE_TYPE.items():
            if class_name in content:
                return node_type

        # Try LaTeX detection
        if element.content:
            detected = self._detect_type_from_latex(element.content)
            if detected:
                return detected

        # Source-based fallback
        if element.source == "visual":
            return NodeType.ANNOTATION
        else:  # text source
            return NodeType.LABEL

    def _detect_type_from_latex(self, latex: str) -> Optional[NodeType]:
        """Detect node type from LaTeX content patterns.

        Args:
            latex: LaTeX string to analyze

        Returns:
            Detected NodeType or None if no pattern matches
        """
        if not latex:
            return None

        latex_lower = latex.lower()

        # Equation patterns (contains = with variables)
        if "=" in latex and re.search(r"[a-zA-Z]", latex):
            # Check if it's a function definition
            if re.search(r"[fg]\s*\(.*\)\s*=", latex):
                return NodeType.FUNCTION
            return NodeType.EQUATION

        # Function patterns
        function_patterns = [
            r"f\s*\(",
            r"g\s*\(",
            r"h\s*\(",
            r"\\sin",
            r"\\cos",
            r"\\tan",
            r"\\log",
            r"\\ln",
            r"\\exp",
        ]
        if any(re.search(p, latex_lower) for p in function_patterns):
            return NodeType.FUNCTION

        # Point coordinate patterns: (x, y)
        if re.search(r"\(\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*\s*\)", latex):
            return NodeType.POINT

        # Single letter variable
        if re.match(r"^[a-zA-Z]$", latex.strip()):
            return NodeType.VARIABLE

        # Greek letters (often used as variables)
        greek_pattern = r"\\(alpha|beta|gamma|delta|theta|phi|psi|omega)"
        if re.search(greek_pattern, latex_lower):
            return NodeType.VARIABLE

        # Constant patterns
        if re.match(r"^-?\d+\.?\d*$", latex.strip()):
            return NodeType.CONSTANT

        # Pi, e constants
        if latex.strip() in ["\\pi", "\\e", "e", "\\infty"]:
            return NodeType.CONSTANT

        return None

    def _detect_type_from_content(self, content: str) -> Optional[NodeType]:
        """Detect node type from text content.

        Args:
            content: Plain text content to analyze

        Returns:
            Detected NodeType or None if no pattern matches
        """
        if not content:
            return None

        content_lower = content.lower().strip()

        # Axis labels
        if content_lower in ["x", "y", "z", "x-axis", "y-axis", "z-axis"]:
            return NodeType.AXIS

        # Common point labels (A, B, C, P, Q, etc.)
        if len(content_lower) == 1 and content_lower.isalpha():
            return NodeType.POINT

        # Origin
        if content_lower in ["o", "origin", "(0,0)", "(0, 0)"]:
            return NodeType.POINT

        # Angle notation
        if content_lower.startswith("angle") or "degree" in content_lower:
            return NodeType.ANGLE

        return None

    def _generate_label(
        self,
        text_element: Optional[TextElement],
        visual_element: Optional[VisualElement],
        node_type: NodeType,
    ) -> str:
        """Generate a human-readable label for the node.

        Priority:
        1. Text element content (user-visible label)
        2. Visual element semantic label
        3. Node type based fallback

        Args:
            text_element: TextElement from alignment
            visual_element: VisualElement from alignment
            node_type: Classified node type

        Returns:
            Human-readable label string
        """
        # Priority 1: Text content
        if text_element:
            if text_element.content:
                return text_element.content.strip()
            if text_element.latex:
                return text_element.latex.strip()

        # Priority 2: Visual semantic label
        if visual_element and visual_element.semantic_label:
            return visual_element.semantic_label.strip()

        # Priority 3: Node type fallback
        return f"{node_type.value}_{uuid.uuid4().hex[:4]}"

    def _compute_matched_confidence(self, pair: MatchedPair) -> Confidence:
        """Compute node confidence from matched pair alignment scores.

        Combines:
        - Consistency score (primary)
        - Semantic similarity (if available)
        - Source confidence

        Args:
            pair: MatchedPair containing alignment scores

        Returns:
            Computed Confidence object
        """
        # Base from consistency score
        base = pair.consistency_score

        # Boost from semantic similarity if available
        if pair.semantic_similarity is not None:
            base = (base + pair.semantic_similarity) / 2

        # Apply source confidence
        source_conf = pair.confidence.value if pair.confidence else 0.8
        final = base * source_conf

        # Clamp to valid range
        final = max(0.0, min(1.0, final))

        return Confidence(
            value=round(final, 4),
            source="alignment_propagation",
            element_type=pair.match_type.value,
        )

    def _extract_properties(
        self,
        text_element: Optional[TextElement],
        visual_element: Optional[VisualElement],
        node_type: NodeType,
    ) -> NodeProperties:
        """Extract type-specific properties from elements.

        Properties vary by node type:
        - POINT: coordinates, point_label
        - LINE/CURVE: equation, slope, y_intercept
        - CIRCLE: center, radius
        - ANGLE: measure, measure_unit
        - FUNCTION: function_type, domain, range
        - All: latex, description

        Args:
            text_element: TextElement from alignment
            visual_element: VisualElement from alignment
            node_type: Classified node type

        Returns:
            NodeProperties with type-specific fields populated
        """
        props = NodeProperties()

        # Extract LaTeX if available
        if text_element and text_element.latex:
            props.latex = text_element.latex

        # Extract description from visual semantic label
        if visual_element and visual_element.semantic_label:
            props.description = visual_element.semantic_label

        # Type-specific property extraction
        if node_type == NodeType.POINT:
            coords = self._extract_coordinates(text_element)
            if coords:
                props.coordinates = {"x": coords[0], "y": coords[1]}
            if text_element and text_element.content:
                # Single letter labels for points
                content = text_element.content.strip()
                if len(content) <= 2:
                    props.point_label = content

        elif node_type in (NodeType.LINE, NodeType.CURVE, NodeType.LINE_SEGMENT):
            equation_info = self._extract_equation_info(text_element)
            if equation_info:
                props.equation = equation_info.get("equation")
                props.slope = equation_info.get("slope")
                props.y_intercept = equation_info.get("y_intercept")

        elif node_type == NodeType.CIRCLE:
            circle_info = self._extract_circle_info(text_element)
            if circle_info:
                props.center = circle_info.get("center")
                props.radius = circle_info.get("radius")

        elif node_type == NodeType.ANGLE:
            angle_info = self._extract_angle_info(text_element)
            if angle_info:
                props.measure = angle_info.get("measure")
                props.measure_unit = angle_info.get("unit", "degrees")

        elif node_type == NodeType.FUNCTION:
            func_info = self._extract_function_info(text_element)
            if func_info:
                props.function_type = func_info.get("type")
                props.domain = func_info.get("domain")
                props.range = func_info.get("range")

        return props

    def _extract_unmatched_properties(
        self,
        element: UnmatchedElement,
        node_type: NodeType,
    ) -> NodeProperties:
        """Extract properties from an unmatched element.

        Args:
            element: UnmatchedElement to process
            node_type: Classified node type

        Returns:
            NodeProperties with available fields
        """
        props = NodeProperties()

        if element.content:
            # Try to detect LaTeX
            if "\\" in element.content or "$" in element.content:
                props.latex = element.content
            else:
                props.description = element.content

            # Type-specific extraction
            if node_type == NodeType.POINT:
                coords = self._parse_coordinates(element.content)
                if coords:
                    props.coordinates = {"x": coords[0], "y": coords[1]}

        return props

    def _extract_coordinates(
        self, text_element: Optional[TextElement]
    ) -> Optional[Tuple[float, float]]:
        """Extract point coordinates from text element.

        Args:
            text_element: TextElement potentially containing coordinates

        Returns:
            Tuple of (x, y) or None if not found
        """
        if not text_element:
            return None

        # Try content first, then latex
        for content in [text_element.content, text_element.latex]:
            if content:
                coords = self._parse_coordinates(content)
                if coords:
                    return coords

        return None

    def _parse_coordinates(self, text: str) -> Optional[Tuple[float, float]]:
        """Parse coordinate pair from text.

        Handles formats:
        - (x, y)
        - (x,y)
        - x, y

        Args:
            text: Text potentially containing coordinates

        Returns:
            Tuple of (x, y) or None if parsing fails
        """
        if not text:
            return None

        # Pattern: (number, number) with optional spaces
        pattern = r"\(\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)"
        match = re.search(pattern, text)
        if match:
            try:
                x = float(match.group(1))
                y = float(match.group(2))
                return (x, y)
            except ValueError:
                pass

        return None

    def _extract_equation_info(
        self, text_element: Optional[TextElement]
    ) -> Optional[Dict[str, any]]:
        """Extract equation information from text element.

        Args:
            text_element: TextElement potentially containing equation

        Returns:
            Dict with equation, slope, y_intercept or None
        """
        if not text_element:
            return None

        content = text_element.latex or text_element.content
        if not content:
            return None

        result: Dict[str, any] = {"equation": content}

        # Try to extract slope-intercept form: y = mx + b
        slope_pattern = r"y\s*=\s*(-?\d*\.?\d*)\s*x\s*([+-]\s*\d+\.?\d*)?"
        match = re.search(slope_pattern, content, re.IGNORECASE)
        if match:
            try:
                slope_str = match.group(1) or "1"
                result["slope"] = float(slope_str) if slope_str else 1.0

                if match.group(2):
                    intercept_str = match.group(2).replace(" ", "")
                    result["y_intercept"] = float(intercept_str)
            except ValueError:
                pass

        return result

    def _extract_circle_info(
        self, text_element: Optional[TextElement]
    ) -> Optional[Dict[str, any]]:
        """Extract circle information from text element.

        Args:
            text_element: TextElement potentially containing circle info

        Returns:
            Dict with center and radius or None
        """
        if not text_element:
            return None

        content = text_element.latex or text_element.content
        if not content:
            return None

        result: Dict[str, any] = {}

        # Standard form: (x-h)^2 + (y-k)^2 = r^2
        # Try to extract center and radius
        center_pattern = r"\(x\s*-\s*(-?\d+\.?\d*)\)"
        match_x = re.search(center_pattern, content)
        if match_x:
            result["center"] = {"x": float(match_x.group(1)), "y": 0}

        # Look for radius
        radius_pattern = r"=\s*(\d+\.?\d*)"
        match_r = re.search(radius_pattern, content)
        if match_r:
            r_squared = float(match_r.group(1))
            result["radius"] = r_squared**0.5

        return result if result else None

    def _extract_angle_info(
        self, text_element: Optional[TextElement]
    ) -> Optional[Dict[str, any]]:
        """Extract angle information from text element.

        Args:
            text_element: TextElement potentially containing angle info

        Returns:
            Dict with measure and unit or None
        """
        if not text_element:
            return None

        content = text_element.latex or text_element.content
        if not content:
            return None

        result: Dict[str, any] = {"unit": "degrees"}

        # Pattern: number followed by degree symbol or "degrees"
        degree_pattern = r"(\d+\.?\d*)\s*(°|degrees?|deg)"
        match = re.search(degree_pattern, content, re.IGNORECASE)
        if match:
            result["measure"] = float(match.group(1))
            return result

        # Radians pattern
        radian_pattern = r"(\d+\.?\d*)\s*(rad|radians?)"
        match = re.search(radian_pattern, content, re.IGNORECASE)
        if match:
            result["measure"] = float(match.group(1))
            result["unit"] = "radians"
            return result

        # Pi fractions: pi/2, 2*pi/3, etc.
        pi_pattern = r"(\d*)\s*\\?pi\s*/\s*(\d+)"
        match = re.search(pi_pattern, content, re.IGNORECASE)
        if match:
            numerator = float(match.group(1)) if match.group(1) else 1.0
            denominator = float(match.group(2))
            result["measure"] = numerator / denominator
            result["unit"] = "pi_radians"
            return result

        return None

    def _extract_function_info(
        self, text_element: Optional[TextElement]
    ) -> Optional[Dict[str, any]]:
        """Extract function information from text element.

        Args:
            text_element: TextElement potentially containing function info

        Returns:
            Dict with function_type, domain, range or None
        """
        if not text_element:
            return None

        content = text_element.latex or text_element.content
        if not content:
            return None

        result: Dict[str, any] = {}

        # Detect function type from patterns
        content_lower = content.lower()

        if "sin" in content_lower:
            result["type"] = "trigonometric"
        elif "cos" in content_lower:
            result["type"] = "trigonometric"
        elif "tan" in content_lower:
            result["type"] = "trigonometric"
        elif "log" in content_lower or "ln" in content_lower:
            result["type"] = "logarithmic"
        elif "exp" in content_lower or "e^" in content_lower:
            result["type"] = "exponential"
        elif "x^2" in content or "x^3" in content:
            result["type"] = "polynomial"
        elif "/" in content and "x" in content:
            result["type"] = "rational"
        else:
            result["type"] = "general"

        return result if result else None

    def _generate_node_id(self, prefix: str = "node") -> str:
        """Generate unique node ID.

        Args:
            prefix: Prefix for the ID (e.g., "matched", "unmatched")

        Returns:
            Unique identifier string
        """
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


# =============================================================================
# Factory Function
# =============================================================================

def create_node_extractor(
    threshold: float = 0.60,
    penalty: float = 0.3,
) -> NodeExtractor:
    """Factory function to create NodeExtractor with custom config.

    Args:
        threshold: Default confidence threshold for nodes
        penalty: Confidence penalty for unmatched elements

    Returns:
        Configured NodeExtractor instance
    """
    return NodeExtractor(
        default_threshold=threshold,
        unmatched_confidence_penalty=penalty,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "NodeExtractor",
    "create_node_extractor",
    "MATCH_TYPE_TO_NODE_TYPE",
    "ELEMENT_CLASS_TO_NODE_TYPE",
]
