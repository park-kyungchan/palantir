"""COW Vision MCP Server — Gemini 3.0 Pro visual analysis + region merging."""

import json
import traceback

from mcp.server.fastmcp import FastMCP

from cow_mcp.models.common import BBox, RegionSource
from cow_mcp.models.ocr import OcrRegion
from cow_mcp.models.vision import CombinedRegion
from cow_mcp.vision.gemini import GeminiVisionClient

mcp = FastMCP("cow-vision")

_client: GeminiVisionClient | None = None


def _get_client() -> GeminiVisionClient:
    global _client
    if _client is None:
        _client = GeminiVisionClient()
    return _client


# ---------------------------------------------------------------------------
# IoU merge algorithm (COND-4)
# ---------------------------------------------------------------------------

def _compute_iou(a: BBox, b: BBox) -> float:
    """Compute Intersection over Union of two bounding boxes."""
    ix1 = max(a.x, b.x)
    iy1 = max(a.y, b.y)
    ix2 = min(a.x2, b.x2)
    iy2 = min(a.y2, b.y2)

    intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = a.area + b.area - intersection

    return intersection / union if union > 0 else 0.0


def _union_bbox(a: BBox, b: BBox) -> BBox:
    """Compute the union (enclosing) bounding box of two bboxes."""
    x = min(a.x, b.x)
    y = min(a.y, b.y)
    x2 = max(a.x2, b.x2)
    y2 = max(a.y2, b.y2)
    return BBox(x=x, y=y, width=x2 - x, height=y2 - y)


def merge_regions(
    mathpix_regions: list[dict],
    gemini_regions: list[dict],
    iou_threshold: float = 0.5,
) -> list[CombinedRegion]:
    """Merge Mathpix OCR regions with Gemini vision regions using IoU (COND-4).

    Algorithm:
    1. Compute all pairwise IoU values.
    2. Sort pairs by IoU descending.
    3. Greedy matching: match pairs with IoU > threshold (each region matched at most once).
    4. Matched pairs → CombinedRegion(source=MERGED, bbox=union, content=Mathpix,
       confidence=max).
    5. Unmatched Mathpix → CombinedRegion(source=MATHPIX).
    6. Unmatched Gemini → CombinedRegion(source=GEMINI).

    Args:
        mathpix_regions: List of dicts with keys: id, type, bbox (dict), content, confidence.
        gemini_regions: List of dicts with keys: id, type, bbox (dict), confidence.
        iou_threshold: IoU threshold for merging (default 0.5).

    Returns:
        List of CombinedRegion with source attribution.
    """
    results: list[CombinedRegion] = []

    # Parse bboxes
    def _parse_bbox(d: dict) -> BBox | None:
        bbox_data = d.get("bbox", {})
        if isinstance(bbox_data, BBox):
            return bbox_data
        try:
            return BBox(
                x=max(0, int(bbox_data.get("x", 0))),
                y=max(0, int(bbox_data.get("y", 0))),
                width=max(1, int(bbox_data.get("width", 1))),
                height=max(1, int(bbox_data.get("height", 1))),
            )
        except (ValueError, TypeError):
            return None

    m_bboxes = [(i, _parse_bbox(r)) for i, r in enumerate(mathpix_regions)]
    g_bboxes = [(i, _parse_bbox(r)) for i, r in enumerate(gemini_regions)]

    # Filter out invalid bboxes
    m_bboxes = [(i, b) for i, b in m_bboxes if b is not None]
    g_bboxes = [(i, b) for i, b in g_bboxes if b is not None]

    # Compute all pairwise IoUs
    pairs: list[tuple[float, int, int]] = []  # (iou, m_idx, g_idx)
    for mi, mb in m_bboxes:
        for gi, gb in g_bboxes:
            iou = _compute_iou(mb, gb)
            if iou > 0:
                pairs.append((iou, mi, gi))

    # Sort by IoU descending for greedy matching
    pairs.sort(key=lambda x: x[0], reverse=True)

    matched_m: set[int] = set()
    matched_g: set[int] = set()
    merge_idx = 0

    for iou, mi, gi in pairs:
        if mi in matched_m or gi in matched_g:
            continue
        if iou <= iou_threshold:
            break  # All remaining pairs have IoU <= threshold

        matched_m.add(mi)
        matched_g.add(gi)

        m_region = mathpix_regions[mi]
        g_region = gemini_regions[gi]
        m_bbox = _parse_bbox(m_region)
        g_bbox = _parse_bbox(g_region)

        # Merged bbox = union of both (COND-4)
        merged_bbox = _union_bbox(m_bbox, g_bbox)

        # Content: Mathpix preferred (COND-4)
        content = m_region.get("content") or g_region.get("content")

        # Confidence: max of both (COND-4)
        m_conf = m_region.get("confidence") or 0.0
        g_conf = g_region.get("confidence") or 0.0
        confidence = max(float(m_conf), float(g_conf))

        # Type: Mathpix type preferred (finer granularity from OCR)
        region_type = m_region.get("type", g_region.get("type", "text"))

        results.append(
            CombinedRegion(
                id=f"merged-{merge_idx}",
                type=region_type,
                bbox=merged_bbox,
                source=RegionSource.MERGED,
                confidence=confidence,
                content=content,
            )
        )
        merge_idx += 1

    # Unmatched Mathpix regions
    for mi, mb in m_bboxes:
        if mi in matched_m:
            continue
        m_region = mathpix_regions[mi]
        results.append(
            CombinedRegion(
                id=m_region.get("id", f"mathpix-{mi}"),
                type=m_region.get("type", "text"),
                bbox=mb,
                source=RegionSource.MATHPIX,
                confidence=m_region.get("confidence"),
                content=m_region.get("content"),
            )
        )

    # Unmatched Gemini regions
    for gi, gb in g_bboxes:
        if gi in matched_g:
            continue
        g_region = gemini_regions[gi]
        results.append(
            CombinedRegion(
                id=g_region.get("id", f"gemini-{gi}"),
                type=g_region.get("type", "text"),
                bbox=gb,
                source=RegionSource.GEMINI,
                confidence=g_region.get("confidence"),
                content=g_region.get("content"),
            )
        )

    return results


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def cow_gemini_detect_elements(image_path: str, regions: str = "[]") -> str:
    """Detect visual elements within diagram regions using Gemini 3.0 Pro.

    Analyzes diagrams/figures to find internal elements (axes, labels, data points,
    lines, shapes, arrows, text, legends) with bounding boxes.

    Args:
        image_path: Absolute path to the image file.
        regions: JSON array of diagram region dicts with 'id' and 'bbox' keys.
                 Empty array analyzes the full image.
    """
    try:
        region_list = json.loads(regions) if regions and regions != "[]" else None
        client = _get_client()
        results = await client.detect_elements(image_path, region_list)
        return json.dumps(
            [r.model_dump() for r in results],
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_gemini_layout_analysis(image_path: str, ocr_regions: str = "[]") -> str:
    """Analyze document layout using Gemini 3.0 Pro.

    Detects column structure, reading order, and spatial relationships between regions.

    Args:
        image_path: Absolute path to the image file.
        ocr_regions: JSON array of OCR region dicts with 'id', 'type', 'bbox' keys.
    """
    try:
        region_list = json.loads(ocr_regions) if ocr_regions and ocr_regions != "[]" else None
        client = _get_client()
        result = await client.analyze_layout(image_path, region_list)
        return result.model_dump_json(indent=2)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_merge_regions(mathpix_regions: str, gemini_regions: str, iou_threshold: float = 0.5) -> str:
    """Merge Mathpix OCR regions with Gemini vision regions using IoU algorithm.

    Pairs regions by bounding box overlap. IoU > threshold creates merged regions;
    unmatched regions are preserved with their original source.

    Args:
        mathpix_regions: JSON array of Mathpix region dicts (id, type, bbox, content, confidence).
        gemini_regions: JSON array of Gemini region dicts (id, type, bbox, confidence).
        iou_threshold: IoU threshold for merging (default 0.5).
    """
    try:
        m_regions = json.loads(mathpix_regions)
        g_regions = json.loads(gemini_regions)
        results = merge_regions(m_regions, g_regions, iou_threshold)
        return json.dumps(
            [r.model_dump() for r in results],
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()})


if __name__ == "__main__":
    mcp.run(transport="stdio")
