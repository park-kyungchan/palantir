"""Gemini 3.0 Pro API client for visual analysis (bbox detection + layout).

Uses google-genai SDK with structured JSON output.
COND-3: Normalizes Gemini bbox from [0,1] to pixel coordinates.
Graceful degradation: returns empty results on failure, never crashes.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from cow_mcp.models.common import BBox
from cow_mcp.models.vision import (
    DiagramElement,
    DiagramInternals,
    LayoutAnalysis,
    SpatialRelation,
)

logger = logging.getLogger("cow-mcp.vision.gemini")

# Structured output schemas for Gemini API
DETECT_ELEMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "elements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["axis", "label", "data_point", "line",
                                 "shape", "arrow", "text", "legend"],
                    },
                    "bbox": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "width": {"type": "number"},
                            "height": {"type": "number"},
                        },
                        "required": ["x", "y", "width", "height"],
                    },
                    "content": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["type", "bbox"],
            },
        },
    },
    "required": ["elements"],
}

LAYOUT_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "columns": {"type": "integer"},
        "reading_order": {
            "type": "array",
            "items": {"type": "string"},
        },
        "spatial_relations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_id": {"type": "string"},
                    "target_id": {"type": "string"},
                    "relation": {
                        "type": "string",
                        "enum": ["above", "below", "left_of",
                                 "right_of", "contains", "adjacent"],
                    },
                },
                "required": ["source_id", "target_id", "relation"],
            },
        },
    },
    "required": ["columns", "reading_order"],
}


class GeminiVisionClient:
    """Gemini 3.0 Pro client for visual analysis.

    Features:
    - Structured JSON output for reliable parsing
    - Bbox normalization from [0,1] to pixel coordinates (COND-3)
    - Confidence threshold filtering (default 0.3)
    - Exponential backoff retry (max 3 retries)
    - Graceful degradation on API failure
    """

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2.0
    DEFAULT_CONFIDENCE_THRESHOLD = 0.3

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.0-pro",
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ):
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._model = model
        self._confidence_threshold = confidence_threshold

        if self._api_key:
            self._client = genai.Client(api_key=self._api_key)
        else:
            self._client = None

    def _validate_client(self) -> None:
        if not self._client or not self._api_key:
            raise ValueError(
                "Gemini API key not configured. "
                "Set GEMINI_API_KEY environment variable."
            )

    async def _generate_with_retry(
        self,
        contents: list,
        config: types.GenerateContentConfig,
    ) -> Optional[str]:
        """Call Gemini API with exponential backoff retry.

        Returns response text or None on failure (graceful degradation).
        """
        self._validate_client()

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=config,
                )
                return response.text

            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        f"Gemini API error (attempt {attempt + 1}/{self.MAX_RETRIES}), "
                        f"retrying after {wait_time:.1f}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Gemini API failed after {self.MAX_RETRIES} retries: {e}")
                    return None

        return None

    @staticmethod
    def _normalize_bbox(
        raw: dict,
        image_width: int,
        image_height: int,
    ) -> Optional[BBox]:
        """Normalize Gemini bbox to pixel coordinates (COND-3).

        Gemini may return normalized [0,1] or pixel coordinates.
        Detection: if all values < 1.0 (and > 0), treat as normalized.
        Converts to pixel coords using image dimensions.
        Applies clamping for BBox validation (ge=0, ge=1).
        """
        try:
            x = float(raw.get("x", 0))
            y = float(raw.get("y", 0))
            w = float(raw.get("width", 0))
            h = float(raw.get("height", 0))

            # Detect normalized coordinates: all position values < 2.0
            # (using 2.0 threshold to handle edge cases near 1.0)
            all_values = [x, y, w, h]
            if all(0 <= v <= 1.0 for v in all_values):
                # Normalized [0,1] → pixel coordinates
                x = x * image_width
                y = y * image_height
                w = w * image_width
                h = h * image_height

            # Clamp and ensure integer pixel values
            x_int = max(0, int(round(x)))
            y_int = max(0, int(round(y)))
            w_int = max(1, int(round(w)))
            h_int = max(1, int(round(h)))

            # Clamp to image bounds
            if x_int + w_int > image_width:
                w_int = max(1, image_width - x_int)
            if y_int + h_int > image_height:
                h_int = max(1, image_height - y_int)

            return BBox(x=x_int, y=y_int, width=w_int, height=h_int)

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid bbox data: {raw} — {e}")
            return None

    async def detect_elements(
        self,
        image_path: str,
        regions: list[dict] | None = None,
    ) -> list[DiagramInternals]:
        """Detect internal elements within diagram regions using Gemini.

        Args:
            image_path: Path to the image file.
            regions: Optional list of diagram region dicts with 'id' and 'bbox' keys.
                     If None, analyzes the full image as one region.

        Returns:
            List of DiagramInternals. Empty list on failure (graceful degradation).
        """
        try:
            img_path = Path(image_path)
            if not img_path.exists():
                logger.error(f"Image not found: {image_path}")
                return []

            image = Image.open(img_path)
            img_width, img_height = image.size

            # Build region context for the prompt
            region_context = ""
            if regions:
                region_descs = []
                for r in regions:
                    rid = r.get("id", "unknown")
                    bbox = r.get("bbox", {})
                    region_descs.append(
                        f"  - Region '{rid}': x={bbox.get('x',0)}, y={bbox.get('y',0)}, "
                        f"w={bbox.get('width',0)}, h={bbox.get('height',0)}"
                    )
                region_context = (
                    "Focus on these diagram regions:\n" + "\n".join(region_descs) + "\n"
                )

            prompt = (
                "Analyze this document image and detect all visual elements "
                "(axes, labels, data points, lines, shapes, arrows, text, legends) "
                "within diagrams and figures.\n"
                f"{region_context}"
                f"Image dimensions: {img_width}x{img_height} pixels.\n"
                "Return bounding boxes in PIXEL coordinates (not normalized). "
                "Include a confidence score (0-1) for each detection."
            )

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=DETECT_ELEMENTS_SCHEMA,
            )

            response_text = await self._generate_with_retry(
                contents=[image, prompt],
                config=config,
            )

            if not response_text:
                return []

            data = json.loads(response_text)
            elements_raw = data.get("elements", [])

            # Group elements by region
            if regions:
                results = []
                for region in regions:
                    rid = region.get("id", "unknown")
                    rbbox_raw = region.get("bbox", {})
                    rbbox = self._normalize_bbox(rbbox_raw, img_width, img_height)
                    if rbbox is None:
                        continue

                    region_elements = []
                    for i, elem in enumerate(elements_raw):
                        bbox = self._normalize_bbox(
                            elem.get("bbox", {}), img_width, img_height
                        )
                        if bbox is None:
                            continue

                        conf = elem.get("confidence", 0.0)
                        if conf < self._confidence_threshold:
                            continue

                        region_elements.append(
                            DiagramElement(
                                id=f"gem-{rid}-{i}",
                                type=elem.get("type", "text"),
                                bbox=bbox,
                                content=elem.get("content"),
                            )
                        )

                    results.append(
                        DiagramInternals(
                            diagram_id=rid,
                            elements=region_elements,
                            bbox=rbbox,
                        )
                    )
                return results
            else:
                # No regions specified — treat full image as one region
                full_bbox = BBox(x=0, y=0, width=img_width, height=img_height)
                elements = []
                for i, elem in enumerate(elements_raw):
                    bbox = self._normalize_bbox(
                        elem.get("bbox", {}), img_width, img_height
                    )
                    if bbox is None:
                        continue

                    conf = elem.get("confidence", 0.0)
                    if conf < self._confidence_threshold:
                        continue

                    elements.append(
                        DiagramElement(
                            id=f"gem-full-{i}",
                            type=elem.get("type", "text"),
                            bbox=bbox,
                            content=elem.get("content"),
                        )
                    )

                return [
                    DiagramInternals(
                        diagram_id="full-image",
                        elements=elements,
                        bbox=full_bbox,
                    )
                ] if elements else []

        except Exception as e:
            logger.error(f"detect_elements failed: {e}")
            return []

    async def analyze_layout(
        self,
        image_path: str,
        ocr_regions: list[dict] | None = None,
    ) -> LayoutAnalysis:
        """Analyze document layout: columns, reading order, spatial relations.

        Args:
            image_path: Path to the image file.
            ocr_regions: Optional OCR region dicts with 'id', 'type', 'bbox' keys.

        Returns:
            LayoutAnalysis. Default (1 column, empty) on failure (graceful degradation).
        """
        try:
            img_path = Path(image_path)
            if not img_path.exists():
                logger.error(f"Image not found: {image_path}")
                return LayoutAnalysis()

            image = Image.open(img_path)

            # Build region context
            region_context = ""
            if ocr_regions:
                region_descs = []
                for r in ocr_regions:
                    rid = r.get("id", "unknown")
                    rtype = r.get("type", "unknown")
                    bbox = r.get("bbox", {})
                    region_descs.append(
                        f"  - '{rid}' ({rtype}): x={bbox.get('x',0)}, y={bbox.get('y',0)}, "
                        f"w={bbox.get('width',0)}, h={bbox.get('height',0)}"
                    )
                region_context = (
                    "OCR has detected these content regions:\n"
                    + "\n".join(region_descs)
                    + "\n"
                    "Use these region IDs in your reading_order and spatial_relations.\n"
                )

            prompt = (
                "Analyze this document's layout structure.\n"
                f"{region_context}"
                "Identify:\n"
                "1. Number of text columns\n"
                "2. Reading order of content blocks (list region IDs)\n"
                "3. Spatial relationships between regions "
                "(above, below, left_of, right_of, contains, adjacent)"
            )

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=LAYOUT_ANALYSIS_SCHEMA,
            )

            response_text = await self._generate_with_retry(
                contents=[image, prompt],
                config=config,
            )

            if not response_text:
                return LayoutAnalysis()

            data = json.loads(response_text)

            spatial = []
            for rel in data.get("spatial_relations", []):
                try:
                    spatial.append(
                        SpatialRelation(
                            source_id=rel["source_id"],
                            target_id=rel["target_id"],
                            relation=rel["relation"],
                        )
                    )
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid spatial relation: {rel} — {e}")

            return LayoutAnalysis(
                columns=max(1, data.get("columns", 1)),
                reading_order=data.get("reading_order", []),
                spatial_relations=spatial,
            )

        except Exception as e:
            logger.error(f"analyze_layout failed: {e}")
            return LayoutAnalysis()
