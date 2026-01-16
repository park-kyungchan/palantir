"""
Orion ODA v4.0 - Team/Group Management (Phase 3.1.2)
=====================================================

Provides team hierarchy and group-based permission management.

This module defines:
- Team: Group of agents with shared permissions
- TeamMembership: Agent's membership in a team
- TeamHierarchy: Tree structure for team inheritance

Palantir Pattern:
- Teams can have parent teams (hierarchical inheritance)
- Permissions flow down from parent to child teams
- Members inherit all permissions from their team and ancestors

Example:
    ```python
    # Create a team hierarchy
    engineering_team = Team(
        name="Engineering",
        members=["agent-001", "agent-002"],
        permissions=[
            ObjectTypePermission(object_type="Task", role_id="engineering", can_read=True)
        ]
    )

    # Create a sub-team
    backend_team = Team(
        name="Backend",
        parent_team_id=engineering_team.id,
        members=["agent-003"],
        permissions=[
            ObjectTypePermission(object_type="Database", role_id="backend", can_update=True)
        ]
    )
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.agent.object_permissions import ObjectTypePermission

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class TeamMembershipType(str, Enum):
    """Types of team membership."""
    MEMBER = "member"        # Regular member
    ADMIN = "admin"          # Team administrator
    OWNER = "owner"          # Team owner (full control)
    GUEST = "guest"          # Guest (limited access)


class TeamStatus(str, Enum):
    """Status of a team."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


# =============================================================================
# TEAM MEMBERSHIP
# =============================================================================


class TeamMembership(BaseModel):
    """
    Represents an agent's membership in a team.

    Attributes:
        agent_id: ID of the agent
        team_id: ID of the team
        membership_type: Type of membership (member, admin, owner, guest)
        joined_at: When the agent joined the team
        expires_at: Optional membership expiration
        added_by: ID of the actor who added this member

    Example:
        ```python
        membership = TeamMembership(
            agent_id="agent-123",
            team_id="team-456",
            membership_type=TeamMembershipType.MEMBER,
            added_by="admin-001",
        )
        ```
    """

    agent_id: str = Field(
        ...,
        description="ID of the agent",
        min_length=1,
    )
    team_id: str = Field(
        ...,
        description="ID of the team",
        min_length=1,
    )
    membership_type: TeamMembershipType = Field(
        default=TeamMembershipType.MEMBER,
        description="Type of membership",
    )
    joined_at: datetime = Field(
        default_factory=utc_now,
        description="When the agent joined the team",
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When membership expires (None = never)",
    )
    added_by: str = Field(
        default="system",
        description="ID of actor who added this member",
    )

    def is_expired(self) -> bool:
        """Check if membership has expired."""
        if self.expires_at is None:
            return False
        return utc_now() > self.expires_at

    def is_active(self) -> bool:
        """Check if membership is currently active."""
        return not self.is_expired()

    def can_manage_team(self) -> bool:
        """Check if member can manage the team."""
        return self.membership_type in (TeamMembershipType.ADMIN, TeamMembershipType.OWNER)

    def can_add_members(self) -> bool:
        """Check if member can add other members."""
        return self.membership_type in (TeamMembershipType.ADMIN, TeamMembershipType.OWNER)


# =============================================================================
# TEAM MODEL
# =============================================================================


class Team(OntologyObject):
    """
    Team/Group with hierarchical permissions.

    A Team groups agents together and provides shared permissions.
    Teams can have parent teams, enabling permission inheritance.

    Attributes:
        name: Human-readable team name
        description: Team description
        members: List of agent IDs in this team
        memberships: Detailed membership records
        parent_team_id: ID of parent team (for hierarchy)
        permissions: ObjectType permissions for this team
        status: Team status (active, inactive, archived)
        created_by: ID of actor who created the team

    Example:
        ```python
        team = Team(
            name="Backend Engineering",
            description="Backend development team",
            members=["agent-001", "agent-002"],
            permissions=[
                ObjectTypePermission(
                    object_type="Database",
                    role_id="backend",
                    can_read=True,
                    can_update=True,
                )
            ]
        )
        ```
    """

    name: str = Field(
        ...,
        description="Human-readable team name",
        min_length=1,
        max_length=255,
    )
    description: str = Field(
        default="",
        description="Team description",
        max_length=1000,
    )

    # Members
    members: List[str] = Field(
        default_factory=list,
        description="List of agent IDs in this team",
    )
    memberships: List[TeamMembership] = Field(
        default_factory=list,
        description="Detailed membership records",
    )

    # Hierarchy
    parent_team_id: Optional[str] = Field(
        default=None,
        description="ID of parent team (for hierarchy)",
    )

    # Permissions
    permissions: List[ObjectTypePermission] = Field(
        default_factory=list,
        description="ObjectType permissions for this team",
    )

    # Status and metadata
    status: TeamStatus = Field(
        default=TeamStatus.ACTIVE,
        description="Team status",
    )
    created_by: str = Field(
        default="system",
        description="ID of actor who created the team",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate team name."""
        if not v.strip():
            raise ValueError("Team name cannot be empty or whitespace")
        return v.strip()

    @model_validator(mode="after")
    def sync_members_and_memberships(self) -> "Team":
        """Ensure members list and memberships are in sync."""
        # Add members from memberships list if not in members
        for membership in self.memberships:
            if membership.agent_id not in self.members:
                self.members.append(membership.agent_id)
        return self

    def add_member(
        self,
        agent_id: str,
        membership_type: TeamMembershipType = TeamMembershipType.MEMBER,
        added_by: str = "system",
        expires_at: Optional[datetime] = None,
    ) -> TeamMembership:
        """
        Add a member to the team.

        Args:
            agent_id: ID of agent to add
            membership_type: Type of membership
            added_by: ID of actor adding the member
            expires_at: Optional membership expiration

        Returns:
            Created TeamMembership
        """
        if agent_id in self.members:
            # Update existing membership
            for m in self.memberships:
                if m.agent_id == agent_id:
                    m.membership_type = membership_type
                    m.expires_at = expires_at
                    return m

        # Create new membership
        membership = TeamMembership(
            agent_id=agent_id,
            team_id=self.id,
            membership_type=membership_type,
            added_by=added_by,
            expires_at=expires_at,
        )
        self.memberships.append(membership)
        self.members.append(agent_id)

        logger.info(f"Added {agent_id} to team {self.name} as {membership_type.value}")
        return membership

    def remove_member(self, agent_id: str) -> bool:
        """
        Remove a member from the team.

        Args:
            agent_id: ID of agent to remove

        Returns:
            True if member was removed
        """
        if agent_id not in self.members:
            return False

        self.members.remove(agent_id)
        self.memberships = [m for m in self.memberships if m.agent_id != agent_id]

        logger.info(f"Removed {agent_id} from team {self.name}")
        return True

    def get_membership(self, agent_id: str) -> Optional[TeamMembership]:
        """Get membership details for an agent."""
        for m in self.memberships:
            if m.agent_id == agent_id:
                return m
        return None

    def has_member(self, agent_id: str) -> bool:
        """Check if agent is a member."""
        return agent_id in self.members

    def get_active_members(self) -> List[str]:
        """Get list of active (non-expired) members."""
        active = set()
        for m in self.memberships:
            if m.is_active():
                active.add(m.agent_id)
        return list(active)

    def get_permission_for_object_type(
        self,
        object_type: str,
    ) -> Optional[ObjectTypePermission]:
        """Get permission for a specific ObjectType."""
        for perm in self.permissions:
            if perm.object_type == object_type and not perm.is_expired():
                return perm
        return None

    def add_permission(self, permission: ObjectTypePermission) -> None:
        """Add or update a permission."""
        # Remove existing permission for same object_type
        self.permissions = [
            p for p in self.permissions
            if p.object_type != permission.object_type
        ]
        self.permissions.append(permission)
        logger.info(
            f"Added permission for {permission.object_type} to team {self.name}"
        )

    def remove_permission(self, object_type: str) -> bool:
        """Remove permission for an ObjectType."""
        original_count = len(self.permissions)
        self.permissions = [
            p for p in self.permissions if p.object_type != object_type
        ]
        return len(self.permissions) < original_count

    def is_active(self) -> bool:
        """Check if team is active."""
        return self.status == TeamStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "members": self.members,
            "memberships": [m.model_dump() for m in self.memberships],
            "parent_team_id": self.parent_team_id,
            "permissions": [p.to_dict() for p in self.permissions],
            "status": self.status.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# =============================================================================
# TEAM REGISTRY
# =============================================================================


class TeamRegistry:
    """
    Registry for teams with hierarchy support.

    Provides lookup by ID, name, and hierarchy traversal.
    """

    def __init__(self):
        self._teams: Dict[str, Team] = {}
        # Index: parent_team_id -> List[child_team_id]
        self._children: Dict[str, List[str]] = {}

    def register(self, team: Team) -> None:
        """Register a team."""
        self._teams[team.id] = team

        # Update hierarchy index
        if team.parent_team_id:
            if team.parent_team_id not in self._children:
                self._children[team.parent_team_id] = []
            if team.id not in self._children[team.parent_team_id]:
                self._children[team.parent_team_id].append(team.id)

        logger.info(f"Registered team: {team.name} ({team.id})")

    def get(self, team_id: str) -> Optional[Team]:
        """Get team by ID."""
        return self._teams.get(team_id)

    def get_by_name(self, name: str) -> Optional[Team]:
        """Get team by name (case-insensitive)."""
        name_lower = name.lower()
        for team in self._teams.values():
            if team.name.lower() == name_lower:
                return team
        return None

    def remove(self, team_id: str) -> bool:
        """Remove a team."""
        if team_id not in self._teams:
            return False

        team = self._teams[team_id]

        # Remove from parent's children
        if team.parent_team_id and team.parent_team_id in self._children:
            if team_id in self._children[team.parent_team_id]:
                self._children[team.parent_team_id].remove(team_id)

        # Remove team's children index entry
        if team_id in self._children:
            del self._children[team_id]

        del self._teams[team_id]
        logger.info(f"Removed team: {team.name} ({team_id})")
        return True

    def get_children(self, team_id: str) -> List[Team]:
        """Get direct child teams."""
        child_ids = self._children.get(team_id, [])
        return [self._teams[cid] for cid in child_ids if cid in self._teams]

    def get_all_descendants(self, team_id: str) -> List[Team]:
        """Get all descendant teams (recursive)."""
        descendants = []
        children = self.get_children(team_id)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_all_descendants(child.id))
        return descendants

    def get_ancestors(self, team_id: str) -> List[Team]:
        """Get all ancestor teams (parent chain)."""
        ancestors = []
        team = self.get(team_id)
        while team and team.parent_team_id:
            parent = self.get(team.parent_team_id)
            if parent:
                ancestors.append(parent)
                team = parent
            else:
                break
        return ancestors

    def get_teams_for_agent(self, agent_id: str) -> List[Team]:
        """Get all teams an agent belongs to."""
        return [
            team for team in self._teams.values()
            if agent_id in team.members and team.is_active()
        ]

    def get_root_teams(self) -> List[Team]:
        """Get all root teams (no parent)."""
        return [
            team for team in self._teams.values()
            if team.parent_team_id is None
        ]

    def list_all(self) -> List[Team]:
        """List all registered teams."""
        return list(self._teams.values())

    def clear(self) -> None:
        """Clear all teams."""
        self._teams.clear()
        self._children.clear()


# Global registry instance
_team_registry: Optional[TeamRegistry] = None


def get_team_registry() -> TeamRegistry:
    """Get or create the global TeamRegistry."""
    global _team_registry
    if _team_registry is None:
        _team_registry = TeamRegistry()
    return _team_registry


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "TeamMembershipType",
    "TeamStatus",
    # Models
    "TeamMembership",
    "Team",
    # Registry
    "TeamRegistry",
    "get_team_registry",
]
