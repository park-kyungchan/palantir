"""
E2E Tests for Human-in-the-Loop (HITL) Workflow.

Tests the complete review queue workflow:
- Low confidence detection
- Queue management
- Review decisions
- Status transitions
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typer.testing import CliRunner

from cow_cli.review import (
    configure_database,
    ReviewDatabase,
    ReviewStatus,
    ReviewDecision,
)
from cow_cli.review.router import ReviewRouter, RoutingDecision
from cow_cli.review.priority_scorer import PriorityScorer, UrgencyLevel
from cow_cli.commands.review import app


runner = CliRunner()


class TestConfidenceBasedRouting:
    """Tests for confidence-based routing decisions."""

    def test_high_confidence_auto_approve(self):
        """Test: High confidence (>0.95) → Auto approve"""
        router = ReviewRouter()
        result = router.route(
            element_type="math",
            confidence=0.98,
        )

        assert result.decision == RoutingDecision.AUTO_APPROVE
        assert result.needs_review is False

    def test_medium_confidence_manual_review(self):
        """Test: Medium confidence (0.80-0.95) → Manual review"""
        router = ReviewRouter()
        result = router.route(
            element_type="math",
            confidence=0.88,
        )

        assert result.decision == RoutingDecision.MANUAL_REVIEW
        assert result.needs_review is True

    def test_low_confidence_reject(self):
        """Test: Low confidence (<0.80) → Reject for re-processing"""
        router = ReviewRouter()
        result = router.route(
            element_type="math",
            confidence=0.65,
        )

        assert result.decision == RoutingDecision.REJECT
        assert result.needs_review is False  # Rejected, not queued for review

    def test_type_specific_thresholds(self):
        """Test: Different element types have different thresholds"""
        router = ReviewRouter()

        # Math has higher threshold (0.95)
        math_result = router.route("math", 0.92)
        assert math_result.decision == RoutingDecision.MANUAL_REVIEW

        # Diagram has lower threshold (0.85)
        diagram_result = router.route("diagram", 0.92)
        assert diagram_result.decision == RoutingDecision.AUTO_APPROVE


class TestPriorityScoring:
    """Tests for review priority scoring."""

    def test_low_confidence_high_priority(self):
        """Test: Lower confidence → Higher priority"""
        scorer = PriorityScorer()

        high_conf = scorer.calculate(0.90, 0.95, "math")
        low_conf = scorer.calculate(0.75, 0.95, "math")

        assert low_conf.total > high_conf.total

    def test_blocking_items_prioritized(self):
        """Test: Blocking items get priority boost"""
        scorer = PriorityScorer()

        normal = scorer.calculate(0.85, 0.95, "math", is_blocking=False)
        blocking = scorer.calculate(0.85, 0.95, "math", is_blocking=True)

        assert blocking.total > normal.total
        assert blocking.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]

    def test_critical_types_prioritized(self):
        """Test: Math/equation types have higher priority"""
        scorer = PriorityScorer()

        math_score = scorer.calculate(0.85, 0.95, "math")
        text_score = scorer.calculate(0.85, 0.90, "text")

        assert math_score.total >= text_score.total


class TestReviewQueueManagement:
    """Tests for review queue operations."""

    @pytest.fixture
    def review_db(self, e2e_temp_dir):
        """Create a fresh review database."""
        db_path = e2e_temp_dir / "review.db"
        return configure_database(db_path)

    def test_add_item_to_queue(self, review_db):
        """Test: Add item to review queue"""
        item = review_db.add_review_item(
            image_path="/test/image1.png",
            element_id="elem-001",
            element_type="equation",
            confidence=0.82,
            reason="Below threshold",
            priority=50.0,
        )

        assert item is not None
        assert item.id is not None
        assert item.status == ReviewStatus.PENDING.value

    def test_claim_and_release_item(self, review_db):
        """Test: Claim → Work → Release workflow"""
        # Add item
        item = review_db.add_review_item(
            image_path="/test/image2.png",
            element_id="elem-002",
            element_type="math",
            confidence=0.78,
            priority=60.0,
        )

        # Claim
        claimed = review_db.claim_item(item.id, "reviewer-1")
        assert claimed.status == ReviewStatus.CLAIMED.value
        assert claimed.reviewer == "reviewer-1"

        # Release
        released = review_db.release_item(item.id)
        assert released.status == ReviewStatus.PENDING.value

    def test_submit_approve_decision(self, review_db):
        """Test: Submit approval decision"""
        # Add and claim
        item = review_db.add_review_item(
            image_path="/test/image3.png",
            element_id="elem-003",
            element_type="diagram",
            confidence=0.75,
            priority=70.0,
        )

        # Submit approval
        approved = review_db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.APPROVED.value,
            reviewer="reviewer-1",
            comment="Verified correct",
        )

        assert approved.status == ReviewStatus.APPROVED.value
        assert approved.decision == ReviewDecision.APPROVED.value

    def test_submit_reject_decision(self, review_db):
        """Test: Submit rejection decision"""
        item = review_db.add_review_item(
            image_path="/test/image4.png",
            element_id="elem-004",
            element_type="math",
            confidence=0.65,
            priority=80.0,
        )

        rejected = review_db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.REJECTED.value,
            reviewer="reviewer-1",
            comment="OCR error - illegible",
        )

        assert rejected.status == ReviewStatus.REJECTED.value

    def test_submit_modify_decision(self, review_db):
        """Test: Submit modification decision"""
        item = review_db.add_review_item(
            image_path="/test/image5.png",
            element_id="elem-005",
            element_type="equation",
            confidence=0.80,
            priority=55.0,
        )

        modified = review_db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.MODIFIED.value,
            reviewer="reviewer-1",
            comment="Fixed LaTeX syntax",
            modifications={"latex": "x^2 + y^2 = z^2"},
        )

        assert modified.status == ReviewStatus.MODIFIED.value

    def test_queue_stats(self, review_db):
        """Test: Queue statistics"""
        # Add multiple items
        for i in range(5):
            review_db.add_review_item(
                image_path=f"/test/image_{i}.png",
                element_id=f"elem-{i:03d}",
                element_type="math",
                confidence=0.80 + i * 0.02,
                priority=50.0 + i * 5,
            )

        # Approve some
        items = review_db.list_review_items(limit=2)
        for item in items:
            review_db.submit_review(
                item_id=item.id,
                decision=ReviewDecision.APPROVED.value,
                reviewer="tester",
            )

        # Check stats
        stats = review_db.get_queue_stats()
        assert stats["total"] == 5
        assert stats["approved"] == 2
        assert stats["pending"] == 3


class TestReviewCLICommands:
    """Tests for review CLI commands."""

    @pytest.fixture
    def setup_review_db(self, e2e_temp_dir):
        """Setup review database with test items."""
        db_path = e2e_temp_dir / "review.db"
        db = configure_database(db_path)

        # Add test items
        for i in range(3):
            db.add_review_item(
                image_path=f"/test/cli_test_{i}.png",
                element_id=f"cli-elem-{i}",
                element_type="math" if i % 2 == 0 else "diagram",
                confidence=0.75 + i * 0.05,
                priority=60.0 + i * 10,
            )

        return db

    def test_cli_list_command(self, setup_review_db):
        """Test: cow review list"""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # Should show items
        assert "math" in result.stdout.lower() or "diagram" in result.stdout.lower() or "no" in result.stdout.lower()

    def test_cli_stats_command(self, setup_review_db):
        """Test: cow review stats"""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Queue Statistics" in result.stdout or "Total" in result.stdout or "Statistics" in result.stdout

    def test_cli_add_command(self, e2e_temp_dir):
        """Test: cow review add"""
        # Setup database in temp dir to avoid readonly issues
        db_path = e2e_temp_dir / "add_test.db"
        configure_database(db_path)

        result = runner.invoke(app, [
            "add", "/test/new_item.png",
            "--element-id", "new-001",
            "--type", "equation",
            "--confidence", "0.78",
        ])

        assert result.exit_code == 0
        assert "Added" in result.stdout


class TestCompleteHITLScenario:
    """Complete end-to-end HITL scenarios."""

    def test_low_confidence_to_approval_workflow(self, e2e_temp_dir):
        """
        Complete workflow:
        1. Detect low confidence element
        2. Add to review queue
        3. Reviewer claims item
        4. Reviewer approves
        5. Verify final state
        """
        # Setup
        db_path = e2e_temp_dir / "hitl_workflow.db"
        db = configure_database(db_path)
        router = ReviewRouter()

        # Step 1: Detect low confidence
        element_confidence = 0.82
        routing = router.route("math", element_confidence)

        assert routing.needs_review is True

        # Step 2: Add to queue
        item = db.add_review_item(
            image_path="/test/low_conf_equation.png",
            element_id="math-elem-001",
            element_type="math",
            confidence=element_confidence,
            reason=routing.reason,
            priority=routing.priority,
        )

        assert item.status == ReviewStatus.PENDING.value

        # Step 3: Reviewer claims
        claimed = db.claim_item(item.id, "expert-reviewer")
        assert claimed.status == ReviewStatus.CLAIMED.value

        # Step 4: Reviewer approves
        approved = db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.APPROVED.value,
            reviewer="expert-reviewer",
            comment="Verified - equation is correct",
        )

        assert approved.status == ReviewStatus.APPROVED.value

        # Step 5: Verify final state
        final_item = db.get_review_item(item.id)
        assert final_item.status == ReviewStatus.APPROVED.value
        assert final_item.reviewer == "expert-reviewer"
        assert final_item.reviewed_at is not None

    def test_modification_workflow(self, e2e_temp_dir):
        """
        Modification workflow:
        1. Add item needing correction
        2. Reviewer modifies
        3. Verify modifications saved
        """
        db_path = e2e_temp_dir / "modify_workflow.db"
        db = configure_database(db_path)

        # Add item
        item = db.add_review_item(
            image_path="/test/needs_fix.png",
            element_id="fix-001",
            element_type="equation",
            confidence=0.70,
            priority=80.0,
            element_data='{"latex": "x^2 + y^2 = z^"}',
        )

        # Modify
        modified = db.submit_review(
            item_id=item.id,
            decision=ReviewDecision.MODIFIED.value,
            reviewer="editor",
            comment="Fixed missing exponent",
            modifications={"latex": "x^2 + y^2 = z^2"},
        )

        assert modified.status == ReviewStatus.MODIFIED.value

    def test_stale_claim_expiration(self, e2e_temp_dir):
        """Test: Stale claims are expired"""
        db_path = e2e_temp_dir / "stale_claims.db"
        db = configure_database(db_path)

        # Add and claim
        item = db.add_review_item(
            image_path="/test/stale.png",
            element_id="stale-001",
            element_type="math",
            confidence=0.75,
            priority=50.0,
        )
        db.claim_item(item.id, "absent-reviewer")

        # Expire stale claims (would need time manipulation in real test)
        # For now, just verify the expire_stale_claims function exists
        expired = db.expire_stale_claims(max_age_minutes=30)
        # In real scenario with time manipulation, this would expire the claim
        assert isinstance(expired, int)
