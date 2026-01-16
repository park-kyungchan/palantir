"""
Claude 3-Stage Protocol Evidence Requirements

Single source of truth for anti-hallucination minimums across:
- EvidenceTracker.validate()
- ClaudeProtocolRunner stage configs
- ODAProtocolAdapter boundary validation

V2.1.x Enhancement: Stage C evidence now uses structured QualityCheck schema.
Reference: lib/oda/ontology/evidence/quality_checks.py
"""

from __future__ import annotations

from lib.oda.ontology.protocols.stage_requirements import (
    EvidenceRequirements,
    EVIDENCE_REQUIREMENTS,
    get_evidence_requirements,
    # V2.1.x: Enhanced Stage C requirements
    StageCRequirements,
    STAGE_C_REQUIREMENTS,
    get_stage_c_requirements,
)

__all__ = [
    "EvidenceRequirements",
    "EVIDENCE_REQUIREMENTS",
    "get_evidence_requirements",
    # V2.1.x: Enhanced Stage C
    "StageCRequirements",
    "STAGE_C_REQUIREMENTS",
    "get_stage_c_requirements",
]
