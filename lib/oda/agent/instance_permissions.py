"""
Orion ODA v4.0 - Instance-Level Permissions (Phase 3.2.2)
==========================================================

Provides per-object ACL (Access Control List) for fine-grained permissions.

This module defines:
- InstancePermission: Per-object permission overrides
- InstanceACL: Collection of permission grants for an object

Palantir Pattern:
- Individual objects can have their own permission overrides
- Instance permissions take precedence over ObjectType permissions
- Enables owner-based access control patterns

Example:
    ```python
    # Create per-object permission
    instance_perm = InstancePermission(
        instance_id="task-123",
        object_type="Task",
        grants=[
            PermissionGrant(
                principal_type="agent",
                principal_id="agent-456",
                permission_type=PermissionType.GRANT,
                operations={"read", "update"},
            ),
            PermissionGrant(
                principal_type="team",
                principal_id="team-789",
                permission_type=PermissionType.GRANT,
                operations={"read"},
            ),
        ],
        owner_id="agent-001",
    )
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from lib.oda.ontology.ontology_types import utc_now
from lib.oda.agent.object_permissions import (
    PermissionGrant,
    PermissionType,
    FieldAccessLevel,
    FieldPermission,
)

logger = logging.getLogger(__name__)


# =============================================================================
# INSTANCE PERMISSION
# =============================================================================


class InstancePermission(BaseModel):
    """
    Per-object permission configuration (Instance-level ACL).

    Enables fine-grained access control for individual objects,
    overriding ObjectType-level permissions when present.

    Attributes:
        id: Unique identifier for this instance permission
        instance_id: ID of the object this permission applies to
        object_type: Type name of the object
        grants: List of permission grants for this object
        owner_id: ID of the object owner (full access)
        field_restrictions: Per-field permission overrides for this instance
        inherit_from_object_type: Whether to inherit ObjectType permissions
        created_at: When this permission was created
        created_by: ID of actor who created this permission

    Resolution Order (highest to lowest priority):
        1. Explicit DENY grants for the principal
        2. Explicit GRANT grants for the principal
        3. Owner permissions (if principal is owner)
        4. ObjectType permissions (if inherit_from_object_type is True)
        5. Default deny

    Example:
        ```python
        instance_perm = InstancePermission(
            instance_id="doc-123",
            object_type="Document",
            grants=[
                PermissionGrant(
                    principal_type="agent",
                    principal_id="agent-456",
                    operations={"read"},
                ),
            ],
            owner_id="agent-001",  # Owner has full access
        )
        ```
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique instance permission ID",
    )
    instance_id: str = Field(
        ...,
        description="ID of the object this permission applies to",
        min_length=1,
    )
    object_type: str = Field(
        ...,
        description="Type name of the object",
        min_length=1,
    )

    # Permission grants
    grants: List[PermissionGrant] = Field(
        default_factory=list,
        description="List of permission grants for this object",
    )

    # Owner
    owner_id: Optional[str] = Field(
        default=None,
        description="ID of the object owner (has full access)",
    )

    # Field-level overrides
    field_restrictions: Dict[str, FieldPermission] = Field(
        default_factory=dict,
        description="Per-field permission overrides for this instance",
    )

    # Inheritance
    inherit_from_object_type: bool = Field(
        default=True,
        description="Whether to inherit ObjectType permissions",
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=utc_now,
        description="When this permission was created",
    )
    created_by: str = Field(
        default="system",
        description="ID of actor who created this permission",
    )

    def is_owner(self, principal_id: str) -> bool:
        """Check if principal is the owner."""
        return self.owner_id == principal_id

    def get_grants_for_principal(
        self,
        principal_type: str,
        principal_id: str,
    ) -> List[PermissionGrant]:
        """
        Get all grants for a specific principal.

        Args:
            principal_type: Type of principal ("agent", "team", "role")
            principal_id: ID of the principal

        Returns:
            List of matching PermissionGrant objects
        """
        return [
            g for g in self.grants
            if g.principal_type == principal_type
            and g.principal_id == principal_id
            and not g.is_expired()
        ]

    def check_operation(
        self,
        principal_type: str,
        principal_id: str,
        operation: str,
    ) -> Optional[bool]:
        """
        Check if a principal can perform an operation.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            operation: Operation to check ("read", "update", "delete", "link")

        Returns:
            True if explicitly granted
            False if explicitly denied
            None if no explicit rule (fall through to ObjectType)
        """
        # Check owner first
        if principal_type == "agent" and self.is_owner(principal_id):
            return True  # Owner has full access

        grants = self.get_grants_for_principal(principal_type, principal_id)

        # Check for explicit DENY first (DENY wins over GRANT)
        for grant in grants:
            if grant.permission_type == PermissionType.DENY:
                if operation in grant.operations:
                    return False

        # Check for explicit GRANT
        for grant in grants:
            if grant.permission_type == PermissionType.GRANT:
                if operation in grant.operations:
                    return True

        # No explicit rule - return None to fall through
        return None

    def add_grant(self, grant: PermissionGrant) -> None:
        """Add a permission grant."""
        self.grants.append(grant)
        logger.debug(
            f"Added {grant.permission_type.value} grant for "
            f"{grant.principal_type}:{grant.principal_id} on {self.instance_id}"
        )

    def remove_grant(
        self,
        principal_type: str,
        principal_id: str,
        operations: Optional[Set[str]] = None,
    ) -> int:
        """
        Remove permission grants.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            operations: Specific operations to remove (None = all)

        Returns:
            Number of grants removed
        """
        original_count = len(self.grants)

        if operations is None:
            # Remove all grants for this principal
            self.grants = [
                g for g in self.grants
                if not (g.principal_type == principal_type and g.principal_id == principal_id)
            ]
        else:
            # Remove specific operations
            for grant in self.grants:
                if grant.principal_type == principal_type and grant.principal_id == principal_id:
                    grant.operations -= operations

            # Remove empty grants
            self.grants = [g for g in self.grants if g.operations]

        removed = original_count - len(self.grants)
        if removed:
            logger.debug(
                f"Removed {removed} grants for "
                f"{principal_type}:{principal_id} on {self.instance_id}"
            )
        return removed

    def get_field_access_level(self, field_name: str) -> FieldAccessLevel:
        """Get access level for a specific field."""
        if field_name in self.field_restrictions:
            return self.field_restrictions[field_name].access_level
        return FieldAccessLevel.FULL

    def set_owner(self, owner_id: str, changed_by: str = "system") -> None:
        """Set the owner of this object."""
        old_owner = self.owner_id
        self.owner_id = owner_id
        logger.info(
            f"Changed owner of {self.object_type}:{self.instance_id} "
            f"from {old_owner} to {owner_id} by {changed_by}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "object_type": self.object_type,
            "grants": [g.model_dump() for g in self.grants],
            "owner_id": self.owner_id,
            "field_restrictions": {
                k: v.model_dump() for k, v in self.field_restrictions.items()
            },
            "inherit_from_object_type": self.inherit_from_object_type,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }


# =============================================================================
# INSTANCE PERMISSION REGISTRY
# =============================================================================


class InstancePermissionRegistry:
    """
    Registry for instance-level permissions.

    Provides lookup by instance_id.
    """

    def __init__(self):
        # key: instance_id -> InstancePermission
        self._permissions: Dict[str, InstancePermission] = {}

    def register(self, permission: InstancePermission) -> None:
        """Register an instance permission."""
        self._permissions[permission.instance_id] = permission
        logger.debug(
            f"Registered instance permission for {permission.object_type}:{permission.instance_id}"
        )

    def get(self, instance_id: str) -> Optional[InstancePermission]:
        """Get permission for an instance."""
        return self._permissions.get(instance_id)

    def get_or_create(
        self,
        instance_id: str,
        object_type: str,
        owner_id: Optional[str] = None,
    ) -> InstancePermission:
        """
        Get existing permission or create a new one.

        Args:
            instance_id: ID of the instance
            object_type: Type of the object
            owner_id: Optional owner ID for new permissions

        Returns:
            Existing or newly created InstancePermission
        """
        existing = self.get(instance_id)
        if existing:
            return existing

        permission = InstancePermission(
            instance_id=instance_id,
            object_type=object_type,
            owner_id=owner_id,
        )
        self.register(permission)
        return permission

    def remove(self, instance_id: str) -> bool:
        """Remove permission for an instance."""
        if instance_id in self._permissions:
            del self._permissions[instance_id]
            return True
        return False

    def get_by_owner(self, owner_id: str) -> List[InstancePermission]:
        """Get all permissions where the principal is the owner."""
        return [
            perm for perm in self._permissions.values()
            if perm.owner_id == owner_id
        ]

    def get_by_object_type(self, object_type: str) -> List[InstancePermission]:
        """Get all permissions for a specific ObjectType."""
        return [
            perm for perm in self._permissions.values()
            if perm.object_type == object_type
        ]

    def list_all(self) -> List[InstancePermission]:
        """List all registered instance permissions."""
        return list(self._permissions.values())

    def clear(self) -> None:
        """Clear all permissions."""
        self._permissions.clear()


# Global registry instance
_instance_permission_registry: Optional[InstancePermissionRegistry] = None


def get_instance_permission_registry() -> InstancePermissionRegistry:
    """Get or create the global InstancePermissionRegistry."""
    global _instance_permission_registry
    if _instance_permission_registry is None:
        _instance_permission_registry = InstancePermissionRegistry()
    return _instance_permission_registry


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Models
    "InstancePermission",
    # Registry
    "InstancePermissionRegistry",
    "get_instance_permission_registry",
]
