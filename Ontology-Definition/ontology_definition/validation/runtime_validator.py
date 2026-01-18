"""
Runtime Validator - Pydantic-based runtime validation for ontology types.

This validator performs runtime type checking and constraint validation
using Pydantic's built-in validation. It provides:
    - Full model validation with detailed error reporting
    - Partial validation (validate specific fields only)
    - Instance data validation against ObjectType schemas
    - Batch validation with aggregated results

Example:
    from ontology_definition.validation import RuntimeValidator
    from ontology_definition import ObjectType

    validator = RuntimeValidator()

    # Validate a complete model
    result = validator.validate_model(my_object_type)

    # Validate instance data against an ObjectType schema
    result = validator.validate_instance(
        object_type=employee_type,
        data={"employeeId": "123", "name": "John"}
    )

    # Batch validation
    types_to_validate = [obj1, obj2, obj3, link1, link2]
    results = validator.validate_batch(types_to_validate)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError as PydanticValidationError

if TYPE_CHECKING:
    from ontology_definition.types.object_type import ObjectType
    from ontology_definition.types.property_def import PropertyDefinition


@dataclass
class FieldValidationError:
    """Details of a single field validation error."""

    field: str
    message: str
    input_value: Any = None
    error_type: str = ""
    loc: tuple[str, ...] = ()


@dataclass
class RuntimeValidationResult:
    """Result of runtime validation."""

    is_valid: bool
    errors: list[FieldValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    model_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                    "input_value": str(e.input_value)[:100] if e.input_value else None,
                    "error_type": e.error_type,
                    "loc": list(e.loc),
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
            "model_type": self.model_type,
        }


@dataclass
class InstanceValidationResult:
    """Result of validating instance data against ObjectType schema."""

    is_valid: bool
    errors: list[FieldValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    extra_fields: list[str] = field(default_factory=list)
    object_type_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                    "input_value": str(e.input_value)[:100] if e.input_value else None,
                    "error_type": e.error_type,
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
            "missing_required": self.missing_required,
            "extra_fields": self.extra_fields,
            "object_type_name": self.object_type_name,
        }


class RuntimeValidator:
    """
    Runtime validator using Pydantic's validation system.

    Provides validation for ontology type definitions and instance data.
    """

    def __init__(self, strict_mode: bool = False) -> None:
        """
        Initialize the RuntimeValidator.

        Args:
            strict_mode: If True, treat warnings as errors.
        """
        self._strict_mode = strict_mode

    def validate_model(
        self, model: Any, model_class: type[Any] | None = None
    ) -> RuntimeValidationResult:
        """
        Validate a Pydantic model instance.

        This re-validates an already-constructed model by round-tripping
        through model_dump/model_validate. Useful for catching post-mutation
        validation issues.

        Args:
            model: A Pydantic model instance.
            model_class: Optional explicit class to validate against.

        Returns:
            RuntimeValidationResult with any errors.
        """
        if model_class is None:
            model_class = model.__class__

        model_name = model_class.__name__
        errors: list[FieldValidationError] = []
        warnings: list[str] = []

        try:
            # Round-trip validation: dump and re-validate
            data = model.model_dump(by_alias=True)
            model_class.model_validate(data)

        except PydanticValidationError as e:
            for error in e.errors():
                errors.append(
                    FieldValidationError(
                        field=".".join(str(loc) for loc in error["loc"]),
                        message=error["msg"],
                        input_value=error.get("input"),
                        error_type=error["type"],
                        loc=error["loc"],
                    )
                )
        except Exception as e:
            errors.append(
                FieldValidationError(
                    field="__root__",
                    message=str(e),
                    error_type="unexpected_error",
                )
            )

        return RuntimeValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            model_type=model_name,
        )

    def validate_dict_as_model(
        self, data: dict[str, Any], model_class: type[Any]
    ) -> RuntimeValidationResult:
        """
        Validate a dictionary against a Pydantic model class.

        Args:
            data: Dictionary to validate.
            model_class: Pydantic model class to validate against.

        Returns:
            RuntimeValidationResult with any errors.
        """
        model_name = model_class.__name__
        errors: list[FieldValidationError] = []

        try:
            model_class.model_validate(data)
        except PydanticValidationError as e:
            for error in e.errors():
                errors.append(
                    FieldValidationError(
                        field=".".join(str(loc) for loc in error["loc"]),
                        message=error["msg"],
                        input_value=error.get("input"),
                        error_type=error["type"],
                        loc=error["loc"],
                    )
                )
        except Exception as e:
            errors.append(
                FieldValidationError(
                    field="__root__",
                    message=str(e),
                    error_type="unexpected_error",
                )
            )

        return RuntimeValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            model_type=model_name,
        )

    def validate_instance(
        self,
        object_type: ObjectType,
        data: dict[str, Any],
        allow_extra: bool = False,
    ) -> InstanceValidationResult:
        """
        Validate instance data against an ObjectType schema.

        This validates actual object instances (e.g., Employee records)
        against their ObjectType definition (e.g., Employee ObjectType).

        Args:
            object_type: The ObjectType defining the schema.
            data: The instance data to validate.
            allow_extra: If False, extra fields not in schema are flagged.

        Returns:
            InstanceValidationResult with validation details.
        """

        errors: list[FieldValidationError] = []
        warnings: list[str] = []
        missing_required: list[str] = []
        extra_fields: list[str] = []

        # Build property map
        prop_map: dict[str, PropertyDefinition] = {}
        for prop in object_type.properties:
            prop_map[prop.api_name] = prop

        # Check for required fields
        for prop in object_type.properties:
            if prop.constraints and prop.constraints.required:
                if prop.api_name not in data or data[prop.api_name] is None:
                    missing_required.append(prop.api_name)
                    errors.append(
                        FieldValidationError(
                            field=prop.api_name,
                            message=f"Required field '{prop.api_name}' is missing",
                            error_type="missing_required",
                        )
                    )

        # Check each provided field
        for field_name, value in data.items():
            if field_name not in prop_map:
                extra_fields.append(field_name)
                if not allow_extra:
                    warnings.append(f"Extra field '{field_name}' not in schema")
                continue

            prop = prop_map[field_name]
            field_errors = self._validate_field_value(prop, value)
            errors.extend(field_errors)

        # Check primary key if present
        pk_prop_name = object_type.primary_key.property_api_name
        if pk_prop_name not in data or data[pk_prop_name] is None:
            if pk_prop_name not in missing_required:
                missing_required.append(pk_prop_name)
                errors.append(
                    FieldValidationError(
                        field=pk_prop_name,
                        message=f"Primary key field '{pk_prop_name}' is required",
                        error_type="missing_primary_key",
                    )
                )

        return InstanceValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required,
            extra_fields=extra_fields,
            object_type_name=object_type.api_name,
        )

    def _validate_field_value(
        self, prop: PropertyDefinition, value: Any
    ) -> list[FieldValidationError]:
        """Validate a single field value against its PropertyDefinition."""

        errors: list[FieldValidationError] = []

        if value is None:
            # Null check is handled elsewhere (required fields)
            return errors

        data_type = prop.data_type.type if prop.data_type else None

        # Type checking based on DataType
        if data_type:
            type_error = self._check_type(prop.api_name, value, data_type)
            if type_error:
                errors.append(type_error)
                return errors  # Skip constraint checks if type is wrong

        # Constraint validation
        if prop.constraints:
            constraint_errors = self._validate_constraints(prop, value)
            errors.extend(constraint_errors)

        return errors

    def _check_type(
        self, field_name: str, value: Any, data_type: Any
    ) -> FieldValidationError | None:
        """Check if value matches expected data type."""
        from ontology_definition.core.enums import DataType

        # Type mapping for basic validation
        # Note: Only types that exist in the DataType enum are included
        type_checks: dict[DataType, type | tuple[type, ...]] = {
            DataType.STRING: str,
            DataType.BOOLEAN: bool,
            DataType.INTEGER: int,
            DataType.LONG: int,
            DataType.FLOAT: (int, float),
            DataType.DOUBLE: (int, float),
            DataType.DECIMAL: (int, float, str),  # Decimal can be string
            DataType.DATE: str,  # ISO date string
            DataType.TIMESTAMP: str,  # ISO timestamp string
            DataType.DATETIME: str,  # ISO datetime string
        }

        expected_type = type_checks.get(data_type)
        if expected_type and not isinstance(value, expected_type):
            return FieldValidationError(
                field=field_name,
                message=f"Expected type {data_type.value}, got {type(value).__name__}",
                input_value=value,
                error_type="type_error",
            )

        # Special handling for arrays
        if data_type == DataType.ARRAY:
            if not isinstance(value, (list, tuple)):
                return FieldValidationError(
                    field=field_name,
                    message=f"Expected array, got {type(value).__name__}",
                    input_value=value,
                    error_type="type_error",
                )

        # Special handling for structs
        if data_type == DataType.STRUCT:
            if not isinstance(value, dict):
                return FieldValidationError(
                    field=field_name,
                    message=f"Expected object/struct, got {type(value).__name__}",
                    input_value=value,
                    error_type="type_error",
                )

        return None

    def _validate_constraints(
        self, prop: PropertyDefinition, value: Any
    ) -> list[FieldValidationError]:
        """Validate value against PropertyConstraints.

        PropertyConstraints uses nested constraint objects:
        - constraints.string.min_length/max_length/pattern for STRING
        - constraints.numeric.min_value/max_value for numeric types
        - constraints.array.min_items/max_items for ARRAY
        - constraints.enum for allowed values (top-level)
        """
        errors: list[FieldValidationError] = []
        constraints = prop.constraints

        if not constraints:
            return errors

        # Min/max length for strings (nested in constraints.string)
        if isinstance(value, str) and constraints.string:
            string_constraints = constraints.string
            if string_constraints.min_length is not None and len(value) < string_constraints.min_length:
                errors.append(
                    FieldValidationError(
                        field=prop.api_name,
                        message=f"String length {len(value)} is less than minimum {string_constraints.min_length}",
                        input_value=value,
                        error_type="min_length",
                    )
                )
            if string_constraints.max_length is not None and len(value) > string_constraints.max_length:
                errors.append(
                    FieldValidationError(
                        field=prop.api_name,
                        message=f"String length {len(value)} exceeds maximum {string_constraints.max_length}",
                        input_value=value,
                        error_type="max_length",
                    )
                )
            # Pattern matching for strings (nested in constraints.string)
            if string_constraints.pattern:
                import re

                if not re.match(string_constraints.pattern, value):
                    errors.append(
                        FieldValidationError(
                            field=prop.api_name,
                            message=f"Value '{value}' does not match pattern '{string_constraints.pattern}'",
                            input_value=value,
                            error_type="pattern",
                        )
                    )

        # Min/max value for numbers (nested in constraints.numeric)
        if isinstance(value, (int, float)) and constraints.numeric:
            numeric_constraints = constraints.numeric
            if numeric_constraints.min_value is not None and value < numeric_constraints.min_value:
                errors.append(
                    FieldValidationError(
                        field=prop.api_name,
                        message=f"Value {value} is less than minimum {numeric_constraints.min_value}",
                        input_value=value,
                        error_type="min_value",
                    )
                )
            if numeric_constraints.max_value is not None and value > numeric_constraints.max_value:
                errors.append(
                    FieldValidationError(
                        field=prop.api_name,
                        message=f"Value {value} exceeds maximum {numeric_constraints.max_value}",
                        input_value=value,
                        error_type="max_value",
                    )
                )

        # Enum validation (top-level in constraints)
        if constraints.enum and value not in constraints.enum:
            errors.append(
                FieldValidationError(
                    field=prop.api_name,
                    message=f"Value '{value}' is not in allowed values: {constraints.enum}",
                    input_value=value,
                    error_type="enum",
                )
            )

        return errors

    def validate_batch(
        self, models: list[Any]
    ) -> dict[str, RuntimeValidationResult]:
        """
        Validate multiple models in batch.

        Args:
            models: List of Pydantic models to validate.

        Returns:
            Dictionary mapping model identifiers to validation results.
        """
        results: dict[str, RuntimeValidationResult] = {}

        for model in models:
            # Generate unique key
            model_type = model.__class__.__name__
            api_name = getattr(model, "api_name", str(id(model)))
            key = f"{model_type}:{api_name}"

            results[key] = self.validate_model(model)

        return results

    def validate_batch_summary(
        self, models: list[Any]
    ) -> RuntimeValidationResult:
        """
        Validate multiple models and return combined result.

        Args:
            models: List of Pydantic models to validate.

        Returns:
            Combined RuntimeValidationResult.
        """
        all_results = self.validate_batch(models)

        all_errors: list[FieldValidationError] = []
        all_warnings: list[str] = []

        for key, result in all_results.items():
            # Prefix errors with model identifier
            for error in result.errors:
                prefixed_error = FieldValidationError(
                    field=f"{key}.{error.field}",
                    message=error.message,
                    input_value=error.input_value,
                    error_type=error.error_type,
                    loc=error.loc,
                )
                all_errors.append(prefixed_error)
            all_warnings.extend(result.warnings)

        return RuntimeValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            model_type="batch",
        )


# Convenience functions
def validate_model(model: Any) -> RuntimeValidationResult:
    """Validate a Pydantic model using default validator."""
    return RuntimeValidator().validate_model(model)


def validate_instance(
    object_type: ObjectType, data: dict[str, Any]
) -> InstanceValidationResult:
    """Validate instance data against an ObjectType."""
    return RuntimeValidator().validate_instance(object_type, data)
