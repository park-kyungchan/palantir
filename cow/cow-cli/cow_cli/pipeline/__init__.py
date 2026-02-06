"""
COW CLI - Pipeline Module

Stage-based processing pipeline for Mathpix OCR output.
"""
from cow_cli.pipeline.processor import (
    PipelineProcessor,
    PipelineResult,
    PipelineError,
    process_image,
    process_batch,
)

__all__ = [
    "PipelineProcessor",
    "PipelineResult",
    "PipelineError",
    "process_image",
    "process_batch",
]
