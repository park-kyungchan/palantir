"""
Orion ODA v3.0 - 3-Stage Protocol Framework
=============================================
Enforced governance framework for all ODA operations.

This protocol ensures:
1. Anti-Hallucination: Evidence-based decisions
2. Progressive Deep-Dive: Stage A → B → C
3. Quality Gates: Cannot proceed without passing

Palantir AIP/Foundry Alignment:
- Similar to Foundry Rules pipeline stages
- SubmissionCriteria pattern at protocol level
"""

from .base import (
    Stage,
    StageResult,
    ProtocolResult,
    ProtocolContext,
    ProtocolPolicy,
    ThreeStageProtocol,
    Finding,
    Severity,
    AntiHallucinationError,
)
from .decorators import require_protocol, stage_a, stage_b, stage_c

__all__ = [
    # Core Types
    "Stage",
    "StageResult",
    "ProtocolResult",
    "ProtocolContext",
    "ProtocolPolicy",
    "ThreeStageProtocol",
    "Finding",
    "Severity",
    "AntiHallucinationError",
    # Decorators
    "require_protocol",
    "stage_a",
    "stage_b",
    "stage_c",
]
