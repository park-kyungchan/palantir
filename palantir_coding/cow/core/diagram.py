# cow/core/diagram.py
"""Diagram detection, cropping, and verification.

- detect_diagrams(): Loop A detects diagram bounding boxes in the image.
- crop_diagrams(): PIL crops regions with padding.
- verify_crops(): Loop A verifies each crop is correctly extracted.

ISS-4: Gemini returns bbox in ~1000-unit width scale. Apply SCALE = actual_width / 1000.
ISS-5: MCP vision tools insufficient — uses direct Gemini API (AD-6).
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult

logger = logging.getLogger("cow.core.diagram")


@dataclass
class BboxResult:
    """Bounding box detection result.

    Attributes:
        id: Diagram identifier (e.g., "diagram_1").
        x, y, width, height: Pixel coordinates (after scale correction).
        description: Brief description of the diagram content.
        confidence: Detection confidence (0.0-1.0).
    """
    id: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    description: str = ""
    confidence: float = 0.0


@dataclass
class CropVerifyResult:
    """Crop verification result.

    Attributes:
        path: Path to the cropped PNG file.
        passed: Whether the crop passed verification.
        issues: List of issues found (empty if passed).
        confidence: Verification confidence (0.0-1.0).
    """
    path: str = ""
    passed: bool = False
    issues: list = field(default_factory=list)
    confidence: float = 0.0


def detect_diagrams(
    image_path: str,
    loop_params: dict | None = None,
) -> list[BboxResult]:
    """Detect diagram regions via Loop A.

    ISS-4: Applies scale correction — Gemini bbox uses ~1000-unit width.

    Args:
        image_path: Path to image file (PNG).
        loop_params: Optional GeminiQualityLoop parameters.

    Returns:
        List of BboxResult with pixel-coordinate bounding boxes.
    """
    params = loop_params or {}

    # Get actual image dimensions for scale correction (ISS-4)
    img = Image.open(image_path)
    actual_width, actual_height = img.size
    scale_x = actual_width / 1000.0  # ISS-4: Gemini uses ~1000-unit width
    scale_y = actual_height / 1000.0

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Detect ALL diagrams, figures, charts, and graphs in this image.\n"
        "For each diagram, return a JSON array:\n"
        '[{"id": "diagram_1", "bbox": {"x": N, "y": N, "w": N, "h": N}, '
        '"desc": "brief description"}]\n'
        "Coordinates should be in your native scale (approximately 1000-unit width).\n"
        "Include ALL visual elements that are not pure text."
    )

    validation_prompt = (
        "Validate diagram detection results against the original image.\n"
        "Check for:\n"
        "1. Missing diagrams (false negatives)\n"
        "2. Non-diagram regions detected (false positives)\n"
        "3. Bounding box accuracy (tight fit, no excessive padding)\n"
        "Score confidence 0-1."
    )

    result: LoopResult = loop.run(
        image_path=image_path,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    # Parse result into BboxResult list with scale correction
    diagrams = []
    raw = result.result
    if isinstance(raw, str):
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines).strip()
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "diagrams" in parsed:
                parsed = parsed["diagrams"]
        except json.JSONDecodeError:
            logger.warning("Failed to parse diagram detection result: %s", raw[:200])
            return []
    elif isinstance(raw, list):
        parsed = raw
    else:
        return []

    for item in parsed:
        bbox = item.get("bbox", {})
        diagrams.append(BboxResult(
            id=item.get("id", f"diagram_{len(diagrams) + 1}"),
            x=int(bbox.get("x", 0) * scale_x),  # ISS-4 scale correction
            y=int(bbox.get("y", 0) * scale_y),
            width=int(bbox.get("w", 0) * scale_x),
            height=int(bbox.get("h", 0) * scale_y),
            description=item.get("desc", ""),
            confidence=result.confidence,
        ))

    return diagrams


def crop_diagrams(
    image_path: str,
    bboxes: list[BboxResult],
    output_dir: str | None = None,
    padding: int = 15,
) -> list[str]:
    """Crop diagram regions from image using PIL.

    Args:
        image_path: Path to source image.
        bboxes: List of BboxResult with pixel coordinates.
        output_dir: Directory for cropped PNGs. Defaults to image's directory.
        padding: Extra pixels around each crop.

    Returns:
        List of paths to cropped PNG files.
    """
    img = Image.open(image_path)
    img_width, img_height = img.size

    if output_dir is None:
        output_dir = str(Path(image_path).parent)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    crop_paths = []
    for bbox in bboxes:
        # Apply padding with clamping
        x1 = max(0, bbox.x - padding)
        y1 = max(0, bbox.y - padding)
        x2 = min(img_width, bbox.x + bbox.width + padding)
        y2 = min(img_height, bbox.y + bbox.height + padding)

        cropped = img.crop((x1, y1, x2, y2))
        crop_path = str(Path(output_dir) / f"{bbox.id}.png")
        cropped.save(crop_path)
        crop_paths.append(crop_path)
        logger.info("Cropped %s: (%d,%d)-(%d,%d) → %s", bbox.id, x1, y1, x2, y2, crop_path)

    return crop_paths


def verify_crops(
    crop_paths: list[str],
    loop_params: dict | None = None,
) -> list[CropVerifyResult]:
    """Verify crop quality via Loop A.

    Args:
        crop_paths: List of cropped PNG file paths.
        loop_params: Optional GeminiQualityLoop parameters.

    Returns:
        List of CropVerifyResult (one per crop).
    """
    params = loop_params or {}
    results = []

    for crop_path in crop_paths:
        loop = GeminiQualityLoop(
            image_model=params.get("image_model", "gemini-3-pro-image-preview"),
            reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
            api_key=params.get("api_key"),
        )

        task_prompt = (
            "Analyze this cropped diagram image.\n"
            "Is this a complete, well-cropped diagram?\n"
            'Return JSON: {"complete": true/false, "issues": ["..."]}'
        )

        validation_prompt = (
            "Validate the crop quality assessment.\n"
            "Check: Is the diagram fully captured? Any truncation? "
            "Any excess non-diagram content included?\n"
            "Score confidence 0-1."
        )

        result: LoopResult = loop.run(
            image_path=crop_path,
            task_prompt=task_prompt,
            validation_prompt=validation_prompt,
            temperature=0.1,
            max_iterations=2,  # Quick verification — fewer iterations
            confidence_threshold=0.8,
        )

        # Parse verification result
        issues = []
        passed = True
        if isinstance(result.result, str):
            try:
                cleaned = result.result.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    cleaned = "\n".join(lines).strip()
                parsed = json.loads(cleaned)
                passed = parsed.get("complete", True)
                issues = parsed.get("issues", [])
            except json.JSONDecodeError:
                passed = result.converged

        results.append(CropVerifyResult(
            path=crop_path,
            passed=passed,
            issues=issues,
            confidence=result.confidence,
        ))

    return results
