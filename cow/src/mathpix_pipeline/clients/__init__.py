"""
Math Image Parsing Pipeline - API Clients

Provides Mathpix API integration for Stage B (Text Parse).
"""

from .mathpix_config import (
    MathpixConfig,
    RetryConfig,
    MathpixError,
    RateLimitError,
    TimeoutError,
    InvalidImageError,
    ServerError,
)
from .mathpix_converter import (
    detection_map_to_content_flags,
    should_trigger_vision_parse,
    line_data_to_segments,
    extract_equations,
    parse_detection_regions,
    detect_writing_style,
)
from .mathpix_client import MathpixClient

__all__ = [
    # Client
    "MathpixClient",
    # Config
    "MathpixConfig",
    "RetryConfig",
    # Exceptions
    "MathpixError",
    "RateLimitError",
    "TimeoutError",
    "InvalidImageError",
    "ServerError",
    # Converters
    "detection_map_to_content_flags",
    "should_trigger_vision_parse",
    "line_data_to_segments",
    "extract_equations",
    "parse_detection_regions",
    "detect_writing_style",
]
