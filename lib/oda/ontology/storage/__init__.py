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
    "Database": "lib.oda.ontology.storage.database",
    "get_database": "lib.oda.ontology.storage.database",
    "initialize_database": "lib.oda.ontology.storage.database",
    "ConcurrencyError": "lib.oda.ontology.storage.exceptions",
    "OptimisticLockError": "lib.oda.ontology.storage.exceptions",
    "EntityNotFoundError": "lib.oda.ontology.storage.exceptions",
    "ProposalNotFoundError": "lib.oda.ontology.storage.exceptions",
    "ValidationError": "lib.oda.ontology.storage.exceptions",
    "GenericRepository": "lib.oda.ontology.storage.base_repository",
    "RepositoryError": "lib.oda.ontology.storage.base_repository",
    "PaginatedResult": "lib.oda.ontology.storage.base_repository",
    "ProposalRepository": "lib.oda.ontology.storage.proposal_repository",
    "ProposalQuery": "lib.oda.ontology.storage.proposal_repository",
    "TaskRepository": "lib.oda.ontology.storage.task_repository",
    "ActionLogRepository": "lib.oda.ontology.storage.repositories",
    "JobResultRepository": "lib.oda.ontology.storage.repositories",
    "InsightRepository": "lib.oda.ontology.storage.repositories",
    "PatternRepository": "lib.oda.ontology.storage.repositories",
    "ProposalModel": "lib.oda.ontology.storage.models",
    "ProposalHistoryModel": "lib.oda.ontology.storage.models",
    "OrionActionLogModel": "lib.oda.ontology.storage.models",
    "JobResultModel": "lib.oda.ontology.storage.models",
    "OrionInsightModel": "lib.oda.ontology.storage.models",
    "OrionPatternModel": "lib.oda.ontology.storage.models",
}


def __getattr__(name: str):
    module_path = _LAZY_IMPORTS.get(name)
    if not module_path:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_path)
    return getattr(module, name)
