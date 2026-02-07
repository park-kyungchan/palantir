"""
Tests for HITL Review Database.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy import text

from cow_cli.review import (
    ReviewDatabase,
    ReviewItem,
    AuditLog,
    ReviewerStats,
    ReviewStatus,
    ReviewDecision,
    AuditAction,
    get_database,
    configure_database,
)


class TestReviewModels:
    """Tests for review models."""

    def test_review_status_values(self):
        """Test ReviewStatus enum values."""
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.CLAIMED.value == "claimed"
        assert ReviewStatus.APPROVED.value == "approved"
        assert ReviewStatus.REJECTED.value == "rejected"
        assert ReviewStatus.MODIFIED.value == "modified"
        assert ReviewStatus.SKIPPED.value == "skipped"

    def test_review_decision_values(self):
        """Test ReviewDecision enum values."""
        assert ReviewDecision.APPROVED.value == "approved"
        assert ReviewDecision.REJECTED.value == "rejected"
        assert ReviewDecision.MODIFIED.value == "modified"
        assert ReviewDecision.SKIPPED.value == "skipped"

    def test_audit_action_values(self):
        """Test AuditAction enum values."""
        assert AuditAction.CREATED.value == "created"
        assert AuditAction.CLAIMED.value == "claimed"
        assert AuditAction.REVIEWED.value == "reviewed"
        assert AuditAction.RELEASED.value == "released"
        assert AuditAction.PRIORITY_CHANGED.value == "priority_changed"
        assert AuditAction.EXPIRED.value == "expired"


class TestReviewDatabase:
    """Tests for ReviewDatabase class."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_review.db"
            yield ReviewDatabase(db_path=db_path)

    def test_initialization(self, db):
        """Test database initialization."""
        assert db.db_path.exists()
        assert db.engine is not None

    def test_add_review_item(self, db):
        """Test adding a review item."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem-001",
            element_type="equation",
            confidence=0.65,
            reason="Low confidence",
            priority=1.5,
        )

        assert item.id is not None
        assert item.image_path == "/test/image.png"
        assert item.element_id == "elem-001"
        assert item.element_type == "equation"
        assert item.confidence == 0.65
        assert item.status == ReviewStatus.PENDING.value

    def test_add_item_with_reviewer(self, db):
        """Test adding item with pre-assigned reviewer."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem-002",
            element_type="diagram",
            reviewer="alice",
        )

        assert item.status == ReviewStatus.CLAIMED.value
        assert item.reviewer == "alice"
        assert item.claimed_at is not None

    def test_add_item_with_element_data(self, db):
        """Test adding item with element data."""
        element_data = {
            "latex": "x^2 + y^2 = r^2",
            "bbox": {"x": 10, "y": 20, "w": 100, "h": 50},
        }
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem-003",
            element_type="equation",
            element_data=element_data,
        )

        assert item.element_data is not None
        assert "latex" in item.element_data

    def test_get_review_item(self, db):
        """Test getting a review item."""
        created = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem-004",
            element_type="text",
        )

        retrieved = db.get_review_item(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.element_id == "elem-004"

    def test_get_nonexistent_item(self, db):
        """Test getting non-existent item."""
        item = db.get_review_item("nonexistent")
        assert item is None

    def test_list_review_items(self, db):
        """Test listing review items."""
        # Add multiple items
        for i in range(5):
            db.add_review_item(
                image_path=f"/test/image{i}.png",
                element_id=f"elem-{i}",
                element_type="equation" if i % 2 == 0 else "diagram",
                priority=i,
            )

        items = db.list_review_items()
        assert len(items) == 5

        # Test limit
        limited = db.list_review_items(limit=3)
        assert len(limited) == 3

    def test_list_items_by_status(self, db):
        """Test listing items filtered by status."""
        db.add_review_item(
            image_path="/test/a.png",
            element_id="a",
            element_type="text",
        )
        item2 = db.add_review_item(
            image_path="/test/b.png",
            element_id="b",
            element_type="text",
        )
        db.claim_item(item2.id, "bob")

        pending = db.list_review_items(status=ReviewStatus.PENDING.value)
        claimed = db.list_review_items(status=ReviewStatus.CLAIMED.value)

        assert len(pending) == 1
        assert len(claimed) == 1

    def test_list_items_by_type(self, db):
        """Test listing items filtered by element type."""
        db.add_review_item(
            image_path="/test/a.png",
            element_id="a",
            element_type="equation",
        )
        db.add_review_item(
            image_path="/test/b.png",
            element_id="b",
            element_type="diagram",
        )

        equations = db.list_review_items(element_type="equation")
        assert len(equations) == 1
        assert equations[0].element_type == "equation"

    def test_get_pending_items(self, db):
        """Test getting pending items."""
        db.add_review_item(
            image_path="/test/a.png",
            element_id="a",
            element_type="text",
            priority=2.0,
        )
        db.add_review_item(
            image_path="/test/b.png",
            element_id="b",
            element_type="text",
            priority=1.0,
        )

        pending = db.get_pending_items(limit=2)

        assert len(pending) == 2
        # Higher priority first
        assert pending[0].priority > pending[1].priority

    def test_claim_item(self, db):
        """Test claiming an item."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )

        claimed = db.claim_item(item.id, "alice")

        assert claimed is not None
        assert claimed.status == ReviewStatus.CLAIMED.value
        assert claimed.reviewer == "alice"
        assert claimed.claimed_at is not None

    def test_claim_already_claimed(self, db):
        """Test claiming an already claimed item."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )
        db.claim_item(item.id, "alice")

        # Try to claim again
        result = db.claim_item(item.id, "bob")
        assert result is None

    def test_release_item(self, db):
        """Test releasing a claimed item."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )
        db.claim_item(item.id, "alice")

        released = db.release_item(item.id)

        assert released is not None
        assert released.status == ReviewStatus.PENDING.value
        assert released.reviewer is None
        assert released.claimed_at is None

    def test_submit_review_approved(self, db):
        """Test submitting an approval."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )
        db.claim_item(item.id, "alice")

        reviewed = db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.APPROVED.value,
            reviewer="alice",
            comment="Looks good!",
        )

        assert reviewed is not None
        assert reviewed.status == ReviewDecision.APPROVED.value
        assert reviewed.decision == ReviewDecision.APPROVED.value
        assert reviewed.reviewed_at is not None
        assert reviewed.comment == "Looks good!"

    def test_submit_review_modified(self, db):
        """Test submitting with modifications."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="equation",
        )
        db.claim_item(item.id, "alice")

        modifications = {"latex": "x^2 + y^2 = z^2"}
        reviewed = db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.MODIFIED.value,
            reviewer="alice",
            modifications=modifications,
        )

        assert reviewed.status == ReviewDecision.MODIFIED.value
        assert reviewed.modifications is not None

    def test_update_priority(self, db):
        """Test updating item priority."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
            priority=1.0,
        )

        updated = db.update_priority(item.id, 5.0, actor="system")

        assert updated is not None
        assert updated.priority == 5.0

    def test_delete_item(self, db):
        """Test deleting an item."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )

        deleted = db.delete_item(item.id)
        assert deleted is True

        # Verify deleted
        assert db.get_review_item(item.id) is None

    def test_delete_nonexistent(self, db):
        """Test deleting non-existent item."""
        deleted = db.delete_item("nonexistent")
        assert deleted is False


class TestQueueStatistics:
    """Tests for queue statistics."""

    @pytest.fixture
    def db_with_data(self):
        """Create database with test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_stats.db"
            db = ReviewDatabase(db_path=db_path)

            # Add items with different statuses
            item1 = db.add_review_item(
                image_path="/test/a.png",
                element_id="a",
                element_type="text",
                confidence=0.5,
            )
            item2 = db.add_review_item(
                image_path="/test/b.png",
                element_id="b",
                element_type="text",
                confidence=0.6,
            )
            item3 = db.add_review_item(
                image_path="/test/c.png",
                element_id="c",
                element_type="text",
            )

            # Claim and review some
            db.claim_item(item2.id, "alice")
            db.submit_review(item3.id, ReviewDecision.APPROVED.value, "bob")

            yield db

    def test_queue_stats(self, db_with_data):
        """Test queue statistics."""
        stats = db_with_data.get_queue_stats()

        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["claimed"] == 1
        assert stats["approved"] == 1
        assert stats["reviewed"] == 1

    def test_avg_confidence(self, db_with_data):
        """Test average pending confidence."""
        stats = db_with_data.get_queue_stats()
        # Only pending item has confidence 0.5
        assert stats["avg_pending_confidence"] == 0.5


class TestReviewerStatistics:
    """Tests for reviewer statistics."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_reviewer.db"
            yield ReviewDatabase(db_path=db_path)

    def test_reviewer_stats_created(self, db):
        """Test that reviewer stats are created on review."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )
        db.claim_item(item.id, "alice")
        db.submit_review(item.id, ReviewDecision.APPROVED.value, "alice")

        stats = db.get_reviewer_stats("alice")

        assert stats is not None
        assert stats.reviewer == "alice"
        assert stats.total_reviews == 1
        assert stats.approved == 1

    def test_reviewer_stats_accumulate(self, db):
        """Test stats accumulation across reviews."""
        for i, decision in enumerate([
            ReviewDecision.APPROVED,
            ReviewDecision.APPROVED,
            ReviewDecision.REJECTED,
            ReviewDecision.MODIFIED,
        ]):
            item = db.add_review_item(
                image_path=f"/test/{i}.png",
                element_id=f"e{i}",
                element_type="text",
            )
            db.claim_item(item.id, "alice")
            db.submit_review(item.id, decision.value, "alice")

        stats = db.get_reviewer_stats("alice")

        assert stats.total_reviews == 4
        assert stats.approved == 2
        assert stats.rejected == 1
        assert stats.modified == 1
        assert stats.approval_rate == 0.5

    def test_get_all_reviewer_stats(self, db):
        """Test getting all reviewer stats."""
        # Alice reviews
        item1 = db.add_review_item(
            image_path="/test/a.png",
            element_id="a",
            element_type="text",
        )
        db.submit_review(item1.id, ReviewDecision.APPROVED.value, "alice")

        # Bob reviews
        item2 = db.add_review_item(
            image_path="/test/b.png",
            element_id="b",
            element_type="text",
        )
        db.submit_review(item2.id, ReviewDecision.APPROVED.value, "bob")

        all_stats = db.get_all_reviewer_stats()

        assert len(all_stats) == 2


class TestAuditLogs:
    """Tests for audit logging."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_audit.db"
            yield ReviewDatabase(db_path=db_path)

    def test_create_audit_log(self, db):
        """Test audit log on item creation."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )

        logs = db.get_audit_logs(item_id=item.id)

        assert len(logs) == 1
        assert logs[0].action == AuditAction.CREATED.value

    def test_claim_audit_log(self, db):
        """Test audit log on claim."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )
        db.claim_item(item.id, "alice")

        logs = db.get_audit_logs(item_id=item.id)

        assert len(logs) == 2
        actions = [log.action for log in logs]
        assert AuditAction.CLAIMED.value in actions

    def test_review_audit_log(self, db):
        """Test audit log on review."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )
        db.submit_review(item.id, ReviewDecision.APPROVED.value, "alice")

        logs = db.get_audit_logs(item_id=item.id)

        actions = [log.action for log in logs]
        assert AuditAction.REVIEWED.value in actions

    def test_filter_logs_by_actor(self, db):
        """Test filtering audit logs by actor."""
        item1 = db.add_review_item(
            image_path="/test/a.png",
            element_id="a",
            element_type="text",
        )
        item2 = db.add_review_item(
            image_path="/test/b.png",
            element_id="b",
            element_type="text",
        )

        db.claim_item(item1.id, "alice")
        db.claim_item(item2.id, "bob")

        alice_logs = db.get_audit_logs(actor="alice")
        bob_logs = db.get_audit_logs(actor="bob")

        assert len(alice_logs) == 1
        assert len(bob_logs) == 1


class TestMaintenance:
    """Tests for maintenance operations."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_maintenance.db"
            yield ReviewDatabase(db_path=db_path)

    def test_expire_stale_claims(self, db):
        """Test expiring stale claims."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )
        db.claim_item(item.id, "alice")

        # Manually set claimed_at to past
        with db.session() as session:
            session.execute(
                text(f"UPDATE review_items SET claimed_at = datetime('now', '-2 hours') WHERE id = '{item.id}'")
            )

        expired = db.expire_stale_claims(max_age_minutes=60)

        assert expired == 1

        # Check item is now pending
        updated = db.get_review_item(item.id)
        assert updated.status == ReviewStatus.PENDING.value

    def test_vacuum(self, db):
        """Test database vacuum."""
        # Just verify it doesn't raise
        db.vacuum()


class TestReviewItemMethods:
    """Tests for ReviewItem model methods."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_item.db"
            yield ReviewDatabase(db_path=db_path)

    def test_to_dict(self, db):
        """Test item to_dict."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="equation",
            confidence=0.7,
        )

        d = item.to_dict()

        assert d["id"] == item.id
        assert d["image_path"] == "/test/image.png"
        assert d["element_id"] == "elem"
        assert d["element_type"] == "equation"
        assert d["confidence"] == 0.7
        assert d["status"] == "pending"
        assert "created_at" in d

    def test_is_pending(self, db):
        """Test is_pending property."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )

        assert item.is_pending is True

        db.claim_item(item.id, "alice")
        updated = db.get_review_item(item.id)
        assert updated.is_pending is False

    def test_is_claimed(self, db):
        """Test is_claimed property."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )

        assert item.is_claimed is False

        db.claim_item(item.id, "alice")
        updated = db.get_review_item(item.id)
        assert updated.is_claimed is True

    def test_is_reviewed(self, db):
        """Test is_reviewed property."""
        item = db.add_review_item(
            image_path="/test/image.png",
            element_id="elem",
            element_type="text",
        )

        assert item.is_reviewed is False

        db.submit_review(item.id, ReviewDecision.APPROVED.value, "alice")
        updated = db.get_review_item(item.id)
        assert updated.is_reviewed is True


class TestGlobalFunctions:
    """Tests for global database functions."""

    def test_configure_database(self):
        """Test configure_database function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "global_test.db"
            db = configure_database(db_path)

            assert db.db_path == db_path
            assert db_path.exists()
