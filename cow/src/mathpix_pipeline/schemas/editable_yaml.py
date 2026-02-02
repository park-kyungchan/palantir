"""
Editable YAML Schema for Export Enhancement.

Defines schemas for the editable intermediate YAML format used in
the round-trip pipeline:
- RegenerationSpec → YAML → Manual Editing → PDF

This schema enables:
- Position and style editing
- Version tracking
- Human review integration
- PDF regeneration

Schema Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from .common import MathpixBaseModel, utc_now


# =============================================================================
# Enums
# =============================================================================

class CoordinateUnit(str, Enum):
    """Coordinate system units for position specification."""
    MM = "mm"  # Millimeters (default)
    PT = "pt"  # Points (1/72 inch)
    PX = "px"  # Pixels
    IN = "in"  # Inches


# =============================================================================
# Position and Style Models
# =============================================================================

class Position(MathpixBaseModel):
    """Position specification for elements in editable YAML.

    Coordinates are relative to page origin (top-left for PDF).
    All values must be positive.
    """
    x: float = Field(..., ge=0.0, description="X coordinate")
    y: float = Field(..., ge=0.0, description="Y coordinate")
    width: float = Field(..., gt=0.0, description="Width of element")
    height: float = Field(..., gt=0.0, description="Height of element")
    unit: CoordinateUnit = Field(
        default=CoordinateUnit.MM,
        description="Coordinate unit"
    )


class StyleSpec(MathpixBaseModel):
    """Style specification for text and equations.

    Defines font, size, color, and text styling options.
    """
    font_family: Optional[str] = Field(
        default="Latin Modern Math",
        description="Font family name"
    )
    font_size: float = Field(
        default=12.0,
        gt=0.0,
        description="Font size"
    )
    font_size_unit: str = Field(
        default="pt",
        description="Font size unit (pt, px)"
    )
    color: str = Field(
        default="#000000",
        description="Text color (hex)"
    )
    bold: bool = Field(default=False, description="Bold text")
    italic: bool = Field(default=False, description="Italic text")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Ensure color is valid hex format."""
        if not v.startswith("#"):
            v = f"#{v}"
        if len(v) not in (4, 7):  # #RGB or #RRGGBB
            raise ValueError(f"Invalid hex color: {v}")
        return v


# =============================================================================
# Element Model
# =============================================================================

class EditableElement(MathpixBaseModel):
    """A single editable element in the YAML document.

    Represents an equation, text, figure, or other content
    with position, style, and editability metadata.
    """
    element_id: str = Field(..., description="Unique element identifier")
    element_type: str = Field(
        ...,
        description="Type: equation, text, figure, etc."
    )
    latex: Optional[str] = Field(
        default=None,
        description="LaTeX content for equations"
    )
    text: Optional[str] = Field(
        default=None,
        description="Plain text content"
    )
    position: Position = Field(..., description="Element position on page")
    style: StyleSpec = Field(
        default_factory=StyleSpec,
        description="Style specification"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Element confidence score"
    )
    editable: bool = Field(
        default=True,
        description="Whether element can be edited"
    )
    source_node_id: Optional[str] = Field(
        default=None,
        description="SemanticGraph node reference"
    )


# =============================================================================
# Version Tracking
# =============================================================================

class VersionInfo(MathpixBaseModel):
    """Version tracking metadata for YAML documents.

    Enables git-style versioning with change tracking.
    """
    version_id: str = Field(..., description="Unique version identifier")
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Version creation time"
    )
    created_by: str = Field(
        default="system",
        description="Creator identifier"
    )
    parent_version_id: Optional[str] = Field(
        default=None,
        description="Previous version ID"
    )
    change_summary: str = Field(
        default="",
        description="Human-readable change description"
    )
    changes_count: int = Field(
        default=0,
        ge=0,
        description="Number of changes from parent"
    )


# =============================================================================
# Page Layout
# =============================================================================

class PageLayout(MathpixBaseModel):
    """Page layout configuration for PDF generation.

    Defines page size and margins.
    """
    page_size: str = Field(
        default="A4",
        description="Page size (A4, Letter, etc.)"
    )
    margins: Dict[str, float] = Field(
        default_factory=lambda: {
            "top": 25.0,
            "bottom": 25.0,
            "left": 25.0,
            "right": 25.0,
        },
        description="Page margins (top, bottom, left, right)"
    )
    margin_unit: CoordinateUnit = Field(
        default=CoordinateUnit.MM,
        description="Margin unit"
    )


# =============================================================================
# Main Schema
# =============================================================================

class EditableYAMLSpec(MathpixBaseModel):
    """Top-level schema for editable YAML documents.

    This is the main schema exported from RegenerationSpec and
    used for manual editing and PDF regeneration.

    Example YAML structure:
    ```yaml
    schema_version: "1.0.0"
    image_id: "img_12345"
    source_regeneration_id: "regen_67890"
    version_info:
      version_id: "v1_20260202_120000"
      created_at: "2026-02-02T12:00:00Z"
    elements:
      - element_id: "eq_1"
        element_type: "equation"
        latex: "x^2 + y^2 = r^2"
        position:
          x: 50.0
          y: 100.0
          width: 80.0
          height: 20.0
          unit: mm
    page_layout:
      page_size: "A4"
      margins:
        top: 25.0
        bottom: 25.0
        left: 25.0
        right: 25.0
    ```
    """
    schema_version: str = Field(
        default="1.0.0",
        description="Schema version"
    )
    image_id: str = Field(..., description="Source image identifier")
    source_regeneration_id: str = Field(
        ...,
        description="RegenerationSpec reference"
    )
    version_info: VersionInfo = Field(..., description="Version metadata")
    elements: List[EditableElement] = Field(
        default_factory=list,
        description="Editable elements"
    )
    page_layout: PageLayout = Field(
        default_factory=PageLayout,
        description="Page layout config"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "CoordinateUnit",
    # Models
    "Position",
    "StyleSpec",
    "EditableElement",
    "VersionInfo",
    "PageLayout",
    # Main Schema
    "EditableYAMLSpec",
]
