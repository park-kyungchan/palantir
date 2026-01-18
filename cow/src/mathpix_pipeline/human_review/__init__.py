"""
Human Review Module for Stage G.

Provides human-in-the-loop review capabilities for pipeline results:
- ReviewQueueManager: Task queue management
- AnnotationWorkflow: Review session handling
- FeedbackLoopManager: Training data generation
- PriorityScorer: Task prioritization

Components:
- Queue: Task queue with priority ordering
- Workflow: Annotation sessions and review submission
- Feedback: Correction recording and pattern analysis
- Models: Task, Annotation, Reviewer data models
- API: FastAPI endpoints for review operations

Schema Version: 2.0.0
Module Version: 1.0.0
"""

# Queue Manager
from .queue_manager import (
    QueueConfig,
    QueueStats,
    ReviewQueueManager,
    create_queue_manager,
)

# Annotation Workflow
from .annotation_workflow import (
    AnnotationWorkflowConfig,
    ReviewResult,
    AnnotationWorkflow,
    create_annotation_workflow,
)

# Feedback Loop
from .feedback_loop import (
    FeedbackLoopConfig,
    DateRange,
    CorrectionRecord,
    TrainingDataset,
    ErrorPattern,
    ErrorPatternReport,
    FeedbackLoopManager,
    create_feedback_loop_manager,
)

# Priority Scorer
from .priority_scorer import (
    PriorityScorerConfig,
    PriorityScorer,
    create_priority_scorer,
)

# Models
from .models import (
    # Task models
    ReviewTask,
    TaskContext,
    TaskMetrics,
    # Annotation models
    Annotation,
    Correction,
    AnnotationSession,
    CorrectionType,
    # Reviewer models
    Reviewer,
    ReviewerRole,
    ReviewerCapability,
    ReviewerStats,
)

from .models.task import (
    ReviewStatus,
    ReviewDecision,
    ReviewPriority,
)

from .models.annotation import (
    SessionStatus,
)

from .models.reviewer import (
    ReviewerStatus,
)

# Exceptions
from .exceptions import (
    HumanReviewError,
    QueueError,
    AnnotationError,
    ReviewTaskError,
    FeedbackLoopError,
    SessionExpiredError,
    TaskNotFoundError,
)

# API (optional, requires FastAPI)
try:
    from .api import router, create_review_router
    _API_AVAILABLE = True
except ImportError:
    _API_AVAILABLE = False
    router = None
    create_review_router = None


def get_api_router():
    """Get API router if FastAPI is available.

    Returns:
        APIRouter or None if FastAPI not installed
    """
    if not _API_AVAILABLE:
        raise ImportError(
            "FastAPI not available. Install with: pip install fastapi"
        )
    return router


__all__ = [
    # Queue Manager
    "QueueConfig",
    "QueueStats",
    "ReviewQueueManager",
    "create_queue_manager",
    # Annotation Workflow
    "AnnotationWorkflowConfig",
    "ReviewResult",
    "AnnotationWorkflow",
    "create_annotation_workflow",
    # Feedback Loop
    "FeedbackLoopConfig",
    "DateRange",
    "CorrectionRecord",
    "TrainingDataset",
    "ErrorPattern",
    "ErrorPatternReport",
    "FeedbackLoopManager",
    "create_feedback_loop_manager",
    # Priority Scorer
    "PriorityScorerConfig",
    "PriorityScorer",
    "create_priority_scorer",
    # Task models
    "ReviewTask",
    "TaskContext",
    "TaskMetrics",
    "ReviewStatus",
    "ReviewDecision",
    "ReviewPriority",
    # Annotation models
    "Annotation",
    "Correction",
    "AnnotationSession",
    "CorrectionType",
    "SessionStatus",
    # Reviewer models
    "Reviewer",
    "ReviewerRole",
    "ReviewerStatus",
    "ReviewerCapability",
    "ReviewerStats",
    # Exceptions
    "HumanReviewError",
    "QueueError",
    "AnnotationError",
    "ReviewTaskError",
    "FeedbackLoopError",
    "SessionExpiredError",
    "TaskNotFoundError",
    # API
    "router",
    "create_review_router",
    "get_api_router",
]
