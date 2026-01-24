"""
Export module exception hierarchy.

Provides specific exception types for different export failure modes:
- ExportError: Base exception for all export errors
- StorageError: Storage operation failures
- FormatError: Export format issues
- JobError: Async job failures

Schema Version: 2.0.0
"""

from typing import Any, Dict, List, Optional


class ExportError(Exception):
    """Base exception for all export-related errors.

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


class StorageError(ExportError):
    """Raised when storage operations fail."""

    def __init__(
        self,
        message: str,
        storage_type: Optional[str] = None,
        path: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if storage_type:
            details["storage_type"] = storage_type
        if path:
            details["path"] = path
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            details=details,
            recoverable=True,  # Usually recoverable with retry
        )
        self.storage_type = storage_type
        self.path = path
        self.operation = operation


class FormatError(ExportError):
    """Raised when export format operations fail."""

    def __init__(
        self,
        message: str,
        format_type: Optional[str] = None,
        supported_formats: Optional[List[str]] = None,
    ):
        details = {}
        if format_type:
            details["format_type"] = format_type
        if supported_formats:
            details["supported_formats"] = supported_formats

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.format_type = format_type
        self.supported_formats = supported_formats


class JobError(ExportError):
    """Raised when async export job fails."""

    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        job_status: Optional[str] = None,
    ):
        details = {}
        if job_id:
            details["job_id"] = job_id
        if job_status:
            details["job_status"] = job_status

        super().__init__(
            message=message,
            details=details,
            recoverable=True,
        )
        self.job_id = job_id
        self.job_status = job_status


class ExporterError(ExportError):
    """Raised when an exporter fails during processing."""

    def __init__(
        self,
        message: str,
        exporter_type: Optional[str] = None,
        element_id: Optional[str] = None,
    ):
        details = {}
        if exporter_type:
            details["exporter_type"] = exporter_type
        if element_id:
            details["element_id"] = element_id

        super().__init__(
            message=message,
            details=details,
            recoverable=True,
        )
        self.exporter_type = exporter_type
        self.element_id = element_id


class ContentError(ExportError):
    """Raised when content cannot be exported."""

    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {}
        if content_type:
            details["content_type"] = content_type
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.content_type = content_type
        self.reason = reason


class ExportPipelineError(ExportError):
    """Raised when the export pipeline fails."""

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        details = {}
        if stage:
            details["stage"] = stage
        if cause:
            details["cause"] = str(cause)

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.stage = stage
        self.cause = cause


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "ExportError",
    "StorageError",
    "FormatError",
    "JobError",
    "ExporterError",
    "ContentError",
    "ExportPipelineError",
]
