"""
Versioning & Governance module for Ontology.

Provides tools for managing ontology schema changes with version control,
migration support, and proposal workflow management.

This module exports:
    - SchemaChange: Breaking/non-breaking change classification
    - Migration: Migration operation definitions
    - OntologyProposal: Proposal workflow management

Reference: docs/Ontology.md Section 11 - Versioning & Governance
"""

from ontology_definition.versioning.schema_change import (
    BreakingChangeDetector,
    ChangeType,
    SchemaChange,
    SchemaChangeCategory,
)
from ontology_definition.versioning.migration import (
    Migration,
    MigrationBatch,
    MigrationType,
    TypeCastMatrix,
)
from ontology_definition.versioning.proposal import (
    OntologyProposal,
    ProposalStatus,
    ProposalTask,
    TaskStatus,
)

__all__ = [
    # Schema Change
    "SchemaChange",
    "ChangeType",
    "SchemaChangeCategory",
    "BreakingChangeDetector",
    # Migration
    "Migration",
    "MigrationBatch",
    "MigrationType",
    "TypeCastMatrix",
    # Proposal
    "OntologyProposal",
    "ProposalTask",
    "ProposalStatus",
    "TaskStatus",
]
