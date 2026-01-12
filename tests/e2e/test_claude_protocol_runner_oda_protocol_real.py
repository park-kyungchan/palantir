import pytest

from lib.oda.claude.protocol_runner import ClaudeProtocolRunner


@pytest.mark.asyncio
async def test_claude_protocol_runner_audit_oda_protocol_real() -> None:
    runner = ClaudeProtocolRunner(
        protocol_name="audit",
        target_path="lib/oda",
        use_oda_protocol=True,
    )

    result = await runner.execute()
    assert result.passed is True
    assert len(result.stages) == 3
    assert all(s.passed for s in result.stages)

    evidence = result.evidence
    assert len(evidence.get("files_viewed", [])) >= 5

    line_refs = evidence.get("lines_referenced", {}) or {}
    assert sum(len(v) for v in line_refs.values()) >= 15

    assert len(evidence.get("code_snippets", [])) >= 3


@pytest.mark.asyncio
async def test_claude_protocol_runner_planning_oda_protocol_real() -> None:
    runner = ClaudeProtocolRunner(
        protocol_name="planning",
        target_path="lib/oda",
        use_oda_protocol=True,
    )

    result = await runner.execute()
    assert result.passed is True
    assert len(result.stages) == 3
    assert all(s.passed for s in result.stages)

    evidence = result.evidence
    assert len(evidence.get("files_viewed", [])) >= 5

    line_refs = evidence.get("lines_referenced", {}) or {}
    assert sum(len(v) for v in line_refs.values()) >= 15

    assert len(evidence.get("code_snippets", [])) >= 3


@pytest.mark.asyncio
async def test_claude_protocol_runner_execution_oda_protocol_real() -> None:
    runner = ClaudeProtocolRunner(
        protocol_name="execution",
        target_path="lib/oda",
        use_oda_protocol=True,
    )

    result = await runner.execute()
    assert result.passed is True
    assert len(result.stages) == 3
    assert all(s.passed for s in result.stages)

    evidence = result.evidence
    assert len(evidence.get("files_viewed", [])) >= 5

    line_refs = evidence.get("lines_referenced", {}) or {}
    assert sum(len(v) for v in line_refs.values()) >= 15

    assert len(evidence.get("code_snippets", [])) >= 3
