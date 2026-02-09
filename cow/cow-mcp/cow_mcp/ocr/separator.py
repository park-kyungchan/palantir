"""BBox conversion logic adapted from cow-cli/semantic/separator.py.

Extracts cnt_to_bbox() preserving original _cnt_to_region() semantics:
- Returns None for degenerate contours (len < 2)
- Clamps negative coordinates to 0
- Ensures minimum dimension of 1 pixel
All clamping happens BEFORE Pydantic BBox validation (ge=0, ge=1).
"""

import logging
from typing import Optional

from cow_mcp.models.common import BBox
from cow_mcp.models.ocr import OcrRegion

logger = logging.getLogger("cow-mcp.ocr.separator")


def cnt_to_bbox(cnt: list[list[int]]) -> Optional[BBox]:
    """Convert Mathpix polygon contour to axis-aligned bounding box.

    Preserves original cow-cli _cnt_to_region() error-handling semantics (COND-1):
    - Returns None for empty or degenerate contours (len < 2)
    - Clamps negative coordinates: max(0, min_x)
    - Ensures minimum dimensions: max(1, width)

    Args:
        cnt: List of [x, y] coordinate pairs from Mathpix API.

    Returns:
        BBox or None if contour is invalid.
    """
    if not cnt or len(cnt) < 2:
        return None

    try:
        xs = [p[0] for p in cnt]
        ys = [p[1] for p in cnt]

        min_x = min(xs)
        min_y = min(ys)
        max_x = max(xs)
        max_y = max(ys)

        width = max_x - min_x
        height = max_y - min_y

        # Clamp negative coordinates (original: max(0, min_x))
        x = max(0, min_x)
        y = max(0, min_y)

        # Ensure minimum dimensions (original: max(1, width))
        width = max(1, width)
        height = max(1, height)

        return BBox(x=x, y=y, width=width, height=height)

    except (IndexError, TypeError) as e:
        logger.warning(f"Invalid contour data: {e}")
        return None


def _map_mathpix_type(raw_type: str) -> str:
    """Map Mathpix element types to OcrRegion types."""
    type_map = {
        "text": "text",
        "math": "math",
        "table": "table",
        "diagram": "diagram",
        "chart": "chart",
        "figure": "figure",
        "equation_number": "equation_number",
        # Mathpix-specific types mapped to closest match
        "image": "figure",
        "chemistry": "math",
        "geometry": "diagram",
    }
    return type_map.get(raw_type, "text")


def process_mathpix_regions(line_data: list[dict]) -> list[OcrRegion]:
    """Convert Mathpix line_data into OcrRegions with bbox conversion.

    Args:
        line_data: List of line/word dicts from Mathpix API response,
                   each may contain 'cnt', 'type', 'text', 'confidence'.

    Returns:
        List of OcrRegion with converted bounding boxes.
        Lines with invalid contours are skipped.
    """
    regions: list[OcrRegion] = []

    for i, line in enumerate(line_data):
        # Try cnt first, fall back to region dict
        bbox: Optional[BBox] = None
        cnt = line.get("cnt")
        if cnt:
            bbox = cnt_to_bbox(cnt)

        if bbox is None:
            # Try pre-computed region field
            region = line.get("region")
            if region and isinstance(region, dict):
                try:
                    x = max(0, int(region.get("top_left_x", 0)))
                    y = max(0, int(region.get("top_left_y", 0)))
                    w = max(1, int(region.get("width", 1)))
                    h = max(1, int(region.get("height", 1)))
                    bbox = BBox(x=x, y=y, width=w, height=h)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid region dict at index {i}: {e}")

        if bbox is None:
            continue

        raw_type = line.get("type", "text")
        region_type = _map_mathpix_type(raw_type)

        confidence = line.get("confidence") or line.get("confidence_rate")
        if confidence is not None:
            confidence = max(0.0, min(1.0, float(confidence)))

        regions.append(
            OcrRegion(
                id=f"ocr-region-{i}",
                type=region_type,
                bbox=bbox,
                content=line.get("text") or line.get("text_display"),
                confidence=confidence,
                parent_id=line.get("parent_id"),
                children_ids=line.get("children_ids") or [],
            )
        )

    return regions
