"""
FastAPI Routes for Stage G (Human Review).

Provides REST API endpoints for review operations:
- /api/v1/review/queue - Get queue status
- /api/v1/review/claim - Claim a task
- /api/v1/review/submit - Submit a review
- /api/v1/review/task/{task_id} - Get task details
- /api/v1/review/session/{session_id} - Session operations

Module Version: 1.0.0
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..models.task import ReviewStatus, ReviewDecision, ReviewPriority
from ..models.annotation import CorrectionType
from ..exceptions import (
    HumanReviewError,
    TaskNotFoundError,
    SessionExpiredError,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class QueueStatusResponse(BaseModel):
    """Response model for queue status."""
    queue_name: str
    total_tasks: int
    pending_tasks: int
    assigned_tasks: int
    in_progress_tasks: int

    # Priority breakdown
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Health
    avg_wait_time_ms: float = 0.0
    stale_task_count: int = 0

    last_updated: datetime


class ClaimTaskRequest(BaseModel):
    """Request model for claiming a task."""
    reviewer_id: str = Field(..., description="ID of the reviewer claiming")
    queue_name: Optional[str] = Field(None, description="Queue to claim from")
    preferred_priority: Optional[ReviewPriority] = Field(
        None, description="Preferred priority level"
    )


class ClaimTaskResponse(BaseModel):
    """Response model for claimed task."""
    task_id: str
    session_id: str
    priority: ReviewPriority
    element_type: str
    review_reason: str
    original_confidence: float
    threshold: float
    image_id: str
    claimed_at: datetime


class TaskDetailsResponse(BaseModel):
    """Response model for task details."""
    task_id: str
    image_id: str
    status: ReviewStatus
    priority: ReviewPriority

    # Context
    pipeline_stage: str
    element_type: str
    element_id: str
    original_confidence: float
    applied_threshold: float
    review_reason: str

    # Assignment
    assigned_to: Optional[str]
    assigned_at: Optional[datetime]

    # Timing
    created_at: datetime
    due_at: Optional[datetime]


class CorrectionRequest(BaseModel):
    """Request model for a correction."""
    correction_type: CorrectionType
    element_id: str
    field_name: str
    original_value: Any
    corrected_value: Any
    reason: Optional[str] = None


class SubmitReviewRequest(BaseModel):
    """Request model for submitting a review."""
    session_id: str = Field(..., description="Session identifier")
    decision: ReviewDecision = Field(..., description="Review decision")
    reason: Optional[str] = Field(None, description="Reason for decision")
    corrections: List[CorrectionRequest] = Field(
        default_factory=list, description="Corrections made"
    )
    comments: str = Field(default="", description="General comments")
    confidence_override: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Override confidence"
    )
    flag_for_training: bool = Field(
        False, description="Flag for training data"
    )


class SubmitReviewResponse(BaseModel):
    """Response model for submitted review."""
    result_id: str
    task_id: str
    decision: ReviewDecision
    review_time_ms: float
    correction_count: int
    message: str
    completed_at: datetime


class SecondOpinionRequest(BaseModel):
    """Request model for second opinion."""
    task_id: str = Field(..., description="Task to get second opinion on")
    requester_id: str = Field(..., description="Who is requesting")
    reason: str = Field(..., description="Reason for request")


class SaveAnnotationRequest(BaseModel):
    """Request model for saving annotation progress."""
    session_id: str
    corrections: List[CorrectionRequest] = Field(default_factory=list)
    comments: str = Field(default="")


class SessionStatusResponse(BaseModel):
    """Response model for session status."""
    session_id: str
    task_id: str
    status: str
    started_at: datetime
    expires_at: datetime
    is_active: bool
    correction_count: int
    action_count: int


# =============================================================================
# Router Factory
# =============================================================================

def create_review_router(
    queue_manager: Optional[Any] = None,
    annotation_workflow: Optional[Any] = None,
    feedback_manager: Optional[Any] = None,
) -> APIRouter:
    """Create review router with injected dependencies.

    Args:
        queue_manager: ReviewQueueManager instance
        annotation_workflow: AnnotationWorkflow instance
        feedback_manager: FeedbackLoopManager instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter(
        prefix="/api/v1/review",
        tags=["review"],
        responses={
            404: {"description": "Not found"},
            400: {"description": "Bad request"},
            500: {"description": "Internal error"},
        },
    )

    # =========================================================================
    # Queue Operations
    # =========================================================================

    @router.get(
        "/queue",
        response_model=QueueStatusResponse,
        summary="Get queue status",
        description="Get the current status of the review queue.",
    )
    async def get_queue_status(
        queue_name: Optional[str] = None,
    ) -> QueueStatusResponse:
        """Get queue status."""
        if queue_manager is None:
            return QueueStatusResponse(
                queue_name=queue_name or "default",
                total_tasks=0,
                pending_tasks=0,
                assigned_tasks=0,
                in_progress_tasks=0,
                last_updated=datetime.now(timezone.utc),
            )

        try:
            stats = await queue_manager.get_queue_stats(queue_name)
            return QueueStatusResponse(
                queue_name=stats.queue_name,
                total_tasks=stats.total_tasks,
                pending_tasks=stats.pending_tasks,
                assigned_tasks=stats.assigned_tasks,
                in_progress_tasks=stats.in_progress_tasks,
                critical_count=stats.critical_count,
                high_count=stats.high_count,
                medium_count=stats.medium_count,
                low_count=stats.low_count,
                avg_wait_time_ms=stats.avg_wait_time_ms,
                stale_task_count=stats.stale_task_count,
                last_updated=stats.last_updated,
            )
        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    @router.get(
        "/queues",
        response_model=List[str],
        summary="List queues",
        description="List all available review queues.",
    )
    async def list_queues() -> List[str]:
        """List available queues."""
        if queue_manager is None:
            return ["default"]
        return await queue_manager.list_queues()

    # =========================================================================
    # Task Operations
    # =========================================================================

    @router.post(
        "/claim",
        response_model=ClaimTaskResponse,
        status_code=status.HTTP_200_OK,
        summary="Claim a task",
        description="Claim a task for review and start an annotation session.",
    )
    async def claim_task(
        request: ClaimTaskRequest,
    ) -> ClaimTaskResponse:
        """Claim a task for review."""
        if queue_manager is None or annotation_workflow is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review service not configured",
            )

        try:
            # Dequeue a task
            task = await queue_manager.dequeue(
                reviewer_id=request.reviewer_id,
                queue_name=request.queue_name,
            )

            if task is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No tasks available in queue",
                )

            # Start annotation session
            session = await annotation_workflow.start_annotation(
                task_id=task.task_id,
                reviewer_id=request.reviewer_id,
                task=task,
            )

            return ClaimTaskResponse(
                task_id=task.task_id,
                session_id=session.session_id,
                priority=task.priority,
                element_type=task.context.element_type,
                review_reason=task.context.review_reason,
                original_confidence=task.context.original_confidence,
                threshold=task.context.applied_threshold,
                image_id=task.image_id,
                claimed_at=datetime.now(timezone.utc),
            )

        except TaskNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    @router.get(
        "/task/{task_id}",
        response_model=TaskDetailsResponse,
        summary="Get task details",
        description="Get detailed information about a specific task.",
    )
    async def get_task_details(
        task_id: str,
    ) -> TaskDetailsResponse:
        """Get task details."""
        if queue_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review service not configured",
            )

        try:
            task = await queue_manager.get_task(task_id)

            if task is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task not found: {task_id}",
                )

            return TaskDetailsResponse(
                task_id=task.task_id,
                image_id=task.image_id,
                status=task.status,
                priority=task.priority,
                pipeline_stage=task.context.pipeline_stage.value,
                element_type=task.context.element_type,
                element_id=task.context.element_id,
                original_confidence=task.context.original_confidence,
                applied_threshold=task.context.applied_threshold,
                review_reason=task.context.review_reason,
                assigned_to=task.assigned_to,
                assigned_at=task.metrics.assigned_at,
                created_at=task.created_at,
                due_at=task.due_at,
            )

        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    # =========================================================================
    # Session Operations
    # =========================================================================

    @router.get(
        "/session/{session_id}",
        response_model=SessionStatusResponse,
        summary="Get session status",
        description="Get the current status of an annotation session.",
    )
    async def get_session_status(
        session_id: str,
    ) -> SessionStatusResponse:
        """Get session status."""
        if annotation_workflow is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review service not configured",
            )

        try:
            session = await annotation_workflow.get_session(session_id)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            return SessionStatusResponse(
                session_id=session.session_id,
                task_id=session.task_id,
                status=session.status.value,
                started_at=session.started_at,
                expires_at=session.expires_at,
                is_active=session.is_active,
                correction_count=(
                    session.annotation.correction_count
                    if session.annotation else 0
                ),
                action_count=session.action_count,
            )

        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    @router.post(
        "/session/{session_id}/save",
        status_code=status.HTTP_200_OK,
        summary="Save annotation progress",
        description="Save the current annotation progress.",
    )
    async def save_annotation_progress(
        session_id: str,
        request: SaveAnnotationRequest,
    ):
        """Save annotation progress."""
        if annotation_workflow is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review service not configured",
            )

        try:
            session = await annotation_workflow.get_session(session_id)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            # Add corrections
            import uuid
            from ..models.annotation import Correction

            for corr_req in request.corrections:
                correction = Correction(
                    correction_id=f"corr-{uuid.uuid4().hex[:8]}",
                    correction_type=corr_req.correction_type,
                    element_id=corr_req.element_id,
                    field_name=corr_req.field_name,
                    original_value=corr_req.original_value,
                    corrected_value=corr_req.corrected_value,
                    reason=corr_req.reason,
                )
                await annotation_workflow.add_correction(session_id, correction)

            if session.annotation:
                session.annotation.comments = request.comments

            return {"message": "Progress saved", "session_id": session_id}

        except SessionExpiredError as e:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=str(e),
            )
        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    @router.post(
        "/session/{session_id}/extend",
        status_code=status.HTTP_200_OK,
        summary="Extend session timeout",
        description="Extend the timeout of an annotation session.",
    )
    async def extend_session(
        session_id: str,
        additional_minutes: int = 30,
    ):
        """Extend session timeout."""
        if annotation_workflow is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review service not configured",
            )

        try:
            session = await annotation_workflow.extend_session(
                session_id, additional_minutes
            )
            return {
                "message": f"Session extended by {additional_minutes} minutes",
                "new_expires_at": session.expires_at.isoformat(),
            }

        except SessionExpiredError as e:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=str(e),
            )
        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    # =========================================================================
    # Review Submission
    # =========================================================================

    @router.post(
        "/submit",
        response_model=SubmitReviewResponse,
        status_code=status.HTTP_200_OK,
        summary="Submit a review",
        description="Submit a completed review with annotations.",
    )
    async def submit_review(
        request: SubmitReviewRequest,
    ) -> SubmitReviewResponse:
        """Submit a review."""
        if annotation_workflow is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review service not configured",
            )

        try:
            # Get session
            session = await annotation_workflow.get_session(request.session_id)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {request.session_id}",
                )

            # Add final corrections
            import uuid
            from ..models.annotation import Correction

            for corr_req in request.corrections:
                correction = Correction(
                    correction_id=f"corr-{uuid.uuid4().hex[:8]}",
                    correction_type=corr_req.correction_type,
                    element_id=corr_req.element_id,
                    field_name=corr_req.field_name,
                    original_value=corr_req.original_value,
                    corrected_value=corr_req.corrected_value,
                    reason=corr_req.reason,
                )
                await annotation_workflow.add_correction(
                    request.session_id, correction
                )

            # Update annotation metadata
            if session.annotation:
                session.annotation.comments = request.comments
                session.annotation.confidence_override = request.confidence_override
                session.annotation.flagged_for_training = request.flag_for_training

            # Submit review
            result = await annotation_workflow.submit_review(
                session_id=request.session_id,
                decision=request.decision,
                reason=request.reason,
            )

            # Record in feedback loop
            if feedback_manager and session.annotation:
                task = await queue_manager.get_task(session.task_id) if queue_manager else None
                if task:
                    await feedback_manager.bulk_record_corrections(
                        task=task,
                        annotation=session.annotation,
                        review_decision=request.decision,
                    )

            return SubmitReviewResponse(
                result_id=result.result_id,
                task_id=result.task_id,
                decision=result.decision,
                review_time_ms=result.review_time_ms,
                correction_count=(
                    result.annotation.correction_count
                    if result.annotation else 0
                ),
                message="Review submitted successfully",
                completed_at=result.created_at,
            )

        except SessionExpiredError as e:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=str(e),
            )
        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    # =========================================================================
    # Second Opinion
    # =========================================================================

    @router.post(
        "/second-opinion",
        status_code=status.HTTP_200_OK,
        summary="Request second opinion",
        description="Request a second opinion on a task.",
    )
    async def request_second_opinion(
        request: SecondOpinionRequest,
    ):
        """Request second opinion."""
        if annotation_workflow is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Review service not configured",
            )

        try:
            task = await annotation_workflow.request_second_opinion(
                task_id=request.task_id,
                reason=request.reason,
                requester_id=request.requester_id,
            )

            return {
                "message": "Second opinion requested",
                "task_id": task.task_id,
                "new_priority": task.priority.value,
            }

        except TaskNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except HumanReviewError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    # =========================================================================
    # Health Check
    # =========================================================================

    @router.get(
        "/health",
        summary="Health check",
        description="Check if review service is healthy.",
    )
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "human-review",
            "version": "1.0.0",
            "queue_manager": "connected" if queue_manager else "not configured",
            "annotation_workflow": "connected" if annotation_workflow else "not configured",
            "feedback_manager": "connected" if feedback_manager else "not configured",
        }

    return router


# =============================================================================
# Default Router
# =============================================================================

# Create default router without dependencies (for basic usage)
router = create_review_router()


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "router",
    "create_review_router",
    "QueueStatusResponse",
    "ClaimTaskRequest",
    "ClaimTaskResponse",
    "TaskDetailsResponse",
    "SubmitReviewRequest",
    "SubmitReviewResponse",
    "SecondOpinionRequest",
    "SaveAnnotationRequest",
    "SessionStatusResponse",
]
