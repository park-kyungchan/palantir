"""
Orion ODA v4.0 - Ontology Type Definitions

This package contains type definitions for the Ontology-Driven Architecture:
- link_types.py: LinkTypeMetadata, constraint validators, cascade policies
- property_types.py: PropertyDefinition, constraint validators

Schema Version: 4.0.0
"""

from lib.oda.ontology.types.link_types import (
    # Enums
    CascadePolicy,
    LinkDirection,
    IntegrityViolationType,
    # Models
    LinkTypeMetadata,
    LinkTypeConstraints,
    LinkConstraint,
    IntegrityViolation,
    # Services
    ReferentialIntegrityChecker,
)

from lib.oda.ontology.types.property_types import (
    # Enums
    PropertyDataType,
    ConstraintType,
    ConstraintSeverity,
    # Models
    PropertyConstraint,
    PropertyDefinition,
    ConstraintViolation,
    # Validator
    PropertyConstraintValidator,
    get_property_validator,
)

__all__ = [
    # Link Type Enums
    "CascadePolicy",
    "LinkDirection",
    "IntegrityViolationType",
    # Link Type Models
    "LinkTypeMetadata",
    "LinkTypeConstraints",
    "LinkConstraint",
    "IntegrityViolation",
    # Link Type Services
    "ReferentialIntegrityChecker",
    # Property Type Enums
    "PropertyDataType",
    "ConstraintType",
    "ConstraintSeverity",
    # Property Type Models
    "PropertyConstraint",
    "PropertyDefinition",
    "ConstraintViolation",
    # Property Type Services
    "PropertyConstraintValidator",
    "get_property_validator",
]
