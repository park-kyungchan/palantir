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

from scripts.ontology.storage.database import (
    Database,
    get_database,
    initialize_database,
)
from scripts.ontology.storage.exceptions import (
    ConcurrencyError,
    OptimisticLockError,
    EntityNotFoundError,
    ProposalNotFoundError,
    ValidationError,
)
from scripts.ontology.storage.base_repository import (
    GenericRepository,
    RepositoryError,
    PaginatedResult,
)
from scripts.ontology.storage.proposal_repository import (
    ProposalRepository,
    ProposalQuery,
)
from scripts.ontology.storage.task_repository import TaskRepository
from scripts.ontology.storage.repositories import (
    ActionLogRepository,
    JobResultRepository,
    InsightRepository,
    PatternRepository,
)
from scripts.ontology.storage.models import (
    ProposalModel,
    ProposalHistoryModel,
    OrionActionLogModel,
    JobResultModel,
    OrionInsightModel,
    OrionPatternModel,
)

__all__ = [
    # Database
    "Database",
    "get_database",
    "initialize_database",
    # Exceptions (centralized)
    "ConcurrencyError",
    "OptimisticLockError",
    "EntityNotFoundError",
    "ProposalNotFoundError",
    "ValidationError",
    # Base Repository
    "GenericRepository",
    "RepositoryError",
    "PaginatedResult",
    # Proposal (existing)
    "ProposalRepository",
    "ProposalQuery",
    "TaskRepository",
    # New Repositories (Sprint 2-3)
    "ActionLogRepository",
    "JobResultRepository",
    "InsightRepository",
    "PatternRepository",
    # ORM Models
    "ProposalModel",
    "ProposalHistoryModel",
    "OrionActionLogModel",
    "JobResultModel",
    "OrionInsightModel",
    "OrionPatternModel",
]
