from .plan import Plan
from .job import Job
from .action import Action
from .trace import Trace, Status as StatusEnum
from .event import Event, EventType
from .metric import Metric

# Bridge module - provides canonical types from ontology_definition
# This is the preferred import path for schema definition types
from .bridge import (
    # Core Enums (canonical source)
    DataType as BridgeDataType,
    Cardinality as BridgeCardinality,
    ObjectStatus as BridgeObjectStatus,
    # Schema Types
    ObjectType,
    LinkType,
    ActionType,
    PropertyDefinition as BridgePropertyDefinition,
    DataTypeSpec,
    # Validation
    SchemaValidator,
    validate_all,
)

# Runtime types from ontology_types (ODA-specific)
from .ontology_types import (
    # Runtime Enums (short notation for backward compatibility)
    Cardinality,
    PropertyType,
    ObjectStatus,
    # Runtime Classes
    Link,
    Reference,
    OntologyObject,
    # Utilities
    generate_object_id,
    utc_now,
)

__all__ = [
    # Original exports
    "Plan",
    "Job",
    "Action",
    "Trace",
    "StatusEnum",
    "Event",
    "EventType",
    "Metric",
    # Bridge exports (canonical schema types)
    "BridgeDataType",
    "BridgeCardinality",
    "BridgeObjectStatus",
    "ObjectType",
    "LinkType",
    "ActionType",
    "BridgePropertyDefinition",
    "DataTypeSpec",
    "SchemaValidator",
    "validate_all",
    # Runtime exports (ODA-specific)
    "Cardinality",
    "PropertyType",
    "ObjectStatus",
    "Link",
    "Reference",
    "OntologyObject",
    "generate_object_id",
    "utc_now",
]
