# cow/core/ocr.py
"""OCR extraction: Gemini (via Loop A) and Mathpix (v3/text API).

Two extraction methods — user selects per-problem:
- extract_gemini(): Uses GeminiQualityLoop for L1+L2 verified OCR.
- extract_mathpix(): Direct Mathpix v3/text API call (sync, requests).

ISS-1: Never use include_line_data + include_word_data together (Mathpix opts_conflict).
ISS-2: Gemini OCR hallucination mitigated by Loop A L2 cross-validation.
"""

import base64
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import requests

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult
from cow.config.models import ModelUnavailableError

logger = logging.getLogger("cow.core.ocr")


@dataclass
class OcrResult:
    """OCR extraction result.

    Attributes:
        text: Extracted LaTeX/text content.
        confidence: Overall confidence (0.0-1.0).
        method: "gemini" or "mathpix".
        iterations: Number of Loop A iterations (gemini only).
        raw_response: Raw API response for debugging.
    """
    text: str = ""
    confidence: float = 0.0
    method: str = ""
    iterations: int = 0
    raw_response: dict = field(default_factory=dict)


def extract_gemini(
    image_path: str,
    loop_params: dict | None = None,
) -> OcrResult:
    """Gemini OCR via Loop A (L1+L2 verified).

    Args:
        image_path: Path to image file (PNG).
        loop_params: Optional dict with keys: image_model, reasoning_model,
                     api_key, temperature, max_iterations, confidence_threshold.

    Returns:
        OcrResult with LaTeX text and confidence.
    """
    params = loop_params or {}

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Extract ALL text content from this image as LaTeX.\n"
        "Include mathematical expressions with proper LaTeX notation.\n"
        "Preserve the document structure: headings, problem numbers, solutions.\n"
        "Use $...$ for inline math and $$...$$ or \\[...\\] for display math.\n"
        "Return ONLY the LaTeX content, no commentary."
    )

    validation_prompt = (
        "Validate this OCR extraction against the original image.\n"
        "Check for:\n"
        "1. Missing text or equations\n"
        "2. Incorrect LaTeX notation\n"
        "3. Hallucinated content (\\quad repetition, ISS-2)\n"
        "4. Structural accuracy (problem numbers, section ordering)\n"
        "Score confidence 0-1 based on extraction quality."
    )

    result: LoopResult = loop.run(
        image_path=image_path,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    return OcrResult(
        text=result.result if isinstance(result.result, str) else json.dumps(result.result),
        confidence=result.confidence,
        method="gemini",
        iterations=result.iterations,
    )


def extract_mathpix(
    image_path: str,
    app_id: str | None = None,
    app_key: str | None = None,
) -> OcrResult:
    """Mathpix v3/text OCR (sync, requests).

    ISS-1: Never uses include_line_data + include_word_data together.

    Args:
        image_path: Path to image file.
        app_id: Mathpix app ID. Falls back to MATHPIX_APP_ID env var.
        app_key: Mathpix app key. Falls back to MATHPIX_APP_KEY env var.

    Returns:
        OcrResult with LaTeX text and confidence.

    Raises:
        ValueError: If Mathpix credentials are missing.
        requests.HTTPError: If API returns error status.
    """
    app_id = app_id or os.environ.get("MATHPIX_APP_ID", "")
    app_key = app_key or os.environ.get("MATHPIX_APP_KEY", "")

    if not app_id or not app_key:
        raise ValueError("Mathpix credentials not set. Set MATHPIX_APP_ID and MATHPIX_APP_KEY.")

    img_path = Path(image_path)
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image_bytes = img_path.read_bytes()
    src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"

    # ISS-1: Use include_line_data ONLY (no include_word_data)
    payload = {
        "src": src,
        "formats": ["text", "latex_styled"],
        "include_line_data": True,
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True,
    }

    headers = {
        "app_id": app_id,
        "app_key": app_key,
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.mathpix.com/v3/text",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    text = data.get("text", "") or data.get("latex_styled", "")
    confidence = data.get("confidence", 0.0) or data.get("confidence_rate", 0.0)

    return OcrResult(
        text=text,
        confidence=float(confidence),
        method="mathpix",
        iterations=1,
        raw_response=data,
    )
