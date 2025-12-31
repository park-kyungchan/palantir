"""
Unit tests for Learning ActionTypes: SaveLearnerStateAction

Run: pytest tests/unit/actions/test_learning_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from scripts.ontology.actions import ActionContext
from scripts.ontology.actions.learning_actions import SaveLearnerStateAction


class TestSaveLearnerStateAction:
    """Tests for SaveLearnerStateAction."""

    @pytest.fixture
    def action(self):
        return SaveLearnerStateAction()

    @pytest.fixture
    def valid_params(self):
        return {
            "user_id": "learner-001",
            "theta": 1.5,
            "knowledge_state": {"algebra": {"p_know": 0.8}}
        }

    def test_api_name_correct(self, action):
        assert action.api_name == "learning.save_state"

    def test_submission_criteria_defined(self, action):
        criteria_names = [c.name for c in action.submission_criteria]
        assert "RequiredField(user_id)" in criteria_names
        assert "RequiredField(theta)" in criteria_names

    def test_validate_missing_fields_fails(self, action, user_context):
        errors = action.validate({}, user_context)
        assert len(errors) >= 2

    @pytest.mark.asyncio
    async def test_apply_edits_saves_learner(self, action, user_context, valid_params):
        with patch('scripts.ontology.actions.learning_actions.get_database') as mock_get_db, \
             patch('scripts.ontology.actions.learning_actions.LearnerRepository') as MockRepo:
            mock_get_db.return_value = MagicMock()
            mock_repo = AsyncMock()
            mock_repo.save.return_value = MagicMock(id="learner-db-id")
            MockRepo.return_value = mock_repo

            result = await action.apply_edits(valid_params, user_context)
            assert result.success is True
