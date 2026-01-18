"""
Orion ODA v4.0 - Course ObjectType
===================================

Course represents a structured learning program with
modules, lessons, and knowledge components.

Palantir Pattern:
- Courses contain hierarchical content structure
- Knowledge components map to course content
- Progress tracking per learner-course pair

Schema Version: 4.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


class CourseLevel(str, Enum):
    """Course difficulty level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CourseStatus(str, Enum):
    """Course publication status."""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class CourseType(str, Enum):
    """Type of course."""
    SELF_PACED = "self_paced"
    INSTRUCTOR_LED = "instructor_led"
    BLENDED = "blended"
    ADAPTIVE = "adaptive"


@register_object_type
class Course(OntologyObject):
    """
    ObjectType: Course

    Represents a structured learning program with content,
    assessments, and progress tracking.

    Features:
    - Hierarchical content structure (modules/lessons)
    - Knowledge component mapping
    - Prerequisite requirements
    - Progress and completion tracking

    Links:
    - workspace: Workspace (Many-to-One)
    - learners: Learner[] (Many-to-Many)
    - assessments: Assessment[] (One-to-Many)
    - resources: Resource[] (One-to-Many)
    - prerequisites: Course[] (Many-to-Many, self-referential)
    """

    # Required fields
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Course title"
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Course code (e.g., CS101)"
    )

    # Type and status
    course_type: CourseType = Field(
        default=CourseType.SELF_PACED,
        description="Type of course delivery"
    )
    course_status: CourseStatus = Field(
        default=CourseStatus.DRAFT,
        description="Publication status"
    )
    level: CourseLevel = Field(
        default=CourseLevel.BEGINNER,
        description="Difficulty level"
    )

    # Foreign keys
    workspace_id: Optional[str] = Field(
        default=None,
        description="Parent workspace ID"
    )
    instructor_id: Optional[str] = Field(
        default=None,
        description="Primary instructor/author ID"
    )

    # Description
    description: str = Field(
        default="",
        max_length=5000,
        description="Course description"
    )
    short_description: str = Field(
        default="",
        max_length=500,
        description="Short description for previews"
    )
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="Learning objectives"
    )

    # Content structure
    modules: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Course modules: [{id, title, lessons: [{id, title, content_id}]}]"
    )
    module_count: int = Field(
        default=0,
        ge=0,
        description="Number of modules"
    )
    lesson_count: int = Field(
        default=0,
        ge=0,
        description="Total number of lessons"
    )

    # Knowledge components
    knowledge_components: List[str] = Field(
        default_factory=list,
        description="Knowledge component IDs covered"
    )
    kc_count: int = Field(
        default=0,
        ge=0,
        description="Number of knowledge components"
    )

    # Timing
    estimated_hours: float = Field(
        default=1.0,
        ge=0.0,
        description="Estimated completion time in hours"
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="Publication timestamp"
    )
    last_updated_at: Optional[datetime] = Field(
        default=None,
        description="Last content update timestamp"
    )

    # Enrollment
    max_enrollment: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum enrollment (None = unlimited)"
    )
    enrollment_count: int = Field(
        default=0,
        ge=0,
        description="Current enrollment count"
    )
    enrollment_open: bool = Field(
        default=True,
        description="Whether enrollment is open"
    )
    enrollment_start: Optional[datetime] = Field(
        default=None,
        description="Enrollment start date"
    )
    enrollment_end: Optional[datetime] = Field(
        default=None,
        description="Enrollment end date"
    )

    # Completion criteria
    passing_score: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Minimum passing score percentage"
    )
    completion_criteria: Dict[str, Any] = Field(
        default_factory=lambda: {
            "min_lessons_completed": 0.8,  # 80% of lessons
            "min_assessments_passed": 1,
            "min_kc_mastery": 0.7,  # 70% of KCs
        },
        description="Completion criteria"
    )

    # Statistics
    completion_count: int = Field(
        default=0,
        ge=0,
        description="Number of completions"
    )
    average_rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Average rating (0-5)"
    )
    rating_count: int = Field(
        default=0,
        ge=0,
        description="Number of ratings"
    )
    average_completion_hours: float = Field(
        default=0.0,
        ge=0.0,
        description="Average completion time in hours"
    )

    # Metadata
    language: str = Field(
        default="en",
        max_length=10,
        description="Primary language"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Course tags"
    )
    categories: List[str] = Field(
        default_factory=list,
        description="Course categories"
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="Thumbnail image URL"
    )
    preview_video_url: Optional[str] = Field(
        default=None,
        description="Preview video URL"
    )

    # Settings
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Course settings"
    )
    is_featured: bool = Field(
        default=False,
        description="Featured course flag"
    )
    is_certified: bool = Field(
        default=False,
        description="Offers certificate on completion"
    )

    # Link definitions
    workspace: ClassVar[Link["Workspace"]] = Link(
        target="Workspace",
        link_type_id="course_belongs_to_workspace",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="workspace_has_courses",
        description="Parent workspace",
    )

    learners: ClassVar[Link["Learner"]] = Link(
        target="Learner",
        link_type_id="course_has_learners",
        cardinality=Cardinality.MANY_TO_MANY,
        reverse_link_id="learner_enrolled_in_courses",
        description="Enrolled learners",
        backing_table_name="learner_enrollments",
    )

    assessments: ClassVar[Link["Assessment"]] = Link(
        target="Assessment",
        link_type_id="course_has_assessments",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="assessment_belongs_to_course",
        description="Course assessments",
    )

    resources: ClassVar[Link["Resource"]] = Link(
        target="Resource",
        link_type_id="course_has_resources",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="resource_belongs_to_course",
        description="Course resources",
    )

    prerequisites: ClassVar[Link["Course"]] = Link(
        target="Course",
        link_type_id="course_requires_prerequisite",
        cardinality=Cardinality.MANY_TO_MANY,
        reverse_link_id="course_is_prerequisite_for",
        description="Prerequisite courses",
        backing_table_name="course_prerequisites",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Normalize course code to uppercase."""
        return v.upper().strip()

    @property
    def is_published(self) -> bool:
        """Check if course is published."""
        return self.course_status == CourseStatus.PUBLISHED

    @property
    def is_enrollable(self) -> bool:
        """Check if course can accept enrollments."""
        if not self.is_published:
            return False
        if not self.enrollment_open:
            return False
        if self.max_enrollment and self.enrollment_count >= self.max_enrollment:
            return False
        now = datetime.now(timezone.utc)
        if self.enrollment_start and now < self.enrollment_start:
            return False
        if self.enrollment_end and now > self.enrollment_end:
            return False
        return True

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        if self.enrollment_count == 0:
            return 0.0
        return (self.completion_count / self.enrollment_count) * 100

    def publish(self) -> None:
        """Publish the course."""
        self.course_status = CourseStatus.PUBLISHED
        self.published_at = datetime.now(timezone.utc)
        self.touch()

    def archive(self) -> None:
        """Archive the course."""
        self.course_status = CourseStatus.ARCHIVED
        self.enrollment_open = False
        self.touch()

    def enroll_learner(self) -> bool:
        """Record a learner enrollment."""
        if not self.is_enrollable:
            return False
        self.enrollment_count += 1
        self.touch()
        return True

    def record_completion(self, hours_to_complete: float) -> None:
        """Record a course completion."""
        old_count = self.completion_count
        old_avg = self.average_completion_hours

        self.completion_count += 1

        # Update running average
        if old_count == 0:
            self.average_completion_hours = hours_to_complete
        else:
            total_hours = (old_avg * old_count) + hours_to_complete
            self.average_completion_hours = total_hours / self.completion_count

        self.touch()

    def add_rating(self, rating: float) -> None:
        """Add a rating and update average."""
        if not 0 <= rating <= 5:
            raise ValueError("Rating must be between 0 and 5")

        old_count = self.rating_count
        old_avg = self.average_rating

        self.rating_count += 1

        # Update running average
        if old_count == 0:
            self.average_rating = rating
        else:
            total_rating = (old_avg * old_count) + rating
            self.average_rating = total_rating / self.rating_count

        self.touch()

    def update_content(self) -> None:
        """Mark content as updated."""
        self.last_updated_at = datetime.now(timezone.utc)
        self.touch()


# Forward reference resolution
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.oda.ontology.objects.workspace import Workspace
    from lib.oda.ontology.objects.learner import Learner
    from lib.oda.ontology.objects.assessment import Assessment
    from lib.oda.ontology.objects.resource import Resource
