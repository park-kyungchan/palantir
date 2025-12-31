"""
Domain Layer - Core Business Types

This layer contains pure domain entities with no external dependencies.
All types use Pydantic for validation and serialization.

Clean Architecture Principle: The domain layer is the innermost layer
and has no dependencies on any other layer or external libraries
(except Pydantic for type safety).
"""

from palantir_fde_learning.domain.types import (
    DifficultyTier,
    KnowledgeComponentState,
    LearningConcept,
    LearningDomain,
)

__all__ = [
    "DifficultyTier",
    "LearningDomain",
    "LearningConcept",
    "KnowledgeComponentState",
]
