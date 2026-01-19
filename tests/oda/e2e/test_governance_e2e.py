from __future__ import annotations

from lib.oda.ontology.governance import CodeQualityGate, QualityGateEnforcement
from lib.oda.ontology.governance.violations import ViolationSeverity, ViolationType


def test_code_quality_gate_reports_violations_and_strict_mode_marks_errors() -> None:
    class BadAction:
        api_name = "namespace.bad_action"

        async def apply_edits(self, params, context):  # pragma: no cover
            return None, []

    report = CodeQualityGate.validate_action_class(BadAction, strict=False)
    assert any(v.type == ViolationType.MISSING_DOCSTRING for v in report.violations)
    assert any(v.type == ViolationType.NON_SNAKE_CASE for v in report.violations)
    assert report.has_errors is False

    strict_report = CodeQualityGate.validate_action_class(BadAction, strict=True)
    assert any(v.severity == ViolationSeverity.ERROR for v in strict_report.violations)
    assert strict_report.has_errors is True


def test_quality_gate_enforcement_mode_switching() -> None:
    original = QualityGateEnforcement.get_mode()
    try:
        QualityGateEnforcement.set_mode("warn")
        assert QualityGateEnforcement.is_enabled() is True
        assert QualityGateEnforcement.should_block() is False

        QualityGateEnforcement.set_mode("off")
        assert QualityGateEnforcement.is_enabled() is False
    finally:
        QualityGateEnforcement.set_mode(original)

