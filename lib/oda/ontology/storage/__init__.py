"""
ODA Storage
===========

Persistence primitives for the ODA runtime (database + repositories).

The database wrapper is required for tests and for runtime components that
create SQLAlchemy sessions.
"""

from lib.oda.ontology.storage.database import (
    Database,
    DatabaseManager,
    get_database,
    initialize_database,
)
from lib.oda.ontology.storage.learner_repository import LearnerRepository
from lib.oda.ontology.storage.proposal_repository import ProposalRepository
from lib.oda.ontology.storage.repositories import (
    ActionLogRepository,
    InsightRepository,
    JobResultRepository,
    PatternRepository,
)

__all__ = [
    "Database",
    "DatabaseManager",
    "get_database",
    "initialize_database",
    "ProposalRepository",
    "InsightRepository",
    "PatternRepository",
    "ActionLogRepository",
    "JobResultRepository",
    "LearnerRepository",
]
