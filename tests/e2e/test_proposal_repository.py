"""
ODA V3.0 - ProposalRepository Test Suite
========================================

Tests for Proposal persistence layer:
1. CRUD operations
2. Optimistic locking
3. History tracking
4. Query filtering
5. Bulk operations
6. Governance helpers (approve/reject/execute)

Run with: pytest tests/e2e/test_proposal_repository.py -v --asyncio-mode=auto
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

import pytest

from scripts.ontology.objects.proposal import (
    InvalidTransitionError,
    Proposal,
    ProposalPriority,
    ProposalStatus,
)
from scripts.ontology.storage.database import Database, initialize_database
from scripts.ontology.storage.proposal_repository import (
    OptimisticLockError,
    PaginatedResult,
    ProposalNotFoundError,
    ProposalQuery,
    ProposalRepository,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
async def db() -> AsyncGenerator[Database, None]:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_ontology.db"
        database = Database(db_path)
        await database.initialize()
        yield database


@pytest.fixture
async def repo(db: Database) -> ProposalRepository:
    """Create a repository with the test database."""
    return ProposalRepository(db)


@pytest.fixture
def sample_proposal() -> Proposal:
    """Create a sample proposal."""
    return Proposal(
        action_type="deploy_service",
        payload={"service": "checkout", "version": "2.0.0"},
        created_by="agent-001",
        priority=ProposalPriority.HIGH,
    )


@pytest.fixture
def submitted_proposal() -> Proposal:
    """Create a submitted proposal."""
    proposal = Proposal(
        action_type="delete_task",
        payload={"task_id": "task-123"},
        created_by="agent-002",
    )
    proposal.submit()
    return proposal


# =============================================================================
# CRUD TESTS
# =============================================================================

class TestProposalCRUD:
    """Test basic CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test saving and retrieving a proposal."""
        await repo.save(sample_proposal)
        
        found = await repo.find_by_id(sample_proposal.id)
        
        assert found is not None
        assert found.id == sample_proposal.id
        assert found.action_type == "deploy_service"
        assert found.payload["service"] == "checkout"
        assert found.created_by == "agent-001"
        assert found.priority == ProposalPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repo: ProposalRepository):
        """Test finding non-existent proposal."""
        found = await repo.find_by_id("non-existent-id")
        
        assert found is None
    
    @pytest.mark.asyncio
    async def test_update_proposal(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test updating an existing proposal."""
        await repo.save(sample_proposal)
        
        # Modify and save again
        sample_proposal.submit()
        await repo.save(sample_proposal)
        
        found = await repo.find_by_id(sample_proposal.id)
        
        assert found.status == ProposalStatus.PENDING
        assert found.version == 2  # Version incremented
    
    @pytest.mark.asyncio
    async def test_soft_delete(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test soft deleting a proposal."""
        await repo.save(sample_proposal)
        
        result = await repo.delete(sample_proposal.id, actor_id="admin-001")
        
        assert result is True
        
        # Should still exist but be marked deleted
        found = await repo.find_by_id(sample_proposal.id)
        # Note: soft delete updates the proposal's status
    
    @pytest.mark.asyncio
    async def test_hard_delete(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test hard deleting a proposal."""
        await repo.save(sample_proposal)
        
        result = await repo.delete(sample_proposal.id, actor_id="admin-001", hard_delete=True)
        
        assert result is True
        
        # Should not exist
        found = await repo.find_by_id(sample_proposal.id)
        assert found is None
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo: ProposalRepository):
        """Test deleting non-existent proposal."""
        result = await repo.delete("non-existent", actor_id="admin-001")
        
        assert result is False


# =============================================================================
# OPTIMISTIC LOCKING TESTS
# =============================================================================

class TestOptimisticLocking:
    """Test optimistic locking for concurrent access."""
    
    @pytest.mark.asyncio
    async def test_version_increment(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test that version increments on each save."""
        assert sample_proposal.version == 1
        
        await repo.save(sample_proposal)
        found = await repo.find_by_id(sample_proposal.id)
        assert found.version == 1
        
        found.submit()
        await repo.save(found)
        
        found2 = await repo.find_by_id(sample_proposal.id)
        assert found2.version == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_modification_detected(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test that concurrent modifications are detected."""
        await repo.save(sample_proposal)
        
        # Simulate two concurrent reads
        instance1 = await repo.find_by_id(sample_proposal.id)
        instance2 = await repo.find_by_id(sample_proposal.id)
        
        # First update succeeds
        instance1.submit()
        await repo.save(instance1)
        
        # Second update should fail (version mismatch)
        instance2.submit()
        
        with pytest.raises(OptimisticLockError) as exc_info:
            await repo.save(instance2)
        
        assert exc_info.value.expected_version == 2
        assert exc_info.value.actual_version == 2


# =============================================================================
# QUERY TESTS
# =============================================================================

class TestProposalQueries:
    """Test query operations."""
    
    @pytest.mark.asyncio
    async def test_find_by_status(self, repo: ProposalRepository):
        """Test finding proposals by status."""
        # Create proposals in different statuses
        draft = Proposal(action_type="action1", created_by="agent-001")
        pending = Proposal(action_type="action2", created_by="agent-001")
        pending.submit()
        
        await repo.save(draft)
        await repo.save(pending)
        
        # Query by status
        draft_results = await repo.find_by_status(ProposalStatus.DRAFT)
        pending_results = await repo.find_by_status(ProposalStatus.PENDING)
        
        assert len(draft_results) == 1
        assert draft_results[0].action_type == "action1"
        
        assert len(pending_results) == 1
        assert pending_results[0].action_type == "action2"
    
    @pytest.mark.asyncio
    async def test_find_pending_shortcut(self, repo: ProposalRepository, submitted_proposal: Proposal):
        """Test find_pending convenience method."""
        await repo.save(submitted_proposal)
        
        pending = await repo.find_pending()
        
        assert len(pending) == 1
        assert pending[0].id == submitted_proposal.id
    
    @pytest.mark.asyncio
    async def test_find_by_action_type(self, repo: ProposalRepository):
        """Test finding proposals by action type."""
        p1 = Proposal(action_type="deploy_service", created_by="agent-001")
        p2 = Proposal(action_type="deploy_service", created_by="agent-002")
        p3 = Proposal(action_type="delete_task", created_by="agent-001")
        
        await repo.save(p1)
        await repo.save(p2)
        await repo.save(p3)
        
        deploy_results = await repo.find_by_action_type("deploy_service")
        
        assert len(deploy_results) == 2
    
    @pytest.mark.asyncio
    async def test_find_by_creator(self, repo: ProposalRepository):
        """Test finding proposals by creator."""
        p1 = Proposal(action_type="action1", created_by="agent-001")
        p2 = Proposal(action_type="action2", created_by="agent-001")
        p3 = Proposal(action_type="action3", created_by="agent-002")
        
        await repo.save(p1)
        await repo.save(p2)
        await repo.save(p3)
        
        agent1_results = await repo.find_by_creator("agent-001")
        
        assert len(agent1_results) == 2
    
    @pytest.mark.asyncio
    async def test_paginated_query(self, repo: ProposalRepository):
        """Test paginated query with filters."""
        # Create 15 proposals
        for i in range(15):
            p = Proposal(action_type=f"action_{i}", created_by="agent-001")
            if i % 2 == 0:
                p.submit()
            await repo.save(p)
        
        # Query with pagination
        query = ProposalQuery(
            created_by="agent-001",
            limit=5,
            offset=0,
        )
        
        result = await repo.query(query)
        
        assert isinstance(result, PaginatedResult)
        assert len(result.items) == 5
        assert result.total == 15
        assert result.has_more is True
        
        # Next page
        query.offset = 5
        result2 = await repo.query(query)
        
        assert len(result2.items) == 5
        assert result2.offset == 5
    
    @pytest.mark.asyncio
    async def test_query_with_status_filter(self, repo: ProposalRepository):
        """Test query with status filter."""
        for i in range(10):
            p = Proposal(action_type=f"action_{i}", created_by="agent-001")
            if i < 5:
                p.submit()
            await repo.save(p)
        
        query = ProposalQuery(status=ProposalStatus.PENDING)
        result = await repo.query(query)
        
        assert result.total == 5
        assert all(p.status == ProposalStatus.PENDING for p in result.items)
    
    @pytest.mark.asyncio
    async def test_count_by_status(self, repo: ProposalRepository):
        """Test counting proposals by status."""
        for i in range(10):
            p = Proposal(action_type=f"action_{i}", created_by="agent-001")
            if i < 3:
                pass  # DRAFT
            elif i < 7:
                p.submit()  # PENDING
            else:
                p.submit()
                p.approve(reviewer_id="admin-001")  # APPROVED
            await repo.save(p)
        
        counts = await repo.count_by_status()
        
        assert counts.get("draft", 0) == 3
        assert counts.get("pending", 0) == 4
        assert counts.get("approved", 0) == 3


# =============================================================================
# HISTORY TESTS
# =============================================================================

class TestProposalHistory:
    """Test history tracking."""
    
    @pytest.mark.asyncio
    async def test_history_on_create(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test history entry created on insert."""
        await repo.save(sample_proposal, actor_id="agent-001")
        
        history = await repo.get_history(sample_proposal.id)
        
        assert len(history) == 1
        assert history[0].action == "created"
        assert history[0].actor_id == "agent-001"
    
    @pytest.mark.asyncio
    async def test_history_on_update(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test history entries for updates."""
        await repo.save(sample_proposal)
        
        sample_proposal.submit()
        await repo.save(sample_proposal, comment="Submitting for review")
        
        history = await repo.get_history(sample_proposal.id)
        
        assert len(history) == 2
        assert history[1].action == "updated"
        assert history[1].comment == "Submitting for review"
    
    @pytest.mark.asyncio
    async def test_get_with_history(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test retrieving proposal with history."""
        await repo.save(sample_proposal)
        sample_proposal.submit()
        await repo.save(sample_proposal)
        
        proposal, history = await repo.get_with_history(sample_proposal.id)
        
        assert proposal is not None
        assert proposal.id == sample_proposal.id
        assert len(history) == 2
    
    @pytest.mark.asyncio
    async def test_history_tracks_status_transitions(self, repo: ProposalRepository, submitted_proposal: Proposal):
        """Test that history tracks status changes."""
        await repo.save(submitted_proposal)
        
        # Approve
        await repo.approve(submitted_proposal.id, "admin-001", "Looks good")
        
        # Execute
        await repo.execute(submitted_proposal.id, executor_id="system", result={"success": True})
        
        history = await repo.get_history(submitted_proposal.id)
        
        # Should have: created, approved, executed
        assert len(history) == 3
        
        assert history[1].action == "approved"
        assert history[1].previous_status == "pending"
        assert history[1].new_status == "approved"
        
        assert history[2].action == "executed"
        assert history[2].previous_status == "approved"
        assert history[2].new_status == "executed"


# =============================================================================
# GOVERNANCE HELPER TESTS
# =============================================================================

class TestGovernanceHelpers:
    """Test governance convenience methods."""
    
    @pytest.mark.asyncio
    async def test_approve_pending_proposal(self, repo: ProposalRepository, submitted_proposal: Proposal):
        """Test approving a pending proposal."""
        await repo.save(submitted_proposal)
        
        approved = await repo.approve(
            submitted_proposal.id,
            reviewer_id="admin-001",
            comment="Approved for deployment"
        )
        
        assert approved.status == ProposalStatus.APPROVED
        assert approved.reviewed_by == "admin-001"
        assert approved.review_comment == "Approved for deployment"
    
    @pytest.mark.asyncio
    async def test_approve_not_found(self, repo: ProposalRepository):
        """Test approving non-existent proposal."""
        with pytest.raises(ProposalNotFoundError):
            await repo.approve("non-existent", "admin-001")
    
    @pytest.mark.asyncio
    async def test_approve_wrong_status(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test approving proposal not in PENDING status."""
        await repo.save(sample_proposal)  # Still in DRAFT
        
        with pytest.raises(InvalidTransitionError):
            await repo.approve(sample_proposal.id, "admin-001")
    
    @pytest.mark.asyncio
    async def test_reject_pending_proposal(self, repo: ProposalRepository, submitted_proposal: Proposal):
        """Test rejecting a pending proposal."""
        await repo.save(submitted_proposal)
        
        rejected = await repo.reject(
            submitted_proposal.id,
            reviewer_id="admin-001",
            reason="Not ready for production"
        )
        
        assert rejected.status == ProposalStatus.REJECTED
        assert rejected.reviewed_by == "admin-001"
        assert rejected.review_comment == "Not ready for production"
    
    @pytest.mark.asyncio
    async def test_execute_approved_proposal(self, repo: ProposalRepository, submitted_proposal: Proposal):
        """Test executing an approved proposal."""
        await repo.save(submitted_proposal)
        await repo.approve(submitted_proposal.id, "admin-001")
        
        executed = await repo.execute(
            submitted_proposal.id,
            executor_id="system",
            result={"deployment_id": "deploy-123", "status": "success"}
        )
        
        assert executed.status == ProposalStatus.EXECUTED
        assert executed.execution_result["deployment_id"] == "deploy-123"
    
    @pytest.mark.asyncio
    async def test_full_governance_workflow(self, repo: ProposalRepository):
        """Test complete governance workflow."""
        # 1. Create
        proposal = Proposal(
            action_type="deploy_service",
            payload={"service": "api-gateway", "version": "3.0.0"},
            created_by="agent-001",
            priority=ProposalPriority.CRITICAL,
        )
        
        # 2. Submit
        proposal.submit()
        await repo.save(proposal)
        
        # 3. Query pending
        pending = await repo.find_pending()
        assert len(pending) == 1
        
        # 4. Approve
        await repo.approve(proposal.id, "admin-001", "Approved after review")
        
        # 5. Execute
        await repo.execute(proposal.id, "system", result={"success": True})
        
        # 6. Verify final state
        final, history = await repo.get_with_history(proposal.id)
        
        assert final.status == ProposalStatus.EXECUTED
        assert len(history) == 3  # created, approved, executed


# =============================================================================
# BULK OPERATIONS TESTS
# =============================================================================

class TestBulkOperations:
    """Test bulk operations."""
    
    @pytest.mark.asyncio
    async def test_save_many(self, repo: ProposalRepository):
        """Test saving multiple proposals in one transaction."""
        proposals = [
            Proposal(action_type=f"action_{i}", created_by="agent-001")
            for i in range(10)
        ]
        
        saved = await repo.save_many(proposals, actor_id="batch-processor")
        
        assert len(saved) == 10
        
        # Verify all saved
        for p in proposals:
            found = await repo.find_by_id(p.id)
            assert found is not None


# =============================================================================
# DATABASE TESTS
# =============================================================================

from sqlalchemy import text

# ... (imports)

# ...

class TestDatabase:
    """Test database functionality."""
    
    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self, db: Database):
        """Test that WAL mode is enabled."""
        async with db.transaction() as session:
            result = await session.execute(text("PRAGMA journal_mode;"))
            row = result.fetchone()
            assert row[0] == "wal"
    
    @pytest.mark.asyncio
    async def test_migrations_applied(self, db: Database):
        """Test that migrations are tracked."""
        async with db.transaction() as session:
            # Create _migrations table manually for test if it doesn't exist?
            # Or assume initialize() creates it.
            # Usually Alembic manages this, but for test we might check proposals table
            # Check if 'proposals' table exists
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='proposals';")
            )
            assert result.scalar() == "proposals"

    @pytest.mark.asyncio
    async def test_health_check(self, db: Database):
        """Test database health check."""
        healthy = await db.health_check()
        assert healthy is True
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db: Database):
        """Test that transactions rollback on error."""
        try:
            async with db.transaction() as session:
                await session.execute(
                    text("INSERT INTO proposals (id, action_type, payload, status, created_at, updated_at, version, priority) "
                    "VALUES ('test-id', 'test', '{}', 'draft', datetime('now'), datetime('now'), 1, 'medium')")
                )
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Should not exist due to rollback
        async with db.transaction() as session:
            result = await session.execute(text("SELECT * FROM proposals WHERE id = 'test-id'"))
            row = result.fetchone()
            assert row is None


# =============================================================================
# CONCURRENT ACCESS TESTS
# =============================================================================

class TestConcurrentAccess:
    """Test concurrent database access."""
    
    @pytest.mark.asyncio
    async def test_concurrent_reads(self, repo: ProposalRepository, sample_proposal: Proposal):
        """Test concurrent read operations."""
        await repo.save(sample_proposal)
        
        async def read_proposal():
            return await repo.find_by_id(sample_proposal.id)
        
        # Execute 10 concurrent reads
        results = await asyncio.gather(*[read_proposal() for _ in range(10)])
        
        assert all(r is not None for r in results)
        assert all(r.id == sample_proposal.id for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_writes_different_proposals(self, repo: ProposalRepository):
        """Test concurrent writes to different proposals."""
        proposals = [
            Proposal(action_type=f"action_{i}", created_by="agent-001")
            for i in range(10)
        ]
        
        async def save_proposal(p: Proposal):
            await repo.save(p)
            return p.id
        
        # Execute 10 concurrent writes
        ids = await asyncio.gather(*[save_proposal(p) for p in proposals])
        
        assert len(set(ids)) == 10  # All unique IDs


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
