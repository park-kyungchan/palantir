"""
ODA Storage - ProposalRepository
===============================

Implements persistence and governance helpers for `Proposal` objects.
The behavior is primarily specified by `tests/e2e/test_proposal_repository.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, func, select

from lib.oda.ontology.objects.proposal import Proposal, ProposalPriority, ProposalStatus
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.models import ProposalHistoryModel, ProposalModel


class ProposalNotFoundError(Exception):
    def __init__(self, proposal_id: str):
        super().__init__(f"Proposal not found: {proposal_id}")
        self.proposal_id = proposal_id


class OptimisticLockError(Exception):
    def __init__(self, proposal_id: str, expected_version: int, actual_version: int):
        super().__init__(
            f"Optimistic lock failed for {proposal_id}: expected base version {expected_version}, got {actual_version}"
        )
        self.proposal_id = proposal_id
        self.expected_version = expected_version
        self.actual_version = actual_version


@dataclass
class ProposalQuery:
    status: Optional[ProposalStatus] = None
    created_by: Optional[str] = None
    action_type: Optional[str] = None
    priority: Optional[ProposalPriority] = None
    limit: int = 50
    offset: int = 0


@dataclass
class PaginatedResult:
    items: List[Proposal]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total


@dataclass
class ProposalHistoryEntry:
    action: str
    actor_id: Optional[str]
    timestamp: datetime
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    comment: Optional[str] = None


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


class ProposalRepository:
    def __init__(self, db: Database):
        self.db = db

    # ---------------------------------------------------------------------
    # Mapping helpers
    # ---------------------------------------------------------------------

    def _to_model(self, proposal: Proposal, model: Optional[ProposalModel] = None) -> ProposalModel:
        m = model or ProposalModel(id=proposal.id)

        m.action_type = proposal.action_type
        m.payload = _json_dumps(proposal.payload or {})
        m.status = proposal.status.value if isinstance(proposal.status, ProposalStatus) else str(proposal.status)
        m.priority = (
            proposal.priority.value if isinstance(proposal.priority, ProposalPriority) else str(proposal.priority)
        )

        m.created_by = proposal.created_by
        m.updated_by = proposal.updated_by
        m.reviewed_by = proposal.reviewed_by
        m.reviewed_at = proposal.reviewed_at
        m.review_comment = proposal.review_comment
        m.executed_at = proposal.executed_at
        m.execution_result = _json_dumps(proposal.execution_result) if proposal.execution_result is not None else None
        m.tags = _json_dumps(proposal.tags or [])

        m.created_at = proposal.created_at
        m.updated_at = proposal.updated_at
        m.version = proposal.version
        return m

    def _to_domain(self, model: ProposalModel) -> Proposal:
        return Proposal(
            id=model.id,
            action_type=model.action_type,
            payload=_json_loads(model.payload, default={}),
            status=model.status,
            priority=model.priority,
            created_by=model.created_by,
            updated_by=model.updated_by,
            reviewed_by=model.reviewed_by,
            reviewed_at=model.reviewed_at,
            review_comment=model.review_comment,
            executed_at=model.executed_at,
            execution_result=_json_loads(model.execution_result, default=None),
            tags=_json_loads(model.tags, default=[]),
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )

    async def _append_history(
        self,
        proposal_id: str,
        action: str,
        actor_id: Optional[str],
        previous_status: Optional[str],
        new_status: Optional[str],
        comment: Optional[str],
    ) -> None:
        async with self.db.transaction() as session:
            session.add(
                ProposalHistoryModel(
                    proposal_id=proposal_id,
                    action=action,
                    actor_id=actor_id,
                    timestamp=_utc_now(),
                    previous_status=previous_status,
                    new_status=new_status,
                    comment=comment,
                )
            )

    # ---------------------------------------------------------------------
    # CRUD
    # ---------------------------------------------------------------------

    async def find_by_id(self, proposal_id: str) -> Optional[Proposal]:
        async with self.db.transaction() as session:
            model = await session.get(ProposalModel, proposal_id)
            return self._to_domain(model) if model else None

    async def save(
        self,
        proposal: Proposal,
        actor_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Proposal:
        async with self.db.transaction() as session:
            existing = await session.get(ProposalModel, proposal.id)

            if existing is None:
                session.add(self._to_model(proposal))
                created = True
                previous_status = None
            else:
                created = False
                previous_status = existing.status

                # Optimistic lock: require proposal.version == db_version + 1
                if proposal.version != existing.version + 1:
                    raise OptimisticLockError(
                        proposal_id=proposal.id,
                        expected_version=existing.version,
                        actual_version=proposal.version,
                    )

                self._to_model(proposal, model=existing)

        # History is stored as a separate record; keep it simple and consistent.
        if created:
            await self._append_history(
                proposal_id=proposal.id,
                action="created",
                actor_id=actor_id,
                previous_status=previous_status,
                new_status=proposal.status.value,
                comment=comment,
            )
        else:
            await self._append_history(
                proposal_id=proposal.id,
                action="updated",
                actor_id=actor_id,
                previous_status=previous_status,
                new_status=proposal.status.value,
                comment=comment,
            )

        return proposal

    async def delete(self, proposal_id: str, actor_id: str, hard_delete: bool = False) -> bool:
        async with self.db.transaction() as session:
            existing = await session.get(ProposalModel, proposal_id)
            if existing is None:
                return False

            if hard_delete:
                await session.execute(delete(ProposalHistoryModel).where(ProposalHistoryModel.proposal_id == proposal_id))
                await session.execute(delete(ProposalModel).where(ProposalModel.id == proposal_id))
                return True

            # Soft delete: mark status as deleted with optimistic version bump.
            proposal = self._to_domain(existing)
            previous_status = proposal.status.value
            proposal.status = ProposalStatus.DELETED
            proposal.touch(updated_by=actor_id)

            if proposal.version != existing.version + 1:
                raise OptimisticLockError(proposal_id, expected_version=existing.version, actual_version=proposal.version)

            self._to_model(proposal, model=existing)

        await self._append_history(
            proposal_id=proposal_id,
            action="deleted",
            actor_id=actor_id,
            previous_status=previous_status,
            new_status=ProposalStatus.DELETED.value,
            comment=None,
        )
        return True

    async def save_many(self, proposals: List[Proposal], actor_id: Optional[str] = None) -> List[Proposal]:
        async with self.db.transaction() as session:
            for proposal in proposals:
                existing = await session.get(ProposalModel, proposal.id)
                if existing is None:
                    session.add(self._to_model(proposal))
                else:
                    if proposal.version != existing.version + 1:
                        raise OptimisticLockError(
                            proposal_id=proposal.id,
                            expected_version=existing.version,
                            actual_version=proposal.version,
                        )
                    self._to_model(proposal, model=existing)

        # History (best-effort) — keep batch deterministic but not overly slow.
        for proposal in proposals:
            await self._append_history(
                proposal_id=proposal.id,
                action="created",
                actor_id=actor_id,
                previous_status=None,
                new_status=proposal.status.value,
                comment=None,
            )
        return proposals

    # ---------------------------------------------------------------------
    # Queries
    # ---------------------------------------------------------------------

    async def find_by_status(self, status: ProposalStatus) -> List[Proposal]:
        query = ProposalQuery(status=status, limit=10_000, offset=0)
        result = await self.query(query)
        return result.items

    async def find_pending(self) -> List[Proposal]:
        return await self.find_by_status(ProposalStatus.PENDING)

    async def find_by_action_type(self, action_type: str) -> List[Proposal]:
        query = ProposalQuery(action_type=action_type, limit=10_000, offset=0)
        result = await self.query(query)
        return result.items

    async def find_by_creator(self, created_by: str) -> List[Proposal]:
        query = ProposalQuery(created_by=created_by, limit=10_000, offset=0)
        result = await self.query(query)
        return result.items

    async def query(self, query: ProposalQuery) -> PaginatedResult:
        filters = []

        if query.status is not None:
            filters.append(ProposalModel.status == query.status.value)
        if query.created_by is not None:
            filters.append(ProposalModel.created_by == query.created_by)
        if query.action_type is not None:
            filters.append(ProposalModel.action_type == query.action_type)
        if query.priority is not None:
            filters.append(ProposalModel.priority == query.priority.value)

        async with self.db.transaction() as session:
            count_stmt = select(func.count()).select_from(ProposalModel)
            if filters:
                count_stmt = count_stmt.where(*filters)
            total = int((await session.execute(count_stmt)).scalar() or 0)

            stmt = select(ProposalModel)
            if filters:
                stmt = stmt.where(*filters)
            stmt = stmt.order_by(ProposalModel.created_at.desc()).limit(query.limit).offset(query.offset)

            rows = (await session.execute(stmt)).scalars().all()
            items = [self._to_domain(r) for r in rows]

        return PaginatedResult(items=items, total=total, limit=query.limit, offset=query.offset)

    async def count_by_status(self) -> Dict[str, int]:
        async with self.db.transaction() as session:
            stmt = select(ProposalModel.status, func.count()).group_by(ProposalModel.status)
            rows = (await session.execute(stmt)).all()
        return {status: int(count) for status, count in rows}

    # ---------------------------------------------------------------------
    # History
    # ---------------------------------------------------------------------

    async def get_history(self, proposal_id: str) -> List[ProposalHistoryEntry]:
        async with self.db.transaction() as session:
            stmt = (
                select(ProposalHistoryModel)
                .where(ProposalHistoryModel.proposal_id == proposal_id)
                .order_by(ProposalHistoryModel.id.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()

        return [
            ProposalHistoryEntry(
                action=r.action,
                actor_id=r.actor_id,
                timestamp=r.timestamp,
                previous_status=r.previous_status,
                new_status=r.new_status,
                comment=r.comment,
            )
            for r in rows
        ]

    async def get_with_history(self, proposal_id: str) -> Tuple[Optional[Proposal], List[ProposalHistoryEntry]]:
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            return None, []
        history = await self.get_history(proposal_id)
        return proposal, history

    # ---------------------------------------------------------------------
    # Governance helpers
    # ---------------------------------------------------------------------

    async def approve(self, proposal_id: str, reviewer_id: str, comment: Optional[str] = None) -> Proposal:
        async with self.db.transaction() as session:
            model = await session.get(ProposalModel, proposal_id)
            if model is None:
                raise ProposalNotFoundError(proposal_id)

            proposal = self._to_domain(model)
            prev = proposal.status.value
            proposal.approve(reviewer_id=reviewer_id, comment=comment)

            if proposal.version != model.version + 1:
                raise OptimisticLockError(proposal_id, expected_version=model.version, actual_version=proposal.version)

            self._to_model(proposal, model=model)

        await self._append_history(
            proposal_id=proposal_id,
            action="approved",
            actor_id=reviewer_id,
            previous_status=prev,
            new_status=proposal.status.value,
            comment=comment,
        )
        return proposal

    async def reject(self, proposal_id: str, reviewer_id: str, reason: str) -> Proposal:
        async with self.db.transaction() as session:
            model = await session.get(ProposalModel, proposal_id)
            if model is None:
                raise ProposalNotFoundError(proposal_id)

            proposal = self._to_domain(model)
            prev = proposal.status.value
            proposal.reject(reviewer_id=reviewer_id, reason=reason)

            if proposal.version != model.version + 1:
                raise OptimisticLockError(proposal_id, expected_version=model.version, actual_version=proposal.version)

            self._to_model(proposal, model=model)

        await self._append_history(
            proposal_id=proposal_id,
            action="rejected",
            actor_id=reviewer_id,
            previous_status=prev,
            new_status=proposal.status.value,
            comment=reason,
        )
        return proposal

    async def execute(self, proposal_id: str, executor_id: str, result: Optional[Dict[str, Any]] = None) -> Proposal:
        async with self.db.transaction() as session:
            model = await session.get(ProposalModel, proposal_id)
            if model is None:
                raise ProposalNotFoundError(proposal_id)

            proposal = self._to_domain(model)
            prev = proposal.status.value
            proposal.execute(executor_id=executor_id, result=result)

            if proposal.version != model.version + 1:
                raise OptimisticLockError(proposal_id, expected_version=model.version, actual_version=proposal.version)

            self._to_model(proposal, model=model)

        await self._append_history(
            proposal_id=proposal_id,
            action="executed",
            actor_id=executor_id,
            previous_status=prev,
            new_status=proposal.status.value,
            comment=None,
        )
        return proposal


__all__ = [
    "OptimisticLockError",
    "PaginatedResult",
    "ProposalNotFoundError",
    "ProposalQuery",
    "ProposalRepository",
]

