"""
COW CLI - PDF Reconstruction Module

Provides tools for reconstructing PDF from B1 outputs:
- MMDMerger: Merge layout + content → MMD
- MathpixPDFConverter: MMD → PDF via Mathpix API
- ReconstructionValidator: Quality validation

MCP Tools (cow-pdf server):
- merge_to_mmd: Combine layout.json and content.json into MMD
- convert_to_pdf: Convert MMD to PDF via Mathpix /v3/converter
- validate_reconstruction: Verify reconstruction quality
- get_reconstruction_status: Check async conversion status
"""

from cow_cli.pdf.merger import MMDMerger, MergeResult
from cow_cli.pdf.converter import MathpixPDFConverter, ConversionResult, ConversionStatus
from cow_cli.pdf.validator import ReconstructionValidator, ValidationResult, ValidationIssue

__all__ = [
    # Merger
    "MMDMerger",
    "MergeResult",
    # Converter
    "MathpixPDFConverter",
    "ConversionResult",
    "ConversionStatus",
    # Validator
    "ReconstructionValidator",
    "ValidationResult",
    "ValidationIssue",
]
