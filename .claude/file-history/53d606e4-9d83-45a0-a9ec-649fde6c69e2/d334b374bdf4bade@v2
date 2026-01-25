"""
Schema Change Detection for Ontology Versioning.

Provides tools for detecting and classifying schema changes as breaking or
non-breaking to ensure safe ontology evolution.

This module provides:
    - ChangeType: BREAKING or NON_BREAKING classification
    - SchemaChange: Individual schema change definition
    - BreakingChangeDetector: Automatic breaking change detection

Reference: docs/Ontology.md Section 11 - Versioning & Governance
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChangeType(str, Enum):
    """
    Classification of schema changes.

    - BREAKING: Changes that require migration or data loss
    - NON_BREAKING: Safe changes that don't affect existing data/edits

    Breaking changes:
    - Changing input datasources
    - Changing primary key
    - Changing property data type
    - Changing property ID (with existing edits)
    - Deleting property (with existing edits)
    - Changing struct field data type

    Non-breaking changes:
    - Display name changes
    - Title key changes
    - Render hints changes
    - Visibility changes
    - Deleting never-edited properties
    """

    BREAKING = "BREAKING"
    NON_BREAKING = "NON_BREAKING"


class SchemaChangeCategory(str, Enum):
    """
    Categories of schema changes.

    - DATASOURCE: Changes to backing datasources
    - PRIMARY_KEY: Changes to primary key definition
    - PROPERTY_TYPE: Changes to property data types
    - PROPERTY_ID: Changes to property identifiers
    - PROPERTY_DELETION: Deletion of properties
    - STRUCT_FIELD: Changes to struct field definitions
    - DISPLAY_METADATA: Changes to display-only metadata
    - SECURITY: Changes to security policies
    """

    DATASOURCE = "DATASOURCE"
    PRIMARY_KEY = "PRIMARY_KEY"
    PROPERTY_TYPE = "PROPERTY_TYPE"
    PROPERTY_ID = "PROPERTY_ID"
    PROPERTY_DELETION = "PROPERTY_DELETION"
    STRUCT_FIELD = "STRUCT_FIELD"
    DISPLAY_METADATA = "DISPLAY_METADATA"
    SECURITY = "SECURITY"


class SchemaChange(BaseModel):
    """
    Individual schema change definition.

    Records a single change to the ontology schema with classification:
    - change_type: BREAKING or NON_BREAKING
    - category: Category of the change
    - object_type: ObjectType apiName affected
    - property_name: Property apiName affected (if applicable)
    - description: Human-readable description
    - requires_migration: Whether migration is required
    - migration_options: Available migration strategies

    Example:
        SchemaChange(
            change_type=ChangeType.BREAKING,
            category=SchemaChangeCategory.PROPERTY_TYPE,
            object_type="Employee",
            property_name="employeeId",
            old_value="INTEGER",
            new_value="STRING",
            description="Changed employeeId from INTEGER to STRING",
            requires_migration=True,
            migration_options=["cast_property_type"]
        )
    """

    change_type: ChangeType = Field(
        ...,
        description="Classification: BREAKING or NON_BREAKING.",
        alias="changeType",
    )

    category: SchemaChangeCategory = Field(
        ...,
        description="Category of this schema change.",
    )

    object_type: str = Field(
        ...,
        description="ObjectType apiName affected by this change.",
        alias="objectType",
    )

    property_name: Optional[str] = Field(
        default=None,
        description="Property apiName affected (if applicable).",
        alias="propertyName",
    )

    old_value: Optional[Any] = Field(
        default=None,
        description="Previous value before change.",
        alias="oldValue",
    )

    new_value: Optional[Any] = Field(
        default=None,
        description="New value after change.",
        alias="newValue",
    )

    description: str = Field(
        ...,
        description="Human-readable description of the change.",
    )

    requires_migration: bool = Field(
        default=False,
        description="Whether this change requires data migration.",
        alias="requiresMigration",
    )

    migration_options: Optional[list[str]] = Field(
        default=None,
        description="Available migration strategies for this change.",
        alias="migrationOptions",
    )

    has_existing_edits: bool = Field(
        default=False,
        description="Whether the affected property has existing user edits.",
        alias="hasExistingEdits",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "changeType": self.change_type.value,
            "category": self.category.value,
            "objectType": self.object_type,
            "description": self.description,
        }

        if self.property_name:
            result["propertyName"] = self.property_name

        if self.old_value is not None:
            result["oldValue"] = self.old_value

        if self.new_value is not None:
            result["newValue"] = self.new_value

        if self.requires_migration:
            result["requiresMigration"] = True

        if self.migration_options:
            result["migrationOptions"] = self.migration_options

        if self.has_existing_edits:
            result["hasExistingEdits"] = True

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "SchemaChange":
        """Create from Foundry JSON format."""
        return cls(
            change_type=ChangeType(data["changeType"]),
            category=SchemaChangeCategory(data["category"]),
            object_type=data["objectType"],
            property_name=data.get("propertyName"),
            old_value=data.get("oldValue"),
            new_value=data.get("newValue"),
            description=data["description"],
            requires_migration=data.get("requiresMigration", False),
            migration_options=data.get("migrationOptions"),
            has_existing_edits=data.get("hasExistingEdits", False),
        )


class BreakingChangeDetector:
    """
    Automatic breaking change detection utility.

    Analyzes schema changes and classifies them as breaking or non-breaking
    based on Foundry rules.

    Breaking change rules:
    1. Changing input datasources → BREAKING
    2. Changing primary key → BREAKING
    3. Changing property data type → BREAKING
    4. Changing property ID (with existing edits) → BREAKING
    5. Deleting property (with existing edits) → BREAKING
    6. Changing struct field data type → BREAKING

    Non-breaking change examples:
    - Display name changes
    - Title key changes
    - Render hints changes
    - Visibility changes
    - Deleting never-edited properties

    Usage:
        detector = BreakingChangeDetector()
        is_breaking = detector.is_breaking_change(
            category=SchemaChangeCategory.PROPERTY_TYPE,
            old_value="STRING",
            new_value="INTEGER"
        )
    """

    # Breaking change rules based on Foundry documentation
    BREAKING_CATEGORIES = {
        SchemaChangeCategory.DATASOURCE,
        SchemaChangeCategory.PRIMARY_KEY,
        SchemaChangeCategory.PROPERTY_TYPE,
        SchemaChangeCategory.STRUCT_FIELD,
    }

    NON_BREAKING_CATEGORIES = {
        SchemaChangeCategory.DISPLAY_METADATA,
    }

    def is_breaking_change(
        self,
        category: SchemaChangeCategory,
        has_existing_edits: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Determine if a schema change is breaking.

        Args:
            category: Category of the change
            has_existing_edits: Whether the property has existing user edits
            **kwargs: Additional context (old_value, new_value, etc.)

        Returns:
            True if the change is breaking, False otherwise
        """
        # Always breaking categories
        if category in self.BREAKING_CATEGORIES:
            return True

        # Never breaking categories
        if category in self.NON_BREAKING_CATEGORIES:
            return False

        # Property ID change is breaking only if there are existing edits
        if category == SchemaChangeCategory.PROPERTY_ID:
            return has_existing_edits

        # Property deletion is breaking only if there are existing edits
        if category == SchemaChangeCategory.PROPERTY_DELETION:
            return has_existing_edits

        # Default: treat unknown changes as non-breaking
        # (conservative approach - let ontology manager decide)
        return False

    def classify_change(
        self,
        category: SchemaChangeCategory,
        object_type: str,
        description: str,
        property_name: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        has_existing_edits: bool = False,
    ) -> SchemaChange:
        """
        Classify a schema change and create SchemaChange object.

        Args:
            category: Category of the change
            object_type: ObjectType apiName
            description: Human-readable description
            property_name: Property apiName (if applicable)
            old_value: Previous value
            new_value: New value
            has_existing_edits: Whether property has existing edits

        Returns:
            SchemaChange object with proper classification
        """
        is_breaking = self.is_breaking_change(
            category=category,
            has_existing_edits=has_existing_edits,
            old_value=old_value,
            new_value=new_value,
        )

        change_type = ChangeType.BREAKING if is_breaking else ChangeType.NON_BREAKING

        # Determine migration options for breaking changes
        migration_options = None
        requires_migration = False

        if is_breaking:
            requires_migration = True
            migration_options = self._get_migration_options(category)

        return SchemaChange(
            change_type=change_type,
            category=category,
            object_type=object_type,
            property_name=property_name,
            old_value=old_value,
            new_value=new_value,
            description=description,
            requires_migration=requires_migration,
            migration_options=migration_options,
            has_existing_edits=has_existing_edits,
        )

    def _get_migration_options(self, category: SchemaChangeCategory) -> list[str]:
        """Get available migration options for a breaking change category."""
        migration_map = {
            SchemaChangeCategory.PROPERTY_TYPE: ["cast_property_type"],
            SchemaChangeCategory.PROPERTY_DELETION: [
                "drop_property_edits",
                "move_edits",
            ],
            SchemaChangeCategory.STRUCT_FIELD: ["drop_struct_field_edits"],
            SchemaChangeCategory.PROPERTY_ID: ["move_edits"],
            SchemaChangeCategory.DATASOURCE: ["drop_all_edits"],
            SchemaChangeCategory.PRIMARY_KEY: ["drop_all_edits"],
        }

        return migration_map.get(category, [])
