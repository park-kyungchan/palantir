"""
Mathpix API Module - Backward Compatibility Re-exports.

This module re-exports all Mathpix components for backward compatibility.
New code should import directly from specific modules:
- mathpix_config: MathpixConfig, RetryConfig, exceptions
- mathpix_converter: conversion functions
- mathpix_client: MathpixClient

Schema Version: 2.0.0
"""

# Re-export exceptions and config
from .mathpix_config import (
    MathpixError,
    RateLimitError,
    TimeoutError,
    InvalidImageError,
    ServerError,
    MathpixConfig,
    RetryConfig,
)

# Re-export converter functions
from .mathpix_converter import (
    detection_map_to_content_flags,
    should_trigger_vision_parse,
    line_data_to_segments,
    extract_equations,
    parse_detection_regions,
    detect_writing_style,
)

# Re-export client
from .mathpix_client import MathpixClient


__all__ = [
    # Exceptions
    "MathpixError",
    "RateLimitError",
    "TimeoutError",
    "InvalidImageError",
    "ServerError",
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
