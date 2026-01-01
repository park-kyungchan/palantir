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
- Repository: Persistence layer for learner state

ODA Alignment: Adapters implement the "Gateway" pattern from Palantir's
Ontology-Driven Architecture, providing clean interfaces to external systems.
"""

from palantir_fde_learning.adapters.kb_reader import (
    KBReader,
    KBSection,
    ParsedKBDocument,
)
from palantir_fde_learning.adapters.repository import (
    Repository,
    LearnerRepository,
    SQLiteLearnerRepository,
)

__all__ = [
    # KB Reader
    "KBReader",
    "KBSection",
    "ParsedKBDocument",
    # Repository
    "Repository",
    "LearnerRepository",
    "SQLiteLearnerRepository",
]
