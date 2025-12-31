"""
Palantir FDE Learning System - Clean Architecture Implementation

This module implements a learning system for Palantir Foundry Development Environment (FDE)
using Clean Architecture principles with clear separation between:

- Domain Layer: Core business types and entities (no external dependencies)
- Application Layer: Use cases and business logic (ZPD scoping engine)
- Adapters Layer: External interfaces (KB file readers, APIs)

Architecture follows the Dependency Rule: dependencies point inward toward the domain.
"""

from palantir_fde_learning.domain.types import (
    DifficultyTier,
    KnowledgeComponentState,
    LearningConcept,
    LearningDomain,
)

__all__ = [
    "LearningConcept",
    "DifficultyTier",
    "LearningDomain",
    "KnowledgeComponentState",
]

__version__ = "0.1.0"
