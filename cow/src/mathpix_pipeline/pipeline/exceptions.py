"""
Pipeline exceptions for MathpixPipeline.

This module defines exception classes used for pipeline error handling.

Module Version: 1.0.0
"""

from typing import Optional

from ..schemas.common import PipelineStage


# =============================================================================
# Pipeline Exception
# =============================================================================

class PipelineError(Exception):
    """Exception raised during pipeline execution.

    Attributes:
        message: Error description
        stage: Stage where error occurred
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        stage: Optional[PipelineStage] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}

    def __str__(self) -> str:
        if self.stage:
            return f"[Stage {self.stage.value}] {super().__str__()}"
        return super().__str__()
