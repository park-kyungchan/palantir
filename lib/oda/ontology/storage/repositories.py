"""
ODA Storage - Repository Implementations
======================================

These repositories provide simple persistence helpers for core ontology objects
stored in the SQLite database.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from lib.oda.ontology.schemas.governance import OrionActionLog
from lib.oda.ontology.schemas.memory import OrionInsight, OrionPattern
from lib.oda.ontology.schemas.result import JobResult
from lib.oda.ontology.storage.base_repository import TransactionalRepository
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.models import (
    JobResultModel,
    OrionActionLogModel,
    OrionInsightModel,
    OrionPatternModel,
)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _json_loads(value: Optional[str], default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InsightRepository(TransactionalRepository):
    def __init__(self, db: Database):
        super().__init__(db)

    async def save(self, insight: OrionInsight, actor_id: Optional[str] = None) -> OrionInsight:
        async with self.session() as session:
            existing = await session.get(OrionInsightModel, insight.id)
            if existing is None:
                model = OrionInsightModel(
                    id=insight.id,
                    status=str(insight.status.value) if hasattr(insight.status, "value") else str(insight.status),
                    confidence_score=float(insight.confidence_score),
                    decay_factor=insight.decay_factor,
                    provenance=_json_dumps(insight.provenance.model_dump()),
                    content=_json_dumps(insight.content.model_dump()),
                    supports=_json_dumps(insight.supports),
                    contradicts=_json_dumps(insight.contradicts),
                    related_to=_json_dumps(insight.related_to),
                    created_by=insight.created_by,
                    updated_by=actor_id or insight.updated_by,
                    created_at=insight.created_at,
                    updated_at=_utc_now(),
                    version=insight.version,
                )
                session.add(model)
            else:
                # OCC-lite: require client version == db_version + 1 when updating
                if insight.version != existing.version + 1:
                    raise ValueError("Optimistic lock failure for insight update")
                existing.status = str(insight.status.value) if hasattr(insight.status, "value") else str(insight.status)
                existing.confidence_score = float(insight.confidence_score)
                existing.decay_factor = insight.decay_factor
                existing.provenance = _json_dumps(insight.provenance.model_dump())
                existing.content = _json_dumps(insight.content.model_dump())
                existing.supports = _json_dumps(insight.supports)
                existing.contradicts = _json_dumps(insight.contradicts)
                existing.related_to = _json_dumps(insight.related_to)
                existing.updated_by = actor_id or insight.updated_by
                existing.updated_at = _utc_now()
                existing.version = insight.version

            await session.flush()

        return insight

    async def find_by_id(self, insight_id: str) -> Optional[OrionInsight]:
        async with self.session() as session:
            model = await session.get(OrionInsightModel, insight_id)
            if model is None:
                return None

        return OrionInsight(
            id=model.id,
            status=model.status,
            confidence_score=model.confidence_score,
            decay_factor=model.decay_factor,
            provenance=_json_loads(model.provenance, default={}),
            content=_json_loads(model.content, default={}),
            supports=_json_loads(model.supports, default=[]),
            contradicts=_json_loads(model.contradicts, default=[]),
            related_to=_json_loads(model.related_to, default=[]),
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )

    async def find_all(self, limit: int = 10_000) -> List[OrionInsight]:
        async with self.session() as session:
            stmt = select(OrionInsightModel).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()

        return [
            OrionInsight(
                id=m.id,
                status=m.status,
                confidence_score=m.confidence_score,
                decay_factor=m.decay_factor,
                provenance=_json_loads(m.provenance, default={}),
                content=_json_loads(m.content, default={}),
                supports=_json_loads(m.supports, default=[]),
                contradicts=_json_loads(m.contradicts, default=[]),
                related_to=_json_loads(m.related_to, default=[]),
                created_by=m.created_by,
                updated_by=m.updated_by,
                created_at=m.created_at,
                updated_at=m.updated_at,
                version=m.version,
            )
            for m in rows
        ]

    async def search(self, query: str, limit: int = 5) -> List[OrionInsight]:
        # Naive LIKE search on content JSON blob (good enough for tests/dev).
        async with self.session() as session:
            stmt = select(OrionInsightModel).where(OrionInsightModel.content.like(f"%{query}%")).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
        return [await self.find_by_id(m.id) for m in rows if m is not None]  # type: ignore[misc]


class PatternRepository(TransactionalRepository):
    def __init__(self, db: Database):
        super().__init__(db)

    async def save(self, pattern: OrionPattern, actor_id: Optional[str] = None) -> OrionPattern:
        async with self.session() as session:
            existing = await session.get(OrionPatternModel, pattern.id)
            if existing is None:
                model = OrionPatternModel(
                    id=pattern.id,
                    status=str(pattern.status.value) if hasattr(pattern.status, "value") else str(pattern.status),
                    frequency_count=int(pattern.frequency_count),
                    success_rate=float(pattern.success_rate),
                    last_used=pattern.last_used,
                    structure=_json_dumps(pattern.structure.model_dump()),
                    code_snippet_ref=pattern.code_snippet_ref,
                    created_by=pattern.created_by,
                    updated_by=actor_id or pattern.updated_by,
                    created_at=pattern.created_at,
                    updated_at=_utc_now(),
                    version=pattern.version,
                )
                session.add(model)
            else:
                if pattern.version != existing.version + 1:
                    raise ValueError("Optimistic lock failure for pattern update")
                existing.status = str(pattern.status.value) if hasattr(pattern.status, "value") else str(pattern.status)
                existing.frequency_count = int(pattern.frequency_count)
                existing.success_rate = float(pattern.success_rate)
                existing.last_used = pattern.last_used
                existing.structure = _json_dumps(pattern.structure.model_dump())
                existing.code_snippet_ref = pattern.code_snippet_ref
                existing.updated_by = actor_id or pattern.updated_by
                existing.updated_at = _utc_now()
                existing.version = pattern.version

        return pattern

    async def find_by_id(self, pattern_id: str) -> Optional[OrionPattern]:
        async with self.session() as session:
            model = await session.get(OrionPatternModel, pattern_id)
            if model is None:
                return None

        return OrionPattern(
            id=model.id,
            status=model.status,
            frequency_count=model.frequency_count,
            success_rate=model.success_rate,
            last_used=model.last_used,
            structure=_json_loads(model.structure, default={}),
            code_snippet_ref=model.code_snippet_ref,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )


class ActionLogRepository(TransactionalRepository):
    def __init__(self, db: Database, publish_events: bool = True):
        super().__init__(db)
        self.publish_events = publish_events

    async def save(self, log: OrionActionLog) -> OrionActionLog:
        async with self.session() as session:
            existing = await session.get(OrionActionLogModel, log.id)
            if existing is None:
                session.add(
                    OrionActionLogModel(
                        id=log.id,
                        agent_id=getattr(log, "agent_id", None),
                        trace_id=getattr(log, "trace_id", None),
                        action_type=log.action_type,
                        parameters=_json_dumps(log.parameters or {}),
                        status=log.status,
                        error=log.error,
                        affected_ids=_json_dumps(log.affected_ids or []),
                        duration_ms=int(getattr(log, "duration_ms", 0) or 0),
                        created_at=log.created_at,
                        updated_at=log.updated_at,
                    )
                )
            else:
                existing.status = log.status
                existing.error = log.error
                existing.parameters = _json_dumps(log.parameters or {})
                existing.affected_ids = _json_dumps(log.affected_ids or [])
                existing.duration_ms = int(getattr(log, "duration_ms", 0) or 0)
                existing.updated_at = _utc_now()

        return log

    async def find_all(self, limit: int = 10_000) -> List[OrionActionLog]:
        async with self.session() as session:
            stmt = select(OrionActionLogModel).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()

        return [
            OrionActionLog(
                id=m.id,
                agent_id=m.agent_id or "Orion-Kernel",
                trace_id=m.trace_id,
                action_type=m.action_type,
                parameters=_json_loads(m.parameters, default={}),
                status=m.status,
                error=m.error,
                affected_ids=_json_loads(m.affected_ids, default=[]),
                duration_ms=m.duration_ms,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in rows
        ]


class JobResultRepository(TransactionalRepository):
    def __init__(self, db: Database):
        super().__init__(db)

    async def save(self, result: JobResult) -> JobResult:
        async with self.session() as session:
            existing = await session.get(JobResultModel, result.id)
            if existing is None:
                session.add(
                    JobResultModel(
                        id=result.id,
                        job_id=result.job_id,
                        status=result.status,
                        output_artifacts=_json_dumps([a.model_dump() for a in result.output_artifacts]),
                        metrics=_json_dumps(result.metrics or {}),
                        created_at=result.created_at,
                        updated_at=result.updated_at,
                    )
                )
            else:
                existing.status = result.status
                existing.output_artifacts = _json_dumps([a.model_dump() for a in result.output_artifacts])
                existing.metrics = _json_dumps(result.metrics or {})
                existing.updated_at = _utc_now()

        return result

    async def find_by_id(self, result_id: str) -> Optional[JobResult]:
        async with self.session() as session:
            model = await session.get(JobResultModel, result_id)
            if model is None:
                return None

        return JobResult(
            id=model.id,
            job_id=model.job_id,
            status=model.status,
            output_artifacts=_json_loads(model.output_artifacts, default=[]),
            metrics=_json_loads(model.metrics, default={}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


__all__ = [
    "ActionLogRepository",
    "InsightRepository",
    "JobResultRepository",
    "PatternRepository",
]
