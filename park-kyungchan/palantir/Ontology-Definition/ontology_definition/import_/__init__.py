"""
Import module - Schema import and migration.

Note: Named 'import_' to avoid conflict with Python's 'import' keyword.

Provides:
    - FoundryImporter: Import from Palantir Foundry JSON format
    - MigrationManager: Version migration utilities
    - CompatibilityLayer: Backward-compatible field name normalization

Example:
    from ontology_definition.import_ import (
        FoundryImporter,
        MigrationManager,
        import_ontology_from_file,
    )

    # Import from file
    importer = FoundryImporter(auto_register=True)
    result = importer.import_ontology_from_file("ontology.json")

    # Check and migrate versions
    manager = MigrationManager()
    if manager.needs_migration(data):
        result = manager.migrate(data)
        data = result.data
"""

from ontology_definition.import_.foundry_importer import (
    FoundryImporter,
    ImportResult,
    ImportError,
    import_object_type,
    import_ontology,
    import_ontology_from_file,
)

from ontology_definition.import_.migration import (
    MigrationManager,
    MigrationResult,
    MigrationStep,
    CompatibilityLayer,
    CURRENT_SCHEMA_VERSION,
    MINIMUM_SUPPORTED_VERSION,
    detect_version,
    migrate,
    needs_migration,
)

__all__ = [
    # Foundry Importer
    "FoundryImporter",
    "ImportResult",
    "ImportError",
    "import_object_type",
    "import_ontology",
    "import_ontology_from_file",
    # Migration
    "MigrationManager",
    "MigrationResult",
    "MigrationStep",
    "CompatibilityLayer",
    "CURRENT_SCHEMA_VERSION",
    "MINIMUM_SUPPORTED_VERSION",
    "detect_version",
    "migrate",
    "needs_migration",
]
