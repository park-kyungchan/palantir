"""
Migration Support for Ontology Schema Changes.

Provides migration strategies for handling breaking schema changes in a safe,
controlled manner.

This module provides:
    - MigrationType: 6 supported migration types
    - TypeCastMatrix: Allowed type conversions
    - Migration: Individual migration operation definition
    - MigrationBatch: Collection of migrations

Reference: docs/Ontology.md Section 11 - Versioning & Governance
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from ontology_definition.core.enums import DataType


class MigrationType(str, Enum):
    """
    Supported migration types for schema changes.

    6 types aligned with Foundry OSv2 migration framework:
    - DROP_PROPERTY_EDITS: Delete all edits for a specific property
    - DROP_STRUCT_FIELD_EDITS: Delete edits for a struct field
    - DROP_ALL_EDITS: Delete all edits for an ObjectType
    - MOVE_EDITS: Move edits from one property to another
    - CAST_PROPERTY_TYPE: Cast property values to new type
    - REVERT_MIGRATION: Rollback a previous migration

    Limits:
    - Max 500 migrations per batch
    """

    DROP_PROPERTY_EDITS = "drop_property_edits"
    DROP_STRUCT_FIELD_EDITS = "drop_struct_field_edits"
    DROP_ALL_EDITS = "drop_all_edits"
    MOVE_EDITS = "move_edits"
    CAST_PROPERTY_TYPE = "cast_property_type"
    REVERT_MIGRATION = "revert_migration"

    @property
    def is_destructive(self) -> bool:
        """Return True if this migration type deletes data."""
        return self in {
            MigrationType.DROP_PROPERTY_EDITS,
            MigrationType.DROP_STRUCT_FIELD_EDITS,
            MigrationType.DROP_ALL_EDITS,
        }

    @property
    def affects_data_type(self) -> bool:
        """Return True if this migration changes data types."""
        return self == MigrationType.CAST_PROPERTY_TYPE


class TypeCastMatrix:
    """
    Type cast compatibility matrix.

    Defines which type conversions are allowed in Foundry.

    Based on Ontology.md Section 11:
    - String: [Integer, Long, Double, Boolean, Date, Timestamp, Geopoint, Geoshape]
    - Integer: [Long, Double, String]
    - Long: [Integer, Double, String]
    - Double: [Integer, Long, String]

    Usage:
        matrix = TypeCastMatrix()
        can_cast = matrix.can_cast(DataType.STRING, DataType.INTEGER)
        # Returns: True
    """

    # Type cast compatibility rules
    CAST_MATRIX = {
        DataType.STRING: {
            DataType.INTEGER,
            DataType.LONG,
            DataType.DOUBLE,
            DataType.BOOLEAN,
            DataType.DATE,
            DataType.TIMESTAMP,
            DataType.GEOPOINT,
            DataType.GEOSHAPE,
        },
        DataType.INTEGER: {
            DataType.LONG,
            DataType.DOUBLE,
            DataType.STRING,
        },
        DataType.LONG: {
            DataType.INTEGER,
            DataType.DOUBLE,
            DataType.STRING,
        },
        DataType.DOUBLE: {
            DataType.INTEGER,
            DataType.LONG,
            DataType.STRING,
        },
    }

    def can_cast(self, from_type: DataType, to_type: DataType) -> bool:
        """
        Check if a type cast is allowed.

        Args:
            from_type: Source data type
            to_type: Target data type

        Returns:
            True if cast is allowed, False otherwise
        """
        # Same type is always allowed
        if from_type == to_type:
            return True

        # Check matrix
        allowed_targets = self.CAST_MATRIX.get(from_type, set())
        return to_type in allowed_targets

    def get_allowed_casts(self, from_type: DataType) -> list[DataType]:
        """
        Get all allowed target types for a source type.

        Args:
            from_type: Source data type

        Returns:
            List of allowed target types
        """
        allowed = self.CAST_MATRIX.get(from_type, set())
        return sorted(list(allowed), key=lambda t: t.value)

    def is_lossy_cast(self, from_type: DataType, to_type: DataType) -> bool:
        """
        Check if a type cast may lose precision or data.

        Lossy casts:
        - Long → Integer (overflow risk)
        - Double → Integer/Long (precision loss)
        - Any → String (formatting may vary)

        Args:
            from_type: Source data type
            to_type: Target data type

        Returns:
            True if cast may lose data, False otherwise
        """
        lossy_casts = {
            (DataType.LONG, DataType.INTEGER),
            (DataType.DOUBLE, DataType.INTEGER),
            (DataType.DOUBLE, DataType.LONG),
        }

        # Casting to STRING is generally lossy (formatting)
        if to_type == DataType.STRING and from_type != DataType.STRING:
            return True

        return (from_type, to_type) in lossy_casts


class Migration(BaseModel):
    """
    Individual migration operation.

    Defines a single migration action to handle a schema change:
    - migration_type: Type of migration operation
    - object_type: Target ObjectType apiName
    - property_name: Target property apiName (if applicable)
    - source_property: Source property for MOVE_EDITS
    - target_type: Target data type for CAST_PROPERTY_TYPE
    - migration_id: Optional migration ID to revert

    Examples:
        # Drop property edits
        Migration(
            migration_type=MigrationType.DROP_PROPERTY_EDITS,
            object_type="Employee",
            property_name="oldField"
        )

        # Cast property type
        Migration(
            migration_type=MigrationType.CAST_PROPERTY_TYPE,
            object_type="Employee",
            property_name="employeeId",
            source_type=DataType.INTEGER,
            target_type=DataType.STRING
        )

        # Move edits
        Migration(
            migration_type=MigrationType.MOVE_EDITS,
            object_type="Employee",
            source_property="oldName",
            property_name="newName"
        )
    """

    migration_type: MigrationType = Field(
        ...,
        description="Type of migration operation.",
        alias="migrationType",
    )

    object_type: str = Field(
        ...,
        description="Target ObjectType apiName.",
        alias="objectType",
    )

    property_name: Optional[str] = Field(
        default=None,
        description="Target property apiName (for property-level migrations).",
        alias="propertyName",
    )

    source_property: Optional[str] = Field(
        default=None,
        description="Source property apiName (for MOVE_EDITS).",
        alias="sourceProperty",
    )

    source_type: Optional[DataType] = Field(
        default=None,
        description="Source data type (for CAST_PROPERTY_TYPE).",
        alias="sourceType",
    )

    target_type: Optional[DataType] = Field(
        default=None,
        description="Target data type (for CAST_PROPERTY_TYPE).",
        alias="targetType",
    )

    migration_id: Optional[str] = Field(
        default=None,
        description="Migration ID to revert (for REVERT_MIGRATION).",
        alias="migrationId",
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this migration.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def validate_migration(self) -> tuple[bool, Optional[str]]:
        """
        Validate migration configuration.

        Returns:
            (is_valid, error_message) tuple
        """
        # Validate MOVE_EDITS
        if self.migration_type == MigrationType.MOVE_EDITS:
            if not self.source_property or not self.property_name:
                return (
                    False,
                    "MOVE_EDITS requires both source_property and property_name",
                )

        # Validate CAST_PROPERTY_TYPE
        if self.migration_type == MigrationType.CAST_PROPERTY_TYPE:
            if not self.property_name:
                return (False, "CAST_PROPERTY_TYPE requires property_name")

            if not self.source_type or not self.target_type:
                return (
                    False,
                    "CAST_PROPERTY_TYPE requires both source_type and target_type",
                )

            # Check type cast compatibility
            matrix = TypeCastMatrix()
            if not matrix.can_cast(self.source_type, self.target_type):
                return (
                    False,
                    f"Cannot cast from {self.source_type.value} to {self.target_type.value}",
                )

        # Validate REVERT_MIGRATION
        if self.migration_type == MigrationType.REVERT_MIGRATION:
            if not self.migration_id:
                return (False, "REVERT_MIGRATION requires migration_id")

        return (True, None)

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "migrationType": self.migration_type.value,
            "objectType": self.object_type,
        }

        if self.property_name:
            result["propertyName"] = self.property_name

        if self.source_property:
            result["sourceProperty"] = self.source_property

        if self.source_type:
            result["sourceType"] = self.source_type.value

        if self.target_type:
            result["targetType"] = self.target_type.value

        if self.migration_id:
            result["migrationId"] = self.migration_id

        if self.description:
            result["description"] = self.description

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "Migration":
        """Create from Foundry JSON format."""
        source_type = None
        if data.get("sourceType"):
            source_type = DataType(data["sourceType"])

        target_type = None
        if data.get("targetType"):
            target_type = DataType(data["targetType"])

        return cls(
            migration_type=MigrationType(data["migrationType"]),
            object_type=data["objectType"],
            property_name=data.get("propertyName"),
            source_property=data.get("sourceProperty"),
            source_type=source_type,
            target_type=target_type,
            migration_id=data.get("migrationId"),
            description=data.get("description"),
        )


class MigrationBatch(BaseModel):
    """
    Collection of migration operations.

    Groups multiple migrations for atomic execution:
    - migrations: List of migration operations
    - batch_id: Unique identifier for this batch
    - description: Human-readable description

    Limits:
    - Max 500 migrations per batch (Foundry limit)

    Example:
        MigrationBatch(
            batch_id="migration_2024_01_15",
            description="Migrate employee schema v2",
            migrations=[
                Migration(...),
                Migration(...),
            ]
        )
    """

    batch_id: str = Field(
        ...,
        description="Unique identifier for this migration batch.",
        alias="batchId",
    )

    migrations: list[Migration] = Field(
        ...,
        description="List of migration operations.",
        max_length=500,  # Foundry limit
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this migration batch.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def validate_batch(self) -> tuple[bool, list[str]]:
        """
        Validate all migrations in the batch.

        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []

        # Check batch size
        if len(self.migrations) > 500:
            errors.append(
                f"Migration batch exceeds limit: {len(self.migrations)} > 500"
            )

        # Validate each migration
        for i, migration in enumerate(self.migrations):
            is_valid, error = migration.validate_migration()
            if not is_valid:
                errors.append(f"Migration {i}: {error}")

        return (len(errors) == 0, errors)

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "batchId": self.batch_id,
            "migrations": [m.to_foundry_dict() for m in self.migrations],
        }

        if self.description:
            result["description"] = self.description

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "MigrationBatch":
        """Create from Foundry JSON format."""
        return cls(
            batch_id=data["batchId"],
            migrations=[Migration.from_foundry_dict(m) for m in data["migrations"]],
            description=data.get("description"),
        )
