"""
Orion ODA v3.0 - Schema Validator

JSON Schema validation layer for ObjectType mutations.
Ensures all mutations comply with registered ObjectType schemas.

Features:
- Runtime validation against JSON Schema
- Schema versioning with semantic versioning
- Compiled schema caching for performance
- Validation mode configuration (strict, warn, off)

Environment Variables:
    ORION_SCHEMA_VALIDATION: Validation mode (strict|warn|off)

Usage:
    ```python
    from lib.oda.ontology.validators import get_validator

    validator = get_validator()
    result = validator.validate("Task", {"title": "My Task"})
    if not result.is_valid:
        print(result.errors)
    ```
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# VALIDATION MODE
# =============================================================================

class ValidationMode(str, Enum):
    """Schema validation enforcement mode."""
    STRICT = "strict"   # Validation failures raise exceptions
    WARN = "warn"       # Validation failures log warnings
    OFF = "off"         # No validation performed

    @classmethod
    def from_env(cls) -> "ValidationMode":
        """Get validation mode from environment."""
        mode = os.environ.get("ORION_SCHEMA_VALIDATION", "warn").lower()
        if mode == "strict":
            return cls.STRICT
        elif mode == "off":
            return cls.OFF
        return cls.WARN


# =============================================================================
# SCHEMA VERSION
# =============================================================================

@dataclass(frozen=True)
class SchemaVersion:
    """
    Semantic version for schema tracking.

    Format: MAJOR.MINOR.PATCH

    - MAJOR: Breaking changes (incompatible schema modifications)
    - MINOR: Backward-compatible additions
    - PATCH: Backward-compatible fixes
    """
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "SchemaVersion") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "SchemaVersion") -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    @classmethod
    def parse(cls, version_str: str) -> "SchemaVersion":
        """Parse version string (e.g., '3.0.1')."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str.strip())
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
        )

    @classmethod
    def initial(cls) -> "SchemaVersion":
        """Create initial version (3.0.0 for ODA v3)."""
        return cls(major=3, minor=0, patch=0)

    def bump_major(self) -> "SchemaVersion":
        """Bump major version (breaking change)."""
        return SchemaVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> "SchemaVersion":
        """Bump minor version (backward-compatible addition)."""
        return SchemaVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "SchemaVersion":
        """Bump patch version (backward-compatible fix)."""
        return SchemaVersion(self.major, self.minor, self.patch + 1)

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        """Check if this version is compatible with another (same major)."""
        return self.major == other.major


# =============================================================================
# VALIDATION RESULT
# =============================================================================

@dataclass
class ValidationError:
    """Single validation error."""
    path: str           # JSON path to the error (e.g., "properties.title")
    message: str        # Error description
    value: Any = None   # The invalid value (if available)
    schema_path: str = ""  # Path in schema that was violated

    def __str__(self) -> str:
        if self.path:
            return f"[{self.path}] {self.message}"
        return self.message


@dataclass
class ValidationResult:
    """Result of schema validation."""
    is_valid: bool
    object_type: str
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_version: Optional[SchemaVersion] = None
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "object_type": self.object_type,
            "errors": [
                {"path": e.path, "message": e.message}
                for e in self.errors
            ],
            "warnings": self.warnings,
            "schema_version": str(self.schema_version) if self.schema_version else None,
            "validated_at": self.validated_at.isoformat(),
        }

    @property
    def error_messages(self) -> List[str]:
        """Get all error messages as strings."""
        return [str(e) for e in self.errors]


# =============================================================================
# SCHEMA VALIDATOR
# =============================================================================

class SchemaValidationError(Exception):
    """Exception raised when validation fails in strict mode."""
    def __init__(self, result: ValidationResult):
        self.result = result
        super().__init__(
            f"Schema validation failed for {result.object_type}: "
            f"{', '.join(result.error_messages)}"
        )


class SchemaValidator:
    """
    JSON Schema validator for ObjectType mutations.

    Validates payloads against registered ObjectType schemas.
    Uses compiled schema caching for performance.
    """

    # Current schema version
    CURRENT_VERSION = SchemaVersion(major=3, minor=0, patch=1)

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        mode: Optional[ValidationMode] = None,
    ):
        """
        Initialize the schema validator.

        Args:
            schema_path: Path to schema JSON file. Defaults to .agent/schemas/ontology_registry.json
            mode: Validation mode. Defaults to environment variable or WARN.
        """
        self._mode = mode or ValidationMode.from_env()
        self._schema_path = schema_path or self._get_default_schema_path()
        self._schema_cache: Optional[Dict[str, Any]] = None
        self._compiled_schemas: Dict[str, Any] = {}
        self._version: Optional[SchemaVersion] = None

    @staticmethod
    def _get_default_schema_path() -> Path:
        """Get default schema path."""
        # Try to find workspace root
        workspace_root = os.environ.get(
            "ORION_WORKSPACE_ROOT",
            "/home/palantir/park-kyungchan/palantir"
        )
        return Path(workspace_root) / ".agent" / "schemas" / "ontology_registry.json"

    @property
    def mode(self) -> ValidationMode:
        """Current validation mode."""
        return self._mode

    @mode.setter
    def mode(self, value: ValidationMode) -> None:
        """Set validation mode."""
        self._mode = value

    @property
    def version(self) -> SchemaVersion:
        """Current schema version."""
        if self._version is None:
            self._load_schema()
        return self._version or self.CURRENT_VERSION

    def _load_schema(self) -> Dict[str, Any]:
        """Load schema from file with caching."""
        if self._schema_cache is not None:
            return self._schema_cache

        if not self._schema_path.exists():
            logger.warning(f"Schema file not found: {self._schema_path}")
            self._schema_cache = {"objects": {}}
            self._version = self.CURRENT_VERSION
            return self._schema_cache

        try:
            with open(self._schema_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._schema_cache = data

            # Extract version if present
            if "version" in data:
                try:
                    self._version = SchemaVersion.parse(data["version"])
                except ValueError:
                    self._version = self.CURRENT_VERSION
            else:
                self._version = self.CURRENT_VERSION

            logger.debug(f"Loaded schema version {self._version} from {self._schema_path}")
            return self._schema_cache

        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            self._schema_cache = {"objects": {}}
            self._version = self.CURRENT_VERSION
            return self._schema_cache

    def _get_object_schema(self, object_type: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific ObjectType."""
        schema = self._load_schema()
        objects = schema.get("objects", {})
        return objects.get(object_type)

    def _validate_required_fields(
        self,
        object_type: str,
        payload: Dict[str, Any],
        object_schema: Dict[str, Any],
    ) -> List[ValidationError]:
        """Validate required fields are present."""
        errors = []
        properties = object_schema.get("properties", {})

        for prop_name, prop_def in properties.items():
            if prop_def.get("required", False):
                if prop_name not in payload:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Required field '{prop_name}' is missing",
                    ))
                elif payload[prop_name] is None:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Required field '{prop_name}' cannot be null",
                        value=None,
                    ))

        return errors

    def _validate_field_types(
        self,
        object_type: str,
        payload: Dict[str, Any],
        object_schema: Dict[str, Any],
    ) -> List[ValidationError]:
        """Validate field types match schema."""
        errors = []
        properties = object_schema.get("properties", {})

        type_mapping = {
            "string": str,
            "integer": int,
            "boolean": bool,
            "array": list,
            "struct": dict,
            "timestamp": str,  # ISO format string
        }

        for prop_name, value in payload.items():
            if prop_name not in properties:
                continue  # Unknown field, could warn but not error

            if value is None:
                continue  # Null values handled separately

            prop_def = properties[prop_name]
            expected_type = prop_def.get("type", "string")
            python_type = type_mapping.get(expected_type)

            if python_type and not isinstance(value, python_type):
                errors.append(ValidationError(
                    path=f"properties.{prop_name}",
                    message=f"Field '{prop_name}' expected {expected_type}, got {type(value).__name__}",
                    value=value,
                ))

        return errors

    def _validate_constraints(
        self,
        object_type: str,
        payload: Dict[str, Any],
        object_schema: Dict[str, Any],
    ) -> List[ValidationError]:
        """Validate field constraints (min/max length, etc.)."""
        errors = []
        properties = object_schema.get("properties", {})

        for prop_name, value in payload.items():
            if prop_name not in properties or value is None:
                continue

            prop_def = properties[prop_name]
            constraints = prop_def.get("constraints", {})

            # String length constraints
            if isinstance(value, str):
                min_length = constraints.get("min_length")
                max_length = constraints.get("max_length")

                if min_length is not None and len(value) < min_length:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Field '{prop_name}' must be at least {min_length} characters",
                        value=value,
                    ))

                if max_length is not None and len(value) > max_length:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Field '{prop_name}' must be at most {max_length} characters",
                        value=value,
                    ))

            # Numeric constraints
            if isinstance(value, (int, float)):
                min_value = constraints.get("ge") or constraints.get("min")
                max_value = constraints.get("le") or constraints.get("max")

                if min_value is not None and value < min_value:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Field '{prop_name}' must be >= {min_value}",
                        value=value,
                    ))

                if max_value is not None and value > max_value:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Field '{prop_name}' must be <= {max_value}",
                        value=value,
                    ))

            # Array constraints
            if isinstance(value, list):
                min_items = constraints.get("min_items")
                max_items = constraints.get("max_items")

                if min_items is not None and len(value) < min_items:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Field '{prop_name}' must have at least {min_items} items",
                        value=value,
                    ))

                if max_items is not None and len(value) > max_items:
                    errors.append(ValidationError(
                        path=f"properties.{prop_name}",
                        message=f"Field '{prop_name}' must have at most {max_items} items",
                        value=value,
                    ))

        return errors

    def validate(
        self,
        object_type: str,
        payload: Dict[str, Any],
        partial: bool = False,
    ) -> ValidationResult:
        """
        Validate a payload against an ObjectType schema.

        Args:
            object_type: Name of the ObjectType (e.g., "Task")
            payload: Dictionary of field values to validate
            partial: If True, skip required field validation (for updates)

        Returns:
            ValidationResult with validation status and any errors
        """
        # Check if validation is disabled
        if self._mode == ValidationMode.OFF:
            return ValidationResult(
                is_valid=True,
                object_type=object_type,
                schema_version=self.version,
            )

        # Get object schema
        object_schema = self._get_object_schema(object_type)
        if object_schema is None:
            warning = f"No schema found for ObjectType '{object_type}'"
            logger.warning(warning)
            return ValidationResult(
                is_valid=True,  # Pass if schema not found (graceful degradation)
                object_type=object_type,
                warnings=[warning],
                schema_version=self.version,
            )

        # Collect all errors
        all_errors: List[ValidationError] = []

        # Validate required fields (unless partial update)
        if not partial:
            all_errors.extend(
                self._validate_required_fields(object_type, payload, object_schema)
            )

        # Validate field types
        all_errors.extend(
            self._validate_field_types(object_type, payload, object_schema)
        )

        # Validate constraints
        all_errors.extend(
            self._validate_constraints(object_type, payload, object_schema)
        )

        result = ValidationResult(
            is_valid=len(all_errors) == 0,
            object_type=object_type,
            errors=all_errors,
            schema_version=self.version,
        )

        # Handle based on mode
        if not result.is_valid:
            if self._mode == ValidationMode.STRICT:
                raise SchemaValidationError(result)
            elif self._mode == ValidationMode.WARN:
                for error in all_errors:
                    logger.warning(f"Schema validation: {error}")

        return result

    def validate_mutation(
        self,
        object_type: str,
        payload: Dict[str, Any],
        is_create: bool = True,
    ) -> ValidationResult:
        """
        Validate a mutation (create or update) payload.

        Args:
            object_type: Name of the ObjectType
            payload: Mutation payload
            is_create: True for create, False for update

        Returns:
            ValidationResult
        """
        return self.validate(
            object_type=object_type,
            payload=payload,
            partial=not is_create,
        )

    def invalidate_cache(self) -> None:
        """Invalidate the schema cache (call after schema updates)."""
        self._schema_cache = None
        self._compiled_schemas.clear()
        self._version = None

    def get_registered_types(self) -> List[str]:
        """Get list of registered ObjectType names."""
        schema = self._load_schema()
        return list(schema.get("objects", {}).keys())


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_validator_instance: Optional[SchemaValidator] = None


def get_validator() -> SchemaValidator:
    """
    Get the global SchemaValidator instance.

    Creates the instance on first call (lazy initialization).
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = SchemaValidator()
    return _validator_instance


def set_validation_mode(mode: ValidationMode) -> None:
    """Set the global validation mode."""
    get_validator().mode = mode


def invalidate_schema_cache() -> None:
    """Invalidate the global schema cache."""
    get_validator().invalidate_cache()
