"""
COW CLI - Mathpix API Module

Provides async client, schemas, and exceptions for Mathpix API v3.
"""
from cow_cli.mathpix.client import MathpixClient, create_client
from cow_cli.mathpix.schemas import (
    MathpixRequest,
    MathpixResponse,
    DataOptions,
    WordData,
    LineData,
    Region,
)
from cow_cli.mathpix.exceptions import (
    MathpixError,
    MathpixAuthError,
    MathpixRateLimitError,
    MathpixTimeoutError,
    MathpixNetworkError,
    MathpixAPIError,
    MathpixImageError,
    MathpixConfidenceError,
)

__all__ = [
    # Client
    "MathpixClient",
    "create_client",
    # Schemas
    "MathpixRequest",
    "MathpixResponse",
    "DataOptions",
    "WordData",
    "LineData",
    "Region",
    # Exceptions
    "MathpixError",
    "MathpixAuthError",
    "MathpixRateLimitError",
    "MathpixTimeoutError",
    "MathpixNetworkError",
    "MathpixAPIError",
    "MathpixImageError",
    "MathpixConfidenceError",
]
