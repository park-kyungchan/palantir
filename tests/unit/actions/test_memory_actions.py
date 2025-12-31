"""
Unit tests for Memory ActionTypes: SaveInsightAction, SavePatternAction

Run: pytest tests/unit/actions/test_memory_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from scripts.ontology.actions import ActionContext, ActionResult
from scripts.ontology.actions.memory_actions import SaveInsightAction, SavePatternAction


class TestSaveInsightAction:
    """Tests for SaveInsightAction."""

    @pytest.fixture
    def action(self):
        return SaveInsightAction()

    @pytest.fixture
    def valid_insight_params(self):
        return {
            "content": {
                "summary": "Test insight summary",
                "domain": "testing",
                "tags": ["unit-test"]
            },
            "provenance": {
                "source_episodic_ids": ["ep-001"],
                "method": "automated"
            }
        }

    def test_submission_criteria_defined(self, action):
        """Verify submission criteria includes RequiredField for content and provenance."""
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(content)" in criteria_names
        assert "RequiredField(provenance)" in criteria_names

    def test_validate_missing_content_fails(self, action, user_context):
        """Verify validation fails when content is missing."""
        errors = action.validate({"provenance": {}}, user_context)
        assert len(errors) > 0

    def test_validate_valid_params_passes(self, action, user_context, valid_insight_params):
        """Verify validation passes for valid parameters."""
        errors = action.validate(valid_insight_params, user_context)
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_apply_edits_creates_insight(self, action, user_context, valid_insight_params):
        """Verify apply_edits creates an insight."""
        with patch('scripts.ontology.actions.memory_actions.get_database') as mock_get_db, \
             patch('scripts.ontology.actions.memory_actions.InsightRepository') as MockRepo:
            mock_get_db.return_value = MagicMock()
            MockRepo.return_value = AsyncMock()

            result = await action.apply_edits(valid_insight_params, user_context)
            assert isinstance(result, ActionResult)
            assert result.success is True


class TestSavePatternAction:
    """Tests for SavePatternAction."""

    @pytest.fixture
    def action(self):
        return SavePatternAction()

    def test_submission_criteria_defined(self, action):
        """Verify submission criteria includes RequiredField for structure."""
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(structure)" in criteria_names
