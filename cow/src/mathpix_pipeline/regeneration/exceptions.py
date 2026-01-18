"""
Regeneration module exception hierarchy.

Provides specific exception types for different regeneration failure modes:
- RegenerationError: Base exception for all regeneration errors
- TemplateError: Template loading or rendering failures
- LaTeXGenerationError: LaTeX-specific generation failures
- SVGGenerationError: SVG/TikZ generation failures
- DeltaComparisonError: Comparison operation failures

Schema Version: 2.0.0
"""

from typing import Any, Dict, List, Optional


class RegenerationError(Exception):
    """Base exception for all regeneration-related errors.

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


class TemplateError(RegenerationError):
    """Raised when template loading or rendering fails."""

    def __init__(
        self,
        message: str,
        template_name: Optional[str] = None,
        template_path: Optional[str] = None,
        render_context: Optional[Dict[str, Any]] = None,
    ):
        details = {}
        if template_name:
            details["template_name"] = template_name
        if template_path:
            details["template_path"] = template_path
        if render_context:
            details["context_keys"] = list(render_context.keys())

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.template_name = template_name
        self.template_path = template_path


class LaTeXGenerationError(RegenerationError):
    """Raised when LaTeX generation fails."""

    def __init__(
        self,
        message: str,
        element_id: Optional[str] = None,
        element_type: Optional[str] = None,
        latex_fragment: Optional[str] = None,
    ):
        details = {}
        if element_id:
            details["element_id"] = element_id
        if element_type:
            details["element_type"] = element_type
        if latex_fragment:
            # Truncate long fragments
            details["latex_fragment"] = latex_fragment[:100] + "..." if len(latex_fragment) > 100 else latex_fragment

        super().__init__(
            message=message,
            details=details,
            recoverable=True,  # Often can be recovered with fallback
        )
        self.element_id = element_id
        self.element_type = element_type


class SVGGenerationError(RegenerationError):
    """Raised when SVG or TikZ generation fails."""

    def __init__(
        self,
        message: str,
        element_id: Optional[str] = None,
        output_type: Optional[str] = None,  # 'svg' or 'tikz'
        coordinates: Optional[Dict[str, float]] = None,
    ):
        details = {}
        if element_id:
            details["element_id"] = element_id
        if output_type:
            details["output_type"] = output_type
        if coordinates:
            details["coordinates"] = coordinates

        super().__init__(
            message=message,
            details=details,
            recoverable=True,
        )
        self.element_id = element_id
        self.output_type = output_type


class DeltaComparisonError(RegenerationError):
    """Raised when delta comparison fails."""

    def __init__(
        self,
        message: str,
        comparison_type: Optional[str] = None,
        original_type: Optional[str] = None,
        regenerated_type: Optional[str] = None,
    ):
        details = {}
        if comparison_type:
            details["comparison_type"] = comparison_type
        if original_type:
            details["original_type"] = original_type
        if regenerated_type:
            details["regenerated_type"] = regenerated_type

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.comparison_type = comparison_type


class UnsupportedNodeTypeError(RegenerationError):
    """Raised when a node type cannot be regenerated."""

    def __init__(
        self,
        message: str,
        node_type: Optional[str] = None,
        supported_types: Optional[List[str]] = None,
    ):
        details = {}
        if node_type:
            details["node_type"] = node_type
        if supported_types:
            details["supported_types"] = supported_types

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.node_type = node_type
        self.supported_types = supported_types


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "RegenerationError",
    "TemplateError",
    "LaTeXGenerationError",
    "SVGGenerationError",
    "DeltaComparisonError",
    "UnsupportedNodeTypeError",
]
