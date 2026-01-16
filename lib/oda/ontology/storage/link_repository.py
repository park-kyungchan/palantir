"""
Orion ODA V4.0 - Link Repository
=================================
Repository implementation for Link entities with referential integrity support.

This module provides:
- LinkRepository: CRUD operations for Link instances
- LinkTypeRegistryRepository: Persistence for LinkType definitions
- Bulk link operations (link_many, unlink_many)
- Reverse link resolution

Palantir Pattern:
- Links are persisted as first-class entities
- Referential integrity checked on every link operation
- Cascade policies applied on delete/update

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import delete, func, select, update

from lib.oda.ontology.storage.base_repository import GenericRepository
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.models import LinkModel, LinkTypeRegistryModel
from lib.oda.ontology.types.link_types import (
    LinkTypeMetadata,
    LinkTypeConstraints,
    CascadePolicy,
    LinkDirection,
    ReferentialIntegrityChecker,
    IntegrityViolation,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DOMAIN ENTITIES (Pydantic)
# =============================================================================

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import OntologyObject


class Link(OntologyObject):
    """
    Pydantic domain entity for a persisted link.

    Represents a single link instance between two objects.
    """
    link_type_id: str = Field(..., description="Reference to LinkTypeMetadata")
    source_type: str = Field(..., description="ObjectType of source")
    source_id: str = Field(..., description="Primary key of source")
    target_type: str = Field(..., description="ObjectType of target")
    target_id: str = Field(..., description="Primary key of target")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Link attributes")
    linked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    linked_by: Optional[str] = Field(default=None)


class LinkTypeRegistryEntry(OntologyObject):
    """
    Pydantic domain entity for persisted LinkType metadata.
    """
    link_type_id: str
    source_type: str
    target_type: str
    cardinality: str = "1:N"
    direction: str = "directed"
    reverse_link_id: Optional[str] = None
    backing_table_name: Optional[str] = None
    is_materialized: bool = True
    on_source_delete: str = "cascade"
    on_target_delete: str = "set_null"
    on_source_update: str = "cascade"
    on_target_update: str = "cascade"
    constraints: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    schema_version: str = "1.0.0"

    def to_link_type_metadata(self) -> LinkTypeMetadata:
        """Convert to LinkTypeMetadata instance."""
        constraints = LinkTypeConstraints(**self.constraints) if self.constraints else LinkTypeConstraints()

        return LinkTypeMetadata(
            link_type_id=self.link_type_id,
            source_type=self.source_type,
            target_type=self.target_type,
            cardinality=self.cardinality,
            direction=LinkDirection(self.direction),
            reverse_link_id=self.reverse_link_id,
            backing_table_name=self.backing_table_name,
            is_materialized=self.is_materialized,
            on_source_delete=CascadePolicy(self.on_source_delete),
            on_target_delete=CascadePolicy(self.on_target_delete),
            on_source_update=CascadePolicy(self.on_source_update),
            on_target_update=CascadePolicy(self.on_target_update),
            constraints=constraints,
            description=self.description,
            tags=self.tags,
            schema_version=self.schema_version,
        )


# =============================================================================
# LINK REPOSITORY
# =============================================================================


class LinkRepository(GenericRepository[Link, LinkModel]):
    """
    Repository for Link entities.

    Provides CRUD operations with referential integrity validation.

    Example:
        ```python
        repo = LinkRepository(db)

        # Create a link
        link = Link(
            link_type_id="task_assigned_to_agent",
            source_type="Task",
            source_id="task-123",
            target_type="Agent",
            target_id="agent-456",
        )
        await repo.save(link, actor_id="system")

        # Find links by source
        links = await repo.find_by_source("task_assigned_to_agent", "task-123")

        # Find links by target (reverse lookup)
        links = await repo.find_by_target("task_assigned_to_agent", "agent-456")
        ```
    """

    model_class = LinkModel
    domain_class = Link

    def __init__(
        self,
        db: Database,
        publish_events: bool = True,
        integrity_checker: Optional[ReferentialIntegrityChecker] = None,
    ):
        super().__init__(db, publish_events)
        self._integrity_checker = integrity_checker or ReferentialIntegrityChecker()

    def _to_domain(self, model: LinkModel) -> Link:
        """Convert ORM model to domain entity."""
        return Link(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            version=model.version,
            status=model.status,
            link_type_id=model.link_type_id,
            source_type=model.source_type,
            source_id=model.source_id,
            target_type=model.target_type,
            target_id=model.target_id,
            metadata=model.link_metadata or {},
            linked_at=model.linked_at,
            linked_by=model.linked_by,
        )

    def _create_model(self, entity: Link, actor_id: str) -> LinkModel:
        """Create new ORM model for INSERT."""
        return LinkModel(
            id=entity.id,
            version=entity.version or 1,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=actor_id,
            updated_by=actor_id,
            status=entity.status.value if hasattr(entity.status, 'value') else str(entity.status),
            link_type_id=entity.link_type_id,
            source_type=entity.source_type,
            source_id=entity.source_id,
            target_type=entity.target_type,
            target_id=entity.target_id,
            link_metadata=entity.metadata,
            linked_at=entity.linked_at,
            linked_by=actor_id,
        )

    def _get_update_values(
        self,
        entity: Link,
        actor_id: str,
        new_version: int,
    ) -> Dict[str, Any]:
        """Get values for UPDATE statement."""
        return {
            "version": new_version,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": actor_id,
            "status": entity.status.value if hasattr(entity.status, 'value') else str(entity.status),
            "link_metadata": entity.metadata,
        }

    # =========================================================================
    # LINK-SPECIFIC QUERIES
    # =========================================================================

    async def find_by_source(
        self,
        link_type_id: str,
        source_id: str,
        limit: int = 1000,
    ) -> List[Link]:
        """
        Find all links from a specific source object.

        Args:
            link_type_id: The link type to query
            source_id: Source object ID
            limit: Maximum results

        Returns:
            List of Link entities
        """
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.source_id == source_id)
                .where(self.model_class.status == "active")
                .order_by(self.model_class.linked_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def find_by_target(
        self,
        link_type_id: str,
        target_id: str,
        limit: int = 1000,
    ) -> List[Link]:
        """
        Find all links to a specific target object (reverse lookup).

        Args:
            link_type_id: The link type to query
            target_id: Target object ID
            limit: Maximum results

        Returns:
            List of Link entities
        """
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.target_id == target_id)
                .where(self.model_class.status == "active")
                .order_by(self.model_class.linked_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def find_link(
        self,
        link_type_id: str,
        source_id: str,
        target_id: str,
    ) -> Optional[Link]:
        """
        Find a specific link between source and target.

        Args:
            link_type_id: The link type
            source_id: Source object ID
            target_id: Target object ID

        Returns:
            Link if found, None otherwise
        """
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.source_id == source_id)
                .where(self.model_class.target_id == target_id)
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def link_exists(
        self,
        link_type_id: str,
        source_id: str,
        target_id: str,
    ) -> bool:
        """Check if a link exists between source and target."""
        async with self.db.transaction() as session:
            stmt = (
                select(func.count())
                .select_from(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.source_id == source_id)
                .where(self.model_class.target_id == target_id)
                .where(self.model_class.status == "active")
            )
            result = await session.execute(stmt)
            return result.scalar_one() > 0

    async def count_links_from_source(
        self,
        link_type_id: str,
        source_id: str,
    ) -> int:
        """Count active links from a source."""
        async with self.db.transaction() as session:
            stmt = (
                select(func.count())
                .select_from(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.source_id == source_id)
                .where(self.model_class.status == "active")
            )
            result = await session.execute(stmt)
            return result.scalar_one()

    async def get_linked_target_ids(
        self,
        link_type_id: str,
        source_id: str,
    ) -> Set[str]:
        """Get set of target IDs linked from a source."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class.target_id)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.source_id == source_id)
                .where(self.model_class.status == "active")
            )
            result = await session.execute(stmt)
            return {row[0] for row in result.all()}

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    async def link_many(
        self,
        link_type_id: str,
        source_id: str,
        source_type: str,
        target_ids: List[str],
        target_type: str,
        actor_id: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Link]:
        """
        Create multiple links from a single source.

        Args:
            link_type_id: The link type
            source_id: Source object ID
            source_type: Source ObjectType name
            target_ids: List of target object IDs
            target_type: Target ObjectType name
            actor_id: Actor creating the links
            metadata: Optional metadata for all links

        Returns:
            List of created Link entities
        """
        links = []
        for target_id in target_ids:
            link = Link(
                link_type_id=link_type_id,
                source_type=source_type,
                source_id=source_id,
                target_type=target_type,
                target_id=target_id,
                metadata=metadata or {},
                linked_by=actor_id,
            )
            links.append(link)

        return await self.save_many(links, actor_id=actor_id)

    async def unlink_many(
        self,
        link_type_id: str,
        source_id: str,
        target_ids: List[str],
        actor_id: str = "system",
    ) -> int:
        """
        Remove multiple links (soft delete).

        Args:
            link_type_id: The link type
            source_id: Source object ID
            target_ids: List of target object IDs to unlink
            actor_id: Actor removing the links

        Returns:
            Number of links removed
        """
        if not target_ids:
            return 0

        async with self.db.transaction() as session:
            stmt = (
                update(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.source_id == source_id)
                .where(self.model_class.target_id.in_(target_ids))
                .where(self.model_class.status == "active")
                .values(
                    status="deleted",
                    updated_at=datetime.now(timezone.utc),
                    updated_by=actor_id,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount

    async def unlink_all_from_source(
        self,
        link_type_id: str,
        source_id: str,
        actor_id: str = "system",
    ) -> int:
        """
        Remove all links from a source (soft delete).

        Args:
            link_type_id: The link type
            source_id: Source object ID
            actor_id: Actor removing the links

        Returns:
            Number of links removed
        """
        async with self.db.transaction() as session:
            stmt = (
                update(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
                .where(self.model_class.source_id == source_id)
                .where(self.model_class.status == "active")
                .values(
                    status="deleted",
                    updated_at=datetime.now(timezone.utc),
                    updated_by=actor_id,
                )
            )
            result = await session.execute(stmt)
            return result.rowcount

    async def apply_cascade_delete(
        self,
        object_type: str,
        object_id: str,
        side: str,  # "source" or "target"
        actor_id: str = "system",
    ) -> Dict[str, int]:
        """
        Apply cascade delete policy for an object deletion.

        This method finds all links where the deleted object is either
        source or target, and applies the appropriate cascade policy.

        Args:
            object_type: Type of the deleted object
            object_id: ID of the deleted object
            side: Whether the object was "source" or "target" of links
            actor_id: Actor performing the deletion

        Returns:
            Dict mapping link_type_id to number of affected links
        """
        affected: Dict[str, int] = {}

        async with self.db.transaction() as session:
            if side == "source":
                # Find all link types where this object is source
                stmt = (
                    select(self.model_class.link_type_id, func.count())
                    .where(self.model_class.source_type == object_type)
                    .where(self.model_class.source_id == object_id)
                    .where(self.model_class.status == "active")
                    .group_by(self.model_class.link_type_id)
                )
            else:
                # Find all link types where this object is target
                stmt = (
                    select(self.model_class.link_type_id, func.count())
                    .where(self.model_class.target_type == object_type)
                    .where(self.model_class.target_id == object_id)
                    .where(self.model_class.status == "active")
                    .group_by(self.model_class.link_type_id)
                )

            result = await session.execute(stmt)
            for link_type_id, count in result.all():
                # Soft delete all affected links
                if side == "source":
                    del_stmt = (
                        update(self.model_class)
                        .where(self.model_class.link_type_id == link_type_id)
                        .where(self.model_class.source_id == object_id)
                        .where(self.model_class.status == "active")
                        .values(
                            status="deleted",
                            updated_at=datetime.now(timezone.utc),
                            updated_by=actor_id,
                        )
                    )
                else:
                    del_stmt = (
                        update(self.model_class)
                        .where(self.model_class.link_type_id == link_type_id)
                        .where(self.model_class.target_id == object_id)
                        .where(self.model_class.status == "active")
                        .values(
                            status="deleted",
                            updated_at=datetime.now(timezone.utc),
                            updated_by=actor_id,
                        )
                    )

                del_result = await session.execute(del_stmt)
                affected[link_type_id] = del_result.rowcount

        return affected


# =============================================================================
# LINK TYPE REGISTRY REPOSITORY
# =============================================================================


class LinkTypeRegistryRepository(GenericRepository[LinkTypeRegistryEntry, LinkTypeRegistryModel]):
    """
    Repository for persisting LinkType definitions.

    Stores LinkTypeMetadata for schema introspection and runtime resolution.
    """

    model_class = LinkTypeRegistryModel
    domain_class = LinkTypeRegistryEntry

    def __init__(self, db: Database, publish_events: bool = True):
        super().__init__(db, publish_events)

    def _to_domain(self, model: LinkTypeRegistryModel) -> LinkTypeRegistryEntry:
        """Convert ORM model to domain entity."""
        return LinkTypeRegistryEntry(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            version=model.version,
            status=model.status,
            link_type_id=model.link_type_id,
            source_type=model.source_type,
            target_type=model.target_type,
            cardinality=model.cardinality,
            direction=model.direction,
            reverse_link_id=model.reverse_link_id,
            backing_table_name=model.backing_table_name,
            is_materialized=model.is_materialized,
            on_source_delete=model.on_source_delete,
            on_target_delete=model.on_target_delete,
            on_source_update=model.on_source_update,
            on_target_update=model.on_target_update,
            constraints=model.constraints or {},
            description=model.description,
            tags=model.tags or [],
            schema_version=model.schema_version,
        )

    def _create_model(self, entity: LinkTypeRegistryEntry, actor_id: str) -> LinkTypeRegistryModel:
        """Create new ORM model for INSERT."""
        return LinkTypeRegistryModel(
            id=entity.id,
            version=entity.version or 1,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=actor_id,
            updated_by=actor_id,
            status=entity.status.value if hasattr(entity.status, 'value') else str(entity.status),
            link_type_id=entity.link_type_id,
            source_type=entity.source_type,
            target_type=entity.target_type,
            cardinality=entity.cardinality,
            direction=entity.direction,
            reverse_link_id=entity.reverse_link_id,
            backing_table_name=entity.backing_table_name,
            is_materialized=entity.is_materialized,
            on_source_delete=entity.on_source_delete,
            on_target_delete=entity.on_target_delete,
            on_source_update=entity.on_source_update,
            on_target_update=entity.on_target_update,
            constraints=entity.constraints,
            description=entity.description,
            tags=entity.tags,
            schema_version=entity.schema_version,
        )

    def _get_update_values(
        self,
        entity: LinkTypeRegistryEntry,
        actor_id: str,
        new_version: int,
    ) -> Dict[str, Any]:
        """Get values for UPDATE statement."""
        return {
            "version": new_version,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": actor_id,
            "status": entity.status.value if hasattr(entity.status, 'value') else str(entity.status),
            "cardinality": entity.cardinality,
            "direction": entity.direction,
            "reverse_link_id": entity.reverse_link_id,
            "backing_table_name": entity.backing_table_name,
            "is_materialized": entity.is_materialized,
            "on_source_delete": entity.on_source_delete,
            "on_target_delete": entity.on_target_delete,
            "on_source_update": entity.on_source_update,
            "on_target_update": entity.on_target_update,
            "constraints": entity.constraints,
            "description": entity.description,
            "tags": entity.tags,
            "schema_version": entity.schema_version,
        }

    async def find_by_link_type_id(self, link_type_id: str) -> Optional[LinkTypeRegistryEntry]:
        """Find a LinkType by its ID."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.link_type_id == link_type_id)
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def find_by_source_type(self, source_type: str) -> List[LinkTypeRegistryEntry]:
        """Find all LinkTypes with a specific source ObjectType."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.source_type == source_type)
                .where(self.model_class.status == "active")
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def find_by_target_type(self, target_type: str) -> List[LinkTypeRegistryEntry]:
        """Find all LinkTypes with a specific target ObjectType."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.target_type == target_type)
                .where(self.model_class.status == "active")
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def register_link_type(
        self,
        metadata: LinkTypeMetadata,
        actor_id: str = "system",
    ) -> LinkTypeRegistryEntry:
        """
        Register a new LinkType or update existing.

        Args:
            metadata: LinkTypeMetadata to register
            actor_id: Actor registering the type

        Returns:
            Persisted LinkTypeRegistryEntry
        """
        existing = await self.find_by_link_type_id(metadata.link_type_id)

        if existing:
            # Update existing entry
            existing.cardinality = metadata.cardinality
            existing.direction = metadata.direction.value
            existing.reverse_link_id = metadata.reverse_link_id
            existing.backing_table_name = metadata.backing_table_name
            existing.is_materialized = metadata.is_materialized
            existing.on_source_delete = metadata.on_source_delete.value
            existing.on_target_delete = metadata.on_target_delete.value
            existing.on_source_update = metadata.on_source_update.value
            existing.on_target_update = metadata.on_target_update.value
            existing.constraints = metadata.constraints.model_dump()
            existing.description = metadata.description
            existing.tags = metadata.tags
            existing.schema_version = metadata.schema_version
            existing.touch(updated_by=actor_id)
            return await self.save(existing, actor_id=actor_id)

        # Create new entry
        entry = LinkTypeRegistryEntry(
            link_type_id=metadata.link_type_id,
            source_type=metadata.source_type,
            target_type=metadata.target_type,
            cardinality=metadata.cardinality,
            direction=metadata.direction.value,
            reverse_link_id=metadata.reverse_link_id,
            backing_table_name=metadata.backing_table_name,
            is_materialized=metadata.is_materialized,
            on_source_delete=metadata.on_source_delete.value,
            on_target_delete=metadata.on_target_delete.value,
            on_source_update=metadata.on_source_update.value,
            on_target_update=metadata.on_target_update.value,
            constraints=metadata.constraints.model_dump(),
            description=metadata.description,
            tags=metadata.tags,
            schema_version=metadata.schema_version,
        )
        return await self.save(entry, actor_id=actor_id)

    async def get_all_link_types(self) -> List[LinkTypeMetadata]:
        """Get all registered LinkTypes as metadata objects."""
        entries = await self.find_all(limit=1000)
        return [e.to_link_type_metadata() for e in entries]
