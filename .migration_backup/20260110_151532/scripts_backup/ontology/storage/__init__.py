"""
ODA V3.0 Storage Layer
=======================
Async ORM-based persistence with Repository pattern.

Exports:
- Database: Connection manager
- GenericRepository: Base class for all repositories
- Domain-specific repositories: ActionLogRepository, JobResultRepository, etc.
- ORM Models: OrionActionLogModel, JobResultModel, etc.
- Exceptions: ConcurrencyError, EntityNotFoundError, etc.
"""

from __future__ import annotations

import importlib
from typing import Dict

__all__ = [
    "Database",
    "get_database",
    "initialize_database",
    "ConcurrencyError",
    "OptimisticLockError",
    "EntityNotFoundError",
    "ProposalNotFoundError",
    "ValidationError",
    "GenericRepository",
    "RepositoryError",
    "PaginatedResult",
    "ProposalRepository",
    "ProposalQuery",
    "TaskRepository",
    "ActionLogRepository",
    "JobResultRepository",
    "InsightRepository",
    "PatternRepository",
    "ProposalModel",
    "ProposalHistoryModel",
    "OrionActionLogModel",
    "JobResultModel",
    "OrionInsightModel",
    "OrionPatternModel",
]

_LAZY_IMPORTS: Dict[str, str] = {
    "Database": "scripts.ontology.storage.database",
    "get_database": "scripts.ontology.storage.database",
    "initialize_database": "scripts.ontology.storage.database",
    "ConcurrencyError": "scripts.ontology.storage.exceptions",
    "OptimisticLockError": "scripts.ontology.storage.exceptions",
    "EntityNotFoundError": "scripts.ontology.storage.exceptions",
    "ProposalNotFoundError": "scripts.ontology.storage.exceptions",
    "ValidationError": "scripts.ontology.storage.exceptions",
    "GenericRepository": "scripts.ontology.storage.base_repository",
    "RepositoryError": "scripts.ontology.storage.base_repository",
    "PaginatedResult": "scripts.ontology.storage.base_repository",
    "ProposalRepository": "scripts.ontology.storage.proposal_repository",
    "ProposalQuery": "scripts.ontology.storage.proposal_repository",
    "TaskRepository": "scripts.ontology.storage.task_repository",
    "ActionLogRepository": "scripts.ontology.storage.repositories",
    "JobResultRepository": "scripts.ontology.storage.repositories",
    "InsightRepository": "scripts.ontology.storage.repositories",
    "PatternRepository": "scripts.ontology.storage.repositories",
    "ProposalModel": "scripts.ontology.storage.models",
    "ProposalHistoryModel": "scripts.ontology.storage.models",
    "OrionActionLogModel": "scripts.ontology.storage.models",
    "JobResultModel": "scripts.ontology.storage.models",
    "OrionInsightModel": "scripts.ontology.storage.models",
    "OrionPatternModel": "scripts.ontology.storage.models",
}


def __getattr__(name: str):
    module_path = _LAZY_IMPORTS.get(name)
    if not module_path:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_path)
    return getattr(module, name)
