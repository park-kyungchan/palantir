"""
YAML Diff Parser for Human Review Integration.

Bidirectional conversion between:
- DeepDiff results → Correction list (for feedback recording)
- Correction list → YAML patches (for review application)

Module Version: 1.0.0
"""

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..human_review.models.annotation import (
    Correction,
    CorrectionType,
)
from ..schemas.common import BBox
from ..schemas.editable_yaml import EditableYAMLSpec, Position

logger = logging.getLogger(__name__)


# =============================================================================
# Path Parser
# =============================================================================

@dataclass
class ParsedPath:
    """Parsed DeepDiff path information."""
    element_index: Optional[int] = None
    field_path: str = ""
    is_element_operation: bool = False
    operation_type: Optional[str] = None  # 'add', 'remove', 'modify'


def parse_diff_path(path: str) -> ParsedPath:
    """Parse DeepDiff path to extract element index and field.

    Args:
        path: DeepDiff path (e.g., "root['elements'][0]['latex']")

    Returns:
        ParsedPath with extracted information

    Examples:
        "root['elements'][0]['latex']" → element_index=0, field_path="latex"
        "root['elements'][1]['position']['x']" → element_index=1, field_path="position.x"
        "root['page_layout']['margins']['top']" → element_index=None, field_path="page_layout.margins.top"
    """
    result = ParsedPath()

    # Match element index pattern
    element_match = re.search(r"\['elements'\]\[(\d+)\]", path)
    if element_match:
        result.element_index = int(element_match.group(1))

        # Extract field path after elements[N]
        field_part = re.sub(r".*\['elements'\]\[\d+\]", "", path)
        # Convert ['field'] to field
        result.field_path = re.sub(r"\['([^']+)'\]", r".\1", field_part).strip(".")

    else:
        # Not an element path - could be page_layout, metadata, etc.
        field_part = path.replace("root", "")
        result.field_path = re.sub(r"\['([^']+)'\]", r".\1", field_part).strip(".")

    return result


def map_field_to_correction_type(field_path: str) -> CorrectionType:
    """Map field path to CorrectionType.

    Args:
        field_path: Field path (e.g., "latex", "position.x", "element_type")

    Returns:
        Appropriate CorrectionType
    """
    field_lower = field_path.lower()

    # Content corrections
    if field_lower == "latex":
        return CorrectionType.LATEX_CORRECTION
    if field_lower == "text":
        return CorrectionType.TEXT_CORRECTION

    # Position/BBox corrections
    if field_lower.startswith("position"):
        return CorrectionType.BBOX_ADJUSTMENT

    # Type corrections
    if field_lower == "element_type":
        return CorrectionType.TYPE_CHANGE

    # Confidence corrections
    if field_lower == "confidence":
        return CorrectionType.CONFIDENCE_OVERRIDE

    # Style is treated as text correction
    if field_lower.startswith("style"):
        return CorrectionType.TEXT_CORRECTION

    # Default
    return CorrectionType.TEXT_CORRECTION


# =============================================================================
# YAML Diff Parser
# =============================================================================

class YAMLDiffParser:
    """Parse YAML diffs to Corrections and vice versa.

    Usage:
        parser = YAMLDiffParser()

        # DeepDiff → Corrections
        corrections = parser.diff_to_corrections(deepdiff_result, yaml_spec)

        # Corrections → YAML patches
        patches = parser.corrections_to_patches(corrections, yaml_spec)
    """

    def __init__(self, reviewer_id: str = "yaml_editor"):
        """Initialize parser.

        Args:
            reviewer_id: Default reviewer identifier for generated corrections
        """
        self.reviewer_id = reviewer_id

    def diff_to_corrections(
        self,
        diff: Dict[str, Any],
        yaml_spec: EditableYAMLSpec,
        reviewer_id: Optional[str] = None,
    ) -> List[Correction]:
        """Convert DeepDiff result to Correction list.

        Args:
            diff: DeepDiff result (or dict representation)
            yaml_spec: Current YAML spec (for element ID lookup)
            reviewer_id: Optional override for reviewer ID

        Returns:
            List of Correction objects
        """
        corrections = []
        reviewer = reviewer_id or self.reviewer_id

        # Handle values_changed
        values_changed = diff.get("values_changed", {})
        for path, change in values_changed.items():
            correction = self._create_value_change_correction(
                path, change, yaml_spec, reviewer
            )
            if correction:
                corrections.append(correction)

        # Handle iterable_item_added (new elements)
        items_added = diff.get("iterable_item_added", {})
        for path, value in items_added.items():
            correction = self._create_add_correction(
                path, value, yaml_spec, reviewer
            )
            if correction:
                corrections.append(correction)

        # Handle iterable_item_removed (deleted elements)
        items_removed = diff.get("iterable_item_removed", {})
        for path, value in items_removed.items():
            correction = self._create_remove_correction(
                path, value, yaml_spec, reviewer
            )
            if correction:
                corrections.append(correction)

        # Handle dictionary_item_added
        dict_added = diff.get("dictionary_item_added", {})
        for path, value in dict_added.items():
            correction = self._create_value_change_correction(
                path, {"old_value": None, "new_value": value},
                yaml_spec, reviewer
            )
            if correction:
                corrections.append(correction)

        # Handle dictionary_item_removed
        dict_removed = diff.get("dictionary_item_removed", {})
        for path, value in dict_removed.items():
            correction = self._create_value_change_correction(
                path, {"old_value": value, "new_value": None},
                yaml_spec, reviewer
            )
            if correction:
                corrections.append(correction)

        logger.info(f"Generated {len(corrections)} corrections from diff")
        return corrections

    def _create_value_change_correction(
        self,
        path: str,
        change: Dict[str, Any],
        yaml_spec: EditableYAMLSpec,
        reviewer_id: str,
    ) -> Optional[Correction]:
        """Create correction for a value change.

        Args:
            path: DeepDiff path
            change: Change dict with old_value and new_value
            yaml_spec: YAML spec for element lookup
            reviewer_id: Reviewer identifier

        Returns:
            Correction object or None if not applicable
        """
        try:
            parsed = parse_diff_path(path)

            # Get element ID
            element_id = "global"
            if parsed.element_index is not None:
                if 0 <= parsed.element_index < len(yaml_spec.elements):
                    element_id = yaml_spec.elements[parsed.element_index].element_id
                else:
                    logger.warning(f"Element index out of range: {parsed.element_index}")
                    return None

            # Get values
            old_value = change.get("old_value") or change.get("t1")
            new_value = change.get("new_value") or change.get("t2")

            # Map to correction type
            correction_type = map_field_to_correction_type(parsed.field_path)

            # Handle special cases
            confidence_override = None
            if correction_type == CorrectionType.CONFIDENCE_OVERRIDE:
                confidence_override = float(new_value) if new_value else None

            original_bbox = None
            corrected_bbox = None
            if correction_type == CorrectionType.BBOX_ADJUSTMENT:
                original_bbox, corrected_bbox = self._extract_bbox_changes(
                    parsed, old_value, new_value, yaml_spec
                )

            return Correction(
                correction_id=f"yaml-{uuid.uuid4().hex[:8]}",
                correction_type=correction_type,
                element_id=element_id,
                field_name=parsed.field_path or "unknown",
                original_value=old_value,
                corrected_value=new_value,
                confidence_override=confidence_override,
                original_bbox=original_bbox,
                corrected_bbox=corrected_bbox,
                reason="YAML edit",
                notes=f"Changed via YAML editor at path: {path}",
                created_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.warning(f"Failed to create correction for {path}: {e}")
            return None

    def _create_add_correction(
        self,
        path: str,
        value: Any,
        yaml_spec: EditableYAMLSpec,
        reviewer_id: str,
    ) -> Optional[Correction]:
        """Create correction for added element.

        Args:
            path: DeepDiff path
            value: Added value
            yaml_spec: YAML spec
            reviewer_id: Reviewer identifier

        Returns:
            Correction for ADD_ELEMENT
        """
        try:
            # Check if this is an element addition
            if "elements" not in path:
                return None

            element_id = f"new-{uuid.uuid4().hex[:8]}"
            if isinstance(value, dict):
                element_id = value.get("element_id", element_id)

            return Correction(
                correction_id=f"yaml-{uuid.uuid4().hex[:8]}",
                correction_type=CorrectionType.ADD_ELEMENT,
                element_id=element_id,
                field_name="elements",
                original_value=None,
                corrected_value=value,
                reason="Element added",
                notes=f"New element via YAML editor at path: {path}",
                created_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.warning(f"Failed to create add correction for {path}: {e}")
            return None

    def _create_remove_correction(
        self,
        path: str,
        value: Any,
        yaml_spec: EditableYAMLSpec,
        reviewer_id: str,
    ) -> Optional[Correction]:
        """Create correction for removed element.

        Args:
            path: DeepDiff path
            value: Removed value
            yaml_spec: YAML spec
            reviewer_id: Reviewer identifier

        Returns:
            Correction for DELETE_ELEMENT
        """
        try:
            if "elements" not in path:
                return None

            element_id = "unknown"
            if isinstance(value, dict):
                element_id = value.get("element_id", element_id)

            return Correction(
                correction_id=f"yaml-{uuid.uuid4().hex[:8]}",
                correction_type=CorrectionType.DELETE_ELEMENT,
                element_id=element_id,
                field_name="elements",
                original_value=value,
                corrected_value=None,
                reason="Element deleted",
                notes=f"Element removed via YAML editor at path: {path}",
                created_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.warning(f"Failed to create remove correction for {path}: {e}")
            return None

    def _extract_bbox_changes(
        self,
        parsed: ParsedPath,
        old_value: Any,
        new_value: Any,
        yaml_spec: EditableYAMLSpec,
    ) -> Tuple[Optional[BBox], Optional[BBox]]:
        """Extract BBox changes from position modification.

        Args:
            parsed: Parsed path
            old_value: Old value
            new_value: New value
            yaml_spec: YAML spec

        Returns:
            Tuple of (original_bbox, corrected_bbox)
        """
        try:
            if parsed.element_index is None:
                return None, None

            element = yaml_spec.elements[parsed.element_index]
            pos = element.position

            # Create current bbox from position
            original_bbox = BBox(
                x=pos.x,
                y=pos.y,
                width=pos.width,
                height=pos.height,
            )

            # Determine which field changed and create corrected bbox
            corrected_bbox = BBox(
                x=pos.x,
                y=pos.y,
                width=pos.width,
                height=pos.height,
            )

            field = parsed.field_path.split(".")[-1]
            if field == "x":
                corrected_bbox = BBox(x=float(new_value), y=pos.y, width=pos.width, height=pos.height)
            elif field == "y":
                corrected_bbox = BBox(x=pos.x, y=float(new_value), width=pos.width, height=pos.height)
            elif field == "width":
                corrected_bbox = BBox(x=pos.x, y=pos.y, width=float(new_value), height=pos.height)
            elif field == "height":
                corrected_bbox = BBox(x=pos.x, y=pos.y, width=pos.width, height=float(new_value))

            return original_bbox, corrected_bbox

        except Exception as e:
            logger.warning(f"Failed to extract bbox changes: {e}")
            return None, None

    def corrections_to_patches(
        self,
        corrections: List[Correction],
        yaml_spec: EditableYAMLSpec,
    ) -> List[Dict[str, Any]]:
        """Convert Corrections to YAML patch operations.

        Args:
            corrections: List of corrections to apply
            yaml_spec: Current YAML spec

        Returns:
            List of patch operations (can be applied to YAML)
        """
        patches = []

        for correction in corrections:
            patch = self._correction_to_patch(correction, yaml_spec)
            if patch:
                patches.append(patch)

        return patches

    def _correction_to_patch(
        self,
        correction: Correction,
        yaml_spec: EditableYAMLSpec,
    ) -> Optional[Dict[str, Any]]:
        """Convert single Correction to patch operation.

        Args:
            correction: Correction to convert
            yaml_spec: Current YAML spec

        Returns:
            Patch operation dict
        """
        # Find element index
        element_idx = None
        for idx, elem in enumerate(yaml_spec.elements):
            if elem.element_id == correction.element_id:
                element_idx = idx
                break

        if correction.correction_type == CorrectionType.DELETE_ELEMENT:
            return {
                "operation": "delete",
                "path": f"elements[{element_idx}]" if element_idx is not None else None,
                "element_id": correction.element_id,
            }

        if correction.correction_type == CorrectionType.ADD_ELEMENT:
            return {
                "operation": "add",
                "path": "elements",
                "value": correction.corrected_value,
            }

        if element_idx is None:
            return None

        # Value modification
        return {
            "operation": "modify",
            "path": f"elements[{element_idx}].{correction.field_name}",
            "element_id": correction.element_id,
            "field": correction.field_name,
            "old_value": correction.original_value,
            "new_value": correction.corrected_value,
        }

    def apply_patches(
        self,
        patches: List[Dict[str, Any]],
        yaml_spec: EditableYAMLSpec,
    ) -> EditableYAMLSpec:
        """Apply patch operations to YAML spec.

        Args:
            patches: List of patch operations
            yaml_spec: YAML spec to modify

        Returns:
            Modified EditableYAMLSpec
        """
        # Create a mutable copy
        spec_dict = yaml_spec.model_dump()

        for patch in patches:
            try:
                op = patch.get("operation")

                if op == "delete":
                    element_id = patch.get("element_id")
                    spec_dict["elements"] = [
                        e for e in spec_dict["elements"]
                        if e.get("element_id") != element_id
                    ]

                elif op == "add":
                    spec_dict["elements"].append(patch.get("value", {}))

                elif op == "modify":
                    element_id = patch.get("element_id")
                    field = patch.get("field")
                    new_value = patch.get("new_value")

                    for elem in spec_dict["elements"]:
                        if elem.get("element_id") == element_id:
                            self._set_nested_value(elem, field, new_value)
                            break

            except Exception as e:
                logger.warning(f"Failed to apply patch: {patch}, error: {e}")

        return EditableYAMLSpec(**spec_dict)

    def _set_nested_value(
        self,
        obj: Dict[str, Any],
        path: str,
        value: Any,
    ) -> None:
        """Set nested value in dictionary.

        Args:
            obj: Dictionary to modify
            path: Dot-separated path (e.g., "position.x")
            value: Value to set
        """
        parts = path.split(".")
        for part in parts[:-1]:
            obj = obj.setdefault(part, {})
        obj[parts[-1]] = value


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "ParsedPath",
    "YAMLDiffParser",
    "map_field_to_correction_type",
    "parse_diff_path",
]
