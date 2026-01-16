"""
Orion ODA V4.0 - Link Migration Utilities
==========================================
Utilities for migrating link tables and link data between schema versions.

Palantir Pattern:
- Schema migrations are versioned and idempotent
- Link data migrations preserve referential integrity
- Rollback support for failed migrations
- Dry-run mode for validation without changes

This module provides:
- LinkMigration: Main migration orchestrator
- MigrationAction: Enum of migration action types
- LinkMigrationResult: Result of migration operations

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.link_tables import (
    JoinTableFactory,
    JoinTableRegistry,
)
from lib.oda.ontology.types.link_types import (
    CascadePolicy,
    LinkTypeMetadata,
)

logger = logging.getLogger(__name__)


class MigrationAction(Enum):
    """Types of migration actions."""
    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    MIGRATE_DATA = "migrate_data"
    VALIDATE_INTEGRITY = "validate_integrity"
    BACKUP_DATA = "backup_data"
    RESTORE_DATA = "restore_data"


@dataclass
class MigrationStep:
    """A single migration step."""
    action: MigrationAction
    table_name: str
    details: Dict[str, Any] = field(default_factory=dict)
    sql: Optional[str] = None
    executed: bool = False
    success: bool = False
    error: Optional[str] = None
    affected_rows: int = 0


@dataclass
class LinkMigrationResult:
    """Result of a link migration operation."""
    success: bool
    migration_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[MigrationStep] = field(default_factory=list)
    tables_created: List[str] = field(default_factory=list)
    tables_dropped: List[str] = field(default_factory=list)
    data_migrated: Dict[str, int] = field(default_factory=dict)
    integrity_violations: List[Dict[str, Any]] = field(default_factory=list)
    rollback_performed: bool = False
    error: Optional[str] = None

    def add_step(self, step: MigrationStep) -> None:
        """Add a step to the migration result."""
        self.steps.append(step)

    @property
    def total_affected_rows(self) -> int:
        """Total rows affected across all steps."""
        return sum(s.affected_rows for s in self.steps)


class LinkMigration:
    """
    Orchestrates link table migrations.

    Provides utilities for:
    - Creating link tables from LinkTypeMetadata
    - Migrating data between schema versions
    - Validating referential integrity
    - Rollback on failure

    Example:
        ```python
        migration = LinkMigration(db)

        # Create all link tables
        result = await migration.create_link_tables(link_types)

        # Migrate data with validation
        result = await migration.migrate_links(
            source_table="old_links",
            target_table="links",
            validate=True,
        )

        # Validate integrity
        violations = await migration.validate_integrity(link_types)
        ```
    """

    def __init__(self, db: Database):
        """
        Initialize migration utilities.

        Args:
            db: Database instance
        """
        self.db = db
        self.factory = JoinTableFactory()
        self._backup_tables: Dict[str, str] = {}

    async def create_link_tables(
        self,
        link_types: List[LinkTypeMetadata],
        dry_run: bool = False,
    ) -> LinkMigrationResult:
        """
        Create all required link tables.

        Args:
            link_types: List of LinkTypeMetadata definitions
            dry_run: If True, validate without creating tables

        Returns:
            LinkMigrationResult with created tables
        """
        import uuid
        migration_id = f"create-{uuid.uuid4().hex[:8]}"
        result = LinkMigrationResult(
            success=False,
            migration_id=migration_id,
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Filter to N:N links that need join tables
            nn_links = [lt for lt in link_types if lt.is_many_to_many]

            for link_type in nn_links:
                step = MigrationStep(
                    action=MigrationAction.CREATE_TABLE,
                    table_name=link_type.backing_table_name,
                    details={
                        "link_type_id": link_type.link_type_id,
                        "source_type": link_type.source_type,
                        "target_type": link_type.target_type,
                    },
                )

                if dry_run:
                    step.executed = False
                    step.success = True
                    logger.info(f"[DRY-RUN] Would create table: {link_type.backing_table_name}")
                else:
                    try:
                        table = self.factory.create_join_table(link_type)
                        async with self.db.engine.begin() as conn:
                            await conn.run_sync(
                                lambda sync_conn: table.create(sync_conn, checkfirst=True)
                            )
                        step.executed = True
                        step.success = True
                        result.tables_created.append(link_type.backing_table_name)
                        logger.info(f"Created table: {link_type.backing_table_name}")
                    except Exception as e:
                        step.executed = True
                        step.success = False
                        step.error = str(e)
                        logger.error(f"Failed to create table {link_type.backing_table_name}: {e}")

                result.add_step(step)

            # Also ensure main links table exists
            await self._ensure_links_table()

            result.success = all(s.success for s in result.steps)
            result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            result.success = False
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)
            logger.error(f"Migration failed: {e}")

        return result

    async def _ensure_links_table(self) -> None:
        """Ensure the main links table exists."""
        async with self.db.engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS links (
                    id VARCHAR PRIMARY KEY,
                    link_type_id VARCHAR(100) NOT NULL,
                    source_type VARCHAR(100) NOT NULL,
                    source_id VARCHAR NOT NULL,
                    target_type VARCHAR(100) NOT NULL,
                    target_id VARCHAR NOT NULL,
                    metadata JSON DEFAULT '{}',
                    linked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    linked_by VARCHAR,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'active'
                )
            """))
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_links_source ON links(link_type_id, source_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_links_target ON links(link_type_id, target_id)
            """))
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_links_unique
                ON links(link_type_id, source_id, target_id)
            """))

    async def migrate_links(
        self,
        source_table: str,
        target_table: str,
        column_mapping: Optional[Dict[str, str]] = None,
        transform: Optional[callable] = None,
        validate: bool = True,
        batch_size: int = 1000,
    ) -> LinkMigrationResult:
        """
        Migrate link data from source to target table.

        Args:
            source_table: Source table name
            target_table: Target table name
            column_mapping: Optional column name mapping
            transform: Optional row transformation function
            validate: Validate integrity after migration
            batch_size: Rows per batch

        Returns:
            LinkMigrationResult with migration details
        """
        import uuid
        migration_id = f"migrate-{uuid.uuid4().hex[:8]}"
        result = LinkMigrationResult(
            success=False,
            migration_id=migration_id,
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Backup source data
            backup_step = await self._backup_table(source_table)
            result.add_step(backup_step)

            if not backup_step.success:
                raise Exception(f"Backup failed: {backup_step.error}")

            # Migrate data in batches
            total_migrated = 0
            offset = 0

            async with self.db.transaction() as session:
                while True:
                    # Fetch batch from source
                    fetch_sql = f"SELECT * FROM {source_table} LIMIT {batch_size} OFFSET {offset}"
                    rows = await session.execute(text(fetch_sql))
                    batch = rows.fetchall()

                    if not batch:
                        break

                    # Transform and insert
                    for row in batch:
                        row_dict = dict(row._mapping)

                        # Apply column mapping
                        if column_mapping:
                            row_dict = {
                                column_mapping.get(k, k): v
                                for k, v in row_dict.items()
                            }

                        # Apply transformation
                        if transform:
                            row_dict = transform(row_dict)

                        # Build insert
                        columns = ", ".join(row_dict.keys())
                        placeholders = ", ".join(f":{k}" for k in row_dict.keys())
                        insert_sql = f"INSERT INTO {target_table} ({columns}) VALUES ({placeholders})"

                        await session.execute(text(insert_sql), row_dict)
                        total_migrated += 1

                    offset += batch_size

            migrate_step = MigrationStep(
                action=MigrationAction.MIGRATE_DATA,
                table_name=target_table,
                details={
                    "source_table": source_table,
                    "column_mapping": column_mapping,
                },
                executed=True,
                success=True,
                affected_rows=total_migrated,
            )
            result.add_step(migrate_step)
            result.data_migrated[target_table] = total_migrated

            # Validate if requested
            if validate:
                violations = await self._validate_migrated_data(target_table)
                if violations:
                    result.integrity_violations = violations
                    result.success = False
                    # Rollback
                    await self._rollback_migration(source_table, target_table)
                    result.rollback_performed = True
                else:
                    result.success = True
            else:
                result.success = True

            result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            result.success = False
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)
            logger.error(f"Migration failed: {e}")

        return result

    async def _backup_table(self, table_name: str) -> MigrationStep:
        """Create a backup of a table."""
        backup_name = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        step = MigrationStep(
            action=MigrationAction.BACKUP_DATA,
            table_name=table_name,
            details={"backup_table": backup_name},
        )

        try:
            async with self.db.engine.begin() as conn:
                await conn.execute(text(
                    f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}"
                ))
            self._backup_tables[table_name] = backup_name
            step.executed = True
            step.success = True
            logger.info(f"Backed up {table_name} to {backup_name}")
        except Exception as e:
            step.executed = True
            step.success = False
            step.error = str(e)

        return step

    async def _validate_migrated_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Validate migrated data for integrity issues."""
        violations = []

        async with self.db.transaction() as session:
            # Check for null required fields
            null_check = await session.execute(text(f"""
                SELECT id, 'null_source_id' as violation
                FROM {table_name}
                WHERE source_id IS NULL
                UNION ALL
                SELECT id, 'null_target_id' as violation
                FROM {table_name}
                WHERE target_id IS NULL
            """))

            for row in null_check.fetchall():
                violations.append({
                    "link_id": row[0],
                    "violation_type": row[1],
                    "table": table_name,
                })

            # Check for duplicate links
            dup_check = await session.execute(text(f"""
                SELECT link_type_id, source_id, target_id, COUNT(*) as cnt
                FROM {table_name}
                GROUP BY link_type_id, source_id, target_id
                HAVING COUNT(*) > 1
            """))

            for row in dup_check.fetchall():
                violations.append({
                    "link_type_id": row[0],
                    "source_id": row[1],
                    "target_id": row[2],
                    "violation_type": "duplicate_link",
                    "count": row[3],
                    "table": table_name,
                })

        return violations

    async def _rollback_migration(self, source_table: str, target_table: str) -> None:
        """Rollback a failed migration."""
        backup_name = self._backup_tables.get(source_table)
        if backup_name:
            async with self.db.engine.begin() as conn:
                await conn.execute(text(f"DELETE FROM {target_table}"))
                await conn.execute(text(
                    f"INSERT INTO {target_table} SELECT * FROM {backup_name}"
                ))
            logger.info(f"Rolled back migration from {backup_name}")

    async def validate_integrity(
        self,
        link_types: List[LinkTypeMetadata],
        fix_violations: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Validate referential integrity for all link types.

        Args:
            link_types: Link types to validate
            fix_violations: If True, attempt to fix violations

        Returns:
            List of integrity violations
        """
        violations = []

        async with self.db.transaction() as session:
            for link_type in link_types:
                # Check orphaned source references
                orphan_source = await session.execute(text(f"""
                    SELECT l.id, l.source_id, l.source_type
                    FROM links l
                    WHERE l.link_type_id = :link_type_id
                    AND l.status = 'active'
                    AND NOT EXISTS (
                        SELECT 1 FROM objects o
                        WHERE o.id = l.source_id
                        AND o.object_type = l.source_type
                        AND o.status = 'active'
                    )
                """), {"link_type_id": link_type.link_type_id})

                for row in orphan_source.fetchall():
                    violation = {
                        "link_id": row[0],
                        "link_type_id": link_type.link_type_id,
                        "violation_type": "orphaned_source",
                        "source_id": row[1],
                        "source_type": row[2],
                    }
                    violations.append(violation)

                    if fix_violations:
                        await self._fix_orphan(session, row[0], link_type)

                # Check orphaned target references
                orphan_target = await session.execute(text(f"""
                    SELECT l.id, l.target_id, l.target_type
                    FROM links l
                    WHERE l.link_type_id = :link_type_id
                    AND l.status = 'active'
                    AND NOT EXISTS (
                        SELECT 1 FROM objects o
                        WHERE o.id = l.target_id
                        AND o.object_type = l.target_type
                        AND o.status = 'active'
                    )
                """), {"link_type_id": link_type.link_type_id})

                for row in orphan_target.fetchall():
                    violation = {
                        "link_id": row[0],
                        "link_type_id": link_type.link_type_id,
                        "violation_type": "orphaned_target",
                        "target_id": row[1],
                        "target_type": row[2],
                    }
                    violations.append(violation)

                    if fix_violations:
                        await self._fix_orphan(session, row[0], link_type)

        logger.info(f"Found {len(violations)} integrity violations")
        return violations

    async def _fix_orphan(
        self,
        session: AsyncSession,
        link_id: str,
        link_type: LinkTypeMetadata,
    ) -> None:
        """Fix an orphaned link based on cascade policy."""
        cascade_policy = link_type.on_delete or CascadePolicy.RESTRICT

        if cascade_policy == CascadePolicy.CASCADE:
            # Delete the orphaned link
            await session.execute(text(
                "UPDATE links SET status = 'deleted' WHERE id = :link_id"
            ), {"link_id": link_id})
            logger.info(f"Deleted orphaned link {link_id}")

        elif cascade_policy == CascadePolicy.SET_NULL:
            # Cannot set null for required fields, log warning
            logger.warning(f"Cannot SET_NULL for link {link_id}, marking as deleted")
            await session.execute(text(
                "UPDATE links SET status = 'deleted' WHERE id = :link_id"
            ), {"link_id": link_id})

        else:
            # RESTRICT or NO_ACTION - just log
            logger.warning(f"Orphaned link {link_id} requires manual review")

    async def drop_link_tables(
        self,
        link_types: List[LinkTypeMetadata],
        dry_run: bool = False,
        backup_first: bool = True,
    ) -> LinkMigrationResult:
        """
        Drop link tables (with optional backup).

        Args:
            link_types: Link types whose tables to drop
            dry_run: If True, validate without dropping
            backup_first: Create backup before dropping

        Returns:
            LinkMigrationResult with dropped tables
        """
        import uuid
        migration_id = f"drop-{uuid.uuid4().hex[:8]}"
        result = LinkMigrationResult(
            success=False,
            migration_id=migration_id,
            started_at=datetime.now(timezone.utc),
        )

        try:
            nn_links = [lt for lt in link_types if lt.is_many_to_many]

            for link_type in nn_links:
                table_name = link_type.backing_table_name

                # Backup first if requested
                if backup_first and not dry_run:
                    backup_step = await self._backup_table(table_name)
                    result.add_step(backup_step)

                step = MigrationStep(
                    action=MigrationAction.DROP_TABLE,
                    table_name=table_name,
                    details={"link_type_id": link_type.link_type_id},
                )

                if dry_run:
                    step.executed = False
                    step.success = True
                    logger.info(f"[DRY-RUN] Would drop table: {table_name}")
                else:
                    try:
                        async with self.db.engine.begin() as conn:
                            await conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        step.executed = True
                        step.success = True
                        result.tables_dropped.append(table_name)
                        logger.info(f"Dropped table: {table_name}")
                    except Exception as e:
                        step.executed = True
                        step.success = False
                        step.error = str(e)

                result.add_step(step)

            result.success = all(s.success for s in result.steps)
            result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            result.success = False
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)

        return result

    async def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a link table.

        Args:
            table_name: Name of the table

        Returns:
            Table information or None if not exists
        """
        async with self.db.engine.begin() as conn:
            def sync_get_info(sync_conn):
                inspector = inspect(sync_conn)
                if table_name not in inspector.get_table_names():
                    return None

                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)
                pk = inspector.get_pk_constraint(table_name)

                return {
                    "name": table_name,
                    "columns": [
                        {
                            "name": c["name"],
                            "type": str(c["type"]),
                            "nullable": c["nullable"],
                        }
                        for c in columns
                    ],
                    "indexes": [
                        {
                            "name": i["name"],
                            "columns": i["column_names"],
                            "unique": i.get("unique", False),
                        }
                        for i in indexes
                    ],
                    "primary_key": pk.get("constrained_columns", []),
                }

            return await conn.run_sync(sync_get_info)

    async def list_link_tables(self) -> List[str]:
        """List all link-related tables in the database."""
        async with self.db.engine.begin() as conn:
            def sync_list_tables(sync_conn):
                inspector = inspect(sync_conn)
                all_tables = inspector.get_table_names()
                # Filter to link-related tables
                return [
                    t for t in all_tables
                    if t == "links" or t.startswith("link_") or t.endswith("_links")
                ]

            return await conn.run_sync(sync_list_tables)
