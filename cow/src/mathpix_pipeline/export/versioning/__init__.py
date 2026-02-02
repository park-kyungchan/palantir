"""
Versioning Module for Export Enhancement.

Provides git-style version control for editable YAML documents.

Module Version: 1.0.0
"""

from .version_manager import (
    DiffResult,
    VersionManager,
    VersionMetadata,
)

__all__ = [
    "DiffResult",
    "VersionManager",
    "VersionMetadata",
]
