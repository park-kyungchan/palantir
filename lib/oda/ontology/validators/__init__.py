"""
Orion ODA v4.0 - Schema Validators

Provides JSON Schema validation for ObjectType mutations,
ensuring schema-first compliance in all operations.

Also provides status transition validation for lifecycle management.
"""
from lib.oda.ontology.validators.schema_validator import (
    SchemaValidator,
    ValidationResult,
    SchemaVersion,
    get_validator,
)

from lib.oda.ontology.validators.status_validator import (
    StatusTransitionError,
    TransitionValidationResult,
    StatusTransitionValidator,
    validate_transition,
    assert_valid_transition,
)

__all__ = [
    # Schema Validators
    "SchemaValidator",
    "ValidationResult",
    "SchemaVersion",
    "get_validator",
    # Status Validators
    "StatusTransitionError",
    "TransitionValidationResult",
    "StatusTransitionValidator",
    "validate_transition",
    "assert_valid_transition",
]
