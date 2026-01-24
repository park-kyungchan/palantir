"""
ODA Storage - LearnerRepository
==============================

Persists `Learner` objects keyed by `user_id` with optimistic concurrency control.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select

from lib.oda.ontology.objects.learning import Learner
from lib.oda.ontology.storage.base_repository import TransactionalRepository
from lib.oda.ontology.storage.database import Database, DatabaseManager
from lib.oda.ontology.storage.models import LearnerModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _json_loads(value: Optional[str], default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


class LearnerRepository(TransactionalRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__(db or DatabaseManager.get())

    async def get_by_user_id(self, user_id: str) -> Optional[Learner]:
        async with self.session() as session:
            stmt = select(LearnerModel).where(LearnerModel.user_id == user_id).limit(1)
            model = (await session.execute(stmt)).scalars().first()
            if model is None:
                return None

        return Learner(
            id=model.id,
            user_id=model.user_id,
            theta=model.theta,
            knowledge_state=_json_loads(model.knowledge_state, default={}),
            last_active=model.last_active,
            created_by=model.created_by,
            updated_by=model.updated_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            status=model.status,
            version=model.version,
        )

    async def save(self, learner: Learner, actor_id: Optional[str] = None) -> Learner:
        async with self.session() as session:
            stmt = select(LearnerModel).where(LearnerModel.user_id == learner.user_id).limit(1)
            existing = (await session.execute(stmt)).scalars().first()

            if existing is None:
                model = LearnerModel(
                    id=learner.id,
                    user_id=learner.user_id,
                    theta=learner.theta,
                    knowledge_state=_json_dumps(learner.knowledge_state or {}),
                    last_active=learner.last_active or "",
                    created_by=learner.created_by,
                    updated_by=actor_id or learner.updated_by,
                    created_at=learner.created_at,
                    updated_at=_utc_now(),
                    status=str(getattr(learner.status, "value", learner.status)),
                    version=learner.version,
                )
                session.add(model)
                return learner

            # Updates use OCC: require client version == db_version + 1
            if learner.version != existing.version + 1:
                raise ValueError("Optimistic lock failure for learner update")

            existing.theta = learner.theta
            existing.knowledge_state = _json_dumps(learner.knowledge_state or {})
            existing.last_active = learner.last_active or ""
            existing.updated_by = actor_id or learner.updated_by
            existing.updated_at = _utc_now()
            existing.version = learner.version

            # Keep stable DB ID
            learner.id = existing.id
            return learner


__all__ = ["LearnerRepository"]

