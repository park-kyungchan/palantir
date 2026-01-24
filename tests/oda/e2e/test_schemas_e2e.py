from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from lib.oda.ontology.schemas.governance import OrionActionLog
from lib.oda.ontology.schemas.memory import OrionInsight, OrionPattern
from lib.oda.ontology.schemas.result import Artifact, JobResult


def test_governance_schema_orion_action_log() -> None:
    log = OrionActionLog(
        action_type="file.read",
        status="SUCCESS",
        parameters={"file_path": "/tmp/example.txt"},
    )
    assert log.agent_id == "Orion-Kernel"
    assert log.action_type == "file.read"
    assert "file.read" in log.get_searchable_text()


def test_result_schema_artifact_forbids_extra_fields() -> None:
    artifact = Artifact(
        path="/tmp/output.txt",
        description="Example artifact",
    )
    assert artifact.path == "/tmp/output.txt"

    with pytest.raises(ValidationError):
        Artifact(
            path="/tmp/output.txt",
            description="Example artifact",
            extra_field="nope",
        )


def test_result_schema_job_result_validates_status_literal() -> None:
    result = JobResult(
        job_id="job-123",
        status="SUCCESS",
        output_artifacts=[Artifact(path="/tmp/a.txt", description="A")],
    )
    assert result.status == "SUCCESS"

    with pytest.raises(ValidationError):
        JobResult(job_id="job-123", status="UNKNOWN")


def test_memory_schemas_validate_constraints_and_search_text() -> None:
    insight = OrionInsight(
        provenance={"source_episodic_ids": [], "method": "manual"},
        content={"summary": "Use snake_case for api_name", "domain": "governance", "tags": ["style"]},
        confidence_score=0.9,
    )
    assert "snake_case" in insight.get_searchable_text()

    with pytest.raises(ValidationError):
        OrionInsight(
            provenance={"source_episodic_ids": [], "method": "manual"},
            content={"summary": "bad", "domain": "x", "tags": []},
            confidence_score=2.0,
        )

    pattern = OrionPattern(
        structure={"trigger": "Need to add tests", "steps": ["scan", "trace", "verify"]},
        success_rate=0.5,
    )
    assert "scan" in pattern.get_searchable_text()


def test_learning_context_json_schema_is_valid_json_schema() -> None:
    import lib.oda.ontology.schemas as schemas_pkg

    schema_path = Path(schemas_pkg.__file__).with_name("learning_context_v1.schema.json")
    raw = schema_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    assert data["$schema"].startswith("https://json-schema.org/")
    assert data["type"] == "object"

