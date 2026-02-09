"""VerificationResult for Stage 4→5 transition."""

from pydantic import BaseModel, Field
from typing import Optional, Literal

from cow_mcp.models.vision import VisionResult


class OcrCorrection(BaseModel):
    """A correction to OCR output found during verification."""
    original: str
    corrected: str
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    region_id: Optional[str] = None


class MathError(BaseModel):
    """A mathematical error detected during verification."""
    element_id: str
    error_type: Literal["typographical", "logical", "notation", "missing_term", "other"]
    description: str
    suggestion: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "medium"


class LogicIssue(BaseModel):
    """A logical issue detected in the document content."""
    location: str = Field(..., description="Description of where the issue occurs")
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    suggestion: Optional[str] = None


class VerificationResult(BaseModel):
    """Output of VERIFY stage. Input to COMPOSE stage."""
    vision_result: VisionResult
    ocr_corrections: list[OcrCorrection] = Field(default_factory=list)
    math_errors: list[MathError] = Field(default_factory=list)
    logic_issues: list[LogicIssue] = Field(default_factory=list)
    verified: bool = Field(False, description="True if no critical issues found")
    verification_notes: str = Field("", description="Summary of verification findings")
