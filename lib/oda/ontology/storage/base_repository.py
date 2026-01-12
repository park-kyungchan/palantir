"""
Orion ODA V3 - Generic Repository Base Class
=============================================
Abstract base implementing Repository Pattern with:
- Optimistic Concurrency Control (OCC) via Atomic CAS
- Transaction-per-operation scope
- Model <-> Domain object conversion
- Event publishing for decoupled observers

Design Improvements over Gemini Research:
1. Separated _create_model() and _get_update_values() instead of single _to_model()
2. AuditableMixin for optional history tracking
3. QueryBuilder pattern for complex filters
4. Type-safe generics with proper bounds

Usage:
    class ActionLogRepository(GenericRepository[OrionActionLog, OrionActionLogModel]):
        model_class = OrionActionLogModel
        domain_class = OrionActionLog

        def _to_domain(self, model): ...
        def _create_model(self, entity, actor_id): ...
        def _get_update_values(self, entity, actor_id, new_version): ...
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lib.oda.infrastructure.event_bus import EventBus
from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.orm import AsyncOntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS (imported from centralized module)
# =============================================================================

from lib.oda.ontology.storage.exceptions import (
    ConcurrencyError,
    OptimisticLockError,
    EntityNotFoundError,
    ProposalNotFoundError,
)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


# =============================================================================
# QUERY RESULT TYPES
# =============================================================================

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """
    Paginated query result with metadata.

    Attributes:
        items: List of domain objects
        total: Total count (without pagination)
        offset: Current offset
        limit: Page size
        has_more: Whether more items exist
    """
    items: List[T]
    total: int
    offset: int
    limit: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total

    @property
    def page(self) -> int:
        """Current page number (1-indexed)."""
        return (self.offset // self.limit) + 1 if self.limit > 0 else 1


# =============================================================================
# TYPE VARIABLES
# =============================================================================

TDomain = TypeVar("TDomain", bound=OntologyObject)
TModel = TypeVar("TModel", bound=AsyncOntologyObject)


# =============================================================================
# GENERIC REPOSITORY
# =============================================================================

class GenericRepository(ABC, Generic[TDomain, TModel]):
    """
    Abstract base repository implementing Repository Pattern with OCC.

    Type Parameters:
        TDomain: Pydantic domain object type (e.g., OrionActionLog)
        TModel: SQLAlchemy ORM model type (e.g., OrionActionLogModel)

    Subclasses must:
        1. Set model_class and domain_class class attributes
        2. Implement _to_domain(), _create_model(), _get_update_values()

    OCC Contract:
        Domain entity should call touch() before save() to increment version.
        Repository validates: entity.version == db_version + 1
    """

    # Subclasses must override these
    model_class: Type[TModel]
    domain_class: Type[TDomain]

    def __init__(self, db: Database, publish_events: bool = True):
        """
        Initialize repository.

        Args:
            db: Database connection manager
            publish_events: Whether to publish domain events (disable for batch ops)
        """
        self.db = db
        self.publish_events = publish_events
        self._event_bus = EventBus.get_instance()

    # =========================================================================
    # ABSTRACT METHODS (Subclasses must implement)
    # =========================================================================

    @abstractmethod
    def _to_domain(self, model: TModel) -> TDomain:
        """
        Convert ORM model to domain entity.

        Example:
            return OrionActionLog(
                id=model.id,
                version=model.version,
                action_type=model.action_type,
                ...
            )
        """
        ...

    @abstractmethod
    def _create_model(self, entity: TDomain, actor_id: str) -> TModel:
        """
        Create new ORM model from domain entity (for INSERT).

        Example:
            return OrionActionLogModel(
                id=entity.id,
                version=1,
                created_by=actor_id,
                ...
            )
        """
        ...

    @abstractmethod
    def _get_update_values(
        self,
        entity: TDomain,
        actor_id: str,
        new_version: int
    ) -> Dict[str, Any]:
        """
        Get values dict for UPDATE statement.

        Example:
            return {
                "action_type": entity.action_type,
                "status": entity.status,
                "version": new_version,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": actor_id,
            }
        """
        ...

    # =========================================================================
    # OPTIONAL OVERRIDES
    # =========================================================================

    def _get_fts_content(self, entity: TDomain) -> str:
        """
        Extract full-text search content from entity.
        Override if domain class has get_searchable_text().
        """
        if hasattr(entity, "get_searchable_text"):
            return entity.get_searchable_text()
        return ""

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    async def save(self, entity: TDomain, actor_id: str = "system") -> TDomain:
        """
        Save entity with Optimistic Concurrency Control.

        Implements Atomic CAS (Compare-And-Swap):
        1. SELECT current version from DB
        2. Validate entity.version == db_version + 1
        3. UPDATE ... WHERE version = db_version
        4. Verify rowcount > 0

        Args:
            entity: Domain entity to save
            actor_id: ID of the actor performing the operation

        Returns:
            Updated entity with new version

        Raises:
            ConcurrencyError: If version conflict detected
        """
        async with self.db.transaction() as session:
            # Step 1: Check current version in DB
            stmt = select(self.model_class.version).where(
                self.model_class.id == entity.id
            )
            result = await session.execute(stmt)
            current_version = result.scalar_one_or_none()

            event_type = "updated"

            if current_version is None:
                # INSERT: New entity
                event_type = "created"
                model = self._create_model(entity, actor_id)

                # Set FTS content if available
                if hasattr(model, "fts_content"):
                    model.fts_content = self._get_fts_content(entity)

                session.add(model)
                entity.version = model.version  # Sync domain object

            else:
                # UPDATE: Existing entity with OCC
                # Validate version sequence: entity should be db_version + 1
                expected_version = current_version
                new_version = current_version + 1

                if entity.version != new_version:
                    # Version mismatch - either stale or concurrent modification
                    raise ConcurrencyError(
                        f"{self.domain_class.__name__} version conflict. "
                        f"DB={current_version}, Entity={entity.version}. "
                        f"Expected={new_version}",
                        expected_version=expected_version,
                        actual_version=entity.version
                    )

                # Get update values
                update_values = self._get_update_values(entity, actor_id, new_version)

                # Add FTS content if model supports it
                if hasattr(self.model_class, "fts_content"):
                    update_values["fts_content"] = self._get_fts_content(entity)

                # Atomic CAS: UPDATE WHERE version = expected_version
                stmt = (
                    update(self.model_class)
                    .where(self.model_class.id == entity.id)
                    .where(self.model_class.version == expected_version)
                    .values(**update_values)
                )

                result = await session.execute(stmt)

                # Verify update succeeded (no concurrent modification)
                if result.rowcount == 0:
                    raise ConcurrencyError(
                        f"Concurrent modification detected for "
                        f"{self.domain_class.__name__} {entity.id}",
                        expected_version=expected_version,
                        actual_version=entity.version
                    )

                entity.version = new_version

        # Publish event after successful commit
        if self.publish_events:
            await self._event_bus.publish(
                f"{self.domain_class.__name__}.{event_type}",
                entity,
                actor_id=actor_id
            )

        return entity

    async def find_by_id(self, entity_id: str) -> Optional[TDomain]:
        """
        Find entity by primary key.

        Args:
            entity_id: Primary key value

        Returns:
            Domain entity or None if not found
        """
        async with self.db.transaction() as session:
            stmt = select(self.model_class).where(self.model_class.id == entity_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def get_by_id(self, entity_id: str) -> TDomain:
        """
        Get entity by ID or raise exception.

        Args:
            entity_id: Primary key value

        Returns:
            Domain entity

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        entity = await self.find_by_id(entity_id)
        if entity is None:
            raise EntityNotFoundError(self.domain_class.__name__, entity_id)
        return entity

    async def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        descending: bool = True
    ) -> List[TDomain]:
        """
        Find all entities with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Column name to order by (default: created_at)
            descending: Sort direction

        Returns:
            List of domain entities
        """
        async with self.db.transaction() as session:
            stmt = select(self.model_class)

            # Apply ordering
            order_column = getattr(
                self.model_class,
                order_by or "created_at",
                self.model_class.created_at
            )
            if descending:
                stmt = stmt.order_by(order_column.desc())
            else:
                stmt = stmt.order_by(order_column.asc())

            stmt = stmt.offset(offset).limit(limit)

            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def find_by_status(self, status: str) -> List[TDomain]:
        """
        Find all entities with given status.

        Args:
            status: Status value to filter by

        Returns:
            List of domain entities
        """
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.status == status)
                .order_by(self.model_class.created_at.desc())
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def count(self) -> int:
        """Get total count of entities."""
        async with self.db.transaction() as session:
            stmt = select(func.count()).select_from(self.model_class)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def count_by_status(self) -> Dict[str, int]:
        """Get count grouped by status."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class.status, func.count())
                .group_by(self.model_class.status)
            )
            result = await session.execute(stmt)
            return {row[0]: row[1] for row in result.all()}

    async def soft_delete(self, entity_id: str, actor_id: str = "system") -> bool:
        """
        Soft delete by setting status to 'deleted'.

        Args:
            entity_id: ID of entity to delete
            actor_id: ID of actor performing deletion

        Returns:
            True if entity was deleted, False if not found
        """
        async with self.db.transaction() as session:
            stmt = (
                update(self.model_class)
                .where(self.model_class.id == entity_id)
                .where(self.model_class.status != "deleted")
                .values(
                    status="deleted",
                    updated_at=datetime.now(timezone.utc),
                    updated_by=actor_id
                )
            )
            result = await session.execute(stmt)

        if result.rowcount > 0 and self.publish_events:
            await self._event_bus.publish(
                f"{self.domain_class.__name__}.deleted",
                {"id": entity_id},
                actor_id=actor_id
            )
            return True
        return False

    async def hard_delete(self, entity_id: str) -> bool:
        """
        Permanently delete entity from database.
        Use with caution - prefer soft_delete for audit compliance.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if entity was deleted, False if not found
        """
        async with self.db.transaction() as session:
            stmt = delete(self.model_class).where(self.model_class.id == entity_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    async def save_many(
        self,
        entities: List[TDomain],
        actor_id: str = "system"
    ) -> List[TDomain]:
        """
        Save multiple entities in a single transaction.
        Note: Events are published individually after commit.

        Args:
            entities: List of domain entities to save
            actor_id: ID of actor performing the operation

        Returns:
            List of saved entities with updated versions
        """
        saved = []
        async with self.db.transaction() as session:
            for entity in entities:
                # Check if exists
                stmt = select(self.model_class.version).where(
                    self.model_class.id == entity.id
                )
                result = await session.execute(stmt)
                current_version = result.scalar_one_or_none()

                if current_version is None:
                    # INSERT
                    model = self._create_model(entity, actor_id)
                    if hasattr(model, "fts_content"):
                        model.fts_content = self._get_fts_content(entity)
                    session.add(model)
                    entity.version = model.version
                else:
                    # UPDATE with OCC
                    new_version = current_version + 1
                    if entity.version != new_version:
                        raise ConcurrencyError(
                            f"Bulk save: version conflict for {entity.id}"
                        )

                    update_values = self._get_update_values(
                        entity, actor_id, new_version
                    )
                    if hasattr(self.model_class, "fts_content"):
                        update_values["fts_content"] = self._get_fts_content(entity)

                    stmt = (
                        update(self.model_class)
                        .where(self.model_class.id == entity.id)
                        .where(self.model_class.version == current_version)
                        .values(**update_values)
                    )
                    await session.execute(stmt)
                    entity.version = new_version

                saved.append(entity)

        # Publish events after commit (if enabled)
        if self.publish_events:
            for entity in saved:
                await self._event_bus.publish(
                    f"{self.domain_class.__name__}.saved",
                    entity,
                    actor_id=actor_id
                )

        return saved

    # =========================================================================
    # QUERY HELPERS
    # =========================================================================

    async def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        async with self.db.transaction() as session:
            stmt = select(func.count()).select_from(self.model_class).where(
                self.model_class.id == entity_id
            )
            result = await session.execute(stmt)
            return result.scalar_one() > 0

    async def find_by_ids(self, entity_ids: List[str]) -> List[TDomain]:
        """Find multiple entities by IDs."""
        if not entity_ids:
            return []

        async with self.db.transaction() as session:
            stmt = select(self.model_class).where(
                self.model_class.id.in_(entity_ids)
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]


# =============================================================================
# TRANSACTIONAL REPOSITORY (Phase 5.4)
# =============================================================================

class TransactionalRepository(GenericRepository[TDomain, TModel]):
    """
    Transaction-aware repository that supports session injection.

    Extends GenericRepository with:
    - Session injection for shared transactions
    - Automatic transaction propagation
    - Support for nested transactions via savepoints

    Usage:
        # With injected session (shared transaction)
        async with db.transaction() as session:
            repo = TransactionalRepository(db)
            repo.set_session(session)
            await repo.save(entity)  # Uses injected session

        # Without injection (creates own transaction)
        repo = TransactionalRepository(db)
        await repo.save(entity)  # Creates new transaction

    Design Pattern:
        This implements the "Session-per-Request" pattern where
        a single session is shared across multiple repository
        operations within a request/transaction boundary.
    """

    def __init__(
        self,
        db: Database,
        session: Optional[AsyncSession] = None,
        publish_events: bool = True
    ):
        """
        Initialize transactional repository.

        Args:
            db: Database connection manager
            session: Optional pre-existing session to use
            publish_events: Whether to publish domain events
        """
        super().__init__(db, publish_events)
        self._injected_session: Optional[AsyncSession] = session

    def set_session(self, session: AsyncSession) -> None:
        """
        Inject a session for shared transaction use.

        Args:
            session: AsyncSession to use for all operations
        """
        self._injected_session = session

    def clear_session(self) -> None:
        """Clear the injected session."""
        self._injected_session = None

    @property
    def has_session(self) -> bool:
        """Check if a session is currently injected."""
        return self._injected_session is not None

    async def save_with_session(
        self,
        entity: TDomain,
        session: AsyncSession,
        actor_id: str = "system"
    ) -> TDomain:
        """
        Save entity using provided session (no new transaction).

        This method is useful when you want to participate in an
        existing transaction without creating a nested one.

        Args:
            entity: Domain entity to save
            session: AsyncSession to use
            actor_id: ID of the actor performing the operation

        Returns:
            Updated entity with new version
        """
        # Check current version in DB
        stmt = select(self.model_class.version).where(
            self.model_class.id == entity.id
        )
        result = await session.execute(stmt)
        current_version = result.scalar_one_or_none()

        event_type = "updated"

        if current_version is None:
            # INSERT: New entity
            event_type = "created"
            model = self._create_model(entity, actor_id)
            if hasattr(model, "fts_content"):
                model.fts_content = self._get_fts_content(entity)
            session.add(model)
            entity.version = model.version
        else:
            # UPDATE with OCC
            expected_version = current_version
            new_version = current_version + 1

            if entity.version != new_version:
                raise ConcurrencyError(
                    f"{self.domain_class.__name__} version conflict. "
                    f"DB={current_version}, Entity={entity.version}",
                    expected_version=expected_version,
                    actual_version=entity.version
                )

            update_values = self._get_update_values(entity, actor_id, new_version)
            if hasattr(self.model_class, "fts_content"):
                update_values["fts_content"] = self._get_fts_content(entity)

            stmt = (
                update(self.model_class)
                .where(self.model_class.id == entity.id)
                .where(self.model_class.version == expected_version)
                .values(**update_values)
            )

            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise ConcurrencyError(
                    f"Concurrent modification for {self.domain_class.__name__} {entity.id}"
                )

            entity.version = new_version

        # Publish event (note: commit hasn't happened yet)
        if self.publish_events:
            await self._event_bus.publish(
                f"{self.domain_class.__name__}.{event_type}",
                entity,
                actor_id=actor_id
            )

        return entity

    async def find_by_id_with_session(
        self,
        entity_id: str,
        session: AsyncSession
    ) -> Optional[TDomain]:
        """
        Find entity using provided session.

        Args:
            entity_id: Primary key value
            session: AsyncSession to use

        Returns:
            Domain entity or None if not found
        """
        stmt = select(self.model_class).where(self.model_class.id == entity_id)
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def delete_with_session(
        self,
        entity_id: str,
        session: AsyncSession,
        actor_id: str = "system",
        hard: bool = False
    ) -> bool:
        """
        Delete entity using provided session.

        Args:
            entity_id: ID of entity to delete
            session: AsyncSession to use
            actor_id: ID of actor performing deletion
            hard: If True, hard delete; else soft delete

        Returns:
            True if deleted, False if not found
        """
        if hard:
            stmt = delete(self.model_class).where(self.model_class.id == entity_id)
        else:
            stmt = (
                update(self.model_class)
                .where(self.model_class.id == entity_id)
                .where(self.model_class.status != "deleted")
                .values(
                    status="deleted",
                    updated_at=datetime.now(timezone.utc),
                    updated_by=actor_id
                )
            )

        result = await session.execute(stmt)
        deleted = result.rowcount > 0

        if deleted and self.publish_events:
            await self._event_bus.publish(
                f"{self.domain_class.__name__}.deleted",
                {"id": entity_id},
                actor_id=actor_id
            )

        return deleted
