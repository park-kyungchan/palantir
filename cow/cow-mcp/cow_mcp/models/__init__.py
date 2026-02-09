"""Shared Pydantic interface contracts for all COW pipeline stages."""

from cow_mcp.models.common import BBox, Dimensions, SessionInfo, RegionSource
from cow_mcp.models.ingest import IngestResult
from cow_mcp.models.ocr import OcrResult, MathElement, OcrRegion, Diagram
from cow_mcp.models.vision import (
    VisionResult, DiagramElement, DiagramInternals,
    SpatialRelation, LayoutAnalysis, CombinedRegion,
)
from cow_mcp.models.verify import (
    VerificationResult, OcrCorrection, MathError, LogicIssue,
)
from cow_mcp.models.compose import CompositionResult, EditAction, DocumentMetadata
from cow_mcp.models.export import ExportResult, LatexSource

__all__ = [
    # common
    "BBox", "Dimensions", "SessionInfo", "RegionSource",
    # ingest
    "IngestResult",
    # ocr
    "OcrResult", "MathElement", "OcrRegion", "Diagram",
    # vision
    "VisionResult", "DiagramElement", "DiagramInternals",
    "SpatialRelation", "LayoutAnalysis", "CombinedRegion",
    # verify
    "VerificationResult", "OcrCorrection", "MathError", "LogicIssue",
    # compose
    "CompositionResult", "EditAction", "DocumentMetadata",
    # export
    "ExportResult", "LatexSource",
]
