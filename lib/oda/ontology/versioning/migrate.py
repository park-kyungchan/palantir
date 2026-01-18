"""
Orion ODA v4.0 - Version Migration Framework
=============================================

Provides up/down migration support for ObjectType schema changes:
- Migration: Single migration step
- MigrationRunner: Executes migrations in order
- MigrationRegistry: Tracks available migrations

Features:
- Bidirectional migrations (up/down)
- Transaction-like semantics
- Rollback on failure
- Migration history tracking

Schema Version: 4.0.0
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
)

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.versioning.schema import (
    SchemaVersion,
    parse_version,
    compare_versions,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND TYPES
# =============================================================================


class MigrationDirection(str, Enum):
    """Direction of migration."""

    UP = "up"  # Upgrade to newer version
    DOWN = "down"  # Downgrade to older version


class MigrationStatus(str, Enum):
    """Status of a migration execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# =============================================================================
# MIGRATION STEP
# =============================================================================


@dataclass
class MigrationStep:
    """
    Represents a single migration step.

    Attributes:
        name: Step identifier
        description: Human-readable description
        transform: Function to transform data
        validate: Optional validation function
    """

    name: str
    description: str
    transform: Callable[[Dict[str, Any]], Dict[str, Any]]
    validate: Optional[Callable[[Dict[str, Any]], bool]] = None

    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the transformation."""
        result = self.transform(data)

        if self.validate and not self.validate(result):
            raise ValueError(f"Validation failed after step: {self.name}")

        return result


# =============================================================================
# MIGRATION PROTOCOL AND BASE CLASS
# =============================================================================


@runtime_checkable
class MigrationProtocol(Protocol):
    """Protocol for migrations."""

    object_type: str
    from_version: str
    to_version: str

    async def up(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data up (to newer version)."""
        ...

    async def down(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data down (to older version)."""
        ...


T = TypeVar("T", bound=OntologyObject)


class Migration(ABC, Generic[T]):
    """
    Base class for migrations.

    Extend this to create versioned migrations.

    Example:
        ```python
        class TaskV1ToV2Migration(Migration[Task]):
            object_type = "Task"
            from_version = "1.0.0"
            to_version = "2.0.0"

            async def up(self, data: Dict[str, Any]) -> Dict[str, Any]:
                # Add new 'priority' field with default
                data["priority"] = data.get("priority", "medium")
                return data

            async def down(self, data: Dict[str, Any]) -> Dict[str, Any]:
                # Remove 'priority' field
                data.pop("priority", None)
                return data
        ```
    """

    # Class attributes to override
    object_type: str = ""
    from_version: str = ""
    to_version: str = ""
    description: str = ""
    reversible: bool = True

    @abstractmethod
    async def up(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate data to newer version.

        Args:
            data: Object data as dict

        Returns:
            Transformed data dict
        """
        ...

    async def down(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate data to older version.

        Override this for reversible migrations.
        Default raises NotImplementedError.

        Args:
            data: Object data as dict

        Returns:
            Transformed data dict
        """
        if not self.reversible:
            raise NotImplementedError(f"Migration {self.__class__.__name__} is not reversible")
        raise NotImplementedError(f"down() not implemented for {self.__class__.__name__}")

    @property
    def migration_id(self) -> str:
        """Unique identifier for this migration."""
        return f"{self.object_type}_{self.from_version}_to_{self.to_version}"

    @property
    def from_schema_version(self) -> SchemaVersion:
        """Get from_version as SchemaVersion."""
        return parse_version(self.from_version)

    @property
    def to_schema_version(self) -> SchemaVersion:
        """Get to_version as SchemaVersion."""
        return parse_version(self.to_version)

    def validate_versions(self) -> None:
        """Validate that from_version < to_version."""
        if compare_versions(self.from_version, self.to_version) >= 0:
            raise ValueError(
                f"Migration from_version ({self.from_version}) must be "
                f"less than to_version ({self.to_version})"
            )


# =============================================================================
# MIGRATION RESULT
# =============================================================================


@dataclass
class MigrationResult:
    """
    Result of a migration execution.

    Attributes:
        migration_id: ID of the migration
        direction: Up or down
        status: Execution status
        data: Transformed data (if successful)
        error: Error message (if failed)
        duration_ms: Execution time
    """

    migration_id: str
    direction: MigrationDirection
    status: MigrationStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0
    steps_completed: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    @property
    def is_successful(self) -> bool:
        """Check if migration completed successfully."""
        return self.status == MigrationStatus.COMPLETED


@dataclass
class MigrationPlan:
    """
    Plan for migrating from one version to another.

    Attributes:
        object_type: ObjectType being migrated
        from_version: Starting version
        to_version: Target version
        migrations: List of migrations to apply (in order)
        direction: Overall direction
    """

    object_type: str
    from_version: str
    to_version: str
    migrations: List[Migration] = field(default_factory=list)
    direction: MigrationDirection = MigrationDirection.UP

    @property
    def step_count(self) -> int:
        """Number of migration steps."""
        return len(self.migrations)

    def validate(self) -> List[str]:
        """Validate the migration plan."""
        errors = []

        if not self.migrations:
            errors.append("No migrations in plan")
            return errors

        # Check version chain
        expected_version = self.from_version
        for i, m in enumerate(self.migrations):
            if self.direction == MigrationDirection.UP:
                if m.from_version != expected_version:
                    errors.append(
                        f"Migration {i} expects from_version {m.from_version}, "
                        f"but chain has {expected_version}"
                    )
                expected_version = m.to_version
            else:
                if m.to_version != expected_version:
                    errors.append(
                        f"Migration {i} expects to_version {m.to_version}, "
                        f"but chain has {expected_version}"
                    )
                expected_version = m.from_version

        # Check final version
        final = self.to_version
        if self.direction == MigrationDirection.UP:
            if expected_version != final:
                errors.append(f"Migration chain ends at {expected_version}, expected {final}")
        else:
            if expected_version != final:
                errors.append(f"Migration chain ends at {expected_version}, expected {final}")

        return errors


# =============================================================================
# MIGRATION REGISTRY
# =============================================================================


class MigrationRegistry:
    """
    Registry for migrations.

    Tracks all available migrations and builds migration paths.

    Usage:
        ```python
        registry = get_migration_registry()

        # Register migrations
        registry.register(TaskV1ToV2Migration())
        registry.register(TaskV2ToV3Migration())

        # Build migration plan
        plan = registry.build_plan("Task", "1.0.0", "3.0.0")

        # Execute
        runner = MigrationRunner(registry)
        result = await runner.migrate(data, plan)
        ```
    """

    _instance: Optional[MigrationRegistry] = None

    def __init__(self) -> None:
        # object_type -> from_version -> Migration
        self._migrations: Dict[str, Dict[str, Migration]] = {}
        # Reverse index: object_type -> to_version -> Migration
        self._reverse_index: Dict[str, Dict[str, Migration]] = {}
        # Execution history
        self._history: List[MigrationResult] = []

    @classmethod
    def get_instance(cls) -> MigrationRegistry:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("MigrationRegistry singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    def register(self, migration: Migration) -> None:
        """
        Register a migration.

        Args:
            migration: Migration instance to register

        Raises:
            ValueError: If migration with same from_version exists
        """
        migration.validate_versions()

        obj_type = migration.object_type
        from_ver = migration.from_version
        to_ver = migration.to_version

        # Initialize dicts if needed
        if obj_type not in self._migrations:
            self._migrations[obj_type] = {}
            self._reverse_index[obj_type] = {}

        # Check for duplicates
        if from_ver in self._migrations[obj_type]:
            existing = self._migrations[obj_type][from_ver]
            raise ValueError(
                f"Migration from {from_ver} already exists for {obj_type}: "
                f"{existing.migration_id}"
            )

        self._migrations[obj_type][from_ver] = migration
        self._reverse_index[obj_type][to_ver] = migration

        logger.info(
            f"Registered migration: {migration.migration_id} "
            f"({from_ver} -> {to_ver})"
        )

    def get_migration(
        self,
        object_type: str,
        from_version: str,
    ) -> Optional[Migration]:
        """Get a migration by object type and from_version."""
        return self._migrations.get(object_type, {}).get(from_version)

    def get_migration_to(
        self,
        object_type: str,
        to_version: str,
    ) -> Optional[Migration]:
        """Get a migration by object type and to_version."""
        return self._reverse_index.get(object_type, {}).get(to_version)

    def list_migrations(
        self,
        object_type: Optional[str] = None,
    ) -> List[Migration]:
        """List all migrations, optionally filtered by object type."""
        result = []

        types_to_check = [object_type] if object_type else list(self._migrations.keys())

        for obj_type in types_to_check:
            if obj_type in self._migrations:
                result.extend(self._migrations[obj_type].values())

        return sorted(result, key=lambda m: (m.object_type, m.from_schema_version))

    def build_plan(
        self,
        object_type: str,
        from_version: str,
        to_version: str,
    ) -> MigrationPlan:
        """
        Build a migration plan from one version to another.

        Args:
            object_type: ObjectType to migrate
            from_version: Starting version
            to_version: Target version

        Returns:
            MigrationPlan with ordered migrations

        Raises:
            ValueError: If no path exists
        """
        comparison = compare_versions(from_version, to_version)

        if comparison == 0:
            return MigrationPlan(
                object_type=object_type,
                from_version=from_version,
                to_version=to_version,
                migrations=[],
            )

        direction = MigrationDirection.UP if comparison < 0 else MigrationDirection.DOWN
        migrations = []
        current = from_version

        if direction == MigrationDirection.UP:
            # Build forward path
            while compare_versions(current, to_version) < 0:
                migration = self.get_migration(object_type, current)
                if not migration:
                    raise ValueError(
                        f"No migration found from {current} for {object_type}. "
                        f"Cannot build path to {to_version}."
                    )
                migrations.append(migration)
                current = migration.to_version
        else:
            # Build backward path
            while compare_versions(current, to_version) > 0:
                migration = self.get_migration_to(object_type, current)
                if not migration:
                    raise ValueError(
                        f"No migration found to {current} for {object_type}. "
                        f"Cannot build path to {to_version}."
                    )
                if not migration.reversible:
                    raise ValueError(
                        f"Migration {migration.migration_id} is not reversible. "
                        f"Cannot downgrade."
                    )
                migrations.append(migration)
                current = migration.from_version

        return MigrationPlan(
            object_type=object_type,
            from_version=from_version,
            to_version=to_version,
            migrations=migrations,
            direction=direction,
        )

    def record_result(self, result: MigrationResult) -> None:
        """Record a migration result in history."""
        self._history.append(result)

    def get_history(
        self,
        object_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MigrationResult]:
        """Get migration history."""
        history = self._history

        if object_type:
            history = [r for r in history if object_type in r.migration_id]

        return history[-limit:]


# =============================================================================
# MIGRATION RUNNER
# =============================================================================


class MigrationRunner:
    """
    Executes migrations.

    Features:
    - Sequential execution
    - Rollback on failure
    - Progress tracking

    Usage:
        ```python
        runner = MigrationRunner()
        plan = registry.build_plan("Task", "1.0.0", "3.0.0")

        result = await runner.migrate(data, plan)
        if result.is_successful:
            new_data = result.data
        ```
    """

    def __init__(self, registry: Optional[MigrationRegistry] = None) -> None:
        self._registry = registry or get_migration_registry()

    async def migrate(
        self,
        data: Dict[str, Any],
        plan: MigrationPlan,
        rollback_on_failure: bool = True,
    ) -> MigrationResult:
        """
        Execute a migration plan.

        Args:
            data: Object data to migrate
            plan: Migration plan to execute
            rollback_on_failure: Whether to rollback on failure

        Returns:
            MigrationResult with transformed data or error
        """
        import time

        # Validate plan
        errors = plan.validate()
        if errors:
            return MigrationResult(
                migration_id=f"{plan.object_type}_{plan.from_version}_to_{plan.to_version}",
                direction=plan.direction,
                status=MigrationStatus.FAILED,
                error=f"Invalid plan: {'; '.join(errors)}",
            )

        if not plan.migrations:
            # No migrations needed
            return MigrationResult(
                migration_id=f"{plan.object_type}_{plan.from_version}_to_{plan.to_version}",
                direction=plan.direction,
                status=MigrationStatus.COMPLETED,
                data=data,
            )

        start_time = time.time()
        current_data = dict(data)
        completed_migrations: List[Migration] = []

        result = MigrationResult(
            migration_id=f"{plan.object_type}_{plan.from_version}_to_{plan.to_version}",
            direction=plan.direction,
            status=MigrationStatus.RUNNING,
        )

        try:
            for migration in plan.migrations:
                logger.info(f"Executing migration: {migration.migration_id}")

                if plan.direction == MigrationDirection.UP:
                    current_data = await migration.up(current_data)
                else:
                    current_data = await migration.down(current_data)

                completed_migrations.append(migration)
                result.steps_completed += 1

            result.status = MigrationStatus.COMPLETED
            result.data = current_data
            result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            result.status = MigrationStatus.FAILED
            result.error = str(e)

            if rollback_on_failure and completed_migrations:
                logger.info("Rolling back migrations...")
                try:
                    rollback_data = current_data
                    for migration in reversed(completed_migrations):
                        if plan.direction == MigrationDirection.UP:
                            rollback_data = await migration.down(rollback_data)
                        else:
                            rollback_data = await migration.up(rollback_data)
                    result.status = MigrationStatus.ROLLED_BACK
                    result.data = rollback_data
                    logger.info("Rollback completed")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}", exc_info=True)
                    result.error = f"{result.error}; Rollback failed: {rollback_error}"

        result.duration_ms = int((time.time() - start_time) * 1000)
        self._registry.record_result(result)

        return result

    async def migrate_object(
        self,
        obj: OntologyObject,
        from_version: str,
        to_version: str,
    ) -> tuple[OntologyObject, MigrationResult]:
        """
        Migrate an OntologyObject.

        Args:
            obj: Object to migrate
            from_version: Current version
            to_version: Target version

        Returns:
            Tuple of (migrated object, result)
        """
        plan = self._registry.build_plan(
            obj.__class__.__name__,
            from_version,
            to_version,
        )

        data = obj.model_dump()
        result = await self.migrate(data, plan)

        if result.is_successful and result.data:
            migrated_obj = obj.__class__(**result.data)
            return migrated_obj, result

        return obj, result


# =============================================================================
# DECORATOR
# =============================================================================


def migration(
    object_type: str,
    from_version: str,
    to_version: str,
    description: str = "",
    reversible: bool = True,
    auto_register: bool = True,
) -> Callable:
    """
    Decorator to create and register a migration from a function.

    Example:
        ```python
        @migration("Task", "1.0.0", "2.0.0", description="Add priority field")
        async def task_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
            data["priority"] = data.get("priority", "medium")
            return data
        ```
    """

    def decorator(func: Callable) -> Migration:
        # Create migration class dynamically with up method defined in body
        # to satisfy ABC requirements
        class FunctionMigration(Migration):
            async def up(self, data: Dict[str, Any]) -> Dict[str, Any]:
                if asyncio.iscoroutinefunction(func):
                    return await func(data)
                return func(data)

        FunctionMigration.object_type = object_type
        FunctionMigration.from_version = from_version
        FunctionMigration.to_version = to_version
        FunctionMigration.description = description
        FunctionMigration.reversible = reversible

        migration_instance = FunctionMigration()

        if auto_register:
            get_migration_registry().register(migration_instance)

        return migration_instance

    return decorator


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_migration_registry() -> MigrationRegistry:
    """Get the global MigrationRegistry instance."""
    return MigrationRegistry.get_instance()
