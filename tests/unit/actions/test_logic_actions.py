"""
Unit tests for Logic ActionTypes: ExecuteLogicAction

Run: pytest tests/unit/actions/test_logic_actions.py -v --asyncio-mode=auto
"""

from __future__ import annotations

from unittest.mock import patch
import pytest

from lib.oda.ontology.actions import ActionContext
from lib.oda.ontology.actions.logic_actions import ExecuteLogicAction


class TestExecuteLogicAction:
    """Tests for ExecuteLogicAction."""

    @pytest.fixture
    def action(self):
        with patch('scripts.ontology.actions.logic_actions.InstructorClient'), \
             patch('scripts.ontology.actions.logic_actions.LogicEngine'):
            return ExecuteLogicAction()

    def test_api_name_correct(self, action):
        assert action.api_name == "execute_logic"

    def test_requires_proposal_false(self, action):
        assert action.requires_proposal is False

    @pytest.mark.asyncio
    async def test_apply_edits_returns_result(self, action, user_context):
        params = {"function_name": "TestFunc", "input_data": {}}
        result, edits = await action.apply_edits(params, user_context)

        assert isinstance(result, dict)
        assert result["function"] == "TestFunc"
        assert len(edits) == 0
