"""
Orion ODA v4.0 - Agent Permission Checks (Phase 7.3.4)
======================================================

Agent permission system for role-based access control:
- AgentPermission model for defining permissions
- Permission checking before action execution
- Role-based access control (RBAC)
- Integration with GovernanceEngine

Permission Levels:
    - EXECUTE: Can execute the action
    - PROPOSE: Can only create proposals
    - VIEW: Can view but not execute
    - DENY: Explicitly denied
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import GovernanceEngine, action_registry, PolicyResult
from lib.oda.ontology.ontology_types import utc_now

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class PermissionLevel(str, Enum):
    """Permission levels for actions."""
    EXECUTE = "execute"    # Can execute directly
    PROPOSE = "propose"    # Can create proposals only
    VIEW = "view"          # Can view/read only
    DENY = "deny"          # Explicitly denied


class RoleType(str, Enum):
    """Predefined role types."""
    ADMIN = "admin"              # Full access
    OPERATOR = "operator"        # Execute most actions
    DEVELOPER = "developer"      # Execute safe actions
    AUDITOR = "auditor"          # View only
    AGENT = "agent"              # Limited agent access
    GUEST = "guest"              # Minimal access


# =============================================================================
# PERMISSION MODELS
# =============================================================================

class ActionPermission(BaseModel):
    """Permission definition for a specific action or action pattern."""
    pattern: str = Field(..., description="Action pattern (e.g., 'file.*', 'memory.save')")
    level: PermissionLevel = Field(default=PermissionLevel.DENY)
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Additional conditions")
    expires_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

    def matches(self, action_type: str) -> bool:
        """Check if this permission matches an action type."""
        if self.pattern == "*":
            return True
        if self.pattern.endswith(".*"):
            prefix = self.pattern[:-2]
            return action_type.startswith(prefix + ".")
        return self.pattern == action_type

    def is_expired(self) -> bool:
        """Check if permission has expired."""
        if self.expires_at:
            return utc_now() > self.expires_at
        return False


class AgentRole(BaseModel):
    """Role definition with associated permissions."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Role name")
    role_type: RoleType = Field(default=RoleType.AGENT)
    description: str = Field(default="")

    # Permissions
    permissions: List[ActionPermission] = Field(default_factory=list)

    # Inheritance
    inherits_from: List[str] = Field(default_factory=list, description="Role IDs to inherit from")

    # Metadata
    created_at: datetime = Field(default_factory=utc_now)
    created_by: str = Field(default="system")

    class Config:
        arbitrary_types_allowed = True

    def get_permission(self, action_type: str) -> Optional[ActionPermission]:
        """Get the most specific permission for an action."""
        # Sort by specificity (longer patterns first, * last)
        sorted_perms = sorted(
            self.permissions,
            key=lambda p: (0 if p.pattern == "*" else len(p.pattern)),
            reverse=True,
        )

        for perm in sorted_perms:
            if perm.matches(action_type) and not perm.is_expired():
                return perm

        return None


class AgentIdentity(BaseModel):
    """Identity and permissions for an agent."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(default="agent")
    agent_type: str = Field(default="general", description="Type of agent")

    # Roles
    roles: List[str] = Field(default_factory=list, description="Assigned role IDs")

    # Teams (Phase 3.2.1: Team-based RBAC)
    team_ids: List[str] = Field(default_factory=list, description="Team IDs the agent belongs to")

    # Direct permissions (override role permissions)
    direct_permissions: List[ActionPermission] = Field(default_factory=list)

    # Session context
    session_id: str = Field(default="")
    active: bool = Field(default=True)
    expires_at: Optional[datetime] = None

    # Trust level
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0)

    # Metadata
    created_at: datetime = Field(default_factory=utc_now)
    last_activity: datetime = Field(default_factory=utc_now)

    class Config:
        arbitrary_types_allowed = True

    def is_active(self) -> bool:
        """Check if identity is currently active."""
        if not self.active:
            return False
        if self.expires_at and utc_now() > self.expires_at:
            return False
        return True

    def add_team(self, team_id: str) -> bool:
        """Add agent to a team."""
        if team_id not in self.team_ids:
            self.team_ids.append(team_id)
            return True
        return False

    def remove_team(self, team_id: str) -> bool:
        """Remove agent from a team."""
        if team_id in self.team_ids:
            self.team_ids.remove(team_id)
            return True
        return False

    def has_team(self, team_id: str) -> bool:
        """Check if agent belongs to a team."""
        return team_id in self.team_ids


@dataclass
class PermissionCheckResult:
    """Result of a permission check."""
    allowed: bool
    level: PermissionLevel
    reason: str = ""
    permission: Optional[ActionPermission] = None
    role: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "level": self.level.value,
            "reason": self.reason,
            "role": self.role,
        }


# =============================================================================
# PREDEFINED ROLES
# =============================================================================

def create_admin_role() -> AgentRole:
    """Create admin role with full access."""
    return AgentRole(
        name="Administrator",
        role_type=RoleType.ADMIN,
        description="Full system access",
        permissions=[
            ActionPermission(pattern="*", level=PermissionLevel.EXECUTE),
        ],
    )


def create_operator_role() -> AgentRole:
    """Create operator role with execution access."""
    return AgentRole(
        name="Operator",
        role_type=RoleType.OPERATOR,
        description="Execute most operations",
        permissions=[
            ActionPermission(pattern="*", level=PermissionLevel.EXECUTE),
            # Deny dangerous operations
            ActionPermission(pattern="system.shutdown", level=PermissionLevel.DENY),
            ActionPermission(pattern="database.drop", level=PermissionLevel.DENY),
        ],
    )


def create_developer_role() -> AgentRole:
    """Create developer role with limited execution."""
    return AgentRole(
        name="Developer",
        role_type=RoleType.DEVELOPER,
        description="Execute safe operations",
        permissions=[
            # File operations
            ActionPermission(pattern="file.read", level=PermissionLevel.EXECUTE),
            ActionPermission(pattern="file.write", level=PermissionLevel.PROPOSE),
            ActionPermission(pattern="file.delete", level=PermissionLevel.PROPOSE),
            # Memory operations
            ActionPermission(pattern="memory.*", level=PermissionLevel.EXECUTE),
            # Learning operations
            ActionPermission(pattern="learning.*", level=PermissionLevel.EXECUTE),
            # Default to propose
            ActionPermission(pattern="*", level=PermissionLevel.PROPOSE),
        ],
    )


def create_auditor_role() -> AgentRole:
    """Create auditor role with view-only access."""
    return AgentRole(
        name="Auditor",
        role_type=RoleType.AUDITOR,
        description="View-only access for auditing",
        permissions=[
            ActionPermission(pattern="*", level=PermissionLevel.VIEW),
        ],
    )


def create_agent_role() -> AgentRole:
    """Create standard agent role."""
    return AgentRole(
        name="Agent",
        role_type=RoleType.AGENT,
        description="Standard agent permissions",
        permissions=[
            # Allow safe read operations
            ActionPermission(pattern="file.read", level=PermissionLevel.EXECUTE),
            ActionPermission(pattern="memory.save_insight", level=PermissionLevel.EXECUTE),
            ActionPermission(pattern="memory.save_pattern", level=PermissionLevel.EXECUTE),
            ActionPermission(pattern="learning.*", level=PermissionLevel.EXECUTE),
            ActionPermission(pattern="llm.*", level=PermissionLevel.EXECUTE),
            # Require proposals for mutations
            ActionPermission(pattern="file.write", level=PermissionLevel.PROPOSE),
            ActionPermission(pattern="file.modify", level=PermissionLevel.PROPOSE),
            ActionPermission(pattern="file.delete", level=PermissionLevel.PROPOSE),
            # Default deny
            ActionPermission(pattern="*", level=PermissionLevel.DENY),
        ],
    )


def create_guest_role() -> AgentRole:
    """Create guest role with minimal access."""
    return AgentRole(
        name="Guest",
        role_type=RoleType.GUEST,
        description="Minimal read-only access",
        permissions=[
            ActionPermission(pattern="file.read", level=PermissionLevel.VIEW),
            ActionPermission(pattern="*", level=PermissionLevel.DENY),
        ],
    )


# =============================================================================
# PERMISSION MANAGER
# =============================================================================

class PermissionManager:
    """
    Manages agent permissions and role-based access control.

    Provides:
    - Role management
    - Agent identity management
    - Permission checking
    - Integration with GovernanceEngine

    Usage:
        ```python
        manager = PermissionManager()

        # Register agent
        agent = manager.register_agent("agent-001", roles=["agent"])

        # Check permission
        result = manager.check_permission("agent-001", "file.delete")
        if result.allowed:
            # Execute action
            pass
        else:
            print(f"Denied: {result.reason}")
        ```
    """

    def __init__(
        self,
        governance: Optional[GovernanceEngine] = None,
        load_defaults: bool = True,
    ):
        """
        Initialize the permission manager.

        Args:
            governance: GovernanceEngine for policy integration
            load_defaults: If True, load predefined roles
        """
        self.governance = governance or GovernanceEngine(action_registry)

        self._roles: Dict[str, AgentRole] = {}
        self._agents: Dict[str, AgentIdentity] = {}

        if load_defaults:
            self._load_default_roles()

    def _load_default_roles(self) -> None:
        """Load predefined roles."""
        default_roles = [
            create_admin_role(),
            create_operator_role(),
            create_developer_role(),
            create_auditor_role(),
            create_agent_role(),
            create_guest_role(),
        ]

        for role in default_roles:
            self._roles[role.role_type.value] = role

    # =========================================================================
    # ROLE MANAGEMENT
    # =========================================================================

    def register_role(self, role: AgentRole) -> None:
        """Register a custom role."""
        self._roles[role.id] = role
        logger.info(f"Registered role: {role.name} ({role.id})")

    def get_role(self, role_id: str) -> Optional[AgentRole]:
        """Get a role by ID."""
        return self._roles.get(role_id)

    def list_roles(self) -> List[AgentRole]:
        """List all registered roles."""
        return list(self._roles.values())

    # =========================================================================
    # AGENT MANAGEMENT
    # =========================================================================

    def register_agent(
        self,
        agent_id: str,
        name: str = "",
        roles: Optional[List[str]] = None,
        agent_type: str = "general",
        trust_score: float = 0.5,
    ) -> AgentIdentity:
        """
        Register an agent with roles.

        Args:
            agent_id: Unique agent identifier
            name: Human-readable name
            roles: List of role IDs to assign
            agent_type: Type of agent
            trust_score: Initial trust score (0-1)

        Returns:
            Created AgentIdentity
        """
        # Default to standard agent role
        assigned_roles = roles or [RoleType.AGENT.value]

        identity = AgentIdentity(
            id=agent_id,
            name=name or agent_id,
            agent_type=agent_type,
            roles=assigned_roles,
            trust_score=trust_score,
        )

        self._agents[agent_id] = identity
        logger.info(f"Registered agent: {agent_id} with roles {assigned_roles}")

        return identity

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get an agent identity by ID."""
        return self._agents.get(agent_id)

    def update_agent_trust(self, agent_id: str, delta: float) -> Optional[float]:
        """
        Update an agent's trust score.

        Args:
            agent_id: Agent ID
            delta: Change to trust score (-1 to 1)

        Returns:
            New trust score, or None if agent not found
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.trust_score = max(0.0, min(1.0, agent.trust_score + delta))
            agent.last_activity = utc_now()
            return agent.trust_score
        return None

    def deactivate_agent(self, agent_id: str) -> bool:
        """
        Deactivate an agent.

        Returns:
            True if agent was deactivated, False if not found
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.active = False
            logger.info(f"Deactivated agent: {agent_id}")
            return True
        return False

    # =========================================================================
    # PERMISSION CHECKING
    # =========================================================================

    def check_permission(
        self,
        agent_id: str,
        action_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheckResult:
        """
        Check if an agent has permission for an action.

        Args:
            agent_id: Agent ID
            action_type: Action API name
            params: Optional action parameters for context

        Returns:
            PermissionCheckResult with decision and reason
        """
        # Get agent identity
        agent = self._agents.get(agent_id)
        if not agent:
            # Unknown agent - use default minimal permissions
            return PermissionCheckResult(
                allowed=False,
                level=PermissionLevel.DENY,
                reason=f"Unknown agent: {agent_id}",
            )

        # Check if agent is active
        if not agent.is_active():
            return PermissionCheckResult(
                allowed=False,
                level=PermissionLevel.DENY,
                reason="Agent is not active",
            )

        # Check direct permissions first (highest priority)
        for perm in agent.direct_permissions:
            if perm.matches(action_type) and not perm.is_expired():
                return self._evaluate_permission(perm, "direct")

        # Check role permissions
        for role_id in agent.roles:
            role = self._roles.get(role_id)
            if not role:
                continue

            perm = role.get_permission(action_type)
            if perm:
                return self._evaluate_permission(perm, role.name)

        # No matching permission found
        return PermissionCheckResult(
            allowed=False,
            level=PermissionLevel.DENY,
            reason="No matching permission found",
        )

    def _evaluate_permission(
        self,
        perm: ActionPermission,
        source: str,
    ) -> PermissionCheckResult:
        """Evaluate a permission and return result."""
        if perm.level == PermissionLevel.EXECUTE:
            return PermissionCheckResult(
                allowed=True,
                level=PermissionLevel.EXECUTE,
                reason=f"Allowed by {source}",
                permission=perm,
                role=source,
            )
        elif perm.level == PermissionLevel.PROPOSE:
            return PermissionCheckResult(
                allowed=True,  # Allowed to propose
                level=PermissionLevel.PROPOSE,
                reason=f"Proposal required by {source}",
                permission=perm,
                role=source,
            )
        elif perm.level == PermissionLevel.VIEW:
            return PermissionCheckResult(
                allowed=False,
                level=PermissionLevel.VIEW,
                reason=f"View only access by {source}",
                permission=perm,
                role=source,
            )
        else:  # DENY
            return PermissionCheckResult(
                allowed=False,
                level=PermissionLevel.DENY,
                reason=f"Denied by {source}",
                permission=perm,
                role=source,
            )

    def check_with_governance(
        self,
        agent_id: str,
        action_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheckResult:
        """
        Check permission with governance policy integration.

        Combines permission check with GovernanceEngine policy check.

        Args:
            agent_id: Agent ID
            action_type: Action API name
            params: Optional action parameters

        Returns:
            Combined PermissionCheckResult
        """
        # First check agent permissions
        perm_result = self.check_permission(agent_id, action_type, params)

        if not perm_result.allowed and perm_result.level == PermissionLevel.DENY:
            return perm_result

        # Then check governance policy
        policy_result: PolicyResult = self.governance.check_execution_policy(
            action_type,
            params or {},
        )

        if policy_result.is_blocked():
            return PermissionCheckResult(
                allowed=False,
                level=PermissionLevel.DENY,
                reason=f"Governance: {policy_result.reason}",
            )

        if policy_result.decision == "REQUIRE_PROPOSAL":
            # Override to PROPOSE if not already EXECUTE
            if perm_result.level != PermissionLevel.EXECUTE:
                return PermissionCheckResult(
                    allowed=True,
                    level=PermissionLevel.PROPOSE,
                    reason=f"Governance requires proposal: {policy_result.reason}",
                    role=perm_result.role,
                )

        return perm_result

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def grant_permission(
        self,
        agent_id: str,
        action_pattern: str,
        level: PermissionLevel,
        expires_in_hours: Optional[float] = None,
    ) -> bool:
        """
        Grant a direct permission to an agent.

        Args:
            agent_id: Agent ID
            action_pattern: Action pattern (e.g., 'file.*')
            level: Permission level
            expires_in_hours: Optional expiration time

        Returns:
            True if permission was granted
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        expires_at = None
        if expires_in_hours:
            from datetime import timedelta
            expires_at = utc_now() + timedelta(hours=expires_in_hours)

        perm = ActionPermission(
            pattern=action_pattern,
            level=level,
            expires_at=expires_at,
        )

        agent.direct_permissions.append(perm)
        logger.info(f"Granted {level.value} permission for {action_pattern} to {agent_id}")

        return True

    def revoke_permission(
        self,
        agent_id: str,
        action_pattern: str,
    ) -> bool:
        """
        Revoke a direct permission from an agent.

        Args:
            agent_id: Agent ID
            action_pattern: Action pattern to revoke

        Returns:
            True if permission was revoked
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        original_count = len(agent.direct_permissions)
        agent.direct_permissions = [
            p for p in agent.direct_permissions
            if p.pattern != action_pattern
        ]

        revoked = len(agent.direct_permissions) < original_count
        if revoked:
            logger.info(f"Revoked permission for {action_pattern} from {agent_id}")

        return revoked

    def assign_role(self, agent_id: str, role_id: str) -> bool:
        """
        Assign a role to an agent.

        Args:
            agent_id: Agent ID
            role_id: Role ID to assign

        Returns:
            True if role was assigned
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        if role_id not in self._roles:
            return False

        if role_id not in agent.roles:
            agent.roles.append(role_id)
            logger.info(f"Assigned role {role_id} to {agent_id}")

        return True

    def remove_role(self, agent_id: str, role_id: str) -> bool:
        """
        Remove a role from an agent.

        Args:
            agent_id: Agent ID
            role_id: Role ID to remove

        Returns:
            True if role was removed
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        if role_id in agent.roles:
            agent.roles.remove(role_id)
            logger.info(f"Removed role {role_id} from {agent_id}")
            return True

        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """Get or create the global PermissionManager instance."""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def check_permission(agent_id: str, action_type: str) -> PermissionCheckResult:
    """
    Quick permission check using global manager.

    Args:
        agent_id: Agent ID
        action_type: Action API name

    Returns:
        PermissionCheckResult
    """
    return get_permission_manager().check_permission(agent_id, action_type)


__all__ = [
    "PermissionLevel",
    "RoleType",
    "ActionPermission",
    "AgentRole",
    "AgentIdentity",
    "PermissionCheckResult",
    "PermissionManager",
    "get_permission_manager",
    "check_permission",
    # Role factories
    "create_admin_role",
    "create_operator_role",
    "create_developer_role",
    "create_auditor_role",
    "create_agent_role",
    "create_guest_role",
]
