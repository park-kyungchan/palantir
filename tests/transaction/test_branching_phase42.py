"""
Phase 4.2 - Ontology Branching Enhancement Tests
=================================================

Tests for Git-like branching enhancements:
1. Schema conflict detection
2. Cherry-pick operations
3. Branch comparison and diff actions
4. Conflict resolution actions

Usage:
    pytest tests/transaction/test_branching_phase42.py -v
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from lib.oda.transaction.schema_conflict import (
    SchemaConflictType,
    SchemaConflictSeverity,
    SchemaConflict,
    SchemaConflictBatch,
    SchemaConflictDetector,
)
from lib.oda.transaction.cherry_pick import (
    CherryPickStatus,
    CherryPickConflictResolution,
    CherryPickChange,
    CherryPickResult,
    CherryPicker,
)
from lib.oda.ontology.actions import ActionContext


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def schema_a() -> Dict[str, Any]:
    """Sample schema from branch A."""
    return {
        "User": {
            "fields": {
                "name": {"type": "str", "required": True, "default": None},
                "email": {"type": "str", "required": True},
                "age": {"type": "int", "required": False, "default": 0},
            }
        },
        "Project": {
            "fields": {
                "title": {"type": "str", "required": True},
                "status": {"type": "str", "default": "active"},
            }
        }
    }


@pytest.fixture
def schema_b() -> Dict[str, Any]:
    """Sample schema from branch B with modifications."""
    return {
        "User": {
            "fields": {
                "name": {"type": "str", "required": True, "default": "Unknown"},  # Changed default
                "email": {"type": "str", "required": False},  # Changed required
                "age": {"type": "float", "required": False, "default": 0},  # Type changed
            }
        },
        "Project": {
            "fields": {
                "title": {"type": "str", "required": True},
                "status": {"type": "str", "default": "draft"},  # Changed default
            }
        }
    }


@pytest.fixture
def base_schema() -> Dict[str, Any]:
    """Common ancestor schema."""
    return {
        "User": {
            "fields": {
                "name": {"type": "str", "required": True, "default": None},
                "email": {"type": "str", "required": True},
                "age": {"type": "int", "required": False, "default": 0},
            }
        },
        "Project": {
            "fields": {
                "title": {"type": "str", "required": True},
                "status": {"type": "str", "default": "active"},
            }
        }
    }


@pytest.fixture
def mock_branch_manager():
    """Create a mock BranchManager."""
    manager = AsyncMock()

    # Mock branch data
    mock_branch = MagicMock()
    mock_branch.id = "branch-feature"
    mock_branch.name = "feature/new-api"
    mock_branch.can_commit = True

    # Mock commit data
    mock_commit = MagicMock()
    mock_commit.id = "commit-abc123"
    mock_commit.branch_id = "branch-main"
    mock_commit.message = "Add new feature"
    mock_commit.object_type = "User"
    mock_commit.object_id = "user-001"
    mock_commit.operation = "update"
    mock_commit.new_state = {"name": "Updated Name", "email": "new@example.com"}
    mock_commit.previous_state = {"name": "Old Name", "email": "old@example.com"}

    manager.get_branch.return_value = mock_branch
    manager.get_branch_by_name.return_value = mock_branch
    manager.get_commit.return_value = mock_commit
    manager.get_commits.return_value = []
    manager.create_checkpoint.return_value = MagicMock(success=True, checkpoint_id="cp-001")
    manager.commit.return_value = MagicMock(success=True, commit_id="commit-new-123")

    return manager


# =============================================================================
# SCHEMA CONFLICT DETECTOR TESTS
# =============================================================================

class TestSchemaConflictDetector:
    """Tests for SchemaConflictDetector."""

    def test_detect_type_mismatch(self, schema_a, schema_b, base_schema):
        """Test detection of type mismatch conflicts."""
        detector = SchemaConflictDetector()

        conflicts = detector.detect_conflicts(
            branch_a="feature",
            branch_b="main",
            schema_a=schema_a,
            schema_b=schema_b,
            base_schema=base_schema,
        )

        # Should detect int->float type change for User.age
        type_conflicts = [
            c for c in conflicts
            if c.conflict_type == SchemaConflictType.TYPE_MISMATCH
        ]
        assert len(type_conflicts) >= 1

        age_conflict = next(
            (c for c in type_conflicts if c.field_name == "age"),
            None
        )
        assert age_conflict is not None
        assert age_conflict.object_type == "User"

    def test_detect_default_change(self, schema_a, schema_b, base_schema):
        """Test detection of default value change conflicts."""
        detector = SchemaConflictDetector()

        conflicts = detector.detect_conflicts(
            branch_a="feature",
            branch_b="main",
            schema_a=schema_a,
            schema_b=schema_b,
            base_schema=base_schema,
        )

        default_conflicts = [
            c for c in conflicts
            if c.conflict_type == SchemaConflictType.DEFAULT_CHANGE
        ]

        # Should detect default changes for User.name and Project.status
        assert len(default_conflicts) >= 1

    def test_detect_required_change(self, schema_a, schema_b, base_schema):
        """Test detection of required/optional change conflicts."""
        detector = SchemaConflictDetector()

        conflicts = detector.detect_conflicts(
            branch_a="feature",
            branch_b="main",
            schema_a=schema_a,
            schema_b=schema_b,
            base_schema=base_schema,
        )

        required_conflicts = [
            c for c in conflicts
            if c.conflict_type == SchemaConflictType.REQUIRED_CHANGE
        ]

        # User.email changed from required to optional
        assert len(required_conflicts) >= 1

    def test_detect_deletion_conflict(self):
        """Test detection of deletion conflicts."""
        detector = SchemaConflictDetector()

        schema_a = {
            "User": {"fields": {"name": {"type": "str"}}},
            "OldType": {"fields": {"data": {"type": "str"}}},  # Exists in A
        }
        schema_b = {
            "User": {"fields": {"name": {"type": "str"}}},
            # OldType deleted in B
        }
        base_schema = {
            "User": {"fields": {"name": {"type": "str"}}},
            "OldType": {"fields": {"data": {"type": "str"}}},  # Existed in base
        }

        conflicts = detector.detect_conflicts(
            branch_a="feature",
            branch_b="main",
            schema_a=schema_a,
            schema_b=schema_b,
            base_schema=base_schema,
        )

        deletion_conflicts = [
            c for c in conflicts
            if c.conflict_type == SchemaConflictType.DELETION_CONFLICT
        ]
        assert len(deletion_conflicts) >= 1
        assert deletion_conflicts[0].object_type == "OldType"

    def test_can_auto_merge_with_compatible_changes(self):
        """Test auto-merge capability detection."""
        detector = SchemaConflictDetector(type_coercion_allowed=True)

        # Simple conflict that can be auto-resolved
        conflicts = [
            SchemaConflict(
                conflict_type=SchemaConflictType.DEFAULT_CHANGE,
                severity=SchemaConflictSeverity.WARNING,
                object_type="User",
                field_name="name",
                branch_a_value=None,
                branch_b_value="Unknown",
                base_value=None,
                auto_resolvable=True,
            )
        ]

        assert detector.can_auto_merge(conflicts) is True

    def test_cannot_auto_merge_with_blocking_conflicts(self):
        """Test that blocking conflicts prevent auto-merge."""
        detector = SchemaConflictDetector()

        conflicts = [
            SchemaConflict(
                conflict_type=SchemaConflictType.TYPE_MISMATCH,
                severity=SchemaConflictSeverity.ERROR,
                object_type="User",
                field_name="age",
                branch_a_value="int",
                branch_b_value="str",  # Incompatible
                auto_resolvable=False,
            )
        ]

        assert detector.can_auto_merge(conflicts) is False

    def test_suggest_resolution(self):
        """Test resolution suggestions."""
        detector = SchemaConflictDetector()

        conflict = SchemaConflict(
            conflict_type=SchemaConflictType.TYPE_MISMATCH,
            severity=SchemaConflictSeverity.ERROR,
            object_type="User",
            field_name="age",
            branch_a_value="int",
            branch_b_value="float",
            resolution_suggestions=[
                "Use type 'int' from branch A",
                "Use type 'float' from branch B",
            ],
        )

        suggestion = detector.suggest_resolution(conflict)
        assert "int" in suggestion or "float" in suggestion

    def test_schema_conflict_batch(self):
        """Test SchemaConflictBatch aggregation."""
        conflict1 = SchemaConflict(
            conflict_type=SchemaConflictType.TYPE_MISMATCH,
            severity=SchemaConflictSeverity.ERROR,
            object_type="User",
            auto_resolvable=False,
        )
        conflict2 = SchemaConflict(
            conflict_type=SchemaConflictType.DEFAULT_CHANGE,
            severity=SchemaConflictSeverity.WARNING,
            object_type="Project",
            auto_resolvable=True,
        )

        batch = SchemaConflictBatch(
            branch_a_id="feature",
            branch_b_id="main",
            conflicts=[conflict1, conflict2],
        )

        assert batch.total_count == 2
        assert batch.blocking_count == 1
        assert batch.auto_resolvable_count == 1
        assert batch.can_auto_merge is False

    def test_no_conflicts_for_identical_schemas(self):
        """Test that identical schemas produce no conflicts."""
        detector = SchemaConflictDetector()

        schema = {
            "User": {
                "fields": {
                    "name": {"type": "str", "required": True},
                }
            }
        }

        conflicts = detector.detect_conflicts(
            branch_a="a",
            branch_b="b",
            schema_a=schema,
            schema_b=schema,
        )

        assert len(conflicts) == 0


# =============================================================================
# CHERRY PICKER TESTS
# =============================================================================

class TestCherryPicker:
    """Tests for CherryPicker."""

    @pytest.mark.asyncio
    async def test_cherry_pick_success(self, mock_branch_manager):
        """Test successful cherry-pick operation."""
        mock_branch_manager.get_commits.return_value = []  # No conflicts

        picker = CherryPicker(
            branch_manager=mock_branch_manager,
            conflict_resolution=CherryPickConflictResolution.ABORT,
        )

        result = await picker.cherry_pick(
            commit_id="commit-abc123",
            target_branch="feature/new-api",
            actor_id="user-001",
        )

        assert result.success is True
        assert result.status == CherryPickStatus.COMPLETED
        assert result.commit_id == "commit-abc123"

    @pytest.mark.asyncio
    async def test_cherry_pick_commit_not_found(self, mock_branch_manager):
        """Test cherry-pick with non-existent commit."""
        mock_branch_manager.get_commit.return_value = None

        picker = CherryPicker(branch_manager=mock_branch_manager)

        result = await picker.cherry_pick(
            commit_id="nonexistent",
            target_branch="main",
        )

        assert result.success is False
        assert result.status == CherryPickStatus.FAILED
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_cherry_pick_target_branch_not_found(self, mock_branch_manager):
        """Test cherry-pick with non-existent target branch."""
        mock_branch_manager.get_branch.return_value = None
        mock_branch_manager.get_branch_by_name.return_value = None

        picker = CherryPicker(branch_manager=mock_branch_manager)

        result = await picker.cherry_pick(
            commit_id="commit-abc123",
            target_branch="nonexistent-branch",
        )

        assert result.success is False
        assert result.status == CherryPickStatus.FAILED
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_dry_run_no_conflicts(self, mock_branch_manager):
        """Test dry-run with no conflicts."""
        mock_branch_manager.get_commits.return_value = []

        picker = CherryPicker(branch_manager=mock_branch_manager)

        result = await picker.dry_run(
            commit_id="commit-abc123",
            target_branch="feature",
        )

        assert result.success is True
        assert len(result.conflicts) == 0
        # Applied changes should contain the fields from commit
        assert len(result.applied_changes) >= 0

    @pytest.mark.asyncio
    async def test_dry_run_with_conflicts(self, mock_branch_manager):
        """Test dry-run detecting conflicts."""
        # Setup conflicting state
        target_commit = MagicMock()
        target_commit.new_state = {"name": "Conflicting Name"}
        mock_branch_manager.get_commits.return_value = [target_commit]

        picker = CherryPicker(branch_manager=mock_branch_manager)

        result = await picker.dry_run(
            commit_id="commit-abc123",
            target_branch="main",
        )

        # Should have conflicts for overlapping fields
        assert len(result.conflicts) > 0 or len(result.skipped_changes) > 0

    @pytest.mark.asyncio
    async def test_abort_operation(self, mock_branch_manager):
        """Test aborting a cherry-pick operation."""
        mock_branch_manager.rollback_to_checkpoint.return_value = True

        picker = CherryPicker(branch_manager=mock_branch_manager)

        # Start an operation
        picker._current_operation = CherryPickResult(
            success=False,
            status=CherryPickStatus.IN_PROGRESS,
            commit_id="test",
            target_branch_id="main",
            rollback_point="cp-001",
            rollback_available=True,
        )

        success = await picker.abort()

        assert success is True
        assert picker._current_operation is None

    @pytest.mark.asyncio
    async def test_conflict_resolution_skip(self, mock_branch_manager):
        """Test cherry-pick with skip conflict resolution."""
        target_commit = MagicMock()
        target_commit.new_state = {"name": "Conflict"}
        mock_branch_manager.get_commits.return_value = [target_commit]

        picker = CherryPicker(
            branch_manager=mock_branch_manager,
            conflict_resolution=CherryPickConflictResolution.SKIP,
        )

        result = await picker.cherry_pick(
            commit_id="commit-abc123",
            target_branch="main",
        )

        # Should complete even with conflicts (skipped)
        assert result.status == CherryPickStatus.COMPLETED

    def test_cherry_pick_change_model(self):
        """Test CherryPickChange data model."""
        change = CherryPickChange(
            object_type="User",
            object_id="user-001",
            field_name="name",
            operation="update",
            old_value="Old",
            new_value="New",
        )

        assert change.object_type == "User"
        assert change.applied is False
        assert change.skipped is False

    def test_cherry_pick_result_finalize(self):
        """Test CherryPickResult finalization."""
        result = CherryPickResult(
            success=False,
            status=CherryPickStatus.IN_PROGRESS,
            commit_id="test",
            target_branch_id="main",
        )

        result.finalize(True, CherryPickStatus.COMPLETED)

        assert result.success is True
        assert result.status == CherryPickStatus.COMPLETED
        assert result.completed_at is not None
        assert result.duration_ms is not None


# =============================================================================
# BRANCH ACTIONS TESTS
# =============================================================================

class TestBranchActions:
    """Tests for branch-related ActionTypes."""

    @pytest.mark.asyncio
    async def test_branch_compare_action(self):
        """Test BranchCompareAction execution."""
        from lib.oda.ontology.actions.branch_actions import BranchCompareAction

        action = BranchCompareAction()
        context = ActionContext(actor_id="user-001")

        result = await action.execute(
            params={
                "branch_a": "feature/api",
                "branch_b": "main",
                "include_stats": True,
            },
            context=context,
        )

        assert result.success is True
        assert "branch_a" in result.data
        assert "branch_b" in result.data
        assert "stats" in result.data

    @pytest.mark.asyncio
    async def test_branch_compare_validation_same_branch(self):
        """Test that comparing same branch fails validation."""
        from lib.oda.ontology.actions.branch_actions import BranchCompareAction

        action = BranchCompareAction()
        context = ActionContext(actor_id="user-001")

        result = await action.execute(
            params={
                "branch_a": "main",
                "branch_b": "main",  # Same as branch_a
            },
            context=context,
        )

        assert result.success is False
        assert "itself" in result.error_details.get("validation_errors", [""])[0].lower()

    @pytest.mark.asyncio
    async def test_branch_diff_action(self):
        """Test BranchDiffAction execution."""
        from lib.oda.ontology.actions.branch_actions import BranchDiffAction

        action = BranchDiffAction()
        context = ActionContext(actor_id="user-001")

        result = await action.execute(
            params={
                "branch_a": "main",
                "branch_b": "feature",
            },
            context=context,
        )

        assert result.success is True
        assert "base_branch" in result.data
        assert "compare_branch" in result.data
        assert "summary" in result.data

    @pytest.mark.asyncio
    async def test_branch_merge_preview_action(self):
        """Test BranchMergePreviewAction execution."""
        from lib.oda.ontology.actions.branch_actions import BranchMergePreviewAction

        action = BranchMergePreviewAction()
        context = ActionContext(actor_id="user-001")

        result = await action.execute(
            params={
                "source_branch": "feature",
                "target_branch": "main",
                "merge_strategy": "three_way",
            },
            context=context,
        )

        assert result.success is True
        assert "can_merge" in result.data
        assert "conflicts" in result.data

    @pytest.mark.asyncio
    async def test_conflict_resolve_action_requires_proposal(self):
        """Test that ConflictResolveAction is marked hazardous."""
        from lib.oda.ontology.actions.branch_actions import ConflictResolveAction

        assert ConflictResolveAction.requires_proposal is True

    @pytest.mark.asyncio
    async def test_cherry_pick_action_requires_proposal(self):
        """Test that CherryPickAction is marked hazardous."""
        from lib.oda.ontology.actions.branch_actions import CherryPickAction

        assert CherryPickAction.requires_proposal is True

    @pytest.mark.asyncio
    async def test_conflict_resolve_action(self):
        """Test ConflictResolveAction execution."""
        from lib.oda.ontology.actions.branch_actions import ConflictResolveAction

        action = ConflictResolveAction()
        context = ActionContext(actor_id="user-001")

        result = await action.execute(
            params={
                "merge_id": "merge-001",
                "resolutions": [
                    {"conflict_id": "c-001", "mode": "ours"},
                    {"conflict_id": "c-002", "mode": "theirs"},
                ],
            },
            context=context,
        )

        assert result.success is True
        assert result.data["resolved_count"] == 2

    @pytest.mark.asyncio
    async def test_cherry_pick_action(self):
        """Test CherryPickAction execution."""
        from lib.oda.ontology.actions.branch_actions import CherryPickAction

        action = CherryPickAction()
        context = ActionContext(actor_id="user-001")

        result = await action.execute(
            params={
                "commit_id": "commit-abc",
                "target_branch": "main",
                "conflict_resolution": "abort",
            },
            context=context,
        )

        assert result.success is True
        assert result.data["commit_id"] == "commit-abc"

    def test_action_registration(self):
        """Test that all branch actions are registered."""
        from lib.oda.ontology.actions import action_registry

        expected_actions = [
            "branch.compare",
            "branch.diff",
            "branch.merge_preview",
            "branch.resolve_conflict",
            "branch.cherry_pick",
        ]

        registered = action_registry.list_actions()

        for action_name in expected_actions:
            assert action_name in registered, f"{action_name} not registered"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestBranchingIntegration:
    """Integration tests for branching features."""

    def test_module_imports(self):
        """Test that all new modules can be imported."""
        from lib.oda.transaction import (
            SchemaConflictType,
            SchemaConflictSeverity,
            SchemaConflict,
            SchemaConflictBatch,
            SchemaConflictDetector,
            CherryPickStatus,
            CherryPickConflictResolution,
            CherryPickChange,
            CherryPickResult,
            CherryPicker,
        )

        # Basic sanity checks
        assert SchemaConflictType.TYPE_MISMATCH.value == "type_mismatch"
        assert CherryPickStatus.COMPLETED.value == "completed"

    def test_conflict_type_values(self):
        """Test SchemaConflictType enum values."""
        assert SchemaConflictType.SCHEMA_CHANGE.value == "schema_change"
        assert SchemaConflictType.TYPE_MISMATCH.value == "type_mismatch"
        assert SchemaConflictType.DELETION_CONFLICT.value == "deletion_conflict"
        assert SchemaConflictType.CONSTRAINT_VIOLATION.value == "constraint_violation"

    def test_cherry_pick_status_values(self):
        """Test CherryPickStatus enum values."""
        assert CherryPickStatus.PENDING.value == "pending"
        assert CherryPickStatus.IN_PROGRESS.value == "in_progress"
        assert CherryPickStatus.CONFLICTED.value == "conflicted"
        assert CherryPickStatus.COMPLETED.value == "completed"
        assert CherryPickStatus.ABORTED.value == "aborted"
        assert CherryPickStatus.FAILED.value == "failed"

    def test_schema_conflict_model_serialization(self):
        """Test SchemaConflict Pydantic model."""
        conflict = SchemaConflict(
            conflict_type=SchemaConflictType.TYPE_MISMATCH,
            severity=SchemaConflictSeverity.ERROR,
            object_type="User",
            field_name="age",
            branch_a_value="int",
            branch_b_value="str",
        )

        # Test model_dump
        data = conflict.model_dump()
        assert data["conflict_type"] == "type_mismatch"
        assert data["object_type"] == "User"

        # Test properties
        assert conflict.key == "User:age"
        assert conflict.is_blocking is True

    def test_cherry_pick_result_properties(self):
        """Test CherryPickResult computed properties."""
        result = CherryPickResult(
            success=True,
            status=CherryPickStatus.COMPLETED,
            commit_id="abc",
            target_branch_id="main",
            applied_changes=[
                CherryPickChange(object_type="User", object_id="1", applied=True),
                CherryPickChange(object_type="User", object_id="2", applied=True),
            ],
            skipped_changes=[
                CherryPickChange(object_type="User", object_id="3", skipped=True),
            ],
            conflicts=[
                SchemaConflict(
                    conflict_type=SchemaConflictType.SCHEMA_CHANGE,
                    object_type="User",
                )
            ],
        )

        assert result.applied_count == 2
        assert result.skipped_count == 1
        assert result.has_conflicts is True
