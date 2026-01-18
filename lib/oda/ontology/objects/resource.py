"""
Orion ODA v4.0 - Resource ObjectType
=====================================

Resource represents learning materials like documents,
videos, images, and other content assets.

Palantir Pattern:
- Resources are reusable content units
- Versioning support for content updates
- Access tracking for analytics

Schema Version: 4.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


class ResourceType(str, Enum):
    """Type of resource."""
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    CODE = "code"
    INTERACTIVE = "interactive"
    SIMULATION = "simulation"
    EXTERNAL_LINK = "external_link"
    EMBED = "embed"
    PDF = "pdf"
    EBOOK = "ebook"
    ARCHIVE = "archive"
    OTHER = "other"


class ResourceStatus(str, Enum):
    """Resource availability status."""
    DRAFT = "draft"
    PROCESSING = "processing"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ContentFormat(str, Enum):
    """Content format/encoding."""
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    XML = "xml"
    BINARY = "binary"
    EXTERNAL_URL = "external_url"


class AccessLevel(str, Enum):
    """Access level for resource."""
    PUBLIC = "public"
    ENROLLED = "enrolled"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"
    PRIVATE = "private"


@register_object_type
class Resource(OntologyObject):
    """
    ObjectType: Resource

    Represents learning materials and content assets.
    Supports multiple content types with versioning and access tracking.

    Features:
    - Multiple content types (video, document, etc.)
    - File storage integration
    - Version history
    - Access and view tracking
    - Knowledge component mapping

    Links:
    - course: Course (Many-to-One)
    - related_resources: Resource[] (Many-to-Many, self-referential)
    """

    # Required fields
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Resource title"
    )
    resource_type: ResourceType = Field(
        ...,
        description="Type of resource"
    )

    # Status
    resource_status: ResourceStatus = Field(
        default=ResourceStatus.DRAFT,
        description="Availability status"
    )
    access_level: AccessLevel = Field(
        default=AccessLevel.ENROLLED,
        description="Access level required"
    )

    # Foreign keys
    course_id: Optional[str] = Field(
        default=None,
        description="Parent course ID"
    )
    author_id: Optional[str] = Field(
        default=None,
        description="Author/uploader ID"
    )
    module_id: Optional[str] = Field(
        default=None,
        description="Associated module ID"
    )
    lesson_id: Optional[str] = Field(
        default=None,
        description="Associated lesson ID"
    )

    # Content
    description: str = Field(
        default="",
        max_length=2000,
        description="Resource description"
    )
    content_format: ContentFormat = Field(
        default=ContentFormat.BINARY,
        description="Content format"
    )
    content_text: Optional[str] = Field(
        default=None,
        description="Text content (for text-based resources)"
    )
    content_url: Optional[str] = Field(
        default=None,
        description="URL to content (external or storage)"
    )
    embed_code: Optional[str] = Field(
        default=None,
        description="Embed code for external content"
    )

    # File information
    file_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Original file name"
    )
    file_size_bytes: int = Field(
        default=0,
        ge=0,
        description="File size in bytes"
    )
    mime_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="MIME type"
    )
    file_hash: Optional[str] = Field(
        default=None,
        description="File hash (SHA256)"
    )

    # Storage
    storage_provider: str = Field(
        default="local",
        max_length=50,
        description="Storage provider (local, s3, gcs, etc.)"
    )
    storage_path: Optional[str] = Field(
        default=None,
        description="Path in storage system"
    )
    storage_bucket: Optional[str] = Field(
        default=None,
        description="Storage bucket name"
    )

    # Media-specific fields
    duration_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        description="Duration for audio/video resources"
    )
    width: Optional[int] = Field(
        default=None,
        ge=0,
        description="Width for images/videos"
    )
    height: Optional[int] = Field(
        default=None,
        ge=0,
        description="Height for images/videos"
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="Thumbnail image URL"
    )

    # Versioning
    version_number: int = Field(
        default=1,
        ge=1,
        description="Current version number"
    )
    version_label: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Version label (e.g., '1.0', 'Draft 2')"
    )
    previous_version_id: Optional[str] = Field(
        default=None,
        description="ID of previous version"
    )
    version_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Version history entries"
    )

    # Knowledge components
    knowledge_components: List[str] = Field(
        default_factory=list,
        description="Related knowledge component IDs"
    )
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="Learning objectives covered"
    )
    difficulty_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Difficulty level (0=easy, 1=hard)"
    )
    estimated_time_minutes: int = Field(
        default=5,
        ge=1,
        description="Estimated time to complete/consume"
    )

    # Usage tracking
    view_count: int = Field(
        default=0,
        ge=0,
        description="Number of views"
    )
    download_count: int = Field(
        default=0,
        ge=0,
        description="Number of downloads"
    )
    completion_count: int = Field(
        default=0,
        ge=0,
        description="Number of completions"
    )
    unique_viewers: int = Field(
        default=0,
        ge=0,
        description="Number of unique viewers"
    )
    average_view_duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Average view duration"
    )
    last_accessed_at: Optional[datetime] = Field(
        default=None,
        description="Last access timestamp"
    )

    # Ratings
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

    # Metadata
    language: str = Field(
        default="en",
        max_length=10,
        description="Content language"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Resource tags"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Search keywords"
    )
    license: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Content license (e.g., CC-BY-4.0)"
    )
    attribution: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Attribution text"
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Original source URL"
    )

    # Timestamps
    published_at: Optional[datetime] = Field(
        default=None,
        description="Publication timestamp"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiration timestamp"
    )

    # Settings
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resource-specific settings"
    )
    is_downloadable: bool = Field(
        default=True,
        description="Allow downloads"
    )
    is_printable: bool = Field(
        default=True,
        description="Allow printing"
    )
    is_required: bool = Field(
        default=False,
        description="Required for course completion"
    )
    order_index: int = Field(
        default=0,
        ge=0,
        description="Display order within parent"
    )

    # Link definitions
    course: ClassVar[Link["Course"]] = Link(
        target="Course",
        link_type_id="resource_belongs_to_course",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="course_has_resources",
        description="Parent course",
    )

    related_resources: ClassVar[Link["Resource"]] = Link(
        target="Resource",
        link_type_id="resource_related_to_resource",
        cardinality=Cardinality.MANY_TO_MANY,
        reverse_link_id="resource_related_from_resource",
        description="Related resources",
        backing_table_name="resource_relations",
    )

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: Optional[str]) -> Optional[str]:
        """Normalize MIME type to lowercase."""
        if v:
            return v.lower().strip()
        return v

    @property
    def is_available(self) -> bool:
        """Check if resource is available for viewing."""
        if self.resource_status != ResourceStatus.AVAILABLE:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)

    @property
    def is_media(self) -> bool:
        """Check if resource is audio/video."""
        return self.resource_type in (ResourceType.VIDEO, ResourceType.AUDIO)

    @property
    def is_document(self) -> bool:
        """Check if resource is a document."""
        return self.resource_type in (
            ResourceType.DOCUMENT,
            ResourceType.PDF,
            ResourceType.EBOOK,
            ResourceType.PRESENTATION,
            ResourceType.SPREADSHEET,
        )

    @property
    def duration_formatted(self) -> Optional[str]:
        """Get duration as formatted string (MM:SS or HH:MM:SS)."""
        if not self.duration_seconds:
            return None
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def record_view(self, duration_seconds: Optional[float] = None) -> None:
        """Record a view of this resource."""
        self.view_count += 1
        self.last_accessed_at = datetime.now(timezone.utc)

        # Update average view duration
        if duration_seconds is not None:
            old_total = self.average_view_duration_seconds * (self.view_count - 1)
            self.average_view_duration_seconds = (old_total + duration_seconds) / self.view_count

        self.touch()

    def record_download(self) -> None:
        """Record a download of this resource."""
        self.download_count += 1
        self.last_accessed_at = datetime.now(timezone.utc)
        self.touch()

    def record_completion(self) -> None:
        """Record a completion of this resource."""
        self.completion_count += 1
        self.touch()

    def add_rating(self, rating: float) -> None:
        """Add a rating and update average."""
        if not 0 <= rating <= 5:
            raise ValueError("Rating must be between 0 and 5")

        old_total = self.average_rating * self.rating_count
        self.rating_count += 1
        self.average_rating = (old_total + rating) / self.rating_count
        self.touch()

    def publish(self) -> None:
        """Publish the resource."""
        self.resource_status = ResourceStatus.AVAILABLE
        self.published_at = datetime.now(timezone.utc)
        self.touch()

    def archive(self) -> None:
        """Archive the resource."""
        self.resource_status = ResourceStatus.ARCHIVED
        self.touch()

    def create_version(self, label: Optional[str] = None) -> None:
        """Create a new version entry."""
        version_entry = {
            "version_number": self.version_number,
            "version_label": self.version_label,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_hash": self.file_hash,
            "file_size_bytes": self.file_size_bytes,
        }
        self.version_history.append(version_entry)
        self.version_number += 1
        self.version_label = label or f"v{self.version_number}"
        self.touch()


# Forward reference resolution
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.oda.ontology.objects.course import Course
