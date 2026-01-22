"""
Unit tests for schemas module.

Tests cover:
- SCHEMA_DIR constant
- get_schema_path function
- Schema file existence and validity
"""

import json
from pathlib import Path

import pytest

from ontology_definition.schemas import SCHEMA_DIR, get_schema_path


class TestSchemaDir:
    """Tests for SCHEMA_DIR constant."""

    def test_schema_dir_is_path(self):
        """SCHEMA_DIR should be a Path object."""
        assert isinstance(SCHEMA_DIR, Path)

    def test_schema_dir_exists(self):
        """SCHEMA_DIR should point to an existing directory."""
        assert SCHEMA_DIR.exists()
        assert SCHEMA_DIR.is_dir()

    def test_schema_dir_contains_schema_files(self):
        """SCHEMA_DIR should contain .schema.json files."""
        schema_files = list(SCHEMA_DIR.glob("*.schema.json"))
        assert len(schema_files) > 0


class TestGetSchemaPath:
    """Tests for get_schema_path function."""

    def test_get_schema_path_returns_path(self):
        """get_schema_path should return a Path object."""
        result = get_schema_path("ObjectType")
        assert isinstance(result, Path)

    def test_get_schema_path_format(self):
        """get_schema_path should return correct path format."""
        result = get_schema_path("ObjectType")
        assert result.name == "ObjectType.schema.json"
        assert result.parent == SCHEMA_DIR

    @pytest.mark.parametrize(
        "schema_name",
        [
            "ObjectType",
            "LinkType",
            "ActionType",
            "Property",
            "Metadata",
            "Interaction",
        ],
    )
    def test_get_schema_path_for_known_schemas(self, schema_name):
        """get_schema_path should return existing paths for known schemas."""
        path = get_schema_path(schema_name)
        assert path.exists(), f"Schema file for {schema_name} should exist"

    def test_get_schema_path_nonexistent(self):
        """get_schema_path should return path even for nonexistent schema."""
        path = get_schema_path("NonExistent")
        assert path.name == "NonExistent.schema.json"
        assert not path.exists()


class TestSchemaFileValidity:
    """Tests for schema file validity."""

    @pytest.mark.parametrize(
        "schema_name",
        [
            "ObjectType",
            "LinkType",
            "ActionType",
            "Property",
            "Metadata",
            "Interaction",
        ],
    )
    def test_schema_files_are_valid_json(self, schema_name):
        """Schema files should contain valid JSON."""
        path = get_schema_path(schema_name)
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    @pytest.mark.parametrize(
        "schema_name",
        [
            "ObjectType",
            "LinkType",
            "ActionType",
            "Property",
            "Metadata",
            "Interaction",
        ],
    )
    def test_schema_files_have_schema_key(self, schema_name):
        """Schema files should have $schema key (JSON Schema standard)."""
        path = get_schema_path(schema_name)
        with open(path) as f:
            data = json.load(f)
        assert "$schema" in data, f"{schema_name} should have $schema key"

    @pytest.mark.parametrize(
        "schema_name",
        [
            "ObjectType",
            "LinkType",
            "ActionType",
            "Property",
            "Metadata",
            "Interaction",
        ],
    )
    def test_schema_files_have_type_key(self, schema_name):
        """Schema files should have type key."""
        path = get_schema_path(schema_name)
        with open(path) as f:
            data = json.load(f)
        assert "type" in data, f"{schema_name} should have type key"


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports(self):
        """__all__ should contain expected exports."""
        from ontology_definition import schemas

        assert hasattr(schemas, "__all__")
        assert "SCHEMA_DIR" in schemas.__all__
        assert "get_schema_path" in schemas.__all__

    def test_can_import_from_package(self):
        """Should be able to import from ontology_definition.schemas."""
        from ontology_definition.schemas import SCHEMA_DIR, get_schema_path

        assert SCHEMA_DIR is not None
        assert callable(get_schema_path)
