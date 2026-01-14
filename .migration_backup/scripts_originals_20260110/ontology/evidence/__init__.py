"""
Orion ODA v3.0 - Evidence Collection System

Automatic evidence tracking for anti-hallucination enforcement.
Captures files_viewed, lines_referenced, and code_snippets.
"""
from lib.oda.ontology.evidence.collector import (
    EvidenceCollector,
    EvidenceContext,
    EvidenceRecord,
    track_evidence,
    get_current_evidence,
    clear_evidence,
)

__all__ = [
    "EvidenceCollector",
    "EvidenceContext",
    "EvidenceRecord",
    "track_evidence",
    "get_current_evidence",
    "clear_evidence",
]
