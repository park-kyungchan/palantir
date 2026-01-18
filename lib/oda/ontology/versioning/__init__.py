"""
Orion ODA v4.0 - ObjectType Versioning
======================================

Provides schema versioning and migration support:
- Schema version tracking (semver)
- Version migration framework (up/down)
- Backward compatibility layer

Reference: Palantir Ontology evolution patterns
"""

from lib.oda.ontology.versioning.schema import (
    SchemaVersion,
    ObjectTypeVersion,
    SchemaVersionRegistry,
    get_schema_version,
    parse_version,
    compare_versions,
)

from lib.oda.ontology.versioning.migrate import (
    Migration,
    MigrationStep,
    MigrationDirection,
    MigrationRegistry,
    MigrationRunner,
    get_migration_registry,
    migration,
)

from lib.oda.ontology.versioning.compat import (
    CompatibilityLayer,
    PropertyMapping,
    TypeCoercion,
    DeprecatedProperty,
    get_compat_layer,
)

__all__ = [
    # Schema
    "SchemaVersion",
    "ObjectTypeVersion",
    "SchemaVersionRegistry",
    "get_schema_version",
    "parse_version",
    "compare_versions",
    # Migration
    "Migration",
    "MigrationStep",
    "MigrationDirection",
    "MigrationRegistry",
    "MigrationRunner",
    "get_migration_registry",
    "migration",
    # Compatibility
    "CompatibilityLayer",
    "PropertyMapping",
    "TypeCoercion",
    "DeprecatedProperty",
    "get_compat_layer",
]
