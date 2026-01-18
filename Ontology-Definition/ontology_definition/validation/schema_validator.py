"""
JSON Schema Validator - Validates ontology definitions against JSON Schemas.

Uses JSON Schema Draft 2020-12 for validation, aligned with Palantir Foundry's
schema definitions. Schemas are bundled in the ontology_definition/schemas/ directory.

Supported Schemas:
    - ObjectType.schema.json: ObjectType validation
    - LinkType.schema.json: LinkType validation
    - ActionType.schema.json: ActionType validation
    - PropertyDefinition.schema.json: Property validation
    - Interface.schema.json: Interface validation
    - SharedProperty.schema.json: SharedProperty validation

Example:
    from ontology_definition.validation import SchemaValidator

    validator = SchemaValidator()

    # Validate an ObjectType
    result = validator.validate_object_type(my_object_type)
    if result.is_valid:
        print("Valid!")
    else:
        for error in result.errors:
            print(f"Error: {error.message} at {error.path}")

    # Validate raw JSON/dict
    result = validator.validate_dict("ObjectType", raw_data)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft202012Validator, ValidationError
    from jsonschema.protocols import Validator

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    jsonschema = None  # type: ignore
    Draft202012Validator = None  # type: ignore
    ValidationError = None  # type: ignore
    Validator = None  # type: ignore


class SchemaType(str, Enum):
    """Supported schema types for validation."""

    OBJECT_TYPE = "ObjectType"
    LINK_TYPE = "LinkType"
    ACTION_TYPE = "ActionType"
    PROPERTY_DEFINITION = "PropertyDefinition"
    INTERFACE = "Interface"
    SHARED_PROPERTY = "SharedProperty"


@dataclass
class ValidationErrorDetail:
    """Details of a single validation error."""

    message: str
    path: str
    schema_path: str = ""
    value: Any = None
    constraint: str = ""


@dataclass
class ValidationResult:
    """Result of schema validation."""

    is_valid: bool
    errors: list[ValidationErrorDetail] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": [
                {
                    "message": e.message,
                    "path": e.path,
                    "schema_path": e.schema_path,
                    "value": str(e.value)[:100] if e.value else None,
                    "constraint": e.constraint,
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
            "schema_type": self.schema_type,
        }


class SchemaValidator:
    """
    JSON Schema validator for ontology definitions.

    Validates Pydantic models or dictionaries against bundled JSON Schemas.
    Uses JSON Schema Draft 2020-12 (jsonschema library required).
    """

    # Schema file mapping
    SCHEMA_FILES: dict[SchemaType, str] = {
        SchemaType.OBJECT_TYPE: "ObjectType.schema.json",
        SchemaType.LINK_TYPE: "LinkType.schema.json",
        SchemaType.ACTION_TYPE: "ActionType.schema.json",
        SchemaType.PROPERTY_DEFINITION: "PropertyDefinition.schema.json",
        SchemaType.INTERFACE: "Interface.schema.json",
        SchemaType.SHARED_PROPERTY: "SharedProperty.schema.json",
    }

    def __init__(self, schemas_dir: Path | None = None) -> None:
        """
        Initialize the SchemaValidator.

        Args:
            schemas_dir: Custom directory containing schema files.
                        Defaults to ontology_definition/schemas/.
        """
        if schemas_dir is None:
            # Default to bundled schemas directory
            self._schemas_dir = Path(__file__).parent.parent / "schemas"
        else:
            self._schemas_dir = schemas_dir

        # Cache loaded schemas
        self._schema_cache: dict[SchemaType, dict[str, Any]] = {}

        # Cache compiled validators
        self._validator_cache: dict[SchemaType, Any] = {}

    def _ensure_jsonschema(self) -> None:
        """Ensure jsonschema is installed."""
        if not HAS_JSONSCHEMA:
            raise ImportError(
                "jsonschema library is required for schema validation. "
                "Install it with: pip install jsonschema"
            )

    def load_schema(self, schema_type: SchemaType) -> dict[str, Any]:
        """
        Load a JSON schema by type.

        Args:
            schema_type: The type of schema to load.

        Returns:
            The parsed JSON schema as a dictionary.

        Raises:
            FileNotFoundError: If schema file doesn't exist.
            json.JSONDecodeError: If schema file is invalid JSON.
        """
        if schema_type in self._schema_cache:
            return self._schema_cache[schema_type]

        schema_file = self._schemas_dir / self.SCHEMA_FILES[schema_type]

        if not schema_file.exists():
            raise FileNotFoundError(
                f"Schema file not found: {schema_file}. "
                f"Available schemas: {list(self._schemas_dir.glob('*.json'))}"
            )

        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)

        self._schema_cache[schema_type] = schema
        return schema

    def get_validator(self, schema_type: SchemaType) -> Any:
        """
        Get a compiled validator for a schema type.

        Args:
            schema_type: The type of schema.

        Returns:
            A jsonschema Validator instance.
        """
        self._ensure_jsonschema()

        if schema_type in self._validator_cache:
            return self._validator_cache[schema_type]

        schema = self.load_schema(schema_type)
        validator = Draft202012Validator(schema)
        self._validator_cache[schema_type] = validator
        return validator

    def validate_dict(
        self, schema_type: SchemaType | str, data: dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a dictionary against a JSON schema.

        Args:
            schema_type: The schema type (enum or string name).
            data: The dictionary to validate.

        Returns:
            ValidationResult with is_valid and any errors.
        """
        self._ensure_jsonschema()

        # Convert string to enum if needed
        if isinstance(schema_type, str):
            try:
                schema_type = SchemaType(schema_type)
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    errors=[
                        ValidationErrorDetail(
                            message=f"Unknown schema type: {schema_type}",
                            path="",
                        )
                    ],
                    schema_type=str(schema_type),
                )

        try:
            validator = self.get_validator(schema_type)
        except FileNotFoundError as e:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationErrorDetail(message=str(e), path="")],
                schema_type=schema_type.value,
            )

        errors: list[ValidationErrorDetail] = []
        for error in validator.iter_errors(data):
            errors.append(
                ValidationErrorDetail(
                    message=error.message,
                    path="/".join(str(p) for p in error.absolute_path),
                    schema_path="/".join(str(p) for p in error.schema_path),
                    value=error.instance,
                    constraint=error.validator,
                )
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            schema_type=schema_type.value,
        )

    def validate_model(
        self, model: Any, schema_type: SchemaType | None = None
    ) -> ValidationResult:
        """
        Validate a Pydantic model against its JSON schema.

        Args:
            model: A Pydantic model instance with model_dump() or to_foundry_dict().
            schema_type: Optional explicit schema type. If not provided,
                        will be inferred from model class name.

        Returns:
            ValidationResult with is_valid and any errors.
        """
        # Infer schema type from class name if not provided
        if schema_type is None:
            class_name = model.__class__.__name__
            try:
                schema_type = SchemaType(class_name)
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    errors=[
                        ValidationErrorDetail(
                            message=f"Cannot infer schema type from class: {class_name}",
                            path="",
                        )
                    ],
                )

        # Convert model to dict
        if hasattr(model, "to_foundry_dict"):
            data = model.to_foundry_dict()
        elif hasattr(model, "model_dump"):
            data = model.model_dump(by_alias=True, exclude_none=True)
        else:
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationErrorDetail(
                        message="Model must have to_foundry_dict() or model_dump() method",
                        path="",
                    )
                ],
            )

        return self.validate_dict(schema_type, data)

    # Convenience methods for specific types
    def validate_object_type(self, obj: Any) -> ValidationResult:
        """Validate an ObjectType model or dict."""
        if isinstance(obj, dict):
            return self.validate_dict(SchemaType.OBJECT_TYPE, obj)
        return self.validate_model(obj, SchemaType.OBJECT_TYPE)

    def validate_link_type(self, obj: Any) -> ValidationResult:
        """Validate a LinkType model or dict."""
        if isinstance(obj, dict):
            return self.validate_dict(SchemaType.LINK_TYPE, obj)
        return self.validate_model(obj, SchemaType.LINK_TYPE)

    def validate_action_type(self, obj: Any) -> ValidationResult:
        """Validate an ActionType model or dict."""
        if isinstance(obj, dict):
            return self.validate_dict(SchemaType.ACTION_TYPE, obj)
        return self.validate_model(obj, SchemaType.ACTION_TYPE)

    def validate_interface(self, obj: Any) -> ValidationResult:
        """Validate an Interface model or dict."""
        if isinstance(obj, dict):
            return self.validate_dict(SchemaType.INTERFACE, obj)
        return self.validate_model(obj, SchemaType.INTERFACE)

    def list_available_schemas(self) -> list[str]:
        """List all available schema files."""
        if not self._schemas_dir.exists():
            return []
        return [f.name for f in self._schemas_dir.glob("*.json")]

    def get_schema_as_dict(self, schema_type: SchemaType) -> dict[str, Any]:
        """Get a schema as a dictionary (for export/inspection)."""
        return self.load_schema(schema_type)


# Module-level convenience functions
def validate_object_type(obj: Any) -> ValidationResult:
    """Validate an ObjectType using default validator."""
    return SchemaValidator().validate_object_type(obj)


def validate_link_type(obj: Any) -> ValidationResult:
    """Validate a LinkType using default validator."""
    return SchemaValidator().validate_link_type(obj)


def validate_action_type(obj: Any) -> ValidationResult:
    """Validate an ActionType using default validator."""
    return SchemaValidator().validate_action_type(obj)
