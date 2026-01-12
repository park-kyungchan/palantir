"""
3-Stage Protocol Evidence Requirements

Single source of truth for anti-hallucination minimums across:
- ODA protocol implementations (lib.oda.ontology.protocols.*)
- Claude EvidenceTracker / ProtocolRunner (lib.oda.claude.*)

V2.1.x Enhancement: Stage C evidence now uses structured QualityCheck schema.
Reference: lib/oda/ontology/evidence/quality_checks.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from lib.oda.ontology.evidence.quality_checks import StageCEvidence


@dataclass(frozen=True)
class EvidenceRequirements:
    min_files: int
    min_line_refs: int
    min_snippets: int


@dataclass(frozen=True)
class StageCRequirements:
    """
    V2.1.x: Enhanced Stage C requirements with QualityCheck schema.

    Uses structured evidence schema from lib.oda.ontology.evidence.quality_checks.
    """
    min_files: int = 5
    min_line_refs: int = 15
    min_snippets: int = 3
    # Quality check requirements
    required_checks: tuple = ("build", "tests", "lint")
    max_critical_findings: int = 0
    max_error_findings: int = 5

    def validate_stage_c_evidence(self, evidence: "StageCEvidence") -> tuple[bool, List[str]]:
        """
        Validate Stage C evidence against requirements.

        Args:
            evidence: StageCEvidence instance from quality_checks module

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues: List[str] = []

        # Check required quality gates
        executed_checks = {check.name for check in evidence.quality_checks}
        missing_checks = set(self.required_checks) - executed_checks
        if missing_checks:
            issues.append(f"Missing required checks: {missing_checks}")

        # Check critical findings
        if evidence.critical_count > self.max_critical_findings:
            issues.append(
                f"Too many CRITICAL findings: {evidence.critical_count} "
                f"(max: {self.max_critical_findings})"
            )

        # Check error findings
        if evidence.error_count > self.max_error_findings:
            issues.append(
                f"Too many ERROR findings: {evidence.error_count} "
                f"(max: {self.max_error_findings})"
            )

        return len(issues) == 0, issues


EVIDENCE_REQUIREMENTS: dict[str, EvidenceRequirements] = {
    "A_SCAN": EvidenceRequirements(min_files=3, min_line_refs=0, min_snippets=0),
    "B_TRACE": EvidenceRequirements(min_files=5, min_line_refs=10, min_snippets=0),
    "C_VERIFY": EvidenceRequirements(min_files=5, min_line_refs=15, min_snippets=3),
}

# V2.1.x: Enhanced Stage C requirements
STAGE_C_REQUIREMENTS = StageCRequirements()


def get_evidence_requirements(stage: str) -> EvidenceRequirements:
    stage_key = (stage or "").strip()
    return EVIDENCE_REQUIREMENTS.get(stage_key, EVIDENCE_REQUIREMENTS["A_SCAN"])


def get_stage_c_requirements() -> StageCRequirements:
    """Get enhanced Stage C requirements with quality check validation."""
    return STAGE_C_REQUIREMENTS

