"""
Unit tests for export functionality - Foundry and LLM formats.

Tests cover:
- FoundryExporter: JSON export to Palantir Foundry format
- LLMSchemaExporter: Compact YAML, Markdown, TypeScript exports
- File export operations
- Registry export
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
from ontology_definition.export import (
    FoundryExporter,
    LLMSchemaExporter,
    to_compact_yaml,
    to_markdown,
    to_typescript,
)
from ontology_definition.registry import OntologyRegistry, get_registry


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry before and after each test."""
    OntologyRegistry.reset_instance()
    yield
    OntologyRegistry.reset_instance()


@pytest.fixture
def sample_object_type():
    """Create a sample ObjectType for testing."""
    return ObjectType(
        api_name="Employee",
        display_name="Employee",
        description="Company employee entity",
        primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
        properties=[
            PropertyDefinition(
                api_name="employeeId",
                display_name="Employee ID",
                description="Unique identifier for employees",
                data_type=DataTypeSpec(type=DataType.STRING),
                constraints=PropertyConstraints(required=True, unique=True),
            ),
            PropertyDefinition(
                api_name="name",
                display_name="Name",
                description="Full name of the employee",
                data_type=DataTypeSpec(type=DataType.STRING),
                constraints=PropertyConstraints(required=True),
            ),
            PropertyDefinition(
                api_name="email",
                display_name="Email",
                description="Work email address",
                data_type=DataTypeSpec(type=DataType.STRING),
            ),
            PropertyDefinition(
                api_name="age",
                display_name="Age",
                description="Age in years",
                data_type=DataTypeSpec(type=DataType.INTEGER),
            ),
            PropertyDefinition(
                api_name="isActive",
                display_name="Is Active",
                description="Whether the employee is currently active",
                data_type=DataTypeSpec(type=DataType.BOOLEAN),
            ),
        ],
        status=ObjectStatus.ACTIVE,
        endorsed=True,
        interfaces=["Auditable", "Identifiable"],
    )


class TestFoundryExporter:
    """Tests for FoundryExporter - JSON export."""

    def test_export_object_type_json_string(self, sample_object_type):
        """Export ObjectType to JSON string."""
        exporter = FoundryExporter()
        result = exporter.export_object_type(sample_object_type)

        # Should be valid JSON
        data = json.loads(result)
        assert data["apiName"] == "Employee"
        assert data["displayName"] == "Employee"
        assert data["description"] == "Company employee entity"
        assert data["primaryKey"]["propertyApiName"] == "employeeId"
        assert len(data["properties"]) == 5

    def test_export_object_type_as_dict(self, sample_object_type):
        """Export ObjectType as dictionary."""
        exporter = FoundryExporter()
        result = exporter.export_object_type(sample_object_type, as_dict=True)

        assert isinstance(result, dict)
        assert result["apiName"] == "Employee"

    def test_export_includes_metadata(self, sample_object_type):
        """Export should include metadata when enabled."""
        exporter = FoundryExporter(include_metadata=True)
        result = exporter.export_object_type(sample_object_type, as_dict=True)

        assert "_metadata" in result
        assert "exportVersion" in result["_metadata"]
        assert "exportTimestamp" in result["_metadata"]
        assert "sourcePackage" in result["_metadata"]
        assert result["_metadata"]["sourcePackage"] == "ontology_definition"

    def test_export_without_metadata(self, sample_object_type):
        """Export without metadata when disabled."""
        exporter = FoundryExporter(include_metadata=False)
        result = exporter.export_object_type(sample_object_type, as_dict=True)

        assert "_metadata" not in result

    def test_export_pretty_print(self, sample_object_type):
        """Pretty printed JSON should have newlines and indentation."""
        exporter = FoundryExporter(pretty_print=True, indent=2)
        result = exporter.export_object_type(sample_object_type)

        # Pretty printed should have newlines
        assert "\n" in result
        assert "  " in result  # Indentation

    def test_export_compact(self, sample_object_type):
        """Compact JSON should not have newlines."""
        exporter = FoundryExporter(pretty_print=False)
        result = exporter.export_object_type(sample_object_type)

        # Compact should be single line (no newlines except in strings)
        lines = result.split("\n")
        assert len(lines) == 1

    def test_export_preserves_status_and_endorsed(self, sample_object_type):
        """Export should preserve status and endorsed flags."""
        exporter = FoundryExporter()
        result = exporter.export_object_type(sample_object_type, as_dict=True)

        assert result["status"] == "ACTIVE"
        assert result["endorsed"] is True

    def test_export_preserves_interfaces(self, sample_object_type):
        """Export should preserve interface list."""
        exporter = FoundryExporter()
        result = exporter.export_object_type(sample_object_type, as_dict=True)

        assert "interfaces" in result
        assert set(result["interfaces"]) == {"Auditable", "Identifiable"}

    def test_export_preserves_constraints(self, sample_object_type):
        """Export should preserve property constraints."""
        exporter = FoundryExporter()
        result = exporter.export_object_type(sample_object_type, as_dict=True)

        # Find employeeId property
        employee_id_prop = next(
            p for p in result["properties"] if p["apiName"] == "employeeId"
        )
        assert employee_id_prop["constraints"]["required"] is True
        assert employee_id_prop["constraints"]["unique"] is True

    def test_export_registry(self, sample_object_type):
        """Export entire registry."""
        registry = get_registry()
        registry.register_object_type(sample_object_type)

        exporter = FoundryExporter()
        result = exporter.export_registry(registry, as_dict=True)

        assert "ontology" in result
        assert "statistics" in result
        assert len(result["ontology"]["objectTypes"]) == 1
        assert result["statistics"]["object_types"] == 1

    def test_export_to_file(self, sample_object_type):
        """Export to file."""
        exporter = FoundryExporter()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            result_path = exporter.export_to_file(sample_object_type, path)
            assert result_path == path
            assert path.exists()

            # Verify content
            content = path.read_text()
            data = json.loads(content)
            assert data["apiName"] == "Employee"
        finally:
            path.unlink()


class TestLLMSchemaExporter:
    """Tests for LLMSchemaExporter - LLM-friendly formats."""

    def test_to_compact_yaml_basic(self, sample_object_type):
        """Generate compact YAML representation."""
        exporter = LLMSchemaExporter()
        result = exporter.to_compact_yaml(sample_object_type)

        # Should include key elements
        assert "# Employee" in result
        assert "pk: employeeId" in result
        assert "properties:" in result
        assert "employeeId:" in result
        assert "name:" in result

    def test_to_compact_yaml_includes_interfaces(self, sample_object_type):
        """Compact YAML should include implements clause."""
        exporter = LLMSchemaExporter()
        result = exporter.to_compact_yaml(sample_object_type)

        assert "implements:" in result
        assert "Auditable" in result
        assert "Identifiable" in result

    def test_to_compact_yaml_includes_flags(self, sample_object_type):
        """Compact YAML should include property flags."""
        exporter = LLMSchemaExporter()
        result = exporter.to_compact_yaml(sample_object_type)

        # employeeId should have required and unique flags
        assert "required" in result
        assert "unique" in result

    def test_to_compact_yaml_with_descriptions(self, sample_object_type):
        """Compact YAML should include descriptions when enabled."""
        exporter = LLMSchemaExporter(include_descriptions=True)
        result = exporter.to_compact_yaml(sample_object_type)

        # Should have description comments
        assert "# Company employee entity" in result or "employee entity" in result

    def test_to_compact_yaml_without_descriptions(self, sample_object_type):
        """Compact YAML should exclude descriptions when disabled."""
        exporter = LLMSchemaExporter(include_descriptions=False)
        result = exporter.to_compact_yaml(sample_object_type)

        # Should not have property descriptions (only header comments)
        lines = result.split("\n")
        property_lines = [line for line in lines if line.strip().startswith("employeeId:")]
        for line in property_lines:
            assert "#" not in line or line.startswith("#")

    def test_to_markdown(self, sample_object_type):
        """Generate Markdown documentation."""
        exporter = LLMSchemaExporter()
        result = exporter.to_markdown(sample_object_type)

        # Should include Markdown elements
        assert "## Employee" in result
        assert "**API Name:**" in result
        assert "`Employee`" in result
        assert "| Name | Type | Required | Description |" in result
        assert "`employeeId`" in result

    def test_to_markdown_includes_status(self, sample_object_type):
        """Markdown should include status and endorsement."""
        exporter = LLMSchemaExporter()
        result = exporter.to_markdown(sample_object_type)

        assert "**Status:**" in result
        assert "ACTIVE" in result
        assert "Endorsed" in result

    def test_to_markdown_table_structure(self, sample_object_type):
        """Markdown table should have correct structure."""
        exporter = LLMSchemaExporter()
        result = exporter.to_markdown(sample_object_type)

        # Check table rows
        assert "| `employeeId` |" in result
        assert "| `name` |" in result

    def test_to_typescript_types(self, sample_object_type):
        """Generate TypeScript interface definition."""
        exporter = LLMSchemaExporter()
        result = exporter.to_typescript_types(sample_object_type)

        # Should be valid TypeScript interface
        assert "interface Employee {" in result
        assert "employeeId: string;" in result
        assert "name: string;" in result
        assert "age?: number;" in result  # Optional (no required constraint)
        assert "}" in result

    def test_to_typescript_optional_properties(self, sample_object_type):
        """TypeScript should mark optional properties with ?."""
        exporter = LLMSchemaExporter()
        result = exporter.to_typescript_types(sample_object_type)

        # Required properties should not have ?
        assert "employeeId: string;" in result  # required
        assert "name: string;" in result  # required

        # Optional properties should have ?
        assert "email?: string;" in result  # not required
        assert "age?: number;" in result  # not required

    def test_to_typescript_includes_jsdoc(self, sample_object_type):
        """TypeScript should include JSDoc comments."""
        exporter = LLMSchemaExporter(include_descriptions=True)
        result = exporter.to_typescript_types(sample_object_type)

        assert "/**" in result
        assert "*/" in result
        assert "Company employee entity" in result

    def test_to_natural_language(self, sample_object_type):
        """Generate natural language description."""
        exporter = LLMSchemaExporter()
        result = exporter.to_natural_language(sample_object_type)

        # Should be readable text
        assert "Employee" in result
        assert "identified by employeeId" in result
        assert "Required fields:" in result
        assert "Optional fields:" in result

    def test_convenience_functions(self, sample_object_type):
        """Test convenience functions."""
        compact = to_compact_yaml(sample_object_type)
        assert "# Employee" in compact

        md = to_markdown(sample_object_type)
        assert "## Employee" in md

        ts = to_typescript(sample_object_type)
        assert "interface Employee" in ts


class TestLLMExporterTypeMapping:
    """Tests for type mapping in LLM exporter."""

    def test_string_type(self):
        """STRING maps to string."""
        obj = ObjectType(
            api_name="Test",
            display_name="Test",
            primary_key=PrimaryKeyDefinition(property_api_name="id"),
            properties=[
                PropertyDefinition(
                    api_name="id",
                    display_name="ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                )
            ],
        )
        exporter = LLMSchemaExporter()
        result = exporter.to_typescript_types(obj)
        assert "id: string;" in result or "id?: string;" in result

    def test_integer_type(self):
        """INTEGER maps to number."""
        obj = ObjectType(
            api_name="Test",
            display_name="Test",
            primary_key=PrimaryKeyDefinition(property_api_name="id"),
            properties=[
                PropertyDefinition(
                    api_name="id",
                    display_name="ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
                PropertyDefinition(
                    api_name="count",
                    display_name="Count",
                    data_type=DataTypeSpec(type=DataType.INTEGER),
                ),
            ],
        )
        exporter = LLMSchemaExporter()
        result = exporter.to_typescript_types(obj)
        assert "count?: number;" in result

    def test_boolean_type(self):
        """BOOLEAN maps to boolean."""
        obj = ObjectType(
            api_name="Test",
            display_name="Test",
            primary_key=PrimaryKeyDefinition(property_api_name="id"),
            properties=[
                PropertyDefinition(
                    api_name="id",
                    display_name="ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
                PropertyDefinition(
                    api_name="active",
                    display_name="Active",
                    data_type=DataTypeSpec(type=DataType.BOOLEAN),
                ),
            ],
        )
        exporter = LLMSchemaExporter()
        result = exporter.to_typescript_types(obj)
        assert "active?: boolean;" in result

    def test_timestamp_type(self):
        """TIMESTAMP maps to string."""
        obj = ObjectType(
            api_name="Test",
            display_name="Test",
            primary_key=PrimaryKeyDefinition(property_api_name="id"),
            properties=[
                PropertyDefinition(
                    api_name="id",
                    display_name="ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
                PropertyDefinition(
                    api_name="createdAt",
                    display_name="Created At",
                    data_type=DataTypeSpec(type=DataType.TIMESTAMP),
                ),
            ],
        )
        exporter = LLMSchemaExporter()
        result = exporter.to_typescript_types(obj)
        assert "createdAt?: string;" in result


class TestExportRoundtrip:
    """Tests for export-import roundtrip consistency."""

    def test_foundry_export_import_roundtrip(self, sample_object_type):
        """Foundry export should be importable back."""
        exporter = FoundryExporter(include_metadata=False)
        json_str = exporter.export_object_type(sample_object_type)

        # Parse JSON
        data = json.loads(json_str)

        # Restore ObjectType
        restored = ObjectType.from_foundry_dict(data)

        # Verify key fields match
        assert restored.api_name == sample_object_type.api_name
        assert restored.display_name == sample_object_type.display_name
        assert restored.description == sample_object_type.description
        assert len(restored.properties) == len(sample_object_type.properties)
        assert restored.status == sample_object_type.status
        assert restored.endorsed == sample_object_type.endorsed
        assert set(restored.interfaces) == set(sample_object_type.interfaces)


class TestRegistryExport:
    """Tests for registry-wide export."""

    def test_export_multiple_types(self):
        """Export registry with multiple types."""
        registry = get_registry()

        # Register multiple ObjectTypes
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
        exporter = FoundryExporter()
        result = exporter.export_registry(registry, as_dict=True)

        assert len(result["ontology"]["objectTypes"]) == 3
        assert result["statistics"]["object_types"] == 3

    def test_llm_export_all_compact(self):
        """Export all ObjectTypes in compact format."""
        registry = get_registry()

        for name in ["Employee", "Department"]:
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

        exporter = LLMSchemaExporter()
        result = exporter.export_all_compact(registry)

        assert "# Employee" in result
        assert "# Department" in result
        assert "---" in result  # Separator

    def test_llm_export_all_typescript(self):
        """Export all ObjectTypes as TypeScript."""
        registry = get_registry()

        for name in ["Employee", "Department"]:
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

        exporter = LLMSchemaExporter()
        result = exporter.export_all_typescript(registry)

        assert "interface Employee {" in result
        assert "interface Department {" in result
