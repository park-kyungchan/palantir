from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from lib.oda.ontology.objects.assessment import Assessment, AssessmentStatus
from lib.oda.ontology.objects.session import Session, SessionStatus
from lib.oda.ontology.objects.workspace import Workspace


def test_workspace_slug_and_color_validation_and_activity() -> None:
    ws = Workspace(
        name="My Workspace",
        owner_id="user-123",
        color="fff",
    )

    assert ws.slug == "my-workspace"
    assert ws.color == "#fff"
    assert ws.storage_usage_percent == 0.0

    before_version = ws.version
    ws.record_activity()
    assert ws.last_activity_at is not None
    assert ws.version == before_version + 1

    with pytest.raises(ValueError, match="hex color"):
        Workspace(name="Bad Color", owner_id="user-123", color="#12345")


def test_session_activity_counters_and_lifecycle_helpers() -> None:
    session = Session()
    assert session.session_status == SessionStatus.INITIALIZING

    session.activate()
    assert session.session_status == SessionStatus.ACTIVE

    before_version = session.version
    session.record_message()
    assert session.message_count == 1
    assert session.interaction_count == 1
    assert session.version == before_version + 1

    session.record_answer(is_correct=True)
    assert session.questions_answered == 1
    assert session.correct_answers == 1
    assert session.accuracy_rate == 100.0

    session.pause()
    assert session.session_status == SessionStatus.PAUSED
    session.resume()
    assert session.session_status == SessionStatus.ACTIVE

    # Expiration check (max_duration_minutes is enforced by property)
    expired = Session(
        started_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        max_duration_minutes=1,
    )
    assert expired.is_expired is True


def test_assessment_workflow_start_submit_grade() -> None:
    assessment = Assessment(
        title="Quiz 1",
        items=[
            {"id": "q1", "type": "short_answer", "content": "1+1", "points": 1},
            {"id": "q2", "type": "true_false", "content": "Sky is blue", "points": 1},
        ],
        item_count=2,
        total_points=2.0,
    )

    assert assessment.assessment_status == AssessmentStatus.DRAFT
    assert assessment.is_started is False

    assessment.start()
    assert assessment.is_started is True
    assert assessment.assessment_status == AssessmentStatus.IN_PROGRESS

    assessment.submit_response("q1", "2")
    assessment.submit()
    assert assessment.is_submitted is True
    assert assessment.assessment_status == AssessmentStatus.SUBMITTED

    assessment.grade(item_scores={"q1": 1.0, "q2": 0.0})
    assert assessment.is_graded is True
    assert assessment.assessment_status == AssessmentStatus.GRADED
    assert assessment.score == 1.0
    assert assessment.score_percentage == 50.0


def test_objects_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Workspace(name="X", owner_id="user-1", extra_field="nope")  # type: ignore[arg-type]

