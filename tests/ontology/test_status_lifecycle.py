"""
Orion ODA v4.0 - Status Lifecycle Tests
========================================

Comprehensive test suite for the resource lifecycle status system:
- ResourceLifecycleStatus enum
- StatusTransitionValidator
- StatusMixin
- StatusHistoryTracker
- Status Actions

Run with: pytest tests/ontology/test_status_lifecycle.py -v
"""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Import the modules under test
from lib.oda.ontology.types.status_types import (
    ResourceLifecycleStatus,
    StatusCategory,
    VALID_TRANSITIONS,
    get_allowed_transitions,
    is_valid_transition,
)
from lib.oda.ontology.validators.status_validator import (
    StatusTransitionError,
    StatusTransitionValidator,
    TransitionValidationResult,
    validate_transition,
    assert_valid_transition,
)
from lib.oda.ontology.mixins.status_mixin import (
    StatusMixin,
    StatusTransitionContext,
)
from lib.oda.ontology.tracking.status_history import (
    StatusHistoryEntry,
    StatusHistoryTracker,
)
from lib.oda.ontology.actions import ActionContext


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def status_tracker():
    """Create a fresh StatusHistoryTracker for each test."""
    return StatusHistoryTracker()


@pytest.fixture
def status_validator():
    """Create a StatusTransitionValidator instance."""
    return StatusTransitionValidator()


class MockStatusObject(StatusMixin):
    """Mock object for testing StatusMixin."""

    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self._pre_transition_hooks = []
        self._post_transition_hooks = []
        self._status_history_tracker = None
        self.initialize_status()


# =============================================================================
# RESOURCE LIFECYCLE STATUS ENUM TESTS
# =============================================================================


class TestResourceLifecycleStatus:
    """Tests for ResourceLifecycleStatus enum."""

    def test_all_statuses_defined(self):
        """All expected statuses should be defined."""
        expected = [
            "DRAFT", "EXPERIMENTAL", "ALPHA", "BETA",
            "ACTIVE", "STABLE",
            "DEPRECATED", "SUNSET",
            "ARCHIVED", "DELETED"
        ]
        actual = [s.name for s in ResourceLifecycleStatus]
        assert set(expected) == set(actual)

    def test_status_values(self):
        """Status values should be lowercase strings."""
        for status in ResourceLifecycleStatus:
            assert status.value == status.name.lower()

    def test_development_statuses(self):
        """Development statuses should be correct."""
        dev_statuses = ResourceLifecycleStatus.development_statuses()
        assert ResourceLifecycleStatus.DRAFT in dev_statuses
        assert ResourceLifecycleStatus.EXPERIMENTAL in dev_statuses
        assert ResourceLifecycleStatus.ALPHA in dev_statuses
        assert ResourceLifecycleStatus.BETA in dev_statuses
        assert ResourceLifecycleStatus.ACTIVE not in dev_statuses

    def test_production_statuses(self):
        """Production statuses should be correct."""
        prod_statuses = ResourceLifecycleStatus.production_statuses()
        assert ResourceLifecycleStatus.ACTIVE in prod_statuses
        assert ResourceLifecycleStatus.STABLE in prod_statuses
        assert ResourceLifecycleStatus.BETA not in prod_statuses

    def test_deprecation_statuses(self):
        """Deprecation statuses should be correct."""
        dep_statuses = ResourceLifecycleStatus.deprecation_statuses()
        assert ResourceLifecycleStatus.DEPRECATED in dep_statuses
        assert ResourceLifecycleStatus.SUNSET in dep_statuses
        assert ResourceLifecycleStatus.ARCHIVED not in dep_statuses

    def test_end_of_life_statuses(self):
        """End of life statuses should be correct."""
        eol_statuses = ResourceLifecycleStatus.end_of_life_statuses()
        assert ResourceLifecycleStatus.ARCHIVED in eol_statuses
        assert ResourceLifecycleStatus.DELETED in eol_statuses
        assert ResourceLifecycleStatus.SUNSET not in eol_statuses

    def test_is_usable(self):
        """is_usable should return True for appropriate statuses."""
        assert ResourceLifecycleStatus.ACTIVE.is_usable() is True
        assert ResourceLifecycleStatus.STABLE.is_usable() is True
        assert ResourceLifecycleStatus.BETA.is_usable() is True
        assert ResourceLifecycleStatus.DRAFT.is_usable() is False
        assert ResourceLifecycleStatus.DELETED.is_usable() is False

    def test_is_modifiable(self):
        """is_modifiable should return False for terminal states."""
        assert ResourceLifecycleStatus.ACTIVE.is_modifiable() is True
        assert ResourceLifecycleStatus.DRAFT.is_modifiable() is True
        assert ResourceLifecycleStatus.ARCHIVED.is_modifiable() is False
        assert ResourceLifecycleStatus.DELETED.is_modifiable() is False

    def test_is_visible(self):
        """is_visible should return False only for DELETED."""
        assert ResourceLifecycleStatus.ACTIVE.is_visible() is True
        assert ResourceLifecycleStatus.ARCHIVED.is_visible() is True
        assert ResourceLifecycleStatus.DELETED.is_visible() is False

    def test_get_stage(self):
        """get_stage should return correct stage names."""
        assert ResourceLifecycleStatus.DRAFT.get_stage() == "development"
        assert ResourceLifecycleStatus.ACTIVE.get_stage() == "production"
        assert ResourceLifecycleStatus.DEPRECATED.get_stage() == "deprecation"
        assert ResourceLifecycleStatus.ARCHIVED.get_stage() == "end_of_life"


# =============================================================================
# VALID TRANSITIONS TESTS
# =============================================================================


class TestValidTransitions:
    """Tests for transition rules."""

    def test_draft_transitions(self):
        """DRAFT can transition to EXPERIMENTAL, ACTIVE, or DELETED."""
        allowed = get_allowed_transitions(ResourceLifecycleStatus.DRAFT)
        assert ResourceLifecycleStatus.EXPERIMENTAL in allowed
        assert ResourceLifecycleStatus.ACTIVE in allowed
        assert ResourceLifecycleStatus.DELETED in allowed
        assert ResourceLifecycleStatus.STABLE not in allowed

    def test_experimental_transitions(self):
        """EXPERIMENTAL can transition to ALPHA or DEPRECATED."""
        allowed = get_allowed_transitions(ResourceLifecycleStatus.EXPERIMENTAL)
        assert ResourceLifecycleStatus.ALPHA in allowed
        assert ResourceLifecycleStatus.DEPRECATED in allowed
        assert ResourceLifecycleStatus.BETA not in allowed

    def test_standard_progression(self):
        """Standard progression path should work."""
        # DRAFT -> EXPERIMENTAL -> ALPHA -> BETA -> ACTIVE -> STABLE
        assert is_valid_transition(ResourceLifecycleStatus.DRAFT, ResourceLifecycleStatus.EXPERIMENTAL)
        assert is_valid_transition(ResourceLifecycleStatus.EXPERIMENTAL, ResourceLifecycleStatus.ALPHA)
        assert is_valid_transition(ResourceLifecycleStatus.ALPHA, ResourceLifecycleStatus.BETA)
        assert is_valid_transition(ResourceLifecycleStatus.BETA, ResourceLifecycleStatus.ACTIVE)
        assert is_valid_transition(ResourceLifecycleStatus.ACTIVE, ResourceLifecycleStatus.STABLE)

    def test_deprecation_path(self):
        """Deprecation path should work."""
        assert is_valid_transition(ResourceLifecycleStatus.STABLE, ResourceLifecycleStatus.DEPRECATED)
        assert is_valid_transition(ResourceLifecycleStatus.DEPRECATED, ResourceLifecycleStatus.SUNSET)
        assert is_valid_transition(ResourceLifecycleStatus.SUNSET, ResourceLifecycleStatus.ARCHIVED)
        assert is_valid_transition(ResourceLifecycleStatus.ARCHIVED, ResourceLifecycleStatus.DELETED)

    def test_deleted_is_terminal(self):
        """DELETED should be a terminal state with no transitions."""
        allowed = get_allowed_transitions(ResourceLifecycleStatus.DELETED)
        assert len(allowed) == 0

    def test_invalid_backward_transitions(self):
        """Backward transitions should not be allowed."""
        assert not is_valid_transition(ResourceLifecycleStatus.ACTIVE, ResourceLifecycleStatus.BETA)
        assert not is_valid_transition(ResourceLifecycleStatus.STABLE, ResourceLifecycleStatus.ACTIVE)
        assert not is_valid_transition(ResourceLifecycleStatus.DELETED, ResourceLifecycleStatus.ARCHIVED)


# =============================================================================
# STATUS TRANSITION VALIDATOR TESTS
# =============================================================================


class TestStatusTransitionValidator:
    """Tests for StatusTransitionValidator."""

    def test_valid_transition(self, status_validator):
        """Valid transition should pass validation."""
        result = status_validator.validate_transition(
            ResourceLifecycleStatus.DRAFT,
            ResourceLifecycleStatus.EXPERIMENTAL,
            raise_on_invalid=False,
        )
        assert result.is_valid is True
        assert result.error_message is None

    def test_invalid_transition_result(self, status_validator):
        """Invalid transition should return error result."""
        result = status_validator.validate_transition(
            ResourceLifecycleStatus.DELETED,
            ResourceLifecycleStatus.ACTIVE,
            raise_on_invalid=False,
        )
        assert result.is_valid is False
        assert result.error_message is not None
        assert "Cannot transition" in result.error_message

    def test_invalid_transition_raises(self, status_validator):
        """Invalid transition should raise when configured."""
        with pytest.raises(StatusTransitionError) as exc_info:
            status_validator.validate_transition(
                ResourceLifecycleStatus.DELETED,
                ResourceLifecycleStatus.ACTIVE,
                raise_on_invalid=True,
            )
        assert "Cannot transition" in str(exc_info.value)

    def test_risky_transition_warning(self, status_validator):
        """Risky transitions should generate warnings."""
        result = status_validator.validate_transition(
            ResourceLifecycleStatus.ACTIVE,
            ResourceLifecycleStatus.DEPRECATED,
            raise_on_invalid=False,
        )
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "significant lifecycle change" in result.warnings[0].lower()

    def test_skip_transition_warning(self, status_validator):
        """Skip transitions should generate warnings."""
        result = status_validator.validate_transition(
            ResourceLifecycleStatus.DRAFT,
            ResourceLifecycleStatus.ACTIVE,
            raise_on_invalid=False,
        )
        assert result.is_valid is True
        assert any("skip" in w.lower() for w in result.warnings)

    def test_terminal_state_warning(self, status_validator):
        """Transition to DELETED should warn about terminal state."""
        result = status_validator.validate_transition(
            ResourceLifecycleStatus.ARCHIVED,
            ResourceLifecycleStatus.DELETED,
            raise_on_invalid=False,
        )
        assert result.is_valid is True
        assert any("terminal" in w.lower() for w in result.warnings)

    def test_get_allowed_transitions(self, status_validator):
        """get_allowed_transitions should return correct list."""
        allowed = status_validator.get_allowed_transitions(ResourceLifecycleStatus.DRAFT)
        assert len(allowed) > 0
        assert ResourceLifecycleStatus.EXPERIMENTAL in allowed

    def test_can_transition_to(self, status_validator):
        """can_transition_to should return boolean."""
        assert status_validator.can_transition_to(
            ResourceLifecycleStatus.DRAFT,
            ResourceLifecycleStatus.EXPERIMENTAL
        ) is True
        assert status_validator.can_transition_to(
            ResourceLifecycleStatus.DELETED,
            ResourceLifecycleStatus.ACTIVE
        ) is False

    def test_get_transition_path(self, status_validator):
        """get_transition_path should find valid paths."""
        path = status_validator.get_transition_path(
            ResourceLifecycleStatus.DRAFT,
            ResourceLifecycleStatus.STABLE
        )
        assert path is not None
        assert path[0] == ResourceLifecycleStatus.DRAFT
        assert path[-1] == ResourceLifecycleStatus.STABLE

    def test_get_transition_path_no_path(self, status_validator):
        """get_transition_path should return None for impossible paths."""
        path = status_validator.get_transition_path(
            ResourceLifecycleStatus.DELETED,
            ResourceLifecycleStatus.ACTIVE
        )
        assert path is None


# =============================================================================
# STATUS MIXIN TESTS
# =============================================================================


class TestStatusMixin:
    """Tests for StatusMixin."""

    def test_initialize_status_default(self):
        """initialize_status should set DRAFT by default."""
        obj = MockStatusObject(id="test-1", name="Test")
        assert obj.get_status() == ResourceLifecycleStatus.DRAFT

    def test_initialize_status_custom(self):
        """initialize_status should allow custom initial status."""
        obj = MockStatusObject(id="test-1", name="Test")
        obj.initialize_status(
            status=ResourceLifecycleStatus.ACTIVE,
            actor_id="admin"
        )
        assert obj.get_status() == ResourceLifecycleStatus.ACTIVE
        assert obj._status_changed_by == "admin"

    def test_get_status_info(self):
        """get_status_info should return complete info."""
        obj = MockStatusObject(id="test-1", name="Test")
        info = obj.get_status_info()
        assert info["status"] == "draft"
        assert "changed_at" in info
        assert "changed_by" in info
        assert info["is_usable"] is False  # DRAFT is not usable
        assert info["stage"] == "development"

    def test_can_transition_to(self):
        """can_transition_to should check validity."""
        obj = MockStatusObject(id="test-1", name="Test")
        assert obj.can_transition_to(ResourceLifecycleStatus.EXPERIMENTAL) is True
        assert obj.can_transition_to(ResourceLifecycleStatus.STABLE) is False

    def test_get_allowed_transitions(self):
        """get_allowed_transitions should list valid targets."""
        obj = MockStatusObject(id="test-1", name="Test")
        allowed = obj.get_allowed_transitions()
        assert ResourceLifecycleStatus.EXPERIMENTAL in allowed
        assert ResourceLifecycleStatus.ACTIVE in allowed
        assert ResourceLifecycleStatus.DELETED in allowed

    def test_transition_to_valid(self):
        """transition_to should succeed for valid transitions."""
        obj = MockStatusObject(id="test-1", name="Test")
        result = obj.transition_to(
            ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
            reason="Testing"
        )
        assert result.is_valid is True
        assert obj.get_status() == ResourceLifecycleStatus.EXPERIMENTAL
        assert obj._status_changed_by == "user-1"

    def test_transition_to_invalid_raises(self):
        """transition_to should raise for invalid transitions."""
        obj = MockStatusObject(id="test-1", name="Test")
        with pytest.raises(StatusTransitionError):
            obj.transition_to(
                ResourceLifecycleStatus.STABLE,
                actor_id="user-1"
            )

    def test_transition_to_with_history_tracker(self, status_tracker):
        """transition_to should record in history when tracker set."""
        obj = MockStatusObject(id="test-1", name="Test")
        obj.set_history_tracker(status_tracker)

        obj.transition_to(
            ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
            reason="Testing"
        )

        history = status_tracker.get_history("test-1")
        assert len(history) == 1
        assert history[0].from_status == ResourceLifecycleStatus.DRAFT
        assert history[0].to_status == ResourceLifecycleStatus.EXPERIMENTAL

    def test_is_usable_delegation(self):
        """is_usable should delegate to status."""
        obj = MockStatusObject(id="test-1", name="Test")
        assert obj.is_usable() is False  # DRAFT
        obj.transition_to(ResourceLifecycleStatus.ACTIVE, actor_id="admin")
        assert obj.is_usable() is True

    def test_is_modifiable_delegation(self):
        """is_modifiable should delegate to status."""
        obj = MockStatusObject(id="test-1", name="Test")
        assert obj.is_modifiable() is True
        obj.initialize_status(ResourceLifecycleStatus.ARCHIVED, "admin")
        assert obj.is_modifiable() is False


# =============================================================================
# STATUS HISTORY TRACKER TESTS
# =============================================================================


class TestStatusHistoryTracker:
    """Tests for StatusHistoryTracker."""

    def test_record_transition(self, status_tracker):
        """record_transition should create entry."""
        entry = status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
            reason="Testing"
        )
        assert entry is not None
        assert entry.object_id == "obj-1"
        assert entry.from_status == ResourceLifecycleStatus.DRAFT
        assert entry.to_status == ResourceLifecycleStatus.EXPERIMENTAL

    def test_get_history(self, status_tracker):
        """get_history should return entries in order."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.EXPERIMENTAL,
            to_status=ResourceLifecycleStatus.ALPHA,
            actor_id="user-1",
        )

        history = status_tracker.get_history("obj-1")
        assert len(history) == 2
        # Default is descending (newest first)
        assert history[0].to_status == ResourceLifecycleStatus.ALPHA

    def test_get_history_ascending(self, status_tracker):
        """get_history with ascending should return oldest first."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.EXPERIMENTAL,
            to_status=ResourceLifecycleStatus.ALPHA,
            actor_id="user-1",
        )

        history = status_tracker.get_history("obj-1", ascending=True)
        assert history[0].to_status == ResourceLifecycleStatus.EXPERIMENTAL

    def test_get_history_limit(self, status_tracker):
        """get_history should respect limit."""
        for i in range(5):
            status_tracker.record_transition(
                object_id="obj-1",
                object_type="Project",
                from_status=ResourceLifecycleStatus.DRAFT,
                to_status=ResourceLifecycleStatus.EXPERIMENTAL,
                actor_id="user-1",
            )

        history = status_tracker.get_history("obj-1", limit=2)
        assert len(history) == 2

    def test_get_latest_status(self, status_tracker):
        """get_latest_status should return most recent status."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.EXPERIMENTAL,
            to_status=ResourceLifecycleStatus.ALPHA,
            actor_id="user-1",
        )

        latest = status_tracker.get_latest_status("obj-1")
        assert latest == ResourceLifecycleStatus.ALPHA

    def test_get_latest_status_no_history(self, status_tracker):
        """get_latest_status should return None for no history."""
        latest = status_tracker.get_latest_status("nonexistent")
        assert latest is None

    def test_get_transitions_by_actor(self, status_tracker):
        """get_transitions_by_actor should filter correctly."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )
        status_tracker.record_transition(
            object_id="obj-2",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-2",
        )
        status_tracker.record_transition(
            object_id="obj-3",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )

        user1_transitions = status_tracker.get_transitions_by_actor("user-1")
        assert len(user1_transitions) == 2
        assert all(t.actor_id == "user-1" for t in user1_transitions)

    def test_get_transitions_by_status(self, status_tracker):
        """get_transitions_by_status should filter correctly."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.DEPRECATED,
            actor_id="user-1",
        )
        status_tracker.record_transition(
            object_id="obj-2",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )

        deprecated = status_tracker.get_transitions_by_status(
            ResourceLifecycleStatus.DEPRECATED
        )
        assert len(deprecated) == 1
        assert deprecated[0].object_id == "obj-1"

    def test_get_transition_count(self, status_tracker):
        """get_transition_count should return correct count."""
        for i in range(3):
            status_tracker.record_transition(
                object_id="obj-1",
                object_type="Project",
                from_status=ResourceLifecycleStatus.DRAFT,
                to_status=ResourceLifecycleStatus.EXPERIMENTAL,
                actor_id="user-1",
            )

        count = status_tracker.get_transition_count("obj-1")
        assert count == 3

    def test_clear_history_specific(self, status_tracker):
        """clear_history should clear specific object history."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )
        status_tracker.record_transition(
            object_id="obj-2",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )

        cleared = status_tracker.clear_history("obj-1")
        assert cleared == 1
        assert status_tracker.get_transition_count("obj-1") == 0
        assert status_tracker.get_transition_count("obj-2") == 1

    def test_clear_history_all(self, status_tracker):
        """clear_history without object_id should clear all."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )
        status_tracker.record_transition(
            object_id="obj-2",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )

        cleared = status_tracker.clear_history()
        assert cleared == 2

    def test_export_history(self, status_tracker):
        """export_history should return serializable data."""
        status_tracker.record_transition(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
            reason="Test export",
        )

        exported = status_tracker.export_history("obj-1")
        assert len(exported) == 1
        assert exported[0]["from_status"] == "draft"
        assert exported[0]["to_status"] == "experimental"
        assert exported[0]["reason"] == "Test export"


# =============================================================================
# STATUS HISTORY ENTRY TESTS
# =============================================================================


class TestStatusHistoryEntry:
    """Tests for StatusHistoryEntry model."""

    def test_create_entry(self):
        """Should create entry with all fields."""
        entry = StatusHistoryEntry(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
            reason="Testing"
        )
        assert entry.entry_id is not None
        assert entry.timestamp is not None

    def test_to_dict(self):
        """to_dict should serialize correctly."""
        entry = StatusHistoryEntry(
            object_id="obj-1",
            object_type="Project",
            from_status=ResourceLifecycleStatus.DRAFT,
            to_status=ResourceLifecycleStatus.EXPERIMENTAL,
            actor_id="user-1",
        )
        data = entry.to_dict()
        assert data["from_status"] == "draft"
        assert data["to_status"] == "experimental"
        assert "timestamp" in data

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "entry_id": "entry-1",
            "object_id": "obj-1",
            "object_type": "Project",
            "from_status": "draft",
            "to_status": "experimental",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": "user-1",
            "reason": "Test",
        }
        entry = StatusHistoryEntry.from_dict(data)
        assert entry.from_status == ResourceLifecycleStatus.DRAFT
        assert entry.to_status == ResourceLifecycleStatus.EXPERIMENTAL


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_validate_transition_valid(self):
        """validate_transition should return result for valid transition."""
        result = validate_transition(
            ResourceLifecycleStatus.DRAFT,
            ResourceLifecycleStatus.EXPERIMENTAL
        )
        assert result.is_valid is True

    def test_validate_transition_invalid(self):
        """validate_transition should return result for invalid transition."""
        result = validate_transition(
            ResourceLifecycleStatus.DELETED,
            ResourceLifecycleStatus.ACTIVE
        )
        assert result.is_valid is False

    def test_assert_valid_transition_valid(self):
        """assert_valid_transition should not raise for valid transition."""
        assert_valid_transition(
            ResourceLifecycleStatus.DRAFT,
            ResourceLifecycleStatus.EXPERIMENTAL
        )  # Should not raise

    def test_assert_valid_transition_invalid(self):
        """assert_valid_transition should raise for invalid transition."""
        with pytest.raises(StatusTransitionError):
            assert_valid_transition(
                ResourceLifecycleStatus.DELETED,
                ResourceLifecycleStatus.ACTIVE
            )
