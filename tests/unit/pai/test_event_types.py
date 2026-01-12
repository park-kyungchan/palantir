"""
Unit tests for PAI Hooks event_types module.

Tests HookEventType enum, its properties, and EventBus mappings.

Reference: lib/oda/pai/hooks/event_types.py
"""

import importlib.util
import sys
from pathlib import Path
import pytest


# Load the module directly without triggering package __init__.py
def _load_event_types_module():
    """Load event_types module directly to avoid package init chain issues."""
    module_path = Path(__file__).resolve().parents[3] / "lib/oda/pai/hooks/event_types.py"
    spec = importlib.util.spec_from_file_location("event_types", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["event_types"] = module
    spec.loader.exec_module(module)
    return module


_event_types = _load_event_types_module()

HookEventType = _event_types.HookEventType
HOOK_TO_EVENT_BUS_MAPPING = _event_types.HOOK_TO_EVENT_BUS_MAPPING
EVENT_BUS_TO_HOOK_MAPPING = _event_types.EVENT_BUS_TO_HOOK_MAPPING
get_hook_event_type = _event_types.get_hook_event_type
get_event_bus_type = _event_types.get_event_bus_type


class TestHookEventTypeEnum:
    """Tests for HookEventType enum values."""

    @pytest.mark.parametrize("event_name,expected_value", [
        ("SESSION_START", "SessionStart"),
        ("SESSION_END", "SessionEnd"),
        ("PRE_TOOL_USE", "PreToolUse"),
        ("POST_TOOL_USE", "PostToolUse"),
        ("STOP", "Stop"),
        ("SUBAGENT_STOP", "SubagentStop"),
        ("USER_PROMPT_SUBMIT", "UserPromptSubmit"),
    ])
    def test_all_event_types_exist(self, event_name: str, expected_value: str):
        """Verify all 7 HookEventType enum values exist with correct string values."""
        event = getattr(HookEventType, event_name)
        assert event.value == expected_value
        assert isinstance(event, HookEventType)

    def test_enum_count(self):
        """Verify exactly 7 event types are defined."""
        assert len(HookEventType) == 7

    def test_enum_is_str_subclass(self):
        """Verify HookEventType inherits from str for JSON serialization."""
        assert issubclass(HookEventType, str)


class TestIsBlockingProperty:
    """Tests for the is_blocking property."""

    @pytest.mark.parametrize("event_name,expected", [
        ("PRE_TOOL_USE", True),
        ("USER_PROMPT_SUBMIT", True),
        ("POST_TOOL_USE", False),
        ("SESSION_START", False),
        ("SESSION_END", False),
        ("STOP", False),
        ("SUBAGENT_STOP", False),
    ])
    def test_is_blocking_returns_correct_value(self, event_name: str, expected: bool):
        """Only PRE_TOOL_USE and USER_PROMPT_SUBMIT should return True for is_blocking."""
        event = getattr(HookEventType, event_name)
        assert event.is_blocking == expected

    def test_blocking_events_count(self):
        """Verify exactly 2 events are blocking."""
        blocking_events = [e for e in HookEventType if e.is_blocking]
        assert len(blocking_events) == 2
        assert set(blocking_events) == {
            HookEventType.PRE_TOOL_USE,
            HookEventType.USER_PROMPT_SUBMIT,
        }


class TestIsLifecycleProperty:
    """Tests for the is_lifecycle property."""

    @pytest.mark.parametrize("event_name,expected", [
        ("SESSION_START", True),
        ("SESSION_END", True),
        ("PRE_TOOL_USE", False),
        ("POST_TOOL_USE", False),
        ("STOP", False),
        ("SUBAGENT_STOP", False),
        ("USER_PROMPT_SUBMIT", False),
    ])
    def test_is_lifecycle_returns_correct_value(self, event_name: str, expected: bool):
        """Only SESSION_START and SESSION_END should return True for is_lifecycle."""
        event = getattr(HookEventType, event_name)
        assert event.is_lifecycle == expected

    def test_lifecycle_events_count(self):
        """Verify exactly 2 events are lifecycle events."""
        lifecycle_events = [e for e in HookEventType if e.is_lifecycle]
        assert len(lifecycle_events) == 2
        assert set(lifecycle_events) == {
            HookEventType.SESSION_START,
            HookEventType.SESSION_END,
        }


class TestIsToolEventProperty:
    """Tests for the is_tool_event property."""

    @pytest.mark.parametrize("event_name,expected", [
        ("PRE_TOOL_USE", True),
        ("POST_TOOL_USE", True),
        ("SESSION_START", False),
        ("SESSION_END", False),
        ("STOP", False),
        ("SUBAGENT_STOP", False),
        ("USER_PROMPT_SUBMIT", False),
    ])
    def test_is_tool_event_returns_correct_value(self, event_name: str, expected: bool):
        """Only PRE_TOOL_USE and POST_TOOL_USE should return True for is_tool_event."""
        event = getattr(HookEventType, event_name)
        assert event.is_tool_event == expected

    def test_tool_events_count(self):
        """Verify exactly 2 events are tool events."""
        tool_events = [e for e in HookEventType if e.is_tool_event]
        assert len(tool_events) == 2
        assert set(tool_events) == {
            HookEventType.PRE_TOOL_USE,
            HookEventType.POST_TOOL_USE,
        }


class TestIsAgentEventProperty:
    """Tests for the is_agent_event property."""

    @pytest.mark.parametrize("event_name,expected", [
        ("STOP", True),
        ("SUBAGENT_STOP", True),
        ("SESSION_START", False),
        ("SESSION_END", False),
        ("PRE_TOOL_USE", False),
        ("POST_TOOL_USE", False),
        ("USER_PROMPT_SUBMIT", False),
    ])
    def test_is_agent_event_returns_correct_value(self, event_name: str, expected: bool):
        """Only STOP and SUBAGENT_STOP should return True for is_agent_event."""
        event = getattr(HookEventType, event_name)
        assert event.is_agent_event == expected

    def test_agent_events_count(self):
        """Verify exactly 2 events are agent events."""
        agent_events = [e for e in HookEventType if e.is_agent_event]
        assert len(agent_events) == 2
        assert set(agent_events) == {
            HookEventType.STOP,
            HookEventType.SUBAGENT_STOP,
        }


class TestToEventBusType:
    """Tests for the to_event_bus_type() method."""

    @pytest.mark.parametrize("event_name,expected_bus_type", [
        ("PRE_TOOL_USE", "Tool.pre_execute"),
        ("POST_TOOL_USE", "Tool.post_execute"),
        ("STOP", "Agent.stopped"),
        ("SUBAGENT_STOP", "Subagent.stopped"),
        ("SESSION_START", "Session.started"),
        ("SESSION_END", "Session.ended"),
        ("USER_PROMPT_SUBMIT", "User.prompt_submitted"),
    ])
    def test_to_event_bus_type_returns_correct_mapping(
        self, event_name: str, expected_bus_type: str
    ):
        """Verify each HookEventType maps to correct EventBus type."""
        event = getattr(HookEventType, event_name)
        assert event.to_event_bus_type() == expected_bus_type

    def test_all_events_have_bus_type(self):
        """Verify all HookEventType values have EventBus mappings."""
        for event in HookEventType:
            bus_type = event.to_event_bus_type()
            assert isinstance(bus_type, str)
            assert len(bus_type) > 0


class TestHookToEventBusMapping:
    """Tests for HOOK_TO_EVENT_BUS_MAPPING constant."""

    def test_mapping_contains_all_events(self):
        """Verify mapping covers all HookEventType values."""
        assert len(HOOK_TO_EVENT_BUS_MAPPING) == len(HookEventType)
        for event in HookEventType:
            assert event in HOOK_TO_EVENT_BUS_MAPPING

    @pytest.mark.parametrize("event_name,expected_bus_type", [
        ("PRE_TOOL_USE", "Tool.pre_execute"),
        ("POST_TOOL_USE", "Tool.post_execute"),
        ("STOP", "Agent.stopped"),
        ("SUBAGENT_STOP", "Subagent.stopped"),
        ("SESSION_START", "Session.started"),
        ("SESSION_END", "Session.ended"),
        ("USER_PROMPT_SUBMIT", "User.prompt_submitted"),
    ])
    def test_mapping_values_are_correct(
        self, event_name: str, expected_bus_type: str
    ):
        """Verify each mapping entry has correct value."""
        hook_event = getattr(HookEventType, event_name)
        assert HOOK_TO_EVENT_BUS_MAPPING[hook_event] == expected_bus_type

    def test_all_bus_types_follow_domain_format(self):
        """Verify EventBus types follow Domain.action format."""
        for bus_type in HOOK_TO_EVENT_BUS_MAPPING.values():
            assert "." in bus_type
            domain, action = bus_type.split(".", 1)
            assert len(domain) > 0
            assert len(action) > 0


class TestEventBusToHookMapping:
    """Tests for EVENT_BUS_TO_HOOK_MAPPING reverse mapping."""

    def test_reverse_mapping_is_correct(self):
        """Verify reverse mapping is inverse of forward mapping."""
        for hook_event, bus_type in HOOK_TO_EVENT_BUS_MAPPING.items():
            assert EVENT_BUS_TO_HOOK_MAPPING[bus_type] == hook_event

    def test_mapping_is_bijective(self):
        """Verify mapping is one-to-one (bijective)."""
        assert len(HOOK_TO_EVENT_BUS_MAPPING) == len(EVENT_BUS_TO_HOOK_MAPPING)


class TestHelperFunctions:
    """Tests for get_hook_event_type and get_event_bus_type functions."""

    @pytest.mark.parametrize("bus_type,expected_event_name", [
        ("Tool.pre_execute", "PRE_TOOL_USE"),
        ("Tool.post_execute", "POST_TOOL_USE"),
        ("Agent.stopped", "STOP"),
        ("Subagent.stopped", "SUBAGENT_STOP"),
        ("Session.started", "SESSION_START"),
        ("Session.ended", "SESSION_END"),
        ("User.prompt_submitted", "USER_PROMPT_SUBMIT"),
    ])
    def test_get_hook_event_type_returns_correct_event(
        self, bus_type: str, expected_event_name: str
    ):
        """Verify get_hook_event_type returns correct HookEventType for EventBus type."""
        expected_hook = getattr(HookEventType, expected_event_name)
        result = get_hook_event_type(bus_type)
        assert result == expected_hook

    def test_get_hook_event_type_returns_none_for_unknown(self):
        """Verify get_hook_event_type returns None for unmapped EventBus types."""
        result = get_hook_event_type("Unknown.event")
        assert result is None

    @pytest.mark.parametrize("event_name,expected_bus_type", [
        ("PRE_TOOL_USE", "Tool.pre_execute"),
        ("POST_TOOL_USE", "Tool.post_execute"),
        ("STOP", "Agent.stopped"),
    ])
    def test_get_event_bus_type_returns_correct_value(
        self, event_name: str, expected_bus_type: str
    ):
        """Verify get_event_bus_type returns correct EventBus type string."""
        hook_event = getattr(HookEventType, event_name)
        result = get_event_bus_type(hook_event)
        assert result == expected_bus_type
