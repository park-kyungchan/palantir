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

from ontology_definition.core.base import OntologyEntity
from ontology_definition.core.enums import (
    AccessLevel,
    Cardinality,
    CascadeAction,
    DataType,
    LinkTypeStatus,
    ObjectStatus,
)
from ontology_definition.core.identifiers import RID, ApiName, generate_rid, generate_uuid
from ontology_definition.core.metadata import (
    ActionTypeMetadata,
    AuditMetadata,
    ExportMetadata,
    InterfaceMetadata,
    LinkTypeMetadata,
    ObjectTypeMetadata,
    TagMetadata,
    VersionMetadata,
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
