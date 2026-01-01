# adapters/repository/sqlite.py
"""
SQLite Implementation of LearnerRepository (ODA-Aligned)

This module provides the concrete SQLite implementation of LearnerRepository,
following ODA persistence patterns:

1. Async Operations: Uses aiosqlite for non-blocking I/O
2. JSON Serialization: Stores Pydantic models as JSON blobs
3. Transaction Support: Atomic operations for consistency
4. Audit Trail: Optional history table for change tracking

Architecture Notes:
- Mirrors Orion ODA's SQLite-based ProposalRepository pattern
- Uses JSON serialization (like Pydantic's model_dump_json)
- Maintains separate index table for queryable attributes
- Supports optimistic locking via version field

Performance Considerations:
- JSON blob storage is simple but less queryable
- Index table provides efficient lookups by key attributes
- Consider migration to SQLAlchemy ORM for complex queries

Usage:
    repo = SQLiteLearnerRepository("./data/learners.db")
    profile = await repo.find_by_id("user123")
    await repo.save(profile)
"""

import json
import aiosqlite
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager

from palantir_fde_learning.domain.types import LearnerProfile, LearningDomain
from palantir_fde_learning.adapters.repository.learner_repository import LearnerRepository
from palantir_fde_learning.adapters.repository.base import RepositoryError, EntityNotFoundError


class SQLiteLearnerRepository(LearnerRepository):
    """
    SQLite implementation of LearnerRepository.
    
    Schema Design:
    - learner_profiles: Main entity storage (JSON blob)
    - learner_index: Queryable index for efficient lookups
    - learner_history: Optional audit trail (if auditing enabled)
    
    JSON Storage Rationale:
    - Pydantic models serialize cleanly to JSON
    - Avoids complex ORM mapping for nested structures
    - Easy schema evolution (add fields without migrations)
    - Matches OSDK's thin-client pattern (client doesn't define schema)
    
    Thread Safety:
    - Each method acquires its own connection
    - Uses async context managers for proper cleanup
    - Supports concurrent read/write operations
    """
    
    def __init__(
        self, 
        db_path: str = "learner_state.db",
        enable_audit: bool = False
    ):
        """
        Initialize the SQLite repository.
        
        Args:
            db_path: Path to SQLite database file
            enable_audit: If True, maintain full change history
        """
        self.db_path = Path(db_path)
        self.enable_audit = enable_audit
        self._initialized = False
    
    async def _ensure_schema(self, db: aiosqlite.Connection) -> None:
        """
        Create database schema if not exists.
        
        Uses IF NOT EXISTS for idempotent initialization.
        """
        # Main entity table (JSON blob storage)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS learner_profiles (
                learner_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                overall_mastery REAL DEFAULT 0.0,
                concept_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP,
                version INTEGER DEFAULT 1
            )
        """)
        
        # Index for efficient queries by mastery
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mastery 
            ON learner_profiles(overall_mastery)
        """)
        
        # Index for staleness queries
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed 
            ON learner_profiles(last_accessed_at)
        """)
        
        # Audit history table (optional)
        if self.enable_audit:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS learner_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learner_id TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    action TEXT NOT NULL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (learner_id) REFERENCES learner_profiles(learner_id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_learner 
                ON learner_history(learner_id, changed_at)
            """)
        
        await db.commit()
    
    @asynccontextmanager
    async def connection(self):
        """Get a fresh database connection context, initializing schema if needed."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            # Always ensure schema exists (CREATE IF NOT EXISTS is idempotent)
            await self._ensure_schema(db)
            yield db
    
    async def save(self, entity: LearnerProfile) -> LearnerProfile:
        """
        Persist a LearnerProfile (create or update).
        
        Uses INSERT OR REPLACE for upsert behavior.
        Updates index table for query efficiency.
        Records history if auditing is enabled.
        """
        async with self.connection() as db:
            now = datetime.now().isoformat()
            
            # Calculate queryable attributes
            overall_mastery = entity.overall_mastery()
            concept_count = len(entity.knowledge_states)
            
            # Check if exists (for audit action type)
            cursor = await db.execute(
                "SELECT version FROM learner_profiles WHERE learner_id = ?",
                (entity.learner_id,)
            )
            existing = await cursor.fetchone()
            action = "UPDATE" if existing else "CREATE"
            new_version = (existing["version"] + 1) if existing else 1
            
            # Upsert the profile
            await db.execute("""
                INSERT OR REPLACE INTO learner_profiles 
                (learner_id, profile_json, overall_mastery, concept_count, 
                 updated_at, last_accessed_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.learner_id,
                entity.model_dump_json(),
                overall_mastery,
                concept_count,
                now,
                now,
                new_version,
            ))
            
            # Record audit history if enabled
            if self.enable_audit:
                await db.execute("""
                    INSERT INTO learner_history 
                    (learner_id, profile_json, action)
                    VALUES (?, ?, ?)
                """, (entity.learner_id, entity.model_dump_json(), action))
            
            await db.commit()
            return entity
    
    async def find_by_id(self, entity_id: str) -> Optional[LearnerProfile]:
        """Retrieve a LearnerProfile by ID."""
        async with self.connection() as db:
            cursor = await db.execute(
                "SELECT profile_json FROM learner_profiles WHERE learner_id = ?",
                (entity_id,)
            )
            row = await cursor.fetchone()
            if row:
                return LearnerProfile.model_validate_json(row["profile_json"])
            return None
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[LearnerProfile]:
        """Retrieve all profiles with pagination."""
        async with self.connection() as db:
            cursor = await db.execute(
                "SELECT profile_json FROM learner_profiles ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = await cursor.fetchall()
            return [LearnerProfile.model_validate_json(row["profile_json"]) for row in rows]
    
    async def delete(self, entity_id: str) -> bool:
        """Delete a LearnerProfile by ID."""
        async with self.connection() as db:
            # Record deletion in audit if enabled
            if self.enable_audit:
                cursor = await db.execute(
                    "SELECT profile_json FROM learner_profiles WHERE learner_id = ?",
                    (entity_id,)
                )
                row = await cursor.fetchone()
                if row:
                    await db.execute("""
                        INSERT INTO learner_history (learner_id, profile_json, action)
                        VALUES (?, ?, 'DELETE')
                    """, (entity_id, row["profile_json"]))
            
            cursor = await db.execute(
                "DELETE FROM learner_profiles WHERE learner_id = ?",
                (entity_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def exists(self, entity_id: str) -> bool:
        """Check if a profile exists without loading it."""
        async with self.connection() as db:
            cursor = await db.execute(
                "SELECT 1 FROM learner_profiles WHERE learner_id = ? LIMIT 1",
                (entity_id,)
            )
            return await cursor.fetchone() is not None
    
    async def count(self) -> int:
        """Count total profiles."""
        async with self.connection() as db:
            cursor = await db.execute("SELECT COUNT(*) as cnt FROM learner_profiles")
            row = await cursor.fetchone()
            return row["cnt"] if row else 0
    
    # --- Domain-Specific Queries ---
    
    async def find_by_mastery_above(
        self, 
        threshold: float,
        limit: int = 100
    ) -> List[LearnerProfile]:
        """Find learners with mastery above threshold."""
        async with self.connection() as db:
            cursor = await db.execute(
                """SELECT profile_json FROM learner_profiles 
                   WHERE overall_mastery >= ? 
                   ORDER BY overall_mastery DESC 
                   LIMIT ?""",
                (threshold, limit)
            )
            rows = await cursor.fetchall()
            return [LearnerProfile.model_validate_json(row["profile_json"]) for row in rows]
    
    async def find_by_mastery_below(
        self, 
        threshold: float,
        limit: int = 100
    ) -> List[LearnerProfile]:
        """Find learners with mastery below threshold."""
        async with self.connection() as db:
            cursor = await db.execute(
                """SELECT profile_json FROM learner_profiles 
                   WHERE overall_mastery < ? 
                   ORDER BY overall_mastery ASC 
                   LIMIT ?""",
                (threshold, limit)
            )
            rows = await cursor.fetchall()
            return [LearnerProfile.model_validate_json(row["profile_json"]) for row in rows]
    
    async def find_stale_profiles(
        self, 
        days: int = 7,
        limit: int = 100
    ) -> List[LearnerProfile]:
        """Find profiles not accessed in specified days."""
        async with self.connection() as db:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor = await db.execute(
                """SELECT profile_json FROM learner_profiles 
                   WHERE last_accessed_at < ? OR last_accessed_at IS NULL
                   ORDER BY last_accessed_at ASC 
                   LIMIT ?""",
                (cutoff, limit)
            )
            rows = await cursor.fetchall()
            return [LearnerProfile.model_validate_json(row["profile_json"]) for row in rows]
    
    async def find_by_domain_progress(
        self, 
        domain: LearningDomain,
        min_concepts: int = 1
    ) -> List[LearnerProfile]:
        """
        Find learners with progress in a specific domain.
        
        Note: This requires loading and checking each profile since
        domain info is in the JSON blob. Consider adding a domain
        index table for large-scale deployments.
        """
        async with self.connection() as db:
            cursor = await db.execute(
                "SELECT profile_json FROM learner_profiles"
            )
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                profile = LearnerProfile.model_validate_json(row["profile_json"])
                # Count concepts in the specified domain
                domain_concepts = sum(
                    1 for concept_id in profile.knowledge_states.keys()
                    if concept_id.startswith(domain.value)
                )
                if domain_concepts >= min_concepts:
                    results.append(profile)
            
            return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        async with self.connection() as db:
            # Total count
            cursor = await db.execute("SELECT COUNT(*) as total FROM learner_profiles")
            total = (await cursor.fetchone())["total"]
            
            # Average mastery
            cursor = await db.execute(
                "SELECT AVG(overall_mastery) as avg_mastery FROM learner_profiles"
            )
            avg_mastery = (await cursor.fetchone())["avg_mastery"] or 0.0
            
            # Distribution by mastery tier
            cursor = await db.execute("""
                SELECT 
                    CASE 
                        WHEN overall_mastery >= 0.7 THEN 'mastered'
                        WHEN overall_mastery >= 0.3 THEN 'learning'
                        ELSE 'beginner'
                    END as tier,
                    COUNT(*) as count
                FROM learner_profiles
                GROUP BY tier
            """)
            distribution = {row["tier"]: row["count"] for row in await cursor.fetchall()}
            
            # Stale profiles count
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = await db.execute(
                "SELECT COUNT(*) as stale FROM learner_profiles WHERE last_accessed_at < ? OR last_accessed_at IS NULL",
                (cutoff,)
            )
            stale_count = (await cursor.fetchone())["stale"]
            
            return {
                "total_learners": total,
                "average_mastery": round(avg_mastery, 3),
                "distribution": distribution,
                "stale_count": stale_count,
                "active_count": total - stale_count,
            }
    
    async def bulk_save(self, profiles: List[LearnerProfile]) -> int:
        """Save multiple profiles in a transaction."""
        async with self.connection() as db:
            saved = 0
            try:
                for profile in profiles:
                    now = datetime.now().isoformat()
                    await db.execute("""
                        INSERT OR REPLACE INTO learner_profiles 
                        (learner_id, profile_json, overall_mastery, concept_count, updated_at, last_accessed_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        profile.learner_id,
                        profile.model_dump_json(),
                        profile.overall_mastery(),
                        len(profile.knowledge_states),
                        now,
                        now,
                    ))
                    saved += 1
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise RepositoryError(f"Bulk save failed: {e}") from e
            return saved
