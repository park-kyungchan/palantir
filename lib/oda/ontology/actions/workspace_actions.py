"""
Orion ODA v4.0 - Workspace Action Types
=======================================

ActionTypes for Workspace object management.
Provides CRUD operations with proper governance.

Phase 3.4.1 Implementation:
- workspace.create: Create new workspace
- workspace.update: Update workspace settings
- workspace.archive: Archive workspace
- workspace.delete: Delete workspace (hazardous)
- workspace.add_member: Add member to workspace
- workspace.remove_member: Remove member from workspace

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    AllowedValues,
    CustomValidator,
    EditOperation,
    EditType,
    MaxLength,
    RequiredField,
    register_action,
)
from lib.oda.ontology.objects.workspace import (
    Workspace,
    WorkspaceStatus,
    WorkspaceType,
)
from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# VALIDATORS
# =============================================================================


def validate_workspace_name(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate workspace name is not empty and within limits."""
    name = params.get("name", "")
    if not name or not isinstance(name, str):
        return False
    name = name.strip()
    return 1 <= len(name) <= 100


def validate_workspace_exists(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that workspace_id refers to an existing workspace."""
    # This would typically check the database
    # For now, just verify the ID is provided
    workspace_id = params.get("workspace_id", "")
    return bool(workspace_id)


def validate_member_not_exists(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that member is not already in workspace."""
    # Would check database for existing membership
    return True


def validate_member_exists(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that member is in workspace."""
    # Would check database for existing membership
    return True


# =============================================================================
# WORKSPACE CREATE ACTION
# =============================================================================


@register_action
class WorkspaceCreateAction(ActionType[Workspace]):
    """
    Create a new workspace.

    Non-hazardous action - creates a new workspace with specified settings.

    Parameters:
        name: Workspace display name (required)
        description: Optional description
        workspace_type: Type of workspace (personal, team, organization, project)
        owner_id: ID of the workspace owner
        settings: Optional workspace settings dict
        max_sessions: Maximum concurrent sessions (default: 100)
        max_members: Maximum workspace members (default: 50)

    Returns:
        Workspace: The created workspace object
    """
    api_name = "workspace.create"
    object_type = Workspace
    requires_proposal = False

    submission_criteria = [
        RequiredField("name"),
        RequiredField("owner_id"),
        CustomValidator(
            name="ValidWorkspaceName",
            validator_fn=validate_workspace_name,
            error_message="Workspace name must be 1-100 characters"
        ),
        AllowedValues(
            "workspace_type",
            [wt.value for wt in WorkspaceType]
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Workspace], List[EditOperation]]:
        """Create a new workspace."""
        workspace = Workspace(
            name=params["name"],
            owner_id=params["owner_id"],
            description=params.get("description"),
            workspace_type=WorkspaceType(params.get("workspace_type", "personal")),
            workspace_status=WorkspaceStatus.ACTIVE,
            settings=params.get("settings", {}),
            max_sessions=params.get("max_sessions", 100),
            max_members=params.get("max_members", 50),
            tags=params.get("tags", []),
            default_language=params.get("default_language", "en"),
            timezone=params.get("timezone", "UTC"),
            created_by=context.actor_id,
        )

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Workspace",
            object_id=workspace.id,
            changes={
                "name": workspace.name,
                "owner_id": workspace.owner_id,
                "workspace_type": workspace.workspace_type.value,
                "actor": context.actor_id,
            }
        )

        return workspace, [edit]


# =============================================================================
# WORKSPACE UPDATE ACTION
# =============================================================================


@register_action
class WorkspaceUpdateAction(ActionType[Workspace]):
    """
    Update workspace settings and metadata.

    Parameters:
        workspace_id: ID of workspace to update (required)
        name: New workspace name (optional)
        description: New description (optional)
        settings: Updated settings dict (optional)
        max_sessions: New max sessions limit (optional)
        max_members: New max members limit (optional)
        tags: Updated tags list (optional)
        icon: Workspace icon (optional)
        color: Theme color hex (optional)

    Returns:
        Workspace: The updated workspace object
    """
    api_name = "workspace.update"
    object_type = Workspace
    requires_proposal = False

    submission_criteria = [
        RequiredField("workspace_id"),
        CustomValidator(
            name="WorkspaceExists",
            validator_fn=validate_workspace_exists,
            error_message="Workspace not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Workspace], List[EditOperation]]:
        """Update workspace settings."""
        workspace_id = params["workspace_id"]

        # In a real implementation, we would:
        # 1. Load workspace from storage
        # 2. Apply updates
        # 3. Save and return

        # For now, create a mock updated workspace
        changes = {}
        updatable_fields = [
            "name", "description", "settings", "max_sessions",
            "max_members", "tags", "icon", "color", "default_language", "timezone"
        ]

        for field in updatable_fields:
            if field in params:
                changes[field] = params[field]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Workspace",
            object_id=workspace_id,
            changes={
                **changes,
                "actor": context.actor_id,
            }
        )

        # Return ActionResult instead of tuple for proper handling
        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Workspace {workspace_id} updated",
            edits=[edit],
            modified_ids=[workspace_id],
        )


# =============================================================================
# WORKSPACE ARCHIVE ACTION
# =============================================================================


@register_action
class WorkspaceArchiveAction(ActionType[Workspace]):
    """
    Archive a workspace.

    Archived workspaces are read-only and don't count against limits.

    Parameters:
        workspace_id: ID of workspace to archive (required)
        reason: Reason for archiving (optional)

    Returns:
        Workspace: The archived workspace
    """
    api_name = "workspace.archive"
    object_type = Workspace
    requires_proposal = False

    submission_criteria = [
        RequiredField("workspace_id"),
        CustomValidator(
            name="WorkspaceExists",
            validator_fn=validate_workspace_exists,
            error_message="Workspace not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Workspace], List[EditOperation]]:
        """Archive the workspace."""
        workspace_id = params["workspace_id"]
        reason = params.get("reason", "")

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Workspace",
            object_id=workspace_id,
            changes={
                "workspace_status": WorkspaceStatus.ARCHIVED.value,
                "archive_reason": reason,
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "archived_by": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Workspace {workspace_id} archived",
            edits=[edit],
            modified_ids=[workspace_id],
        )


# =============================================================================
# WORKSPACE DELETE ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class WorkspaceDeleteAction(ActionType[Workspace]):
    """
    Delete a workspace permanently.

    HAZARDOUS: Requires proposal approval.
    This action permanently deletes a workspace and all associated data.

    Parameters:
        workspace_id: ID of workspace to delete (required)
        reason: Reason for deletion (required)
        confirm: Must be True to confirm deletion (required)

    Returns:
        None (workspace is deleted)
    """
    api_name = "workspace.delete"
    object_type = Workspace
    requires_proposal = True

    submission_criteria = [
        RequiredField("workspace_id"),
        RequiredField("reason"),
        RequiredField("confirm"),
        CustomValidator(
            name="WorkspaceExists",
            validator_fn=validate_workspace_exists,
            error_message="Workspace not found"
        ),
        CustomValidator(
            name="ConfirmDeletion",
            validator_fn=lambda p, c: p.get("confirm") is True,
            error_message="Must set confirm=True to delete workspace"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Workspace], List[EditOperation]]:
        """Delete the workspace."""
        workspace_id = params["workspace_id"]
        reason = params["reason"]

        edit = EditOperation(
            edit_type=EditType.DELETE,
            object_type="Workspace",
            object_id=workspace_id,
            changes={
                "deleted_reason": reason,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "deleted_by": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Workspace {workspace_id} deleted",
            edits=[edit],
            deleted_ids=[workspace_id],
        )


# =============================================================================
# WORKSPACE MEMBER ACTIONS
# =============================================================================


@register_action
class WorkspaceAddMemberAction(ActionType[Workspace]):
    """
    Add a member to workspace.

    Parameters:
        workspace_id: ID of workspace (required)
        member_id: ID of member (agent) to add (required)
        role: Member role (default: member)

    Returns:
        Updated workspace
    """
    api_name = "workspace.add_member"
    object_type = Workspace
    requires_proposal = False

    submission_criteria = [
        RequiredField("workspace_id"),
        RequiredField("member_id"),
        CustomValidator(
            name="WorkspaceExists",
            validator_fn=validate_workspace_exists,
            error_message="Workspace not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Workspace], List[EditOperation]]:
        """Add member to workspace."""
        workspace_id = params["workspace_id"]
        member_id = params["member_id"]
        role = params.get("role", "member")

        edit = EditOperation(
            edit_type=EditType.LINK,
            object_type="Workspace",
            object_id=workspace_id,
            changes={
                "linked_object_type": "Agent",
                "linked_object_id": member_id,
                "link_type": "workspace_has_members",
                "role": role,
                "added_by": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Member {member_id} added to workspace {workspace_id}",
            edits=[edit],
            modified_ids=[workspace_id],
        )


@register_action
class WorkspaceRemoveMemberAction(ActionType[Workspace]):
    """
    Remove a member from workspace.

    Parameters:
        workspace_id: ID of workspace (required)
        member_id: ID of member to remove (required)
        reason: Reason for removal (optional)

    Returns:
        Updated workspace
    """
    api_name = "workspace.remove_member"
    object_type = Workspace
    requires_proposal = False

    submission_criteria = [
        RequiredField("workspace_id"),
        RequiredField("member_id"),
        CustomValidator(
            name="WorkspaceExists",
            validator_fn=validate_workspace_exists,
            error_message="Workspace not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Workspace], List[EditOperation]]:
        """Remove member from workspace."""
        workspace_id = params["workspace_id"]
        member_id = params["member_id"]
        reason = params.get("reason", "")

        edit = EditOperation(
            edit_type=EditType.UNLINK,
            object_type="Workspace",
            object_id=workspace_id,
            changes={
                "unlinked_object_type": "Agent",
                "unlinked_object_id": member_id,
                "link_type": "workspace_has_members",
                "removal_reason": reason,
                "removed_by": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Member {member_id} removed from workspace {workspace_id}",
            edits=[edit],
            modified_ids=[workspace_id],
        )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    "WorkspaceCreateAction",
    "WorkspaceUpdateAction",
    "WorkspaceArchiveAction",
    "WorkspaceDeleteAction",
    "WorkspaceAddMemberAction",
    "WorkspaceRemoveMemberAction",
]
