"""
Orion ODA - Stage C Quality Evidence (Structured)
=================================================

Defines deterministic, structured evidence for the Stage C ("VERIFY") gate in
the 3-Stage protocol.

The intent is to mirror Foundry-style enforcement: quality checks are explicit
objects (name/status/command/output) and findings are categorized with severity.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class FindingSeverity(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class QualityCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = Field(..., min_length=1, description="Check name (build/tests/lint/typecheck)")
    status: CheckStatus = Field(..., description="Result status")
    command: str = Field(..., min_length=1, description="Executed command")

    output: str = Field(default="", description="Combined stdout/stderr (truncated)")
    exit_code: Optional[int] = Field(default=None, description="Process exit code")
    duration_ms: int = Field(default=0, ge=0, description="Runtime in ms")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the check ran")


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    severity: FindingSeverity
    category: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)

    file: Optional[str] = None
    line: Optional[int] = Field(default=None, ge=1)
    column: Optional[int] = Field(default=None, ge=1)

    code: Optional[str] = None
    auto_fixable: bool = False


class StageCEvidence(BaseModel):
    """
    Aggregate evidence for Stage C verification.

    Passing criteria (by default):
    - Required checks (build/tests/lint) are present and PASSED
    - No ERROR or CRITICAL findings
    - WARNING findings are allowed
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    stage_started_at: datetime = Field(default_factory=datetime.now)
    stage_completed_at: Optional[datetime] = None
    execution_context: Dict[str, Any] = Field(default_factory=dict)

    quality_checks: List[QualityCheck] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)

    required_checks: List[str] = Field(default_factory=lambda: ["build", "tests", "lint"])

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_quality_check(self, check: QualityCheck) -> None:
        self.quality_checks.append(check)

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------

    @property
    def findings_summary(self) -> Dict[str, int]:
        summary = {sev.value: 0 for sev in FindingSeverity}
        for finding in self.findings:
            summary[finding.severity.value] = summary.get(finding.severity.value, 0) + 1
        return summary

    @property
    def warning_count(self) -> int:
        return self.findings_summary[FindingSeverity.WARNING.value]

    @property
    def error_count(self) -> int:
        return self.findings_summary[FindingSeverity.ERROR.value]

    @property
    def critical_count(self) -> int:
        return self.findings_summary[FindingSeverity.CRITICAL.value]

    @property
    def checks_executed(self) -> int:
        return len(self.quality_checks)

    @property
    def checks_passed(self) -> int:
        return sum(1 for c in self.quality_checks if c.status == CheckStatus.PASSED)

    # ------------------------------------------------------------------
    # Gate logic
    # ------------------------------------------------------------------

    def can_pass_stage(self) -> bool:
        executed = {c.name for c in self.quality_checks}
        if set(self.required_checks) - executed:
            return False

        required_by_name = {c.name: c for c in self.quality_checks if c.name in set(self.required_checks)}
        if any(required_by_name[name].status != CheckStatus.PASSED for name in self.required_checks):
            return False

        if self.critical_count > 0:
            return False
        if self.error_count > 0:
            return False
        return True

    def get_stage_duration_ms(self) -> Optional[int]:
        if not self.stage_completed_at:
            return None
        return int((self.stage_completed_at - self.stage_started_at).total_seconds() * 1000)

    def to_summary(self) -> Dict[str, Any]:
        passed = self.can_pass_stage()
        return {
            "status": "PASSED" if passed else "FAILED",
            "checks_executed": self.checks_executed,
            "checks_passed": self.checks_passed,
            "required_checks": list(self.required_checks),
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "findings_summary": self.findings_summary,
            "duration_ms": self.get_stage_duration_ms(),
        }


class QualityCheckSet(BaseModel):
    """
    Optional helper type: a named collection of checks.

    Not required by current tests but useful for future registry-style workflows.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str
    checks: List[QualityCheck] = Field(default_factory=list)


__all__ = [
    "CheckStatus",
    "FindingSeverity",
    "QualityCheck",
    "Finding",
    "StageCEvidence",
    "QualityCheckSet",
]

