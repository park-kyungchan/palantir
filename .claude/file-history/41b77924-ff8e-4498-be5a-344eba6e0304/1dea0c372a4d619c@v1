"""
PAI Module Test Fixtures

Shared pytest fixtures for PAI unit tests.
"""

from __future__ import annotations

from typing import List
from unittest.mock import MagicMock

import pytest

# Import PAI modules for fixtures
# Note: These imports require Pydantic to be installed
try:
    from lib.oda.pai.algorithm.effort_levels import EffortLevel
    from lib.oda.pai.traits.dimensions import (
        ExpertiseType,
        PersonalityDimension,
        ApproachStyle,
    )
    from lib.oda.pai.hooks.event_types import HookEventType
    PAI_AVAILABLE = True
except ImportError:
    PAI_AVAILABLE = False


# =============================================================================
# SKIP MARKER FOR MISSING DEPENDENCIES
# =============================================================================

requires_pydantic = pytest.mark.skipif(
    not PAI_AVAILABLE,
    reason="PAI modules require Pydantic to be installed"
)


# =============================================================================
# EFFORT LEVEL FIXTURES
# =============================================================================

@pytest.fixture
def trivial_effort() -> "EffortLevel":
    """Trivial effort level."""
    return EffortLevel.TRIVIAL


@pytest.fixture
def standard_effort() -> "EffortLevel":
    """Standard effort level (default)."""
    return EffortLevel.STANDARD


@pytest.fixture
def determined_effort() -> "EffortLevel":
    """Determined effort level (maximum)."""
    return EffortLevel.DETERMINED


@pytest.fixture
def all_effort_levels() -> List["EffortLevel"]:
    """All effort levels in ascending order."""
    return [
        EffortLevel.TRIVIAL,
        EffortLevel.QUICK,
        EffortLevel.STANDARD,
        EffortLevel.THOROUGH,
        EffortLevel.DETERMINED,
    ]


# =============================================================================
# TRAIT FIXTURES
# =============================================================================

@pytest.fixture
def security_expertise() -> "ExpertiseType":
    """Security expertise type."""
    return ExpertiseType.SECURITY


@pytest.fixture
def skeptical_personality() -> "PersonalityDimension":
    """Skeptical personality dimension."""
    return PersonalityDimension.SKEPTICAL


@pytest.fixture
def thorough_approach() -> "ApproachStyle":
    """Thorough approach style."""
    return ApproachStyle.THOROUGH


# =============================================================================
# HOOK FIXTURES
# =============================================================================

@pytest.fixture
def pre_tool_event() -> "HookEventType":
    """PreToolUse event type."""
    return HookEventType.PRE_TOOL_USE


@pytest.fixture
def session_start_event() -> "HookEventType":
    """SessionStart event type."""
    return HookEventType.SESSION_START


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_capability_registry() -> MagicMock:
    """Mock capability registry for algorithm tests."""
    registry = MagicMock()
    registry.get_capabilities.return_value = ["haiku", "sonnet"]
    return registry


@pytest.fixture
def mock_voice_resolver() -> MagicMock:
    """Mock voice resolver for trait tests."""
    resolver = MagicMock()
    resolver.resolve.return_value = "Default"
    return resolver
