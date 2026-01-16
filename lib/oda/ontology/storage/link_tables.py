"""
Orion ODA V4.0 - M:N Join Table Generator
==========================================
Dynamic SQLAlchemy table generation for Many-to-Many link relationships.

Palantir Pattern:
- N:N links require explicit backing table (join table)
- Each join table has source_id, target_id, and metadata columns
- Tables are created dynamically based on LinkTypeMetadata

This module provides:
- JoinTableFactory: Creates SQLAlchemy Table objects dynamically
- JoinTableRegistry: Manages created join tables
- JoinTableOperations: CRUD operations for join tables

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Type

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    delete,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.types.link_types import LinkTypeMetadata

logger = logging.getLogger(__name__)


# =============================================================================
# JOIN TABLE FACTORY
# =============================================================================


class JoinTableFactory:
    """
    Factory for creating SQLAlchemy Table objects for M:N relationships.

    Palantir Pattern:
    - Join table name comes from LinkTypeMetadata.backing_table_name
    - Standard columns: id, source_id, target_id, link_type_id
    - Optional metadata column for link attributes
    - Audit columns: created_at, created_by, status

    Example:
        ```python
        factory = JoinTableFactory(metadata)
        table = factory.create_join_table(
            link_type=LinkTypeMetadata(
                link_type_id="task_depends_on_task",
                source_type="Task",
                target_type="Task",
                cardinality="N:N",
                backing_table_name="task_dependencies",
            )
        )
        ```
    """

    def __init__(self, metadata: Optional[MetaData] = None):
        """
        Initialize the factory.

        Args:
            metadata: SQLAlchemy MetaData instance (creates new if None)
        """
        self.metadata = metadata or MetaData()
        self._tables: Dict[str, Table] = {}

    def create_join_table(
        self,
        link_type: LinkTypeMetadata,
        source_id_column: str = "source_id",
        target_id_column: str = "target_id",
        include_metadata: bool = True,
        include_audit: bool = True,
    ) -> Table:
        """
        Create a join table for an N:N LinkType.

        Args:
            link_type: LinkTypeMetadata with N:N cardinality
            source_id_column: Name of source ID column
            target_id_column: Name of target ID column
            include_metadata: Include JSON metadata column
            include_audit: Include audit columns (created_at, created_by, status)

        Returns:
            SQLAlchemy Table object

        Raises:
            ValueError: If link_type is not N:N or missing backing_table_name
        """
        if not link_type.is_many_to_many:
            raise ValueError(
                f"JoinTableFactory only supports N:N links. "
                f"Got cardinality: {link_type.cardinality}"
            )

        if not link_type.backing_table_name:
            raise ValueError(
                f"N:N LinkType '{link_type.link_type_id}' requires backing_table_name"
            )

        table_name = link_type.backing_table_name

        # Return cached table if exists
        if table_name in self._tables:
            return self._tables[table_name]

        # Build columns
        columns = [
            # Primary key
            Column("id", String, primary_key=True),

            # Link type reference
            Column("link_type_id", String(100), nullable=False, index=True),

            # Source reference
            Column(source_id_column, String, nullable=False, index=True),
            Column("source_type", String(100), nullable=False),

            # Target reference
            Column(target_id_column, String, nullable=False, index=True),
            Column("target_type", String(100), nullable=False),

            # Optimistic locking
            Column("version", Integer, default=1, nullable=False),
        ]

        # Optional metadata column
        if include_metadata:
            columns.append(Column("metadata", JSON, default=dict))

        # Audit columns
        if include_audit:
            columns.extend([
                Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
                Column("updated_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)),
                Column("created_by", String, nullable=True),
                Column("updated_by", String, nullable=True),
                Column("status", String(20), default="active", nullable=False),
            ])

        # Create table with constraints
        table = Table(
            table_name,
            self.metadata,
            *columns,
            # Unique constraint on link
            UniqueConstraint(
                source_id_column,
                target_id_column,
                name=f"uq_{table_name}_source_target"
            ),
            # Indexes
            Index(f"idx_{table_name}_source", source_id_column),
            Index(f"idx_{table_name}_target", target_id_column),
            Index(f"idx_{table_name}_link_type", "link_type_id"),
        )

        self._tables[table_name] = table
        logger.info(f"Created join table: {table_name}")
        return table

    def get_table(self, table_name: str) -> Optional[Table]:
        """Get a previously created table by name."""
        return self._tables.get(table_name)

    def list_tables(self) -> List[str]:
        """List all created table names."""
        return list(self._tables.keys())


# =============================================================================
# JOIN TABLE REGISTRY
# =============================================================================


class JoinTableRegistry:
    """
    Registry for managing join tables across the application.

    Provides centralized management of join tables including:
    - Table creation from LinkTypeMetadata
    - Schema synchronization with database
    - Table discovery and introspection
    """

    _instance: Optional["JoinTableRegistry"] = None

    def __init__(self, db: Database):
        """
        Initialize the registry.

        Args:
            db: Database instance for schema operations
        """
        self.db = db
        self.factory = JoinTableFactory()
        self._initialized_tables: Set[str] = set()

    @classmethod
    def get_instance(cls, db: Optional[Database] = None) -> "JoinTableRegistry":
        """Get singleton instance of the registry."""
        if cls._instance is None:
            if db is None:
                raise ValueError("Database required for first initialization")
            cls._instance = cls(db)
        return cls._instance

    async def register_link_type(
        self,
        link_type: LinkTypeMetadata,
        create_table: bool = True,
    ) -> Optional[Table]:
        """
        Register an N:N LinkType and optionally create its table.

        Args:
            link_type: LinkTypeMetadata to register
            create_table: Whether to create the table in the database

        Returns:
            Table object if N:N link, None otherwise
        """
        if not link_type.is_many_to_many:
            logger.debug(f"Skipping non-N:N link type: {link_type.link_type_id}")
            return None

        table = self.factory.create_join_table(link_type)

        if create_table and link_type.backing_table_name not in self._initialized_tables:
            await self._create_table_if_not_exists(table)
            self._initialized_tables.add(link_type.backing_table_name)

        return table

    async def _create_table_if_not_exists(self, table: Table) -> None:
        """Create table in database if it doesn't exist."""
        async with self.db.engine.begin() as conn:
            # Use checkfirst=True to avoid errors if table exists
            await conn.run_sync(
                lambda sync_conn: table.create(sync_conn, checkfirst=True)
            )
            logger.info(f"Ensured table exists: {table.name}")

    async def sync_all_tables(self, link_types: List[LinkTypeMetadata]) -> List[str]:
        """
        Synchronize all N:N link type tables.

        Args:
            link_types: List of LinkTypeMetadata to sync

        Returns:
            List of created/synced table names
        """
        synced = []
        for lt in link_types:
            if lt.is_many_to_many:
                await self.register_link_type(lt, create_table=True)
                synced.append(lt.backing_table_name)
        return synced

    def get_table(self, table_name: str) -> Optional[Table]:
        """Get a registered table by name."""
        return self.factory.get_table(table_name)


# =============================================================================
# JOIN TABLE OPERATIONS
# =============================================================================


class JoinTableOperations:
    """
    CRUD operations for dynamically created join tables.

    Provides type-safe operations without requiring ORM models.

    Example:
        ```python
        ops = JoinTableOperations(db, registry)

        # Add a link
        await ops.add_link(
            table_name="task_dependencies",
            link_type_id="task_depends_on_task",
            source_id="task-1",
            source_type="Task",
            target_id="task-2",
            target_type="Task",
            actor_id="system",
        )

        # Query links
        links = await ops.find_by_source(
            table_name="task_dependencies",
            source_id="task-1",
        )
        ```
    """

    def __init__(self, db: Database, registry: JoinTableRegistry):
        """
        Initialize operations.

        Args:
            db: Database instance
            registry: JoinTableRegistry instance
        """
        self.db = db
        self.registry = registry

    async def add_link(
        self,
        table_name: str,
        link_type_id: str,
        source_id: str,
        source_type: str,
        target_id: str,
        target_type: str,
        actor_id: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a new link to a join table.

        Args:
            table_name: Name of the join table
            link_type_id: LinkType ID
            source_id: Source object ID
            source_type: Source ObjectType
            target_id: Target object ID
            target_type: Target ObjectType
            actor_id: Actor creating the link
            metadata: Optional link metadata

        Returns:
            ID of the created link row

        Raises:
            ValueError: If table not found
        """
        import uuid

        table = self.registry.get_table(table_name)
        if table is None:
            raise ValueError(f"Join table not found: {table_name}")

        link_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        values = {
            "id": link_id,
            "link_type_id": link_type_id,
            "source_id": source_id,
            "source_type": source_type,
            "target_id": target_id,
            "target_type": target_type,
            "version": 1,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
            "created_by": actor_id,
            "updated_by": actor_id,
            "status": "active",
        }

        async with self.db.transaction() as session:
            await session.execute(insert(table).values(**values))

        logger.debug(f"Added link to {table_name}: {source_id} -> {target_id}")
        return link_id

    async def remove_link(
        self,
        table_name: str,
        source_id: str,
        target_id: str,
        actor_id: str = "system",
        hard_delete: bool = False,
    ) -> bool:
        """
        Remove a link from a join table.

        Args:
            table_name: Name of the join table
            source_id: Source object ID
            target_id: Target object ID
            actor_id: Actor removing the link
            hard_delete: If True, permanently delete; otherwise soft delete

        Returns:
            True if link was removed, False if not found
        """
        table = self.registry.get_table(table_name)
        if table is None:
            raise ValueError(f"Join table not found: {table_name}")

        async with self.db.transaction() as session:
            if hard_delete:
                stmt = (
                    delete(table)
                    .where(table.c.source_id == source_id)
                    .where(table.c.target_id == target_id)
                )
            else:
                stmt = (
                    update(table)
                    .where(table.c.source_id == source_id)
                    .where(table.c.target_id == target_id)
                    .where(table.c.status == "active")
                    .values(
                        status="deleted",
                        updated_at=datetime.now(timezone.utc),
                        updated_by=actor_id,
                    )
                )

            result = await session.execute(stmt)
            return result.rowcount > 0

    async def find_by_source(
        self,
        table_name: str,
        source_id: str,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Find all links from a source.

        Args:
            table_name: Name of the join table
            source_id: Source object ID
            include_deleted: Include soft-deleted links

        Returns:
            List of link rows as dicts
        """
        table = self.registry.get_table(table_name)
        if table is None:
            raise ValueError(f"Join table not found: {table_name}")

        async with self.db.transaction() as session:
            stmt = select(table).where(table.c.source_id == source_id)
            if not include_deleted:
                stmt = stmt.where(table.c.status == "active")

            result = await session.execute(stmt)
            return [dict(row._mapping) for row in result.all()]

    async def find_by_target(
        self,
        table_name: str,
        target_id: str,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Find all links to a target.

        Args:
            table_name: Name of the join table
            target_id: Target object ID
            include_deleted: Include soft-deleted links

        Returns:
            List of link rows as dicts
        """
        table = self.registry.get_table(table_name)
        if table is None:
            raise ValueError(f"Join table not found: {table_name}")

        async with self.db.transaction() as session:
            stmt = select(table).where(table.c.target_id == target_id)
            if not include_deleted:
                stmt = stmt.where(table.c.status == "active")

            result = await session.execute(stmt)
            return [dict(row._mapping) for row in result.all()]

    async def link_exists(
        self,
        table_name: str,
        source_id: str,
        target_id: str,
    ) -> bool:
        """Check if a link exists between source and target."""
        table = self.registry.get_table(table_name)
        if table is None:
            raise ValueError(f"Join table not found: {table_name}")

        async with self.db.transaction() as session:
            stmt = (
                select(table.c.id)
                .where(table.c.source_id == source_id)
                .where(table.c.target_id == target_id)
                .where(table.c.status == "active")
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def count_links_from_source(
        self,
        table_name: str,
        source_id: str,
    ) -> int:
        """Count active links from a source."""
        table = self.registry.get_table(table_name)
        if table is None:
            raise ValueError(f"Join table not found: {table_name}")

        async with self.db.transaction() as session:
            from sqlalchemy import func
            stmt = (
                select(func.count())
                .select_from(table)
                .where(table.c.source_id == source_id)
                .where(table.c.status == "active")
            )
            result = await session.execute(stmt)
            return result.scalar_one()

    async def get_target_ids(
        self,
        table_name: str,
        source_id: str,
    ) -> Set[str]:
        """Get set of target IDs linked from a source."""
        table = self.registry.get_table(table_name)
        if table is None:
            raise ValueError(f"Join table not found: {table_name}")

        async with self.db.transaction() as session:
            stmt = (
                select(table.c.target_id)
                .where(table.c.source_id == source_id)
                .where(table.c.status == "active")
            )
            result = await session.execute(stmt)
            return {row[0] for row in result.all()}
