"""
COW CLI - Mathpix API Exceptions

Custom exception classes for Mathpix API error handling.
"""
from typing import Optional


class MathpixError(Exception):
    """Base exception for Mathpix API errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.request_id = request_id
        self.details = details or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.insert(0, f"[{self.code}]")
        if self.request_id:
            parts.append(f"(request_id: {self.request_id})")
        return " ".join(parts)


class MathpixAuthError(MathpixError):
    """Authentication failure (invalid app_id or app_key)."""

    def __init__(self, message: str = "Invalid Mathpix credentials", **kwargs):
        super().__init__(message, code="AUTH_ERROR", **kwargs)


class MathpixRateLimitError(MathpixError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, code="RATE_LIMIT", **kwargs)
        self.retry_after = retry_after


class MathpixTimeoutError(MathpixError):
    """Request timeout."""

    def __init__(self, message: str = "Request timed out", **kwargs):
        super().__init__(message, code="TIMEOUT", **kwargs)


class MathpixNetworkError(MathpixError):
    """Network connectivity error."""

    def __init__(self, message: str = "Network error", **kwargs):
        super().__init__(message, code="NETWORK_ERROR", **kwargs)


class MathpixAPIError(MathpixError):
    """General API error returned by Mathpix."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_info: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(message, code="API_ERROR", **kwargs)
        self.status_code = status_code
        self.error_info = error_info or {}


class MathpixImageError(MathpixError):
    """Image processing error."""

    def __init__(self, message: str, error_id: Optional[str] = None, **kwargs):
        super().__init__(message, code="IMAGE_ERROR", **kwargs)
        self.error_id = error_id


class MathpixConfidenceError(MathpixError):
    """Low confidence result."""

    def __init__(
        self,
        message: str = "Recognition confidence below threshold",
        confidence: Optional[float] = None,
        threshold: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(message, code="LOW_CONFIDENCE", **kwargs)
        self.confidence = confidence
        self.threshold = threshold


# Error mapping for API responses
ERROR_CODE_MAP = {
    "image_not_supported": MathpixImageError,
    "image_max_size": MathpixImageError,
    "math_confidence": MathpixConfidenceError,
    "image_no_content": MathpixImageError,
}


def parse_api_error(
    status_code: int,
    response_body: dict,
    request_id: Optional[str] = None,
) -> MathpixError:
    """
    Parse API response and return appropriate exception.

    Args:
        status_code: HTTP status code
        response_body: Response JSON body
        request_id: Request ID from response

    Returns:
        Appropriate MathpixError subclass
    """
    error_message = response_body.get("error", "Unknown error")
    error_info = response_body.get("error_info", {})

    if status_code == 401:
        return MathpixAuthError(error_message, request_id=request_id)

    if status_code == 429:
        return MathpixRateLimitError(
            error_message,
            request_id=request_id,
            retry_after=response_body.get("retry_after"),
        )

    # Check for specific error IDs
    error_id = error_info.get("id")
    if error_id in ERROR_CODE_MAP:
        return ERROR_CODE_MAP[error_id](
            error_message,
            error_id=error_id,
            request_id=request_id,
            details=error_info,
        )

    return MathpixAPIError(
        error_message,
        status_code=status_code,
        error_info=error_info,
        request_id=request_id,
    )


__all__ = [
    "MathpixError",
    "MathpixAuthError",
    "MathpixRateLimitError",
    "MathpixTimeoutError",
    "MathpixNetworkError",
    "MathpixAPIError",
    "MathpixImageError",
    "MathpixConfidenceError",
    "parse_api_error",
]
