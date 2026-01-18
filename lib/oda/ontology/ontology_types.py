"""
Orion ODA v3.0 - Core Ontology Runtime Types

This module defines the foundational RUNTIME types for the Ontology-Driven Architecture:
- Cardinality: Relationship multiplicity constraints (re-exported from bridge)
- PropertyType: Supported property data types (re-exported from bridge as DataType)
- Link: Type-safe relationship definitions (ODA-specific runtime)
- OntologyObject: Base class for all domain entities (ODA-specific runtime)

NOTE: Schema definition types (ObjectType, LinkType, ActionType) are in the bridge module.
      This module provides runtime instance types for ODA operations.

Migration Note (v4.0):
    Enums are now re-exported from lib.oda.ontology.bridge for single source of truth.
    Use bridge imports directly for new code:
        from lib.oda.ontology.bridge import Cardinality, DataType, ObjectStatus
"""

from __future__ import annotations

import uuid
import warnings
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field, ConfigDict

# =============================================================================
# RE-EXPORT ENUMS FROM BRIDGE (Single Source of Truth)
# =============================================================================
# Import enums from bridge module - these are the canonical definitions
# from ontology_definition package

try:
    from lib.oda.ontology.bridge import (
        Cardinality as _BridgeCardinality,
        DataType as _BridgeDataType,
        ObjectStatus as _BridgeObjectStatus,
    )
    _BRIDGE_AVAILABLE = True
except ImportError:
    _BRIDGE_AVAILABLE = False
    _BridgeCardinality = None  # type: ignore
    _BridgeDataType = None  # type: ignore
    _BridgeObjectStatus = None  # type: ignore


# =============================================================================
# ENUMS - Runtime-compatible definitions
# =============================================================================
# These maintain backward compatibility with existing ODA code while
# the canonical definitions are in the bridge module.

if _BRIDGE_AVAILABLE:
    # Use bridge enums as the canonical source
    # Create runtime aliases with short notation for Cardinality

    class Cardinality(str, Enum):
        """
        LinkType cardinality constraints (Runtime notation).

        Uses short notation (1:1, 1:N, etc.) for backward compatibility.
        For schema definitions, use bridge.Cardinality (ONE_TO_ONE, etc.).
        """
        ONE_TO_ONE = "1:1"
        ONE_TO_MANY = "1:N"
        MANY_TO_ONE = "N:1"
        MANY_TO_MANY = "N:N"

        def to_bridge(self) -> "_BridgeCardinality":
            """Convert to bridge Cardinality enum."""
            mapping = {
                "1:1": _BridgeCardinality.ONE_TO_ONE,
                "1:N": _BridgeCardinality.ONE_TO_MANY,
                "N:1": _BridgeCardinality.MANY_TO_ONE,
                "N:N": _BridgeCardinality.MANY_TO_MANY,
            }
            return mapping[self.value]

        @classmethod
        def from_bridge(cls, bridge_card: "_BridgeCardinality") -> "Cardinality":
            """Create from bridge Cardinality enum."""
            mapping = {
                "ONE_TO_ONE": cls.ONE_TO_ONE,
                "ONE_TO_MANY": cls.ONE_TO_MANY,
                "MANY_TO_ONE": cls.MANY_TO_ONE,
                "MANY_TO_MANY": cls.MANY_TO_MANY,
            }
            return mapping[bridge_card.name]

    # PropertyType maps to DataType from bridge
    class PropertyType(str, Enum):
        """
        Supported property data types (Runtime notation).

        Uses lowercase for backward compatibility.
        For schema definitions, use bridge.DataType (uppercase).
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

        def to_bridge(self) -> "_BridgeDataType":
            """Convert to bridge DataType enum."""
            return _BridgeDataType(self.value.upper())

        @classmethod
        def from_bridge(cls, bridge_dt: "_BridgeDataType") -> "PropertyType":
            """Create from bridge DataType enum."""
            return cls(bridge_dt.value.lower())

    # ObjectStatus - simplified runtime version
    class ObjectStatus(str, Enum):
        """
        Lifecycle status for OntologyObjects (Runtime notation).

        Simplified version with core statuses.
        For full lifecycle, use bridge.ObjectStatus.
        """
        ACTIVE = "active"
        ARCHIVED = "archived"
        DELETED = "deleted"

        def to_bridge(self) -> "_BridgeObjectStatus":
            """Convert to bridge ObjectStatus enum."""
            mapping = {
                "active": _BridgeObjectStatus.ACTIVE,
                "archived": _BridgeObjectStatus.ARCHIVED,
                "deleted": _BridgeObjectStatus.DELETED,
            }
            return mapping[self.value]

        @classmethod
        def from_bridge(cls, bridge_status: "_BridgeObjectStatus") -> "ObjectStatus":
            """Create from bridge ObjectStatus enum (maps advanced statuses)."""
            # Map full lifecycle to simplified runtime statuses
            if bridge_status in (_BridgeObjectStatus.ACTIVE, _BridgeObjectStatus.STABLE):
                return cls.ACTIVE
            elif bridge_status in (_BridgeObjectStatus.ARCHIVED,):
                return cls.ARCHIVED
            elif bridge_status in (_BridgeObjectStatus.DELETED,):
                return cls.DELETED
            else:
                # DRAFT, EXPERIMENTAL, ALPHA, BETA, DEPRECATED, SUNSET -> ACTIVE for runtime
                return cls.ACTIVE

else:
    # Fallback definitions when bridge is not available
    class Cardinality(str, Enum):
        """LinkType cardinality constraints (Fallback)."""
        ONE_TO_ONE = "1:1"
        ONE_TO_MANY = "1:N"
        MANY_TO_ONE = "N:1"
        MANY_TO_MANY = "N:N"

    class PropertyType(str, Enum):
        """Supported property data types (Fallback)."""
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
        """Lifecycle status for OntologyObjects (Fallback)."""
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
    
    # Interface Support (Phase 1 - Palantir-style Polymorphism)
    # Tracks which interfaces this ObjectType implements
    _implements: ClassVar[List[str]] = []
    _interface_validated_at: ClassVar[Optional[str]] = None

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
