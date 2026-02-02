"""
YAML Exporter for Stage H (Export).

Exports pipeline results to editable YAML format with support for:
- Round-trip editing (YAML → PDF regeneration)
- Position and styling information
- Version tracking metadata
- Human-readable formatting

Module Version: 1.0.0
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from ...schemas.editable_yaml import (
    CoordinateUnit,
    EditableElement,
    EditableYAMLSpec,
    PageLayout,
    Position,
    StyleSpec,
    VersionInfo,
)
from ...schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportSpec,
)
from ..exceptions import ExportError
from .base import BaseExporter, ExporterConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class YAMLExporterConfig(ExporterConfig):
    """Configuration for YAML exporter.

    Attributes:
        include_positions: Extract position info from SemanticGraph nodes
        include_styling: Include font and style information
        literal_block_threshold: Use literal block (|) if text exceeds this length
        preserve_key_order: Preserve YAML key order in output
        editable_fields: List of fields marked as editable
        default_coordinate_unit: Default unit for coordinates
    """
    include_positions: bool = True
    include_styling: bool = True
    literal_block_threshold: int = 40
    preserve_key_order: bool = True
    editable_fields: List[str] = field(
        default_factory=lambda: ["latex", "text", "position", "style"]
    )
    default_coordinate_unit: str = "mm"


# =============================================================================
# YAML Serializer Helper
# =============================================================================

def _serialize_to_yaml(data: Dict[str, Any], literal_threshold: int = 40) -> str:
    """Serialize dictionary to YAML string.

    Uses ruamel.yaml if available for better formatting,
    falls back to PyYAML otherwise.

    Args:
        data: Dictionary to serialize
        literal_threshold: Use literal block for strings exceeding this length

    Returns:
        YAML string
    """
    try:
        from ruamel.yaml import YAML
        from io import StringIO

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)

        stream = StringIO()
        yaml.dump(data, stream)
        return stream.getvalue()

    except ImportError:
        import yaml

        def literal_presenter(dumper, data):
            if len(data) > literal_threshold and "\n" in data:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        yaml.add_representer(str, literal_presenter)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


# =============================================================================
# YAML Exporter
# =============================================================================

class YAMLExporter(BaseExporter[YAMLExporterConfig]):
    """Export pipeline results to editable YAML format.

    Converts RegenerationSpec to EditableYAMLSpec for human editing.
    Supports round-trip pipeline: YAML → Edit → PDF regeneration.

    Usage:
        exporter = YAMLExporter()
        spec = exporter.export(regeneration_spec, options, "img_123")

        # Or export to bytes
        yaml_bytes = exporter.export_to_bytes(data, options)
    """

    def _default_config(self) -> YAMLExporterConfig:
        """Create default configuration."""
        return YAMLExporterConfig()

    @property
    def format(self) -> ExportFormat:
        """Get export format."""
        return ExportFormat.YAML

    @property
    def content_type(self) -> str:
        """Get MIME content type."""
        return "application/x-yaml"

    def _build_editable_spec(
        self,
        data: Any,
        options: ExportOptions,
    ) -> EditableYAMLSpec:
        """Convert input data to EditableYAMLSpec.

        Args:
            data: RegenerationSpec or similar data structure
            options: Export options

        Returns:
            EditableYAMLSpec ready for serialization
        """
        # Extract image_id
        image_id = getattr(data, "image_id", "unknown")

        # Generate version info
        version_id = f"v1_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        version_info = VersionInfo(
            version_id=version_id,
            created_at=datetime.now(timezone.utc),
            created_by="system",
            change_summary="Initial export from pipeline",
            changes_count=0,
        )

        # Convert elements
        elements = self._extract_elements(data, options)

        # Build page layout from options
        page_layout = self._build_page_layout(options)

        # Create spec
        source_id = getattr(data, "regeneration_id", str(uuid.uuid4())[:12])

        return EditableYAMLSpec(
            schema_version="1.0.0",
            image_id=image_id,
            source_regeneration_id=source_id,
            version_info=version_info,
            elements=elements,
            page_layout=page_layout,
            metadata={
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "exporter_version": "1.0.0",
                "yaml_options": options.yaml_options,
            },
        )

    def _extract_elements(
        self,
        data: Any,
        options: ExportOptions,
    ) -> List[EditableElement]:
        """Extract editable elements from source data.

        Args:
            data: Source data (RegenerationSpec, etc.)
            options: Export options

        Returns:
            List of EditableElement
        """
        elements = []

        # Handle RegenerationSpec with element_results
        if hasattr(data, "element_results"):
            for idx, elem in enumerate(data.element_results):
                element = self._convert_element_result(elem, idx, options)
                if element:
                    elements.append(element)

        # Handle SemanticGraph with nodes
        elif hasattr(data, "nodes"):
            for idx, node in enumerate(data.nodes):
                element = self._convert_semantic_node(node, idx, options)
                if element:
                    elements.append(element)

        # Handle list of elements directly
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                element = self._convert_generic_element(item, idx, options)
                if element:
                    elements.append(element)

        return elements

    def _convert_element_result(
        self,
        elem: Any,
        idx: int,
        options: ExportOptions,
    ) -> Optional[EditableElement]:
        """Convert an element result to EditableElement.

        Args:
            elem: Source element
            idx: Element index
            options: Export options

        Returns:
            EditableElement or None if conversion fails
        """
        try:
            element_id = getattr(elem, "element_id", f"elem_{idx:04d}")
            element_type = getattr(elem, "element_type", "unknown")

            # Extract content
            latex = getattr(elem, "latex", None)
            text = getattr(elem, "text", None)

            # Extract position
            position = self._extract_position(elem, options)

            # Extract style
            style = self._extract_style(elem) if self.config.include_styling else StyleSpec()

            # Confidence
            confidence = getattr(elem, "confidence", 1.0)
            if hasattr(confidence, "value"):
                confidence = confidence.value

            return EditableElement(
                element_id=element_id,
                element_type=element_type,
                latex=latex,
                text=text,
                position=position,
                style=style,
                confidence=float(confidence) if confidence else 1.0,
                editable=True,
                source_node_id=getattr(elem, "node_id", None),
            )

        except Exception as e:
            logger.warning(f"Failed to convert element {idx}: {e}")
            return None

    def _convert_semantic_node(
        self,
        node: Any,
        idx: int,
        options: ExportOptions,
    ) -> Optional[EditableElement]:
        """Convert a semantic graph node to EditableElement.

        Args:
            node: SemanticNode
            idx: Node index
            options: Export options

        Returns:
            EditableElement or None
        """
        try:
            node_id = getattr(node, "node_id", f"node_{idx:04d}")
            node_type = getattr(node, "node_type", "unknown")

            # Map node_type to element_type
            type_map = {
                "EQUATION": "equation",
                "TEXT": "text",
                "FIGURE": "figure",
                "TABLE": "table",
            }
            element_type = type_map.get(str(node_type), str(node_type).lower())

            # Extract properties
            props = getattr(node, "properties", {})
            if hasattr(props, "model_dump"):
                props = props.model_dump()

            latex = props.get("latex")
            text = props.get("text")

            # Position from bbox
            position = self._extract_position(node, options)

            return EditableElement(
                element_id=node_id,
                element_type=element_type,
                latex=latex,
                text=text,
                position=position,
                style=StyleSpec(),
                confidence=props.get("confidence", 1.0),
                editable=True,
                source_node_id=node_id,
            )

        except Exception as e:
            logger.warning(f"Failed to convert node {idx}: {e}")
            return None

    def _convert_generic_element(
        self,
        item: Any,
        idx: int,
        options: ExportOptions,
    ) -> Optional[EditableElement]:
        """Convert a generic item to EditableElement.

        Args:
            item: Generic item (dict or object)
            idx: Item index
            options: Export options

        Returns:
            EditableElement or None
        """
        try:
            if isinstance(item, dict):
                data = item
            elif hasattr(item, "model_dump"):
                data = item.model_dump()
            else:
                data = {"content": str(item)}

            return EditableElement(
                element_id=data.get("id", f"item_{idx:04d}"),
                element_type=data.get("type", "unknown"),
                latex=data.get("latex"),
                text=data.get("text", data.get("content")),
                position=Position(x=0, y=idx * 20.0, width=100, height=20),
                style=StyleSpec(),
                confidence=data.get("confidence", 1.0),
                editable=True,
            )

        except Exception as e:
            logger.warning(f"Failed to convert item {idx}: {e}")
            return None

    def _extract_position(self, elem: Any, options: ExportOptions) -> Position:
        """Extract position from element.

        Args:
            elem: Source element with bbox or position info
            options: Export options

        Returns:
            Position object
        """
        if not self.config.include_positions:
            return Position(x=0, y=0, width=100, height=20)

        # Check for bbox attribute
        bbox = getattr(elem, "bbox", None)
        if bbox:
            if hasattr(bbox, "model_dump"):
                bbox = bbox.model_dump()
            elif hasattr(bbox, "__dict__"):
                bbox = bbox.__dict__

            if isinstance(bbox, dict):
                return Position(
                    x=float(bbox.get("x", 0)),
                    y=float(bbox.get("y", 0)),
                    width=float(bbox.get("width", 100)),
                    height=float(bbox.get("height", 20)),
                    unit=CoordinateUnit(self.config.default_coordinate_unit),
                )

        # Check for position attribute
        pos = getattr(elem, "position", None)
        if pos and isinstance(pos, dict):
            return Position(
                x=float(pos.get("x", 0)),
                y=float(pos.get("y", 0)),
                width=float(pos.get("width", 100)),
                height=float(pos.get("height", 20)),
                unit=CoordinateUnit(pos.get("unit", self.config.default_coordinate_unit)),
            )

        # Default position
        return Position(x=0, y=0, width=100, height=20)

    def _extract_style(self, elem: Any) -> StyleSpec:
        """Extract style from element.

        Args:
            elem: Source element with style info

        Returns:
            StyleSpec object
        """
        style = getattr(elem, "style", None)
        if style:
            if hasattr(style, "model_dump"):
                style_dict = style.model_dump()
            elif isinstance(style, dict):
                style_dict = style
            else:
                return StyleSpec()

            return StyleSpec(
                font_family=style_dict.get("font_family", "Latin Modern Math"),
                font_size=float(style_dict.get("font_size", 12.0)),
                color=style_dict.get("color", "#000000"),
                bold=style_dict.get("bold", False),
                italic=style_dict.get("italic", False),
            )

        return StyleSpec()

    def _build_page_layout(self, options: ExportOptions) -> PageLayout:
        """Build page layout from export options.

        Args:
            options: Export options

        Returns:
            PageLayout object
        """
        pdf_opts = options.pdf_options
        yaml_opts = options.yaml_options

        page_size = pdf_opts.get("page_size", "A4")
        if page_size == "letter":
            page_size = "Letter"

        margins = pdf_opts.get("margins", {})
        margin_dict = {
            "top": float(margins.get("top", 25.0)),
            "bottom": float(margins.get("bottom", 25.0)),
            "left": float(margins.get("left", 25.0)),
            "right": float(margins.get("right", 25.0)),
        }

        unit = yaml_opts.get("coordinate_unit", "mm")

        return PageLayout(
            page_size=page_size,
            margins=margin_dict,
            margin_unit=CoordinateUnit(unit),
        )

    def export_to_bytes(
        self,
        data: Any,
        options: ExportOptions,
    ) -> bytes:
        """Export data to YAML bytes.

        Args:
            data: Data to export
            options: Export options

        Returns:
            YAML content as bytes
        """
        # Build editable spec
        editable_spec = self._build_editable_spec(data, options)

        # Serialize to dictionary
        spec_dict = editable_spec.model_dump(mode="json")

        # Convert to YAML string
        yaml_str = _serialize_to_yaml(spec_dict, self.config.literal_block_threshold)

        return yaml_str.encode("utf-8")

    def export(
        self,
        data: Any,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export data to YAML file.

        Args:
            data: Data to export (RegenerationSpec, etc.)
            options: Export options
            image_id: Source image identifier

        Returns:
            ExportSpec with export metadata
        """
        start_time = time.time()

        # Generate identifiers
        export_id = self._generate_export_id(image_id)
        filename = self._generate_filename(image_id, options)
        filepath = self.config.output_dir / filename

        # Check existing file
        if filepath.exists() and not self.config.overwrite_existing:
            filepath = filepath.with_stem(f"{filepath.stem}_{export_id[:6]}")

        # Serialize and write
        try:
            yaml_bytes = self.export_to_bytes(data, options)
            checksum = self._calculate_checksum(yaml_bytes)
            file_size = self._write_file(yaml_bytes, filepath)

        except Exception as e:
            self._stats["exports_failed"] += 1
            raise ExportError(
                f"YAML export failed: {e}",
                details={"image_id": image_id, "path": str(filepath)},
            )

        # Count elements
        element_count = 0
        if hasattr(data, "element_results"):
            element_count = len(data.element_results)
        elif hasattr(data, "nodes"):
            element_count = len(data.nodes)

        processing_time = (time.time() - start_time) * 1000

        self._stats["exports_completed"] += 1

        logger.info(
            f"YAML export completed: {filepath}, "
            f"size={file_size} bytes, elements={element_count}, "
            f"time={processing_time:.1f}ms"
        )

        return self._create_export_spec(
            export_id=export_id,
            image_id=image_id,
            filepath=filepath,
            file_size=file_size,
            checksum=checksum,
            element_count=element_count,
            processing_time_ms=processing_time,
        )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "YAMLExporter",
    "YAMLExporterConfig",
]
