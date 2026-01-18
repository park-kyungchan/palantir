"""
Version Migration Utilities - Handle schema version migrations.

This module provides utilities for migrating ontology definitions
between different schema versions:
    - Upgrade paths from older formats to current
    - Compatibility layer for deprecated fields
    - Version detection and validation

Example:
    from ontology_definition.import_ import MigrationManager

    manager = MigrationManager()

    # Check version of JSON data
    version = manager.detect_version(json_data)

    # Migrate to current version
    migrated_data = manager.migrate(json_data)

    # Check if migration is needed
    if manager.needs_migration(json_data):
        json_data = manager.migrate(json_data)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Version constants
CURRENT_SCHEMA_VERSION = "2.0.0"
MINIMUM_SUPPORTED_VERSION = "1.0.0"


@dataclass
class MigrationStep:
    """A single migration step."""

    from_version: str
    to_version: str
    description: str
    transformer: callable


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    from_version: str
    to_version: str
    steps_applied: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "steps_applied": self.steps_applied,
            "warnings": self.warnings,
        }


class MigrationManager:
    """
    Manager for schema version migrations.

    Handles upgrading ontology definitions from older schema versions
    to the current version.
    """

    def __init__(self) -> None:
        """Initialize the MigrationManager."""
        self._migrations: list[MigrationStep] = []
        self._register_migrations()

    def _register_migrations(self) -> None:
        """Register all migration steps."""
        # V1.0.0 -> V1.1.0: Add endorsed field
        self._migrations.append(
            MigrationStep(
                from_version="1.0.0",
                to_version="1.1.0",
                description="Add endorsed field to ObjectType",
                transformer=self._migrate_1_0_to_1_1,
            )
        )

        # V1.1.0 -> V1.2.0: Add security config
        self._migrations.append(
            MigrationStep(
                from_version="1.1.0",
                to_version="1.2.0",
                description="Add securityConfig structure",
                transformer=self._migrate_1_1_to_1_2,
            )
        )

        # V1.2.0 -> V2.0.0: Full schema update
        self._migrations.append(
            MigrationStep(
                from_version="1.2.0",
                to_version="2.0.0",
                description="Full schema update with new field names",
                transformer=self._migrate_1_2_to_2_0,
            )
        )

    def detect_version(self, data: dict[str, Any]) -> str:
        """
        Detect the schema version of JSON data.

        Args:
            data: JSON data dictionary.

        Returns:
            Detected version string (e.g., "1.0.0").
        """
        # Check explicit version field
        if "_metadata" in data and "schemaVersion" in data["_metadata"]:
            return data["_metadata"]["schemaVersion"]

        if "schemaVersion" in data:
            return data["schemaVersion"]

        # Heuristic detection based on field presence
        if "ontology" in data:
            ontology = data["ontology"]
            sample = None

            # Get a sample ObjectType
            if "objectTypes" in ontology and ontology["objectTypes"]:
                sample = ontology["objectTypes"][0]
            elif "object_types" in ontology and ontology["object_types"]:
                sample = ontology["object_types"][0]
        else:
            sample = data

        if sample:
            # V2.0.0 uses camelCase consistently
            if "apiName" in sample and "primaryKey" in sample:
                if "securityConfig" in sample:
                    return "2.0.0"
                return "1.2.0"

            # V1.x uses mixed casing
            if "api_name" in sample:
                if "security_config" in sample:
                    return "1.2.0"
                if "endorsed" in sample:
                    return "1.1.0"
                return "1.0.0"

        # Default to current
        return CURRENT_SCHEMA_VERSION

    def needs_migration(self, data: dict[str, Any]) -> bool:
        """
        Check if data needs migration.

        Args:
            data: JSON data dictionary.

        Returns:
            True if migration is needed.
        """
        version = self.detect_version(data)
        return version != CURRENT_SCHEMA_VERSION

    def is_version_supported(self, version: str) -> bool:
        """
        Check if a version is supported for migration.

        Args:
            version: Version string.

        Returns:
            True if version can be migrated.
        """
        # Simple version comparison
        return self._compare_versions(version, MINIMUM_SUPPORTED_VERSION) >= 0

    def migrate(
        self,
        data: dict[str, Any],
        target_version: str | None = None,
    ) -> MigrationResult:
        """
        Migrate data to target version.

        Args:
            data: JSON data dictionary.
            target_version: Target version (default: current).

        Returns:
            MigrationResult with migrated data.
        """
        if target_version is None:
            target_version = CURRENT_SCHEMA_VERSION

        from_version = self.detect_version(data)

        if from_version == target_version:
            return MigrationResult(
                success=True,
                from_version=from_version,
                to_version=target_version,
                data=data,
            )

        if not self.is_version_supported(from_version):
            return MigrationResult(
                success=False,
                from_version=from_version,
                to_version=target_version,
                warnings=[
                    f"Version {from_version} is below minimum supported "
                    f"version {MINIMUM_SUPPORTED_VERSION}"
                ],
            )

        # Apply migrations in sequence
        current_version = from_version
        current_data = data.copy()
        steps_applied: list[str] = []
        warnings: list[str] = []

        while current_version != target_version:
            # Find next migration step
            next_step = self._find_migration_step(current_version)

            if next_step is None:
                # No direct migration, try to continue
                warnings.append(
                    f"No migration path from {current_version} to {target_version}"
                )
                break

            try:
                current_data = next_step.transformer(current_data)
                steps_applied.append(next_step.description)
                current_version = next_step.to_version
            except Exception as e:
                return MigrationResult(
                    success=False,
                    from_version=from_version,
                    to_version=current_version,
                    steps_applied=steps_applied,
                    warnings=[f"Migration failed: {str(e)}"],
                )

        # Add version metadata
        if "_metadata" not in current_data:
            current_data["_metadata"] = {}
        current_data["_metadata"]["schemaVersion"] = current_version

        return MigrationResult(
            success=True,
            from_version=from_version,
            to_version=current_version,
            steps_applied=steps_applied,
            warnings=warnings,
            data=current_data,
        )

    def _find_migration_step(self, from_version: str) -> MigrationStep | None:
        """Find the migration step from a given version."""
        for step in self._migrations:
            if step.from_version == from_version:
                return step
        return None

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """

        def parse_version(v: str) -> tuple[int, ...]:
            return tuple(int(x) for x in v.split("."))

        p1 = parse_version(v1)
        p2 = parse_version(v2)

        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1
        return 0

    # Migration transformers
    def _migrate_1_0_to_1_1(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate from V1.0.0 to V1.1.0."""
        result = data.copy()

        def add_endorsed(obj: dict[str, Any]) -> dict[str, Any]:
            if "endorsed" not in obj:
                obj["endorsed"] = False
            return obj

        if "ontology" in result:
            for ot in result["ontology"].get("objectTypes", []):
                add_endorsed(ot)
        elif "apiName" in result or "api_name" in result:
            add_endorsed(result)

        return result

    def _migrate_1_1_to_1_2(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate from V1.1.0 to V1.2.0."""
        result = data.copy()

        def add_security_config(obj: dict[str, Any]) -> dict[str, Any]:
            if "security_config" not in obj and "securityConfig" not in obj:
                obj["securityConfig"] = None
            return obj

        if "ontology" in result:
            for ot in result["ontology"].get("objectTypes", []):
                add_security_config(ot)
        elif "apiName" in result or "api_name" in result:
            add_security_config(result)

        return result

    def _migrate_1_2_to_2_0(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate from V1.2.0 to V2.0.0."""
        result = data.copy()

        # Field name mappings (snake_case -> camelCase)
        field_mappings = {
            "api_name": "apiName",
            "display_name": "displayName",
            "primary_key": "primaryKey",
            "property_api_name": "propertyApiName",
            "data_type": "dataType",
            "item_type": "itemType",
            "struct_definition": "structDefinition",
            "object_types": "objectTypes",
            "link_types": "linkTypes",
            "action_types": "actionTypes",
            "source_object_type": "sourceObjectType",
            "target_object_type": "targetObjectType",
            "foreign_key_config": "foreignKeyConfig",
            "backing_table": "backingTable",
            "security_config": "securityConfig",
            "backing_dataset": "backingDataset",
            "min_length": "minLength",
            "max_length": "maxLength",
            "min_value": "minValue",
            "max_value": "maxValue",
            "allowed_values": "allowedValues",
            "is_mandatory_control": "isMandatoryControl",
        }

        def convert_keys(obj: Any) -> Any:
            if isinstance(obj, dict):
                new_obj = {}
                for key, value in obj.items():
                    new_key = field_mappings.get(key, key)
                    new_obj[new_key] = convert_keys(value)
                return new_obj
            elif isinstance(obj, list):
                return [convert_keys(item) for item in obj]
            return obj

        return convert_keys(result)


class CompatibilityLayer:
    """
    Compatibility layer for deprecated fields.

    Provides backward-compatible access to deprecated field names.
    """

    # Deprecated field mappings
    DEPRECATED_FIELDS: dict[str, tuple[str, str]] = {
        # (old_name, new_name, deprecation_version)
        "isRequired": ("required", "1.2.0"),
        "isUnique": ("unique", "1.2.0"),
        "minLen": ("minLength", "1.1.0"),
        "maxLen": ("maxLength", "1.1.0"),
    }

    @classmethod
    def normalize_fields(
        cls, data: dict[str, Any], warn: bool = True
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Normalize deprecated field names.

        Args:
            data: Dictionary with potentially deprecated field names.
            warn: Return warnings for deprecated fields.

        Returns:
            Tuple of (normalized_data, warnings).
        """
        result = data.copy()
        warnings: list[str] = []

        for old_name, (new_name, version) in cls.DEPRECATED_FIELDS.items():
            if old_name in result:
                if warn:
                    warnings.append(
                        f"Field '{old_name}' is deprecated since v{version}, "
                        f"use '{new_name}' instead"
                    )
                result[new_name] = result.pop(old_name)

        return result, warnings


# Convenience functions
def detect_version(data: dict[str, Any]) -> str:
    """Detect schema version of JSON data."""
    return MigrationManager().detect_version(data)


def migrate(data: dict[str, Any]) -> MigrationResult:
    """Migrate JSON data to current schema version."""
    return MigrationManager().migrate(data)


def needs_migration(data: dict[str, Any]) -> bool:
    """Check if data needs migration."""
    return MigrationManager().needs_migration(data)
