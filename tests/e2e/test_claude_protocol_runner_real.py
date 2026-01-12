import pytest

from lib.oda.claude.handlers.audit_handlers import (
    audit_stage_a_handler,
    audit_stage_b_handler,
    audit_stage_c_handler,
)
from lib.oda.claude.protocol_runner import ClaudeProtocolRunner, ProtocolStage


@pytest.mark.asyncio
async def test_claude_protocol_runner_audit_handlers_real() -> None:
    runner = ClaudeProtocolRunner(
        protocol_name="audit",
        target_path="lib/oda",
        use_oda_protocol=False,
    )
    runner.register_stage_handler(ProtocolStage.A_SCAN, audit_stage_a_handler)
    runner.register_stage_handler(ProtocolStage.B_TRACE, audit_stage_b_handler)
    runner.register_stage_handler(ProtocolStage.C_VERIFY, audit_stage_c_handler)

    result = await runner.execute()
    assert result.passed is True
    assert len(result.stages) == 3
    assert all(s.passed for s in result.stages)

    evidence = result.evidence
    assert len(evidence.get("files_viewed", [])) >= 5

