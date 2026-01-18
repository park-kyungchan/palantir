"""
Ontology Definition Package

Palantir Foundry-aligned ontology schema definitions for ODA system.
Provides ObjectType, LinkType, ActionType, and related primitives.

Usage:
    from ontology_definition import ObjectType, LinkType, ActionType
    from ontology_definition.core import DataType, Cardinality, ObjectStatus
    from ontology_definition.types import PropertyDefinition, DataTypeSpec
    from ontology_definition.security import RestrictedViewPolicy, PolicyTerm
"""

__version__ = "1.0.0"
__author__ = "ODA Team"

# Core exports
# Constraint exports
from ontology_definition.constraints import (
    MandatoryControlConfig,
    PropertyConstraints,
)
from ontology_definition.core import (
    AccessLevel,
    Cardinality,
    CascadeAction,
    DataType,
    LinkTypeStatus,
    ObjectStatus,
    OntologyEntity,
    generate_rid,
    generate_uuid,
)

# Security exports
from ontology_definition.security import (
    ComparisonOperator,
    LogicalOperator,
    PolicyTerm,
    PolicyTermType,
    RestrictedViewPolicy,
)

# Type exports
from ontology_definition.types import (
    ActionType,
    DataTypeSpec,
    Interface,
    LinkType,
    ObjectType,
    PrimaryKeyDefinition,
    PropertyDefinition,
    SharedProperty,
    StructType,
    ValueType,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "DataType",
    "Cardinality",
    "ObjectStatus",
    "LinkTypeStatus",
    "CascadeAction",
    "AccessLevel",
    "OntologyEntity",
    "generate_rid",
    "generate_uuid",
    # Types
    "ObjectType",
    "LinkType",
    "ActionType",
    "PropertyDefinition",
    "DataTypeSpec",
    "PrimaryKeyDefinition",
    "Interface",
    "ValueType",
    "StructType",
    "SharedProperty",
    # Security
    "RestrictedViewPolicy",
    "PolicyTerm",
    "PolicyTermType",
    "LogicalOperator",
    "ComparisonOperator",
    # Constraints
    "PropertyConstraints",
    "MandatoryControlConfig",
]
