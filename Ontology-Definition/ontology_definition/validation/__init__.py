"""
Validation module - Dual-layer validation (Pydantic + JSON Schema).

Provides three complementary validation approaches:
    1. SchemaValidator: JSON Schema Draft 2020-12 validation
    2. CrossRefValidator: Cross-reference integrity validation
    3. RuntimeValidator: Pydantic runtime type/constraint validation

Example:
    from ontology_definition.validation import (
        SchemaValidator,
        CrossRefValidator,
        RuntimeValidator,
        validate_all,
    )

    # JSON Schema validation
    schema_validator = SchemaValidator()
    result = schema_validator.validate_object_type(my_obj)

    # Cross-reference validation
    xref_validator = CrossRefValidator()
    result = xref_validator.validate_all()

    # Runtime validation
    runtime_validator = RuntimeValidator()
    result = runtime_validator.validate_instance(object_type, data)

    # Combined validation
    results = validate_all(my_object_type)
"""

from ontology_definition.validation.schema_validator import (
    SchemaValidator,
    SchemaType,
    ValidationResult,
    ValidationErrorDetail,
    validate_object_type as schema_validate_object_type,
    validate_link_type as schema_validate_link_type,
    validate_action_type as schema_validate_action_type,
)

from ontology_definition.validation.cross_ref_validator import (
    CrossRefValidator,
    CrossRefValidationResult,
    ReferenceError,
    validate_cross_references,
    find_orphaned_types,
)

from ontology_definition.validation.runtime_validator import (
    RuntimeValidator,
    RuntimeValidationResult,
    InstanceValidationResult,
    FieldValidationError,
    validate_model,
    validate_instance,
)


def validate_all(model: object) -> dict[str, object]:
    """
    Perform all three types of validation on a model.

    Args:
        model: An ontology type model (ObjectType, LinkType, etc.)

    Returns:
        Dictionary with results from each validator:
        - schema: SchemaValidator result
        - runtime: RuntimeValidator result
        - cross_ref: CrossRefValidator result (if applicable)
    """
    results: dict[str, object] = {}

    # Schema validation
    try:
        schema_validator = SchemaValidator()
        results["schema"] = schema_validator.validate_model(model)
    except Exception as e:
        results["schema"] = ValidationResult(
            is_valid=False,
            errors=[ValidationErrorDetail(message=str(e), path="")],
        )

    # Runtime validation
    try:
        runtime_validator = RuntimeValidator()
        results["runtime"] = runtime_validator.validate_model(model)
    except Exception as e:
        results["runtime"] = RuntimeValidationResult(
            is_valid=False,
            errors=[FieldValidationError(field="__root__", message=str(e))],
        )

    # Cross-reference validation (type-specific)
    try:
        xref_validator = CrossRefValidator()
        model_type = model.__class__.__name__

        if model_type == "ObjectType":
            results["cross_ref"] = xref_validator.validate_object_type(model)  # type: ignore
        elif model_type == "LinkType":
            results["cross_ref"] = xref_validator.validate_link_type(model)  # type: ignore
        elif model_type == "ActionType":
            results["cross_ref"] = xref_validator.validate_action_type(model)  # type: ignore
        elif model_type == "Interface":
            results["cross_ref"] = xref_validator.validate_interface(model)  # type: ignore
        else:
            results["cross_ref"] = None
    except Exception as e:
        results["cross_ref"] = CrossRefValidationResult(
            is_valid=False,
            errors=[
                ReferenceError(
                    source_type=model.__class__.__name__,
                    source_name=str(getattr(model, "api_name", "unknown")),
                    reference_field="__root__",
                    referenced_type="",
                    referenced_name="",
                    message=str(e),
                )
            ],
        )

    return results


__all__ = [
    # Schema Validator
    "SchemaValidator",
    "SchemaType",
    "ValidationResult",
    "ValidationErrorDetail",
    "schema_validate_object_type",
    "schema_validate_link_type",
    "schema_validate_action_type",
    # Cross-Reference Validator
    "CrossRefValidator",
    "CrossRefValidationResult",
    "ReferenceError",
    "validate_cross_references",
    "find_orphaned_types",
    # Runtime Validator
    "RuntimeValidator",
    "RuntimeValidationResult",
    "InstanceValidationResult",
    "FieldValidationError",
    "validate_model",
    "validate_instance",
    # Combined
    "validate_all",
]
