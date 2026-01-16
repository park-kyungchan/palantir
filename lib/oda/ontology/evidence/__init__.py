"""
Orion ODA v3.0 - Evidence Collection System

Automatic evidence tracking for anti-hallucination enforcement.
Captures files_viewed, lines_referenced, and code_snippets.

Modules:
    - collector: @auto_evidence decorator for evidence tracking
    - quality_checks: Stage C quality check evidence schemas
"""
from lib.oda.ontology.evidence.collector import (
    EvidenceCollector,
    EvidenceContext,
    EvidenceRecord,
    auto_evidence,
    track_evidence,
    get_current_evidence,
    clear_evidence,
    evidence_scope,
    get_collector,
)
from lib.oda.ontology.evidence.quality_checks import (
    CheckStatus,
    QualityCheck,
    Finding,
    FindingSeverity,
    StageCEvidence,
)

__all__ = [
    # Collector
    "EvidenceCollector",
    "EvidenceContext",
    "EvidenceRecord",
    "auto_evidence",
    "track_evidence",
    "get_current_evidence",
    "clear_evidence",
    "evidence_scope",
    "get_collector",
    # Quality Checks (Stage C)
    "CheckStatus",
    "QualityCheck",
    "Finding",
    "FindingSeverity",
    "StageCEvidence",
]
