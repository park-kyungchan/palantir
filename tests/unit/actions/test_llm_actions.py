"""
Unit tests for LLM ActionTypes: GeneratePlanAction, RouteTaskAction

Run: pytest tests/unit/actions/test_llm_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from lib.oda.ontology.actions import ActionContext, EditType
from lib.oda.ontology.actions.llm_actions import GeneratePlanAction, RouteTaskAction


class TestGeneratePlanAction:
    """Tests for GeneratePlanAction."""

    @pytest.fixture
    def action(self):
        return GeneratePlanAction()

    def test_api_name_correct(self, action):
        assert action.api_name == "llm.generate_plan"

    def test_submission_criteria_requires_goal(self, action):
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(goal)" in criteria_names

    def test_validate_missing_goal_fails(self, action, user_context):
        errors = action.validate({}, user_context)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_apply_edits_returns_plan(self, action, user_context):
        """Verify apply_edits returns a Plan and EditOperation."""
        os_environ_patch = {
            "ORION_PLAN_MODE": "llm",
            "ORION_LLM_API_KEY": "test-api-key",
        }
        mock_plan = MagicMock()
        mock_plan.id = "plan-123"
        mock_plan.model_dump.return_value = {"id": "plan-123"}

        with patch.dict("os.environ", os_environ_patch, clear=False), patch(
            "lib.oda.llm.instructor_client.InstructorClient"
        ) as MockClient:
            MockClient.return_value.generate_async = AsyncMock(return_value=mock_plan)

            plan, edits = await action.apply_edits({"goal": "Test"}, user_context)

            assert plan.id == "plan-123"
            assert len(edits) == 1
            assert edits[0].edit_type == EditType.CREATE


class TestRouteTaskAction:
    """Tests for RouteTaskAction."""

    @pytest.fixture
    def action(self):
        return RouteTaskAction()

    def test_api_name_correct(self, action):
        assert action.api_name == "llm.route_task"

    def test_submission_criteria_requires_request(self, action):
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(request)" in criteria_names
