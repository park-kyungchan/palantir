#!/usr/bin/env python3
"""
Orion ODA V3 - Persistence Migration Script
=============================================
Migrates data from legacy 'objects' table (JSON Column pattern)
to typed tables (ORM Repository pattern).

This implements the Strangler Fig pattern:
1. Read from legacy table
2. Transform to domain objects
3. Write to new typed tables
4. Verify migration integrity
5. (Optional) Delete from legacy after validation

Usage:
    # Dry run (no writes)
    python -m scripts.maintenance.migrate_v2_persistence --dry-run

    # Full migration
    python -m scripts.maintenance.migrate_v2_persistence

    # With verification
    python -m scripts.maintenance.migrate_v2_persistence --verify

    # Clean up legacy after verification
    python -m scripts.maintenance.migrate_v2_persistence --cleanup
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import select, delete, text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.ontology.db import objects_table, SessionLocal
from scripts.ontology.storage.database import Database, initialize_database
from scripts.ontology.storage.models import (
    Base,
    OrionActionLogModel,
    JobResultModel,
    OrionInsightModel,
    OrionPatternModel,
)
from scripts.ontology.schemas.governance import OrionActionLog
from scripts.ontology.schemas.result import JobResult, Artifact
from scripts.ontology.schemas.memory import (
    OrionInsight,
    OrionPattern,
    InsightContent,
    InsightProvenance,
    PatternStructure,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("migration")


# =============================================================================
# MIGRATION STATS
# =============================================================================

@dataclass
class MigrationStats:
    """Tracks migration progress and results."""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Counts by type
    action_logs: int = 0
    job_results: int = 0
    insights: int = 0
    patterns: int = 0
    skipped: int = 0
    errors: int = 0

    # Error details
    error_details: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def total_migrated(self) -> int:
        return self.action_logs + self.job_results + self.insights + self.patterns

    @property
    def duration_seconds(self) -> float:
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "action_logs": self.action_logs,
            "job_results": self.job_results,
            "insights": self.insights,
            "patterns": self.patterns,
            "total_migrated": self.total_migrated,
            "skipped": self.skipped,
            "errors": self.errors,
        }


# =============================================================================
# TYPE HANDLERS
# =============================================================================

class TypeHandler:
    """Base class for type-specific migration logic."""

    type_name: str
    model_class: Type

    @classmethod
    def can_handle(cls, type_name: str) -> bool:
        return type_name == cls.type_name

    @classmethod
    def transform(cls, row_id: str, row_data: Dict[str, Any], common: Dict[str, Any]) -> Any:
        """Transform row data to ORM model. Override in subclass."""
        raise NotImplementedError


class ActionLogHandler(TypeHandler):
    type_name = "OrionActionLog"
    model_class = OrionActionLogModel

    @classmethod
    def transform(cls, row_id: str, row_data: Dict[str, Any], common: Dict[str, Any]) -> OrionActionLogModel:
        return OrionActionLogModel(
            **common,
            agent_id=row_data.get("agent_id", "Orion-Kernel"),
            trace_id=row_data.get("trace_id"),
            action_type=row_data.get("action_type", "unknown"),
            parameters=row_data.get("parameters", {}),
            error=row_data.get("error"),
            affected_ids=row_data.get("affected_ids", []),
            duration_ms=row_data.get("duration_ms", 0),
            fts_content=f"{row_data.get('action_type', '')} {row_data.get('status', '')} {row_data.get('error', '')}",
        )


class JobResultHandler(TypeHandler):
    type_name = "JobResult"
    model_class = JobResultModel

    @classmethod
    def transform(cls, row_id: str, row_data: Dict[str, Any], common: Dict[str, Any]) -> JobResultModel:
        return JobResultModel(
            **common,
            job_id=row_data.get("job_id", row_id),
            output_artifacts=row_data.get("output_artifacts", []),
            metrics=row_data.get("metrics", {}),
            fts_content=f"{row_data.get('job_id', '')} {row_data.get('status', '')}",
        )


class InsightHandler(TypeHandler):
    type_name = "OrionInsight"
    model_class = OrionInsightModel

    @classmethod
    def transform(cls, row_id: str, row_data: Dict[str, Any], common: Dict[str, Any]) -> OrionInsightModel:
        # Handle nested content structure
        content = row_data.get("content", {})
        provenance = row_data.get("provenance", {})

        return OrionInsightModel(
            **common,
            summary=content.get("summary", ""),
            domain=content.get("domain", "unknown"),
            tags=content.get("tags", []),
            confidence_score=row_data.get("confidence_score", 1.0),
            decay_factor=row_data.get("decay_factor"),
            source_episodic_ids=provenance.get("source_episodic_ids", []),
            provenance_method=provenance.get("method", "unknown"),
            supports=row_data.get("supports", []),
            contradicts=row_data.get("contradicts", []),
            related_to=row_data.get("related_to", []),
            fts_content=f"{content.get('summary', '')} {content.get('domain', '')} {' '.join(content.get('tags', []))}",
        )


class PatternHandler(TypeHandler):
    type_name = "OrionPattern"
    model_class = OrionPatternModel

    @classmethod
    def transform(cls, row_id: str, row_data: Dict[str, Any], common: Dict[str, Any]) -> OrionPatternModel:
        # Handle nested structure
        structure = row_data.get("structure", {})
        last_used_str = row_data.get("last_used")
        last_used = None
        if last_used_str:
            try:
                last_used = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return OrionPatternModel(
            **common,
            trigger=structure.get("trigger", ""),
            steps=structure.get("steps", []),
            anti_patterns=structure.get("anti_patterns", []),
            frequency_count=row_data.get("frequency_count", 0),
            success_rate=row_data.get("success_rate", 0.0),
            last_used=last_used,
            code_snippet_ref=row_data.get("code_snippet_ref"),
            fts_content=f"{structure.get('trigger', '')} {' '.join(structure.get('steps', []))}",
        )


# Registry of handlers
HANDLERS = [ActionLogHandler, JobResultHandler, InsightHandler, PatternHandler]


def get_handler(type_name: str) -> Optional[Type[TypeHandler]]:
    """Get handler for a given type name."""
    for handler in HANDLERS:
        if handler.can_handle(type_name):
            return handler
    return None


# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

async def migrate_objects_to_typed_tables(
    legacy_db_path: str,
    target_db: Database,
    dry_run: bool = False,
    batch_size: int = 100
) -> MigrationStats:
    """
    Migrate data from legacy 'objects' table to typed tables.

    Args:
        legacy_db_path: Path to legacy SQLite database
        target_db: Async Database instance for new tables
        dry_run: If True, don't actually write data
        batch_size: Number of records to process per batch

    Returns:
        MigrationStats with counts and any errors
    """
    stats = MigrationStats()
    logger.info(f"Starting migration from {legacy_db_path}")
    logger.info(f"Dry run: {dry_run}, Batch size: {batch_size}")

    # Use synchronous session for legacy table
    legacy_session = SessionLocal()

    try:
        # Fetch all rows from legacy table
        result = legacy_session.execute(select(objects_table))
        rows = result.fetchall()
        total_rows = len(rows)
        logger.info(f"Found {total_rows} rows to migrate")

        if total_rows == 0:
            logger.info("No data to migrate")
            stats.completed_at = datetime.now(timezone.utc)
            return stats

        # Process in batches
        batch = []
        for idx, row in enumerate(rows):
            try:
                # Parse row data
                row_id = row.id
                row_type = row.type
                row_version = row.version or 1
                row_data = row.data if isinstance(row.data, dict) else json.loads(row.data or "{}")
                fts_content = row.fts_content or ""

                # Common fields for all models
                common = {
                    "id": row_id,
                    "version": row_version,
                    "created_at": row.created_at or datetime.now(timezone.utc),
                    "updated_at": row.updated_at or datetime.now(timezone.utc),
                    "created_by": row_data.get("created_by"),
                    "updated_by": row_data.get("updated_by"),
                    "status": row_data.get("status", "active"),
                }

                # Get handler for this type
                handler = get_handler(row_type)
                if handler is None:
                    logger.debug(f"No handler for type '{row_type}', skipping row {row_id}")
                    stats.skipped += 1
                    continue

                # Transform to ORM model
                model = handler.transform(row_id, row_data, common)
                batch.append((handler.type_name, model))

                # Update stats
                if handler.type_name == "OrionActionLog":
                    stats.action_logs += 1
                elif handler.type_name == "JobResult":
                    stats.job_results += 1
                elif handler.type_name == "OrionInsight":
                    stats.insights += 1
                elif handler.type_name == "OrionPattern":
                    stats.patterns += 1

                # Flush batch if full
                if len(batch) >= batch_size:
                    if not dry_run:
                        await _flush_batch(target_db, batch)
                    logger.info(f"Processed {idx + 1}/{total_rows} rows")
                    batch = []

            except Exception as e:
                logger.error(f"Error processing row {row.id} ({row.type}): {e}")
                stats.errors += 1
                stats.error_details.append({
                    "row_id": row.id,
                    "type": row.type,
                    "error": str(e),
                })
                continue

        # Flush remaining batch
        if batch and not dry_run:
            await _flush_batch(target_db, batch)

    finally:
        legacy_session.close()

    stats.completed_at = datetime.now(timezone.utc)
    logger.info(f"Migration completed: {stats.to_dict()}")
    return stats


async def _flush_batch(db: Database, batch: List[tuple]) -> None:
    """Write a batch of models to the database."""
    async with db.transaction() as session:
        for type_name, model in batch:
            # Check if already exists (for idempotency)
            existing = await session.execute(
                select(model.__class__).where(model.__class__.id == model.id)
            )
            if existing.scalar_one_or_none() is None:
                session.add(model)
            else:
                logger.debug(f"Skipping duplicate: {type_name} {model.id}")


async def verify_migration(
    legacy_db_path: str,
    target_db: Database
) -> Dict[str, Any]:
    """
    Verify migration by comparing counts between legacy and new tables.

    Returns:
        Verification report with counts and discrepancies
    """
    logger.info("Starting migration verification...")

    # Count legacy records by type
    legacy_session = SessionLocal()
    try:
        result = legacy_session.execute(
            text("SELECT type, COUNT(*) FROM objects GROUP BY type")
        )
        legacy_counts = {row[0]: row[1] for row in result.fetchall()}
    finally:
        legacy_session.close()

    # Count new table records
    new_counts = {}
    async with target_db.transaction() as session:
        for handler in HANDLERS:
            result = await session.execute(
                select(text("COUNT(*)")).select_from(handler.model_class)
            )
            new_counts[handler.type_name] = result.scalar_one()

    # Compare
    report = {
        "legacy_counts": legacy_counts,
        "new_counts": new_counts,
        "discrepancies": {},
        "verified": True,
    }

    for type_name in legacy_counts:
        legacy = legacy_counts.get(type_name, 0)
        new = new_counts.get(type_name, 0)
        if legacy != new:
            report["discrepancies"][type_name] = {
                "legacy": legacy,
                "new": new,
                "difference": legacy - new,
            }
            report["verified"] = False

    if report["verified"]:
        logger.info("✓ Migration verification passed")
    else:
        logger.warning(f"✗ Migration verification failed: {report['discrepancies']}")

    return report


async def cleanup_legacy_table(legacy_db_path: str, migrated_types: List[str]) -> int:
    """
    Remove migrated records from legacy table.
    Only call after successful verification!

    Args:
        legacy_db_path: Path to legacy database
        migrated_types: List of type names that were migrated

    Returns:
        Number of records deleted
    """
    logger.warning("Cleaning up legacy table - this is irreversible!")

    legacy_session = SessionLocal()
    try:
        deleted = 0
        for type_name in migrated_types:
            result = legacy_session.execute(
                delete(objects_table).where(objects_table.c.type == type_name)
            )
            deleted += result.rowcount
        legacy_session.commit()
        logger.info(f"Deleted {deleted} records from legacy table")
        return deleted
    finally:
        legacy_session.close()


# =============================================================================
# CLI
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Migrate Orion data from JSON column to typed tables"
    )
    parser.add_argument(
        "--legacy-db",
        default="/home/palantir/.agent/orion_ontology.db",
        help="Path to legacy SQLite database"
    )
    parser.add_argument(
        "--target-db",
        default="/home/palantir/orion-orchestrator-v2/data/ontology.db",
        help="Path to target SQLite database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually write data, just report what would happen"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify migration after completion"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove migrated records from legacy table (requires --verify)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to process per batch"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize target database
    logger.info("Initializing target database...")
    target_db = await initialize_database(args.target_db)

    # Run migration
    stats = await migrate_objects_to_typed_tables(
        legacy_db_path=args.legacy_db,
        target_db=target_db,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )

    print("\n" + "=" * 60)
    print("MIGRATION REPORT")
    print("=" * 60)
    print(json.dumps(stats.to_dict(), indent=2))

    # Verify if requested
    if args.verify and not args.dry_run:
        print("\n" + "-" * 60)
        print("VERIFICATION")
        print("-" * 60)
        report = await verify_migration(args.legacy_db, target_db)
        print(json.dumps(report, indent=2))

        # Cleanup if requested and verified
        if args.cleanup and report["verified"]:
            print("\n" + "-" * 60)
            print("CLEANUP")
            print("-" * 60)
            migrated_types = [h.type_name for h in HANDLERS]
            deleted = await cleanup_legacy_table(args.legacy_db, migrated_types)
            print(f"Deleted {deleted} legacy records")

    # Exit with appropriate code
    if stats.errors > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
