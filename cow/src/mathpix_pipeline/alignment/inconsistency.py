"""
Inconsistency Detector for Stage D (Alignment).

Detects and categorizes inconsistencies between text and visual elements:
- Label mismatches
- Coordinate mismatches
- Equation-graph conflicts
- Missing/extra labels

Schema Version: 2.0.0
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ..schemas import (
    BBox,
    Inconsistency,
    InconsistencyType,
    MatchedPair,
    ReviewMetadata,
    ReviewSeverity,
    TextElement,
    VisualElement,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class InconsistencyConfig:
    """Configuration for inconsistency detection."""
    # Thresholds for triggering inconsistencies
    coefficient_tolerance: float = 0.1  # Tolerance for equation coefficients
    coordinate_tolerance: float = 0.5  # Tolerance for coordinates

    # Severity mapping
    severity_thresholds: Dict[InconsistencyType, float] = field(default_factory=lambda: {
        InconsistencyType.LABEL_MISMATCH: 0.80,
        InconsistencyType.COORDINATE_MISMATCH: 0.80,
        InconsistencyType.EQUATION_GRAPH_MISMATCH: 0.90,
        InconsistencyType.MISSING_LABEL: 0.70,
        InconsistencyType.EXTRA_LABEL: 0.60,
        InconsistencyType.SCALE_INCONSISTENCY: 0.75,
        InconsistencyType.AMBIGUOUS_REFERENCE: 0.65,
    })

    # Auto-fix settings
    enable_auto_fix_suggestions: bool = True


# =============================================================================
# Inconsistency Detectors
# =============================================================================

class LabelInconsistencyDetector:
    """Detect label-related inconsistencies."""

    def detect_mismatch(
        self,
        text_label: str,
        visual_label: str,
    ) -> Optional[Tuple[str, str]]:
        """Detect label mismatch.

        Args:
            text_label: Label from text
            visual_label: Label from visual

        Returns:
            (expected, actual) if mismatch, None otherwise
        """
        if not text_label or not visual_label:
            return None

        # Normalize for comparison
        norm_text = text_label.strip().upper()
        norm_visual = visual_label.strip().upper()

        # Check for mismatch
        if norm_text != norm_visual:
            # Allow some flexibility
            if norm_text[0] == norm_visual[0]:
                return None  # First character matches, likely OK
            return (text_label, visual_label)

        return None


class EquationInconsistencyDetector:
    """Detect equation-graph inconsistencies."""

    def __init__(self, config: InconsistencyConfig):
        self.config = config

    def extract_coefficients(self, latex: str) -> Dict[str, float]:
        """Extract coefficients from equation.

        Args:
            latex: LaTeX equation

        Returns:
            Dict of coefficient names to values
        """
        coeffs = {}

        # Extract quadratic: ax² + bx + c
        quad_match = re.search(
            r"(-?\d*\.?\d*)?\s*x\^?2\s*([+-]\s*\d*\.?\d*)\s*x\s*([+-]\s*\d+\.?\d*)?",
            latex, re.IGNORECASE
        )
        if quad_match:
            a = quad_match.group(1) or "1"
            b = quad_match.group(2).replace(" ", "") if quad_match.group(2) else "0"
            c = quad_match.group(3).replace(" ", "") if quad_match.group(3) else "0"
            try:
                coeffs["a"] = float(a) if a not in ("", "-") else (-1.0 if a == "-" else 1.0)
                coeffs["b"] = float(b)
                coeffs["c"] = float(c)
            except ValueError:
                pass

        # Extract linear: mx + b
        linear_match = re.search(
            r"y\s*=\s*(-?\d*\.?\d*)\s*x\s*([+-]\s*\d+\.?\d*)?",
            latex, re.IGNORECASE
        )
        if linear_match and "a" not in coeffs:
            m = linear_match.group(1) or "1"
            b = linear_match.group(2).replace(" ", "") if linear_match.group(2) else "0"
            try:
                coeffs["m"] = float(m) if m not in ("", "-") else (-1.0 if m == "-" else 1.0)
                coeffs["b"] = float(b)
            except ValueError:
                pass

        return coeffs

    def detect_coefficient_mismatch(
        self,
        text_equation: str,
        inferred_equation: Optional[str],
    ) -> Optional[Tuple[str, str]]:
        """Detect coefficient mismatch between text and inferred equation.

        Args:
            text_equation: Equation from text
            inferred_equation: Equation inferred from visual

        Returns:
            (expected, actual) if mismatch, None otherwise
        """
        if not text_equation or not inferred_equation:
            return None

        text_coeffs = self.extract_coefficients(text_equation)
        inferred_coeffs = self.extract_coefficients(inferred_equation)

        if not text_coeffs or not inferred_coeffs:
            return None

        # Compare common coefficients
        for key in text_coeffs:
            if key in inferred_coeffs:
                diff = abs(text_coeffs[key] - inferred_coeffs[key])
                if diff > self.config.coefficient_tolerance:
                    return (
                        f"{key}={text_coeffs[key]}",
                        f"{key}={inferred_coeffs[key]}"
                    )

        return None


class CoordinateInconsistencyDetector:
    """Detect coordinate-related inconsistencies."""

    def __init__(self, config: InconsistencyConfig):
        self.config = config

    def detect_mismatch(
        self,
        text_coords: Optional[Tuple[float, float]],
        visual_coords: Optional[Dict[str, float]],
    ) -> Optional[Tuple[str, str]]:
        """Detect coordinate mismatch.

        Args:
            text_coords: Coordinates from text
            visual_coords: Coordinates from visual

        Returns:
            (expected, actual) if mismatch, None otherwise
        """
        if not text_coords or not visual_coords:
            return None

        if "x" not in visual_coords or "y" not in visual_coords:
            return None

        tx, ty = text_coords
        vx, vy = visual_coords["x"], visual_coords["y"]

        dx = abs(tx - vx)
        dy = abs(ty - vy)

        if dx > self.config.coordinate_tolerance or dy > self.config.coordinate_tolerance:
            return (
                f"({tx}, {ty})",
                f"({vx}, {vy})"
            )

        return None


# =============================================================================
# Main Detector
# =============================================================================

class InconsistencyDetector:
    """Main inconsistency detector for Stage D.

    Detects and categorizes all types of inconsistencies between
    text and visual elements.

    Usage:
        config = InconsistencyConfig()
        detector = InconsistencyDetector(config)

        inconsistencies = detector.detect_all(
            matched_pairs,
            unmatched_text,
            unmatched_visual,
            image_id
        )
    """

    def __init__(self, config: Optional[InconsistencyConfig] = None):
        """Initialize detector.

        Args:
            config: Inconsistency detection configuration
        """
        self.config = config or InconsistencyConfig()
        self.label_detector = LabelInconsistencyDetector()
        self.equation_detector = EquationInconsistencyDetector(self.config)
        self.coord_detector = CoordinateInconsistencyDetector(self.config)

    def _determine_severity(
        self,
        inconsistency_type: InconsistencyType,
        confidence: float,
    ) -> ReviewSeverity:
        """Determine severity based on type and confidence.

        Args:
            inconsistency_type: Type of inconsistency
            confidence: Detection confidence

        Returns:
            Appropriate severity level
        """
        threshold = self.config.severity_thresholds.get(
            inconsistency_type,
            0.80
        )

        if confidence >= 0.9:
            # High confidence inconsistency
            if inconsistency_type in (
                InconsistencyType.EQUATION_GRAPH_MISMATCH,
                InconsistencyType.COORDINATE_MISMATCH,
            ):
                return ReviewSeverity.BLOCKER
            return ReviewSeverity.HIGH

        if confidence >= threshold:
            return ReviewSeverity.HIGH

        return ReviewSeverity.MEDIUM

    def _suggest_fix(
        self,
        inconsistency_type: InconsistencyType,
        expected: str,
        actual: str,
    ) -> Optional[str]:
        """Suggest a fix for the inconsistency.

        Args:
            inconsistency_type: Type of inconsistency
            expected: Expected value
            actual: Actual value

        Returns:
            Fix suggestion or None
        """
        if not self.config.enable_auto_fix_suggestions:
            return None

        if inconsistency_type == InconsistencyType.LABEL_MISMATCH:
            return f"Update visual label to match text: '{expected}'"

        if inconsistency_type == InconsistencyType.COORDINATE_MISMATCH:
            return f"Verify coordinates: text shows {expected}, visual shows {actual}"

        if inconsistency_type == InconsistencyType.MISSING_LABEL:
            return f"Add missing label: '{expected}' to visual element"

        return None

    def detect_from_pair(
        self,
        pair: MatchedPair,
        image_id: str,
        idx: int,
    ) -> List[Inconsistency]:
        """Detect inconsistencies in a matched pair.

        Args:
            pair: Matched pair to check
            image_id: Image identifier
            idx: Index for ID generation

        Returns:
            List of detected inconsistencies
        """
        inconsistencies: List[Inconsistency] = []

        text_elem = pair.text_element
        visual_elem = pair.visual_element

        # Label mismatch
        label_mismatch = self.label_detector.detect_mismatch(
            text_elem.content,
            visual_elem.semantic_label
        )
        if label_mismatch:
            expected, actual = label_mismatch
            inconsistencies.append(Inconsistency(
                id=f"{image_id}-incon-{idx:03d}",
                inconsistency_type=InconsistencyType.LABEL_MISMATCH,
                severity=self._determine_severity(
                    InconsistencyType.LABEL_MISMATCH,
                    0.85
                ),
                text_element=text_elem,
                visual_element=visual_elem,
                description=f"Label mismatch: text '{expected}' vs visual '{actual}'",
                expected_value=expected,
                actual_value=actual,
                confidence=0.85,
                suggested_fix=self._suggest_fix(
                    InconsistencyType.LABEL_MISMATCH,
                    expected, actual
                ),
            ))
            idx += 1

        # Equation-graph mismatch (if applicable)
        if text_elem.latex:
            coeff_mismatch = self.equation_detector.detect_coefficient_mismatch(
                text_elem.latex,
                None  # Would need inferred equation from visual
            )
            if coeff_mismatch:
                expected, actual = coeff_mismatch
                inconsistencies.append(Inconsistency(
                    id=f"{image_id}-incon-{idx:03d}",
                    inconsistency_type=InconsistencyType.EQUATION_GRAPH_MISMATCH,
                    severity=ReviewSeverity.BLOCKER,
                    text_element=text_elem,
                    visual_element=visual_elem,
                    description=f"Equation coefficient mismatch: {expected} vs {actual}",
                    expected_value=expected,
                    actual_value=actual,
                    confidence=0.90,
                ))
                idx += 1

        return inconsistencies

    def detect_missing_labels(
        self,
        unmatched_text: List[TextElement],
        image_id: str,
        start_idx: int,
    ) -> List[Inconsistency]:
        """Detect missing labels (text without visual).

        Args:
            unmatched_text: Text elements without visual match
            image_id: Image identifier
            start_idx: Starting index for IDs

        Returns:
            List of missing label inconsistencies
        """
        inconsistencies: List[Inconsistency] = []

        for i, text_elem in enumerate(unmatched_text):
            # Skip non-label text
            if len(text_elem.content) > 20:  # Likely not a label
                continue

            inconsistencies.append(Inconsistency(
                id=f"{image_id}-incon-{start_idx + i:03d}",
                inconsistency_type=InconsistencyType.MISSING_LABEL,
                severity=ReviewSeverity.HIGH,
                text_element=text_elem,
                visual_element=None,
                description=f"Text label '{text_elem.content}' has no matching visual element",
                expected_value=text_elem.content,
                actual_value=None,
                confidence=0.80,
                suggested_fix=self._suggest_fix(
                    InconsistencyType.MISSING_LABEL,
                    text_elem.content, ""
                ),
            ))

        return inconsistencies

    def detect_extra_labels(
        self,
        unmatched_visual: List[VisualElement],
        image_id: str,
        start_idx: int,
    ) -> List[Inconsistency]:
        """Detect extra labels (visual without text).

        Args:
            unmatched_visual: Visual elements without text match
            image_id: Image identifier
            start_idx: Starting index for IDs

        Returns:
            List of extra label inconsistencies
        """
        inconsistencies: List[Inconsistency] = []

        for i, visual_elem in enumerate(unmatched_visual):
            # Only flag label-type elements
            if "label" not in visual_elem.element_class.lower():
                continue

            inconsistencies.append(Inconsistency(
                id=f"{image_id}-incon-{start_idx + i:03d}",
                inconsistency_type=InconsistencyType.EXTRA_LABEL,
                severity=ReviewSeverity.MEDIUM,
                text_element=None,
                visual_element=visual_elem,
                description=f"Visual label '{visual_elem.semantic_label}' has no matching text",
                expected_value=None,
                actual_value=visual_elem.semantic_label,
                confidence=0.75,
            ))

        return inconsistencies

    def detect_all(
        self,
        matched_pairs: List[MatchedPair],
        unmatched_text: List[TextElement],
        unmatched_visual: List[VisualElement],
        image_id: str,
    ) -> List[Inconsistency]:
        """Detect all inconsistencies.

        Args:
            matched_pairs: All matched pairs
            unmatched_text: Text elements without match
            unmatched_visual: Visual elements without match
            image_id: Image identifier

        Returns:
            All detected inconsistencies
        """
        all_inconsistencies: List[Inconsistency] = []
        idx = 0

        # From matched pairs
        for pair in matched_pairs:
            pair_inconsistencies = self.detect_from_pair(pair, image_id, idx)
            all_inconsistencies.extend(pair_inconsistencies)
            idx += len(pair_inconsistencies)

        # Missing labels
        missing = self.detect_missing_labels(unmatched_text, image_id, idx)
        all_inconsistencies.extend(missing)
        idx += len(missing)

        # Extra labels
        extra = self.detect_extra_labels(unmatched_visual, image_id, idx)
        all_inconsistencies.extend(extra)

        logger.info(f"Detected {len(all_inconsistencies)} inconsistencies for {image_id}")

        return all_inconsistencies


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "InconsistencyConfig",
    "LabelInconsistencyDetector",
    "EquationInconsistencyDetector",
    "CoordinateInconsistencyDetector",
    "InconsistencyDetector",
]
