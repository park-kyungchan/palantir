"""
Orion ODA v4.0 - ObjectType-Level Permissions (Phase 3.1.1)
============================================================

Provides fine-grained permissions at the ObjectType level,
enabling Palantir-style ACL patterns for ontology objects.

This module defines:
- ObjectTypePermission: Permissions for an ObjectType (CRUD + Link)
- FieldPermission: Per-field access restrictions
- PermissionGrant: Individual permission grants for ACLs

Palantir Pattern:
- ObjectTypes can have different permissions per role
- Field-level restrictions enable data masking
- Supports both positive (grant) and negative (deny) permissions

Example:
    ```python
    # Create permission for Developer role on Task ObjectType
    permission = ObjectTypePermission(
        object_type="Task",
        role_id="developer",
        can_read=True,
        can_create=True,
        can_update=True,
        can_delete=False,  # Developers cannot delete tasks
        field_restrictions={
            "internal_notes": FieldPermission(readable=False),
        }
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

from lib.oda.ontology.ontology_types import utc_now

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class PermissionType(str, Enum):
    """Types of permission grants."""
    GRANT = "grant"      # Explicitly allows access
    DENY = "deny"        # Explicitly denies access
    INHERIT = "inherit"  # Inherits from parent (default)


class FieldAccessLevel(str, Enum):
    """Access levels for individual fields."""
    FULL = "full"        # Full read/write access
    READ_ONLY = "read_only"  # Can read but not write
    MASKED = "masked"    # Can see masked value (e.g., "****")
    HIDDEN = "hidden"    # Field is completely hidden


# =============================================================================
# FIELD PERMISSION
# =============================================================================


class FieldPermission(BaseModel):
    """
    Permission configuration for a specific field within an ObjectType.

    Enables fine-grained data masking and field-level access control.

    Attributes:
        field_name: Name of the field this permission applies to
        readable: Whether the field can be read
        writable: Whether the field can be written
        access_level: Level of access (full, read_only, masked, hidden)
        mask_pattern: Pattern for masking (e.g., "****" or "xxx-xxx-{last4}")

    Example:
        ```python
        # Hide SSN field from non-admins
        FieldPermission(
            field_name="ssn",
            readable=False,
            access_level=FieldAccessLevel.HIDDEN
        )

        # Mask credit card - show only last 4 digits
        FieldPermission(
            field_name="credit_card",
            readable=True,
            access_level=FieldAccessLevel.MASKED,
            mask_pattern="****-****-****-{last4}"
        )
        ```
    """

    field_name: str = Field(
        default="",
        description="Field name (can be set from dict key)",
    )
    readable: bool = Field(
        default=True,
        description="Whether the field can be read",
    )
    writable: bool = Field(
        default=True,
        description="Whether the field can be written",
    )
    access_level: FieldAccessLevel = Field(
        default=FieldAccessLevel.FULL,
        description="Level of access to the field",
    )
    mask_pattern: Optional[str] = Field(
        default=None,
        description="Pattern for masking (e.g., '****' or '{first3}...{last3}')",
    )

    @model_validator(mode="after")
    def validate_access_consistency(self) -> "FieldPermission":
        """Ensure access level is consistent with readable/writable."""
        if self.access_level == FieldAccessLevel.HIDDEN:
            if self.readable:
                logger.warning(
                    f"Field {self.field_name}: HIDDEN access level overrides readable=True"
                )
        if self.access_level == FieldAccessLevel.READ_ONLY and self.writable:
            logger.warning(
                f"Field {self.field_name}: READ_ONLY access level overrides writable=True"
            )
        return self

    def apply_mask(self, value: Any) -> Any:
        """
        Apply masking pattern to a value.

        Args:
            value: The original value to mask

        Returns:
            Masked value based on mask_pattern or access_level
        """
        if self.access_level == FieldAccessLevel.HIDDEN:
            return None

        if self.access_level == FieldAccessLevel.MASKED:
            if not self.mask_pattern:
                return "****"

            str_value = str(value) if value else ""

            # Simple pattern replacement
            result = self.mask_pattern
            if "{last4}" in result and len(str_value) >= 4:
                result = result.replace("{last4}", str_value[-4:])
            if "{first3}" in result and len(str_value) >= 3:
                result = result.replace("{first3}", str_value[:3])
            if "{last3}" in result and len(str_value) >= 3:
                result = result.replace("{last3}", str_value[-3:])

            return result

        return value


# =============================================================================
# OBJECT TYPE PERMISSION
# =============================================================================


class ObjectTypePermission(BaseModel):
    """
    Permission definition for a specific ObjectType and role combination.

    Palantir-style ACL pattern for controlling access to ObjectTypes.

    Attributes:
        id: Unique identifier for this permission
        object_type: Name of the ObjectType (e.g., "Task", "Project")
        role_id: ID of the role this permission applies to
        can_read: Whether objects can be read/queried
        can_create: Whether new objects can be created
        can_update: Whether existing objects can be modified
        can_delete: Whether objects can be deleted
        can_link: Whether objects can be linked to other objects
        field_restrictions: Per-field permission overrides
        conditions: Additional conditions for permission (e.g., "owner_id == actor_id")
        expires_at: Optional expiration time for temporary permissions

    Example:
        ```python
        permission = ObjectTypePermission(
            object_type="Task",
            role_id="developer",
            can_read=True,
            can_create=True,
            can_update=True,
            can_delete=False,
            field_restrictions={
                "internal_notes": FieldPermission(readable=False),
                "budget": FieldPermission(access_level=FieldAccessLevel.MASKED),
            }
        )
        ```
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique permission ID",
    )
    object_type: str = Field(
        ...,
        description="Name of the ObjectType this permission applies to",
        min_length=1,
    )
    role_id: str = Field(
        ...,
        description="ID of the role this permission applies to",
        min_length=1,
    )

    # CRUD permissions
    can_read: bool = Field(
        default=True,
        description="Whether objects can be read/queried",
    )
    can_create: bool = Field(
        default=False,
        description="Whether new objects can be created",
    )
    can_update: bool = Field(
        default=False,
        description="Whether existing objects can be modified",
    )
    can_delete: bool = Field(
        default=False,
        description="Whether objects can be deleted",
    )
    can_link: bool = Field(
        default=False,
        description="Whether objects can be linked to other objects",
    )

    # Field-level restrictions
    field_restrictions: Dict[str, FieldPermission] = Field(
        default_factory=dict,
        description="Per-field permission overrides",
    )

    # Conditional permissions
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional conditions (e.g., owner-based access)",
    )

    # Temporal
    created_at: datetime = Field(
        default_factory=utc_now,
        description="When this permission was created",
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When this permission expires (None = never)",
    )

    @field_validator("object_type")
    @classmethod
    def validate_object_type(cls, v: str) -> str:
        """Ensure object_type follows naming convention (PascalCase)."""
        # Allow any non-empty string but log warning for non-PascalCase
        if v and not v[0].isupper():
            logger.warning(
                f"ObjectType '{v}' does not follow PascalCase convention"
            )
        return v

    def is_expired(self) -> bool:
        """Check if this permission has expired."""
        if self.expires_at is None:
            return False
        return utc_now() > self.expires_at

    def can_access_field(self, field_name: str, operation: str = "read") -> bool:
        """
        Check if a specific field can be accessed.

        Args:
            field_name: Name of the field to check
            operation: "read" or "write"

        Returns:
            True if access is allowed
        """
        if field_name not in self.field_restrictions:
            # No restriction - use object-level permission
            if operation == "read":
                return self.can_read
            else:
                return self.can_update

        restriction = self.field_restrictions[field_name]

        if restriction.access_level == FieldAccessLevel.HIDDEN:
            return False

        if operation == "read":
            return restriction.readable
        else:
            return restriction.writable and restriction.access_level != FieldAccessLevel.READ_ONLY

    def get_field_access_level(self, field_name: str) -> FieldAccessLevel:
        """Get the access level for a specific field."""
        if field_name not in self.field_restrictions:
            return FieldAccessLevel.FULL if self.can_read else FieldAccessLevel.HIDDEN
        return self.field_restrictions[field_name].access_level

    def mask_object_fields(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply field masking to an object based on restrictions.

        Args:
            obj: Object dictionary to mask

        Returns:
            New dictionary with masked/hidden fields
        """
        result = {}

        for field_name, value in obj.items():
            if field_name in self.field_restrictions:
                restriction = self.field_restrictions[field_name]

                if restriction.access_level == FieldAccessLevel.HIDDEN:
                    continue  # Skip hidden fields
                elif restriction.access_level == FieldAccessLevel.MASKED:
                    result[field_name] = restriction.apply_mask(value)
                elif not restriction.readable:
                    continue  # Skip unreadable fields
                else:
                    result[field_name] = value
            else:
                result[field_name] = value

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "object_type": self.object_type,
            "role_id": self.role_id,
            "can_read": self.can_read,
            "can_create": self.can_create,
            "can_update": self.can_update,
            "can_delete": self.can_delete,
            "can_link": self.can_link,
            "field_restrictions": {
                k: v.model_dump() for k, v in self.field_restrictions.items()
            },
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


# =============================================================================
# PERMISSION GRANT (FOR INSTANCE-LEVEL ACLS)
# =============================================================================


class PermissionGrant(BaseModel):
    """
    Individual permission grant for instance-level ACLs.

    Used by InstancePermission to define per-object permission overrides.

    Attributes:
        principal_type: Type of principal ("agent", "team", "role")
        principal_id: ID of the agent, team, or role
        permission_type: GRANT, DENY, or INHERIT
        operations: Set of allowed operations ("read", "update", "delete", "link")
        granted_by: ID of the actor who granted this permission
        granted_at: When the permission was granted
        expires_at: Optional expiration time

    Example:
        ```python
        grant = PermissionGrant(
            principal_type="agent",
            principal_id="agent-123",
            permission_type=PermissionType.GRANT,
            operations={"read", "update"},
            granted_by="admin-001",
        )
        ```
    """

    principal_type: str = Field(
        ...,
        description="Type of principal: 'agent', 'team', or 'role'",
    )
    principal_id: str = Field(
        ...,
        description="ID of the agent, team, or role",
    )
    permission_type: PermissionType = Field(
        default=PermissionType.GRANT,
        description="Whether this grants, denies, or inherits",
    )
    operations: Set[str] = Field(
        default_factory=set,
        description="Set of operations: 'read', 'create', 'update', 'delete', 'link'",
    )
    granted_by: str = Field(
        default="system",
        description="ID of actor who granted this permission",
    )
    granted_at: datetime = Field(
        default_factory=utc_now,
        description="When the permission was granted",
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When this grant expires",
    )

    @field_validator("principal_type")
    @classmethod
    def validate_principal_type(cls, v: str) -> str:
        """Validate principal type."""
        allowed = {"agent", "team", "role"}
        if v not in allowed:
            raise ValueError(f"principal_type must be one of {allowed}, got '{v}'")
        return v

    @field_validator("operations")
    @classmethod
    def validate_operations(cls, v: Set[str]) -> Set[str]:
        """Validate operation names."""
        allowed = {"read", "create", "update", "delete", "link"}
        invalid = v - allowed
        if invalid:
            raise ValueError(f"Invalid operations: {invalid}. Allowed: {allowed}")
        return v

    def is_expired(self) -> bool:
        """Check if this grant has expired."""
        if self.expires_at is None:
            return False
        return utc_now() > self.expires_at

    def allows_operation(self, operation: str) -> Optional[bool]:
        """
        Check if this grant allows an operation.

        Returns:
            True if explicitly granted
            False if explicitly denied
            None if inherits (no explicit rule)
        """
        if self.is_expired():
            return None

        if self.permission_type == PermissionType.INHERIT:
            return None

        if operation in self.operations:
            return self.permission_type == PermissionType.GRANT

        return None


# =============================================================================
# OBJECT TYPE PERMISSION REGISTRY
# =============================================================================


class ObjectTypePermissionRegistry:
    """
    Registry for ObjectType-level permissions.

    Provides lookup by object_type and role_id combination.
    """

    def __init__(self):
        # key: (object_type, role_id) -> ObjectTypePermission
        self._permissions: Dict[tuple[str, str], ObjectTypePermission] = {}

    def register(self, permission: ObjectTypePermission) -> None:
        """Register an ObjectType permission."""
        key = (permission.object_type, permission.role_id)
        self._permissions[key] = permission
        logger.info(
            f"Registered permission for {permission.object_type}:{permission.role_id}"
        )

    def get(
        self,
        object_type: str,
        role_id: str,
    ) -> Optional[ObjectTypePermission]:
        """Get permission for object_type and role_id."""
        return self._permissions.get((object_type, role_id))

    def get_for_object_type(self, object_type: str) -> List[ObjectTypePermission]:
        """Get all permissions for an object type."""
        return [
            perm for (ot, _), perm in self._permissions.items()
            if ot == object_type
        ]

    def get_for_role(self, role_id: str) -> List[ObjectTypePermission]:
        """Get all permissions for a role."""
        return [
            perm for (_, rid), perm in self._permissions.items()
            if rid == role_id
        ]

    def remove(self, object_type: str, role_id: str) -> bool:
        """Remove a permission."""
        key = (object_type, role_id)
        if key in self._permissions:
            del self._permissions[key]
            return True
        return False

    def list_all(self) -> List[ObjectTypePermission]:
        """List all registered permissions."""
        return list(self._permissions.values())

    def clear(self) -> None:
        """Clear all permissions."""
        self._permissions.clear()


# Global registry instance
_object_permission_registry: Optional[ObjectTypePermissionRegistry] = None


def get_object_permission_registry() -> ObjectTypePermissionRegistry:
    """Get or create the global ObjectTypePermissionRegistry."""
    global _object_permission_registry
    if _object_permission_registry is None:
        _object_permission_registry = ObjectTypePermissionRegistry()
    return _object_permission_registry


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "PermissionType",
    "FieldAccessLevel",
    # Models
    "FieldPermission",
    "ObjectTypePermission",
    "PermissionGrant",
    # Registry
    "ObjectTypePermissionRegistry",
    "get_object_permission_registry",
]
