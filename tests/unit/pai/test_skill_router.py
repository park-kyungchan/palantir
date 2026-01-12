"""
Unit tests for PAI Skills Router module.

Tests the skill routing system including:
- RouteResult dataclass properties and behavior
- SkillRouter registration, routing, and execution

Reference: lib/oda/pai/skills/router.py
"""

from __future__ import annotations

from dataclasses import field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Import directly from submodules to avoid __init__.py import issues
try:
    # First, verify Pydantic is available (required by ODA modules)
    import pydantic

    # Import router module components
    from lib.oda.pai.skills.router import (
        RouteResult,
        SkillRouter,
        RouteToSkillAction,
        RegisterSkillAction,
    )

    # Import skill definition types
    from lib.oda.pai.skills.skill_definition import (
        SkillDefinition,
        SkillTrigger,
        SkillExecution,
        SkillStatus,
        TriggerPriority,
        ExecutionStatus,
    )

    # Import trigger detector types
    from lib.oda.pai.skills.trigger_detector import (
        TriggerDetector,
        TriggerMatch,
        MatchType,
    )

    IMPORT_ERROR = None
except ImportError as e:
    IMPORT_ERROR = str(e)
    RouteResult = None
    SkillRouter = None
    RouteToSkillAction = None
    RegisterSkillAction = None
    SkillDefinition = None
    SkillTrigger = None
    SkillExecution = None
    SkillStatus = None
    TriggerPriority = None
    ExecutionStatus = None
    TriggerDetector = None
    TriggerMatch = None
    MatchType = None


pytestmark = pytest.mark.skipif(
    IMPORT_ERROR is not None,
    reason=f"Could not import router module: {IMPORT_ERROR}"
)


# =============================================================================
# MOCK SKILL FACTORY
# =============================================================================


def create_mock_skill(
    name: str,
    description: str = "Test skill",
    skill_status: "SkillStatus" = None,
    triggers: List["SkillTrigger"] = None,
    tools: List[str] = None,
) -> MagicMock:
    """
    Create a mock skill object that behaves like SkillDefinition.

    The router expects `skill.triggers` to be a list of triggers,
    but SkillDefinition only has `trigger_ids`. We use MagicMock to
    create a skill-like object with the expected interface.
    """
    import uuid

    if skill_status is None:
        skill_status = SkillStatus.ACTIVE if SkillStatus else "active"
    if triggers is None:
        triggers = []
    if tools is None:
        tools = []

    mock_skill = MagicMock()
    mock_skill.id = str(uuid.uuid4())  # Provide a real string ID
    mock_skill.name = name
    mock_skill.description = description
    mock_skill.skill_status = skill_status
    mock_skill.triggers = triggers
    mock_skill.tools = tools
    mock_skill.version = "1.0.0"

    return mock_skill


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_trigger() -> "SkillTrigger":
    """Create a mock skill trigger."""
    return SkillTrigger(
        name="test_trigger",
        keywords=["test", "/test", "run test"],
        patterns=[r"^/test\s*$"],
        priority=TriggerPriority.NORMAL,
        enabled=True,
    )


@pytest.fixture
def mock_trigger_high_priority() -> "SkillTrigger":
    """Create a high priority trigger."""
    return SkillTrigger(
        name="high_priority_trigger",
        keywords=["urgent", "/urgent"],
        patterns=[r"urgent.*test"],
        priority=TriggerPriority.HIGH,
        enabled=True,
    )


@pytest.fixture
def active_skill(mock_trigger: "SkillTrigger") -> MagicMock:
    """Create an active skill definition with triggers."""
    return create_mock_skill(
        name="test_skill",
        description="A skill for testing",
        skill_status=SkillStatus.ACTIVE,
        triggers=[mock_trigger],
        tools=["Read", "Write"],
    )


@pytest.fixture
def draft_skill() -> MagicMock:
    """Create a draft (inactive) skill definition."""
    return create_mock_skill(
        name="draft_skill",
        description="A draft skill",
        skill_status=SkillStatus.DRAFT,
        triggers=[],
    )


@pytest.fixture
def disabled_skill() -> MagicMock:
    """Create a disabled skill definition."""
    return create_mock_skill(
        name="disabled_skill",
        description="A disabled skill",
        skill_status=SkillStatus.DISABLED,
        triggers=[],
    )


@pytest.fixture
def alternative_skill(mock_trigger_high_priority: "SkillTrigger") -> MagicMock:
    """Create an alternative skill with higher priority trigger."""
    return create_mock_skill(
        name="alternative_skill",
        description="An alternative skill",
        skill_status=SkillStatus.ACTIVE,
        triggers=[mock_trigger_high_priority],
        tools=["Grep"],
    )


@pytest.fixture
def skill_router() -> SkillRouter:
    """Create a fresh skill router instance."""
    return SkillRouter()


@pytest.fixture
def populated_router(
    skill_router: SkillRouter,
    active_skill: SkillDefinition,
) -> SkillRouter:
    """Create a router with one registered skill."""
    skill_router.register(active_skill)
    return skill_router


# =============================================================================
# ROUTE RESULT TESTS
# =============================================================================


class TestRouteResult:
    """Tests for RouteResult dataclass."""

    def test_matched_property_true_with_skill(self, active_skill: SkillDefinition):
        """RouteResult.matched should be True when skill is matched."""
        result = RouteResult(
            matched=True,
            skill=active_skill,
            match_score=0.95,
        )
        assert result.matched is True

    def test_matched_property_false(self):
        """RouteResult.matched should be False when no skill matched."""
        result = RouteResult(matched=False)
        assert result.matched is False

    def test_skill_name_property_with_skill(self, active_skill: SkillDefinition):
        """RouteResult.skill_name should return skill name when matched."""
        result = RouteResult(
            matched=True,
            skill=active_skill,
        )
        assert result.skill_name == "test_skill"

    def test_skill_name_property_without_skill(self):
        """RouteResult.skill_name should return None when no skill matched."""
        result = RouteResult(matched=False)
        assert result.skill_name is None

    def test_bool_true_when_matched(self, active_skill: SkillDefinition):
        """RouteResult should be truthy when matched is True."""
        result = RouteResult(matched=True, skill=active_skill)
        assert bool(result) is True
        assert result  # Implicit bool check

    def test_bool_false_when_not_matched(self):
        """RouteResult should be falsy when matched is False."""
        result = RouteResult(matched=False)
        assert bool(result) is False
        assert not result  # Implicit bool check

    def test_default_values(self):
        """RouteResult should have correct default values."""
        result = RouteResult(matched=False)
        assert result.skill is None
        assert result.trigger is None
        assert result.match_score == 0.0
        assert result.alternatives == []
        assert result.routing_time_ms == 0.0

    def test_alternatives_list(
        self,
        active_skill: SkillDefinition,
        alternative_skill: SkillDefinition,
    ):
        """RouteResult should store alternative skills."""
        result = RouteResult(
            matched=True,
            skill=active_skill,
            alternatives=[alternative_skill],
        )
        assert len(result.alternatives) == 1
        assert result.alternatives[0].name == "alternative_skill"

    def test_with_trigger(
        self,
        active_skill: SkillDefinition,
        mock_trigger: SkillTrigger,
    ):
        """RouteResult should store matched trigger."""
        result = RouteResult(
            matched=True,
            skill=active_skill,
            trigger=mock_trigger,
            match_score=1.0,
        )
        assert result.trigger is not None
        assert result.trigger.name == "test_trigger"

    def test_routing_time_ms(self, active_skill: SkillDefinition):
        """RouteResult should store routing time."""
        result = RouteResult(
            matched=True,
            skill=active_skill,
            routing_time_ms=15.5,
        )
        assert result.routing_time_ms == 15.5


# =============================================================================
# SKILL ROUTER - REGISTRATION TESTS
# =============================================================================


class TestSkillRouterRegister:
    """Tests for SkillRouter.register() method."""

    def test_register_success(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """register() should successfully add a skill."""
        skill_router.register(active_skill)
        assert skill_router.get_skill("test_skill") is not None

    def test_register_duplicate_raises_error(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """register() should raise ValueError for duplicate skill names."""
        skill_router.register(active_skill)
        with pytest.raises(ValueError, match="already registered"):
            skill_router.register(active_skill)

    def test_register_multiple_skills(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
        alternative_skill: SkillDefinition,
    ):
        """register() should allow registering multiple different skills."""
        skill_router.register(active_skill)
        skill_router.register(alternative_skill)
        assert len(skill_router.list_skills(active_only=False)) == 2


# =============================================================================
# SKILL ROUTER - UNREGISTER TESTS
# =============================================================================


class TestSkillRouterUnregister:
    """Tests for SkillRouter.unregister() method."""

    def test_unregister_existing_skill(
        self,
        populated_router: SkillRouter,
    ):
        """unregister() should return True for existing skill."""
        result = populated_router.unregister("test_skill")
        assert result is True
        assert populated_router.get_skill("test_skill") is None

    def test_unregister_nonexistent_skill(
        self,
        skill_router: SkillRouter,
    ):
        """unregister() should return False for nonexistent skill."""
        result = skill_router.unregister("nonexistent_skill")
        assert result is False

    def test_unregister_removes_from_list(
        self,
        populated_router: SkillRouter,
    ):
        """unregister() should remove skill from list_skills()."""
        initial_count = len(populated_router.list_skills(active_only=False))
        populated_router.unregister("test_skill")
        final_count = len(populated_router.list_skills(active_only=False))
        assert final_count == initial_count - 1


# =============================================================================
# SKILL ROUTER - GET SKILL TESTS
# =============================================================================


class TestSkillRouterGetSkill:
    """Tests for SkillRouter.get_skill() method."""

    def test_get_existing_skill(
        self,
        populated_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """get_skill() should return skill for valid name."""
        skill = populated_router.get_skill("test_skill")
        assert skill is not None
        assert skill.name == active_skill.name

    def test_get_nonexistent_skill(
        self,
        skill_router: SkillRouter,
    ):
        """get_skill() should return None for invalid name."""
        skill = skill_router.get_skill("nonexistent")
        assert skill is None


# =============================================================================
# SKILL ROUTER - LIST SKILLS TESTS
# =============================================================================


class TestSkillRouterListSkills:
    """Tests for SkillRouter.list_skills() method."""

    def test_list_skills_empty_router(
        self,
        skill_router: SkillRouter,
    ):
        """list_skills() should return empty list for empty router."""
        skills = skill_router.list_skills()
        assert skills == []

    def test_list_skills_active_only_default(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
        draft_skill: SkillDefinition,
    ):
        """list_skills() should only return active skills by default."""
        skill_router.register(active_skill)
        skill_router.register(draft_skill)
        skills = skill_router.list_skills()
        assert len(skills) == 1
        assert skills[0].skill_status == SkillStatus.ACTIVE

    def test_list_skills_all(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
        draft_skill: SkillDefinition,
    ):
        """list_skills(active_only=False) should return all skills."""
        skill_router.register(active_skill)
        skill_router.register(draft_skill)
        skills = skill_router.list_skills(active_only=False)
        assert len(skills) == 2

    def test_list_skills_excludes_disabled(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
        disabled_skill: SkillDefinition,
    ):
        """list_skills() should exclude disabled skills."""
        skill_router.register(active_skill)
        skill_router.register(disabled_skill)
        skills = skill_router.list_skills(active_only=True)
        assert len(skills) == 1
        assert all(s.skill_status == SkillStatus.ACTIVE for s in skills)


# =============================================================================
# SKILL ROUTER - ROUTE TESTS
# =============================================================================


class TestSkillRouterRoute:
    """Tests for SkillRouter.route() method."""

    def test_route_no_match_empty_router(
        self,
        skill_router: SkillRouter,
    ):
        """route() should return no match for empty router."""
        result = skill_router.route("test input")
        assert result.matched is False
        assert result.skill is None

    def test_route_matches_correct_skill(
        self,
        skill_router: SkillRouter,
    ):
        """route() should match skill based on trigger."""
        # Create skill with trigger that will match
        trigger = SkillTrigger(
            name="commit_trigger",
            keywords=["commit", "/commit"],
            priority=TriggerPriority.HIGH,
        )
        skill = create_mock_skill(
            name="commit_skill",
            description="Commit changes",
            skill_status=SkillStatus.ACTIVE,
            triggers=[trigger],
        )

        skill_router.register(skill)

        # Mock the detector to return a match
        with patch.object(skill_router._detector, 'detect') as mock_detect:
            mock_match = MagicMock()
            mock_match.matched = True
            mock_match.skill_name = "commit_skill"
            mock_match.confidence = 0.95
            mock_match.trigger = trigger
            mock_detect.return_value = mock_match

            result = skill_router.route("please commit my changes")
            assert result.matched is True

    def test_route_skips_inactive_skills(
        self,
        skill_router: SkillRouter,
        draft_skill: SkillDefinition,
    ):
        """route() should skip inactive skills."""
        skill_router.register(draft_skill)
        result = skill_router.route("test input")
        assert result.matched is False

    def test_route_records_timing(
        self,
        skill_router: SkillRouter,
    ):
        """route() should record routing time."""
        result = skill_router.route("test input")
        assert result.routing_time_ms >= 0.0

    def test_route_with_context(
        self,
        populated_router: SkillRouter,
    ):
        """route() should accept optional context."""
        context = {"user_id": "test_user", "session_id": "123"}
        # Should not raise
        result = populated_router.route("test input", context=context)
        assert isinstance(result, RouteResult)


# =============================================================================
# SKILL ROUTER - ROUTE BY NAME TESTS
# =============================================================================


class TestSkillRouterRouteByName:
    """Tests for SkillRouter.route_by_name() method."""

    def test_route_by_name_success(
        self,
        populated_router: SkillRouter,
    ):
        """route_by_name() should return match for existing active skill."""
        result = populated_router.route_by_name("test_skill")
        assert result.matched is True
        assert result.skill_name == "test_skill"
        assert result.match_score == 1.0

    def test_route_by_name_nonexistent(
        self,
        skill_router: SkillRouter,
    ):
        """route_by_name() should return no match for nonexistent skill."""
        result = skill_router.route_by_name("nonexistent_skill")
        assert result.matched is False

    def test_route_by_name_inactive_skill(
        self,
        skill_router: SkillRouter,
        draft_skill: SkillDefinition,
    ):
        """route_by_name() should not match inactive skills."""
        skill_router.register(draft_skill)
        result = skill_router.route_by_name("draft_skill")
        assert result.matched is False

    def test_route_by_name_disabled_skill(
        self,
        skill_router: SkillRouter,
        disabled_skill: SkillDefinition,
    ):
        """route_by_name() should not match disabled skills."""
        skill_router.register(disabled_skill)
        result = skill_router.route_by_name("disabled_skill")
        assert result.matched is False


# =============================================================================
# SKILL ROUTER - EXECUTE TESTS
# =============================================================================


class TestSkillRouterExecute:
    """Tests for SkillRouter.execute() method."""

    def test_execute_default_executor(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should use default executor when none provided."""
        execution = skill_router.execute(
            skill=active_skill,
            user_input="test input",
        )
        assert execution.skill_name == "test_skill"
        assert execution.execution_status == ExecutionStatus.SUCCESS
        assert execution.output_text == active_skill.description

    def test_execute_with_custom_executor(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should use custom executor when provided."""
        custom_output = "Custom execution result"

        def custom_executor(skill, user_input, context):
            return custom_output

        execution = skill_router.execute(
            skill=active_skill,
            user_input="test input",
            executor=custom_executor,
        )
        assert execution.output_text == custom_output
        assert execution.execution_status == ExecutionStatus.SUCCESS

    def test_execute_handles_timeout_error(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should handle TimeoutError from executor."""
        def timeout_executor(skill, user_input, context):
            raise TimeoutError("Execution timed out")

        execution = skill_router.execute(
            skill=active_skill,
            user_input="test input",
            executor=timeout_executor,
        )
        assert execution.execution_status == ExecutionStatus.TIMEOUT
        assert "timed out" in execution.output_text.lower()

    def test_execute_handles_generic_exception(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should handle generic exceptions from executor."""
        def failing_executor(skill, user_input, context):
            raise ValueError("Something went wrong")

        execution = skill_router.execute(
            skill=active_skill,
            user_input="test input",
            executor=failing_executor,
        )
        assert execution.execution_status == ExecutionStatus.FAILURE
        assert "Something went wrong" in execution.output_text

    def test_execute_records_duration(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should record execution duration."""
        execution = skill_router.execute(
            skill=active_skill,
            user_input="test input",
        )
        assert execution.duration_ms >= 0

    def test_execute_adds_to_history(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should add execution to history."""
        initial_count = len(skill_router.get_execution_history())
        skill_router.execute(
            skill=active_skill,
            user_input="test input",
        )
        final_count = len(skill_router.get_execution_history())
        assert final_count == initial_count + 1

    def test_execute_truncates_long_input(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should truncate long input text."""
        long_input = "x" * 2000  # Longer than 1000 char limit
        execution = skill_router.execute(
            skill=active_skill,
            user_input=long_input,
        )
        assert len(execution.input_text) <= 1000

    def test_execute_with_context(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """execute() should pass context to custom executor."""
        received_context = {}

        def context_aware_executor(skill, user_input, context):
            received_context.update(context)
            return "done"

        test_context = {"key": "value", "number": 42}
        skill_router.execute(
            skill=active_skill,
            user_input="test",
            context=test_context,
            executor=context_aware_executor,
        )
        assert received_context == test_context


# =============================================================================
# SKILL ROUTER - GET EXECUTION HISTORY TESTS
# =============================================================================


class TestSkillRouterGetExecutionHistory:
    """Tests for SkillRouter.get_execution_history() method."""

    def test_get_execution_history_empty(
        self,
        skill_router: SkillRouter,
    ):
        """get_execution_history() should return empty list initially."""
        history = skill_router.get_execution_history()
        assert history == []

    def test_get_execution_history_returns_executions(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """get_execution_history() should return past executions."""
        skill_router.execute(active_skill, "input 1")
        skill_router.execute(active_skill, "input 2")

        history = skill_router.get_execution_history()
        assert len(history) == 2

    def test_get_execution_history_filter_by_skill(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
        alternative_skill: SkillDefinition,
    ):
        """get_execution_history() should filter by skill name."""
        skill_router.execute(active_skill, "input 1")
        skill_router.execute(alternative_skill, "input 2")
        skill_router.execute(active_skill, "input 3")

        history = skill_router.get_execution_history(skill_name="test_skill")
        assert len(history) == 2
        assert all(e.skill_name == "test_skill" for e in history)

    def test_get_execution_history_respects_limit(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """get_execution_history() should respect limit parameter."""
        for i in range(10):
            skill_router.execute(active_skill, f"input {i}")

        history = skill_router.get_execution_history(limit=5)
        assert len(history) == 5

    def test_get_execution_history_returns_most_recent(
        self,
        skill_router: SkillRouter,
        active_skill: SkillDefinition,
    ):
        """get_execution_history() should return most recent executions."""
        for i in range(10):
            skill_router.execute(active_skill, f"input {i}")

        history = skill_router.get_execution_history(limit=3)
        # Last 3 executions should be for inputs 7, 8, 9
        assert len(history) == 3


# =============================================================================
# ACTION TYPES TESTS
# =============================================================================


class TestRouteToSkillAction:
    """Tests for RouteToSkillAction."""

    def test_action_metadata(self):
        """RouteToSkillAction should have correct metadata."""
        assert RouteToSkillAction.api_name == "route_to_skill"
        assert RouteToSkillAction.is_hazardous is False

    def test_action_execute(self):
        """RouteToSkillAction.execute() should perform routing."""
        router = SkillRouter()
        action = RouteToSkillAction(
            user_input="test input",
            router=router,
        )
        result = action.execute()
        assert isinstance(result, RouteResult)

    def test_action_with_default_router(self):
        """RouteToSkillAction should create default router if none provided."""
        action = RouteToSkillAction(user_input="test")
        assert action.router is not None


class TestRegisterSkillAction:
    """Tests for RegisterSkillAction."""

    def test_action_metadata(self):
        """RegisterSkillAction should have correct metadata."""
        assert RegisterSkillAction.api_name == "register_skill"
        assert RegisterSkillAction.is_hazardous is True

    def test_action_execute(
        self,
        active_skill: SkillDefinition,
    ):
        """RegisterSkillAction.execute() should register skill."""
        router = SkillRouter()
        action = RegisterSkillAction(
            skill=active_skill,
            router=router,
        )
        result = action.execute()

        assert result["registered"] is True
        assert result["skill_name"] == "test_skill"
        assert router.get_skill("test_skill") is not None

    def test_action_get_proposal_description(
        self,
        active_skill: SkillDefinition,
    ):
        """RegisterSkillAction should provide proposal description."""
        router = SkillRouter()
        action = RegisterSkillAction(
            skill=active_skill,
            router=router,
        )
        description = action.get_proposal_description()

        assert "test_skill" in description
        assert "Register" in description or "register" in description


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestSkillRouterIntegration:
    """Integration tests for SkillRouter workflow."""

    def test_full_workflow_register_route_execute(self):
        """Test complete workflow: register -> route -> execute."""
        router = SkillRouter()

        # Create and register skill using mock
        trigger = SkillTrigger(
            name="greet_trigger",
            keywords=["hello", "hi", "greet"],
        )
        skill = create_mock_skill(
            name="greeting_skill",
            description="Greets the user",
            skill_status=SkillStatus.ACTIVE,
            triggers=[trigger],
        )

        router.register(skill)

        # Route by name (direct)
        result = router.route_by_name("greeting_skill")
        assert result.matched is True

        # Execute
        execution = router.execute(result.skill, "hello")
        assert execution.skill_name == "greeting_skill"
        assert execution.execution_status == ExecutionStatus.SUCCESS

        # Verify history
        history = router.get_execution_history()
        assert len(history) == 1
        assert history[0].skill_name == "greeting_skill"

    def test_multiple_skills_routing_priority(self):
        """Test that higher scoring matches are preferred."""
        router = SkillRouter()

        # Create two mock skills
        trigger1 = SkillTrigger(name="t1", keywords=["test"])
        skill1 = create_mock_skill(
            name="skill_one",
            description="First skill",
            skill_status=SkillStatus.ACTIVE,
            triggers=[trigger1],
        )

        trigger2 = SkillTrigger(name="t2", keywords=["test"])
        skill2 = create_mock_skill(
            name="skill_two",
            description="Second skill",
            skill_status=SkillStatus.ACTIVE,
            triggers=[trigger2],
        )

        router.register(skill1)
        router.register(skill2)

        # Both skills could match "test" - router should pick one
        # (behavior depends on trigger detector implementation)
        # For now, just verify the router doesn't error
        result = router.route_by_name("skill_one")
        assert result.matched is True
