"""
Unit tests for import functionality - Foundry import and version migration.

Tests cover:
- FoundryImporter: JSON import from Palantir Foundry format
- Auto-registration
- Validation during import
- Error handling
- Bulk import from ontology files
"""

import json
import tempfile
from pathlib import Path

import pytest

from ontology_definition import (
    DataType,
    DataTypeSpec,
    ObjectStatus,
    ObjectType,
    PrimaryKeyDefinition,
    PropertyConstraints,
    PropertyDefinition,
)
from ontology_definition.export import FoundryExporter
from ontology_definition.import_ import (
    FoundryImporter,
    import_object_type,
    import_ontology,
)
from ontology_definition.registry import OntologyRegistry, get_registry


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry before and after each test."""
    OntologyRegistry.reset_instance()
    yield
    OntologyRegistry.reset_instance()


@pytest.fixture
def sample_object_type_json():
    """Create sample Foundry JSON for ObjectType."""
    return {
        "apiName": "Employee",
        "displayName": "Employee",
        "description": "Company employee entity",
        "primaryKey": {"propertyApiName": "employeeId"},
        "properties": [
            {
                "apiName": "employeeId",
                "displayName": "Employee ID",
                "description": "Unique identifier",
                "dataType": {"type": "STRING"},
                "constraints": {"required": True, "unique": True},
            },
            {
                "apiName": "name",
                "displayName": "Name",
                "description": "Full name",
                "dataType": {"type": "STRING"},
                "constraints": {"required": True},
            },
            {
                "apiName": "age",
                "displayName": "Age",
                "dataType": {"type": "INTEGER"},
            },
        ],
        "status": "ACTIVE",
        "endorsed": True,
        "interfaces": ["Auditable"],
    }


@pytest.fixture
def sample_interface_json():
    """Create sample Foundry JSON for Interface."""
    return {
        "apiName": "Auditable",
        "displayName": "Auditable",
        "description": "Interface for auditable entities",
        "properties": [
            {
                "apiName": "createdAt",
                "displayName": "Created At",
                "dataType": {"type": "TIMESTAMP"},
            },
            {
                "apiName": "updatedAt",
                "displayName": "Updated At",
                "dataType": {"type": "TIMESTAMP"},
            },
        ],
    }


class TestFoundryImporterBasic:
    """Basic tests for FoundryImporter."""

    def test_import_object_type_from_dict(self, sample_object_type_json):
        """Import ObjectType from dictionary."""
        importer = FoundryImporter()
        obj = importer.import_object_type(sample_object_type_json)

        assert obj.api_name == "Employee"
        assert obj.display_name == "Employee"
        assert obj.description == "Company employee entity"
        assert len(obj.properties) == 3
        assert obj.status == ObjectStatus.ACTIVE
        assert obj.endorsed is True

    def test_import_object_type_from_json_string(self, sample_object_type_json):
        """Import ObjectType from JSON string."""
        importer = FoundryImporter()
        json_str = json.dumps(sample_object_type_json)
        obj = importer.import_object_type(json_str)

        assert obj.api_name == "Employee"
        assert len(obj.properties) == 3

    def test_import_strips_metadata(self, sample_object_type_json):
        """Import should strip _metadata field."""
        sample_object_type_json["_metadata"] = {
            "exportVersion": "1.0.0",
            "exportTimestamp": "2024-01-01T00:00:00Z",
        }

        importer = FoundryImporter()
        obj = importer.import_object_type(sample_object_type_json)

        # Should succeed without error (metadata stripped)
        assert obj.api_name == "Employee"

    def test_import_preserves_constraints(self, sample_object_type_json):
        """Import should preserve property constraints."""
        importer = FoundryImporter()
        obj = importer.import_object_type(sample_object_type_json)

        employee_id = obj.get_property("employeeId")
        assert employee_id is not None
        assert employee_id.constraints is not None
        assert employee_id.constraints.required is True
        assert employee_id.constraints.unique is True

    def test_import_preserves_interfaces(self, sample_object_type_json):
        """Import should preserve interface list."""
        importer = FoundryImporter()
        obj = importer.import_object_type(sample_object_type_json)

        assert obj.interfaces == ["Auditable"]


class TestFoundryImporterAutoRegister:
    """Tests for auto-registration feature."""

    def test_import_without_auto_register(self, sample_object_type_json):
        """Import without auto-register should not register."""
        importer = FoundryImporter(auto_register=False)
        importer.import_object_type(sample_object_type_json)

        registry = get_registry()
        assert registry.has_object_type("Employee") is False

    def test_import_with_auto_register(self, sample_object_type_json):
        """Import with auto-register should register."""
        importer = FoundryImporter(auto_register=True)
        obj = importer.import_object_type(sample_object_type_json)

        registry = get_registry()
        assert registry.has_object_type("Employee") is True
        assert registry.get_object_type("Employee") is obj

    def test_import_with_register_override(self, sample_object_type_json):
        """Register parameter should override auto_register."""
        importer = FoundryImporter(auto_register=False)
        importer.import_object_type(sample_object_type_json, register=True)

        registry = get_registry()
        assert registry.has_object_type("Employee") is True


class TestFoundryImporterValidation:
    """Tests for validation during import."""

    def test_import_invalid_json_fails(self):
        """Invalid JSON should raise error."""
        importer = FoundryImporter()

        with pytest.raises(json.JSONDecodeError):
            importer.import_object_type("not valid json")

    def test_import_missing_required_field_fails(self):
        """Missing required field should raise error."""
        importer = FoundryImporter()

        invalid_data = {
            "apiName": "Employee",
            # Missing displayName, primaryKey, properties
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            importer.import_object_type(invalid_data)

    def test_import_invalid_primary_key_fails(self):
        """Primary key referencing non-existent property should fail."""
        importer = FoundryImporter()

        invalid_data = {
            "apiName": "Employee",
            "displayName": "Employee",
            "primaryKey": {"propertyApiName": "nonexistent"},
            "properties": [
                {
                    "apiName": "employeeId",
                    "displayName": "Employee ID",
                    "dataType": {"type": "STRING"},
                }
            ],
        }

        with pytest.raises(Exception) as exc_info:
            importer.import_object_type(invalid_data)
        assert "not found in properties" in str(exc_info.value)


class TestFoundryImporterBulkImport:
    """Tests for bulk import operations."""

    def test_import_ontology(self, sample_object_type_json, sample_interface_json):
        """Import complete ontology."""
        ontology_data = {
            "ontology": {
                "objectTypes": [sample_object_type_json],
                "linkTypes": [],
                "actionTypes": [],
                "interfaces": [sample_interface_json],
            }
        }

        importer = FoundryImporter(auto_register=True)
        result = importer.import_ontology(ontology_data)

        assert result.success is True
        assert result.imported_count == 2
        assert "Employee" in result.imported_types["object_types"]
        assert "Auditable" in result.imported_types["interfaces"]

    def test_import_ontology_partial_failure(self, sample_object_type_json):
        """Partial failure should still succeed with strict_mode=False."""
        invalid_type = {
            "apiName": "Invalid",
            "displayName": "Invalid",
            # Missing required fields
        }

        ontology_data = {
            "ontology": {
                "objectTypes": [sample_object_type_json, invalid_type],
                "linkTypes": [],
                "actionTypes": [],
                "interfaces": [],
            }
        }

        importer = FoundryImporter(auto_register=True, strict_mode=False)
        result = importer.import_ontology(ontology_data)

        # Should succeed partially
        assert result.success is True
        assert result.imported_count == 1
        assert len(result.errors) == 1
        assert result.errors[0].api_name == "Invalid"

    def test_import_ontology_strict_failure(self, sample_object_type_json):
        """Strict mode should fail on any error."""
        invalid_type = {
            "apiName": "Invalid",
            "displayName": "Invalid",
        }

        ontology_data = {
            "ontology": {
                "objectTypes": [sample_object_type_json, invalid_type],
            }
        }

        importer = FoundryImporter(auto_register=False, strict_mode=True)
        result = importer.import_ontology(ontology_data)

        # Should fail due to error
        assert result.success is False

    def test_import_result_to_dict(self, sample_object_type_json):
        """ImportResult should be serializable."""
        ontology_data = {"ontology": {"objectTypes": [sample_object_type_json]}}

        importer = FoundryImporter()
        result = importer.import_ontology(ontology_data)
        result_dict = result.to_dict()

        assert "success" in result_dict
        assert "imported_count" in result_dict
        assert "errors" in result_dict
        assert "imported_types" in result_dict


class TestFoundryImporterFileOperations:
    """Tests for file-based import operations."""

    def test_import_object_type_from_file(self, sample_object_type_json):
        """Import ObjectType from file."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump(sample_object_type_json, f)
            path = Path(f.name)

        try:
            importer = FoundryImporter()
            obj = importer.import_object_type_from_file(path)

            assert obj.api_name == "Employee"
        finally:
            path.unlink()

    def test_import_ontology_from_file(self, sample_object_type_json):
        """Import ontology from file."""
        ontology_data = {
            "ontology": {
                "objectTypes": [sample_object_type_json],
                "linkTypes": [],
                "actionTypes": [],
                "interfaces": [],
            }
        }

        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump(ontology_data, f)
            path = Path(f.name)

        try:
            importer = FoundryImporter()
            result = importer.import_ontology_from_file(path)

            assert result.success is True
            assert result.imported_count == 1
        finally:
            path.unlink()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_import_object_type_convenience(self, sample_object_type_json):
        """Test import_object_type convenience function."""
        obj = import_object_type(sample_object_type_json)

        assert obj.api_name == "Employee"

    def test_import_ontology_convenience(self, sample_object_type_json):
        """Test import_ontology convenience function."""
        ontology_data = {
            "ontology": {"objectTypes": [sample_object_type_json]}
        }

        result = import_ontology(ontology_data)

        assert result.success is True
        assert result.imported_count == 1


class TestExportImportRoundtrip:
    """Tests for export -> import roundtrip."""

    def test_object_type_roundtrip(self):
        """Export then import should preserve data."""
        # Create original
        original = ObjectType(
            api_name="Employee",
            display_name="Employee",
            description="Company employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    constraints=PropertyConstraints(required=True, unique=True),
                ),
                PropertyDefinition(
                    api_name="name",
                    display_name="Name",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    constraints=PropertyConstraints(required=True),
                ),
                PropertyDefinition(
                    api_name="salary",
                    display_name="Salary",
                    data_type=DataTypeSpec(type=DataType.DOUBLE),
                ),
            ],
            status=ObjectStatus.ACTIVE,
            endorsed=True,
            interfaces=["Identifiable"],
        )

        # Export
        exporter = FoundryExporter(include_metadata=False)
        json_str = exporter.export_object_type(original)

        # Import
        importer = FoundryImporter()
        restored = importer.import_object_type(json_str)

        # Verify
        assert restored.api_name == original.api_name
        assert restored.display_name == original.display_name
        assert restored.description == original.description
        assert len(restored.properties) == len(original.properties)
        assert restored.status == original.status
        assert restored.endorsed == original.endorsed
        assert restored.interfaces == original.interfaces

        # Verify property details
        orig_emp_id = original.get_property("employeeId")
        rest_emp_id = restored.get_property("employeeId")
        assert orig_emp_id is not None and rest_emp_id is not None
        assert rest_emp_id.constraints.required == orig_emp_id.constraints.required
        assert rest_emp_id.constraints.unique == orig_emp_id.constraints.unique

    def test_registry_roundtrip(self):
        """Export then import entire registry should preserve data."""
        # Create and register types
        registry = get_registry()

        for name in ["Employee", "Department", "Project"]:
            obj = ObjectType(
                api_name=name,
                display_name=name,
                primary_key=PrimaryKeyDefinition(property_api_name="id"),
                properties=[
                    PropertyDefinition(
                        api_name="id",
                        display_name="ID",
                        data_type=DataTypeSpec(type=DataType.STRING),
                    )
                ],
            )
            registry.register_object_type(obj)

        # Export
        exporter = FoundryExporter(include_metadata=False)
        json_str = exporter.export_registry(registry)

        # Reset registry
        OntologyRegistry.reset_instance()
        new_registry = get_registry()
        assert new_registry.stats()["total"] == 0

        # Import
        importer = FoundryImporter(auto_register=True)
        result = importer.import_ontology(json_str)

        # Verify
        assert result.success is True
        assert result.imported_count == 3
        assert new_registry.stats()["object_types"] == 3
        assert new_registry.has_object_type("Employee")
        assert new_registry.has_object_type("Department")
        assert new_registry.has_object_type("Project")
