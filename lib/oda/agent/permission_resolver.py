"""
Orion ODA v4.0 - Permission Resolver (Phase 3.2.3)
===================================================

Unified permission resolution across all RBAC levels.

Resolution Order (highest to lowest priority):
    1. Instance-level permissions (per-object ACL)
    2. ObjectType-level permissions (for the agent's roles)
    3. Team permissions (from agent's team memberships)
    4. Role permissions (from existing PermissionManager)
    5. Default deny

This module provides:
- PermissionResolver: Unified resolution across all permission layers
- ResolvedPermission: Result of permission resolution with audit trail
- PermissionContext: Context for permission checks (object, action, etc.)

Palantir Pattern:
- Permissions flow from broad to narrow
- More specific permissions override general ones
- DENY always wins over GRANT at the same level
- Full audit trail for permission decisions

Example:
    ```python
    resolver = PermissionResolver()

    # Check if agent can update a specific task
    result = resolver.resolve(
        agent_id="agent-123",
        object_type="Task",
        operation="update",
        instance_id="task-456",  # Optional: for instance-level check
    )

    if result.allowed:
        print(f"Allowed by: {result.source}")
    else:
        print(f"Denied: {result.reason}")
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from lib.oda.ontology.ontology_types import utc_now

# Import permission models
from lib.oda.agent.object_permissions import (
    ObjectTypePermission,
    ObjectTypePermissionRegistry,
    get_object_permission_registry,
    PermissionType,
    FieldAccessLevel,
)
from lib.oda.agent.instance_permissions import (
    InstancePermission,
    InstancePermissionRegistry,
    get_instance_permission_registry,
)
from lib.oda.agent.teams import (
    Team,
    TeamRegistry,
    get_team_registry,
)
from lib.oda.agent.permissions import (
    PermissionManager,
    PermissionLevel,
    PermissionCheckResult,
    get_permission_manager,
    AgentIdentity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class PermissionSource(str, Enum):
    """Source of the permission decision."""
    INSTANCE = "instance"          # Instance-level permission
    OBJECT_TYPE = "object_type"    # ObjectType-level permission
    TEAM = "team"                  # Team permission
    ROLE = "role"                  # Role-based permission
    OWNER = "owner"                # Owner of the instance
    DIRECT = "direct"              # Direct agent permission
    DEFAULT = "default"            # Default (deny)


class Operation(str, Enum):
    """Standard CRUD operations."""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LINK = "link"


# =============================================================================
# RESOLUTION RESULT
# =============================================================================


@dataclass
class ResolvedPermission:
    """
    Result of a permission resolution.

    Attributes:
        allowed: Whether the operation is allowed
        level: Permission level (EXECUTE, PROPOSE, VIEW, DENY)
        source: Where the permission decision came from
        reason: Human-readable explanation
        checked_at: When the check was performed
        resolution_chain: Ordered list of sources checked
        matching_permission: The permission that matched (if any)
    """
    allowed: bool
    level: PermissionLevel = PermissionLevel.DENY
    source: PermissionSource = PermissionSource.DEFAULT
    reason: str = ""
    checked_at: datetime = field(default_factory=utc_now)
    resolution_chain: List[str] = field(default_factory=list)
    matching_permission: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "allowed": self.allowed,
            "level": self.level.value,
            "source": self.source.value,
            "reason": self.reason,
            "checked_at": self.checked_at.isoformat(),
            "resolution_chain": self.resolution_chain,
            "matching_permission": self.matching_permission,
        }


# =============================================================================
# PERMISSION CONTEXT
# =============================================================================


@dataclass
class PermissionContext:
    """
    Context for a permission check.

    Attributes:
        agent_id: ID of the agent requesting access
        object_type: Type of object being accessed
        operation: Operation being performed
        instance_id: Optional specific instance ID
        field_name: Optional specific field being accessed
        action_type: Optional action API name (for action-based checks)
        metadata: Additional context metadata
    """
    agent_id: str
    object_type: str
    operation: str
    instance_id: Optional[str] = None
    field_name: Optional[str] = None
    action_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PERMISSION RESOLVER
# =============================================================================


class PermissionResolver:
    """
    Unified permission resolver across all RBAC levels.

    Resolution Order:
        1. Instance permissions (if instance_id provided)
        2. ObjectType permissions (for agent's roles)
        3. Team permissions (inherited from teams)
        4. Role permissions (from PermissionManager)
        5. Default deny

    Usage:
        ```python
        resolver = PermissionResolver()

        result = resolver.resolve(
            agent_id="agent-123",
            object_type="Task",
            operation="update",
            instance_id="task-456",
        )

        if result.allowed:
            # Proceed with operation
            pass
        else:
            # Handle denial
            print(f"Denied: {result.reason}")
        ```
    """

    def __init__(
        self,
        permission_manager: Optional[PermissionManager] = None,
        object_permission_registry: Optional[ObjectTypePermissionRegistry] = None,
        instance_permission_registry: Optional[InstancePermissionRegistry] = None,
        team_registry: Optional[TeamRegistry] = None,
    ):
        """
        Initialize the resolver with registries.

        Args:
            permission_manager: Role/action permission manager
            object_permission_registry: ObjectType permission registry
            instance_permission_registry: Instance permission registry
            team_registry: Team registry
        """
        self._permission_manager = permission_manager or get_permission_manager()
        self._object_registry = object_permission_registry or get_object_permission_registry()
        self._instance_registry = instance_permission_registry or get_instance_permission_registry()
        self._team_registry = team_registry or get_team_registry()

    def resolve(
        self,
        agent_id: str,
        object_type: str,
        operation: str,
        instance_id: Optional[str] = None,
        field_name: Optional[str] = None,
    ) -> ResolvedPermission:
        """
        Resolve permission for an operation.

        Args:
            agent_id: ID of the agent requesting access
            object_type: Type of object being accessed
            operation: Operation (read, create, update, delete, link)
            instance_id: Optional specific instance ID
            field_name: Optional specific field

        Returns:
            ResolvedPermission with decision and audit trail
        """
        resolution_chain: List[str] = []
        context = PermissionContext(
            agent_id=agent_id,
            object_type=object_type,
            operation=operation,
            instance_id=instance_id,
            field_name=field_name,
        )

        # Get agent identity
        agent = self._permission_manager.get_agent(agent_id)
        if not agent:
            return ResolvedPermission(
                allowed=False,
                level=PermissionLevel.DENY,
                source=PermissionSource.DEFAULT,
                reason=f"Unknown agent: {agent_id}",
                resolution_chain=["agent_lookup:not_found"],
            )

        if not agent.is_active():
            return ResolvedPermission(
                allowed=False,
                level=PermissionLevel.DENY,
                source=PermissionSource.DEFAULT,
                reason="Agent is not active",
                resolution_chain=["agent_lookup:inactive"],
            )

        # 1. Check Instance Permissions (if instance_id provided)
        if instance_id:
            result = self._check_instance_permission(
                agent=agent,
                context=context,
                resolution_chain=resolution_chain,
            )
            if result is not None:
                return result

        # 2. Check ObjectType Permissions (for agent's roles)
        result = self._check_object_type_permission(
            agent=agent,
            context=context,
            resolution_chain=resolution_chain,
        )
        if result is not None:
            return result

        # 3. Check Team Permissions
        result = self._check_team_permission(
            agent=agent,
            context=context,
            resolution_chain=resolution_chain,
        )
        if result is not None:
            return result

        # 4. Check Role Permissions (from PermissionManager)
        result = self._check_role_permission(
            agent=agent,
            context=context,
            resolution_chain=resolution_chain,
        )
        if result is not None:
            return result

        # 5. Default Deny
        return ResolvedPermission(
            allowed=False,
            level=PermissionLevel.DENY,
            source=PermissionSource.DEFAULT,
            reason="No matching permission found",
            resolution_chain=resolution_chain,
        )

    def _check_instance_permission(
        self,
        agent: AgentIdentity,
        context: PermissionContext,
        resolution_chain: List[str],
    ) -> Optional[ResolvedPermission]:
        """Check instance-level permission."""
        resolution_chain.append("instance_check:start")

        instance_perm = self._instance_registry.get(context.instance_id)
        if not instance_perm:
            resolution_chain.append("instance_check:no_permission")
            return None

        # Check owner first
        if instance_perm.is_owner(agent.id):
            resolution_chain.append("instance_check:owner_match")
            return ResolvedPermission(
                allowed=True,
                level=PermissionLevel.EXECUTE,
                source=PermissionSource.OWNER,
                reason="Agent is owner of this instance",
                resolution_chain=resolution_chain,
                matching_permission=instance_perm.id,
            )

        # Check explicit grants for agent
        result = instance_perm.check_operation("agent", agent.id, context.operation)
        if result is not None:
            resolution_chain.append(f"instance_check:agent_grant:{result}")
            return ResolvedPermission(
                allowed=result,
                level=PermissionLevel.EXECUTE if result else PermissionLevel.DENY,
                source=PermissionSource.INSTANCE,
                reason=f"Instance {'grants' if result else 'denies'} {context.operation}",
                resolution_chain=resolution_chain,
                matching_permission=instance_perm.id,
            )

        # Check grants for agent's teams
        for team_id in agent.team_ids:
            result = instance_perm.check_operation("team", team_id, context.operation)
            if result is not None:
                resolution_chain.append(f"instance_check:team_grant:{team_id}:{result}")
                return ResolvedPermission(
                    allowed=result,
                    level=PermissionLevel.EXECUTE if result else PermissionLevel.DENY,
                    source=PermissionSource.INSTANCE,
                    reason=f"Instance team grant {'allows' if result else 'denies'} {context.operation}",
                    resolution_chain=resolution_chain,
                    matching_permission=instance_perm.id,
                )

        # Check grants for agent's roles
        for role_id in agent.roles:
            result = instance_perm.check_operation("role", role_id, context.operation)
            if result is not None:
                resolution_chain.append(f"instance_check:role_grant:{role_id}:{result}")
                return ResolvedPermission(
                    allowed=result,
                    level=PermissionLevel.EXECUTE if result else PermissionLevel.DENY,
                    source=PermissionSource.INSTANCE,
                    reason=f"Instance role grant {'allows' if result else 'denies'} {context.operation}",
                    resolution_chain=resolution_chain,
                    matching_permission=instance_perm.id,
                )

        # Check if we should inherit from ObjectType
        if not instance_perm.inherit_from_object_type:
            resolution_chain.append("instance_check:no_inherit")
            return ResolvedPermission(
                allowed=False,
                level=PermissionLevel.DENY,
                source=PermissionSource.INSTANCE,
                reason="Instance permission set to not inherit from ObjectType",
                resolution_chain=resolution_chain,
                matching_permission=instance_perm.id,
            )

        resolution_chain.append("instance_check:no_match")
        return None

    def _check_object_type_permission(
        self,
        agent: AgentIdentity,
        context: PermissionContext,
        resolution_chain: List[str],
    ) -> Optional[ResolvedPermission]:
        """Check ObjectType-level permission for agent's roles."""
        resolution_chain.append("object_type_check:start")

        for role_id in agent.roles:
            perm = self._object_registry.get(context.object_type, role_id)
            if perm and not perm.is_expired():
                allowed = self._check_operation_on_object_permission(perm, context.operation)
                if allowed is not None:
                    resolution_chain.append(f"object_type_check:{role_id}:{allowed}")

                    # Check field restriction if field_name provided
                    if context.field_name and not allowed:
                        if not perm.can_access_field(context.field_name, context.operation):
                            return ResolvedPermission(
                                allowed=False,
                                level=PermissionLevel.DENY,
                                source=PermissionSource.OBJECT_TYPE,
                                reason=f"Field '{context.field_name}' is restricted",
                                resolution_chain=resolution_chain,
                                matching_permission=perm.id,
                            )

                    return ResolvedPermission(
                        allowed=allowed,
                        level=PermissionLevel.EXECUTE if allowed else PermissionLevel.DENY,
                        source=PermissionSource.OBJECT_TYPE,
                        reason=f"ObjectType permission for role '{role_id}'",
                        resolution_chain=resolution_chain,
                        matching_permission=perm.id,
                    )

        resolution_chain.append("object_type_check:no_match")
        return None

    def _check_team_permission(
        self,
        agent: AgentIdentity,
        context: PermissionContext,
        resolution_chain: List[str],
    ) -> Optional[ResolvedPermission]:
        """Check team-based permissions with inheritance."""
        resolution_chain.append("team_check:start")

        # Get all teams for agent (including ancestor teams)
        teams_to_check = self._get_all_teams_for_agent(agent)

        for team in teams_to_check:
            if not team.is_active():
                continue

            perm = team.get_permission_for_object_type(context.object_type)
            if perm and not perm.is_expired():
                allowed = self._check_operation_on_object_permission(perm, context.operation)
                if allowed is not None:
                    resolution_chain.append(f"team_check:{team.name}:{allowed}")
                    return ResolvedPermission(
                        allowed=allowed,
                        level=PermissionLevel.EXECUTE if allowed else PermissionLevel.DENY,
                        source=PermissionSource.TEAM,
                        reason=f"Team '{team.name}' permission",
                        resolution_chain=resolution_chain,
                        matching_permission=perm.id,
                    )

        resolution_chain.append("team_check:no_match")
        return None

    def _check_role_permission(
        self,
        agent: AgentIdentity,
        context: PermissionContext,
        resolution_chain: List[str],
    ) -> Optional[ResolvedPermission]:
        """Check role-based permissions from PermissionManager."""
        resolution_chain.append("role_check:start")

        # Map object operation to action pattern
        action_pattern = f"{context.object_type.lower()}.{context.operation}"

        # Use existing PermissionManager
        result = self._permission_manager.check_permission(
            agent_id=agent.id,
            action_type=action_pattern,
        )

        if result.level != PermissionLevel.DENY:
            resolution_chain.append(f"role_check:{result.role}:{result.allowed}")
            return ResolvedPermission(
                allowed=result.allowed,
                level=result.level,
                source=PermissionSource.ROLE,
                reason=result.reason,
                resolution_chain=resolution_chain,
            )

        # Try with wildcard pattern
        wildcard_pattern = f"{context.object_type.lower()}.*"
        result = self._permission_manager.check_permission(
            agent_id=agent.id,
            action_type=wildcard_pattern,
        )

        if result.level != PermissionLevel.DENY:
            resolution_chain.append(f"role_check:wildcard:{result.allowed}")
            return ResolvedPermission(
                allowed=result.allowed,
                level=result.level,
                source=PermissionSource.ROLE,
                reason=result.reason,
                resolution_chain=resolution_chain,
            )

        resolution_chain.append("role_check:no_match")
        return None

    def _check_operation_on_object_permission(
        self,
        perm: ObjectTypePermission,
        operation: str,
    ) -> Optional[bool]:
        """Check if operation is allowed by ObjectTypePermission."""
        op_map = {
            "read": perm.can_read,
            "create": perm.can_create,
            "update": perm.can_update,
            "delete": perm.can_delete,
            "link": perm.can_link,
        }
        return op_map.get(operation)

    def _get_all_teams_for_agent(self, agent: AgentIdentity) -> List[Team]:
        """
        Get all teams for an agent, including ancestor teams.

        Teams are ordered by specificity: direct teams first, then ancestors.
        """
        all_teams: List[Team] = []
        seen_ids: Set[str] = set()

        for team_id in agent.team_ids:
            team = self._team_registry.get(team_id)
            if team and team.id not in seen_ids:
                all_teams.append(team)
                seen_ids.add(team.id)

                # Add ancestor teams
                ancestors = self._team_registry.get_ancestors(team.id)
                for ancestor in ancestors:
                    if ancestor.id not in seen_ids:
                        all_teams.append(ancestor)
                        seen_ids.add(ancestor.id)

        return all_teams

    def can_access_field(
        self,
        agent_id: str,
        object_type: str,
        field_name: str,
        operation: str = "read",
        instance_id: Optional[str] = None,
    ) -> tuple[bool, FieldAccessLevel]:
        """
        Check if agent can access a specific field.

        Returns:
            Tuple of (allowed, access_level)
        """
        # First check if basic operation is allowed
        result = self.resolve(
            agent_id=agent_id,
            object_type=object_type,
            operation=operation,
            instance_id=instance_id,
            field_name=field_name,
        )

        if not result.allowed:
            return (False, FieldAccessLevel.HIDDEN)

        # Check instance field restriction
        if instance_id:
            instance_perm = self._instance_registry.get(instance_id)
            if instance_perm:
                level = instance_perm.get_field_access_level(field_name)
                if level != FieldAccessLevel.FULL:
                    return (level != FieldAccessLevel.HIDDEN, level)

        # Check ObjectType field restriction
        agent = self._permission_manager.get_agent(agent_id)
        if agent:
            for role_id in agent.roles:
                perm = self._object_registry.get(object_type, role_id)
                if perm:
                    level = perm.get_field_access_level(field_name)
                    if level != FieldAccessLevel.FULL:
                        return (level != FieldAccessLevel.HIDDEN, level)

        return (True, FieldAccessLevel.FULL)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


_permission_resolver: Optional[PermissionResolver] = None


def get_permission_resolver() -> PermissionResolver:
    """Get or create the global PermissionResolver."""
    global _permission_resolver
    if _permission_resolver is None:
        _permission_resolver = PermissionResolver()
    return _permission_resolver


def resolve_permission(
    agent_id: str,
    object_type: str,
    operation: str,
    instance_id: Optional[str] = None,
) -> ResolvedPermission:
    """
    Quick permission resolution using global resolver.

    Args:
        agent_id: Agent requesting access
        object_type: Type of object
        operation: Operation to perform
        instance_id: Optional specific instance

    Returns:
        ResolvedPermission with decision
    """
    return get_permission_resolver().resolve(
        agent_id=agent_id,
        object_type=object_type,
        operation=operation,
        instance_id=instance_id,
    )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "PermissionSource",
    "Operation",
    # Result types
    "ResolvedPermission",
    "PermissionContext",
    # Resolver
    "PermissionResolver",
    "get_permission_resolver",
    "resolve_permission",
]
