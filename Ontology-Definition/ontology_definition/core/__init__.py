"""
Core module - Base classes, enums, and fundamental types.

Exports:
    - OntologyEntity: Base class for all ontology entities
    - DataType: 20 supported data types (STRING, INTEGER, etc.)
    - Cardinality: Relationship cardinality (ONE_TO_ONE, ONE_TO_MANY, etc.)
    - ObjectStatus: Lifecycle status (DRAFT, ACTIVE, DEPRECATED, etc.)
    - RID, ApiName: Identifier types
    - AuditMetadata, ExportMetadata: Metadata models
"""

from ontology_definition.core.enums import (
    Cardinality,
    DataType,
    ObjectStatus,
    LinkTypeStatus,
    CascadeAction,
    AccessLevel,
)
from ontology_definition.core.base import OntologyEntity
from ontology_definition.core.identifiers import RID, ApiName, generate_rid, generate_uuid
from ontology_definition.core.metadata import (
    AuditMetadata,
    ExportMetadata,
    VersionMetadata,
    TagMetadata,
    ObjectTypeMetadata,
    InterfaceMetadata,
    LinkTypeMetadata,
    ActionTypeMetadata,
)

__all__ = [
    # Enums
    "DataType",
    "Cardinality",
    "ObjectStatus",
    "LinkTypeStatus",
    "CascadeAction",
    "AccessLevel",
    # Base
    "OntologyEntity",
    # Identifiers
    "RID",
    "ApiName",
    "generate_rid",
    "generate_uuid",
    # Metadata
    "AuditMetadata",
    "ExportMetadata",
    "VersionMetadata",
    "TagMetadata",
    "ObjectTypeMetadata",
    "InterfaceMetadata",
    "LinkTypeMetadata",
    "ActionTypeMetadata",
]
