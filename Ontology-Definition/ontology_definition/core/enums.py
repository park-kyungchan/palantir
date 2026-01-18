"""
Core Enumerations for Ontology Definition.

This module defines all enumeration types used across the ontology schema system,
aligned with Palantir Foundry ontology specifications.

Includes:
    - DataType: 20 supported property data types
    - Cardinality: LinkType relationship cardinality
    - ObjectStatus: Lifecycle status for ObjectTypes (includes ENDORSED)
    - LinkTypeStatus: Lifecycle status for LinkTypes (no ENDORSED)
    - CascadeAction: Referential integrity actions
    - AccessLevel: Property access levels
    - ControlType: Mandatory control types for row-level security
"""

from enum import Enum


class DataType(str, Enum):
    """
    Supported property data types in Palantir Foundry Ontology.

    20 base types covering:
    - Primitives: STRING, INTEGER, LONG, FLOAT, DOUBLE, BOOLEAN, DECIMAL
    - Temporal: DATE, TIMESTAMP, DATETIME, TIMESERIES
    - Complex: ARRAY, STRUCT, JSON
    - Spatial: GEOPOINT, GEOSHAPE
    - Media: MEDIA_REFERENCE, BINARY, MARKDOWN
    - AI/ML: VECTOR

    Note: ARRAY and STRUCT require additional configuration:
    - ARRAY: Must specify arrayItemType
    - STRUCT: Must specify structFields
    - VECTOR: Must specify vectorDimension
    - DECIMAL: Should specify precision and scale
    """

    # Primitive Types
    STRING = "STRING"
    INTEGER = "INTEGER"
    LONG = "LONG"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    BOOLEAN = "BOOLEAN"
    DECIMAL = "DECIMAL"

    # Temporal Types
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    DATETIME = "DATETIME"
    TIMESERIES = "TIMESERIES"

    # Complex Types
    ARRAY = "ARRAY"
    STRUCT = "STRUCT"
    JSON = "JSON"

    # Spatial Types
    GEOPOINT = "GEOPOINT"
    GEOSHAPE = "GEOSHAPE"

    # Media Types
    MEDIA_REFERENCE = "MEDIA_REFERENCE"
    BINARY = "BINARY"
    MARKDOWN = "MARKDOWN"

    # AI/ML Types
    VECTOR = "VECTOR"

    @classmethod
    def primitive_types(cls) -> list["DataType"]:
        """Return all primitive (scalar) types."""
        return [
            cls.STRING,
            cls.INTEGER,
            cls.LONG,
            cls.FLOAT,
            cls.DOUBLE,
            cls.BOOLEAN,
            cls.DECIMAL,
        ]

    @classmethod
    def temporal_types(cls) -> list["DataType"]:
        """Return all temporal (date/time) types."""
        return [cls.DATE, cls.TIMESTAMP, cls.DATETIME, cls.TIMESERIES]

    @classmethod
    def complex_types(cls) -> list["DataType"]:
        """Return all complex (nested) types."""
        return [cls.ARRAY, cls.STRUCT, cls.JSON]

    @classmethod
    def requires_config(cls) -> list["DataType"]:
        """Return types that require additional configuration."""
        return [cls.ARRAY, cls.STRUCT, cls.VECTOR, cls.DECIMAL]


class Cardinality(str, Enum):
    """
    LinkType relationship cardinality constraints.

    Aligned with Palantir Foundry Link Types:
    - ONE_TO_ONE: Single object on both sides (indicator only, not enforced by default)
    - ONE_TO_MANY: Foreign key on "many" side pointing to "one" side
    - MANY_TO_ONE: Reverse of ONE_TO_MANY
    - MANY_TO_MANY: Requires backing/junction table

    Note: In Palantir Foundry, ONE_TO_ONE is typically an indicator rather than
    a strictly enforced constraint. Use `enforced=True` for strict enforcement.
    """

    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"

    @property
    def requires_backing_table(self) -> bool:
        """Return True if this cardinality requires a backing (junction) table."""
        return self == Cardinality.MANY_TO_MANY

    @property
    def short_notation(self) -> str:
        """Return short notation (1:1, 1:N, N:1, N:N)."""
        mapping = {
            Cardinality.ONE_TO_ONE: "1:1",
            Cardinality.ONE_TO_MANY: "1:N",
            Cardinality.MANY_TO_ONE: "N:1",
            Cardinality.MANY_TO_MANY: "N:N",
        }
        return mapping[self]


class ObjectStatus(str, Enum):
    """
    Lifecycle status for ObjectTypes.

    Full lifecycle progression:
    DRAFT → EXPERIMENTAL → ALPHA → BETA → ACTIVE → STABLE → DEPRECATED → SUNSET → ARCHIVED/DELETED

    Key statuses:
    - DRAFT: Initial creation, not visible to others
    - EXPERIMENTAL: Visible but schema may change significantly
    - ACTIVE: Production-ready, schema changes need migration
    - STABLE: Frozen schema, no changes allowed
    - DEPRECATED: Marked for removal, use alternative
    - ARCHIVED: Soft-deleted, data preserved but inaccessible

    Note: Unlike LinkTypeStatus, ObjectStatus supports ENDORSED status
    which can only be set by Ontology Owner.
    """

    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    ALPHA = "ALPHA"
    BETA = "BETA"
    ACTIVE = "ACTIVE"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"
    SUNSET = "SUNSET"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"

    @property
    def allows_schema_changes(self) -> bool:
        """Return True if schema modifications are allowed in this status."""
        return self in {
            ObjectStatus.DRAFT,
            ObjectStatus.EXPERIMENTAL,
            ObjectStatus.ALPHA,
            ObjectStatus.BETA,
        }

    @property
    def is_production(self) -> bool:
        """Return True if this is a production status."""
        return self in {ObjectStatus.ACTIVE, ObjectStatus.STABLE}

    @property
    def is_end_of_life(self) -> bool:
        """Return True if this status indicates end-of-life."""
        return self in {
            ObjectStatus.DEPRECATED,
            ObjectStatus.SUNSET,
            ObjectStatus.ARCHIVED,
            ObjectStatus.DELETED,
        }


class LinkTypeStatus(str, Enum):
    """
    Lifecycle status for LinkTypes.

    Same as ObjectStatus but WITHOUT ENDORSED status.
    Palantir Foundry only supports endorsed status on ObjectTypes, not LinkTypes.
    """

    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    ALPHA = "ALPHA"
    BETA = "BETA"
    ACTIVE = "ACTIVE"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"
    SUNSET = "SUNSET"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class CascadeAction(str, Enum):
    """
    Referential integrity actions for LinkType cascade policies.

    Actions taken when source or target objects are modified/deleted:
    - RESTRICT: Prevent operation if links exist
    - CASCADE: Propagate the operation to linked objects/links
    - SET_NULL: Set foreign key to null (requires nullable FK)
    - SET_DEFAULT: Set foreign key to default value
    - NO_ACTION: Take no action (may leave orphan references)
    """

    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    SET_NULL = "SET_NULL"
    SET_DEFAULT = "SET_DEFAULT"
    NO_ACTION = "NO_ACTION"


class AccessLevel(str, Enum):
    """
    Property access level for security policies.

    Defines visibility and mutability:
    - FULL: Complete read/write access
    - READ_ONLY: Can view but not modify
    - MASKED: Partial visibility (e.g., last 4 digits of SSN)
    - HIDDEN: Completely hidden from user
    """

    FULL = "FULL"
    READ_ONLY = "READ_ONLY"
    MASKED = "MASKED"
    HIDDEN = "HIDDEN"


class ControlType(str, Enum):
    """
    Mandatory control types for row-level security (GAP-002).

    Palantir Foundry supports these mandatory control mechanisms:
    - MARKINGS: Controls based on security markings (most common)
    - ORGANIZATIONS: Controls based on organization membership
    - CLASSIFICATIONS: Classification-Based Access Control (CBAC), government use

    Note: MARKINGS is the most commonly used type in Foundry.
    CLASSIFICATIONS is typically only used in government deployments.
    """

    MARKINGS = "MARKINGS"
    ORGANIZATIONS = "ORGANIZATIONS"
    CLASSIFICATIONS = "CLASSIFICATIONS"


class ClassificationLevel(str, Enum):
    """
    Classification levels for CBAC (Classification-Based Access Control).

    Used with ControlType.CLASSIFICATIONS in government deployments.
    """

    UNCLASSIFIED = "UNCLASSIFIED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"


class SecurityPolicyType(str, Enum):
    """
    Types of security policies for ObjectTypes.

    - RESTRICTED_VIEW: Uses Foundry Restricted View for row filtering
    - PROPERTY_BASED: Filter based on property values and user attributes
    - CUSTOM: Custom security logic via function/expression
    """

    RESTRICTED_VIEW = "RESTRICTED_VIEW"
    PROPERTY_BASED = "PROPERTY_BASED"
    CUSTOM = "CUSTOM"


class LinkImplementationType(str, Enum):
    """
    Physical implementation type for LinkTypes.

    - FOREIGN_KEY: Standard FK relationship (1:1, 1:N, N:1)
    - BACKING_TABLE: Junction table (required for N:N)
    """

    FOREIGN_KEY = "FOREIGN_KEY"
    BACKING_TABLE = "BACKING_TABLE"


class ForeignKeyLocation(str, Enum):
    """
    Which side of the link holds the foreign key.

    For FOREIGN_KEY implementation:
    - SOURCE: FK is on the source ObjectType
    - TARGET: FK is on the target ObjectType
    """

    SOURCE = "SOURCE"
    TARGET = "TARGET"


class MergeStrategy(str, Enum):
    """
    Merge strategy for conflicting data from multiple sources (MDO).

    - FIRST_WINS: First value encountered takes precedence
    - LAST_WINS: Last value encountered takes precedence
    - PRIORITY_BASED: Use priority field to determine winner
    """

    FIRST_WINS = "FIRST_WINS"
    LAST_WINS = "LAST_WINS"
    PRIORITY_BASED = "PRIORITY_BASED"


class BackingDatasetMode(str, Enum):
    """
    Mode for ObjectType backing dataset configuration.

    - SINGLE: Single dataset backs the ObjectType (default)
    - MULTI: Multi-Dataset Object (MDO) - multiple datasets merged
    """

    SINGLE = "SINGLE"
    MULTI = "MULTI"


# Alias for LinkType-specific usage
LinkMergeStrategy = MergeStrategy
