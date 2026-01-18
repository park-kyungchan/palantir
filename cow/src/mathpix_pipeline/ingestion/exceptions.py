"""
Ingestion module exception hierarchy.

Provides specific exception types for different ingestion failure modes:
- ImageFormatError: Unsupported or corrupted image format
- ImageSizeError: Image exceeds size limits
- ValidationError: Image fails validation checks
- StorageError: Storage operation failures
- PreprocessingError: Image preprocessing failures

Schema Version: 2.0.0
"""

from typing import Any, Dict, List, Optional


class IngestionError(Exception):
    """Base exception for all ingestion-related errors.

    Attributes:
        message: Human-readable error description
        details: Additional context about the error
        recoverable: Whether the error is potentially recoverable
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable

    def __str__(self) -> str:
        base = self.message
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base = f"{base} ({detail_str})"
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


class ImageFormatError(IngestionError):
    """Raised when image format is unsupported or file is corrupted."""

    def __init__(
        self,
        message: str,
        format_received: Optional[str] = None,
        supported_formats: Optional[List[str]] = None,
    ):
        details = {}
        if format_received:
            details["format_received"] = format_received
        if supported_formats:
            details["supported_formats"] = supported_formats

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.format_received = format_received
        self.supported_formats = supported_formats


class ImageSizeError(IngestionError):
    """Raised when image exceeds size limits."""

    def __init__(
        self,
        message: str,
        actual_size: Optional[int] = None,
        max_size: Optional[int] = None,
        dimension: Optional[str] = None,
    ):
        details = {}
        if actual_size is not None:
            details["actual_size"] = actual_size
        if max_size is not None:
            details["max_size"] = max_size
        if dimension:
            details["dimension"] = dimension

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.actual_size = actual_size
        self.max_size = max_size
        self.dimension = dimension


class ValidationError(IngestionError):
    """Raised when image fails validation checks."""

    def __init__(
        self,
        message: str,
        checks_failed: Optional[List[str]] = None,
        checks_passed: Optional[List[str]] = None,
    ):
        details = {}
        if checks_failed:
            details["checks_failed"] = checks_failed
        if checks_passed:
            details["checks_passed"] = checks_passed

        super().__init__(
            message=message,
            details=details,
            recoverable=True,  # May be recoverable with preprocessing
        )
        self.checks_failed = checks_failed or []
        self.checks_passed = checks_passed or []


class StorageError(IngestionError):
    """Raised when storage operations fail."""

    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if path:
            details["path"] = path
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            details=details,
            recoverable=True,  # Usually recoverable with retry
        )
        self.path = path
        self.operation = operation


class PreprocessingError(IngestionError):
    """Raised when image preprocessing fails."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            details=details,
            recoverable=True,
        )
        self.operation = operation
        self.reason = reason


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "IngestionError",
    "ImageFormatError",
    "ImageSizeError",
    "ValidationError",
    "StorageError",
    "PreprocessingError",
]
