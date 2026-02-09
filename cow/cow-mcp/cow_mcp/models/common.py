"""Shared types used across all stage models."""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class BBox(BaseModel):
    """Axis-aligned bounding box in pixel coordinates."""
    x: int = Field(..., ge=0, description="Top-left X")
    y: int = Field(..., ge=0, description="Top-left Y")
    width: int = Field(..., ge=1, description="Width in pixels")
    height: int = Field(..., ge=1, description="Height in pixels")

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


class Dimensions(BaseModel):
    """Image or page dimensions."""
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)


class SessionInfo(BaseModel):
    """Session metadata."""
    session_id: str
    created_at: str  # ISO 8601
    source_path: str
    source_type: Literal["image", "pdf"]
    page_count: int = 1


class RegionSource(str, Enum):
    """Origin of a detected region."""
    MATHPIX = "mathpix"
    GEMINI = "gemini"
    MERGED = "merged"
