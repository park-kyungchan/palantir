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
from ontology_definition.core import (
    DataType,
    Cardinality,
    ObjectStatus,
    LinkTypeStatus,
    CascadeAction,
    AccessLevel,
    OntologyEntity,
    generate_rid,
    generate_uuid,
)

# Type exports
from ontology_definition.types import (
    ObjectType,
    LinkType,
    ActionType,
    PropertyDefinition,
    DataTypeSpec,
    PrimaryKeyDefinition,
    Interface,
    ValueType,
    StructType,
    SharedProperty,
)

# Security exports
from ontology_definition.security import (
    RestrictedViewPolicy,
    PolicyTerm,
    PolicyTermType,
    LogicalOperator,
    ComparisonOperator,
)

# Constraint exports
from ontology_definition.constraints import (
    PropertyConstraints,
    MandatoryControlConfig,
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
