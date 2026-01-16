"""
Orion ODA v4.0 - ActionType Expansion Tests
============================================

Tests for Phase 3.3-3.4 ActionType implementations:
- Batch execution (3.3.1-3.3.4)
- WorkspaceAction types (3.4.1)
- SessionAction types (3.4.2)
- AssessmentAction types (3.4.3)

Schema Version: 4.0.0
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    action_registry,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def action_context() -> ActionContext:
    """Create a test action context."""
    return ActionContext(
        actor_id="test-user",
        metadata={"test": True}
    )


@pytest.fixture
def system_context() -> ActionContext:
    """Create a system action context."""
    return ActionContext.system()


# =============================================================================
# BATCH EXECUTION TESTS (Phase 3.3)
# =============================================================================


class TestBatchExecution:
    """Tests for batch execution functionality."""

    @pytest.mark.asyncio
    async def test_batch_executor_creation(self):
        """Test BatchExecutor can be created."""
        from lib.oda.ontology.actions.batch import BatchExecutor

        executor = BatchExecutor()
        assert executor.batch_id.startswith("batch-")
        assert len(executor.items) == 0

    @pytest.mark.asyncio
    async def test_batch_executor_custom_id(self):
        """Test BatchExecutor with custom batch ID."""
        from lib.oda.ontology.actions.batch import BatchExecutor

        executor = BatchExecutor(batch_id="my-custom-batch")
        assert executor.batch_id == "my-custom-batch"

    @pytest.mark.asyncio
    async def test_batch_add_item(self):
        """Test adding items to batch."""
        from lib.oda.ontology.actions.batch import BatchExecutor, BatchItemStatus

        executor = BatchExecutor()
        idx = executor.add_item(
            action_type="file.read",
            params={"file_path": "/test/path"}
        )

        assert idx == 0
        assert len(executor.items) == 1
        assert executor.items[0].action_type == "file.read"
        assert executor.items[0].status == BatchItemStatus.PENDING

    @pytest.mark.asyncio
    async def test_batch_transaction_group(self):
        """Test creating transaction groups."""
        from lib.oda.ontology.actions.batch import BatchExecutor

        executor = BatchExecutor()
        indices = executor.create_transaction_group("file_ops", [
            {"action_type": "file.read", "params": {"file_path": "/a"}},
            {"action_type": "file.read", "params": {"file_path": "/b"}},
        ])

        assert len(indices) == 2
        assert len(executor.items) == 2
        assert "file_ops" in executor._transaction_groups
        assert executor._transaction_groups["file_ops"] == [0, 1]

    @pytest.mark.asyncio
    async def test_batch_progress_creation(self):
        """Test BatchProgress creation."""
        from lib.oda.ontology.actions.batch import BatchProgress

        progress = BatchProgress(
            batch_id="test-batch",
            total_items=10,
            completed_items=5,
            failed_items=1,
            percent_complete=50.0,
            elapsed_ms=1000.0,
            status="running"
        )

        assert progress.batch_id == "test-batch"
        assert progress.total_items == 10
        assert progress.completed_items == 5
        assert progress.failed_items == 1

        # Test serialization
        data = progress.to_dict()
        assert data["batch_id"] == "test-batch"
        assert data["percent_complete"] == 50.0

    @pytest.mark.asyncio
    async def test_batch_result_model(self):
        """Test BatchResult Pydantic model."""
        from lib.oda.ontology.actions.batch import BatchResult

        result = BatchResult(
            batch_id="test-batch",
            success=True,
            total_items=3,
            succeeded_items=3,
            failed_items=0,
        )

        assert result.batch_id == "test-batch"
        assert result.success is True
        assert result.succeeded_items == 3

    @pytest.mark.asyncio
    async def test_batch_execution_modes(self):
        """Test batch execution mode enum values."""
        from lib.oda.ontology.actions.batch import BatchExecutionMode

        assert BatchExecutionMode.SEQUENTIAL == "sequential"
        assert BatchExecutionMode.PARALLEL == "parallel"
        assert BatchExecutionMode.TRANSACTIONAL == "transactional"

    @pytest.mark.asyncio
    async def test_rollback_strategy_enum(self):
        """Test rollback strategy enum values."""
        from lib.oda.ontology.actions.batch import RollbackStrategy

        assert RollbackStrategy.CONTINUE == "continue"
        assert RollbackStrategy.STOP == "stop"
        assert RollbackStrategy.ROLLBACK == "rollback"

    @pytest.mark.asyncio
    async def test_batch_item_duration(self):
        """Test BatchItem duration calculation."""
        from lib.oda.ontology.actions.batch import BatchItem

        item = BatchItem(
            action_type="test.action",
            params={}
        )
        assert item.duration_ms is None

        # Set times
        item.started_at = datetime.now(timezone.utc)
        item.completed_at = datetime.now(timezone.utc)
        assert item.duration_ms is not None
        assert item.duration_ms >= 0


# =============================================================================
# WORKSPACE ACTION TESTS (Phase 3.4.1)
# =============================================================================


class TestWorkspaceActions:
    """Tests for WorkspaceAction types."""

    def test_workspace_create_action_registered(self):
        """Test WorkspaceCreateAction is registered."""
        action_cls = action_registry.get("workspace.create")
        assert action_cls is not None

    def test_workspace_update_action_registered(self):
        """Test WorkspaceUpdateAction is registered."""
        action_cls = action_registry.get("workspace.update")
        assert action_cls is not None

    def test_workspace_archive_action_registered(self):
        """Test WorkspaceArchiveAction is registered."""
        action_cls = action_registry.get("workspace.archive")
        assert action_cls is not None

    def test_workspace_delete_action_registered(self):
        """Test WorkspaceDeleteAction is registered and hazardous."""
        action_cls = action_registry.get("workspace.delete")
        assert action_cls is not None

        meta = action_registry.get_metadata("workspace.delete")
        assert meta is not None
        assert meta.requires_proposal is True

    def test_workspace_add_member_action_registered(self):
        """Test WorkspaceAddMemberAction is registered."""
        action_cls = action_registry.get("workspace.add_member")
        assert action_cls is not None

    def test_workspace_remove_member_action_registered(self):
        """Test WorkspaceRemoveMemberAction is registered."""
        action_cls = action_registry.get("workspace.remove_member")
        assert action_cls is not None

    @pytest.mark.asyncio
    async def test_workspace_create_execution(self, action_context: ActionContext):
        """Test WorkspaceCreateAction execution."""
        from lib.oda.ontology.actions.workspace_actions import WorkspaceCreateAction

        action = WorkspaceCreateAction()
        result = await action.execute(
            params={
                "name": "Test Workspace",
                "owner_id": "user-123",
                "workspace_type": "personal",
                "description": "A test workspace",
            },
            context=action_context
        )

        assert result.success is True
        assert result.data is not None
        assert result.data.name == "Test Workspace"
        assert result.data.owner_id == "user-123"
        assert len(result.edits) == 1
        assert result.edits[0].edit_type == EditType.CREATE

    @pytest.mark.asyncio
    async def test_workspace_create_validation_failure(self, action_context: ActionContext):
        """Test WorkspaceCreateAction validation failure."""
        from lib.oda.ontology.actions.workspace_actions import WorkspaceCreateAction

        action = WorkspaceCreateAction()
        result = await action.execute(
            params={
                # Missing required 'name' and 'owner_id'
            },
            context=action_context
        )

        assert result.success is False
        assert "validation" in result.error.lower()


# =============================================================================
# SESSION ACTION TESTS (Phase 3.4.2)
# =============================================================================


class TestSessionActions:
    """Tests for SessionAction types."""

    def test_session_create_action_registered(self):
        """Test SessionCreateAction is registered."""
        action_cls = action_registry.get("session.create")
        assert action_cls is not None

    def test_session_start_action_registered(self):
        """Test SessionStartAction is registered."""
        action_cls = action_registry.get("session.start")
        assert action_cls is not None

    def test_session_pause_action_registered(self):
        """Test SessionPauseAction is registered."""
        action_cls = action_registry.get("session.pause")
        assert action_cls is not None

    def test_session_resume_action_registered(self):
        """Test SessionResumeAction is registered."""
        action_cls = action_registry.get("session.resume")
        assert action_cls is not None

    def test_session_end_action_registered(self):
        """Test SessionEndAction is registered."""
        action_cls = action_registry.get("session.end")
        assert action_cls is not None

    def test_session_update_state_action_registered(self):
        """Test SessionUpdateStateAction is registered."""
        action_cls = action_registry.get("session.update_state")
        assert action_cls is not None

    def test_session_record_activity_action_registered(self):
        """Test SessionRecordActivityAction is registered."""
        action_cls = action_registry.get("session.record_activity")
        assert action_cls is not None

    @pytest.mark.asyncio
    async def test_session_create_execution(self, action_context: ActionContext):
        """Test SessionCreateAction execution."""
        from lib.oda.ontology.actions.session_actions import SessionCreateAction
        from lib.oda.ontology.objects.session import SessionStatus, SessionType

        action = SessionCreateAction()
        result = await action.execute(
            params={
                "session_type": "learning",
                "workspace_id": "ws-123",
                "learner_id": "learner-456",
                "client_type": "web",
            },
            context=action_context
        )

        assert result.success is True
        assert result.data is not None
        assert result.data.session_type == SessionType.LEARNING
        assert result.data.session_status == SessionStatus.INITIALIZING
        assert result.data.workspace_id == "ws-123"

    @pytest.mark.asyncio
    async def test_session_lifecycle_actions(self, action_context: ActionContext):
        """Test session lifecycle action sequence."""
        from lib.oda.ontology.actions.session_actions import (
            SessionCreateAction,
            SessionStartAction,
            SessionPauseAction,
            SessionResumeAction,
            SessionEndAction,
        )

        # Create
        create_action = SessionCreateAction()
        create_result = await create_action.execute(
            params={"session_type": "workspace"},
            context=action_context
        )
        assert create_result.success is True
        session_id = create_result.data.id

        # Start
        start_action = SessionStartAction()
        start_result = await start_action.execute(
            params={"session_id": session_id},
            context=action_context
        )
        assert start_result.success is True

        # Pause
        pause_action = SessionPauseAction()
        pause_result = await pause_action.execute(
            params={"session_id": session_id, "reason": "break"},
            context=action_context
        )
        assert pause_result.success is True

        # Resume
        resume_action = SessionResumeAction()
        resume_result = await resume_action.execute(
            params={"session_id": session_id},
            context=action_context
        )
        assert resume_result.success is True

        # End
        end_action = SessionEndAction()
        end_result = await end_action.execute(
            params={"session_id": session_id, "end_reason": "user_logout"},
            context=action_context
        )
        assert end_result.success is True


# =============================================================================
# ASSESSMENT ACTION TESTS (Phase 3.4.3)
# =============================================================================


class TestAssessmentActions:
    """Tests for AssessmentAction types."""

    def test_assessment_create_action_registered(self):
        """Test AssessmentCreateAction is registered."""
        action_cls = action_registry.get("assessment.create")
        assert action_cls is not None

    def test_assessment_start_action_registered(self):
        """Test AssessmentStartAction is registered."""
        action_cls = action_registry.get("assessment.start")
        assert action_cls is not None

    def test_assessment_submit_response_action_registered(self):
        """Test AssessmentSubmitResponseAction is registered."""
        action_cls = action_registry.get("assessment.submit_response")
        assert action_cls is not None

    def test_assessment_submit_action_registered(self):
        """Test AssessmentSubmitAction is registered."""
        action_cls = action_registry.get("assessment.submit")
        assert action_cls is not None

    def test_assessment_grade_action_registered(self):
        """Test AssessmentGradeAction is registered."""
        action_cls = action_registry.get("assessment.grade")
        assert action_cls is not None

    def test_assessment_add_feedback_action_registered(self):
        """Test AssessmentAddFeedbackAction is registered."""
        action_cls = action_registry.get("assessment.add_feedback")
        assert action_cls is not None

    def test_assessment_retry_action_registered(self):
        """Test AssessmentRetryAction is registered."""
        action_cls = action_registry.get("assessment.retry")
        assert action_cls is not None

    @pytest.mark.asyncio
    async def test_assessment_create_execution(self, action_context: ActionContext):
        """Test AssessmentCreateAction execution."""
        from lib.oda.ontology.actions.assessment_actions import AssessmentCreateAction
        from lib.oda.ontology.objects.assessment import AssessmentStatus, AssessmentType

        items = [
            {
                "id": "q1",
                "type": "multiple_choice",
                "content": "What is 2+2?",
                "options": ["3", "4", "5"],
                "correct_answer": "4",
                "points": 1,
            },
            {
                "id": "q2",
                "type": "true_false",
                "content": "The sky is blue.",
                "correct_answer": True,
                "points": 1,
            },
        ]

        action = AssessmentCreateAction()
        result = await action.execute(
            params={
                "title": "Math Quiz",
                "assessment_type": "quiz",
                "grading_method": "automatic",
                "items": items,
                "time_limit_minutes": 30,
                "passing_score": 70,
            },
            context=action_context
        )

        assert result.success is True
        assert result.data is not None
        assert result.data.title == "Math Quiz"
        assert result.data.assessment_type == AssessmentType.QUIZ
        assert result.data.assessment_status == AssessmentStatus.DRAFT
        assert result.data.item_count == 2
        assert result.data.total_points == 2

    @pytest.mark.asyncio
    async def test_assessment_workflow(self, action_context: ActionContext):
        """Test complete assessment workflow."""
        from lib.oda.ontology.actions.assessment_actions import (
            AssessmentCreateAction,
            AssessmentStartAction,
            AssessmentSubmitResponseAction,
            AssessmentSubmitAction,
            AssessmentGradeAction,
        )

        # Create assessment
        create_action = AssessmentCreateAction()
        create_result = await create_action.execute(
            params={
                "title": "Test Assessment",
                "assessment_type": "quiz",
                "items": [
                    {"id": "q1", "type": "short_answer", "content": "What is 1+1?", "points": 1}
                ],
            },
            context=action_context
        )
        assert create_result.success is True
        assessment_id = create_result.data.id

        # Start
        start_action = AssessmentStartAction()
        start_result = await start_action.execute(
            params={"assessment_id": assessment_id},
            context=action_context
        )
        assert start_result.success is True

        # Submit response
        response_action = AssessmentSubmitResponseAction()
        response_result = await response_action.execute(
            params={
                "assessment_id": assessment_id,
                "item_id": "q1",
                "response": "2"
            },
            context=action_context
        )
        assert response_result.success is True

        # Submit for grading
        submit_action = AssessmentSubmitAction()
        submit_result = await submit_action.execute(
            params={"assessment_id": assessment_id},
            context=action_context
        )
        assert submit_result.success is True

        # Grade
        grade_action = AssessmentGradeAction()
        grade_result = await grade_action.execute(
            params={
                "assessment_id": assessment_id,
                "item_scores": {"q1": 1.0},
            },
            context=action_context
        )
        assert grade_result.success is True


# =============================================================================
# ACTION REGISTRY INTEGRATION TESTS
# =============================================================================


class TestActionRegistryIntegration:
    """Integration tests for action registry."""

    def test_all_new_actions_registered(self):
        """Verify all Phase 3.3-3.4 actions are registered."""
        expected_actions = [
            # Workspace (3.4.1)
            "workspace.create",
            "workspace.update",
            "workspace.archive",
            "workspace.delete",
            "workspace.add_member",
            "workspace.remove_member",
            # Session (3.4.2)
            "session.create",
            "session.start",
            "session.pause",
            "session.resume",
            "session.end",
            "session.update_state",
            "session.update_context",
            "session.record_activity",
            "session.record_hint",
            # Assessment (3.4.3)
            "assessment.create",
            "assessment.start",
            "assessment.submit_response",
            "assessment.submit",
            "assessment.grade",
            "assessment.auto_grade",
            "assessment.add_feedback",
            "assessment.retry",
            "assessment.add_item",
            "assessment.remove_item",
        ]

        registered = action_registry.list_actions()

        for action_name in expected_actions:
            assert action_name in registered, f"Action '{action_name}' not registered"

    def test_hazardous_actions_marked(self):
        """Verify hazardous actions are properly marked."""
        hazardous_actions = [
            "workspace.delete",
            # Add more hazardous actions as needed
        ]

        for action_name in hazardous_actions:
            meta = action_registry.get_metadata(action_name)
            assert meta is not None, f"Metadata for '{action_name}' not found"
            assert meta.requires_proposal is True, f"'{action_name}' should require proposal"

    def test_non_hazardous_actions_not_marked(self):
        """Verify non-hazardous actions are not marked as requiring proposal."""
        non_hazardous_actions = [
            "workspace.create",
            "workspace.update",
            "session.create",
            "session.start",
            "assessment.create",
        ]

        for action_name in non_hazardous_actions:
            meta = action_registry.get_metadata(action_name)
            if meta:
                assert meta.requires_proposal is False, f"'{action_name}' should not require proposal"


# =============================================================================
# EDIT OPERATION TESTS
# =============================================================================


class TestEditOperations:
    """Tests for EditOperation generation."""

    @pytest.mark.asyncio
    async def test_create_action_generates_create_edit(self, action_context: ActionContext):
        """Test that create actions generate CREATE edit type."""
        from lib.oda.ontology.actions.workspace_actions import WorkspaceCreateAction

        action = WorkspaceCreateAction()
        result = await action.execute(
            params={"name": "Test", "owner_id": "user-1"},
            context=action_context
        )

        assert len(result.edits) == 1
        assert result.edits[0].edit_type == EditType.CREATE

    @pytest.mark.asyncio
    async def test_link_action_generates_link_edit(self, action_context: ActionContext):
        """Test that add_member action generates LINK edit type."""
        from lib.oda.ontology.actions.workspace_actions import WorkspaceAddMemberAction

        action = WorkspaceAddMemberAction()
        result = await action.execute(
            params={
                "workspace_id": "ws-1",
                "member_id": "agent-1",
                "role": "member"
            },
            context=action_context
        )

        assert result.success is True
        assert len(result.edits) == 1
        assert result.edits[0].edit_type == EditType.LINK


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    "TestBatchExecution",
    "TestWorkspaceActions",
    "TestSessionActions",
    "TestAssessmentActions",
    "TestActionRegistryIntegration",
    "TestEditOperations",
]
