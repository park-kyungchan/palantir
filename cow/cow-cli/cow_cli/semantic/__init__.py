"""
COW CLI - Semantic Module

Layout/Content separation schemas and processing.
"""
from cow_cli.semantic.schemas import (
    # Shared types
    Region,
    DataFormat,
    DataObject,
    PageInfo,
    # Element types
    ElementType,
    ElementSubtype,
    # Layout
    LayoutElement,
    LayoutMetadata,
    LayoutData,
    # Content
    QualityMetrics,
    ContentElement,
    QualitySummary,
    DetectedAlphabets,
    ContentMetadata,
    ContentData,
    # Combined
    SeparatedDocument,
)
from cow_cli.semantic.separator import (
    SeparationError,
    LayoutContentSeparator,
    separate_mathpix_output,
)

__all__ = [
    # Schemas
    "Region",
    "DataFormat",
    "DataObject",
    "PageInfo",
    "ElementType",
    "ElementSubtype",
    "LayoutElement",
    "LayoutMetadata",
    "LayoutData",
    "QualityMetrics",
    "ContentElement",
    "QualitySummary",
    "DetectedAlphabets",
    "ContentMetadata",
    "ContentData",
    "SeparatedDocument",
    # Separator
    "SeparationError",
    "LayoutContentSeparator",
    "separate_mathpix_output",
]
