"""
Orion ODA V4.0 - ObjectType Expansion Tests
============================================

Unit tests for Phase 2.3-2.4 ObjectType expansion:
- Lifecycle Hooks (pre_save, post_save, pre_delete, validation)
- Schema Versioning (version tracking, migrations, compatibility)

Tests cover:
- LifecycleHookRegistry operations
- Hook priority ordering
- Hook chaining and abort behavior
- SchemaVersion parsing and comparison
- MigrationRegistry and MigrationRunner
- CompatibilityLayer transforms

Schema Version: 4.0.0
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from lib.oda.ontology.ontology_types import OntologyObject, ObjectStatus
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# TEST OBJECT TYPES
# =============================================================================


class TestTask(OntologyObject):
    """Test ObjectType for lifecycle hooks tests."""

    title: str = "Untitled"
    priority: str = "medium"
    assigned_to_id: Optional[str] = None


# =============================================================================
# LIFECYCLE HOOKS TESTS
# =============================================================================


class TestLifecycleHookTypes:
    """Tests for LifecycleHookType enum."""

    def test_hook_types_exist(self):
        """Test all expected hook types exist."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleHookType

        assert LifecycleHookType.PRE_SAVE.value == "pre_save"
        assert LifecycleHookType.POST_SAVE.value == "post_save"
        assert LifecycleHookType.PRE_DELETE.value == "pre_delete"
        assert LifecycleHookType.POST_DELETE.value == "post_delete"
        assert LifecycleHookType.VALIDATION.value == "validation"

    def test_hook_priority_ordering(self):
        """Test hook priority values are ordered correctly."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleHookPriority

        assert LifecycleHookPriority.CRITICAL < LifecycleHookPriority.HIGH
        assert LifecycleHookPriority.HIGH < LifecycleHookPriority.NORMAL
        assert LifecycleHookPriority.NORMAL < LifecycleHookPriority.LOW
        assert LifecycleHookPriority.LOW < LifecycleHookPriority.DEFERRED


class TestLifecycleContext:
    """Tests for LifecycleContext."""

    def test_context_for_save_create(self):
        """Test creating context for new object save."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleContext

        task = TestTask(title="New Task")
        context = LifecycleContext.for_save(task, actor_id="agent-1")

        assert context.object_type == "TestTask"
        assert context.object_id == task.id
        assert context.operation == "save"
        assert context.is_create is True
        assert context.is_update is False
        assert context.original is None
        assert context.current == task
        assert context.actor_id == "agent-1"

    def test_context_for_save_update(self):
        """Test creating context for object update."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleContext

        original = TestTask(title="Original")
        updated = TestTask(id=original.id, title="Updated")
        context = LifecycleContext.for_save(updated, original=original)

        assert context.is_create is False
        assert context.is_update is True
        assert context.original == original
        assert context.current == updated

    def test_context_for_delete(self):
        """Test creating context for delete."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleContext

        task = TestTask(title="To Delete")
        context = LifecycleContext.for_delete(task, actor_id="agent-1")

        assert context.operation == "delete"
        assert context.object_id == task.id


class TestHookResult:
    """Tests for HookResult."""

    def test_ok_result(self):
        """Test creating OK result."""
        from lib.oda.ontology.hooks.lifecycle import HookResult

        result = HookResult.ok()
        assert result.success is True
        assert result.abort is False

    def test_ok_with_modified_object(self):
        """Test OK result with modified object."""
        from lib.oda.ontology.hooks.lifecycle import HookResult

        task = TestTask(title="Modified")
        result = HookResult.ok(modified_object=task)

        assert result.success is True
        assert result.modified_object == task

    def test_abort_result(self):
        """Test creating abort result."""
        from lib.oda.ontology.hooks.lifecycle import HookResult

        result = HookResult.abort_operation("Validation failed")

        assert result.success is True
        assert result.abort is True
        assert result.abort_reason == "Validation failed"

    def test_validation_failed_result(self):
        """Test creating validation failure result."""
        from lib.oda.ontology.hooks.lifecycle import HookResult

        result = HookResult.validation_failed(["Field 'title' is required"])

        assert result.abort is True
        assert "Field 'title' is required" in result.validation_errors


class TestLifecycleHookRegistry:
    """Tests for LifecycleHookRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleHookRegistry

        LifecycleHookRegistry.reset_instance()
        return LifecycleHookRegistry.get_instance()

    def test_singleton_pattern(self, registry):
        """Test registry is a singleton."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleHookRegistry

        assert LifecycleHookRegistry.get_instance() is registry

    def test_register_hook_class(self, registry):
        """Test registering a hook class."""
        from lib.oda.ontology.hooks.lifecycle import (
            LifecycleHook,
            LifecycleHookType,
            HookResult,
            LifecycleContext,
        )

        class TestHook(LifecycleHook[TestTask]):
            hook_type = LifecycleHookType.PRE_SAVE
            name = "test_hook"

            async def execute(self, obj: TestTask, context: LifecycleContext) -> HookResult:
                return HookResult.ok()

        hook = TestHook()
        registry.register(hook)

        hooks = registry.get_hooks(LifecycleHookType.PRE_SAVE)
        assert len(hooks) == 1

    def test_register_callable(self, registry):
        """Test registering a callable as hook."""
        from lib.oda.ontology.hooks.lifecycle import (
            LifecycleHookType,
            HookResult,
            LifecycleContext,
        )

        async def test_hook(obj: OntologyObject, context: LifecycleContext) -> HookResult:
            return HookResult.ok()

        registry.register(test_hook, hook_type=LifecycleHookType.POST_SAVE)

        hooks = registry.get_hooks(LifecycleHookType.POST_SAVE)
        assert len(hooks) == 1

    def test_priority_ordering(self, registry):
        """Test hooks are ordered by priority."""
        from lib.oda.ontology.hooks.lifecycle import (
            LifecycleHook,
            LifecycleHookType,
            LifecycleHookPriority,
            HookResult,
            LifecycleContext,
        )

        class LowPriorityHook(LifecycleHook):
            hook_type = LifecycleHookType.PRE_SAVE
            priority = LifecycleHookPriority.LOW
            name = "low"

            async def execute(self, obj, context) -> HookResult:
                return HookResult.ok()

        class HighPriorityHook(LifecycleHook):
            hook_type = LifecycleHookType.PRE_SAVE
            priority = LifecycleHookPriority.HIGH
            name = "high"

            async def execute(self, obj, context) -> HookResult:
                return HookResult.ok()

        registry.register(LowPriorityHook())
        registry.register(HighPriorityHook())

        hooks = registry.get_hooks(LifecycleHookType.PRE_SAVE)
        assert len(hooks) == 2
        # High priority should come first
        assert hooks[0].hook_name == "high"
        assert hooks[1].hook_name == "low"

    @pytest.mark.asyncio
    async def test_run_hooks(self, registry):
        """Test running hooks chain."""
        from lib.oda.ontology.hooks.lifecycle import (
            LifecycleHookType,
            LifecycleContext,
            HookResult,
            run_hooks,
        )

        call_order = []

        async def hook1(obj, context) -> HookResult:
            call_order.append("hook1")
            return HookResult.ok()

        async def hook2(obj, context) -> HookResult:
            call_order.append("hook2")
            return HookResult.ok()

        registry.register(hook1, hook_type=LifecycleHookType.PRE_SAVE)
        registry.register(hook2, hook_type=LifecycleHookType.PRE_SAVE)

        task = TestTask(title="Test")
        context = LifecycleContext.for_save(task)

        result = await run_hooks(LifecycleHookType.PRE_SAVE, task, context)

        assert result.success is True
        assert call_order == ["hook1", "hook2"]

    @pytest.mark.asyncio
    async def test_hook_abort_stops_chain(self, registry):
        """Test that abort stops the hook chain."""
        from lib.oda.ontology.hooks.lifecycle import (
            LifecycleHookType,
            LifecycleContext,
            HookResult,
            run_hooks,
        )

        call_order = []

        async def hook1(obj, context) -> HookResult:
            call_order.append("hook1")
            return HookResult.abort_operation("Stopped")

        async def hook2(obj, context) -> HookResult:
            call_order.append("hook2")
            return HookResult.ok()

        registry.register(hook1, hook_type=LifecycleHookType.PRE_SAVE)
        registry.register(hook2, hook_type=LifecycleHookType.PRE_SAVE)

        task = TestTask(title="Test")
        context = LifecycleContext.for_save(task)

        result = await run_hooks(LifecycleHookType.PRE_SAVE, task, context)

        assert result.aborted is True
        assert result.abort_reason == "Stopped"
        assert call_order == ["hook1"]  # hook2 should not run

    @pytest.mark.asyncio
    async def test_hook_modifies_object(self, registry):
        """Test that hooks can modify objects."""
        from lib.oda.ontology.hooks.lifecycle import (
            LifecycleHookType,
            LifecycleContext,
            HookResult,
            run_hooks,
        )

        async def normalize_title(obj: TestTask, context: LifecycleContext) -> HookResult:
            obj.title = obj.title.strip().upper()
            return HookResult.ok(modified_object=obj)

        registry.register(normalize_title, hook_type=LifecycleHookType.PRE_SAVE)

        task = TestTask(title="  my task  ")
        context = LifecycleContext.for_save(task)

        result = await run_hooks(LifecycleHookType.PRE_SAVE, task, context)

        assert result.success is True
        assert result.final_object.title == "MY TASK"


class TestLifecycleHookDecorator:
    """Tests for the @lifecycle_hook decorator."""

    def test_decorator_registers_hook(self):
        """Test decorator auto-registers hook."""
        from lib.oda.ontology.hooks.lifecycle import (
            lifecycle_hook,
            LifecycleHookType,
            LifecycleHookPriority,
            HookResult,
            LifecycleContext,
            LifecycleHookRegistry,
        )

        LifecycleHookRegistry.reset_instance()

        @lifecycle_hook(LifecycleHookType.POST_SAVE, priority=LifecycleHookPriority.LOW)
        async def log_save(obj, context) -> HookResult:
            return HookResult.ok()

        registry = LifecycleHookRegistry.get_instance()
        hooks = registry.get_hooks(LifecycleHookType.POST_SAVE)
        assert len(hooks) >= 1


# =============================================================================
# SCHEMA VERSIONING TESTS
# =============================================================================


class TestSchemaVersion:
    """Tests for SchemaVersion."""

    def test_parse_simple_version(self):
        """Test parsing simple version string."""
        from lib.oda.ontology.versioning.schema import SchemaVersion

        v = SchemaVersion.parse("4.0.0")
        assert v.major == 4
        assert v.minor == 0
        assert v.patch == 0

    def test_parse_version_with_prerelease(self):
        """Test parsing version with prerelease."""
        from lib.oda.ontology.versioning.schema import SchemaVersion

        v = SchemaVersion.parse("4.1.0-beta.1")
        assert v.major == 4
        assert v.minor == 1
        assert v.prerelease == "beta.1"

    def test_parse_version_with_build(self):
        """Test parsing version with build metadata."""
        from lib.oda.ontology.versioning.schema import SchemaVersion

        v = SchemaVersion.parse("4.0.0+build.123")
        assert v.build == "build.123"

    def test_version_comparison(self):
        """Test version comparison."""
        from lib.oda.ontology.versioning.schema import SchemaVersion

        v1 = SchemaVersion(4, 0, 0)
        v2 = SchemaVersion(4, 1, 0)
        v3 = SchemaVersion(5, 0, 0)

        assert v1 < v2
        assert v2 < v3
        assert v1 == SchemaVersion(4, 0, 0)

    def test_version_bump(self):
        """Test version bumping."""
        from lib.oda.ontology.versioning.schema import SchemaVersion, VersionChangeType

        v = SchemaVersion(4, 0, 0)

        v_patch = v.bump(VersionChangeType.PATCH)
        assert str(v_patch) == "4.0.1"

        v_minor = v.bump(VersionChangeType.MINOR)
        assert str(v_minor) == "4.1.0"

        v_major = v.bump(VersionChangeType.MAJOR)
        assert str(v_major) == "5.0.0"

    def test_version_compatibility(self):
        """Test version compatibility check."""
        from lib.oda.ontology.versioning.schema import SchemaVersion

        v4_0 = SchemaVersion(4, 0, 0)
        v4_1 = SchemaVersion(4, 1, 0)
        v5_0 = SchemaVersion(5, 0, 0)

        assert v4_0.is_compatible_with(v4_1)  # Same major
        assert not v4_0.is_compatible_with(v5_0)  # Different major


class TestSchemaVersionRegistry:
    """Tests for SchemaVersionRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        from lib.oda.ontology.versioning.schema import SchemaVersionRegistry

        SchemaVersionRegistry.reset_instance()
        return SchemaVersionRegistry.get_instance()

    def test_register_object_type(self, registry):
        """Test registering an ObjectType with version."""
        obj_version = registry.register("Task", "1.0.0", "Initial Task type")

        assert obj_version.object_type == "Task"
        assert obj_version.version == "1.0.0"

    def test_get_version(self, registry):
        """Test getting version for an ObjectType."""
        registry.register("Task", "2.0.0")

        version = registry.get_version_string("Task")
        assert version == "2.0.0"

    def test_bump_version(self, registry):
        """Test bumping version."""
        from lib.oda.ontology.versioning.schema import VersionChangeType

        registry.register("Task", "1.0.0")
        new_version = registry.bump_version(
            "Task",
            VersionChangeType.MINOR,
            "Added priority field",
        )

        assert new_version.version == "1.1.0"
        assert len(new_version.change_log) == 2  # Initial + bump

    def test_deprecate_object_type(self, registry):
        """Test deprecating an ObjectType."""
        registry.register("OldTask", "1.0.0")
        deprecated = registry.deprecate(
            "OldTask",
            "Use Task instead",
            successor_type="Task",
        )

        assert deprecated.deprecated is True
        assert deprecated.successor_type == "Task"

    def test_check_compatibility(self, registry):
        """Test compatibility checking."""
        registry.register("Task", "2.0.0")

        compat = registry.check_compatibility("Task", "2.1.0")
        assert compat["compatible"] is True

        compat = registry.check_compatibility("Task", "3.0.0")
        assert compat["compatible"] is False


# =============================================================================
# MIGRATION TESTS
# =============================================================================


class TestMigration:
    """Tests for Migration base class."""

    def test_create_migration(self):
        """Test creating a migration class."""
        from lib.oda.ontology.versioning.migrate import Migration

        class TaskV1ToV2(Migration[TestTask]):
            object_type = "Task"
            from_version = "1.0.0"
            to_version = "2.0.0"

            async def up(self, data: Dict[str, Any]) -> Dict[str, Any]:
                data["priority"] = data.get("priority", "medium")
                return data

            async def down(self, data: Dict[str, Any]) -> Dict[str, Any]:
                data.pop("priority", None)
                return data

        migration = TaskV1ToV2()
        assert migration.migration_id == "Task_1.0.0_to_2.0.0"
        assert migration.reversible is True

    def test_migration_version_validation(self):
        """Test migration validates from < to version."""
        from lib.oda.ontology.versioning.migrate import Migration

        class BadMigration(Migration):
            object_type = "Task"
            from_version = "2.0.0"
            to_version = "1.0.0"  # Invalid: to < from

            async def up(self, data):
                return data

        with pytest.raises(ValueError, match="must be less than"):
            BadMigration().validate_versions()


class TestMigrationRegistry:
    """Tests for MigrationRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        from lib.oda.ontology.versioning.migrate import MigrationRegistry

        MigrationRegistry.reset_instance()
        return MigrationRegistry.get_instance()

    def test_register_migration(self, registry):
        """Test registering a migration."""
        from lib.oda.ontology.versioning.migrate import Migration

        class TaskV1ToV2(Migration):
            object_type = "Task"
            from_version = "1.0.0"
            to_version = "2.0.0"

            async def up(self, data):
                return data

        migration = TaskV1ToV2()
        registry.register(migration)

        assert registry.get_migration("Task", "1.0.0") is migration

    def test_build_migration_plan(self, registry):
        """Test building migration plan."""
        from lib.oda.ontology.versioning.migrate import Migration, MigrationDirection

        class TaskV1ToV2(Migration):
            object_type = "Task"
            from_version = "1.0.0"
            to_version = "2.0.0"

            async def up(self, data):
                return data

        class TaskV2ToV3(Migration):
            object_type = "Task"
            from_version = "2.0.0"
            to_version = "3.0.0"

            async def up(self, data):
                return data

        registry.register(TaskV1ToV2())
        registry.register(TaskV2ToV3())

        plan = registry.build_plan("Task", "1.0.0", "3.0.0")

        assert plan.direction == MigrationDirection.UP
        assert plan.step_count == 2
        assert len(plan.validate()) == 0  # No errors

    def test_build_downgrade_plan(self, registry):
        """Test building downgrade plan."""
        from lib.oda.ontology.versioning.migrate import Migration, MigrationDirection

        class TaskV1ToV2(Migration):
            object_type = "Task"
            from_version = "1.0.0"
            to_version = "2.0.0"
            reversible = True

            async def up(self, data):
                return data

            async def down(self, data):
                return data

        registry.register(TaskV1ToV2())

        plan = registry.build_plan("Task", "2.0.0", "1.0.0")

        assert plan.direction == MigrationDirection.DOWN
        assert plan.step_count == 1


class TestMigrationRunner:
    """Tests for MigrationRunner."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry."""
        from lib.oda.ontology.versioning.migrate import MigrationRegistry

        MigrationRegistry.reset_instance()
        return MigrationRegistry.get_instance()

    @pytest.mark.asyncio
    async def test_run_migration(self, registry):
        """Test running a migration."""
        from lib.oda.ontology.versioning.migrate import (
            Migration,
            MigrationRunner,
            MigrationStatus,
        )

        class TaskV1ToV2(Migration):
            object_type = "Task"
            from_version = "1.0.0"
            to_version = "2.0.0"

            async def up(self, data):
                data["priority"] = "medium"
                return data

        registry.register(TaskV1ToV2())
        runner = MigrationRunner(registry)

        plan = registry.build_plan("Task", "1.0.0", "2.0.0")
        result = await runner.migrate({"title": "Test"}, plan)

        assert result.status == MigrationStatus.COMPLETED
        assert result.data["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_migration_rollback_on_failure(self, registry):
        """Test migration rollback on failure."""
        from lib.oda.ontology.versioning.migrate import (
            Migration,
            MigrationRunner,
            MigrationStatus,
        )

        class TaskV1ToV2(Migration):
            object_type = "Task"
            from_version = "1.0.0"
            to_version = "2.0.0"

            async def up(self, data):
                data["step1"] = True
                return data

            async def down(self, data):
                data.pop("step1", None)
                return data

        class TaskV2ToV3(Migration):
            object_type = "Task"
            from_version = "2.0.0"
            to_version = "3.0.0"

            async def up(self, data):
                raise ValueError("Migration failed!")

            async def down(self, data):
                return data

        registry.register(TaskV1ToV2())
        registry.register(TaskV2ToV3())
        runner = MigrationRunner(registry)

        plan = registry.build_plan("Task", "1.0.0", "3.0.0")
        result = await runner.migrate({"title": "Test"}, plan)

        assert result.status == MigrationStatus.ROLLED_BACK
        assert "step1" not in result.data  # Rolled back


class TestMigrationDecorator:
    """Tests for @migration decorator."""

    def test_migration_decorator(self):
        """Test creating migration with decorator."""
        from lib.oda.ontology.versioning.migrate import (
            migration,
            MigrationRegistry,
        )

        MigrationRegistry.reset_instance()

        @migration("Task", "1.0.0", "1.1.0", description="Add tags")
        async def task_add_tags(data: Dict[str, Any]) -> Dict[str, Any]:
            data["tags"] = []
            return data

        registry = MigrationRegistry.get_instance()
        m = registry.get_migration("Task", "1.0.0")
        assert m is not None
        assert m.description == "Add tags"


# =============================================================================
# COMPATIBILITY LAYER TESTS
# =============================================================================


class TestPropertyMapping:
    """Tests for PropertyMapping."""

    def test_simple_rename(self):
        """Test simple property rename."""
        from lib.oda.ontology.versioning.compat import PropertyMapping

        mapping = PropertyMapping(
            old_name="user_id",
            new_name="assigned_to_id",
        )

        assert mapping.apply_forward("123") == "123"

    def test_mapping_with_transform(self):
        """Test mapping with transformation."""
        from lib.oda.ontology.versioning.compat import PropertyMapping

        mapping = PropertyMapping(
            old_name="priority_level",
            new_name="priority",
            transform=lambda v: {"1": "low", "2": "medium", "3": "high"}[v],
        )

        assert mapping.apply_forward("2") == "medium"


class TestTypeCoercion:
    """Tests for TypeCoercion."""

    def test_string_to_int_coercion(self):
        """Test coercing string to int."""
        from lib.oda.ontology.versioning.compat import TypeCoercion

        coercion = TypeCoercion(
            property_name="count",
            from_type=str,
            to_type=int,
            coerce=lambda v: int(v) if v else 0,
        )

        assert coercion.apply("42") == 42
        assert coercion.apply("") == 0

    def test_coercion_with_default(self):
        """Test coercion with default value."""
        from lib.oda.ontology.versioning.compat import TypeCoercion, CoercionType

        coercion = TypeCoercion(
            property_name="status",
            from_type=str,
            to_type=str,
            coerce=lambda v: v,
            coercion_type=CoercionType.DEFAULT,
            default_value="active",
        )

        assert coercion.apply(None) == "active"


class TestDeprecatedProperty:
    """Tests for DeprecatedProperty."""

    def test_deprecation_warning(self):
        """Test deprecation warning is issued."""
        import warnings
        from lib.oda.ontology.versioning.compat import DeprecatedProperty

        deprecated = DeprecatedProperty(
            name="assignee",
            deprecated_in="2.0.0",
            replacement="assigned_to_id",
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            deprecated.check("2.0.0")
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)


class TestCompatibilityLayer:
    """Tests for CompatibilityLayer."""

    @pytest.fixture
    def layer(self):
        """Create a fresh compatibility layer."""
        from lib.oda.ontology.versioning.compat import CompatibilityLayer

        CompatibilityLayer.reset_instance()
        return CompatibilityLayer.get_instance()

    def test_transform_with_mapping(self, layer):
        """Test transforming data with property mapping."""
        from lib.oda.ontology.versioning.compat import PropertyMapping

        layer.register_mapping(
            "Task",
            PropertyMapping("user_id", "assigned_to_id"),
        )

        data = {"title": "Test", "user_id": "123"}
        result = layer.transform("Task", data)

        assert "user_id" not in result
        assert result["assigned_to_id"] == "123"

    def test_transform_with_coercion(self, layer):
        """Test transforming data with type coercion."""
        from lib.oda.ontology.versioning.compat import TypeCoercion

        layer.register_coercion(
            "Task",
            TypeCoercion(
                property_name="count",
                from_type=str,
                to_type=int,
                coerce=lambda v: int(v),
            ),
        )

        data = {"title": "Test", "count": "42"}
        result = layer.transform("Task", data)

        assert result["count"] == 42

    def test_type_alias(self, layer):
        """Test type alias resolution."""
        layer.register_type_alias("Task", "OldTask")

        assert layer.resolve_type_alias("OldTask") == "Task"
        assert layer.resolve_type_alias("Task") == "Task"

    def test_version_validation(self, layer):
        """Test version validation."""
        layer.register_object_type("Task", "3.0.0", min_supported_version="2.0.0")

        assert layer.validate_version("Task", "2.0.0") is True
        assert layer.validate_version("Task", "1.0.0") is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestLifecycleHooksIntegration:
    """Integration tests for lifecycle hooks with versioning."""

    @pytest.fixture
    def setup_registries(self):
        """Reset all registries."""
        from lib.oda.ontology.hooks.lifecycle import LifecycleHookRegistry
        from lib.oda.ontology.versioning.schema import SchemaVersionRegistry
        from lib.oda.ontology.versioning.migrate import MigrationRegistry
        from lib.oda.ontology.versioning.compat import CompatibilityLayer

        LifecycleHookRegistry.reset_instance()
        SchemaVersionRegistry.reset_instance()
        MigrationRegistry.reset_instance()
        CompatibilityLayer.reset_instance()

    @pytest.mark.asyncio
    async def test_full_lifecycle_with_versioning(self, setup_registries):
        """Test full lifecycle with hooks and versioning."""
        from lib.oda.ontology.hooks.lifecycle import (
            LifecycleHookRegistry,
            LifecycleHookType,
            LifecycleContext,
            HookResult,
        )
        from lib.oda.ontology.versioning.schema import (
            SchemaVersionRegistry,
            VersionChangeType,
        )

        # Setup
        hook_registry = LifecycleHookRegistry.get_instance()
        version_registry = SchemaVersionRegistry.get_instance()

        # Register Task version
        version_registry.register("TestTask", "1.0.0")

        # Register pre_save hook
        async def validate_title(obj: TestTask, context: LifecycleContext) -> HookResult:
            if not obj.title or obj.title == "Untitled":
                return HookResult.validation_failed(["Title is required"])
            return HookResult.ok()

        hook_registry.register(validate_title, hook_type=LifecycleHookType.VALIDATION)

        # Test validation
        task = TestTask(title="My Task")
        context = LifecycleContext.for_save(task)

        result = await hook_registry.run_hooks(LifecycleHookType.VALIDATION, task, context)
        assert result.success is True

        # Test validation failure
        task_bad = TestTask()  # Uses default "Untitled"
        context_bad = LifecycleContext.for_save(task_bad)

        result_bad = await hook_registry.run_hooks(
            LifecycleHookType.VALIDATION, task_bad, context_bad
        )
        assert result_bad.aborted is True
        assert "Title is required" in result_bad.validation_errors


# =============================================================================
# EXPORT TESTS
# =============================================================================


class TestVersioningExport:
    """Tests for versioning export functionality."""

    def test_export_version_registry(self):
        """Test exporting version registry to JSON."""
        from lib.oda.ontology.versioning.schema import SchemaVersionRegistry

        SchemaVersionRegistry.reset_instance()
        registry = SchemaVersionRegistry.get_instance()

        registry.register("Task", "2.0.0", "Task ObjectType")
        registry.register("Agent", "1.5.0", "Agent ObjectType")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "versions.json"
            registry.export_json(path)

            assert path.exists()
            data = json.loads(path.read_text())

            assert "global_version" in data
            assert "object_types" in data
            assert "Task" in data["object_types"]
            assert data["object_types"]["Task"]["version"] == "2.0.0"
