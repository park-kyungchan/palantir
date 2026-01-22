"""
Hybrid Merger for Stage C (Vision Parse).

Combines YOLO detection and Claude interpretation results:
- Matches detection elements with interpretation elements
- Merges bbox (from YOLO) with semantic info (from Claude)
- Handles unmatched elements from both layers
- Computes combined confidence scores

Schema Version: 2.0.0
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..schemas import (
    BBox,
    CombinedConfidence,
    DetectionElement,
    DetectionLayer,
    InterpretedElement,
    InterpretationLayer,
    MergedElement,
    MergedOutput,
    ReviewMetadata,
    ReviewSeverity,
    calculate_combined_confidence,
)
from ..utils.geometry import calculate_iou

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class MergerConfig:
    """Configuration for hybrid merger."""
    # Matching thresholds
    iou_threshold: float = 0.5  # Minimum IoU for element matching
    fallback_iou_threshold: float = 0.3  # Lower threshold if no good match

    # Confidence weights
    detection_weight: float = 0.6  # YOLO confidence weight
    interpretation_weight: float = 0.4  # Claude confidence weight

    # Review thresholds
    low_confidence_threshold: float = 0.5
    very_low_confidence_threshold: float = 0.3


# =============================================================================
# Hybrid Merger
# =============================================================================

class HybridMerger:
    """Merges YOLO detection and Claude interpretation results.

    The merger:
    1. Matches detection elements to interpretation elements by bbox overlap
    2. Creates merged elements with bbox from YOLO, semantics from Claude
    3. Handles unmatched elements (detection-only, interpretation-only)
    4. Computes combined confidence scores

    Usage:
        merger = HybridMerger(config)
        merged_output = merger.merge(detection_layer, interpretation_layer, image_id)
    """

    def __init__(self, config: Optional[MergerConfig] = None):
        """Initialize merger.

        Args:
            config: Merger configuration
        """
        self.config = config or MergerConfig()

    def _find_best_match(
        self,
        interp_element: InterpretedElement,
        detection_elements: List[DetectionElement],
        used_detections: set,
    ) -> Optional[Tuple[DetectionElement, float]]:
        """Find best matching detection for an interpretation.

        Args:
            interp_element: Interpreted element to match
            detection_elements: Available detection elements
            used_detections: Set of already-matched detection IDs

        Returns:
            Tuple of (best matching detection, IoU score) or None
        """
        # If interpretation has explicit detection reference, use it
        if interp_element.detection_element_id:
            for det in detection_elements:
                if det.id == interp_element.detection_element_id:
                    if det.id not in used_detections:
                        return (det, 1.0)  # Perfect match by reference
            # Referenced detection not found or already used
            logger.warning(
                f"Interpretation {interp_element.id} references "
                f"{interp_element.detection_element_id} but not available"
            )

        # No explicit reference - this is expected for interpretation-only elements
        # Return None to mark as interpretation-only
        return None

    def _create_merged_element(
        self,
        detection: DetectionElement,
        interpretation: Optional[InterpretedElement],
        image_id: str,
        idx: int,
    ) -> MergedElement:
        """Create merged element from detection and optional interpretation.

        Args:
            detection: YOLO detection element (provides bbox)
            interpretation: Claude interpretation (provides semantics), may be None
            image_id: Image identifier
            idx: Element index for ID generation

        Returns:
            Merged element
        """
        if interpretation:
            # Full merge: bbox from YOLO, semantics from Claude
            combined_conf = calculate_combined_confidence(
                detection_conf=detection.detection_confidence,
                interpretation_conf=interpretation.interpretation_confidence,
                detection_weight=self.config.detection_weight,
                interpretation_weight=self.config.interpretation_weight,
            )

            return MergedElement(
                id=f"{image_id}-merged-{idx:03d}",
                detection_id=detection.id,
                interpretation_id=interpretation.id,
                bbox_source="yolo26",
                label_source="claude-opus-4-5",
                element_class=detection.element_class,
                bbox=detection.bbox,
                semantic_label=interpretation.semantic_label,
                description=interpretation.description,
                combined_confidence=combined_conf,
                latex_representation=interpretation.latex_representation,
                equation=interpretation.equation,
                coordinates=interpretation.coordinates,
            )
        else:
            # Detection-only: no semantic info from Claude
            combined_conf = CombinedConfidence(
                detection_confidence=detection.detection_confidence,
                interpretation_confidence=0.0,
                combined_value=detection.detection_confidence * self.config.detection_weight,
                bbox_source="yolo26",
                label_source="none",
                detection_weight=self.config.detection_weight,
                interpretation_weight=0.0,
            )

            review = ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.MEDIUM,
                review_reason="Detection-only element: no semantic interpretation",
            )

            return MergedElement(
                id=f"{image_id}-merged-{idx:03d}",
                detection_id=detection.id,
                interpretation_id=None,
                bbox_source="yolo26",
                label_source="none",
                element_class=detection.element_class,
                bbox=detection.bbox,
                semantic_label=detection.element_class.value,  # Use class as label
                combined_confidence=combined_conf,
                review=review,
            )

    def _create_interpretation_only_element(
        self,
        interpretation: InterpretedElement,
        image_id: str,
        idx: int,
    ) -> MergedElement:
        """Create merged element from interpretation without detection.

        Args:
            interpretation: Claude interpretation element
            image_id: Image identifier
            idx: Element index

        Returns:
            Merged element (bbox is placeholder)
        """
        # Placeholder bbox (Claude doesn't provide precise coordinates)
        placeholder_bbox = BBox(x=0, y=0, width=1, height=1)

        combined_conf = CombinedConfidence(
            detection_confidence=0.0,
            interpretation_confidence=interpretation.interpretation_confidence,
            combined_value=interpretation.interpretation_confidence * self.config.interpretation_weight,
            bbox_source="none",
            label_source="claude-opus-4-5",
            detection_weight=0.0,
            interpretation_weight=self.config.interpretation_weight,
        )

        review = ReviewMetadata(
            review_required=True,
            review_severity=ReviewSeverity.HIGH,
            review_reason="Interpretation-only element: no bbox available",
        )

        # Infer element class from semantic label
        from ..schemas import ElementClass
        element_class = ElementClass.UNKNOWN

        return MergedElement(
            id=f"{image_id}-merged-{idx:03d}",
            detection_id=None,
            interpretation_id=interpretation.id,
            bbox_source="none",
            label_source="claude-opus-4-5",
            element_class=element_class,
            bbox=placeholder_bbox,
            semantic_label=interpretation.semantic_label,
            description=interpretation.description,
            combined_confidence=combined_conf,
            latex_representation=interpretation.latex_representation,
            equation=interpretation.equation,
            coordinates=interpretation.coordinates,
            review=review,
        )

    def merge(
        self,
        detection_layer: DetectionLayer,
        interpretation_layer: InterpretationLayer,
        image_id: str,
    ) -> MergedOutput:
        """Merge detection and interpretation layers.

        Args:
            detection_layer: YOLO detection results
            interpretation_layer: Claude interpretation results
            image_id: Image identifier

        Returns:
            MergedOutput with combined elements
        """
        merged_elements: List[MergedElement] = []
        used_detections: set = set()
        used_interpretations: set = set()
        idx = 0

        # Phase 1: Match interpretations to detections
        for interp in interpretation_layer.elements:
            match = self._find_best_match(
                interp,
                detection_layer.elements,
                used_detections,
            )

            if match:
                detection, iou = match
                merged = self._create_merged_element(
                    detection,
                    interp,
                    image_id,
                    idx,
                )
                merged_elements.append(merged)
                used_detections.add(detection.id)
                used_interpretations.add(interp.id)
                idx += 1
            else:
                # Interpretation without matching detection
                # Will be handled in Phase 3
                pass

        # Phase 2: Add unmatched detections (detection-only)
        for detection in detection_layer.elements:
            if detection.id not in used_detections:
                merged = self._create_merged_element(
                    detection,
                    None,
                    image_id,
                    idx,
                )
                merged_elements.append(merged)
                idx += 1

        detection_only_count = len(detection_layer.elements) - len(used_detections) + len(used_detections)
        detection_only_count = len([e for e in merged_elements if e.interpretation_id is None])

        # Phase 3: Add unmatched interpretations (interpretation-only)
        for interp in interpretation_layer.elements:
            if interp.id not in used_interpretations:
                merged = self._create_interpretation_only_element(
                    interp,
                    image_id,
                    idx,
                )
                merged_elements.append(merged)
                idx += 1

        interpretation_only_count = len([e for e in merged_elements if e.detection_id is None])
        matched_count = len([e for e in merged_elements if e.detection_id and e.interpretation_id])

        return MergedOutput(
            elements=merged_elements,
            relations=interpretation_layer.relations,  # Pass through relations
            diagram_type=interpretation_layer.diagram_type,
            diagram_description=interpretation_layer.diagram_description,
            coordinate_system=interpretation_layer.coordinate_system,
            matched_count=matched_count,
            detection_only_count=detection_only_count,
            interpretation_only_count=interpretation_only_count,
        )


# =============================================================================
# Utility Functions
# =============================================================================

def compute_overall_confidence(merged_output: MergedOutput) -> float:
    """Compute overall confidence from merged elements.

    Args:
        merged_output: Merged output with elements

    Returns:
        Average combined confidence (0.0 if no elements)
    """
    if not merged_output.elements:
        return 0.0

    confidences = [e.combined_confidence.combined_value for e in merged_output.elements]
    return sum(confidences) / len(confidences)


def get_elements_needing_review(merged_output: MergedOutput) -> List[MergedElement]:
    """Get elements that require human review.

    Args:
        merged_output: Merged output

    Returns:
        List of elements marked for review
    """
    return [e for e in merged_output.elements if e.review.review_required]


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "MergerConfig",
    "HybridMerger",
    "compute_overall_confidence",
    "get_elements_needing_review",
]
