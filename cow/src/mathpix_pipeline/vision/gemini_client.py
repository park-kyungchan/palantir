"""
Gemini Vision Client for Stage C Fallback.

Uses Gemini 2.5 for zero-shot bbox detection and semantic interpretation
when YOLO + Claude primary path fails.

Schema Version: 2.0.0
"""

import asyncio
import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..schemas import (
    BBox,
    BBoxFormat,
    CombinedConfidence,
    DetectionElement,
    DetectionLayer,
    DiagramType,
    ElementClass,
    InterpretationLayer,
    InterpretedElement,
    InterpretedRelation,
    MergedElement,
    MergedOutput,
    PipelineStage,
    Provenance,
    RelationType,
    ReviewMetadata,
    VisionSpec,
)
from .exceptions import (
    GeminiAPIError,
    GeminiNotConfiguredError,
    GeminiRateLimitError,
    GeminiResponseParseError,
    GeminiTimeoutError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DETECTION_PROMPT = """Analyze this mathematical diagram image and return a JSON response with the following structure:

{
  "diagram_type": "one of: function_graph, coordinate_system, geometry, number_line, bar_chart, pie_chart, venn_diagram, flowchart, table, unknown",
  "diagram_description": "Brief description of what the diagram shows",
  "coordinate_system": "cartesian, polar, or null if not applicable",
  "elements": [
    {
      "id": "elem_001",
      "element_class": "one of: axis, curve, point, label, grid, arrow, line_segment, circle, polygon, angle, equation_region, text_region, unknown",
      "bbox": [x_min, y_min, x_max, y_max],
      "confidence": 0.0 to 1.0,
      "semantic_label": "Human readable label (e.g., 'Point A', 'x-axis', 'y = x^2')",
      "description": "Optional detailed description",
      "latex": "LaTeX representation if applicable (e.g., 'y = x^2')",
      "coordinates": {"x": 1, "y": 2} if this is a point with known coordinates,
      "function_type": "linear, quadratic, exponential, etc. if this is a curve",
      "equation": "Mathematical equation if identified"
    }
  ],
  "relations": [
    {
      "id": "rel_001",
      "source_id": "elem_001",
      "target_id": "elem_002",
      "relation_type": "one of: label_of, point_on, intersects, parallel_to, perpendicular_to, passes_through, bounded_by, contains",
      "confidence": 0.0 to 1.0,
      "description": "Optional description of relationship"
    }
  ],
  "overall_confidence": 0.0 to 1.0
}

IMPORTANT:
- bbox coordinates are [x_min, y_min, x_max, y_max] in pixel space
- Return ONLY valid JSON, no markdown code blocks or explanations
- Include all visible mathematical elements
- Be precise with bounding boxes - they should tightly enclose each element
"""

# Map string classes to ElementClass enum
ELEMENT_CLASS_MAP: Dict[str, ElementClass] = {
    "axis": ElementClass.AXIS,
    "curve": ElementClass.CURVE,
    "point": ElementClass.POINT,
    "label": ElementClass.LABEL,
    "grid": ElementClass.GRID,
    "arrow": ElementClass.ARROW,
    "line_segment": ElementClass.LINE_SEGMENT,
    "circle": ElementClass.CIRCLE,
    "polygon": ElementClass.POLYGON,
    "angle": ElementClass.ANGLE,
    "equation_region": ElementClass.EQUATION_REGION,
    "text_region": ElementClass.TEXT_REGION,
    "unknown": ElementClass.UNKNOWN,
}

# Map string diagram types to DiagramType enum
DIAGRAM_TYPE_MAP: Dict[str, DiagramType] = {
    "function_graph": DiagramType.FUNCTION_GRAPH,
    "coordinate_system": DiagramType.COORDINATE_SYSTEM,
    "geometry": DiagramType.GEOMETRY,
    "number_line": DiagramType.NUMBER_LINE,
    "bar_chart": DiagramType.BAR_CHART,
    "pie_chart": DiagramType.PIE_CHART,
    "venn_diagram": DiagramType.VENN_DIAGRAM,
    "flowchart": DiagramType.FLOWCHART,
    "table": DiagramType.TABLE,
    "unknown": DiagramType.UNKNOWN,
}

# Map string relation types to RelationType enum
RELATION_TYPE_MAP: Dict[str, RelationType] = {
    "label_of": RelationType.LABEL_OF,
    "point_on": RelationType.POINT_ON,
    "intersects": RelationType.INTERSECTS,
    "parallel_to": RelationType.PARALLEL_TO,
    "perpendicular_to": RelationType.PERPENDICULAR_TO,
    "passes_through": RelationType.PASSES_THROUGH,
    "bounded_by": RelationType.BOUNDED_BY,
    "contains": RelationType.CONTAINS,
}


# =============================================================================
# Gemini Vision Client
# =============================================================================

class GeminiVisionClient:
    """Gemini 2.5 zero-shot bbox + interpretation fallback.

    This client uses Gemini's native vision capabilities to:
    1. Detect mathematical elements in diagram images
    2. Provide semantic interpretation of detected elements
    3. Return results in VisionSpec format

    Usage:
        client = GeminiVisionClient()
        result = await client.detect_and_interpret(image_bytes, "image_001")

    Environment Variables:
        GOOGLE_API_KEY: Required Gemini API key
        GEMINI_MODEL: Optional model override (default: gemini-2.0-flash)
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        timeout_seconds: float = 45.0,
        max_retries: int = 2,
        api_key: Optional[str] = None,
    ):
        """Initialize Gemini client.

        Args:
            model: Gemini model to use (default: gemini-2.0-flash)
            timeout_seconds: Request timeout in seconds
            max_retries: Number of retry attempts on transient failures
            api_key: Optional API key (defaults to GOOGLE_API_KEY env var)
        """
        self.model = os.environ.get("GEMINI_MODEL", model)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self._client = None  # Lazy initialization

    def _ensure_configured(self) -> None:
        """Ensure API key is configured.

        Raises:
            GeminiNotConfiguredError: If API key is missing
        """
        if not self._api_key:
            raise GeminiNotConfiguredError(
                "Gemini API key not configured. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

    def _get_client(self) -> Any:
        """Get or create Gemini client with lazy initialization.

        Returns:
            Configured genai GenerativeModel

        Raises:
            GeminiNotConfiguredError: If google-generativeai not installed or not configured
        """
        if self._client is not None:
            return self._client

        self._ensure_configured()

        try:
            import google.generativeai as genai
        except ImportError as e:
            raise GeminiNotConfiguredError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai",
                cause=e,
            )

        genai.configure(api_key=self._api_key)
        self._client = genai.GenerativeModel(self.model)
        return self._client

    def _prepare_image(self, image: Union[str, Path, bytes]) -> Dict[str, Any]:
        """Convert image to Gemini API format.

        Args:
            image: Image as path string, Path object, or raw bytes

        Returns:
            Dict with mime_type and data for Gemini API

        Raises:
            FileNotFoundError: If image path doesn't exist
            ValueError: If image format not supported
        """
        if isinstance(image, bytes):
            # Detect format from magic bytes
            if image[:8] == b'\x89PNG\r\n\x1a\n':
                mime_type = "image/png"
            elif image[:2] == b'\xff\xd8':
                mime_type = "image/jpeg"
            elif image[:4] == b'GIF8':
                mime_type = "image/gif"
            elif image[:4] == b'RIFF' and image[8:12] == b'WEBP':
                mime_type = "image/webp"
            else:
                # Default to PNG
                mime_type = "image/png"

            image_data = base64.b64encode(image).decode('utf-8')
            return {"mime_type": mime_type, "data": image_data}

        # Handle path
        path = Path(image)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        # Determine MIME type from extension
        suffix = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(suffix)
        if not mime_type:
            raise ValueError(f"Unsupported image format: {suffix}")

        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        return {"mime_type": mime_type, "data": image_data}

    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from response, handling markdown code blocks.

        Args:
            text: Raw response text

        Returns:
            Cleaned JSON string
        """
        # Try to extract from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json_match.group(1).strip()

        # Try to find raw JSON object
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            return brace_match.group(0)

        return text.strip()

    def _parse_element_class(self, class_str: str) -> ElementClass:
        """Parse element class string to enum.

        Args:
            class_str: Class name string

        Returns:
            ElementClass enum value
        """
        normalized = class_str.lower().strip().replace(" ", "_")
        return ELEMENT_CLASS_MAP.get(normalized, ElementClass.UNKNOWN)

    def _parse_diagram_type(self, type_str: str) -> DiagramType:
        """Parse diagram type string to enum.

        Args:
            type_str: Diagram type string

        Returns:
            DiagramType enum value
        """
        normalized = type_str.lower().strip().replace(" ", "_")
        return DIAGRAM_TYPE_MAP.get(normalized, DiagramType.UNKNOWN)

    def _parse_relation_type(self, type_str: str) -> Optional[RelationType]:
        """Parse relation type string to enum.

        Args:
            type_str: Relation type string

        Returns:
            RelationType enum value or None if invalid
        """
        normalized = type_str.lower().strip().replace(" ", "_")
        return RELATION_TYPE_MAP.get(normalized)

    async def _parse_response(
        self,
        response_text: str,
        image_id: str,
    ) -> VisionSpec:
        """Parse Gemini response into VisionSpec format.

        Args:
            response_text: Raw JSON response from Gemini
            image_id: Image identifier

        Returns:
            Parsed VisionSpec

        Raises:
            GeminiResponseParseError: If response format is invalid
        """
        # Extract JSON from potential markdown wrapping
        json_str = self._extract_json_from_response(response_text)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise GeminiResponseParseError(
                f"Invalid JSON response: {e}",
                image_id=image_id,
            )

        # Validate required fields
        if not isinstance(data, dict):
            raise GeminiResponseParseError(
                f"Expected dict response, got {type(data).__name__}",
                image_id=image_id,
            )

        # Parse elements into detection and interpretation layers
        detection_elements: List[DetectionElement] = []
        interpreted_elements: List[InterpretedElement] = []
        merged_elements: List[MergedElement] = []

        raw_elements = data.get("elements", [])
        for i, elem in enumerate(raw_elements):
            elem_id = elem.get("id", f"gemini_elem_{i:03d}")
            element_class = self._parse_element_class(elem.get("element_class", "unknown"))

            # Parse bbox [x_min, y_min, x_max, y_max] -> BBox
            raw_bbox = elem.get("bbox", [0, 0, 10, 10])
            if len(raw_bbox) != 4:
                logger.warning(f"Invalid bbox for {elem_id}: {raw_bbox}")
                raw_bbox = [0, 0, 10, 10]

            x_min, y_min, x_max, y_max = raw_bbox
            bbox = BBox(
                x=x_min,
                y=y_min,
                width=max(1, x_max - x_min),
                height=max(1, y_max - y_min),
                format=BBoxFormat.XYWH,
            )

            # Get confidence
            confidence = float(elem.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            # Create detection element
            det_elem = DetectionElement(
                id=f"det_{elem_id}",
                element_class=element_class,
                bbox=bbox,
                detection_confidence=confidence,
            )
            detection_elements.append(det_elem)

            # Create interpreted element
            semantic_label = elem.get("semantic_label", f"Unknown {element_class.value}")
            interp_elem = InterpretedElement(
                id=f"interp_{elem_id}",
                detection_element_id=f"det_{elem_id}",
                semantic_label=semantic_label,
                description=elem.get("description"),
                latex_representation=elem.get("latex"),
                function_type=elem.get("function_type"),
                equation=elem.get("equation"),
                coordinates=elem.get("coordinates"),
                point_label=elem.get("semantic_label") if element_class == ElementClass.POINT else None,
                interpretation_confidence=confidence,
            )
            interpreted_elements.append(interp_elem)

            # Create merged element
            combined_conf = CombinedConfidence(
                detection_confidence=confidence,
                interpretation_confidence=confidence,
                combined_value=confidence,  # Same source, same confidence
                bbox_source="gemini-fallback",
                label_source="gemini-fallback",
                detection_weight=0.5,
                interpretation_weight=0.5,
            )

            merged_elem = MergedElement(
                id=elem_id,
                detection_id=f"det_{elem_id}",
                interpretation_id=f"interp_{elem_id}",
                bbox_source="gemini-fallback",
                label_source="gemini-fallback",
                element_class=element_class,
                bbox=bbox,
                semantic_label=semantic_label,
                description=elem.get("description"),
                combined_confidence=combined_conf,
                latex_representation=elem.get("latex"),
                equation=elem.get("equation"),
                coordinates=elem.get("coordinates"),
            )
            merged_elements.append(merged_elem)

        # Parse relations
        interpreted_relations: List[InterpretedRelation] = []
        for i, rel in enumerate(data.get("relations", [])):
            rel_type = self._parse_relation_type(rel.get("relation_type", ""))
            if rel_type is None:
                logger.warning(f"Unknown relation type: {rel.get('relation_type')}")
                continue

            interp_rel = InterpretedRelation(
                id=rel.get("id", f"rel_{i:03d}"),
                source_id=rel.get("source_id", ""),
                target_id=rel.get("target_id", ""),
                relation_type=rel_type,
                confidence=float(rel.get("confidence", 0.5)),
                description=rel.get("description"),
            )
            interpreted_relations.append(interp_rel)

        # Parse diagram-level info
        diagram_type = self._parse_diagram_type(data.get("diagram_type", "unknown"))
        diagram_description = data.get("diagram_description")
        coordinate_system = data.get("coordinate_system")

        # Build layers
        detection_layer = DetectionLayer(
            model=f"{self.model}-fallback",
            model_version="1.0.0",
            elements=detection_elements,
        )

        interpretation_layer = InterpretationLayer(
            model=f"{self.model}-fallback",
            elements=interpreted_elements,
            relations=interpreted_relations,
            diagram_type=diagram_type,
            diagram_description=diagram_description,
            coordinate_system=coordinate_system,
        )

        merged_output = MergedOutput(
            elements=merged_elements,
            relations=interpreted_relations,
            diagram_type=diagram_type,
            diagram_description=diagram_description,
            coordinate_system=coordinate_system,
            matched_count=len(merged_elements),
            detection_only_count=0,
            interpretation_only_count=0,
        )

        # Build VisionSpec
        provenance = Provenance(
            stage=PipelineStage.VISION_PARSE,
            model=f"{self.model}-fallback",
        )

        overall_conf = float(data.get("overall_confidence", 0.5))

        vision_spec = VisionSpec(
            image_id=image_id,
            provenance=provenance,
            detection_layer=detection_layer,
            interpretation_layer=interpretation_layer,
            merged_output=merged_output,
            fallback_used=True,
            fallback_model=self.model,
            fallback_reason="primary_yolo_claude_failed",
        )

        return vision_spec

    async def _call_gemini_api(
        self,
        image_data: Dict[str, Any],
        image_id: str,
    ) -> str:
        """Make the actual API call to Gemini.

        Args:
            image_data: Prepared image data dict
            image_id: Image identifier for error reporting

        Returns:
            Response text from Gemini

        Raises:
            GeminiAPIError: On API failures
            GeminiTimeoutError: On timeout
            GeminiRateLimitError: On rate limiting
        """
        client = self._get_client()

        # Build content with image and prompt
        content = [
            {
                "mime_type": image_data["mime_type"],
                "data": image_data["data"],
            },
            DETECTION_PROMPT,
        ]

        try:
            # Run with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.generate_content,
                    content,
                ),
                timeout=self.timeout_seconds,
            )

            # Check for valid response
            if not response or not response.text:
                raise GeminiAPIError(
                    "Empty response from Gemini API",
                    image_id=image_id,
                )

            return response.text

        except asyncio.TimeoutError:
            raise GeminiTimeoutError(
                f"Gemini request timed out after {self.timeout_seconds}s",
                image_id=image_id,
                timeout_seconds=self.timeout_seconds,
            )
        except Exception as e:
            # Check for specific Google API errors
            error_type = type(e).__name__

            if "ResourceExhausted" in error_type or "429" in str(e):
                raise GeminiRateLimitError(
                    f"Gemini rate limit exceeded: {e}",
                    image_id=image_id,
                )

            if "InvalidArgument" in error_type or "400" in str(e):
                raise GeminiAPIError(
                    f"Invalid request to Gemini: {e}",
                    image_id=image_id,
                    status_code=400,
                    cause=e,
                )

            if "PermissionDenied" in error_type or "403" in str(e):
                raise GeminiAPIError(
                    f"Gemini API access denied: {e}",
                    image_id=image_id,
                    status_code=403,
                    cause=e,
                )

            # Generic API error
            raise GeminiAPIError(
                f"Gemini API error: {error_type}: {e}",
                image_id=image_id,
                cause=e,
            )

    async def detect_and_interpret(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
    ) -> Optional[VisionSpec]:
        """Use Gemini for combined detection and interpretation.

        This is the main entry point for fallback processing.

        Args:
            image: Image to process (path or bytes)
            image_id: Image identifier

        Returns:
            VisionSpec if successful, None on recoverable failures

        Raises:
            GeminiNotConfiguredError: If Gemini is not configured
            GeminiAPIError: On API failures after retries exhausted
            GeminiTimeoutError: On timeout after retries exhausted
            GeminiResponseParseError: On invalid response format
        """
        logger.info(f"Starting Gemini fallback for {image_id}")

        # Prepare image
        try:
            image_data = self._prepare_image(image)
        except FileNotFoundError as e:
            logger.error(f"Image not found for {image_id}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid image format for {image_id}: {e}")
            return None

        # Retry loop
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response_text = await self._call_gemini_api(image_data, image_id)
                vision_spec = await self._parse_response(response_text, image_id)

                logger.info(
                    f"Gemini fallback succeeded for {image_id}: "
                    f"{len(vision_spec.merged_output.elements)} elements detected"
                )
                return vision_spec

            except GeminiRateLimitError as e:
                # Rate limit - wait and retry
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6 seconds
                logger.warning(
                    f"Gemini rate limited for {image_id}, "
                    f"waiting {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                await asyncio.sleep(wait_time)
                last_error = e

            except GeminiTimeoutError as e:
                # Timeout - retry with shorter timeout or give up
                logger.warning(
                    f"Gemini timeout for {image_id} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                last_error = e

            except (GeminiNotConfiguredError, GeminiResponseParseError):
                # Non-recoverable errors
                raise

            except GeminiAPIError as e:
                # Other API errors - may be transient
                logger.warning(
                    f"Gemini API error for {image_id}: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                last_error = e

        # All retries exhausted
        if last_error:
            logger.error(
                f"Gemini fallback failed for {image_id} after "
                f"{self.max_retries + 1} attempts: {last_error}"
            )

        return None


# =============================================================================
# Factory Function
# =============================================================================

def create_gemini_client(
    model: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    max_retries: Optional[int] = None,
) -> GeminiVisionClient:
    """Factory function to create GeminiVisionClient.

    Args:
        model: Optional model override
        timeout_seconds: Optional timeout override
        max_retries: Optional retry count override

    Returns:
        Configured GeminiVisionClient
    """
    kwargs = {}
    if model:
        kwargs["model"] = model
    if timeout_seconds:
        kwargs["timeout_seconds"] = timeout_seconds
    if max_retries is not None:
        kwargs["max_retries"] = max_retries

    return GeminiVisionClient(**kwargs)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "GeminiVisionClient",
    "create_gemini_client",
    "DETECTION_PROMPT",
]
