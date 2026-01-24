from __future__ import annotations

from lib.oda.ontology.evidence.quality_checks import (
    CheckStatus,
    Finding,
    FindingSeverity,
    QualityCheck,
    StageCEvidence,
)


def test_stage_c_evidence_gate_logic_and_counts() -> None:
    evidence = StageCEvidence()
    evidence.add_quality_check(QualityCheck(name="build", status=CheckStatus.PASSED, command="build"))
    evidence.add_quality_check(QualityCheck(name="tests", status=CheckStatus.PASSED, command="tests"))
    evidence.add_quality_check(QualityCheck(name="lint", status=CheckStatus.PASSED, command="lint"))

    evidence.add_finding(
        Finding(
            severity=FindingSeverity.WARNING,
            category="lint",
            message="Line too long",
            file="a.py",
            line=1,
            code="E501",
            auto_fixable=True,
        )
    )

    assert evidence.warning_count == 1
    assert evidence.error_count == 0
    assert evidence.critical_count == 0
    assert evidence.can_pass_stage() is True
    assert evidence.to_summary()["status"] == "PASSED"

    evidence.add_finding(
        Finding(
            severity=FindingSeverity.ERROR,
            category="tests",
            message="One test failed",
            file="tests/test_x.py",
            line=10,
        )
    )
    assert evidence.error_count == 1
    assert evidence.can_pass_stage() is False
    assert evidence.to_summary()["status"] == "FAILED"

