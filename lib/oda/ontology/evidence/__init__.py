"""
Orion ODA - Evidence Package
============================

This package provides structured evidence models used across the 3-Stage
protocol (SCAN → TRACE → VERIFY). In particular, Stage C ("VERIFY") relies on
structured quality check evidence that can be evaluated deterministically.
"""

from lib.oda.ontology.evidence.quality_checks import (
    CheckStatus,
    Finding,
    FindingSeverity,
    QualityCheck,
    StageCEvidence,
)


class EvidenceCollector:
    """
    Minimal placeholder for evidence collection utilities.

    The current codebase primarily uses structured Stage C evidence via
    `StageCEvidence`. This collector exists to keep the public API stable.
    """

    def __init__(self) -> None:
        self.records: list[dict] = []

    def add(self, record: dict) -> None:
        self.records.append(record)


def auto_evidence(func):
    """
    Decorator to wrap an async function and capture basic timing evidence.

    This is a lightweight implementation intended to support documentation
    examples; higher-fidelity evidence collection can be layered on later.
    """

    import functools
    import time

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.monotonic()
        try:
            return await func(*args, **kwargs)
        finally:
            _ = time.monotonic() - start

    return wrapper


__all__ = [
    "CheckStatus",
    "Finding",
    "FindingSeverity",
    "QualityCheck",
    "StageCEvidence",
    "EvidenceCollector",
    "auto_evidence",
]

