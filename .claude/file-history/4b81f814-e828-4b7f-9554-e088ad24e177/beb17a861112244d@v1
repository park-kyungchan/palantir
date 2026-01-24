"""
Vision Module Exception Hierarchy.

Provides specific exception types for Stage C (Vision Parse) operations.
Replaces bare `except Exception` patterns with explicit error handling.

Schema Version: 2.0.0
"""

from typing import Optional


# =============================================================================
# Base Exception
# =============================================================================

class VisionError(Exception):
    """Base exception for all vision module errors.

    All vision-specific exceptions inherit from this class,
    allowing for broad catch patterns when needed:

        try:
            result = await process_image(image)
        except VisionError as e:
            logger.error(f"Vision processing failed: {e}")
    """

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        self.image_id = image_id
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:
        base = super().__str__()
        if self.image_id:
            base = f"[{self.image_id}] {base}"
        if self.cause:
            base = f"{base} (caused by: {type(self.cause).__name__}: {self.cause})"
        return base


# =============================================================================
# YOLO Detection Errors
# =============================================================================

class YoloError(VisionError):
    """Base exception for YOLO detection failures."""
    pass


class YoloModelNotFoundError(YoloError):
    """YOLO model file not found or failed to load."""
    pass


class YoloDetectionTimeoutError(YoloError):
    """YOLO detection exceeded timeout limit."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, image_id)


class YoloLowConfidenceError(YoloError):
    """YOLO detection confidence below threshold."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        confidence: Optional[float] = None,
        threshold: Optional[float] = None,
    ):
        self.confidence = confidence
        self.threshold = threshold
        super().__init__(message, image_id)


class YoloNoDetectionsError(YoloError):
    """YOLO found no detections in image."""
    pass


# =============================================================================
# Claude Interpretation Errors
# =============================================================================

class ClaudeError(VisionError):
    """Base exception for Claude interpretation failures."""
    pass


class ClaudeAPIError(ClaudeError):
    """Claude API request failed."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        status_code: Optional[int] = None,
        cause: Optional[Exception] = None,
    ):
        self.status_code = status_code
        super().__init__(message, image_id, cause)


class ClaudeTimeoutError(ClaudeError):
    """Claude interpretation exceeded timeout limit."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, image_id)


class ClaudeResponseParseError(ClaudeError):
    """Failed to parse Claude's response into expected format."""
    pass


class ClaudeLowConfidenceError(ClaudeError):
    """Claude interpretation confidence below threshold."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        confidence: Optional[float] = None,
        threshold: Optional[float] = None,
    ):
        self.confidence = confidence
        self.threshold = threshold
        super().__init__(message, image_id)


# =============================================================================
# Gemini Fallback Errors
# =============================================================================

class GeminiError(VisionError):
    """Base exception for Gemini fallback failures."""
    pass


class GeminiAPIError(GeminiError):
    """Gemini API request failed.

    Wraps google.api_core.exceptions.GoogleAPIError and similar.
    """

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        status_code: Optional[int] = None,
        cause: Optional[Exception] = None,
    ):
        self.status_code = status_code
        super().__init__(message, image_id, cause)


class GeminiTimeoutError(GeminiError):
    """Gemini request exceeded timeout limit."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, image_id)


class GeminiResponseParseError(GeminiError):
    """Failed to parse Gemini's response into VisionSpec format."""
    pass


class GeminiRateLimitError(GeminiError):
    """Gemini API rate limit exceeded."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        retry_after_seconds: Optional[float] = None,
    ):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message, image_id)


class GeminiNotConfiguredError(GeminiError):
    """Gemini API key or configuration missing."""
    pass


# =============================================================================
# Image Processing Errors
# =============================================================================

class ImageError(VisionError):
    """Base exception for image processing failures."""
    pass


class ImageLoadError(ImageError):
    """Failed to load or decode image file."""
    pass


class ImageFormatError(ImageError):
    """Image format not supported or corrupted."""
    pass


class ImageTooLargeError(ImageError):
    """Image exceeds maximum size limits."""

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        actual_size: Optional[tuple] = None,
        max_size: Optional[tuple] = None,
    ):
        self.actual_size = actual_size
        self.max_size = max_size
        super().__init__(message, image_id)


# =============================================================================
# Fallback Chain Errors
# =============================================================================

class FallbackChainExhaustedError(VisionError):
    """All fallback options exhausted without successful result.

    Raised when:
    1. YOLO + Claude fails
    2. Gemini fallback fails
    3. Manual annotation is disabled or fails
    """

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        attempted_methods: Optional[list] = None,
    ):
        self.attempted_methods = attempted_methods or []
        super().__init__(message, image_id)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Base
    "VisionError",
    # YOLO
    "YoloError",
    "YoloModelNotFoundError",
    "YoloDetectionTimeoutError",
    "YoloLowConfidenceError",
    "YoloNoDetectionsError",
    # Claude
    "ClaudeError",
    "ClaudeAPIError",
    "ClaudeTimeoutError",
    "ClaudeResponseParseError",
    "ClaudeLowConfidenceError",
    # Gemini
    "GeminiError",
    "GeminiAPIError",
    "GeminiTimeoutError",
    "GeminiResponseParseError",
    "GeminiRateLimitError",
    "GeminiNotConfiguredError",
    # Image
    "ImageError",
    "ImageLoadError",
    "ImageFormatError",
    "ImageTooLargeError",
    # Fallback
    "FallbackChainExhaustedError",
]
