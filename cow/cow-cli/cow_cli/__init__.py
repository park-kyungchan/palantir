"""
COW CLI - Layout/Content Separation Pipeline

A CLI tool for processing math/science images through the COW pipeline,
enabling layout/content separation and human-in-the-loop review.
"""

__version__ = "0.1.0"


def __getattr__(name: str):
    """Lazy import to avoid circular import warnings when running as module."""
    if name == "app":
        from cow_cli.cli import app
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["app", "__version__"]
