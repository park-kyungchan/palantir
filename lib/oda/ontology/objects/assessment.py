"""
Orion ODA v4.0 - Assessment ObjectType
=======================================

Assessment represents a test, quiz, or evaluation
with items, scoring, and results tracking.

Palantir Pattern:
- Assessments contain items (questions)
- Items map to knowledge components
- Results tracked per learner attempt

Schema Version: 4.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


class AssessmentType(str, Enum):
    """Type of assessment."""
    QUIZ = "quiz"
    TEST = "test"
    EXAM = "exam"
    PRACTICE = "practice"
    DIAGNOSTIC = "diagnostic"
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    ADAPTIVE = "adaptive"


class AssessmentStatus(str, Enum):
    """Assessment lifecycle status."""
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADING = "grading"
    GRADED = "graded"
    REVIEWED = "reviewed"


class ItemType(str, Enum):
    """Type of assessment item."""
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"
    ORDERING = "ordering"
    CODE = "code"
    FILE_UPLOAD = "file_upload"


class GradingMethod(str, Enum):
    """Grading method for assessment."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    HYBRID = "hybrid"
    PEER_REVIEW = "peer_review"


@register_object_type
class Assessment(OntologyObject):
    """
    ObjectType: Assessment

    Represents an assessment (test, quiz, exam) with items,
    scoring configuration, and attempt tracking.

    Features:
    - Multiple item types support
    - Adaptive item selection
    - Time limits and attempts
    - Detailed scoring and feedback

    Links:
    - course: Course (Many-to-One)
    - learner: Learner (Many-to-One)
    - session: Session (Many-to-One)
    """

    # Required fields
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Assessment title"
    )

    # Type and status
    assessment_type: AssessmentType = Field(
        default=AssessmentType.QUIZ,
        description="Type of assessment"
    )
    assessment_status: AssessmentStatus = Field(
        default=AssessmentStatus.DRAFT,
        description="Current status"
    )
    grading_method: GradingMethod = Field(
        default=GradingMethod.AUTOMATIC,
        description="Grading method"
    )

    # Foreign keys
    course_id: Optional[str] = Field(
        default=None,
        description="Associated course ID"
    )
    learner_id: Optional[str] = Field(
        default=None,
        description="Learner attempting this assessment"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session where assessment was taken"
    )

    # Description
    description: str = Field(
        default="",
        max_length=2000,
        description="Assessment description"
    )
    instructions: str = Field(
        default="",
        max_length=5000,
        description="Instructions for the assessment"
    )

    # Items (questions)
    items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Assessment items: [{id, type, content, options, correct_answer, kc_id, points, difficulty}]"
    )
    item_count: int = Field(
        default=0,
        ge=0,
        description="Number of items"
    )
    item_order: List[str] = Field(
        default_factory=list,
        description="Order of item IDs (for randomization)"
    )
    shuffle_items: bool = Field(
        default=False,
        description="Shuffle item order"
    )
    shuffle_options: bool = Field(
        default=False,
        description="Shuffle answer options within items"
    )

    # Knowledge components
    knowledge_components: List[str] = Field(
        default_factory=list,
        description="Knowledge components tested"
    )

    # Scoring
    total_points: float = Field(
        default=0.0,
        ge=0.0,
        description="Total possible points"
    )
    passing_score: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Minimum passing score percentage"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Weight in course grade"
    )
    allow_partial_credit: bool = Field(
        default=True,
        description="Allow partial credit on items"
    )

    # Time limits
    time_limit_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Time limit in minutes (None = unlimited)"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Start timestamp"
    )
    submitted_at: Optional[datetime] = Field(
        default=None,
        description="Submission timestamp"
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Due date"
    )

    # Attempts
    max_attempts: int = Field(
        default=1,
        ge=1,
        description="Maximum attempts allowed"
    )
    attempt_number: int = Field(
        default=1,
        ge=1,
        description="Current attempt number"
    )
    attempts_used: int = Field(
        default=0,
        ge=0,
        description="Number of attempts used"
    )
    best_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Best score across attempts"
    )

    # Responses and scoring
    responses: Dict[str, Any] = Field(
        default_factory=dict,
        description="Learner responses: {item_id: response}"
    )
    item_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores per item: {item_id: score}"
    )
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Total score achieved"
    )
    score_percentage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Score as percentage"
    )
    passed: Optional[bool] = Field(
        default=None,
        description="Whether assessment was passed"
    )

    # Feedback
    feedback: Dict[str, str] = Field(
        default_factory=dict,
        description="Feedback per item: {item_id: feedback}"
    )
    overall_feedback: str = Field(
        default="",
        max_length=5000,
        description="Overall assessment feedback"
    )
    show_correct_answers: bool = Field(
        default=False,
        description="Show correct answers after submission"
    )
    show_feedback_immediately: bool = Field(
        default=False,
        description="Show feedback immediately after each item"
    )

    # Statistics (for template assessments)
    average_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Average score across all attempts"
    )
    average_duration_minutes: float = Field(
        default=0.0,
        ge=0.0,
        description="Average completion time"
    )
    completion_count: int = Field(
        default=0,
        ge=0,
        description="Number of completions"
    )
    pass_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Pass rate percentage"
    )

    # Adaptive assessment settings
    is_adaptive: bool = Field(
        default=False,
        description="Use adaptive item selection"
    )
    target_difficulty: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Target difficulty for adaptive selection"
    )
    theta_estimate: Optional[float] = Field(
        default=None,
        description="Current ability estimate (IRT theta)"
    )
    se_estimate: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Standard error of ability estimate"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Assessment tags"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional settings"
    )

    # Link definitions
    course: ClassVar[Link["Course"]] = Link(
        target="Course",
        link_type_id="assessment_belongs_to_course",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="course_has_assessments",
        description="Parent course",
    )

    learner: ClassVar[Link["Learner"]] = Link(
        target="Learner",
        link_type_id="assessment_belongs_to_learner",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="learner_has_assessments",
        description="Learner who took this assessment",
    )

    session: ClassVar[Link["Session"]] = Link(
        target="Session",
        link_type_id="assessment_in_session",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="session_has_assessments",
        description="Session where assessment was taken",
    )

    @property
    def is_timed(self) -> bool:
        """Check if assessment has a time limit."""
        return self.time_limit_minutes is not None

    @property
    def is_started(self) -> bool:
        """Check if assessment has been started."""
        return self.started_at is not None

    @property
    def is_submitted(self) -> bool:
        """Check if assessment has been submitted."""
        return self.submitted_at is not None

    @property
    def is_graded(self) -> bool:
        """Check if assessment has been graded."""
        return self.score is not None

    @property
    def time_remaining_seconds(self) -> Optional[float]:
        """Get remaining time in seconds."""
        if not self.is_timed or not self.started_at:
            return None
        if self.is_submitted:
            return 0
        deadline = self.started_at + timedelta(minutes=self.time_limit_minutes)
        remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
        return max(0, remaining)

    @property
    def is_time_expired(self) -> bool:
        """Check if time has expired."""
        remaining = self.time_remaining_seconds
        return remaining is not None and remaining <= 0

    @property
    def duration_minutes(self) -> Optional[float]:
        """Get duration of the attempt in minutes."""
        if not self.started_at:
            return None
        end = self.submitted_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds() / 60

    @property
    def has_attempts_remaining(self) -> bool:
        """Check if more attempts are available."""
        return self.attempts_used < self.max_attempts

    @property
    def items_answered(self) -> int:
        """Get count of answered items."""
        return len(self.responses)

    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        if self.item_count == 0:
            return 0.0
        return (self.items_answered / self.item_count) * 100

    def start(self) -> None:
        """Start the assessment."""
        if self.is_started:
            raise ValueError("Assessment already started")
        self.started_at = datetime.now(timezone.utc)
        self.assessment_status = AssessmentStatus.IN_PROGRESS
        self.attempts_used += 1
        self.touch()

    def submit_response(self, item_id: str, response: Any) -> None:
        """Submit a response for an item."""
        if self.is_submitted:
            raise ValueError("Assessment already submitted")
        if self.is_time_expired:
            raise ValueError("Time has expired")
        self.responses[item_id] = response
        self.touch()

    def submit(self) -> None:
        """Submit the assessment for grading."""
        if not self.is_started:
            raise ValueError("Assessment not started")
        if self.is_submitted:
            raise ValueError("Assessment already submitted")
        self.submitted_at = datetime.now(timezone.utc)
        self.assessment_status = AssessmentStatus.SUBMITTED
        self.touch()

    def grade(self, item_scores: Dict[str, float], feedback: Optional[Dict[str, str]] = None) -> None:
        """Grade the assessment."""
        self.item_scores = item_scores
        if feedback:
            self.feedback = feedback

        # Calculate total score
        self.score = sum(item_scores.values())
        if self.total_points > 0:
            self.score_percentage = (self.score / self.total_points) * 100
        else:
            self.score_percentage = 0.0

        self.passed = self.score_percentage >= self.passing_score
        self.assessment_status = AssessmentStatus.GRADED

        # Update best score
        if self.best_score is None or self.score > self.best_score:
            self.best_score = self.score

        self.touch()

    def add_feedback(self, overall: str) -> None:
        """Add overall feedback."""
        self.overall_feedback = overall
        self.assessment_status = AssessmentStatus.REVIEWED
        self.touch()


# Forward reference resolution
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.oda.ontology.objects.course import Course
    from lib.oda.ontology.objects.learner import Learner
    from lib.oda.ontology.objects.session import Session
