"""
ODA V3.0 Storage Layer
=======================
Async ORM-based persistence with Repository pattern.

Exports:
- Database: Connection manager
- GenericRepository: Base class for all repositories
- Domain-specific repositories: ActionLogRepository, JobResultRepository, etc.
- ORM Models: OrionActionLogModel, JobResultModel, etc.
"""

from scripts.ontology.storage.database import (
    Database,
    get_database,
    initialize_database,
)
from scripts.ontology.storage.base_repository import (
    GenericRepository,
    ConcurrencyError,
    EntityNotFoundError,
    RepositoryError,
    PaginatedResult,
)
from scripts.ontology.storage.proposal_repository import (
    ProposalRepository,
    ProposalQuery,
    ProposalNotFoundError,
    OptimisticLockError,
)
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
    # Base Repository
    "GenericRepository",
    "ConcurrencyError",
    "EntityNotFoundError",
    "RepositoryError",
    "PaginatedResult",
    # Proposal (existing)
    "ProposalRepository",
    "ProposalQuery",
    "ProposalNotFoundError",
    "OptimisticLockError",
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
