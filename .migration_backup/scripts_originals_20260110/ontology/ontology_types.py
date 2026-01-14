"""
Orion ODA v3.0 - Core Ontology Types
Palantir AIP/Foundry Compliant Type Definitions

This module defines the foundational types for the Ontology-Driven Architecture:
- Cardinality: Relationship multiplicity constraints
- PropertyType: Supported property data types
- Link: Type-safe relationship definitions
- OntologyObject: Base class for all domain entities
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod  # Fixed: Added ABC import
from datetime import datetime, timezone
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from pydantic import BaseModel, Field, field_validator, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================

class Cardinality(str, Enum):
    """
    LinkType cardinality constraints.
    Aligned with Palantir Ontology Link Types.
    
    - ONE_TO_ONE: Single object on both sides (e.g., User ↔ Profile)
    - ONE_TO_MANY: Foreign key pattern (e.g., Department → Employees)
    - MANY_TO_MANY: Join table pattern (e.g., Task ↔ Tags)
    """
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"
    MANY_TO_MANY = "N:N"


class PropertyType(str, Enum):
    """
    Supported property data types.
    Aligned with Palantir Ontology Property Types.
    """
    STRING = "string"
    INTEGER = "integer"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    ARRAY = "array"
    STRUCT = "struct"
    GEOPOINT = "geopoint"
    GEOSHAPE = "geoshape"
    TIMESERIES = "timeseries"
    VECTOR = "vector"


class ObjectStatus(str, Enum):
    """
    Lifecycle status for OntologyObjects.
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# =============================================================================
# LINK TYPE
# =============================================================================

T = TypeVar("T", bound="OntologyObject")


class Link(Generic[T]):
    """
    Represents a LinkType (Relationship) between OntologyObjects.
    
    Attributes:
        target: The target ObjectType class
        link_type_id: Unique identifier for this link type (e.g., "task_assigned_to_agent")
        cardinality: Relationship multiplicity constraint
        reverse_link_id: Optional reverse link identifier for bidirectional navigation
        description: Human-readable description of the relationship
    
    Example:
        ```python
        class Task(OntologyObject):
            assigned_to: Link[Agent] = Link(
                target=Agent,
                link_type_id="task_assigned_to_agent",
                cardinality=Cardinality.MANY_TO_ONE,
                reverse_link_id="agent_assigned_tasks",
                description="The agent responsible for this task"
            )
        ```
    """
    
    def __init__(
        self,
        target: Type[T],
        link_type_id: str,
        cardinality: Cardinality = Cardinality.ONE_TO_MANY,
        reverse_link_id: Optional[str] = None,
        description: Optional[str] = None,
        backing_table_name: Optional[str] = None,  # NEW
        is_materialized: bool = True,  # NEW
    ):
        self._validate_link_type_id(link_type_id)
        self._validate_n_n_backing(cardinality, backing_table_name)  # NEW

        self.target = target
        self.link_type_id = link_type_id
        self.cardinality = cardinality
        self.reverse_link_id = reverse_link_id
        self.description = description
        self.backing_table_name = backing_table_name  # NEW
        self.is_materialized = is_materialized  # NEW

    @staticmethod
    def _validate_link_type_id(link_type_id: str) -> None:
        """Enforce snake_case naming convention for link type IDs."""
        if not link_type_id:
            raise ValueError("link_type_id cannot be empty")
        if not link_type_id.replace("_", "").isalnum():
            raise ValueError(
                f"link_type_id must be snake_case alphanumeric: {link_type_id}"
            )

    @staticmethod
    def _validate_n_n_backing(cardinality: Cardinality, backing_table: Optional[str]) -> None:
        """Palantir Pattern: MANY_TO_MANY requires backing_table_name."""
        if cardinality == Cardinality.MANY_TO_MANY and not backing_table:
            raise ValueError(
                "MANY_TO_MANY links require backing_table_name. "
                "Example: backing_table_name='task_dependencies'"
            )

    def __repr__(self) -> str:
        return (
            f"Link(target={self.target.__name__}, "
            f"cardinality={self.cardinality.value}, "
            f"link_type_id='{self.link_type_id}')"
        )


class Reference(Generic[T]):
    """
    Type-safe foreign key reference.
    Palantir Pattern: References should be typed, not raw strings.

    Usage:
        assigned_to: Reference[Agent] = Reference(Agent)
    """
    def __init__(self, target_type: Type[T]):
        self.target_type = target_type
        self._id: Optional[str] = None

    @property
    def id(self) -> Optional[str]:
        return self._id

    @id.setter
    def id(self, value: Optional[str]) -> None:
        self._id = value

    @property
    def target_type_name(self) -> str:
        return self.target_type.__name__

    def __repr__(self) -> str:
        return f"Reference[{self.target_type_name}](id={self._id})"


class ObjectSet(Generic[T], ABC):
    """
    Represents a lazy, filterable set of objects.
    Palantir Pattern: Use ObjectSet for chainable filtering logic.
    """
    @abstractmethod
    def where(self, **filters: Any) -> "ObjectSet[T]":
        ...

    @abstractmethod
    async def resolve(self) -> List[T]:
        ...


# =============================================================================
# BASE ONTOLOGY OBJECT
# =============================================================================

def generate_object_id() -> str:
    """
    Generate a unique object ID.
    Format: UUIDv4 string (compatible with distributed systems)
    
    Note: Palantir recommends String-based primary keys over Long
    to avoid JavaScript precision issues in Workshop/Slate.
    """
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class OntologyObject(BaseModel):
    """
    Base class for all Ontology Objects (Domain Entities).
    
    Provides:
    - Primary Key (id): String-based UUID
    - Audit Fields: created_at, updated_at, created_by, updated_by
    - Lifecycle Status: active, archived, deleted
    - Version: Optimistic locking support
    
    All domain entities (Task, Agent, Proposal, etc.) inherit from this class.
    
    Example:
        ```python
        class Task(OntologyObject):
            title: str
            priority: str = "medium"
            assigned_to_id: Optional[str] = None  # FK to Agent
        ```
    """
    
    # Primary Key
    id: str = Field(
        default_factory=generate_object_id,
        description="Primary Key (UUIDv4 string)",
        json_schema_extra={"immutable": True}
    )
    
    # Audit Fields
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        description="Last update timestamp (UTC)"
    )
    created_by: Optional[str] = Field(
        default=None,
        description="ID of the user/agent who created this object"
    )
    updated_by: Optional[str] = Field(
        default=None,
        description="ID of the user/agent who last updated this object"
    )
    
    # Lifecycle
    status: ObjectStatus = Field(
        default=ObjectStatus.ACTIVE,
        description="Object lifecycle status"
    )
    
    # Optimistic Locking
    version: int = Field(
        default=1,
        description="Version number for optimistic locking",
        ge=1
    )
    
    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={"x-palantir-indexing": ["id", "created_at", "updated_at"]}
    )
    
    def touch(self, updated_by: Optional[str] = None) -> None:
        """
        Update the modification timestamp and optionally the modifier.
        Call this before any update operation.
        """
        self.updated_at = utc_now()
        self.version += 1
        if updated_by:
            self.updated_by = updated_by
    
    def soft_delete(self, deleted_by: Optional[str] = None) -> None:
        """
        Soft delete the object (set status to DELETED).
        Preferred over hard deletion for audit compliance.
        """
        self.status = ObjectStatus.DELETED
        self.touch(updated_by=deleted_by)
    
    def archive(self, archived_by: Optional[str] = None) -> None:
        """Archive the object (set status to ARCHIVED)."""
        self.status = ObjectStatus.ARCHIVED
        self.touch(updated_by=archived_by)
    
    @property
    def is_active(self) -> bool:
        """Check if the object is in active status."""
        return self.status == ObjectStatus.ACTIVE


# =============================================================================
# TYPE ALIASES FOR CONVENIENCE
# =============================================================================

ObjectId = str
LinkTypeId = str
PropertyName = str

# For type hints in Link definitions
if TYPE_CHECKING:
    from lib.oda.ontology.objects.task_types import Agent, Task
    from lib.oda.ontology.objects.proposal import Proposal
OrionObject = OntologyObject
