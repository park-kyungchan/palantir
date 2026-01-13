"""
Orion ODA v3.0 - AuditLog ObjectType

Immutable audit log record for all ODA operations.
Provides complete audit trail for governance and compliance.

Features:
- Immutable records (no updates after creation)
- Full operation context capture
- Evidence linking
- Before/after state snapshots

Environment Variables:
    ORION_AUDIT_ENABLED: Enable/disable audit logging (true|false)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import Field, field_validator

from scripts.ontology.ontology_types import OntologyObject
from scripts.ontology.registry import register_object_type


class AuditOperationType(str, Enum):
    """Type of operation being audited."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LINK = "LINK"
    UNLINK = "UNLINK"
    EXECUTE = "EXECUTE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    TRANSITION = "TRANSITION"


class AuditSeverity(str, Enum):
    """Severity level of the audit event."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@register_object_type
class AuditLog(OntologyObject):
    """
    Immutable audit log record for ODA operations.

    Captures complete context of any operation including:
    - Who performed the operation (actor_id)
    - What operation was performed (operation_type)
    - What object was affected (target_object_type, target_object_id)
    - What evidence supports this operation (evidence_id)
    - What was the state before/after (before_state, after_state)

    AuditLog records are IMMUTABLE - they cannot be updated or deleted
    after creation. This ensures complete audit trail integrity.
    """

    # Operation identification
    operation_type: AuditOperationType = Field(
        description="Type of operation performed"
    )
    operation_name: str = Field(
        default="",
        max_length=255,
        description="Specific operation name (e.g., 'proposal.create')"
    )

    # Target object
    target_object_type: str = Field(
        max_length=100,
        description="Type of the target object (e.g., 'Task', 'Proposal')"
    )
    target_object_id: str = Field(
        max_length=100,
        description="ID of the target object"
    )

    # Actor
    actor_id: str = Field(
        default="system",
        max_length=100,
        description="ID of the actor who performed the operation"
    )
    actor_type: str = Field(
        default="agent",
        max_length=50,
        description="Type of actor (agent, user, system)"
    )

    # Evidence
    evidence_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="ID of associated evidence record"
    )
    protocol_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="ID of the protocol execution that triggered this"
    )

    # State snapshots
    before_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Object state before the operation"
    )
    after_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Object state after the operation"
    )

    # Result
    success: bool = Field(
        default=True,
        description="Whether the operation succeeded"
    )
    error_message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message if operation failed"
    )

    # Metadata
    severity: AuditSeverity = Field(
        default=AuditSeverity.INFO,
        description="Severity level of the audit event"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    # Timestamps (inherited from OntologyObject, but emphasized here)
    # created_at: datetime - when the audit record was created
    # Note: AuditLog has no updated_at as it's immutable

    @field_validator("operation_name")
    @classmethod
    def validate_operation_name(cls, v: str) -> str:
        """Validate operation name is snake_case."""
        if v and not v.replace(".", "").replace("_", "").isalnum():
            raise ValueError(f"operation_name must be alphanumeric with dots/underscores: {v}")
        return v.lower() if v else v

    def __init__(self, **data: Any) -> None:
        """Initialize AuditLog with immutability enforcement."""
        # Set creation timestamp if not provided
        if "created_at" not in data:
            data["created_at"] = datetime.now(timezone.utc)

        super().__init__(**data)

    @classmethod
    def create(
        cls,
        operation_type: AuditOperationType,
        target_object_type: str,
        target_object_id: str,
        actor_id: str = "system",
        operation_name: str = "",
        evidence_id: Optional[str] = None,
        protocol_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AuditLog":
        """
        Factory method to create an AuditLog record.

        This is the preferred way to create AuditLog records.
        """
        return cls(
            operation_type=operation_type,
            operation_name=operation_name,
            target_object_type=target_object_type,
            target_object_id=target_object_id,
            actor_id=actor_id,
            evidence_id=evidence_id,
            protocol_id=protocol_id,
            before_state=before_state,
            after_state=after_state,
            success=success,
            error_message=error_message,
            severity=severity,
            tags=tags or [],
            metadata=metadata or {},
        )

    @classmethod
    def for_create(
        cls,
        target_type: str,
        target_id: str,
        actor_id: str,
        after_state: Dict[str, Any],
        **kwargs: Any,
    ) -> "AuditLog":
        """Create an audit log for a CREATE operation."""
        return cls.create(
            operation_type=AuditOperationType.CREATE,
            target_object_type=target_type,
            target_object_id=target_id,
            actor_id=actor_id,
            after_state=after_state,
            **kwargs,
        )

    @classmethod
    def for_update(
        cls,
        target_type: str,
        target_id: str,
        actor_id: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        **kwargs: Any,
    ) -> "AuditLog":
        """Create an audit log for an UPDATE operation."""
        return cls.create(
            operation_type=AuditOperationType.UPDATE,
            target_object_type=target_type,
            target_object_id=target_id,
            actor_id=actor_id,
            before_state=before_state,
            after_state=after_state,
            **kwargs,
        )

    @classmethod
    def for_delete(
        cls,
        target_type: str,
        target_id: str,
        actor_id: str,
        before_state: Dict[str, Any],
        **kwargs: Any,
    ) -> "AuditLog":
        """Create an audit log for a DELETE operation."""
        return cls.create(
            operation_type=AuditOperationType.DELETE,
            target_object_type=target_type,
            target_object_id=target_id,
            actor_id=actor_id,
            before_state=before_state,
            **kwargs,
        )

    @classmethod
    def for_error(
        cls,
        operation_type: AuditOperationType,
        target_type: str,
        target_id: str,
        actor_id: str,
        error_message: str,
        **kwargs: Any,
    ) -> "AuditLog":
        """Create an audit log for a failed operation."""
        return cls.create(
            operation_type=operation_type,
            target_object_type=target_type,
            target_object_id=target_id,
            actor_id=actor_id,
            success=False,
            error_message=error_message,
            severity=AuditSeverity.ERROR,
            **kwargs,
        )


def is_audit_enabled() -> bool:
    """Check if audit logging is enabled."""
    return os.environ.get("ORION_AUDIT_ENABLED", "true").lower() in ("true", "1", "yes")
