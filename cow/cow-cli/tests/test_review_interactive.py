"""
Tests for Interactive Review TUI.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from cow_cli.commands.review_interactive import (
    ReviewSession,
    InteractiveReviewer,
    run_interactive_review,
)
from cow_cli.review import configure_database, ReviewStatus


class TestReviewSession:
    """Tests for ReviewSession dataclass."""

    def test_initial_state(self):
        """Test initial session state."""
        session = ReviewSession(reviewer="tester")

        assert session.items_reviewed == 0
        assert session.approved == 0
        assert session.rejected == 0
        assert session.modified == 0
        assert session.skipped == 0
        assert session.reviewer == "tester"

    def test_elapsed_seconds(self):
        """Test elapsed time calculation."""
        session = ReviewSession()
        # Just check it returns a reasonable value
        assert session.elapsed_seconds >= 0

    def test_avg_time_per_item_no_items(self):
        """Test average time with no items."""
        session = ReviewSession()
        assert session.avg_time_per_item == 0.0

    def test_avg_time_per_item_with_items(self):
        """Test average time calculation."""
        session = ReviewSession()
        session.items_reviewed = 10
        # avg_time should be elapsed_seconds / 10
        avg = session.avg_time_per_item
        assert avg >= 0

    def test_approval_rate_no_items(self):
        """Test approval rate with no items."""
        session = ReviewSession()
        assert session.approval_rate == 0.0

    def test_approval_rate_with_items(self):
        """Test approval rate calculation."""
        session = ReviewSession()
        session.items_reviewed = 10
        session.approved = 7
        assert session.approval_rate == 0.7

    def test_to_table(self):
        """Test table generation."""
        session = ReviewSession(reviewer="tester")
        session.items_reviewed = 5
        session.approved = 3
        session.rejected = 1
        session.modified = 1

        table = session.to_table()

        assert table is not None
        # Table should have rows
        assert len(table.rows) > 0


class TestInteractiveReviewer:
    """Tests for InteractiveReviewer class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_tui.db"
            db = configure_database(db_path)
            yield db

    @pytest.fixture
    def db_with_items(self, temp_db):
        """Create database with test items."""
        temp_db.add_review_item(
            image_path="/test/img1.png",
            element_id="e1",
            element_type="equation",
            confidence=0.85,
            priority=50.0,
        )
        temp_db.add_review_item(
            image_path="/test/img2.png",
            element_id="e2",
            element_type="diagram",
            confidence=0.70,
            priority=75.0,
        )
        return temp_db

    def test_initialization(self, temp_db):
        """Test reviewer initialization."""
        reviewer = InteractiveReviewer(
            db=temp_db,
            reviewer="tester",
        )

        assert reviewer.db is temp_db
        assert reviewer.reviewer == "tester"
        assert reviewer.running is True
        assert reviewer.current_index == 0

    def test_load_items(self, db_with_items):
        """Test loading pending items."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        assert len(reviewer.items) == 2

    def test_load_items_with_type_filter(self, db_with_items):
        """Test loading with type filter."""
        reviewer = InteractiveReviewer(
            db=db_with_items,
            element_type="equation",
        )
        reviewer.load_items()

        # Should only get equation type
        assert all(item.element_type == "equation" for item in reviewer.items)

    def test_current_item(self, db_with_items):
        """Test current item property."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        assert reviewer.current_item is not None
        assert reviewer.current_item.element_id in ["e1", "e2"]

    def test_current_item_empty(self, temp_db):
        """Test current item when empty."""
        reviewer = InteractiveReviewer(db=temp_db)
        reviewer.load_items()

        assert reviewer.current_item is None

    def test_items_remaining(self, db_with_items):
        """Test items remaining count."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        assert reviewer.items_remaining == 2

        reviewer.current_index = 1
        assert reviewer.items_remaining == 1

    def test_handle_key_quit(self, db_with_items):
        """Test quit key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        result = reviewer.handle_key('q')

        assert result is False
        assert reviewer.running is False

    def test_handle_key_approve(self, db_with_items):
        """Test approve key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        initial_count = len(reviewer.items)
        reviewer.handle_key('a')

        assert reviewer.session.approved == 1
        assert reviewer.session.items_reviewed == 1
        assert len(reviewer.items) == initial_count - 1

    def test_handle_key_reject(self, db_with_items):
        """Test reject key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        reviewer.handle_key('r')

        assert reviewer.session.rejected == 1
        assert reviewer.session.items_reviewed == 1

    def test_handle_key_modify(self, db_with_items):
        """Test modify key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        reviewer.handle_key('m')

        assert reviewer.session.modified == 1
        assert reviewer.session.items_reviewed == 1

    def test_handle_key_skip(self, db_with_items):
        """Test skip key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        reviewer.handle_key('s')

        assert reviewer.session.skipped == 1
        assert reviewer.session.items_reviewed == 1

    def test_handle_key_next(self, db_with_items):
        """Test next key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        assert reviewer.current_index == 0
        reviewer.handle_key('n')
        assert reviewer.current_index == 1

    def test_handle_key_previous(self, db_with_items):
        """Test previous key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        reviewer.current_index = 1
        reviewer.handle_key('p')
        assert reviewer.current_index == 0

    def test_handle_key_previous_at_start(self, db_with_items):
        """Test previous at start does nothing."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        reviewer.handle_key('p')
        assert reviewer.current_index == 0

    def test_handle_key_next_at_end(self, db_with_items):
        """Test next at end does nothing."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        reviewer.current_index = len(reviewer.items) - 1
        old_index = reviewer.current_index
        reviewer.handle_key('n')
        assert reviewer.current_index == old_index

    def test_make_layout(self, db_with_items):
        """Test layout creation."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        layout = reviewer.make_layout()

        assert layout is not None
        # Check layout has children
        assert len(layout.children) == 2

    def test_render_item_panel_with_item(self, db_with_items):
        """Test item panel rendering."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        panel = reviewer._render_item_panel()

        assert panel is not None
        assert "Review Item" in panel.title

    def test_render_item_panel_empty(self, temp_db):
        """Test item panel when empty."""
        reviewer = InteractiveReviewer(db=temp_db)
        reviewer.load_items()

        panel = reviewer._render_item_panel()

        assert panel is not None
        assert "Complete" in panel.title

    def test_uppercase_keys(self, db_with_items):
        """Test uppercase key handling."""
        reviewer = InteractiveReviewer(db=db_with_items)
        reviewer.load_items()

        # Uppercase should work too
        result = reviewer.handle_key('A')
        assert reviewer.session.approved == 1


class TestRunInteractiveReview:
    """Tests for run_interactive_review function."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_run.db"
            configure_database(db_path)
            yield

    def test_run_empty_queue(self, temp_db):
        """Test running with empty queue."""
        session = run_interactive_review(reviewer="tester")

        # Should return immediately with empty session
        assert session.items_reviewed == 0
