"""
Orion ODA v3.0 - Quality Check Evidence Schemas
================================================

Pydantic models for complete Stage C evidence in 3-Stage Protocol.
Provides structured representation of quality gates: build, tests, lint, typecheck.

Reference: .agent/plans/claude_code_v21x_feature_enhancement.md (Phase 4.1)
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CheckStatus(str, Enum):
    """Status of a quality check execution."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RUNNING = "running"
    TIMEOUT = "timeout"


class QualityCheck(BaseModel):
    """
    Individual quality check result.

    Represents a single quality gate execution (build, tests, lint, typecheck).
    """

    name: str = Field(
        ...,
        description="Check name: 'build', 'tests', 'lint', 'typecheck'"
    )
    status: CheckStatus = Field(
        ...,
        description="Execution status of the check"
    )
    command: str = Field(
        ...,
        description="Command that was executed (e.g., 'pytest', 'ruff check')"
    )
    output: Optional[str] = Field(
        default=None,
        description="Stdout/stderr output (truncated if large)"
    )
    coverage: Optional[str] = Field(
        default=None,
        description="Test coverage percentage if applicable"
    )
    duration_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Execution duration in milliseconds"
    )
    exit_code: Optional[int] = Field(
        default=None,
        description="Process exit code"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the check was executed"
    )

    class Config:
        use_enum_values = True


class FindingSeverity(str, Enum):
    """Severity levels for findings."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class Finding(BaseModel):
    """
    Individual finding from quality checks.

    Represents a lint error, test failure, type error, or build issue.
    """

    severity: FindingSeverity = Field(
        ...,
        description="Severity: CRITICAL, ERROR, WARNING, INFO"
    )
    category: str = Field(
        ...,
        description="Category: 'lint', 'test', 'type', 'build', 'security'"
    )
    message: str = Field(
        ...,
        description="Human-readable finding description"
    )
    file: str = Field(
        ...,
        description="Relative file path where finding occurred"
    )
    line: int = Field(
        ...,
        ge=1,
        description="Line number (1-indexed)"
    )
    column: Optional[int] = Field(
        default=None,
        ge=1,
        description="Column number (1-indexed)"
    )
    code: Optional[str] = Field(
        default=None,
        description="Error/warning code (e.g., 'E501', 'F401')"
    )
    auto_fixable: bool = Field(
        default=False,
        description="Whether this finding can be auto-fixed"
    )
    fix_suggestion: Optional[str] = Field(
        default=None,
        description="Suggested fix if available"
    )

    class Config:
        use_enum_values = True


class StageCEvidence(BaseModel):
    """
    Complete Stage C evidence collection.

    Aggregates all quality checks and findings for Stage C: VERIFY gate.
    Used to determine if code changes are safe to deploy.

    Example:
        evidence = StageCEvidence(
            quality_checks=[
                QualityCheck(name="tests", status="passed", command="pytest"),
                QualityCheck(name="lint", status="passed", command="ruff check"),
            ],
            findings=[],
            findings_summary={"CRITICAL": 0, "ERROR": 0, "WARNING": 2, "INFO": 5},
            critical_count=0,
        )

        if evidence.can_pass_stage():
            print("Stage C: PASSED")
    """

    quality_checks: List[QualityCheck] = Field(
        default_factory=list,
        description="List of quality check results"
    )
    findings: List[Finding] = Field(
        default_factory=list,
        description="List of findings from all checks"
    )
    findings_summary: Dict[str, int] = Field(
        default_factory=lambda: {
            "CRITICAL": 0,
            "ERROR": 0,
            "WARNING": 0,
            "INFO": 0,
        },
        description="Count of findings by severity"
    )
    critical_count: int = Field(
        default=0,
        ge=0,
        description="Number of CRITICAL findings (must be 0 to pass)"
    )
    error_count: int = Field(
        default=0,
        ge=0,
        description="Number of ERROR findings"
    )
    verification_commands: List[str] = Field(
        default_factory=list,
        description="Commands used for verification"
    )
    execution_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution context (env, config, etc.)"
    )
    stage_started_at: Optional[datetime] = Field(
        default=None,
        description="When Stage C verification started"
    )
    stage_completed_at: Optional[datetime] = Field(
        default=None,
        description="When Stage C verification completed"
    )

    def can_pass_stage(self) -> bool:
        """
        Determine if Stage C can pass.

        Rules:
            - Zero CRITICAL findings
            - All required checks executed
            - No FAILED required checks
        """
        if self.critical_count > 0:
            return False

        required_checks = {"build", "tests", "lint"}
        executed_checks = {check.name for check in self.quality_checks}

        if not required_checks.issubset(executed_checks):
            return False

        for check in self.quality_checks:
            if check.name in required_checks and check.status == CheckStatus.FAILED:
                return False

        return True

    def add_finding(self, finding: Finding) -> None:
        """Add a finding and update summary counts."""
        self.findings.append(finding)
        self.findings_summary[finding.severity] = (
            self.findings_summary.get(finding.severity, 0) + 1
        )
        if finding.severity == FindingSeverity.CRITICAL:
            self.critical_count += 1
        elif finding.severity == FindingSeverity.ERROR:
            self.error_count += 1

    def add_quality_check(self, check: QualityCheck) -> None:
        """Add a quality check result."""
        self.quality_checks.append(check)
        self.verification_commands.append(check.command)

    def get_stage_duration_ms(self) -> Optional[int]:
        """Calculate total Stage C duration in milliseconds."""
        if self.stage_started_at and self.stage_completed_at:
            delta = self.stage_completed_at - self.stage_started_at
            return int(delta.total_seconds() * 1000)
        return None

    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary for reporting."""
        return {
            "status": "PASSED" if self.can_pass_stage() else "FAILED",
            "checks_executed": len(self.quality_checks),
            "checks_passed": sum(
                1 for c in self.quality_checks if c.status == CheckStatus.PASSED
            ),
            "findings": self.findings_summary,
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "duration_ms": self.get_stage_duration_ms(),
        }

    class Config:
        use_enum_values = True
