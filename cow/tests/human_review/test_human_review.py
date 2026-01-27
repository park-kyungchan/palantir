"""
Tests for Stage G (Human Review) modules.

Tests QueueManager, PriorityScorer, and AnnotationWorkflow functionality.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from mathpix_pipeline.human_review import (
    ReviewQueueManager,
    QueueConfig,
    QueueStats,
    PriorityScorer,
    PriorityScorerConfig,
    AnnotationWorkflow,
    AnnotationWorkflowConfig,
    create_queue_manager,
    create_priority_scorer,
    create_annotation_workflow,
)
from mathpix_pipeline.human_review.models.task import (
    ReviewTask,
    ReviewStatus,
    ReviewPriority,
    ReviewDecision,
    TaskContext,
    TaskMetrics,
)
from mathpix_pipeline.human_review.models.annotation import (
    Annotation,
    AnnotationSession,
    Correction,
    SessionStatus,
)
from mathpix_pipeline.human_review.exceptions import (
    QueueError,
    TaskNotFoundError,
    SessionExpiredError,
    AnnotationError,
)
from mathpix_pipeline.schemas import ReviewSeverity, PipelineStage


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_review_context():
    """Sample review context."""
    return TaskContext(
        image_id="test-image-001",
        element_type="equation",
        element_id="eq-001",
        original_confidence=0.42,
        threshold_delta=0.18,
        pipeline_stage=PipelineStage.SEMANTIC_GRAPH,
        related_elements=["point-A", "line-001"],
    )


@pytest.fixture
def sample_review_task(sample_review_context):
    """Sample review task."""
    return ReviewTask(
        task_id="task-001",
        context=sample_review_context,
        priority=ReviewPriority.MEDIUM,
        severity=ReviewSeverity.MEDIUM,
    )


@pytest.fixture
def sample_correction():
    """Sample correction."""
    return Correction(
        correction_id="corr-001",
        element_id="eq-001",
        correction_type="latex",
        original_value="y = mx + b",
        corrected_value="y = 2x + 1",
        reason="Coefficient incorrect",
    )


# =============================================================================
# ReviewQueueManager Tests
# =============================================================================

class TestQueueManagerInit:
    """Test ReviewQueueManager initialization."""

    def test_default_init(self):
        """Test default initialization."""
        manager = ReviewQueueManager()

        assert manager.config is not None
        assert manager.config.default_queue_name == "default"
        assert "default" in manager._queues

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = QueueConfig(
            max_queue_size=500,
            stale_threshold_hours=12,
        )
        manager = ReviewQueueManager(config=config)

        assert manager.config.max_queue_size == 500
        assert manager.config.stale_threshold_hours == 12

    def test_factory_function(self):
        """Test factory function."""
        manager = create_queue_manager()

        assert isinstance(manager, ReviewQueueManager)


class TestQueueManagerEnqueue:
    """Test task enqueueing."""

    @pytest.mark.asyncio
    async def test_enqueue_task(self, sample_review_task):
        """Test enqueueing a task."""
        manager = ReviewQueueManager()

        task_id = await manager.enqueue(sample_review_task)

        assert task_id == sample_review_task.task_id
        assert sample_review_task.status == ReviewStatus.PENDING

    @pytest.mark.asyncio
    async def test_enqueue_with_priority_scoring(self, sample_review_task):
        """Test enqueueing with automatic priority scoring."""
        config = QueueConfig(enable_priority_scoring=True)
        manager = ReviewQueueManager(config=config)

        task_id = await manager.enqueue(sample_review_task)

        # Priority may be adjusted by scorer
        assert task_id == sample_review_task.task_id

    @pytest.mark.asyncio
    async def test_enqueue_batch(self, sample_review_context):
        """Test batch enqueueing."""
        manager = ReviewQueueManager()

        tasks = [
            ReviewTask(
                task_id=f"task-{i}",
                context=sample_review_context,
                priority=ReviewPriority.MEDIUM,
            )
            for i in range(3)
        ]

        task_ids = await manager.enqueue_batch(tasks)

        assert len(task_ids) == 3

    @pytest.mark.asyncio
    async def test_enqueue_queue_full_raises(self, sample_review_task):
        """Test enqueueing to full queue raises error."""
        config = QueueConfig(max_queue_size=1)
        manager = ReviewQueueManager(config=config)

        await manager.enqueue(sample_review_task)

        # Second enqueue should fail
        task2 = ReviewTask(
            task_id="task-002",
            context=sample_review_task.context,
            priority=ReviewPriority.LOW,
        )

        with pytest.raises(QueueError):
            await manager.enqueue(task2)


class TestQueueManagerDequeue:
    """Test task dequeueing."""

    @pytest.mark.asyncio
    async def test_dequeue_task(self, sample_review_task):
        """Test dequeueing a task."""
        manager = ReviewQueueManager()
        await manager.enqueue(sample_review_task)

        task = await manager.dequeue("reviewer-001")

        assert task is not None
        assert task.task_id == sample_review_task.task_id
        assert task.status == ReviewStatus.ASSIGNED
        assert task.assigned_to == "reviewer-001"

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self):
        """Test dequeueing from empty queue returns None."""
        manager = ReviewQueueManager()

        task = await manager.dequeue("reviewer-001")

        assert task is None

    @pytest.mark.asyncio
    async def test_dequeue_priority_order(self, sample_review_context):
        """Test tasks dequeued in priority order."""
        manager = ReviewQueueManager()

        # Enqueue tasks with different priorities
        low_task = ReviewTask(
            task_id="task-low",
            context=sample_review_context,
            priority=ReviewPriority.LOW,
        )
        high_task = ReviewTask(
            task_id="task-high",
            context=sample_review_context,
            priority=ReviewPriority.HIGH,
        )

        await manager.enqueue(low_task)
        await manager.enqueue(high_task)

        # High priority should be dequeued first
        task = await manager.dequeue("reviewer-001")

        assert task.task_id == "task-high"

    @pytest.mark.asyncio
    async def test_peek_without_removing(self, sample_review_task):
        """Test peeking at tasks without removing them."""
        manager = ReviewQueueManager()
        await manager.enqueue(sample_review_task)

        tasks = await manager.peek(count=1)

        assert len(tasks) == 1
        # Task should still be in queue
        dequeued = await manager.dequeue("reviewer-001")
        assert dequeued is not None


class TestQueueManagerTaskManagement:
    """Test task management operations."""

    @pytest.mark.asyncio
    async def test_get_task(self, sample_review_task):
        """Test getting a task by ID."""
        manager = ReviewQueueManager()
        await manager.enqueue(sample_review_task)

        task = await manager.get_task(sample_review_task.task_id)

        assert task is not None
        assert task.task_id == sample_review_task.task_id

    @pytest.mark.asyncio
    async def test_update_task(self, sample_review_task):
        """Test updating a task."""
        manager = ReviewQueueManager()
        await manager.enqueue(sample_review_task)

        sample_review_task.priority = ReviewPriority.HIGH
        await manager.update_task(sample_review_task)

        updated = await manager.get_task(sample_review_task.task_id)
        assert updated.priority == ReviewPriority.HIGH

    @pytest.mark.asyncio
    async def test_complete_task(self, sample_review_task):
        """Test completing a task."""
        manager = ReviewQueueManager()
        await manager.enqueue(sample_review_task)

        task = await manager.complete_task(
            sample_review_task.task_id,
            ReviewDecision.APPROVE,
            reason="Looks good",
        )

        assert task.status == ReviewStatus.COMPLETED
        assert task.decision == ReviewDecision.APPROVE

    @pytest.mark.asyncio
    async def test_escalate_task(self, sample_review_task):
        """Test escalating a task."""
        manager = ReviewQueueManager()
        await manager.enqueue(sample_review_task)

        task = await manager.escalate_task(
            sample_review_task.task_id,
            reason="Complex case",
        )

        assert task.priority == ReviewPriority.HIGH
        assert task.metrics.escalation_count > 0


class TestQueueManagerStatistics:
    """Test queue statistics."""

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, sample_review_task):
        """Test getting queue statistics."""
        manager = ReviewQueueManager()
        await manager.enqueue(sample_review_task)

        stats = await manager.get_queue_stats()

        assert stats.total_tasks == 1
        assert stats.pending_tasks == 1
        assert stats.queue_name == "default"

    @pytest.mark.asyncio
    async def test_stats_track_priority_distribution(self, sample_review_context):
        """Test stats track priority distribution."""
        manager = ReviewQueueManager()

        # Enqueue tasks with different priorities
        await manager.enqueue(ReviewTask(
            task_id="task-1",
            context=sample_review_context,
            priority=ReviewPriority.HIGH,
        ))
        await manager.enqueue(ReviewTask(
            task_id="task-2",
            context=sample_review_context,
            priority=ReviewPriority.LOW,
        ))

        stats = await manager.get_queue_stats()

        assert stats.high_count == 1
        assert stats.low_count == 1


# =============================================================================
# PriorityScorer Tests
# =============================================================================

class TestPriorityScorerInit:
    """Test PriorityScorer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        scorer = PriorityScorer()

        assert scorer.config is not None
        assert scorer.config.confidence_weight == 0.35

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = PriorityScorerConfig(
            confidence_weight=0.40,
            complexity_weight=0.30,
        )
        scorer = PriorityScorer(config=config)

        assert scorer.config.confidence_weight == 0.40
        assert scorer.config.complexity_weight == 0.30

    def test_factory_function(self):
        """Test factory function."""
        scorer = create_priority_scorer()

        assert isinstance(scorer, PriorityScorer)


class TestPriorityScorerScoring:
    """Test priority scoring."""

    def test_score_low_confidence_task(self):
        """Test scoring low confidence task."""
        scorer = PriorityScorer()

        context = TaskContext(
            image_id="test-001",
            element_type="equation",
            element_id="eq-001",
            original_confidence=0.25,  # Very low
            threshold_delta=0.35,
            pipeline_stage=PipelineStage.SEMANTIC_GRAPH,
        )

        task = ReviewTask(
            task_id="task-001",
            context=context,
            priority=ReviewPriority.MEDIUM,
        )

        priority = scorer.score(task)

        # Low confidence should result in high priority
        assert priority in (ReviewPriority.HIGH, ReviewPriority.CRITICAL)

    def test_score_high_confidence_task(self):
        """Test scoring high confidence task."""
        scorer = PriorityScorer()

        context = TaskContext(
            image_id="test-001",
            element_type="label",
            element_id="label-001",
            original_confidence=0.85,  # High
            threshold_delta=0.05,
            pipeline_stage=PipelineStage.SEMANTIC_GRAPH,
        )

        task = ReviewTask(
            task_id="task-001",
            context=context,
            priority=ReviewPriority.MEDIUM,
        )

        priority = scorer.score(task)

        # High confidence should result in low priority
        assert priority in (ReviewPriority.LOW, ReviewPriority.MEDIUM)

    def test_score_complex_element(self):
        """Test scoring complex element."""
        scorer = PriorityScorer()

        context = TaskContext(
            image_id="test-001",
            element_type="function",  # Complex type
            element_id="func-001",
            original_confidence=0.50,
            threshold_delta=0.10,
            pipeline_stage=PipelineStage.SEMANTIC_GRAPH,
            related_elements=["eq-1", "eq-2", "point-A"],  # Many relations
        )

        task = ReviewTask(
            task_id="task-001",
            context=context,
            priority=ReviewPriority.MEDIUM,
        )

        priority = scorer.score(task)

        # Complexity should influence priority
        assert priority is not None

    def test_score_urgent_task(self):
        """Test scoring urgent task with due date."""
        scorer = PriorityScorer()

        context = TaskContext(
            image_id="test-001",
            element_type="equation",
            element_id="eq-001",
            original_confidence=0.50,
            threshold_delta=0.10,
            pipeline_stage=PipelineStage.SEMANTIC_GRAPH,
        )

        # Task due in 1 hour
        task = ReviewTask(
            task_id="task-001",
            context=context,
            priority=ReviewPriority.MEDIUM,
            due_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        priority = scorer.score(task)

        # Urgency should increase priority
        assert priority in (ReviewPriority.HIGH, ReviewPriority.CRITICAL)

    def test_explain_score(self, sample_review_task):
        """Test score explanation."""
        scorer = PriorityScorer()

        explanation = scorer.explain_score(sample_review_task)

        assert "scores" in explanation
        assert "confidence" in explanation["scores"]
        assert "total_score" in explanation
        assert "priority" in explanation


# =============================================================================
# AnnotationWorkflow Tests
# =============================================================================

class TestAnnotationWorkflowInit:
    """Test AnnotationWorkflow initialization."""

    def test_default_init(self):
        """Test default initialization."""
        workflow = AnnotationWorkflow()

        assert workflow.config is not None
        assert workflow.config.session_timeout_minutes == 60

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = AnnotationWorkflowConfig(
            session_timeout_minutes=30,
            require_reason_for_reject=False,
        )
        workflow = AnnotationWorkflow(config=config)

        assert workflow.config.session_timeout_minutes == 30
        assert workflow.config.require_reason_for_reject is False

    def test_factory_function(self):
        """Test factory function."""
        workflow = create_annotation_workflow()

        assert isinstance(workflow, AnnotationWorkflow)


class TestAnnotationWorkflowSessions:
    """Test annotation session management."""

    @pytest.mark.asyncio
    async def test_start_annotation(self, sample_review_task):
        """Test starting annotation session."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        assert session is not None
        assert session.task_id == sample_review_task.task_id
        assert session.reviewer_id == "reviewer-001"
        assert session.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_session(self, sample_review_task):
        """Test getting a session."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        retrieved = await workflow.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_extend_session(self, sample_review_task):
        """Test extending session timeout."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        original_expiry = session.expires_at
        extended = await workflow.extend_session(session.session_id, 15)

        assert extended.expires_at > original_expiry

    @pytest.mark.asyncio
    async def test_abandon_session(self, sample_review_task):
        """Test abandoning a session."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        await workflow.abandon_session(session.session_id)

        retrieved = await workflow.get_session(session.session_id)
        assert retrieved.status == SessionStatus.ABANDONED


class TestAnnotationWorkflowAnnotations:
    """Test annotation management."""

    @pytest.mark.asyncio
    async def test_save_annotation(self, sample_review_task):
        """Test saving annotation."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        annotation = Annotation(
            annotation_id="ann-001",
            task_id=sample_review_task.task_id,
            reviewer_id="reviewer-001",
        )

        await workflow.save_annotation(session.session_id, annotation)

        # Should succeed without error

    @pytest.mark.asyncio
    async def test_add_correction(self, sample_review_task, sample_correction):
        """Test adding correction to annotation."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        annotation = await workflow.add_correction(
            session.session_id,
            sample_correction,
        )

        assert annotation.correction_count == 1

    @pytest.mark.asyncio
    async def test_remove_correction(self, sample_review_task, sample_correction):
        """Test removing correction."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        await workflow.add_correction(session.session_id, sample_correction)
        removed = await workflow.remove_correction(
            session.session_id,
            sample_correction.correction_id,
        )

        assert removed is True


class TestAnnotationWorkflowReviewSubmission:
    """Test review submission."""

    @pytest.mark.asyncio
    async def test_submit_review_approve(self, sample_review_task):
        """Test submitting approval review."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        # Wait minimum review time
        await asyncio.sleep(0.02)

        result = await workflow.submit_review(
            session.session_id,
            ReviewDecision.APPROVE,
        )

        assert result is not None
        assert result.decision == ReviewDecision.APPROVE

    @pytest.mark.asyncio
    async def test_submit_review_reject_requires_reason(self, sample_review_task):
        """Test reject requires reason."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        await asyncio.sleep(0.02)

        # Reject without reason should fail
        with pytest.raises(AnnotationError):
            await workflow.submit_review(
                session.session_id,
                ReviewDecision.REJECT,
            )

    @pytest.mark.asyncio
    async def test_submit_review_modify_requires_correction(self, sample_review_task):
        """Test modify requires correction."""
        workflow = AnnotationWorkflow()

        session = await workflow.start_annotation(
            sample_review_task.task_id,
            "reviewer-001",
            task=sample_review_task,
        )

        await asyncio.sleep(0.02)

        # Modify without correction should fail
        with pytest.raises(AnnotationError):
            await workflow.submit_review(
                session.session_id,
                ReviewDecision.MODIFY,
            )


class TestAnnotationWorkflowSecondOpinion:
    """Test second opinion handling."""

    @pytest.mark.asyncio
    async def test_request_second_opinion(self, sample_review_task):
        """Test requesting second opinion."""
        workflow = AnnotationWorkflow()

        task = await workflow.request_second_opinion(
            sample_review_task.task_id,
            "Complex equation",
            "reviewer-001",
        )

        assert task.metrics.escalation_count > 0

    @pytest.mark.asyncio
    async def test_check_needs_second_opinion(self):
        """Test checking if task needs second opinion."""
        workflow = AnnotationWorkflow()

        # Low confidence task
        context = TaskContext(
            image_id="test-001",
            element_type="equation",
            element_id="eq-001",
            original_confidence=0.30,  # Below threshold
            threshold_delta=0.30,
            pipeline_stage=PipelineStage.SEMANTIC_GRAPH,
        )

        task = ReviewTask(
            task_id="task-001",
            context=context,
            priority=ReviewPriority.MEDIUM,
        )

        workflow._tasks[task.task_id] = task
        needs_second = await workflow.check_needs_second_opinion(task.task_id)

        assert needs_second is True
