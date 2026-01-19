from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text

from lib.oda.ontology.objects.proposal import Proposal, ProposalPriority, ProposalStatus
from lib.oda.ontology.schemas.memory import InsightContent, InsightProvenance, OrionInsight
from lib.oda.ontology.storage.database import Database
from lib.oda.ontology.storage.proposal_repository import ProposalRepository
from lib.oda.ontology.storage.repositories import InsightRepository


@pytest.mark.asyncio
async def test_database_initialize_health_and_pragmas() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / "e2e_storage.db")
        await db.initialize()
        try:
            assert await db.health_check() is True

            async with db.transaction() as session:
                journal_mode = (await session.execute(text("PRAGMA journal_mode;"))).scalar_one()
                foreign_keys = (await session.execute(text("PRAGMA foreign_keys;"))).scalar_one()

            # journal_mode can be "wal" (preferred) or "memory" depending on SQLite build,
            # but our initializer requests WAL and tests depend on concurrency safety.
            assert str(journal_mode).lower() in {"wal", "memory"}
            assert int(foreign_keys) == 1
        finally:
            await db.dispose()


@pytest.mark.asyncio
async def test_proposal_repository_roundtrip_with_history() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / "e2e_proposals.db")
        await db.initialize()
        try:
            repo = ProposalRepository(db)

            proposal = Proposal(
                id=f"PROP-{uuid4()}",
                action_type="file.read",
                payload={"file_path": "/tmp/example.txt"},
                created_by="agent-1",
                priority=ProposalPriority.HIGH,
                status=ProposalStatus.DRAFT,
            )
            proposal.submit(submitter_id="agent-1")

            await repo.save(proposal, actor_id="agent-1")

            loaded, history = await repo.get_with_history(proposal.id)
            assert loaded is not None
            assert loaded.id == proposal.id
            assert [h.action for h in history] == ["created"]

            await repo.approve(proposal.id, reviewer_id="reviewer-1", comment="LGTM")
            await repo.execute(proposal.id, executor_id="executor-1", result={"success": True})

            loaded, history = await repo.get_with_history(proposal.id)
            assert loaded is not None
            assert loaded.status == ProposalStatus.EXECUTED
            assert [h.action for h in history][-2:] == ["approved", "executed"]
        finally:
            await db.dispose()


@pytest.mark.asyncio
async def test_insight_repository_participates_in_open_transaction() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(Path(tmpdir) / "e2e_insights.db")
        await db.initialize()
        try:
            repo = InsightRepository(db)
            insight = OrionInsight(
                id=f"INS-{uuid4()}",
                confidence_score=0.9,
                provenance=InsightProvenance(source_episodic_ids=[], method="e2e"),
                content=InsightContent(summary="hello", domain="test", tags=["e2e"]),
            )

            async with db.transaction() as session:
                await repo.save(insight, actor_id="tester")
                found = await repo.find_by_id(insight.id)

            assert found is not None
            assert found.id == insight.id
        finally:
            await db.dispose()
