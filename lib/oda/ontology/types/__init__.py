"""
Orion ODA v4.0 - Ontology Type Definitions

This package contains type definitions for the Ontology-Driven Architecture:
- link_types.py: LinkTypeMetadata, constraint validators, cascade policies
- property_types.py: PropertyDefinition, constraint validators
- status_types.py: ResourceLifecycleStatus, transition rules

Schema Version: 4.0.0
"""

from lib.oda.ontology.types.status_types import (
    # Enums
    ResourceLifecycleStatus,
    StatusCategory,
    # Transition Rules
    VALID_TRANSITIONS,
    get_allowed_transitions,
    is_valid_transition,
)

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

from lib.oda.ontology.types.interface_types import (
    # Models
    PropertySpec,
    MethodSpec,
    InterfaceDefinition,
    InterfaceValidationError,
    InterfaceValidationResult,
    InterfaceImplementation,
)

from lib.oda.ontology.types.shared_properties import (
    # Models
    SharedPropertyDefinition,
    SharedPropertyUsage,
    SharedPropertyRegistry,
    # Built-in properties
    BUILTIN_AUDIT_PROPERTIES,
    BUILTIN_VERSION_PROPERTIES,
    BUILTIN_METADATA_PROPERTIES,
    BUILTIN_SHARED_PROPERTIES,
    # Utilities
    get_builtin_property,
    list_builtin_properties,
)

__all__ = [
    # Status Type Enums
    "ResourceLifecycleStatus",
    "StatusCategory",
    # Status Transition Rules
    "VALID_TRANSITIONS",
    "get_allowed_transitions",
    "is_valid_transition",
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
    # Interface Types
    "PropertySpec",
    "MethodSpec",
    "InterfaceDefinition",
    "InterfaceValidationError",
    "InterfaceValidationResult",
    "InterfaceImplementation",
    # Shared Property Types
    "SharedPropertyDefinition",
    "SharedPropertyUsage",
    "SharedPropertyRegistry",
    "BUILTIN_AUDIT_PROPERTIES",
    "BUILTIN_VERSION_PROPERTIES",
    "BUILTIN_METADATA_PROPERTIES",
    "BUILTIN_SHARED_PROPERTIES",
    "get_builtin_property",
    "list_builtin_properties",
]
