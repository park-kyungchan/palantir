"""
YAML Parser for Stage H (Export).

Parses editable YAML files back to EditableYAMLSpec objects.
Supports the round-trip pipeline: YAML → Parse → Validate → Regenerate PDF.

Module Version: 1.0.0
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..schemas.editable_yaml import (
    CoordinateUnit,
    EditableElement,
    EditableYAMLSpec,
    PageLayout,
    Position,
    StyleSpec,
    VersionInfo,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class YAMLParseError(Exception):
    """Error during YAML parsing."""

    def __init__(self, message: str, line: Optional[int] = None, details: Optional[Dict] = None):
        self.message = message
        self.line = line
        self.details = details or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        msg = self.message
        if self.line:
            msg = f"Line {self.line}: {msg}"
        return msg


# =============================================================================
# YAML Parser
# =============================================================================

class YAMLParser:
    """Parse YAML content to EditableYAMLSpec.

    Supports parsing from strings, files, and raw dictionaries.

    Usage:
        parser = YAMLParser()

        # Parse from file
        spec = parser.parse_file(Path("document.yaml"))

        # Parse from string
        spec = parser.parse_string(yaml_content)

        # Parse from dict (already loaded)
        spec = parser.parse_dict(yaml_dict)
    """

    def __init__(self, strict: bool = False):
        """Initialize parser.

        Args:
            strict: If True, raise errors on unknown fields. Default False.
        """
        self.strict = strict

    def parse_file(self, filepath: Union[str, Path]) -> EditableYAMLSpec:
        """Parse YAML file to EditableYAMLSpec.

        Args:
            filepath: Path to YAML file

        Returns:
            Parsed EditableYAMLSpec

        Raises:
            YAMLParseError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"YAML file not found: {filepath}")

        try:
            content = filepath.read_text(encoding="utf-8")
            return self.parse_string(content)

        except YAMLParseError:
            raise
        except Exception as e:
            raise YAMLParseError(
                f"Failed to read file: {e}",
                details={"path": str(filepath)},
            )

    def parse_string(self, content: str) -> EditableYAMLSpec:
        """Parse YAML string to EditableYAMLSpec.

        Args:
            content: YAML content string

        Returns:
            Parsed EditableYAMLSpec

        Raises:
            YAMLParseError: If parsing fails
        """
        try:
            data = self._load_yaml(content)
            return self.parse_dict(data)

        except YAMLParseError:
            raise
        except Exception as e:
            raise YAMLParseError(f"YAML parse error: {e}")

    def parse_raw(self, content: str) -> EditableYAMLSpec:
        """Alias for parse_string.

        Args:
            content: YAML content string

        Returns:
            Parsed EditableYAMLSpec
        """
        return self.parse_string(content)

    def parse_dict(self, data: Dict[str, Any]) -> EditableYAMLSpec:
        """Parse dictionary to EditableYAMLSpec.

        Args:
            data: Dictionary (from YAML load)

        Returns:
            Parsed EditableYAMLSpec

        Raises:
            YAMLParseError: If required fields are missing or invalid
        """
        try:
            # Validate required fields
            self._validate_required_fields(data)

            # Parse version_info
            version_info = self._parse_version_info(data.get("version_info", {}))

            # Parse elements
            elements = self._parse_elements(data.get("elements", []))

            # Parse page_layout
            page_layout = self._parse_page_layout(data.get("page_layout", {}))

            return EditableYAMLSpec(
                schema_version=data.get("schema_version", "1.0.0"),
                image_id=data["image_id"],
                source_regeneration_id=data["source_regeneration_id"],
                version_info=version_info,
                elements=elements,
                page_layout=page_layout,
                metadata=data.get("metadata", {}),
            )

        except YAMLParseError:
            raise
        except Exception as e:
            raise YAMLParseError(f"Failed to parse spec: {e}")

    def _load_yaml(self, content: str) -> Dict[str, Any]:
        """Load YAML content to dictionary.

        Uses ruamel.yaml if available, falls back to PyYAML.

        Args:
            content: YAML string

        Returns:
            Parsed dictionary
        """
        try:
            from ruamel.yaml import YAML
            from io import StringIO

            yaml = YAML()
            yaml.preserve_quotes = True
            result = yaml.load(StringIO(content))
            return dict(result) if result else {}

        except ImportError:
            import yaml
            return yaml.safe_load(content) or {}

    def _validate_required_fields(self, data: Dict[str, Any]) -> None:
        """Validate required fields are present.

        Args:
            data: Dictionary to validate

        Raises:
            YAMLParseError: If required fields are missing
        """
        required = ["image_id", "source_regeneration_id", "version_info"]

        for field in required:
            if field not in data:
                raise YAMLParseError(
                    f"Missing required field: {field}",
                    details={"required_fields": required},
                )

    def _parse_version_info(self, data: Dict[str, Any]) -> VersionInfo:
        """Parse version_info section.

        Args:
            data: version_info dictionary

        Returns:
            VersionInfo object
        """
        if not data:
            raise YAMLParseError("version_info is required")

        if "version_id" not in data:
            raise YAMLParseError("version_info.version_id is required")

        # Parse created_at
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            from datetime import datetime
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.now()
        elif created_at is None:
            from datetime import datetime
            created_at = datetime.now()

        return VersionInfo(
            version_id=data["version_id"],
            created_at=created_at,
            created_by=data.get("created_by", "system"),
            parent_version_id=data.get("parent_version_id"),
            change_summary=data.get("change_summary", ""),
            changes_count=data.get("changes_count", 0),
        )

    def _parse_elements(self, data: list) -> list:
        """Parse elements list.

        Args:
            data: List of element dictionaries

        Returns:
            List of EditableElement objects
        """
        elements = []

        for idx, elem_data in enumerate(data):
            try:
                element = self._parse_element(elem_data, idx)
                elements.append(element)
            except Exception as e:
                if self.strict:
                    raise YAMLParseError(f"Element {idx}: {e}")
                logger.warning(f"Skipping invalid element {idx}: {e}")

        return elements

    def _parse_element(self, data: Dict[str, Any], idx: int) -> EditableElement:
        """Parse single element.

        Args:
            data: Element dictionary
            idx: Element index (for error messages)

        Returns:
            EditableElement object
        """
        # Required fields
        if "element_id" not in data:
            data["element_id"] = f"elem_{idx:04d}"

        if "element_type" not in data:
            raise YAMLParseError(f"Element {idx}: missing element_type")

        # Parse position
        position = self._parse_position(data.get("position", {}))

        # Parse style
        style = self._parse_style(data.get("style", {}))

        return EditableElement(
            element_id=data["element_id"],
            element_type=data["element_type"],
            latex=data.get("latex"),
            text=data.get("text"),
            position=position,
            style=style,
            confidence=float(data.get("confidence", 1.0)),
            editable=data.get("editable", True),
            source_node_id=data.get("source_node_id"),
        )

    def _parse_position(self, data: Dict[str, Any]) -> Position:
        """Parse position object.

        Args:
            data: Position dictionary

        Returns:
            Position object
        """
        if not data:
            return Position(x=0, y=0, width=100, height=20)

        unit_str = data.get("unit", "mm")
        try:
            unit = CoordinateUnit(unit_str)
        except ValueError:
            unit = CoordinateUnit.MM

        return Position(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=float(data.get("width", 100)),
            height=float(data.get("height", 20)),
            unit=unit,
        )

    def _parse_style(self, data: Dict[str, Any]) -> StyleSpec:
        """Parse style object.

        Args:
            data: Style dictionary

        Returns:
            StyleSpec object
        """
        if not data:
            return StyleSpec()

        return StyleSpec(
            font_family=data.get("font_family", "Latin Modern Math"),
            font_size=float(data.get("font_size", 12.0)),
            font_size_unit=data.get("font_size_unit", "pt"),
            color=data.get("color", "#000000"),
            bold=data.get("bold", False),
            italic=data.get("italic", False),
        )

    def _parse_page_layout(self, data: Dict[str, Any]) -> PageLayout:
        """Parse page_layout object.

        Args:
            data: page_layout dictionary

        Returns:
            PageLayout object
        """
        if not data:
            return PageLayout()

        margins = data.get("margins", {})
        if not margins:
            margins = {"top": 25.0, "bottom": 25.0, "left": 25.0, "right": 25.0}

        margin_unit_str = data.get("margin_unit", "mm")
        try:
            margin_unit = CoordinateUnit(margin_unit_str)
        except ValueError:
            margin_unit = CoordinateUnit.MM

        return PageLayout(
            page_size=data.get("page_size", "A4"),
            margins={k: float(v) for k, v in margins.items()},
            margin_unit=margin_unit,
        )

    def validate(self, spec: EditableYAMLSpec) -> list:
        """Validate EditableYAMLSpec and return issues.

        Args:
            spec: Spec to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check required fields
        if not spec.image_id:
            issues.append("Missing image_id")

        if not spec.source_regeneration_id:
            issues.append("Missing source_regeneration_id")

        if not spec.version_info:
            issues.append("Missing version_info")

        # Check elements
        for idx, elem in enumerate(spec.elements):
            if not elem.element_id:
                issues.append(f"Element {idx}: missing element_id")
            if not elem.element_type:
                issues.append(f"Element {idx}: missing element_type")
            if elem.latex is None and elem.text is None:
                issues.append(f"Element {idx}: both latex and text are empty")

        return issues


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "YAMLParser",
    "YAMLParseError",
]
