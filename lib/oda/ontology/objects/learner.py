"""
Orion ODA v4.0 - Learner ObjectType (Expanded)
==============================================

Learner represents a student in the Adaptive Tutoring system
with comprehensive proficiency tracking and learning preferences.

Palantir Pattern:
- Learner maintains knowledge state (BKT parameters)
- Proficiency is tracked per knowledge component
- Learning preferences adapt over time

Schema Version: 4.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


class LearnerLevel(str, Enum):
    """Learner proficiency level."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningStyle(str, Enum):
    """Preferred learning style."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING_WRITING = "reading_writing"
    KINESTHETIC = "kinesthetic"
    MIXED = "mixed"


class LearnerStatus(str, Enum):
    """Learner account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"


@register_object_type
class Learner(OntologyObject):
    """
    ObjectType: Learner (Expanded)

    Represents a student in the Adaptive Tutoring system with
    comprehensive tracking of knowledge state, preferences, and progress.

    Features:
    - Global proficiency estimate (theta)
    - Per-KC knowledge state (BKT parameters)
    - Learning preferences and style
    - Activity and engagement metrics
    - Goal tracking

    Links:
    - sessions: Session[] (One-to-Many)
    - enrolled_courses: Course[] (Many-to-Many)
    - assessments: Assessment[] (One-to-Many)
    """

    # Core identity
    user_id: str = Field(
        ...,
        description="Unique User Identifier"
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Display name"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Email address"
    )

    # Status
    learner_status: LearnerStatus = Field(
        default=LearnerStatus.ACTIVE,
        description="Account status"
    )
    level: LearnerLevel = Field(
        default=LearnerLevel.BEGINNER,
        description="Current proficiency level"
    )

    # Proficiency estimation (IRT/BKT)
    theta: float = Field(
        default=0.0,
        ge=-5.0,
        le=5.0,
        description="Global proficiency estimate (IRT theta)"
    )
    theta_se: float = Field(
        default=1.0,
        ge=0.0,
        description="Standard error of theta estimate"
    )

    # Knowledge state (BKT parameters per Knowledge Component)
    knowledge_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="BKT parameters for each KC: {kc_id: {P_L, P_T, P_G, P_S}}"
    )

    # Mastery tracking
    mastered_kcs: List[str] = Field(
        default_factory=list,
        description="List of mastered knowledge component IDs"
    )
    struggling_kcs: List[str] = Field(
        default_factory=list,
        description="List of struggling knowledge component IDs"
    )

    # Learning preferences
    learning_style: LearningStyle = Field(
        default=LearningStyle.MIXED,
        description="Preferred learning style"
    )
    preferred_language: str = Field(
        default="en",
        max_length=10,
        description="Preferred language code"
    )
    preferred_difficulty: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Preferred difficulty level (0=easy, 1=hard)"
    )
    enable_hints: bool = Field(
        default=True,
        description="Enable hint system"
    )
    enable_explanations: bool = Field(
        default=True,
        description="Enable detailed explanations"
    )

    # Adaptive settings
    adaptive_difficulty: bool = Field(
        default=True,
        description="Enable adaptive difficulty adjustment"
    )
    target_success_rate: float = Field(
        default=0.75,
        ge=0.5,
        le=0.95,
        description="Target success rate for difficulty calibration"
    )

    # Time tracking
    last_active: Optional[datetime] = Field(
        default=None,
        description="Last activity timestamp"
    )
    first_login: Optional[datetime] = Field(
        default=None,
        description="First login timestamp"
    )
    total_learning_time_minutes: int = Field(
        default=0,
        ge=0,
        description="Total learning time in minutes"
    )

    # Activity metrics
    total_sessions: int = Field(
        default=0,
        ge=0,
        description="Total number of sessions"
    )
    total_questions_answered: int = Field(
        default=0,
        ge=0,
        description="Total questions answered"
    )
    total_correct_answers: int = Field(
        default=0,
        ge=0,
        description="Total correct answers"
    )
    current_streak: int = Field(
        default=0,
        ge=0,
        description="Current consecutive correct answer streak"
    )
    best_streak: int = Field(
        default=0,
        ge=0,
        description="Best consecutive correct answer streak"
    )

    # Engagement metrics
    login_count: int = Field(
        default=0,
        ge=0,
        description="Total login count"
    )
    consecutive_days: int = Field(
        default=0,
        ge=0,
        description="Consecutive days of activity"
    )
    last_login_date: Optional[str] = Field(
        default=None,
        description="Last login date (YYYY-MM-DD)"
    )

    # Goals and progress
    daily_goal_minutes: int = Field(
        default=30,
        ge=5,
        le=480,
        description="Daily learning goal in minutes"
    )
    weekly_goal_questions: int = Field(
        default=50,
        ge=1,
        description="Weekly question goal"
    )
    goals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom goals: {goal_id: {target, current, type}}"
    )

    # Achievements and badges
    badges: List[str] = Field(
        default_factory=list,
        description="Earned badge IDs"
    )
    achievements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Achievement progress"
    )
    xp_points: int = Field(
        default=0,
        ge=0,
        description="Experience points"
    )

    # Settings
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="User settings"
    )
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email_reminders": True,
            "push_notifications": True,
            "achievement_alerts": True,
        },
        description="Notification preferences"
    )

    # Tags
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags"
    )

    # Link definitions
    sessions: ClassVar[Link["Session"]] = Link(
        target="Session",
        link_type_id="learner_has_sessions",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="session_belongs_to_learner",
        description="Learning sessions",
    )

    enrolled_courses: ClassVar[Link["Course"]] = Link(
        target="Course",
        link_type_id="learner_enrolled_in_courses",
        cardinality=Cardinality.MANY_TO_MANY,
        reverse_link_id="course_has_learners",
        description="Enrolled courses",
        backing_table_name="learner_enrollments",
    )

    assessments: ClassVar[Link["Assessment"]] = Link(
        target="Assessment",
        link_type_id="learner_has_assessments",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="assessment_belongs_to_learner",
        description="Assessment attempts",
    )

    @property
    def overall_accuracy(self) -> float:
        """Calculate overall accuracy rate."""
        if self.total_questions_answered == 0:
            return 0.0
        return (self.total_correct_answers / self.total_questions_answered) * 100

    @property
    def mastery_count(self) -> int:
        """Get count of mastered knowledge components."""
        return len(self.mastered_kcs)

    @property
    def is_active_today(self) -> bool:
        """Check if learner was active today."""
        if not self.last_active:
            return False
        today = datetime.now(timezone.utc).date()
        return self.last_active.date() == today

    def record_activity(self) -> None:
        """Record user activity."""
        now = datetime.now(timezone.utc)
        today_str = now.date().isoformat()

        # Update consecutive days
        if self.last_login_date:
            last_date = datetime.fromisoformat(self.last_login_date).date()
            delta = (now.date() - last_date).days
            if delta == 1:
                self.consecutive_days += 1
            elif delta > 1:
                self.consecutive_days = 1
        else:
            self.consecutive_days = 1

        self.last_active = now
        self.last_login_date = today_str
        self.login_count += 1
        self.touch()

    def record_answer(self, is_correct: bool, kc_id: Optional[str] = None) -> None:
        """Record an answer attempt."""
        self.total_questions_answered += 1

        if is_correct:
            self.total_correct_answers += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            self.current_streak = 0

        self.touch()

    def update_knowledge_state(
        self,
        kc_id: str,
        p_learn: float,
        p_transit: float = 0.1,
        p_guess: float = 0.2,
        p_slip: float = 0.1,
    ) -> None:
        """Update BKT parameters for a knowledge component."""
        self.knowledge_state[kc_id] = {
            "P_L": p_learn,
            "P_T": p_transit,
            "P_G": p_guess,
            "P_S": p_slip,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Update mastery status
        if p_learn >= 0.95 and kc_id not in self.mastered_kcs:
            self.mastered_kcs.append(kc_id)
            if kc_id in self.struggling_kcs:
                self.struggling_kcs.remove(kc_id)
        elif p_learn < 0.3 and kc_id not in self.struggling_kcs:
            self.struggling_kcs.append(kc_id)
            if kc_id in self.mastered_kcs:
                self.mastered_kcs.remove(kc_id)

        self.touch()

    def add_learning_time(self, minutes: int) -> None:
        """Add learning time."""
        self.total_learning_time_minutes += minutes
        self.touch()

    def award_xp(self, points: int) -> None:
        """Award experience points."""
        self.xp_points += points
        self.touch()

    def earn_badge(self, badge_id: str) -> bool:
        """Earn a badge if not already earned."""
        if badge_id not in self.badges:
            self.badges.append(badge_id)
            self.touch()
            return True
        return False


# Forward reference resolution
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.oda.ontology.objects.session import Session
    from lib.oda.ontology.objects.course import Course
    from lib.oda.ontology.objects.assessment import Assessment
