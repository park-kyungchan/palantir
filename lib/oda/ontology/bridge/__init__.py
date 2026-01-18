"""
ODA <-> Ontology-Definition Integration Bridge

This module re-exports core types from ontology_definition,
ensuring ODA uses a single source of truth for ontology schema definitions.

The ontology_definition package provides Palantir Foundry-aligned schema types:
- ObjectType, LinkType, ActionType for defining ontology entities
- PropertyDefinition, DataTypeSpec for property schemas
- SchemaValidator, validate_all for dual-layer validation

Usage:
    from lib.oda.ontology.bridge import (
        ObjectType,
        LinkType,
        ActionType,
        DataType,
        Cardinality,
    )

Note:
    This bridge ensures backwards compatibility while migrating ODA
    to use ontology_definition as the canonical source of truth.
"""

import sys
from pathlib import Path

# Ensure ontology_definition is importable
# Add Ontology-Definition root to path if not already present
_ontology_def_root = Path(__file__).resolve().parents[4] / "Ontology-Definition"
if _ontology_def_root.exists() and str(_ontology_def_root) not in sys.path:
    sys.path.insert(0, str(_ontology_def_root))

# Core enums - fundamental building blocks
from ontology_definition.core.enums import (
    AccessLevel,
    BackingDatasetMode,
    Cardinality,
    CascadeAction,
    ClassificationLevel,
    ControlType,
    DataType,
    ForeignKeyLocation,
    LinkImplementationType,
    LinkMergeStrategy,
    LinkTypeStatus,
    MergeStrategy,
    ObjectStatus,
    SecurityPolicyType,
)

# Base class for all ontology entities
from ontology_definition.core.base import OntologyEntity, utc_now

# Identifier types and generators
from ontology_definition.core.identifiers import (
    ApiName,
    RID,
    generate_rid,
    generate_uuid,
)

# Alias for backward compatibility with ODA runtime
generate_object_id = generate_uuid

# Metadata types
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

# Main type definitions - ObjectType, LinkType, ActionType
from ontology_definition.types import (
    # ObjectType and related
    ObjectType,
    BackingDatasetConfig,
    SecurityConfig,
    ObjectSecurityPolicy,
    PropertySecurityPolicy,
    # LinkType and related
    LinkType,
    ObjectTypeReference,
    CardinalityConfig,
    LinkImplementation,
    ForeignKeyConfig,
    BackingTableConfig,
    BackingTableColumnMapping,
    CascadePolicy,
    LinkPropertyDefinition,
    LinkMergingConfig,
    LinkSecurityConfig,
    LinkPropertySecurityPolicy,
    # ActionType and related
    ActionType,
    ActionParameter,
    ParameterDataType,
    ParameterConstraints,
    ParameterUIHints,
    AffectedObjectType,
    EditSpecification,
    PropertyMapping,
    ObjectSelection,
    LinkSelection,
    EditCondition,
    SubmissionCriterion,
    SideEffect,
    SideEffectConfig,
    NotificationConfig,
    WebhookConfig,
    TriggerActionConfig,
    ActionImplementation,
    ActionPermissions,
    ObjectTypePermission,
    AuditConfig,
    UndoConfig,
    # Property definitions
    PropertyDefinition,
    DataTypeSpec,
    PrimaryKeyDefinition,
    StructField,
    # Interface
    Interface,
    InterfaceStatus,
    InterfacePropertyRequirement,
    InterfaceActionDefinition,
    InterfaceImplementation,
    # ValueType
    ValueType,
    ValueTypeBaseType,
    ValueTypeConstraints,
    ValueTypeStatus,
    CommonValueTypes,
    # StructType
    StructType,
    StructTypeField,
    StructFieldConstraints,
    StructTypeStatus,
    CommonStructTypes,
    # SharedProperty
    SharedProperty,
    SharedPropertyStatus,
    SemanticType,
    CommonSharedProperties,
)

# Security types
from ontology_definition.security import (
    ComparisonOperator,
    LogicalOperator,
    PolicyTerm,
    PolicyTermType,
    RestrictedViewPolicy,
)

# Constraint types
from ontology_definition.constraints import (
    MandatoryControlConfig,
    PropertyConstraints,
)

# Validation - dual-layer (Pydantic + JSON Schema)
from ontology_definition.validation import (
    # Schema Validator (JSON Schema Draft 2020-12)
    SchemaValidator,
    SchemaType,
    ValidationResult,
    ValidationErrorDetail,
    schema_validate_object_type,
    schema_validate_link_type,
    schema_validate_action_type,
    # Cross-Reference Validator
    CrossRefValidator,
    CrossRefValidationResult,
    ReferenceError,
    validate_cross_references,
    find_orphaned_types,
    # Runtime Validator (Pydantic)
    RuntimeValidator,
    RuntimeValidationResult,
    InstanceValidationResult,
    FieldValidationError,
    validate_model,
    validate_instance,
    # Combined validation
    validate_all,
)

# Re-export version
from ontology_definition import __version__ as ontology_definition_version

__version__ = "1.0.0"
__bridge_version__ = "1.0.0"

# Comprehensive __all__ for explicit exports
__all__ = [
    # Version info
    "__version__",
    "__bridge_version__",
    "ontology_definition_version",
    # Core Enums
    "DataType",
    "Cardinality",
    "ObjectStatus",
    "LinkTypeStatus",
    "CascadeAction",
    "AccessLevel",
    "ControlType",
    "ClassificationLevel",
    "SecurityPolicyType",
    "LinkImplementationType",
    "ForeignKeyLocation",
    "MergeStrategy",
    "LinkMergeStrategy",
    "BackingDatasetMode",
    # Base
    "OntologyEntity",
    "utc_now",
    # Identifiers
    "RID",
    "ApiName",
    "generate_rid",
    "generate_uuid",
    "generate_object_id",  # Alias for generate_uuid
    # Metadata
    "AuditMetadata",
    "ExportMetadata",
    "VersionMetadata",
    "TagMetadata",
    "ObjectTypeMetadata",
    "InterfaceMetadata",
    "LinkTypeMetadata",
    "ActionTypeMetadata",
    # ObjectType
    "ObjectType",
    "BackingDatasetConfig",
    "SecurityConfig",
    "ObjectSecurityPolicy",
    "PropertySecurityPolicy",
    # LinkType
    "LinkType",
    "ObjectTypeReference",
    "CardinalityConfig",
    "LinkImplementation",
    "ForeignKeyConfig",
    "BackingTableConfig",
    "BackingTableColumnMapping",
    "CascadePolicy",
    "LinkPropertyDefinition",
    "LinkMergingConfig",
    "LinkSecurityConfig",
    "LinkPropertySecurityPolicy",
    # ActionType
    "ActionType",
    "ActionParameter",
    "ParameterDataType",
    "ParameterConstraints",
    "ParameterUIHints",
    "AffectedObjectType",
    "EditSpecification",
    "PropertyMapping",
    "ObjectSelection",
    "LinkSelection",
    "EditCondition",
    "SubmissionCriterion",
    "SideEffect",
    "SideEffectConfig",
    "NotificationConfig",
    "WebhookConfig",
    "TriggerActionConfig",
    "ActionImplementation",
    "ActionPermissions",
    "ObjectTypePermission",
    "AuditConfig",
    "UndoConfig",
    # Property definitions
    "PropertyDefinition",
    "DataTypeSpec",
    "PrimaryKeyDefinition",
    "StructField",
    # Interface
    "Interface",
    "InterfaceStatus",
    "InterfacePropertyRequirement",
    "InterfaceActionDefinition",
    "InterfaceImplementation",
    # ValueType
    "ValueType",
    "ValueTypeBaseType",
    "ValueTypeConstraints",
    "ValueTypeStatus",
    "CommonValueTypes",
    # StructType
    "StructType",
    "StructTypeField",
    "StructFieldConstraints",
    "StructTypeStatus",
    "CommonStructTypes",
    # SharedProperty
    "SharedProperty",
    "SharedPropertyStatus",
    "SemanticType",
    "CommonSharedProperties",
    # Security
    "RestrictedViewPolicy",
    "PolicyTerm",
    "PolicyTermType",
    "LogicalOperator",
    "ComparisonOperator",
    # Constraints
    "PropertyConstraints",
    "MandatoryControlConfig",
    # Schema Validation
    "SchemaValidator",
    "SchemaType",
    "ValidationResult",
    "ValidationErrorDetail",
    "schema_validate_object_type",
    "schema_validate_link_type",
    "schema_validate_action_type",
    # Cross-Reference Validation
    "CrossRefValidator",
    "CrossRefValidationResult",
    "ReferenceError",
    "validate_cross_references",
    "find_orphaned_types",
    # Runtime Validation
    "RuntimeValidator",
    "RuntimeValidationResult",
    "InstanceValidationResult",
    "FieldValidationError",
    "validate_model",
    "validate_instance",
    # Combined Validation
    "validate_all",
]


def get_bridge_info() -> dict:
    """Return information about the bridge module."""
    return {
        "bridge_version": __bridge_version__,
        "ontology_definition_version": ontology_definition_version,
        "canonical_source": "ontology_definition",
        "purpose": "Single source of truth for ODA ontology types",
        "export_count": len(__all__),
    }
