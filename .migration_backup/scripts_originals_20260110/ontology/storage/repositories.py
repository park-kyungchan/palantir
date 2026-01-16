"""
Orion ODA V3 - Domain Repositories
===================================
Concrete repository implementations for each domain type.

Each repository:
1. Inherits from GenericRepository
2. Implements _to_domain(), _create_model(), _get_update_values()
3. May add domain-specific query methods

Usage:
    db = await initialize_database()
    repo = ActionLogRepository(db)
    await repo.save(action_log, actor_id="system")
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from lib.oda.ontology.ontology_types import ObjectStatus
from lib.oda.ontology.schemas.governance import OrionActionLog
from lib.oda.ontology.schemas.result import JobResult, Artifact
from lib.oda.ontology.schemas.memory import (
    OrionInsight,
    OrionPattern,
    InsightContent,
    InsightProvenance,
    PatternStructure,
)
from lib.oda.ontology.storage.base_repository import GenericRepository
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.models import (
    OrionActionLogModel,
    JobResultModel,
    OrionInsightModel,
    OrionPatternModel,
)


# =============================================================================
# ACTION LOG REPOSITORY
# =============================================================================

class ActionLogRepository(GenericRepository[OrionActionLog, OrionActionLogModel]):
    """
    Repository for OrionActionLog entities.

    Stores immutable audit records for kinetic actions.
    Note: Action logs should generally not be updated after creation.
    """

    model_class = OrionActionLogModel
    domain_class = OrionActionLog

    def __init__(self, db: Database, publish_events: bool = True):
        super().__init__(db, publish_events)

    def _to_domain(self, model: OrionActionLogModel) -> OrionActionLog:
        """Convert ORM model to domain entity."""
        return OrionActionLog(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            version=model.version,
            status=model.status,  # SUCCESS, FAILURE, ROLLED_BACK
            agent_id=model.agent_id,
            trace_id=model.trace_id,
            action_type=model.action_type,
            parameters=model.parameters or {},
            error=model.error,
            affected_ids=model.affected_ids or [],
            duration_ms=model.duration_ms,
        )

    def _create_model(self, entity: OrionActionLog, actor_id: str) -> OrionActionLogModel:
        """Create new ORM model for INSERT."""
        return OrionActionLogModel(
            id=entity.id,
            version=entity.version or 1,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=actor_id,
            updated_by=actor_id,
            status=entity.status,
            agent_id=entity.agent_id,
            trace_id=entity.trace_id,
            action_type=entity.action_type,
            parameters=entity.parameters,
            error=entity.error,
            affected_ids=entity.affected_ids,
            duration_ms=entity.duration_ms,
            fts_content=entity.get_searchable_text(),
        )

    def _get_update_values(
        self,
        entity: OrionActionLog,
        actor_id: str,
        new_version: int
    ) -> Dict[str, Any]:
        """Get values for UPDATE statement."""
        return {
            "version": new_version,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": actor_id,
            "status": entity.status,
            "error": entity.error,
            "affected_ids": entity.affected_ids,
            "duration_ms": entity.duration_ms,
        }

    # Domain-specific queries
    async def find_by_action_type(
        self,
        action_type: str,
        limit: int = 100
    ) -> List[OrionActionLog]:
        """Find action logs by action type."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.action_type == action_type)
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def find_by_trace_id(self, trace_id: str) -> List[OrionActionLog]:
        """Find all action logs for a given trace/job."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.trace_id == trace_id)
                .order_by(self.model_class.created_at.asc())
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]


# =============================================================================
# JOB RESULT REPOSITORY
# =============================================================================

class JobResultRepository(GenericRepository[JobResult, JobResultModel]):
    """
    Repository for JobResult entities.

    Stores formal output contracts from agent execution.
    """

    model_class = JobResultModel
    domain_class = JobResult

    def __init__(self, db: Database, publish_events: bool = True):
        super().__init__(db, publish_events)

    def _to_domain(self, model: JobResultModel) -> JobResult:
        """Convert ORM model to domain entity."""
        # Convert artifact dicts back to Artifact objects
        artifacts = [
            Artifact(**a) for a in (model.output_artifacts or [])
        ]

        return JobResult(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            version=model.version,
            status=model.status,  # SUCCESS, FAILURE, BLOCKED
            job_id=model.job_id,
            output_artifacts=artifacts,
            metrics=model.metrics or {},
        )

    def _create_model(self, entity: JobResult, actor_id: str) -> JobResultModel:
        """Create new ORM model for INSERT."""
        # Convert Artifact objects to dicts for JSON storage
        artifacts_json = [a.model_dump() for a in entity.output_artifacts]

        return JobResultModel(
            id=entity.id,
            version=entity.version or 1,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=actor_id,
            updated_by=actor_id,
            status=entity.status,
            job_id=entity.job_id,
            output_artifacts=artifacts_json,
            metrics=entity.metrics,
            fts_content=f"{entity.job_id} {entity.status}",
        )

    def _get_update_values(
        self,
        entity: JobResult,
        actor_id: str,
        new_version: int
    ) -> Dict[str, Any]:
        """Get values for UPDATE statement."""
        artifacts_json = [a.model_dump() for a in entity.output_artifacts]

        return {
            "version": new_version,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": actor_id,
            "status": entity.status,
            "output_artifacts": artifacts_json,
            "metrics": entity.metrics,
        }

    # Domain-specific queries
    async def find_by_job_id(self, job_id: str) -> Optional[JobResult]:
        """Find job result by job ID (unique)."""
        async with self.db.transaction() as session:
            stmt = select(self.model_class).where(
                self.model_class.job_id == job_id
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None


# =============================================================================
# INSIGHT REPOSITORY
# =============================================================================

class InsightRepository(GenericRepository[OrionInsight, OrionInsightModel]):
    """
    Repository for OrionInsight entities.

    Stores declarative knowledge learned from execution.
    """

    model_class = OrionInsightModel
    domain_class = OrionInsight

    def __init__(self, db: Database, publish_events: bool = True):
        super().__init__(db, publish_events)

    def _to_domain(self, model: OrionInsightModel) -> OrionInsight:
        """Convert ORM model to domain entity."""
        # Reconstruct nested Pydantic models
        content = InsightContent(
            summary=model.summary,
            domain=model.domain,
            tags=model.tags or [],
        )
        provenance = InsightProvenance(
            source_episodic_ids=model.source_episodic_ids or [],
            method=model.provenance_method,
        )

        # Map model.status (str) to ObjectStatus enum
        try:
            status = ObjectStatus(model.status)
        except ValueError:
            status = ObjectStatus.ACTIVE

        return OrionInsight(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            version=model.version,
            status=status,
            confidence_score=model.confidence_score,
            decay_factor=model.decay_factor,
            provenance=provenance,
            content=content,
            supports=model.supports or [],
            contradicts=model.contradicts or [],
            related_to=model.related_to or [],
        )

    def _create_model(self, entity: OrionInsight, actor_id: str) -> OrionInsightModel:
        """Create new ORM model for INSERT."""
        # Handle status which could be ObjectStatus enum or string
        status_value = entity.status.value if hasattr(entity.status, 'value') else str(entity.status)

        return OrionInsightModel(
            id=entity.id,
            version=entity.version or 1,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=actor_id,
            updated_by=actor_id,
            status=status_value,
            summary=entity.content.summary,
            domain=entity.content.domain,
            tags=entity.content.tags,
            confidence_score=entity.confidence_score,
            decay_factor=entity.decay_factor,
            source_episodic_ids=entity.provenance.source_episodic_ids,
            provenance_method=entity.provenance.method,
            supports=entity.supports,
            contradicts=entity.contradicts,
            related_to=entity.related_to,
            fts_content=entity.get_searchable_text(),
        )

    def _get_update_values(
        self,
        entity: OrionInsight,
        actor_id: str,
        new_version: int
    ) -> Dict[str, Any]:
        """Get values for UPDATE statement."""
        status_value = entity.status.value if hasattr(entity.status, 'value') else str(entity.status)

        return {
            "version": new_version,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": actor_id,
            "status": status_value,
            "summary": entity.content.summary,
            "domain": entity.content.domain,
            "tags": entity.content.tags,
            "confidence_score": entity.confidence_score,
            "decay_factor": entity.decay_factor,
            "supports": entity.supports,
            "contradicts": entity.contradicts,
            "related_to": entity.related_to,
        }

    # Domain-specific queries
    async def find_by_domain(
        self,
        domain: str,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[OrionInsight]:
        """Find insights by domain with minimum confidence threshold."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.domain == domain)
                .where(self.model_class.confidence_score >= min_confidence)
                .where(self.model_class.status == "active")
                .order_by(self.model_class.confidence_score.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def search(self, query: str, limit: int = 50) -> List[OrionInsight]:
        """Full-text search across insights."""
        async with self.db.transaction() as session:
            # Simple LIKE search for now; can be upgraded to FTS5
            pattern = f"%{query}%"
            stmt = (
                select(self.model_class)
                .where(self.model_class.fts_content.ilike(pattern))
                .where(self.model_class.status == "active")
                .order_by(self.model_class.confidence_score.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]


# =============================================================================
# PATTERN REPOSITORY
# =============================================================================

class PatternRepository(GenericRepository[OrionPattern, OrionPatternModel]):
    """
    Repository for OrionPattern entities.

    Stores procedural knowledge (reusable workflows) learned from execution.
    """

    model_class = OrionPatternModel
    domain_class = OrionPattern

    def __init__(self, db: Database, publish_events: bool = True):
        super().__init__(db, publish_events)

    def _to_domain(self, model: OrionPatternModel) -> OrionPattern:
        """Convert ORM model to domain entity."""
        # Reconstruct nested PatternStructure
        structure = PatternStructure(
            trigger=model.trigger,
            steps=model.steps or [],
            anti_patterns=model.anti_patterns or [],
        )

        # Map model.status (str) to ObjectStatus enum
        try:
            status = ObjectStatus(model.status)
        except ValueError:
            status = ObjectStatus.ACTIVE

        return OrionPattern(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            version=model.version,
            status=status,
            frequency_count=model.frequency_count,
            success_rate=model.success_rate,
            last_used=model.last_used,
            structure=structure,
            code_snippet_ref=model.code_snippet_ref,
        )

    def _create_model(self, entity: OrionPattern, actor_id: str) -> OrionPatternModel:
        """Create new ORM model for INSERT."""
        status_value = entity.status.value if hasattr(entity.status, 'value') else str(entity.status)

        return OrionPatternModel(
            id=entity.id,
            version=entity.version or 1,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=actor_id,
            updated_by=actor_id,
            status=status_value,
            trigger=entity.structure.trigger,
            steps=entity.structure.steps,
            anti_patterns=entity.structure.anti_patterns,
            frequency_count=entity.frequency_count,
            success_rate=entity.success_rate,
            last_used=entity.last_used,
            code_snippet_ref=entity.code_snippet_ref,
            fts_content=entity.get_searchable_text(),
        )

    def _get_update_values(
        self,
        entity: OrionPattern,
        actor_id: str,
        new_version: int
    ) -> Dict[str, Any]:
        """Get values for UPDATE statement."""
        status_value = entity.status.value if hasattr(entity.status, 'value') else str(entity.status)

        return {
            "version": new_version,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": actor_id,
            "status": status_value,
            "trigger": entity.structure.trigger,
            "steps": entity.structure.steps,
            "anti_patterns": entity.structure.anti_patterns,
            "frequency_count": entity.frequency_count,
            "success_rate": entity.success_rate,
            "last_used": entity.last_used,
            "code_snippet_ref": entity.code_snippet_ref,
        }

    # Domain-specific queries
    async def find_most_used(self, limit: int = 10) -> List[OrionPattern]:
        """Find most frequently used patterns."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.status == "active")
                .order_by(self.model_class.frequency_count.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def find_most_successful(
        self,
        min_frequency: int = 5,
        limit: int = 10
    ) -> List[OrionPattern]:
        """Find patterns with highest success rate (min frequency filter)."""
        async with self.db.transaction() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.status == "active")
                .where(self.model_class.frequency_count >= min_frequency)
                .order_by(self.model_class.success_rate.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def increment_usage(
        self,
        pattern_id: str,
        success: bool,
        actor_id: str = "system"
    ) -> Optional[OrionPattern]:
        """
        Increment usage count and update success rate.

        Args:
            pattern_id: ID of pattern to update
            success: Whether this usage was successful
            actor_id: Who triggered the usage
        """
        pattern = await self.find_by_id(pattern_id)
        if pattern is None:
            return None

        # Update statistics
        old_count = pattern.frequency_count
        new_count = old_count + 1

        # Recalculate success rate (weighted average)
        old_rate = pattern.success_rate
        if success:
            new_rate = (old_rate * old_count + 1.0) / new_count
        else:
            new_rate = (old_rate * old_count) / new_count

        pattern.frequency_count = new_count
        pattern.success_rate = new_rate
        pattern.last_used = datetime.now(timezone.utc)
        pattern.touch(updated_by=actor_id)

        return await self.save(pattern, actor_id=actor_id)

    async def search(self, query: str, limit: int = 50) -> List[OrionPattern]:
        """
        Full-text search across patterns (trigger and steps).
        
        Matches InsightRepository.search() pattern for consistency.
        Uses LIKE query; can be upgraded to FTS5 for production.
        
        Args:
            query: Search term to match against fts_content
            limit: Maximum results to return
            
        Returns:
            List of matching patterns ordered by success_rate
        """
        async with self.db.transaction() as session:
            pattern = f"%{query}%"
            stmt = (
                select(self.model_class)
                .where(self.model_class.fts_content.ilike(pattern))
                .where(self.model_class.status == "active")
                .order_by(self.model_class.success_rate.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

