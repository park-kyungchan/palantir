"""
Orion ODA v4.0 - RBAC Actions (Phase 3.3.1)
============================================

Actions for Role-Based Access Control management.

Hazardous Actions (require proposal):
- rbac.grant_object: Grant ObjectType permission to a role
- rbac.revoke_object: Revoke ObjectType permission from a role
- rbac.create_team: Create a new team
- rbac.add_member: Add member to a team

Non-hazardous Actions:
- rbac.check: Check permission for an agent/object/operation
- rbac.list_permissions: List permissions for an object type or role
- rbac.get_team: Get team details

Example:
    ```python
    from lib.oda.ontology.actions import action_registry, ActionContext

    # Create a team
    CreateTeamAction = action_registry.get("rbac.create_team")
    action = CreateTeamAction()
    result = await action.execute(
        params={
            "name": "Backend Team",
            "description": "Backend development team",
            "members": ["agent-001", "agent-002"],
        },
        context=ActionContext(actor_id="admin-001")
    )
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Type

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    AllowedValues,
    SubmissionCriterion,
    ValidationError,
    register_action,
)
from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.agent.object_permissions import (
    ObjectTypePermission,
    get_object_permission_registry,
    PermissionType,
    FieldPermission,
)
from lib.oda.agent.instance_permissions import (
    InstancePermission,
    get_instance_permission_registry,
)
from lib.oda.agent.teams import (
    Team,
    TeamMembershipType,
    get_team_registry,
)
from lib.oda.agent.permission_resolver import (
    PermissionResolver,
    get_permission_resolver,
    ResolvedPermission,
)
from lib.oda.agent.permissions import (
    get_permission_manager,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM VALIDATORS
# =============================================================================


class ValidOperationValue(SubmissionCriterion):
    """Validates that operation is a valid CRUD operation."""

    def __init__(self, field_name: str = "operation"):
        self.field_name = field_name
        self._valid_operations = {"read", "create", "update", "delete", "link"}

    @property
    def name(self) -> str:
        return f"ValidOperation({self.field_name})"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        value = params.get(self.field_name)
        if value is None:
            return True

        if isinstance(value, str) and value in self._valid_operations:
            return True

        raise ValidationError(
            criterion=self.name,
            message=f"Invalid operation: '{value}'. Valid: {self._valid_operations}",
            details={"field": self.field_name, "value": value}
        )


class ValidPrincipalType(SubmissionCriterion):
    """Validates principal_type field."""

    def __init__(self, field_name: str = "principal_type"):
        self.field_name = field_name
        self._valid_types = {"agent", "team", "role"}

    @property
    def name(self) -> str:
        return f"ValidPrincipalType({self.field_name})"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        value = params.get(self.field_name)
        if value is None:
            return True

        if value in self._valid_types:
            return True

        raise ValidationError(
            criterion=self.name,
            message=f"Invalid principal_type: '{value}'. Valid: {self._valid_types}",
            details={"field": self.field_name, "value": value}
        )


# =============================================================================
# GRANT OBJECT PERMISSION ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class GrantObjectPermissionAction(ActionType[OntologyObject]):
    """
    Grant ObjectType-level permission to a role.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        object_type: Name of the ObjectType
        role_id: ID of the role to grant permission to
        can_read: Allow read operations (default: True)
        can_create: Allow create operations (default: False)
        can_update: Allow update operations (default: False)
        can_delete: Allow delete operations (default: False)
        can_link: Allow link operations (default: False)
        field_restrictions: Optional field-level restrictions
        expires_in_hours: Optional permission expiration (hours)

    Returns:
        ActionResult with created ObjectTypePermission
    """

    api_name: ClassVar[str] = "rbac.grant_object"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("object_type"),
        RequiredField("role_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """Apply the permission grant."""
        object_type_name = params["object_type"]
        role_id = params["role_id"]

        # Calculate expiration if specified
        expires_at = None
        if params.get("expires_in_hours"):
            from datetime import timedelta
            from lib.oda.ontology.ontology_types import utc_now
            expires_at = utc_now() + timedelta(hours=params["expires_in_hours"])

        # Build field restrictions
        field_restrictions = {}
        if params.get("field_restrictions"):
            for field_name, restriction in params["field_restrictions"].items():
                field_restrictions[field_name] = FieldPermission(
                    field_name=field_name,
                    **restriction
                )

        # Create permission
        permission = ObjectTypePermission(
            object_type=object_type_name,
            role_id=role_id,
            can_read=params.get("can_read", True),
            can_create=params.get("can_create", False),
            can_update=params.get("can_update", False),
            can_delete=params.get("can_delete", False),
            can_link=params.get("can_link", False),
            field_restrictions=field_restrictions,
            expires_at=expires_at,
        )

        # Register permission
        registry = get_object_permission_registry()
        registry.register(permission)

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="ObjectTypePermission",
            object_id=permission.id,
            changes={
                "object_type": object_type_name,
                "role_id": role_id,
                "permissions": {
                    "read": permission.can_read,
                    "create": permission.can_create,
                    "update": permission.can_update,
                    "delete": permission.can_delete,
                    "link": permission.can_link,
                },
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Granted {object_type_name} permissions to role {role_id} by {context.actor_id}"
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=permission.to_dict(),
            edits=[edit],
            created_ids=[permission.id],
            message=f"Granted {object_type_name} permissions to role {role_id}",
        )


# =============================================================================
# REVOKE OBJECT PERMISSION ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class RevokeObjectPermissionAction(ActionType[OntologyObject]):
    """
    Revoke ObjectType-level permission from a role.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        object_type: Name of the ObjectType
        role_id: ID of the role to revoke permission from

    Returns:
        ActionResult indicating success/failure
    """

    api_name: ClassVar[str] = "rbac.revoke_object"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("object_type"),
        RequiredField("role_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """Apply the permission revocation."""
        object_type_name = params["object_type"]
        role_id = params["role_id"]

        registry = get_object_permission_registry()

        # Get existing permission
        existing = registry.get(object_type_name, role_id)
        if not existing:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error="Permission not found",
                error_details={
                    "object_type": object_type_name,
                    "role_id": role_id,
                },
            )

        # Remove permission
        removed = registry.remove(object_type_name, role_id)

        if not removed:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error="Failed to remove permission",
            )

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.DELETE,
            object_type="ObjectTypePermission",
            object_id=existing.id,
            changes={
                "object_type": object_type_name,
                "role_id": role_id,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Revoked {object_type_name} permissions from role {role_id} by {context.actor_id}"
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={"revoked_permission_id": existing.id},
            edits=[edit],
            deleted_ids=[existing.id],
            message=f"Revoked {object_type_name} permissions from role {role_id}",
        )


# =============================================================================
# CREATE TEAM ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class CreateTeamAction(ActionType[Team]):
    """
    Create a new team.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        name: Team name
        description: Optional team description
        members: Optional initial member IDs
        parent_team_id: Optional parent team for hierarchy
        permissions: Optional initial ObjectType permissions

    Returns:
        ActionResult with created Team
    """

    api_name: ClassVar[str] = "rbac.create_team"
    object_type: ClassVar[Type[Team]] = Team
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("name"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[Team], List[EditOperation]]:
        """Create the team."""
        name = params["name"]
        description = params.get("description", "")
        members = params.get("members", [])
        parent_team_id = params.get("parent_team_id")

        # Validate parent team exists if specified
        registry = get_team_registry()
        if parent_team_id:
            parent = registry.get(parent_team_id)
            if not parent:
                return ActionResult(
                    action_type=self.api_name,
                    success=False,
                    error=f"Parent team not found: {parent_team_id}",
                )

        # Create team
        team = Team(
            name=name,
            description=description,
            members=members,
            parent_team_id=parent_team_id,
            created_by=context.actor_id,
        )

        # Add permissions if specified
        if params.get("permissions"):
            for perm_data in params["permissions"]:
                perm = ObjectTypePermission(**perm_data)
                team.add_permission(perm)

        # Register team
        registry.register(team)

        # Also add team to agent identities
        perm_manager = get_permission_manager()
        for member_id in members:
            agent = perm_manager.get_agent(member_id)
            if agent:
                agent.add_team(team.id)

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Team",
            object_id=team.id,
            changes={
                "name": name,
                "members": members,
                "parent_team_id": parent_team_id,
            },
            timestamp=context.timestamp,
        )

        logger.info(f"Created team '{name}' with {len(members)} members by {context.actor_id}")

        return (team, [edit])


# =============================================================================
# ADD MEMBER ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class AddTeamMemberAction(ActionType[Team]):
    """
    Add a member to a team.

    This action is HAZARDOUS and requires a proposal.

    Parameters:
        team_id: ID of the team
        agent_id: ID of the agent to add
        membership_type: Type of membership (default: "member")
        expires_in_hours: Optional membership expiration

    Returns:
        ActionResult with updated Team
    """

    api_name: ClassVar[str] = "rbac.add_member"
    object_type: ClassVar[Type[Team]] = Team
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("team_id"),
        RequiredField("agent_id"),
        AllowedValues("membership_type", ["member", "admin", "owner", "guest"]),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[Team], List[EditOperation]]:
        """Add member to team."""
        team_id = params["team_id"]
        agent_id = params["agent_id"]
        membership_type_str = params.get("membership_type", "member")

        # Get team
        registry = get_team_registry()
        team = registry.get(team_id)
        if not team:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=f"Team not found: {team_id}",
            )

        # Calculate expiration if specified
        expires_at = None
        if params.get("expires_in_hours"):
            from datetime import timedelta
            from lib.oda.ontology.ontology_types import utc_now
            expires_at = utc_now() + timedelta(hours=params["expires_in_hours"])

        # Add member
        membership_type = TeamMembershipType(membership_type_str)
        membership = team.add_member(
            agent_id=agent_id,
            membership_type=membership_type,
            added_by=context.actor_id,
            expires_at=expires_at,
        )

        # Update agent identity
        perm_manager = get_permission_manager()
        agent = perm_manager.get_agent(agent_id)
        if agent:
            agent.add_team(team_id)

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Team",
            object_id=team.id,
            changes={
                "added_member": agent_id,
                "membership_type": membership_type_str,
            },
            timestamp=context.timestamp,
        )

        logger.info(f"Added {agent_id} to team '{team.name}' as {membership_type_str}")

        return (team, [edit])


# =============================================================================
# CHECK PERMISSION ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class CheckPermissionAction(ActionType[OntologyObject]):
    """
    Check permission for an agent/object/operation.

    This action is non-hazardous (read-only).

    Parameters:
        agent_id: ID of the agent to check
        object_type: Type of object
        operation: Operation to check (read, create, update, delete, link)
        instance_id: Optional specific instance ID

    Returns:
        ActionResult with permission check result
    """

    api_name: ClassVar[str] = "rbac.check"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("agent_id"),
        RequiredField("object_type"),
        RequiredField("operation"),
        ValidOperationValue("operation"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """Check permission."""
        agent_id = params["agent_id"]
        object_type_name = params["object_type"]
        operation = params["operation"]
        instance_id = params.get("instance_id")

        resolver = get_permission_resolver()
        result = resolver.resolve(
            agent_id=agent_id,
            object_type=object_type_name,
            operation=operation,
            instance_id=instance_id,
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=result.to_dict(),
            edits=[],
            message=f"Permission {'allowed' if result.allowed else 'denied'} for {agent_id}",
        )


# =============================================================================
# LIST PERMISSIONS ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class ListPermissionsAction(ActionType[OntologyObject]):
    """
    List permissions for an object type or role.

    This action is non-hazardous (read-only).

    Parameters:
        object_type: Optional ObjectType name to filter by
        role_id: Optional role ID to filter by

    Returns:
        ActionResult with list of ObjectTypePermissions
    """

    api_name: ClassVar[str] = "rbac.list_permissions"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = []

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """List permissions."""
        object_type_name = params.get("object_type")
        role_id = params.get("role_id")

        registry = get_object_permission_registry()

        if object_type_name:
            permissions = registry.get_for_object_type(object_type_name)
        elif role_id:
            permissions = registry.get_for_role(role_id)
        else:
            permissions = registry.list_all()

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "permissions": [p.to_dict() for p in permissions],
                "count": len(permissions),
            },
            edits=[],
            message=f"Found {len(permissions)} permissions",
        )


# =============================================================================
# GET TEAM ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class GetTeamAction(ActionType[Team]):
    """
    Get team details.

    This action is non-hazardous (read-only).

    Parameters:
        team_id: Optional team ID
        team_name: Optional team name (case-insensitive)
        include_ancestors: Include ancestor teams (default: False)
        include_descendants: Include descendant teams (default: False)

    Returns:
        ActionResult with Team details
    """

    api_name: ClassVar[str] = "rbac.get_team"
    object_type: ClassVar[Type[Team]] = Team
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = []

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[Team], List[EditOperation]]:
        """Get team details."""
        team_id = params.get("team_id")
        team_name = params.get("team_name")

        registry = get_team_registry()

        # Find team
        team = None
        if team_id:
            team = registry.get(team_id)
        elif team_name:
            team = registry.get_by_name(team_name)

        if not team:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error="Team not found",
                error_details={
                    "team_id": team_id,
                    "team_name": team_name,
                },
            )

        data = team.to_dict()

        # Include ancestors if requested
        if params.get("include_ancestors"):
            ancestors = registry.get_ancestors(team.id)
            data["ancestors"] = [a.to_dict() for a in ancestors]

        # Include descendants if requested
        if params.get("include_descendants"):
            descendants = registry.get_all_descendants(team.id)
            data["descendants"] = [d.to_dict() for d in descendants]

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=data,
            edits=[],
            message=f"Retrieved team '{team.name}'",
        )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Hazardous actions
    "GrantObjectPermissionAction",
    "RevokeObjectPermissionAction",
    "CreateTeamAction",
    "AddTeamMemberAction",
    # Non-hazardous actions
    "CheckPermissionAction",
    "ListPermissionsAction",
    "GetTeamAction",
    # Validators
    "ValidOperationValue",
    "ValidPrincipalType",
]
