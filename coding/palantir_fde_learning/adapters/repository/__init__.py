# adapters/repository/__init__.py
"""
Repository Pattern Implementation (ODA-Aligned)

This module provides data persistence abstractions following Clean Architecture
and Palantir ODA principles:

1. Interface-First Design: Abstract base classes define contracts
2. Async-First: All I/O operations use async/await
3. Type Safety: Generic types ensure type-safe operations
4. Dependency Injection: Repositories can be swapped via DI

Architecture Mapping:
- Repository Pattern -> Palantir DAO Pattern (UserDao, WorldDao)
- LearnerRepository -> Domain-specific data access
- SQLiteLearnerRepository -> Concrete implementation

Usage:
    from palantir_fde_learning.adapters.repository import (
        LearnerRepository,
        SQLiteLearnerRepository,
    )
    
    repo = SQLiteLearnerRepository("learner_state.db")
    profile = await repo.find_by_id("user123")
"""

from palantir_fde_learning.adapters.repository.base import Repository
from palantir_fde_learning.adapters.repository.learner_repository import LearnerRepository
from palantir_fde_learning.adapters.repository.sqlite import SQLiteLearnerRepository

__all__ = [
    "Repository",
    "LearnerRepository",
    "SQLiteLearnerRepository",
]
