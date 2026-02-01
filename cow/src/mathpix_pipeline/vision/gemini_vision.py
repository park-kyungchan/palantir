"""
Gemini 3 Pro Vision Client for Stage C (Vision Parse).

This module implements the primary vision processing client using Gemini 3 Pro
with thinking mode for accurate mathematical diagram detection and interpretation.

Key Features:
- Thinking mode (LOW/MEDIUM/HIGH) for reasoning transparency
- Exponential backoff with jitter for reliability
- Bounding box detection normalized to 0-1000 range
- Format: [y_min, x_min, y_max, x_max]

Model: gemini-3-pro-preview
Schema Version: 3.0.0

CRITICAL: temperature MUST be 1.0 - lower values cause generation loops.
"""

import asyncio
import base64
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None
    GenerationConfig = None

from ..schemas.common import (
    BBox,
    BBoxFormat,
    CombinedConfidence,
    PipelineStage,
    Provenance,
    ReviewMetadata,
    utc_now,
)
from ..schemas.vision_spec import (
    DetectionElement,
    DetectionLayer,
    DiagramType,
    ElementClass,
    InterpretationLayer,
    InterpretedElement,
    InterpretedRelation,
    MergedElement,
    MergedOutput,
    RelationType,
    VisionSpec,
)
from .exceptions import (
    GeminiAPIError,
    GeminiQuotaError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    InvalidImageError,
    VisionError,
)
from ..utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    get_breaker,
    EXTERNAL_SERVICE_CONFIG,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Token costs per media resolution (from Gemini 3 Pro docs)
MEDIA_RESOLUTION_TOKENS: Dict[str, int] = {
    "LOW": 280,
    "MEDIUM": 560,
    "HIGH": 1120,
}

# Supported image formats with MIME types
SUPPORTED_FORMATS: Dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}

# Magic bytes for format detection
MAGIC_BYTES: List[Tuple[bytes, str]] = [
    (b'\x89PNG\r\n\x1a\n', "image/png"),
    (b'\xff\xd8', "image/jpeg"),
    (b'RIFF', "image/webp"),  # WebP starts with RIFF
    (b'\x00\x00\x00', "image/heic"),  # HEIC/HEIF ftyp
]

# Element class mapping (string -> enum)
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

# Diagram type mapping
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

# Relation type mapping
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
# Detection Prompts
# =============================================================================

DETECTION_PROMPT = """Analyze this mathematical diagram and detect all visual elements.

Return a JSON object with the following structure:
{
  "elements": [
    {
      "id": "elem_001",
      "class": "point|curve|axis|label|grid|arrow|line_segment|circle|polygon|angle|equation_region|text_region|unknown",
      "bbox": [y_min, x_min, y_max, x_max],
      "confidence": 0.0-1.0,
      "label": "optional semantic label"
    }
  ]
}

CRITICAL REQUIREMENTS:
- Bounding boxes use [y_min, x_min, y_max, x_max] format
- All coordinates normalized to 0-1000 range
- Include ALL visible mathematical elements
- Return ONLY valid JSON, no markdown blocks
"""

INTERPRETATION_PROMPT = """Interpret this mathematical diagram and provide semantic understanding.

Diagram type hint: {diagram_type}

Return a JSON object with the following structure:
{
  "diagram_type": "function_graph|coordinate_system|geometry|number_line|bar_chart|pie_chart|venn_diagram|flowchart|table|unknown",
  "description": "Brief description of the diagram",
  "coordinate_system": "cartesian|polar|null",
  "elements": [
    {
      "id": "elem_001",
      "class": "point|curve|axis|label|...",
      "bbox": [y_min, x_min, y_max, x_max],
      "confidence": 0.0-1.0,
      "semantic_label": "Human-readable label (e.g., 'Point A', 'y = x^2')",
      "description": "Detailed description",
      "latex": "LaTeX representation if applicable",
      "coordinates": {{"x": 1, "y": 2}} // if point with known coordinates
      "function_type": "linear|quadratic|exponential|..." // if curve
      "equation": "mathematical equation if identified"
    }
  ],
  "relations": [
    {
      "id": "rel_001",
      "source_id": "elem_001",
      "target_id": "elem_002",
      "type": "label_of|point_on|intersects|parallel_to|perpendicular_to|passes_through|bounded_by|contains",
      "confidence": 0.0-1.0,
      "description": "optional"
    }
  ],
  "overall_confidence": 0.0-1.0
}

CRITICAL REQUIREMENTS:
- Bounding boxes use [y_min, x_min, y_max, x_max] format
- All coordinates normalized to 0-1000 range
- Provide semantic labels for all recognized elements
- Include mathematical relationships between elements
- Return ONLY valid JSON, no markdown blocks
"""

FULL_ANALYSIS_PROMPT = """Perform complete visual analysis of this mathematical diagram.

Detect all elements, interpret their meaning, and identify relationships.

Return a JSON object with:
{
  "diagram_type": "function_graph|coordinate_system|geometry|number_line|...",
  "description": "Brief description",
  "coordinate_system": "cartesian|polar|null",
  "elements": [
    {
      "id": "elem_001",
      "class": "point|curve|axis|label|grid|arrow|line_segment|circle|polygon|angle|equation_region|text_region|unknown",
      "bbox": [y_min, x_min, y_max, x_max],
      "detection_confidence": 0.0-1.0,
      "semantic_label": "Human-readable label",
      "description": "Detailed description",
      "latex": "LaTeX if applicable",
      "coordinates": {{"x": 1, "y": 2}},
      "function_type": "linear|quadratic|...",
      "equation": "equation if identified",
      "interpretation_confidence": 0.0-1.0
    }
  ],
  "relations": [
    {
      "id": "rel_001",
      "source_id": "elem_001",
      "target_id": "elem_002",
      "type": "label_of|point_on|intersects|...",
      "confidence": 0.0-1.0,
      "description": "optional"
    }
  ],
  "overall_confidence": 0.0-1.0
}

CRITICAL REQUIREMENTS:
- Bounding boxes: [y_min, x_min, y_max, x_max] normalized 0-1000
- Detect ALL visible mathematical elements
- Provide semantic interpretation for each element
- Identify ALL mathematical relationships
- Return ONLY valid JSON
"""


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class GeminiVisionConfig:
    """Configuration for Gemini 3 Pro Vision client.

    CRITICAL: temperature MUST be 1.0 - lower values cause generation loops.

    Attributes:
        api_key: Google API key for Gemini access
        model: Model identifier (default: gemini-3-pro-preview)
        thinking_level: Reasoning depth (LOW/MEDIUM/HIGH, default: HIGH)
        temperature: Generation temperature (MUST be 1.0)
        media_resolution: Image processing detail (LOW/MEDIUM/HIGH)
        max_retries: Maximum retry attempts on transient failures
        base_delay: Base delay for exponential backoff (seconds)
        max_delay: Maximum delay cap (seconds)
        timeout: Request timeout (seconds)
    """
    api_key: str
    model: str = "gemini-3-pro-preview"
    thinking_level: Literal["LOW", "MEDIUM", "HIGH"] = "HIGH"
    temperature: float = 1.0  # CRITICAL: MUST be 1.0 - lower causes looping
    media_resolution: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    max_retries: int = 3
    base_delay: float = 2.0  # seconds
    max_delay: float = 60.0  # seconds
    timeout: float = 120.0  # seconds

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("api_key is required")

        if self.temperature != 1.0:
            logger.warning(
                f"temperature={self.temperature} is not recommended. "
                "Gemini 3 Pro requires temperature=1.0 to avoid generation loops."
            )

        if self.thinking_level not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError(
                f"Invalid thinking_level: {self.thinking_level}. "
                "Must be LOW, MEDIUM, or HIGH."
            )

        if self.media_resolution not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError(
                f"Invalid media_resolution: {self.media_resolution}. "
                "Must be LOW, MEDIUM, or HIGH."
            )

    @property
    def token_cost_per_image(self) -> int:
        """Get token cost per image based on media_resolution."""
        return MEDIA_RESOLUTION_TOKENS.get(self.media_resolution, 560)


# =============================================================================
# Gemini Vision Client
# =============================================================================

class GeminiVisionClient:
    """Gemini 3 Pro Vision client for mathematical diagram processing.

    Provides detection and interpretation of visual elements in mathematical
    diagrams using Gemini 3 Pro's thinking mode capabilities.

    Features:
        - Detection: Identify visual elements with bounding boxes
        - Interpretation: Semantic understanding of diagrams
        - Full Pipeline: Combined detection + interpretation
        - Retry Logic: Exponential backoff with jitter

    Usage:
        config = GeminiVisionConfig(api_key="your-key")
        client = GeminiVisionClient(config)
        result = await client.process_image(image_bytes)

    Bounding Box Format:
        [y_min, x_min, y_max, x_max] normalized to 0-1000 range
    """

    def __init__(self, config: GeminiVisionConfig):
        """Initialize the Gemini Vision client.

        Args:
            config: Configuration object with API key and settings

        Raises:
            VisionError: If google-generativeai is not installed
        """
        if not HAS_GENAI:
            raise VisionError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        self.config = config
        self._client = None
        self._initialized = False

        # Circuit breaker for API resilience (Task #69)
        self._breaker = get_breaker("gemini_vision", EXTERNAL_SERVICE_CONFIG)

    def _ensure_initialized(self) -> None:
        """Ensure the client is initialized with API key."""
        if self._initialized:
            return

        genai.configure(api_key=self.config.api_key)
        self._client = genai.GenerativeModel(
            model_name=self.config.model,
            generation_config=GenerationConfig(
                temperature=self.config.temperature,
                response_mime_type="application/json",
            ),
        )
        self._initialized = True
        logger.info(f"Initialized Gemini client with model: {self.config.model}")

    async def _exponential_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter.

        Formula: min(base_delay * 2^attempt + jitter, max_delay)

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            Wait time in seconds
        """
        base_wait = self.config.base_delay * (2 ** attempt)
        jitter = random.uniform(0, 0.1 * base_wait)
        wait_time = min(base_wait + jitter, self.config.max_delay)
        return wait_time

    def _prepare_image(self, image_data: bytes) -> Dict[str, Any]:
        """Prepare image data for Gemini API.

        Args:
            image_data: Raw image bytes

        Returns:
            Dict with mime_type and base64 data

        Raises:
            InvalidImageError: If image format cannot be detected or is unsupported
        """
        if not image_data:
            raise InvalidImageError("Empty image data", reason="empty")

        if len(image_data) > 100 * 1024 * 1024:  # 100MB limit
            raise InvalidImageError(
                f"Image too large: {len(image_data)} bytes (max 100MB)",
                size=len(image_data),
                reason="too_large",
            )

        # Detect format from magic bytes
        mime_type = None
        for magic, fmt in MAGIC_BYTES:
            if image_data[:len(magic)] == magic:
                mime_type = fmt
                break

        if not mime_type:
            # Default to PNG for unknown formats
            mime_type = "image/png"
            logger.warning("Could not detect image format, defaulting to PNG")

        # Base64 encode
        b64_data = base64.b64encode(image_data).decode('utf-8')

        return {
            "mime_type": mime_type,
            "data": b64_data,
        }

    async def _call_api(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call with retry logic and error handling.

        Args:
            request: Request dict with 'image' and 'prompt' keys

        Returns:
            Parsed JSON response dict

        Raises:
            GeminiAPIError: On API failures after retries
            GeminiRateLimitError: On rate limit (429)
            GeminiQuotaError: On quota exceeded (403)
            GeminiTimeoutError: On timeout
            CircuitOpenError: When circuit breaker is open
        """
        # Check circuit breaker state before attempting call
        if self._breaker.is_open:
            retry_after = self._breaker._get_retry_after()
            raise CircuitOpenError(self._breaker.name, retry_after)

        self._ensure_initialized()

        image_data = request.get("image")
        prompt = request.get("prompt", FULL_ANALYSIS_PROMPT)
        image_id = request.get("image_id", "unknown")

        # Build content parts
        content = [
            {
                "mime_type": image_data["mime_type"],
                "data": image_data["data"],
            },
            prompt,
        ]

        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Call with timeout
                start_time = time.time()
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._client.generate_content,
                        content,
                    ),
                    timeout=self.config.timeout,
                )
                elapsed = time.time() - start_time

                if not response or not response.text:
                    raise GeminiAPIError(
                        "Empty response from Gemini API",
                        image_id=image_id,
                    )

                # Parse JSON response
                response_text = response.text.strip()

                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    response_text = "\n".join(lines)

                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as e:
                    raise GeminiAPIError(
                        f"Invalid JSON in response: {e}",
                        image_id=image_id,
                        cause=e,
                    )

                # Record success with circuit breaker
                async with self._breaker._lock:
                    self._breaker._record_success()

                logger.debug(
                    f"API call succeeded for {image_id} "
                    f"in {elapsed:.2f}s (attempt {attempt + 1})"
                )
                return result

            except asyncio.TimeoutError:
                raise GeminiTimeoutError(
                    f"Request timed out after {self.config.timeout}s",
                    image_id=image_id,
                    timeout_seconds=self.config.timeout,
                )

            except GeminiTimeoutError:
                raise  # Don't retry timeouts

            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__

                # Check for rate limit
                if "429" in error_str or "ResourceExhausted" in error_type:
                    if attempt < self.config.max_retries:
                        wait_time = await self._exponential_backoff(attempt)
                        logger.warning(
                            f"Rate limited for {image_id}, "
                            f"waiting {wait_time:.2f}s (attempt {attempt + 1})"
                        )
                        await asyncio.sleep(wait_time)
                        last_error = e
                        continue
                    raise GeminiRateLimitError(
                        f"Rate limit exceeded after {attempt + 1} attempts",
                        image_id=image_id,
                    )

                # Check for quota
                if "403" in error_str or "quota" in error_str.lower():
                    raise GeminiQuotaError(
                        f"Quota exceeded: {e}",
                        image_id=image_id,
                    )

                # Other errors - retry if attempts remain
                if attempt < self.config.max_retries:
                    wait_time = await self._exponential_backoff(attempt)
                    logger.warning(
                        f"API error for {image_id}: {e}, "
                        f"retrying in {wait_time:.2f}s (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(wait_time)
                    last_error = e
                    continue

                # Record failure with circuit breaker before raising
                async with self._breaker._lock:
                    self._breaker._record_failure(e)

                raise GeminiAPIError(
                    f"API call failed: {error_type}: {e}",
                    image_id=image_id,
                    cause=e,
                )

        # Should not reach here, but handle it
        if last_error:
            raise GeminiAPIError(
                f"All {self.config.max_retries + 1} attempts failed",
                image_id=image_id,
                cause=last_error,
            )

    def _parse_element_class(self, class_str: str) -> ElementClass:
        """Parse element class string to enum."""
        normalized = class_str.lower().strip().replace(" ", "_").replace("-", "_")
        return ELEMENT_CLASS_MAP.get(normalized, ElementClass.UNKNOWN)

    def _parse_diagram_type(self, type_str: str) -> DiagramType:
        """Parse diagram type string to enum."""
        normalized = type_str.lower().strip().replace(" ", "_").replace("-", "_")
        return DIAGRAM_TYPE_MAP.get(normalized, DiagramType.UNKNOWN)

    def _parse_relation_type(self, type_str: str) -> Optional[RelationType]:
        """Parse relation type string to enum."""
        normalized = type_str.lower().strip().replace(" ", "_").replace("-", "_")
        return RELATION_TYPE_MAP.get(normalized)

    def _bbox_from_gemini(
        self,
        bbox: List[float],
        image_size: Optional[Tuple[int, int]] = None,
    ) -> BBox:
        """Convert Gemini bbox format to internal BBox.

        Gemini format: [y_min, x_min, y_max, x_max] normalized 0-1000
        Internal format: BBox with x, y, width, height

        Args:
            bbox: Gemini bbox [y_min, x_min, y_max, x_max]
            image_size: Optional (width, height) for denormalization

        Returns:
            BBox object in XYWH format
        """
        if len(bbox) != 4:
            logger.warning(f"Invalid bbox length: {bbox}, using default")
            bbox = [0, 0, 100, 100]

        y_min, x_min, y_max, x_max = bbox

        # Ensure valid ranges
        y_min = max(0, min(1000, y_min))
        x_min = max(0, min(1000, x_min))
        y_max = max(y_min + 1, min(1000, y_max))
        x_max = max(x_min + 1, min(1000, x_max))

        # Convert from 0-1000 to pixel space if image_size provided
        if image_size:
            width, height = image_size
            x = (x_min / 1000) * width
            y = (y_min / 1000) * height
            w = ((x_max - x_min) / 1000) * width
            h = ((y_max - y_min) / 1000) * height
        else:
            # Keep in 0-1000 normalized space
            x = x_min
            y = y_min
            w = x_max - x_min
            h = y_max - y_min

        return BBox(
            x=x,
            y=y,
            width=max(1, w),
            height=max(1, h),
            format=BBoxFormat.XYWH,
        )

    async def detect_elements(
        self,
        image_data: bytes,
        image_id: Optional[str] = None,
    ) -> List[DetectionElement]:
        """Detect visual elements in an image.

        Performs detection-only analysis to identify visual elements
        with bounding boxes and confidence scores.

        Args:
            image_data: Raw image bytes
            image_id: Optional image identifier for logging

        Returns:
            List of DetectionElement objects

        Raises:
            InvalidImageError: If image is invalid
            GeminiAPIError: On API failures
        """
        image_id = image_id or f"img_{int(time.time())}"
        logger.info(f"Detecting elements for {image_id}")

        prepared = self._prepare_image(image_data)
        response = await self._call_api({
            "image": prepared,
            "prompt": DETECTION_PROMPT,
            "image_id": image_id,
        })

        elements: List[DetectionElement] = []
        raw_elements = response.get("elements", [])

        for i, elem in enumerate(raw_elements):
            elem_id = elem.get("id", f"det_{i:03d}")
            element_class = self._parse_element_class(elem.get("class", "unknown"))
            bbox = self._bbox_from_gemini(elem.get("bbox", [0, 0, 100, 100]))
            confidence = float(elem.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            det_elem = DetectionElement(
                id=elem_id,
                element_class=element_class,
                bbox=bbox,
                detection_confidence=confidence,
            )
            elements.append(det_elem)

        logger.info(f"Detected {len(elements)} elements for {image_id}")
        return elements

    async def interpret_diagram(
        self,
        image_data: bytes,
        diagram_type: str = "unknown",
        image_id: Optional[str] = None,
    ) -> InterpretationLayer:
        """Interpret a diagram with semantic understanding.

        Performs interpretation analysis to understand the meaning
        and relationships of visual elements.

        Args:
            image_data: Raw image bytes
            diagram_type: Hint about expected diagram type
            image_id: Optional image identifier

        Returns:
            InterpretationLayer with interpreted elements and relations

        Raises:
            InvalidImageError: If image is invalid
            GeminiAPIError: On API failures
        """
        image_id = image_id or f"img_{int(time.time())}"
        logger.info(f"Interpreting diagram for {image_id} (type: {diagram_type})")

        prepared = self._prepare_image(image_data)
        prompt = INTERPRETATION_PROMPT.format(diagram_type=diagram_type)

        response = await self._call_api({
            "image": prepared,
            "prompt": prompt,
            "image_id": image_id,
        })

        # Parse diagram-level info
        parsed_diagram_type = self._parse_diagram_type(
            response.get("diagram_type", "unknown")
        )
        diagram_description = response.get("description")
        coordinate_system = response.get("coordinate_system")

        # Parse elements
        elements: List[InterpretedElement] = []
        for i, elem in enumerate(response.get("elements", [])):
            elem_id = elem.get("id", f"interp_{i:03d}")

            interp_elem = InterpretedElement(
                id=elem_id,
                semantic_label=elem.get("semantic_label", "Unknown"),
                description=elem.get("description"),
                latex_representation=elem.get("latex"),
                function_type=elem.get("function_type"),
                equation=elem.get("equation"),
                coordinates=elem.get("coordinates"),
                interpretation_confidence=float(elem.get("confidence", 0.5)),
            )
            elements.append(interp_elem)

        # Parse relations
        relations: List[InterpretedRelation] = []
        for i, rel in enumerate(response.get("relations", [])):
            rel_type = self._parse_relation_type(rel.get("type", ""))
            if rel_type is None:
                logger.warning(f"Unknown relation type: {rel.get('type')}")
                continue

            interp_rel = InterpretedRelation(
                id=rel.get("id", f"rel_{i:03d}"),
                source_id=rel.get("source_id", ""),
                target_id=rel.get("target_id", ""),
                relation_type=rel_type,
                confidence=float(rel.get("confidence", 0.5)),
                description=rel.get("description"),
            )
            relations.append(interp_rel)

        layer = InterpretationLayer(
            model=self.config.model,
            elements=elements,
            relations=relations,
            diagram_type=parsed_diagram_type,
            diagram_description=diagram_description,
            coordinate_system=coordinate_system,
        )

        logger.info(
            f"Interpreted {len(elements)} elements, "
            f"{len(relations)} relations for {image_id}"
        )
        return layer

    async def process_image(
        self,
        image_data: bytes,
        image_id: Optional[str] = None,
    ) -> VisionSpec:
        """Full vision processing pipeline.

        Performs combined detection and interpretation in a single pass,
        returning a complete VisionSpec with all layers populated.

        Args:
            image_data: Raw image bytes
            image_id: Optional image identifier

        Returns:
            Complete VisionSpec with detection, interpretation, and merged layers

        Raises:
            InvalidImageError: If image is invalid
            GeminiAPIError: On API failures
        """
        image_id = image_id or f"img_{int(time.time())}"
        start_time = time.time()
        logger.info(f"Processing image {image_id}")

        prepared = self._prepare_image(image_data)
        response = await self._call_api({
            "image": prepared,
            "prompt": FULL_ANALYSIS_PROMPT,
            "image_id": image_id,
        })

        # Parse diagram-level info
        diagram_type = self._parse_diagram_type(
            response.get("diagram_type", "unknown")
        )
        diagram_description = response.get("description")
        coordinate_system = response.get("coordinate_system")

        # Build layers
        detection_elements: List[DetectionElement] = []
        interpreted_elements: List[InterpretedElement] = []
        merged_elements: List[MergedElement] = []

        for i, elem in enumerate(response.get("elements", [])):
            elem_id = elem.get("id", f"elem_{i:03d}")
            element_class = self._parse_element_class(elem.get("class", "unknown"))
            bbox = self._bbox_from_gemini(elem.get("bbox", [0, 0, 100, 100]))

            det_confidence = float(elem.get("detection_confidence", 0.5))
            interp_confidence = float(elem.get("interpretation_confidence", 0.5))
            det_confidence = max(0.0, min(1.0, det_confidence))
            interp_confidence = max(0.0, min(1.0, interp_confidence))

            # Detection element
            det_elem = DetectionElement(
                id=f"det_{elem_id}",
                element_class=element_class,
                bbox=bbox,
                detection_confidence=det_confidence,
            )
            detection_elements.append(det_elem)

            # Interpreted element
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
                interpretation_confidence=interp_confidence,
            )
            interpreted_elements.append(interp_elem)

            # Merged element
            combined_conf = CombinedConfidence(
                detection_confidence=det_confidence,
                interpretation_confidence=interp_confidence,
                combined_value=0.5 * det_confidence + 0.5 * interp_confidence,
                bbox_source=self.config.model,
                label_source=self.config.model,
                detection_weight=0.5,
                interpretation_weight=0.5,
            )

            merged_elem = MergedElement(
                id=elem_id,
                detection_id=f"det_{elem_id}",
                interpretation_id=f"interp_{elem_id}",
                bbox_source=self.config.model,
                label_source=self.config.model,
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
        relations: List[InterpretedRelation] = []
        for i, rel in enumerate(response.get("relations", [])):
            rel_type = self._parse_relation_type(rel.get("type", ""))
            if rel_type is None:
                continue

            interp_rel = InterpretedRelation(
                id=rel.get("id", f"rel_{i:03d}"),
                source_id=rel.get("source_id", ""),
                target_id=rel.get("target_id", ""),
                relation_type=rel_type,
                confidence=float(rel.get("confidence", 0.5)),
                description=rel.get("description"),
            )
            relations.append(interp_rel)

        # Build layers
        detection_layer = DetectionLayer(
            model=self.config.model,
            model_version="3.0.0",
            elements=detection_elements,
        )

        interpretation_layer = InterpretationLayer(
            model=self.config.model,
            elements=interpreted_elements,
            relations=relations,
            diagram_type=diagram_type,
            diagram_description=diagram_description,
            coordinate_system=coordinate_system,
        )

        merged_output = MergedOutput(
            elements=merged_elements,
            relations=relations,
            diagram_type=diagram_type,
            diagram_description=diagram_description,
            coordinate_system=coordinate_system,
            matched_count=len(merged_elements),
            detection_only_count=0,
            interpretation_only_count=0,
        )

        # Build VisionSpec
        elapsed = time.time() - start_time
        provenance = Provenance(
            stage=PipelineStage.VISION_PARSE,
            model=self.config.model,
            processing_time_ms=elapsed * 1000,
        )

        vision_spec = VisionSpec(
            image_id=image_id,
            provenance=provenance,
            detection_layer=detection_layer,
            interpretation_layer=interpretation_layer,
            merged_output=merged_output,
            fallback_used=False,
            total_processing_time_ms=elapsed * 1000,
        )

        logger.info(
            f"Processed {image_id} in {elapsed:.2f}s: "
            f"{len(merged_elements)} elements, {len(relations)} relations"
        )
        return vision_spec


# =============================================================================
# Factory Function
# =============================================================================

def create_gemini_vision_client(
    api_key: str,
    model: str = "gemini-3-pro-preview",
    thinking_level: Literal["LOW", "MEDIUM", "HIGH"] = "HIGH",
    media_resolution: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM",
    **kwargs,
) -> GeminiVisionClient:
    """Factory function to create GeminiVisionClient.

    Args:
        api_key: Google API key
        model: Model identifier
        thinking_level: Reasoning depth
        media_resolution: Image processing detail
        **kwargs: Additional config options

    Returns:
        Configured GeminiVisionClient
    """
    config = GeminiVisionConfig(
        api_key=api_key,
        model=model,
        thinking_level=thinking_level,
        media_resolution=media_resolution,
        **kwargs,
    )
    return GeminiVisionClient(config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Configuration
    "GeminiVisionConfig",
    # Client
    "GeminiVisionClient",
    # Factory
    "create_gemini_vision_client",
    # Constants
    "MEDIA_RESOLUTION_TOKENS",
    "SUPPORTED_FORMATS",
    # Circuit Breaker (re-exported for convenience)
    "CircuitOpenError",
]
