"""
Orion ODA v4.0 - Schema Version Tracking
========================================

Provides schema version tracking following semantic versioning:
- SchemaVersion: Semver-compliant version representation
- ObjectTypeVersion: Per-ObjectType version tracking
- SchemaVersionRegistry: Central version management

Version Format: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (incompatible schema changes)
- MINOR: Backward-compatible additions
- PATCH: Backward-compatible fixes

Schema Version: 4.0.0
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel, Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# VERSION TYPES
# =============================================================================


class VersionChangeType(str, Enum):
    """Type of schema change."""

    MAJOR = "major"  # Breaking change
    MINOR = "minor"  # Backward-compatible addition
    PATCH = "patch"  # Backward-compatible fix


@dataclass(frozen=True, order=True)
class SchemaVersion:
    """
    Semantic version representation.

    Immutable and comparable.

    Example:
        ```python
        v1 = SchemaVersion(4, 0, 0)
        v2 = SchemaVersion(4, 1, 0)
        assert v1 < v2
        assert str(v1) == "4.0.0"
        ```
    """

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = field(default=None, compare=False)
    build: Optional[str] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version components must be non-negative")

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __repr__(self) -> str:
        return f"SchemaVersion({self.major}, {self.minor}, {self.patch})"

    def bump(self, change_type: VersionChangeType) -> SchemaVersion:
        """Create a new version with the specified component bumped."""
        if change_type == VersionChangeType.MAJOR:
            return SchemaVersion(self.major + 1, 0, 0)
        elif change_type == VersionChangeType.MINOR:
            return SchemaVersion(self.major, self.minor + 1, 0)
        else:
            return SchemaVersion(self.major, self.minor, self.patch + 1)

    def is_compatible_with(self, other: SchemaVersion) -> bool:
        """
        Check if this version is backward-compatible with another.

        Same major version = compatible (minor/patch can differ).
        """
        return self.major == other.major

    def is_breaking_change(self, from_version: SchemaVersion) -> bool:
        """Check if upgrading from from_version to this is a breaking change."""
        return self.major > from_version.major

    @classmethod
    def parse(cls, version_str: str) -> SchemaVersion:
        """
        Parse a version string.

        Supports formats:
        - "4.0.0"
        - "4.0.0-alpha.1"
        - "4.0.0+build.123"
        - "4.0.0-beta.2+build.456"
        """
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$"
        match = re.match(pattern, version_str.strip())

        if not match:
            raise ValueError(f"Invalid version string: {version_str}")

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
            build=match.group(5),
        )

    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to (major, minor, patch) tuple."""
        return (self.major, self.minor, self.patch)


def parse_version(version_str: str) -> SchemaVersion:
    """Parse a version string into a SchemaVersion."""
    return SchemaVersion.parse(version_str)


def compare_versions(v1: Union[str, SchemaVersion], v2: Union[str, SchemaVersion]) -> int:
    """
    Compare two versions.

    Returns:
        -1 if v1 < v2
        0 if v1 == v2
        1 if v1 > v2
    """
    if isinstance(v1, str):
        v1 = parse_version(v1)
    if isinstance(v2, str):
        v2 = parse_version(v2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    return 0


# =============================================================================
# OBJECT TYPE VERSION
# =============================================================================


class ObjectTypeVersion(BaseModel):
    """
    Version information for a specific ObjectType.

    Tracks the schema version and changes for an ObjectType.
    """

    object_type: str = Field(..., description="Name of the ObjectType")
    version: str = Field(..., description="Current version (semver)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    change_log: List[Dict[str, Any]] = Field(default_factory=list)
    deprecated: bool = Field(default=False)
    deprecated_message: Optional[str] = None
    successor_type: Optional[str] = Field(
        default=None,
        description="ObjectType that replaces this one (if deprecated)",
    )

    @property
    def schema_version(self) -> SchemaVersion:
        """Get the SchemaVersion object."""
        return parse_version(self.version)

    def bump_version(
        self,
        change_type: VersionChangeType,
        description: str,
        changed_by: Optional[str] = None,
    ) -> ObjectTypeVersion:
        """
        Create a new version with bumped version number.

        Args:
            change_type: Type of change (major, minor, patch)
            description: Description of the change
            changed_by: ID of the person/agent making the change

        Returns:
            New ObjectTypeVersion with updated version
        """
        current = self.schema_version
        new_version = current.bump(change_type)

        change_entry = {
            "from_version": str(current),
            "to_version": str(new_version),
            "change_type": change_type.value,
            "description": description,
            "changed_by": changed_by,
            "changed_at": datetime.now(timezone.utc).isoformat(),
        }

        return ObjectTypeVersion(
            object_type=self.object_type,
            version=str(new_version),
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            change_log=self.change_log + [change_entry],
            deprecated=self.deprecated,
            deprecated_message=self.deprecated_message,
            successor_type=self.successor_type,
        )

    def deprecate(
        self,
        message: str,
        successor_type: Optional[str] = None,
    ) -> ObjectTypeVersion:
        """Mark this ObjectType as deprecated."""
        return ObjectTypeVersion(
            object_type=self.object_type,
            version=self.version,
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            change_log=self.change_log,
            deprecated=True,
            deprecated_message=message,
            successor_type=successor_type,
        )


# =============================================================================
# SCHEMA VERSION REGISTRY
# =============================================================================


class SchemaVersionRegistry:
    """
    Registry for tracking ObjectType versions.

    Features:
    - Version tracking per ObjectType
    - Version history
    - Compatibility checking
    - Export/import

    Usage:
        ```python
        registry = SchemaVersionRegistry.get_instance()

        # Register a type with version
        registry.register("Task", "4.0.0")

        # Get current version
        version = registry.get_version("Task")

        # Bump version
        registry.bump_version("Task", VersionChangeType.MINOR, "Added priority field")
        ```
    """

    _instance: Optional[SchemaVersionRegistry] = None

    def __init__(self) -> None:
        self._versions: Dict[str, ObjectTypeVersion] = {}
        self._global_version: SchemaVersion = SchemaVersion(4, 0, 0)

    @classmethod
    def get_instance(cls) -> SchemaVersionRegistry:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("SchemaVersionRegistry singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    @property
    def global_version(self) -> SchemaVersion:
        """Get the global schema version."""
        return self._global_version

    def set_global_version(self, version: Union[str, SchemaVersion]) -> None:
        """Set the global schema version."""
        if isinstance(version, str):
            version = parse_version(version)
        self._global_version = version
        logger.info(f"Global schema version set to {version}")

    def register(
        self,
        object_type: str,
        version: str = "1.0.0",
        description: str = "",
    ) -> ObjectTypeVersion:
        """
        Register an ObjectType with a version.

        Args:
            object_type: Name of the ObjectType
            version: Initial version (default: 1.0.0)
            description: Description of the ObjectType

        Returns:
            ObjectTypeVersion instance
        """
        if object_type in self._versions:
            logger.warning(f"ObjectType {object_type} already registered, updating version")

        obj_version = ObjectTypeVersion(
            object_type=object_type,
            version=version,
            change_log=[
                {
                    "from_version": None,
                    "to_version": version,
                    "change_type": "initial",
                    "description": description or f"Initial registration of {object_type}",
                    "changed_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
        )

        self._versions[object_type] = obj_version
        logger.info(f"Registered ObjectType {object_type} at version {version}")

        return obj_version

    def register_from_class(
        self,
        obj_cls: Type[OntologyObject],
        version: str = "1.0.0",
    ) -> ObjectTypeVersion:
        """Register an ObjectType from its class."""
        return self.register(
            object_type=obj_cls.__name__,
            version=version,
            description=(obj_cls.__doc__ or "").strip().split("\n")[0],
        )

    def get_version(self, object_type: str) -> Optional[ObjectTypeVersion]:
        """Get the version info for an ObjectType."""
        return self._versions.get(object_type)

    def get_version_string(self, object_type: str) -> Optional[str]:
        """Get just the version string for an ObjectType."""
        obj_version = self.get_version(object_type)
        return obj_version.version if obj_version else None

    def bump_version(
        self,
        object_type: str,
        change_type: VersionChangeType,
        description: str,
        changed_by: Optional[str] = None,
    ) -> ObjectTypeVersion:
        """
        Bump the version of an ObjectType.

        Args:
            object_type: Name of the ObjectType
            change_type: Type of change
            description: Description of the change
            changed_by: Who made the change

        Returns:
            New ObjectTypeVersion

        Raises:
            ValueError: If ObjectType not registered
        """
        if object_type not in self._versions:
            raise ValueError(f"ObjectType {object_type} not registered")

        current = self._versions[object_type]
        new_version = current.bump_version(change_type, description, changed_by)
        self._versions[object_type] = new_version

        logger.info(
            f"Bumped {object_type} from {current.version} to {new_version.version} "
            f"({change_type.value}): {description}"
        )

        return new_version

    def deprecate(
        self,
        object_type: str,
        message: str,
        successor_type: Optional[str] = None,
    ) -> ObjectTypeVersion:
        """
        Deprecate an ObjectType.

        Args:
            object_type: Name of the ObjectType to deprecate
            message: Deprecation message
            successor_type: Replacement ObjectType (if any)

        Returns:
            Updated ObjectTypeVersion
        """
        if object_type not in self._versions:
            raise ValueError(f"ObjectType {object_type} not registered")

        current = self._versions[object_type]
        deprecated = current.deprecate(message, successor_type)
        self._versions[object_type] = deprecated

        logger.warning(f"Deprecated ObjectType {object_type}: {message}")

        return deprecated

    def list_versions(self) -> Dict[str, str]:
        """List all ObjectTypes and their current versions."""
        return {name: v.version for name, v in self._versions.items()}

    def get_change_log(self, object_type: str) -> List[Dict[str, Any]]:
        """Get the change log for an ObjectType."""
        obj_version = self.get_version(object_type)
        return obj_version.change_log if obj_version else []

    def check_compatibility(
        self,
        object_type: str,
        target_version: Union[str, SchemaVersion],
    ) -> Dict[str, Any]:
        """
        Check compatibility with a target version.

        Args:
            object_type: Name of the ObjectType
            target_version: Version to check compatibility with

        Returns:
            Compatibility info dict
        """
        if isinstance(target_version, str):
            target_version = parse_version(target_version)

        obj_version = self.get_version(object_type)
        if not obj_version:
            return {
                "compatible": False,
                "reason": f"ObjectType {object_type} not registered",
            }

        current = obj_version.schema_version
        compatible = current.is_compatible_with(target_version)
        breaking = current.is_breaking_change(target_version)

        return {
            "compatible": compatible,
            "current_version": str(current),
            "target_version": str(target_version),
            "breaking_change": breaking,
            "deprecated": obj_version.deprecated,
            "deprecated_message": obj_version.deprecated_message,
        }

    def export_json(self, path: Union[str, Path]) -> None:
        """Export version registry to JSON."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "global_version": str(self._global_version),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "object_types": {
                name: v.model_dump(mode="json") for name, v in self._versions.items()
            },
        }

        target.write_text(json.dumps(payload, indent=2, default=str))
        logger.info(f"Exported version registry to {path}")

    def import_json(self, path: Union[str, Path]) -> None:
        """Import version registry from JSON."""
        target = Path(path)
        data = json.loads(target.read_text())

        self._global_version = parse_version(data.get("global_version", "4.0.0"))

        for name, obj_data in data.get("object_types", {}).items():
            self._versions[name] = ObjectTypeVersion(**obj_data)

        logger.info(f"Imported version registry from {path}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_schema_version(object_type: Optional[str] = None) -> Union[SchemaVersion, str, None]:
    """
    Get schema version.

    Args:
        object_type: If provided, get version for specific type.
                     If None, get global version.

    Returns:
        SchemaVersion (global) or version string (per-type) or None
    """
    registry = SchemaVersionRegistry.get_instance()

    if object_type:
        return registry.get_version_string(object_type)
    return registry.global_version
