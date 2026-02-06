"""
Tests for Review CLI Commands.
"""
import pytest
import tempfile
from pathlib import Path
from typer.testing import CliRunner

from cow_cli.commands.review import app
from cow_cli.review import configure_database, ReviewDatabase


runner = CliRunner()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_review.db"
        db = configure_database(db_path)
        yield db


@pytest.fixture
def db_with_items(temp_db):
    """Create database with test items."""
    # Add some test items
    temp_db.add_review_item(
        image_path="/test/image1.png",
        element_id="elem-001",
        element_type="equation",
        confidence=0.85,
        reason="Low confidence",
        priority=50.0,
    )
    temp_db.add_review_item(
        image_path="/test/image2.png",
        element_id="elem-002",
        element_type="diagram",
        confidence=0.70,
        reason="Complex diagram",
        priority=75.0,
    )
    temp_db.add_review_item(
        image_path="/test/image3.png",
        element_id="elem-003",
        element_type="text",
        confidence=0.95,
        reason="Review needed",
        priority=10.0,
    )
    yield temp_db


class TestListCommand:
    """Tests for review list command."""

    def test_list_empty(self, temp_db):
        """Test listing empty database."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No review items found" in result.stdout

    def test_list_items(self, db_with_items):
        """Test listing items."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "equation" in result.stdout
        assert "diagram" in result.stdout
        assert "text" in result.stdout

    def test_list_with_limit(self, db_with_items):
        """Test listing with limit."""
        result = runner.invoke(app, ["list", "--limit", "2"])
        assert result.exit_code == 0
        # Should show only 2 items (highest priority first)

    def test_list_filter_by_type(self, db_with_items):
        """Test filtering by element type."""
        result = runner.invoke(app, ["list", "--type", "equation"])
        assert result.exit_code == 0
        assert "equation" in result.stdout

    def test_list_json_output(self, db_with_items):
        """Test JSON output format."""
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        assert "[" in result.stdout  # JSON array

    def test_list_filter_by_confidence(self, db_with_items):
        """Test filtering by confidence threshold."""
        result = runner.invoke(app, ["list", "--confidence-below", "0.80"])
        assert result.exit_code == 0
        # Should only show items with confidence < 0.80


class TestShowCommand:
    """Tests for review show command."""

    def test_show_item(self, db_with_items):
        """Test showing item details."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, ["show", item_id])
        assert result.exit_code == 0
        assert item_id in result.stdout
        assert "Confidence" in result.stdout

    def test_show_item_not_found(self, temp_db):
        """Test showing non-existent item."""
        result = runner.invoke(app, ["show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_show_json_output(self, db_with_items):
        """Test JSON output format."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, ["show", item_id, "--json"])
        assert result.exit_code == 0
        assert "{" in result.stdout  # JSON object


class TestApproveCommand:
    """Tests for review approve command."""

    def test_approve_item(self, db_with_items):
        """Test approving an item."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, ["approve", item_id])
        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()

        # Verify status changed
        item = db_with_items.get_review_item(item_id)
        assert item.status == "approved"

    def test_approve_with_comment(self, db_with_items):
        """Test approving with comment."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, [
            "approve", item_id,
            "--comment", "Verified correct",
        ])
        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()

    def test_approve_not_found(self, temp_db):
        """Test approving non-existent item."""
        result = runner.invoke(app, ["approve", "nonexistent"])
        assert result.exit_code == 1


class TestRejectCommand:
    """Tests for review reject command."""

    def test_reject_item(self, db_with_items):
        """Test rejecting an item."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, [
            "reject", item_id,
            "--reason", "Illegible content",
        ])
        assert result.exit_code == 0
        assert "rejected" in result.stdout.lower()

        # Verify status changed
        item = db_with_items.get_review_item(item_id)
        assert item.status == "rejected"


class TestModifyCommand:
    """Tests for review modify command."""

    def test_modify_item(self, db_with_items):
        """Test modifying an item."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, [
            "modify", item_id,
            "--field", "latex_content",
            "--value", "x^2 + y^2 = z^2",
        ])
        assert result.exit_code == 0
        assert "modified" in result.stdout.lower()

        # Verify status changed
        item = db_with_items.get_review_item(item_id)
        assert item.status == "modified"


class TestClaimReleaseCommands:
    """Tests for claim and release commands."""

    def test_claim_item(self, db_with_items):
        """Test claiming an item."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, [
            "claim", item_id,
            "--reviewer", "tester",
        ])
        assert result.exit_code == 0
        assert "claimed" in result.stdout.lower()

        # Verify claimed
        item = db_with_items.get_review_item(item_id)
        assert item.status == "claimed"
        assert item.reviewer == "tester"

    def test_release_item(self, db_with_items):
        """Test releasing a claimed item."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        # First claim
        db_with_items.claim_item(item_id, "tester")

        # Then release
        result = runner.invoke(app, ["release", item_id])
        assert result.exit_code == 0
        assert "released" in result.stdout.lower()

        # Verify released
        item = db_with_items.get_review_item(item_id)
        assert item.status == "pending"


class TestStatsCommand:
    """Tests for review stats command."""

    def test_stats_empty(self, temp_db):
        """Test stats with empty database."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Queue Statistics" in result.stdout

    def test_stats_with_items(self, db_with_items):
        """Test stats with items."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Total Items" in result.stdout
        assert "3" in result.stdout  # 3 items added

    def test_stats_json_output(self, db_with_items):
        """Test JSON output format."""
        result = runner.invoke(app, ["stats", "--json"])
        assert result.exit_code == 0
        assert "{" in result.stdout  # JSON object


class TestAddCommand:
    """Tests for review add command."""

    def test_add_item(self, temp_db):
        """Test adding an item."""
        result = runner.invoke(app, [
            "add", "/test/new.png",
            "--element-id", "new-001",
            "--type", "math",
            "--confidence", "0.75",
        ])
        assert result.exit_code == 0
        assert "Added review item" in result.stdout

    def test_add_with_priority(self, temp_db):
        """Test adding with priority."""
        result = runner.invoke(app, [
            "add", "/test/new.png",
            "--element-id", "new-002",
            "--priority", "100.0",
        ])
        assert result.exit_code == 0


class TestDeleteCommand:
    """Tests for review delete command."""

    def test_delete_item_force(self, db_with_items):
        """Test deleting an item with force."""
        items = db_with_items.list_review_items(limit=1)
        item_id = items[0].id

        result = runner.invoke(app, ["delete", item_id, "--force"])
        assert result.exit_code == 0
        assert "Deleted" in result.stdout

        # Verify deleted
        assert db_with_items.get_review_item(item_id) is None

    def test_delete_not_found(self, temp_db):
        """Test deleting non-existent item."""
        result = runner.invoke(app, ["delete", "nonexistent", "--force"])
        assert result.exit_code == 1


class TestExpireCommand:
    """Tests for review expire command."""

    def test_expire_no_stale(self, db_with_items):
        """Test expire with no stale claims."""
        result = runner.invoke(app, ["expire"])
        assert result.exit_code == 0
        assert "No stale claims" in result.stdout
