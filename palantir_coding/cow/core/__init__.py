# cow/core/__init__.py
"""COW Pipeline v2.0 — Core modules for Triple-Layer Verification."""

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult
from cow.core.ocr import extract_gemini, extract_mathpix, OcrResult
from cow.core.diagram import detect_diagrams, crop_diagrams, verify_crops, BboxResult, CropVerifyResult
from cow.core.layout_design import analyze_layout, LayoutDesignReport
from cow.core.layout_verify import verify_layout, LayoutVerifyReport
from cow.core.compile import compile_latex, CompileResult

__all__ = [
    # gemini_loop
    "GeminiQualityLoop", "LoopResult",
    # ocr
    "extract_gemini", "extract_mathpix", "OcrResult",
    # diagram
    "detect_diagrams", "crop_diagrams", "verify_crops", "BboxResult", "CropVerifyResult",
    # layout_design
    "analyze_layout", "LayoutDesignReport",
    # layout_verify
    "verify_layout", "LayoutVerifyReport",
    # compile
    "compile_latex", "CompileResult",
]
