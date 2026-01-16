# scripts/ontology/fde_learning/__init__.py
"""
Orion FDE Learning Integration Module.

This module bridges the Palantir FDE Learning System with Orion's
Ontology-Driven Architecture, enabling:
- Learning state synchronization via Ontology Actions
- BKT-based mastery tracking through the Action Registry
- Integration with Orion's Kernel event loop

Follows Palantir AIP/Foundry ODA patterns:
- ActionTypes for all mutations
- SubmissionCriteria for validation
- SideEffects for post-commit processing
"""

from lib.oda.ontology.fde_learning.actions import (
    RecordAttemptAction,
    GetRecommendationAction,
    SyncLearnerStateAction,
    register_fde_learning_actions,
)

__all__ = [
    "RecordAttemptAction",
    "GetRecommendationAction",
    "SyncLearnerStateAction",
    "register_fde_learning_actions",
]
