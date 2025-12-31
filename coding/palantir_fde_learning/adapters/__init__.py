"""
Adapters Layer - External Interfaces

This layer contains adapters that connect the application to external
systems and data sources. Adapters translate between the domain's
internal representation and external formats.

Clean Architecture Principle: Adapters are at the outermost layer
and depend on application and domain layers. They implement interfaces
defined in the application layer.

Current adapters:
- KBReader: Reads and parses Knowledge Base markdown files
"""

from palantir_fde_learning.adapters.kb_reader import (
    KBReader,
    KBSection,
    ParsedKBDocument,
)

__all__ = [
    "KBReader",
    "KBSection",
    "ParsedKBDocument",
]
