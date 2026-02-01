"""
Mathpix API Client for Stage B (Text Parse).

Implements:
- Full Mathpix API v3 integration
- detection_map → content_flags conversion
- line_data → line_segments conversion
- Stage C trigger logic
- Error handling with retry strategies

Schema Version: 2.0.0
"""

import asyncio
import base64
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import httpx

from ..schemas import (
    BBox,
    ChemicalFormula,
    Confidence,
    ContentFlags,
    ContentType,
    DetectionMapEntry,
    EquationElement,
    LineSegment,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    ReviewSeverity,
    TableCell,
    TableElement,
    TextSpec,
    VisionParseTrigger,
    WordElement,
    WritingStyle,
)
from ..utils.geometry import contour_to_bbox, position_to_bbox
from ..utils.circuit_breaker import (
    CircuitOpenError,
    get_breaker,
    MATHPIX_API_CONFIG,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class MathpixError(Exception):
    """Base exception for Mathpix API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(MathpixError):
    """Rate limit exceeded (HTTP 429)."""

    def __init__(self, retry_after: Optional[int] = None):
        super().__init__("Rate limit exceeded", status_code=429)
        self.retry_after = retry_after or 60


class TimeoutError(MathpixError):
    """Request timeout (HTTP 408, 504)."""
    pass


class InvalidImageError(MathpixError):
    """Invalid image format or content (HTTP 400)."""
    pass


class ServerError(MathpixError):
    """Server error (HTTP 500-503)."""
    pass


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class RetryConfig:
    """Retry configuration for API calls."""
    max_attempts: int = 3
    base_delay_ms: int = 1000
    max_delay_ms: int = 30000
    exponential_base: float = 2.0


@dataclass
class MathpixConfig:
    """Configuration for Mathpix API client.

    Premium API features include extended output formats, chemistry detection,
    table data extraction, and auto-rotation support.
    """
    # Required credentials
    app_id: str
    app_key: str

    # API settings
    base_url: str = "https://api.mathpix.com/v3"
    timeout_seconds: float = 30.0
    retry: RetryConfig = field(default_factory=RetryConfig)

    # Output Formats - Extended for Premium API
    # Supported: latex_styled, text, mathml, asciimath, data
    formats: List[str] = field(default_factory=lambda: [
        "latex_styled", "text", "mathml", "asciimath", "data"
    ])

    # Data Options - Basic
    include_line_data: bool = True
    include_diagram_text: bool = True

    # Data Options - Premium Features
    include_mathml: bool = True       # Include MathML output for equations
    include_asciimath: bool = True    # Include ASCIImath output for equations
    include_smiles: bool = True       # Enable SMILES output for chemistry detection
    include_table_data: bool = True   # Extract structured table data
    include_word_data: bool = False   # Extract word-level data (increases response size)
    include_geo_data: bool = True     # Extract geometry-specific data

    # Advanced Options - Premium Features
    auto_rotate_confidence: bool = True  # Enable auto-rotation with confidence
    pdf_enabled: bool = True             # Enable PDF document processing

    # Chemistry Approval Gate
    # If false, chemistry content requires explicit user approval before processing
    chemistry_auto_approve: bool = False

    # Confidence thresholds
    low_confidence_threshold: float = 0.5
    very_low_confidence_threshold: float = 0.2


# =============================================================================
# Content Flags Conversion
# =============================================================================

def detection_map_to_content_flags(detection_map: Dict[str, Any]) -> ContentFlags:
    """Convert Mathpix detection_map to ContentFlags.

    Mathpix detection_map contains binary flags (0/1) for content types.

    Args:
        detection_map: Mathpix API detection_map response

    Returns:
        ContentFlags with boolean values
    """
    return ContentFlags(
        contains_equation=bool(detection_map.get("contains_math", 0)),
        contains_text=bool(detection_map.get("is_text_only", 0) == 0),
        contains_diagram=bool(detection_map.get("contains_diagram", 0)),
        contains_graph=bool(detection_map.get("contains_graph", 0)),
        contains_geometry=bool(detection_map.get("contains_geometry", 0)),
        contains_table=bool(detection_map.get("contains_table", 0)),
        contains_handwriting=bool(detection_map.get("is_handwritten", 0)),
        contains_chemistry=bool(detection_map.get("contains_chemistry", 0)),
    )


def should_trigger_vision_parse(
    content_flags: ContentFlags,
    confidence: float,
    low_confidence_threshold: float = 0.5,
) -> Tuple[bool, List[VisionParseTrigger]]:
    """Determine if Stage C (Vision Parse) should be triggered.

    Stage C is triggered when:
    1. Content contains diagrams, graphs, or geometry
    2. Overall confidence is below threshold

    Args:
        content_flags: Content type flags from detection_map
        confidence: Overall extraction confidence
        low_confidence_threshold: Confidence below which to trigger

    Returns:
        Tuple of (should_trigger, list of trigger reasons)
    """
    triggers: List[VisionParseTrigger] = []

    if content_flags.contains_diagram:
        triggers.append(VisionParseTrigger.DIAGRAM_EXTRACTION)

    if content_flags.contains_graph:
        triggers.append(VisionParseTrigger.GRAPH_ANALYSIS)

    if content_flags.contains_geometry:
        triggers.append(VisionParseTrigger.GEOMETRY_DETECTION)

    if content_flags.contains_table:
        triggers.append(VisionParseTrigger.TABLE_STRUCTURE)

    if confidence < low_confidence_threshold:
        triggers.append(VisionParseTrigger.LOW_CONFIDENCE_REGION)

    return len(triggers) > 0, triggers


# =============================================================================
# Line Data Conversion
# =============================================================================

def line_data_to_segments(
    line_data: List[Dict[str, Any]],
    image_id: str,
) -> List[LineSegment]:
    """Convert Mathpix line_data to LineSegment list.

    Mathpix line_data contains:
    - type: "math" | "text"
    - text: extracted text
    - latex: LaTeX if math
    - cnt: contour points
    - confidence: per-line confidence

    Args:
        line_data: Mathpix API line_data array
        image_id: Source image identifier for provenance

    Returns:
        List of LineSegment models
    """
    segments: List[LineSegment] = []

    for idx, line in enumerate(line_data):
        # Determine content type
        line_type = line.get("type", "text")
        content_type = ContentType.EQUATION if line_type == "math" else ContentType.TEXT

        # Extract bbox from contour
        contour = line.get("cnt", [])
        bbox = contour_to_bbox(contour) if contour else BBox(x=0, y=0, width=1, height=1)

        # Determine writing style
        is_handwritten = line.get("is_handwritten", False)
        writing_style = WritingStyle.HANDWRITTEN if is_handwritten else WritingStyle.PRINTED

        # Build confidence
        conf_value = line.get("confidence", 0.0)
        confidence = Confidence(
            value=conf_value,
            source="mathpix-api-v3",
            element_type="line",
        )

        segment = LineSegment(
            id=f"{image_id}-line-{idx:03d}",
            bbox=bbox,
            text=line.get("text", ""),
            latex=line.get("latex"),
            confidence=confidence,
            writing_style=writing_style,
            content_type=content_type,
            line_number=idx,
        )
        segments.append(segment)

    return segments


def extract_equations(
    line_data: List[Dict[str, Any]],
    image_id: str,
    low_confidence_threshold: float = 0.5,
) -> List[EquationElement]:
    """Extract equation elements from line_data.

    Filters for math lines and creates EquationElement models.

    Args:
        line_data: Mathpix API line_data array
        image_id: Source image identifier
        low_confidence_threshold: Threshold for review flagging

    Returns:
        List of EquationElement models
    """
    equations: List[EquationElement] = []

    for idx, line in enumerate(line_data):
        if line.get("type") != "math":
            continue

        contour = line.get("cnt", [])
        bbox = contour_to_bbox(contour) if contour else BBox(x=0, y=0, width=1, height=1)

        conf_value = line.get("confidence", 0.0)
        confidence = Confidence(
            value=conf_value,
            source="mathpix-api-v3",
            element_type="equation",
        )

        # Flag for review if low confidence
        review = ReviewMetadata()
        if conf_value < low_confidence_threshold:
            review.review_required = True
            review.review_severity = ReviewSeverity.MEDIUM
            review.review_reason = f"Low confidence: {conf_value:.2f}"

        equation = EquationElement(
            id=f"{image_id}-eq-{idx:03d}",
            bbox=bbox,
            latex=line.get("latex", ""),
            latex_styled=line.get("latex_styled"),
            confidence=confidence,
            asciimath=line.get("asciimath"),
            mathml=line.get("mathml"),
            review=review,
        )
        equations.append(equation)

    return equations


# =============================================================================
# Detection Map Entries
# =============================================================================

def parse_detection_regions(
    response: Dict[str, Any],
    image_id: str,
) -> List[DetectionMapEntry]:
    """Parse detection regions from Mathpix response.

    Extracts individual detected regions with their types and positions.

    Args:
        response: Full Mathpix API response
        image_id: Source image identifier

    Returns:
        List of DetectionMapEntry models
    """
    entries: List[DetectionMapEntry] = []

    # Parse position if available (full image bounds)
    position = response.get("position")
    if position:
        bbox = position_to_bbox(position)
        entries.append(DetectionMapEntry(
            type="full_content",
            bbox=bbox,
            confidence=response.get("confidence", 0.0),
            content=response.get("text"),
        ))

    # Parse data array if available (multiple regions)
    data = response.get("data", [])
    for idx, region in enumerate(data):
        if "position" in region:
            bbox = position_to_bbox(region["position"])
            entries.append(DetectionMapEntry(
                type=region.get("type", "unknown"),
                bbox=bbox,
                confidence=region.get("confidence", 0.0),
                content=region.get("text"),
            ))

    return entries


# =============================================================================
# Writing Style Detection
# =============================================================================

def detect_writing_style(
    response: Dict[str, Any],
    line_data: List[Dict[str, Any]],
) -> WritingStyle:
    """Detect overall writing style from response.

    Args:
        response: Mathpix API response
        line_data: Line data array

    Returns:
        WritingStyle enum value
    """
    # Check detection_map flags
    detection_map = response.get("detection_map", {})
    is_printed = bool(detection_map.get("is_printed", 0))
    is_handwritten = bool(detection_map.get("is_handwritten", 0))

    if is_printed and not is_handwritten:
        return WritingStyle.PRINTED
    if is_handwritten and not is_printed:
        return WritingStyle.HANDWRITTEN

    # Check line_data for mixed content
    handwritten_count = sum(1 for line in line_data if line.get("is_handwritten", False))
    printed_count = len(line_data) - handwritten_count

    if handwritten_count > 0 and printed_count > 0:
        return WritingStyle.MIXED
    if handwritten_count > printed_count:
        return WritingStyle.HANDWRITTEN

    return WritingStyle.PRINTED


# =============================================================================
# Mathpix Client
# =============================================================================

class MathpixClient:
    """Async client for Mathpix API v3.

    Handles:
    - Image to text/math extraction
    - detection_map parsing
    - line_data extraction
    - Error handling with retries

    Usage:
        config = MathpixConfig(app_id="...", app_key="...")
        client = MathpixClient(config)

        text_spec = await client.process_image(image_path)
    """

    def __init__(self, config: MathpixConfig):
        """Initialize Mathpix client.

        Args:
            config: Client configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

        # Circuit breaker for API resilience (Task #69)
        self._breaker = get_breaker("mathpix_api", MATHPIX_API_CONFIG)

    async def __aenter__(self) -> "MathpixClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            headers={
                "app_id": self.config.app_id,
                "app_key": self.config.app_key,
                "Content-Type": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _encode_image(self, image: Union[str, Path, bytes]) -> str:
        """Encode image to base64 data URI.

        Args:
            image: Image path or raw bytes

        Returns:
            Base64 data URI string
        """
        if isinstance(image, (str, Path)):
            path = Path(image)
            with open(path, "rb") as f:
                image_bytes = f.read()
            # Detect MIME type from extension
            ext = path.suffix.lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_types.get(ext, "image/png")
        else:
            image_bytes = image
            mime_type = "image/png"

        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"

    async def _request_with_retry(
        self,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Make API request with exponential backoff retry.

        Args:
            endpoint: API endpoint path
            payload: Request payload

        Returns:
            API response dictionary

        Raises:
            RateLimitError: On 429 after all retries
            TimeoutError: On 408/504 after all retries
            InvalidImageError: On 400 (no retry)
            ServerError: On 500-503 after all retries
            CircuitOpenError: When circuit breaker is open
        """
        # Check circuit breaker state before attempting call
        if self._breaker.is_open:
            retry_after = self._breaker._get_retry_after()
            raise CircuitOpenError(self._breaker.name, retry_after)

        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        last_error: Optional[Exception] = None
        delay_ms = self.config.retry.base_delay_ms

        for attempt in range(self.config.retry.max_attempts):
            try:
                response = await self._client.post(endpoint, json=payload)

                # Success
                if response.status_code == 200:
                    # Record success with circuit breaker
                    self._breaker._record_success()
                    return response.json()

                # Handle specific error codes
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(retry_after=retry_after)

                if response.status_code in (408, 504):
                    raise TimeoutError(
                        f"Request timeout (HTTP {response.status_code})",
                        status_code=response.status_code,
                    )

                if response.status_code == 400:
                    raise InvalidImageError(
                        f"Invalid image: {response.text}",
                        status_code=400,
                        response=response.json() if response.text else None,
                    )

                if 500 <= response.status_code < 600:
                    raise ServerError(
                        f"Server error (HTTP {response.status_code})",
                        status_code=response.status_code,
                    )

                # Unknown error - don't retry
                raise MathpixError(
                    f"Unexpected response: {response.status_code}",
                    status_code=response.status_code,
                )

            except (RateLimitError, TimeoutError, ServerError) as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.retry.max_attempts} failed: {e}"
                )

                if attempt < self.config.retry.max_attempts - 1:
                    # Exponential backoff
                    await asyncio.sleep(delay_ms / 1000)
                    delay_ms = min(
                        delay_ms * self.config.retry.exponential_base,
                        self.config.retry.max_delay_ms,
                    )
                continue

            except InvalidImageError:
                # Don't retry invalid images
                raise

            except httpx.TimeoutException:
                last_error = TimeoutError("HTTP timeout")
                logger.warning(f"Attempt {attempt + 1} timed out")

                if attempt < self.config.retry.max_attempts - 1:
                    await asyncio.sleep(delay_ms / 1000)
                    delay_ms = min(
                        delay_ms * self.config.retry.exponential_base,
                        self.config.retry.max_delay_ms,
                    )
                continue

        # All retries exhausted - record failure with circuit breaker
        if last_error:
            self._breaker._record_failure(last_error)
            raise last_error

        final_error = MathpixError("All retry attempts failed")
        self._breaker._record_failure(final_error)
        raise final_error

    async def process_image(
        self,
        image: Union[str, Path, bytes],
        image_id: Optional[str] = None,
    ) -> TextSpec:
        """Process image through Mathpix API and return TextSpec.

        This is the main entry point for Stage B processing.

        Args:
            image: Image path or raw bytes
            image_id: Optional image identifier (generated if not provided)

        Returns:
            TextSpec with full extraction results

        Raises:
            MathpixError: On API errors after retries
        """
        start_time = time.time()
        image_id = image_id or str(uuid4())

        # Prepare request with all Premium API options
        payload = {
            "src": self._encode_image(image),
            "formats": self.config.formats,
            "data_options": {
                "include_line_data": self.config.include_line_data,
                "include_smiles": self.config.include_smiles,
                "include_table_data": self.config.include_table_data,
                "include_word_data": self.config.include_word_data,
                "include_geo_data": self.config.include_geo_data,
            },
            "include_detected_alphabets": True,
            "include_diagram_text": self.config.include_diagram_text,
        }

        # Make API call
        response = await self._request_with_retry("/text", payload)

        processing_time_ms = (time.time() - start_time) * 1000

        # Convert response to TextSpec
        return self._response_to_text_spec(
            response=response,
            image_id=image_id,
            processing_time_ms=processing_time_ms,
        )

    async def process_pdf(
        self,
        pdf_data: bytes,
        pdf_id: Optional[str] = None,
    ) -> TextSpec:
        """Process PDF document through Mathpix API.

        Args:
            pdf_data: PDF file bytes
            pdf_id: Optional identifier (generated if not provided)

        Returns:
            TextSpec with extracted content

        Raises:
            MathpixError: On API errors after retries
        """
        start_time = time.time()
        pdf_id = pdf_id or str(uuid4())

        # Prepare request for PDF endpoint
        payload = {
            "src": f"data:application/pdf;base64,{base64.b64encode(pdf_data).decode('utf-8')}",
            "formats": self.config.formats,
            "data_options": {
                "include_line_data": self.config.include_line_data,
                "include_smiles": self.config.include_smiles,
                "include_table_data": self.config.include_table_data,
            },
        }

        response = await self._request_with_retry("/pdf", payload)
        processing_time_ms = (time.time() - start_time) * 1000

        return self._response_to_text_spec(
            response=response,
            image_id=pdf_id,
            processing_time_ms=processing_time_ms,
        )

    def _parse_table_data(
        self,
        response: Dict[str, Any],
        image_id: str,
    ) -> List[TableElement]:
        """Parse table data from Mathpix response.

        Args:
            response: Mathpix API response
            image_id: Source image identifier

        Returns:
            List of TableElement models
        """
        tables: List[TableElement] = []
        table_data = response.get("table_data", [])

        for idx, table in enumerate(table_data):
            cells_data = table.get("cells", [])
            rows: List[List[TableCell]] = []

            # Group cells by row
            current_row: List[TableCell] = []
            current_row_idx = 0

            for cell in cells_data:
                row_idx = cell.get("row", 0)
                if row_idx > current_row_idx:
                    if current_row:
                        rows.append(current_row)
                    current_row = []
                    current_row_idx = row_idx

                current_row.append(TableCell(
                    content=cell.get("text", ""),
                    row_span=cell.get("rowspan", 1),
                    col_span=cell.get("colspan", 1),
                    is_header=cell.get("is_header", False),
                ))

            # Append last row
            if current_row:
                rows.append(current_row)

            # Extract bbox if position available
            bbox = None
            if "position" in table:
                bbox = position_to_bbox(table["position"])

            tables.append(TableElement(
                id=f"{image_id}-table-{idx:03d}",
                rows=rows,
                caption=table.get("caption"),
                bbox=bbox,
                confidence=Confidence(
                    value=table.get("confidence", 0.0),
                    source="mathpix-api-v3",
                    element_type="table",
                ),
            ))

        return tables

    def _parse_chemistry_data(
        self,
        response: Dict[str, Any],
        image_id: str,
    ) -> Tuple[List[ChemicalFormula], bool]:
        """Parse chemistry/SMILES data from Mathpix response.

        Args:
            response: Mathpix API response
            image_id: Source image identifier

        Returns:
            Tuple of (chemistry list, chemistry_detected flag)
        """
        chemistry: List[ChemicalFormula] = []
        smiles_data = response.get("smiles_data", [])
        chemistry_detected = len(smiles_data) > 0

        for idx, chem in enumerate(smiles_data):
            # Extract bbox if position available
            bbox = None
            if "position" in chem:
                bbox = position_to_bbox(chem["position"])

            chemistry.append(ChemicalFormula(
                id=f"{image_id}-chem-{idx:03d}",
                smiles=chem.get("smiles", ""),
                inchi=chem.get("inchi"),
                formula_text=chem.get("formula"),
                bbox=bbox,
                confidence=Confidence(
                    value=chem.get("confidence", 0.0),
                    source="mathpix-api-v3",
                    element_type="chemistry",
                ),
                approval_status="pending",
            ))

        return chemistry, chemistry_detected

    def _parse_word_data(
        self,
        response: Dict[str, Any],
        image_id: str,
    ) -> List[WordElement]:
        """Parse word-level OCR data from Mathpix response.

        Args:
            response: Mathpix API response
            image_id: Source image identifier

        Returns:
            List of WordElement models
        """
        words: List[WordElement] = []
        word_data = response.get("word_data", [])

        for idx, word in enumerate(word_data):
            # Extract bbox from position
            bbox = BBox(x=0, y=0, width=1, height=1)
            if "position" in word:
                bbox = position_to_bbox(word["position"])

            words.append(WordElement(
                text=word.get("text", ""),
                bbox=bbox,
                confidence=Confidence(
                    value=word.get("confidence", 0.0),
                    source="mathpix-api-v3",
                    element_type="word",
                ),
                line_index=word.get("line_index", 0),
            ))

        return words

    def _response_to_text_spec(
        self,
        response: Dict[str, Any],
        image_id: str,
        processing_time_ms: float,
    ) -> TextSpec:
        """Convert Mathpix response to TextSpec.

        Args:
            response: Mathpix API response
            image_id: Image identifier
            processing_time_ms: Processing time

        Returns:
            TextSpec with all extracted data
        """
        # Extract detection_map and convert to content_flags
        detection_map = response.get("detection_map", {})
        content_flags = detection_map_to_content_flags(detection_map)

        # Get overall confidence
        confidence = response.get("confidence", 0.0)

        # Determine Stage C triggers
        should_trigger, triggers = should_trigger_vision_parse(
            content_flags=content_flags,
            confidence=confidence,
            low_confidence_threshold=self.config.low_confidence_threshold,
        )

        # Parse line_data
        line_data = response.get("line_data", [])
        line_segments = line_data_to_segments(line_data, image_id)
        equations = extract_equations(
            line_data,
            image_id,
            self.config.low_confidence_threshold,
        )

        # Parse detection regions
        detection_entries = parse_detection_regions(response, image_id)

        # Detect writing style
        writing_style = detect_writing_style(response, line_data)

        # Parse premium API outputs
        mathml = response.get("mathml")
        asciimath = response.get("asciimath")

        # Parse structured data (Premium API)
        tables: List[TableElement] = []
        if self.config.include_table_data:
            tables = self._parse_table_data(response, image_id)

        chemistry: List[ChemicalFormula] = []
        chemistry_detected = False
        if self.config.include_smiles:
            chemistry, chemistry_detected = self._parse_chemistry_data(response, image_id)

        words: List[WordElement] = []
        if self.config.include_word_data:
            words = self._parse_word_data(response, image_id)

        # Determine chemistry approval requirement
        chemistry_approval_required = chemistry_detected and not self.config.chemistry_auto_approve

        # Add chemistry trigger if detected
        if chemistry_detected:
            triggers.append(VisionParseTrigger.CHEMISTRY_DETECTED)
            content_flags.contains_chemistry = True

        # Build review metadata
        review = ReviewMetadata()
        if confidence < self.config.very_low_confidence_threshold:
            review.review_required = True
            review.review_severity = ReviewSeverity.HIGH
            review.review_reason = f"Very low confidence: {confidence:.2f}"
        elif confidence < self.config.low_confidence_threshold:
            review.review_required = True
            review.review_severity = ReviewSeverity.MEDIUM
            review.review_reason = f"Low confidence: {confidence:.2f}"
        elif chemistry_approval_required:
            review.review_required = True
            review.review_severity = ReviewSeverity.MEDIUM
            review.review_reason = "Chemistry content requires approval"

        # Build provenance
        provenance = Provenance(
            stage=PipelineStage.TEXT_PARSE,
            model="mathpix-api-v3",
            processing_time_ms=processing_time_ms,
        )

        return TextSpec(
            image_id=image_id,
            provenance=provenance,
            content_flags=content_flags,
            vision_parse_triggers=triggers,
            writing_style=writing_style,
            text=response.get("text", ""),
            latex=response.get("latex_styled") or response.get("latex"),
            confidence=confidence,
            mathml=mathml,
            asciimath=asciimath,
            line_segments=line_segments,
            equations=equations,
            detection_map=detection_entries,
            tables=tables,
            chemistry=chemistry,
            words=words,
            chemistry_detected=chemistry_detected,
            chemistry_approval_required=chemistry_approval_required,
            raw_response=response,
            review=review,
            processing_time_ms=processing_time_ms,
        )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Exceptions
    "MathpixError",
    "RateLimitError",
    "TimeoutError",
    "InvalidImageError",
    "ServerError",
    "CircuitOpenError",
    # Config
    "MathpixConfig",
    "RetryConfig",
    # Client
    "MathpixClient",
    # Helper functions
    "detection_map_to_content_flags",
    "should_trigger_vision_parse",
    "line_data_to_segments",
    "extract_equations",
    "parse_detection_regions",
    "detect_writing_style",
]
