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


class PropertyVisibility(str, Enum):
    """
    Property visibility levels for UI display.

    Aligned with Palantir Foundry property visibility:
    - NORMAL: Standard visibility in property lists and UI
    - PROMINENT: Highlighted/featured in UI, shown first
    - HIDDEN: Hidden from standard UI views, only accessible via API
    """

    NORMAL = "NORMAL"
    PROMINENT = "PROMINENT"
    HIDDEN = "HIDDEN"


# Alias for LinkType-specific usage
LinkMergeStrategy = MergeStrategy


class FunctionDecoratorType(str, Enum):
    """
    Function decorator types in Palantir Foundry.

    Aligned with Ontology.md Section 6 - Function Types:
    - FUNCTION: @Function() - General computation, derived values, data transformation
    - ONTOLOGY_EDIT_FUNCTION: @OntologyEditFunction() - Write operations to Ontology
    - QUERY: @Query() - Read-only queries exposed via API Gateway
    """

    FUNCTION = "FUNCTION"
    ONTOLOGY_EDIT_FUNCTION = "ONTOLOGY_EDIT_FUNCTION"
    QUERY = "QUERY"

    @property
    def allows_side_effects(self) -> bool:
        """Return True if this function type allows side effects."""
        # @Query functions must NOT have side effects
        return self != FunctionDecoratorType.QUERY

    @property
    def can_modify_ontology(self) -> bool:
        """Return True if this function type can modify the Ontology."""
        return self == FunctionDecoratorType.ONTOLOGY_EDIT_FUNCTION


class FunctionParameterType(str, Enum):
    """
    Supported types for function parameters and return values.

    Categories:
    - Primitives: Basic scalar types
    - Ontology: Object-related types
    - Collections: Container types
    - Custom: User-defined structures
    """

    # Primitives
    STRING = "STRING"
    INTEGER = "INTEGER"
    LONG = "LONG"
    DOUBLE = "DOUBLE"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    LOCAL_DATE = "LOCAL_DATE"

    # Ontology types
    OBJECT_TYPE = "OBJECT_TYPE"
    OBJECT_SET = "OBJECT_SET"
    SINGLE_LINK = "SINGLE_LINK"
    MULTI_LINK = "MULTI_LINK"

    # Collections
    ARRAY = "ARRAY"
    MAP = "MAP"
    SET = "SET"

    # Custom
    STRUCT = "STRUCT"

    # Void (for return type only)
    VOID = "VOID"

    @classmethod
    def primitive_types(cls) -> list["FunctionParameterType"]:
        """Return all primitive types."""
        return [
            cls.STRING,
            cls.INTEGER,
            cls.LONG,
            cls.DOUBLE,
            cls.FLOAT,
            cls.BOOLEAN,
            cls.TIMESTAMP,
            cls.DATE,
            cls.LOCAL_DATE,
        ]

    @classmethod
    def ontology_types(cls) -> list["FunctionParameterType"]:
        """Return all ontology-related types."""
        return [cls.OBJECT_TYPE, cls.OBJECT_SET, cls.SINGLE_LINK, cls.MULTI_LINK]

    @classmethod
    def collection_types(cls) -> list["FunctionParameterType"]:
        """Return all collection types."""
        return [cls.ARRAY, cls.MAP, cls.SET]

    @property
    def requires_type_parameter(self) -> bool:
        """Return True if this type requires a type parameter (generic)."""
        return self in {
            FunctionParameterType.OBJECT_SET,
            FunctionParameterType.SINGLE_LINK,
            FunctionParameterType.MULTI_LINK,
            FunctionParameterType.ARRAY,
            FunctionParameterType.MAP,
            FunctionParameterType.SET,
        }


class FunctionStatus(str, Enum):
    """
    Lifecycle status for Function definitions.

    Similar to other entity statuses but without ENDORSED
    (only ObjectTypes can be endorsed).
    """

    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    ALPHA = "ALPHA"
    BETA = "BETA"
    ACTIVE = "ACTIVE"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


# ============================================================================
# Automation Enums (Ontology.md Section 8)
# ============================================================================


class AutomationConditionType(str, Enum):
    """
    Types of automation trigger conditions.

    Aligned with Ontology.md Section 8 - Automation:
    - TIME: Schedule-based triggers (cron, hourly, daily, etc.)
    - OBJECT_SET: Data-driven triggers based on object changes
    """

    TIME = "TIME"
    OBJECT_SET = "OBJECT_SET"


class TimeConditionMode(str, Enum):
    """
    Schedule modes for TIME-based automation conditions.

    - HOURLY: Run every hour at specified minute
    - DAILY: Run daily at specified time
    - WEEKLY: Run weekly on specified days
    - MONTHLY: Run monthly on specified days
    - CRON: Custom schedule using 5-field cron expression
    """

    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CRON = "CRON"


class ObjectSetConditionTrigger(str, Enum):
    """
    Trigger types for OBJECT_SET-based automation conditions.

    Specifies what data change should trigger the automation:
    - OBJECTS_ADDED: New objects matching the set criteria
    - OBJECTS_REMOVED: Objects removed from the set
    - OBJECTS_MODIFIED: Existing objects in the set were updated
    - METRIC_CHANGED: Aggregated metric value changed
    - THRESHOLD_CROSSED: Metric crossed a defined threshold
    - OBJECTS_EXIST: Objects matching criteria exist (batch processing)
    """

    OBJECTS_ADDED = "OBJECTS_ADDED"
    OBJECTS_REMOVED = "OBJECTS_REMOVED"
    OBJECTS_MODIFIED = "OBJECTS_MODIFIED"
    METRIC_CHANGED = "METRIC_CHANGED"
    THRESHOLD_CROSSED = "THRESHOLD_CROSSED"
    OBJECTS_EXIST = "OBJECTS_EXIST"


class AutomationEffectType(str, Enum):
    """
    Types of automation effects (actions to execute).

    - ACTION: Execute an ActionType
    - NOTIFICATION: Send a notification (platform or email)
    - FALLBACK: Executed when primary effects fail
    """

    ACTION = "ACTION"
    NOTIFICATION = "NOTIFICATION"
    FALLBACK = "FALLBACK"


class ActionExecutionMode(str, Enum):
    """
    Execution modes for ACTION effects.

    - ONCE_ALL: Execute once for all matching objects
    - ONCE_BATCH: Execute once per batch of objects
    - ONCE_EACH_GROUP: Execute once for each group/partition
    """

    ONCE_ALL = "ONCE_ALL"
    ONCE_BATCH = "ONCE_BATCH"
    ONCE_EACH_GROUP = "ONCE_EACH_GROUP"


class RetryPolicyType(str, Enum):
    """
    Retry policy types for automation effects.

    - CONSTANT: Fixed delay between retries
    - EXPONENTIAL: Exponentially increasing delay (backoff)
    """

    CONSTANT = "CONSTANT"
    EXPONENTIAL = "EXPONENTIAL"


class NotificationEffectType(str, Enum):
    """
    Notification delivery types.

    - PLATFORM: In-app notification in Palantir Foundry
    - EMAIL: Email notification
    """

    PLATFORM = "PLATFORM"
    EMAIL = "EMAIL"


class EvaluationLatency(str, Enum):
    """
    Evaluation latency settings for automation.

    - LIVE: Real-time evaluation with minimal delay
    - SCHEDULED: Batch evaluation at scheduled intervals
    """

    LIVE = "LIVE"
    SCHEDULED = "SCHEDULED"


class AutomationStatus(str, Enum):
    """
    Lifecycle status for Automation definitions.

    Similar to other entity statuses.
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


# ============================================================================
# Writeback Enums (Ontology.md Section 10)
# ============================================================================


class WebhookExecutionOrder(str, Enum):
    """
    Execution order for webhooks in Action processing.

    Aligned with Ontology.md Section 10 - Writeback:
    - BEFORE_OTHER_RULES: Executed before other rules (writeback webhooks)
    - AFTER_OTHER_RULES: Executed after other rules (side effect webhooks)
    """

    BEFORE_OTHER_RULES = "BEFORE_OTHER_RULES"
    AFTER_OTHER_RULES = "AFTER_OTHER_RULES"


class WebhookFailureHandling(str, Enum):
    """
    Failure handling modes for webhooks.

    - BLOCKING: Failure blocks all changes and shows error to user
    - BEST_EFFORT: May fail silently without blocking changes
    """

    BLOCKING = "BLOCKING"
    BEST_EFFORT = "BEST_EFFORT"


class WebhookType(str, Enum):
    """
    Types of webhooks in Writeback configuration.

    - WRITEBACK: Main writeback webhook (one per Action, runs first)
    - SIDE_EFFECT: Additional webhooks for external notifications (multiple allowed)
    """

    WRITEBACK = "WRITEBACK"
    SIDE_EFFECT = "SIDE_EFFECT"


class ExportMode(str, Enum):
    """
    Export modes for external data synchronization.

    - BATCH: Batch export (file exports to S3, GCS, Azure Blob)
    - REALTIME: Real-time streaming (Kafka, Kinesis, PubSub)
    """

    BATCH = "BATCH"
    REALTIME = "REALTIME"


class ExportTargetType(str, Enum):
    """
    Target types for data exports.

    Cloud Storage (BATCH mode):
    - S3: Amazon S3
    - GCS: Google Cloud Storage
    - AZURE_BLOB: Azure Blob Storage

    Streaming (REALTIME mode):
    - KAFKA: Apache Kafka
    - KINESIS: Amazon Kinesis
    - PUBSUB: Google Pub/Sub

    Database:
    - JDBC: JDBC-compatible databases
    """

    # Cloud Storage (BATCH)
    S3 = "S3"
    GCS = "GCS"
    AZURE_BLOB = "AZURE_BLOB"

    # Streaming (REALTIME)
    KAFKA = "KAFKA"
    KINESIS = "KINESIS"
    PUBSUB = "PUBSUB"

    # Database
    JDBC = "JDBC"

    @classmethod
    def batch_targets(cls) -> list["ExportTargetType"]:
        """Return targets that support BATCH mode."""
        return [cls.S3, cls.GCS, cls.AZURE_BLOB, cls.JDBC]

    @classmethod
    def streaming_targets(cls) -> list["ExportTargetType"]:
        """Return targets that support REALTIME mode."""
        return [cls.KAFKA, cls.KINESIS, cls.PUBSUB]


class TableExportMode(str, Enum):
    """
    Write modes for JDBC table exports.

    - TRUNCATE_INSERT: Delete all rows before inserting
    - APPEND: Add new rows without deleting existing
    - UPSERT: Insert new, update existing (merge operation)
    """

    TRUNCATE_INSERT = "TRUNCATE_INSERT"
    APPEND = "APPEND"
    UPSERT = "UPSERT"


class ConflictResolutionStrategy(str, Enum):
    """
    Conflict resolution strategies for writeback datasets.

    - TIMESTAMP_WINS: Later edit wins based on timestamp
    - PRIORITY_WINS: Higher priority source wins
    - MANUAL: Requires manual resolution
    """

    TIMESTAMP_WINS = "TIMESTAMP_WINS"
    PRIORITY_WINS = "PRIORITY_WINS"
    MANUAL = "MANUAL"


class WritebackStatus(str, Enum):
    """
    Status for writeback configuration.
    """

    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PENDING = "PENDING"
    ERROR = "ERROR"
