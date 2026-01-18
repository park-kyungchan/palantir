"""
Orion ODA v4.0 - Workspace ObjectType
=====================================

Workspace represents a logical environment for organizing Sessions,
Agents, and other resources.

Palantir Pattern:
- Workspace is the top-level container for project organization
- Multi-tenant support through workspace isolation
- Configurable settings per workspace

Schema Version: 4.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


class WorkspaceType(str, Enum):
    """Type of workspace."""
    PERSONAL = "personal"
    TEAM = "team"
    ORGANIZATION = "organization"
    PROJECT = "project"


class WorkspaceStatus(str, Enum):
    """Workspace lifecycle status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    DELETED = "deleted"


@register_object_type
class Workspace(OntologyObject):
    """
    ObjectType: Workspace

    Represents a logical environment for organizing work.
    Workspaces contain Sessions, Agents, and other domain objects.

    Links:
    - sessions: Session[] (One-to-Many)
    - members: Agent[] (Many-to-Many)
    - courses: Course[] (One-to-Many) - for learning workspaces
    """

    # Required fields
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Workspace display name"
    )

    # Type and status
    workspace_type: WorkspaceType = Field(
        default=WorkspaceType.PERSONAL,
        description="Type of workspace"
    )
    workspace_status: WorkspaceStatus = Field(
        default=WorkspaceStatus.ACTIVE,
        description="Current workspace status"
    )

    # Ownership
    owner_id: str = Field(
        ...,
        description="ID of the workspace owner (Agent)"
    )

    # Metadata
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Workspace description"
    )
    slug: str = Field(
        default="",
        max_length=100,
        description="URL-friendly identifier"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags"
    )
    icon: Optional[str] = Field(
        default=None,
        description="Icon identifier or URL"
    )
    color: Optional[str] = Field(
        default=None,
        description="Theme color (hex)"
    )

    # Settings
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workspace-specific settings"
    )
    default_language: str = Field(
        default="en",
        max_length=10,
        description="Default language code"
    )
    timezone: str = Field(
        default="UTC",
        max_length=50,
        description="Workspace timezone"
    )

    # Limits
    max_sessions: int = Field(
        default=100,
        ge=1,
        description="Maximum concurrent sessions"
    )
    max_members: int = Field(
        default=50,
        ge=1,
        description="Maximum workspace members"
    )
    storage_limit_mb: int = Field(
        default=1000,
        ge=0,
        description="Storage limit in megabytes"
    )

    # Usage tracking
    session_count: int = Field(
        default=0,
        ge=0,
        description="Current session count"
    )
    member_count: int = Field(
        default=1,
        ge=1,
        description="Current member count"
    )
    storage_used_mb: float = Field(
        default=0.0,
        ge=0.0,
        description="Storage currently used (MB)"
    )
    last_activity_at: Optional[datetime] = Field(
        default=None,
        description="Last activity timestamp"
    )

    # Link definitions
    sessions: ClassVar[Link["Session"]] = Link(
        target="Session",
        link_type_id="workspace_has_sessions",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="session_belongs_to_workspace",
        description="Sessions in this workspace",
    )

    members: ClassVar[Link["Agent"]] = Link(
        target="Agent",
        link_type_id="workspace_has_members",
        cardinality=Cardinality.MANY_TO_MANY,
        reverse_link_id="agent_member_of_workspaces",
        description="Members of this workspace",
        backing_table_name="workspace_members",
    )

    courses: ClassVar[Link["Course"]] = Link(
        target="Course",
        link_type_id="workspace_has_courses",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="course_belongs_to_workspace",
        description="Courses in this workspace",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str, info) -> str:
        """Auto-generate slug from name if not provided."""
        if not v and "name" in info.data:
            # Simple slug generation
            name = info.data["name"]
            v = name.lower().replace(" ", "-")[:100]
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate hex color format."""
        if v is not None:
            v = v.strip()
            if not v.startswith("#"):
                v = f"#{v}"
            if len(v) not in (4, 7):  # #RGB or #RRGGBB
                raise ValueError("Color must be a valid hex color")
        return v

    @property
    def is_at_session_limit(self) -> bool:
        """Check if workspace is at session limit."""
        return self.session_count >= self.max_sessions

    @property
    def is_at_member_limit(self) -> bool:
        """Check if workspace is at member limit."""
        return self.member_count >= self.max_members

    @property
    def storage_usage_percent(self) -> float:
        """Get storage usage as percentage."""
        if self.storage_limit_mb == 0:
            return 100.0
        return (self.storage_used_mb / self.storage_limit_mb) * 100

    def record_activity(self) -> None:
        """Record activity timestamp."""
        self.last_activity_at = datetime.now(timezone.utc)
        self.touch()


# Forward reference resolution
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.oda.ontology.objects.session import Session
    from lib.oda.ontology.objects.task_types import Agent
    from lib.oda.ontology.objects.course import Course
