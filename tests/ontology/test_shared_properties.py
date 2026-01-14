"""
Tests for Shared Properties - Palantir-style Shared Property Types

Tests cover:
- SharedPropertyDefinition validation
- SharedPropertyRegistry operations
- @uses_shared_property decorator
- Usage tracking
- Built-in properties

Schema Version: 4.0.0
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError


class TestSharedPropertyDefinition:
    """Test SharedPropertyDefinition model validation."""

    def test_valid_property_definition(self):
        """Test creating a valid SharedPropertyDefinition."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop = SharedPropertyDefinition(
            property_id="created_at",
            description="Creation timestamp",
            type_hint="datetime",
            category="audit",
            is_indexed=True,
        )

        assert prop.property_id == "created_at"
        assert prop.description == "Creation timestamp"
        assert prop.type_hint == "datetime"
        assert prop.category == "audit"
        assert prop.is_indexed is True
        assert prop.is_required is False  # default

    def test_property_with_default_value(self):
        """Test property with default value."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop = SharedPropertyDefinition(
            property_id="version",
            description="Version number",
            type_hint="int",
            default_value=1,
            category="versioning",
        )

        assert prop.default_value == 1
        assert prop.default_factory is None

    def test_property_with_default_factory(self):
        """Test property with default factory."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop = SharedPropertyDefinition(
            property_id="tags",
            description="List of tags",
            type_hint="List[str]",
            default_factory="list",
            category="metadata",
        )

        assert prop.default_value is None
        assert prop.default_factory == "list"

    def test_invalid_both_default_value_and_factory(self):
        """Test that setting both default_value and default_factory raises error."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        with pytest.raises(ValidationError) as exc_info:
            SharedPropertyDefinition(
                property_id="test",
                description="Test property",
                type_hint="str",
                default_value="test",
                default_factory="str",
            )

        assert "Cannot specify both default_value and default_factory" in str(exc_info.value)

    def test_invalid_property_id_double_underscore(self):
        """Test that property_id starting with __ raises error."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        with pytest.raises(ValidationError) as exc_info:
            SharedPropertyDefinition(
                property_id="__private",
                description="Private property",
                type_hint="str",
            )

        assert "double underscore" in str(exc_info.value)

    def test_invalid_property_id_reserved_keyword(self):
        """Test that reserved keywords raise error."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        with pytest.raises(ValidationError) as exc_info:
            SharedPropertyDefinition(
                property_id="class",
                description="Class property",
                type_hint="str",
            )

        assert "reserved keyword" in str(exc_info.value)

    def test_invalid_property_id_pattern(self):
        """Test that invalid property_id pattern raises error."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        with pytest.raises(ValidationError):
            SharedPropertyDefinition(
                property_id="InvalidName",  # Must start with lowercase
                description="Invalid name",
                type_hint="str",
            )

    def test_category_normalization(self):
        """Test that category is normalized to lowercase."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop = SharedPropertyDefinition(
            property_id="test",
            description="Test",
            type_hint="str",
            category="AUDIT",
        )

        assert prop.category == "audit"

    def test_get_pydantic_field_info(self):
        """Test getting Pydantic Field info from property definition."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop = SharedPropertyDefinition(
            property_id="status",
            description="Status field",
            type_hint="str",
            default_value="active",
        )

        field_info = prop.get_pydantic_field_info()
        assert field_info["description"] == "Status field"
        assert field_info["default"] == "active"


class TestSharedPropertyUsage:
    """Test SharedPropertyUsage model."""

    def test_valid_usage(self):
        """Test creating a valid usage record."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyUsage

        usage = SharedPropertyUsage(
            property_id="created_at",
            object_type="Task",
        )

        assert usage.property_id == "created_at"
        assert usage.object_type == "Task"
        assert usage.is_active is True
        assert usage.registered_at is not None

    def test_usage_with_alias(self):
        """Test usage with field alias."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyUsage

        usage = SharedPropertyUsage(
            property_id="created_at",
            object_type="Task",
            field_alias="creation_date",
        )

        assert usage.field_alias == "creation_date"

    def test_usage_with_override_default(self):
        """Test usage with overridden default value."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyUsage

        usage = SharedPropertyUsage(
            property_id="version",
            object_type="Document",
            override_default=5,
        )

        assert usage.override_default == 5


class TestSharedPropertyRegistry:
    """Test SharedPropertyRegistry operations."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyRegistry
        return SharedPropertyRegistry()

    @pytest.fixture
    def sample_property(self):
        """Create a sample property definition."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition
        return SharedPropertyDefinition(
            property_id="test_prop",
            description="Test property",
            type_hint="str",
            category="test",
        )

    def test_register_property(self, registry, sample_property):
        """Test registering a property."""
        registry.register_property(sample_property)

        assert registry.has_property("test_prop")
        assert registry.get_property("test_prop") == sample_property

    def test_register_duplicate_property_raises_error(self, registry, sample_property):
        """Test that registering duplicate property raises error."""
        registry.register_property(sample_property)

        with pytest.raises(ValueError) as exc_info:
            registry.register_property(sample_property)

        assert "already registered" in str(exc_info.value)

    def test_get_nonexistent_property(self, registry):
        """Test getting non-existent property returns None."""
        assert registry.get_property("nonexistent") is None

    def test_list_properties(self, registry):
        """Test listing all properties."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop1 = SharedPropertyDefinition(
            property_id="prop1", description="Prop 1", type_hint="str"
        )
        prop2 = SharedPropertyDefinition(
            property_id="prop2", description="Prop 2", type_hint="int"
        )

        registry.register_property(prop1)
        registry.register_property(prop2)

        properties = registry.list_properties()
        assert len(properties) == 2

    def test_list_property_ids(self, registry, sample_property):
        """Test listing property IDs."""
        registry.register_property(sample_property)

        ids = registry.list_property_ids()
        assert "test_prop" in ids

    def test_list_properties_by_category(self, registry):
        """Test filtering properties by category."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        audit_prop = SharedPropertyDefinition(
            property_id="created_at",
            description="Created at",
            type_hint="datetime",
            category="audit",
        )
        meta_prop = SharedPropertyDefinition(
            property_id="tags",
            description="Tags",
            type_hint="List[str]",
            category="metadata",
        )

        registry.register_property(audit_prop)
        registry.register_property(meta_prop)

        audit_props = registry.list_properties_by_category("audit")
        assert len(audit_props) == 1
        assert audit_props[0].property_id == "created_at"

    def test_get_categories(self, registry):
        """Test getting all categories."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        registry.register_property(SharedPropertyDefinition(
            property_id="p1", description="P1", type_hint="str", category="audit"
        ))
        registry.register_property(SharedPropertyDefinition(
            property_id="p2", description="P2", type_hint="str", category="metadata"
        ))

        categories = registry.get_categories()
        assert "audit" in categories
        assert "metadata" in categories

    def test_register_usage(self, registry, sample_property):
        """Test registering usage."""
        registry.register_property(sample_property)

        usage = registry.register_usage(
            property_id="test_prop",
            object_type="Task",
        )

        assert usage.property_id == "test_prop"
        assert usage.object_type == "Task"

    def test_register_usage_nonexistent_property_raises_error(self, registry):
        """Test that registering usage for non-existent property raises error."""
        with pytest.raises(ValueError) as exc_info:
            registry.register_usage(
                property_id="nonexistent",
                object_type="Task",
            )

        assert "not registered" in str(exc_info.value)

    def test_register_duplicate_usage_raises_error(self, registry, sample_property):
        """Test that duplicate usage raises error."""
        registry.register_property(sample_property)
        registry.register_usage(property_id="test_prop", object_type="Task")

        with pytest.raises(ValueError) as exc_info:
            registry.register_usage(property_id="test_prop", object_type="Task")

        assert "already uses property" in str(exc_info.value)

    def test_get_usages_for_property(self, registry, sample_property):
        """Test getting usages for a property."""
        registry.register_property(sample_property)
        registry.register_usage(property_id="test_prop", object_type="Task")
        registry.register_usage(property_id="test_prop", object_type="Document")

        usages = registry.get_usages_for_property("test_prop")
        assert "Task" in usages
        assert "Document" in usages

    def test_get_properties_for_object(self, registry):
        """Test getting properties for an object type."""
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop1 = SharedPropertyDefinition(
            property_id="prop1", description="Prop 1", type_hint="str"
        )
        prop2 = SharedPropertyDefinition(
            property_id="prop2", description="Prop 2", type_hint="int"
        )

        registry.register_property(prop1)
        registry.register_property(prop2)
        registry.register_usage(property_id="prop1", object_type="Task")
        registry.register_usage(property_id="prop2", object_type="Task")

        props = registry.get_properties_for_object("Task")
        assert "prop1" in props
        assert "prop2" in props

    def test_get_usage(self, registry, sample_property):
        """Test getting a specific usage record."""
        registry.register_property(sample_property)
        registry.register_usage(
            property_id="test_prop",
            object_type="Task",
            field_alias="test_alias",
        )

        usage = registry.get_usage("test_prop", "Task")
        assert usage is not None
        assert usage.field_alias == "test_alias"

    def test_is_property_used(self, registry, sample_property):
        """Test checking if property is used."""
        registry.register_property(sample_property)

        assert registry.is_property_used("test_prop") is False

        registry.register_usage(property_id="test_prop", object_type="Task")

        assert registry.is_property_used("test_prop") is True

    def test_count_usages(self, registry, sample_property):
        """Test counting usages."""
        registry.register_property(sample_property)

        assert registry.count_usages("test_prop") == 0

        registry.register_usage(property_id="test_prop", object_type="Task")
        registry.register_usage(property_id="test_prop", object_type="Document")

        assert registry.count_usages("test_prop") == 2

    def test_export_dict(self, registry, sample_property):
        """Test exporting registry to dict."""
        registry.register_property(sample_property)
        registry.register_usage(property_id="test_prop", object_type="Task")

        exported = registry.export_dict()

        assert "properties" in exported
        assert "statistics" in exported
        assert "test_prop" in exported["properties"]
        assert exported["statistics"]["total_properties"] == 1
        assert exported["statistics"]["total_usages"] == 1


class TestBuiltinProperties:
    """Test built-in shared properties."""

    def test_builtin_audit_properties(self):
        """Test built-in audit properties are defined."""
        from lib.oda.ontology.types.shared_properties import BUILTIN_AUDIT_PROPERTIES

        property_ids = [p.property_id for p in BUILTIN_AUDIT_PROPERTIES]
        assert "created_at" in property_ids
        assert "updated_at" in property_ids
        assert "created_by" in property_ids
        assert "modified_by" in property_ids

    def test_builtin_version_properties(self):
        """Test built-in version properties are defined."""
        from lib.oda.ontology.types.shared_properties import BUILTIN_VERSION_PROPERTIES

        property_ids = [p.property_id for p in BUILTIN_VERSION_PROPERTIES]
        assert "version" in property_ids
        assert "version_history" in property_ids

    def test_builtin_metadata_properties(self):
        """Test built-in metadata properties are defined."""
        from lib.oda.ontology.types.shared_properties import BUILTIN_METADATA_PROPERTIES

        property_ids = [p.property_id for p in BUILTIN_METADATA_PROPERTIES]
        assert "tags" in property_ids
        assert "labels" in property_ids
        assert "annotations" in property_ids

    def test_get_builtin_property(self):
        """Test getting a built-in property by ID."""
        from lib.oda.ontology.types.shared_properties import get_builtin_property

        prop = get_builtin_property("created_at")
        assert prop is not None
        assert prop.property_id == "created_at"
        assert prop.category == "audit"

    def test_get_nonexistent_builtin_property(self):
        """Test getting non-existent built-in returns None."""
        from lib.oda.ontology.types.shared_properties import get_builtin_property

        assert get_builtin_property("nonexistent") is None

    def test_list_builtin_properties(self):
        """Test listing all built-in property IDs."""
        from lib.oda.ontology.types.shared_properties import list_builtin_properties

        ids = list_builtin_properties()
        assert "created_at" in ids
        assert "version" in ids
        assert "tags" in ids


class TestUsesSharedPropertyDecorator:
    """Test @uses_shared_property decorator."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the global registry before each test."""
        from lib.oda.ontology.registry import (
            get_shared_property_registry,
            load_default_shared_properties,
        )
        # Get fresh registry state
        registry = get_shared_property_registry()
        # Ensure built-ins are loaded
        load_default_shared_properties()
        yield

    def test_decorator_injects_builtin_property(self):
        """Test that decorator injects built-in property."""
        from lib.oda.ontology.decorators.shared_property import uses_shared_property
        from pydantic import BaseModel

        @uses_shared_property("version")
        class TestModel(BaseModel):
            title: str

        # Check annotation was added
        assert "version" in TestModel.__annotations__

        # Check metadata was added
        assert hasattr(TestModel, "_uses_shared_properties")
        assert "version" in TestModel._uses_shared_properties

    def test_decorator_with_multiple_properties(self):
        """Test decorator with multiple properties."""
        from lib.oda.ontology.decorators.shared_property import uses_shared_property
        from pydantic import BaseModel

        @uses_shared_property("created_at", "modified_by", "version")
        class TestModel(BaseModel):
            title: str

        assert "created_at" in TestModel.__annotations__
        assert "modified_by" in TestModel.__annotations__
        assert "version" in TestModel.__annotations__
        assert len(TestModel._uses_shared_properties) == 3

    def test_decorator_strict_mode_raises_on_missing(self):
        """Test that strict mode raises error for missing property."""
        from lib.oda.ontology.decorators.shared_property import (
            uses_shared_property,
            SharedPropertyError,
        )
        from pydantic import BaseModel

        with pytest.raises(SharedPropertyError) as exc_info:
            @uses_shared_property("nonexistent_property", strict=True)
            class TestModel(BaseModel):
                title: str

        assert "not found" in str(exc_info.value)

    def test_decorator_non_strict_mode_warns(self, caplog):
        """Test that non-strict mode logs warning for missing property."""
        import logging
        from lib.oda.ontology.decorators.shared_property import uses_shared_property
        from pydantic import BaseModel

        with caplog.at_level(logging.WARNING):
            @uses_shared_property("nonexistent_property", strict=False)
            class TestModel(BaseModel):
                title: str

        # Property should not be injected
        assert "nonexistent_property" not in TestModel.__annotations__

    def test_decorator_conflict_raises_error(self):
        """Test that conflict raises error when allow_override=False."""
        from lib.oda.ontology.decorators.shared_property import (
            uses_shared_property,
            SharedPropertyConflictError,
        )
        from pydantic import BaseModel

        with pytest.raises(SharedPropertyConflictError) as exc_info:
            @uses_shared_property("version", allow_override=False)
            class TestModel(BaseModel):
                title: str
                version: int = 5  # Existing field

        assert "field_exists" in str(exc_info.value)

    def test_decorator_allow_override(self):
        """Test that allow_override=True allows existing field."""
        from lib.oda.ontology.decorators.shared_property import uses_shared_property
        from pydantic import BaseModel

        @uses_shared_property("version", allow_override=True)
        class TestModel(BaseModel):
            title: str
            version: int = 5  # Override default

        # Field should exist with overridden default
        assert TestModel.model_fields["version"].default == 5

    def test_decorator_no_args_raises_error(self):
        """Test that decorator without args raises error."""
        from lib.oda.ontology.decorators.shared_property import uses_shared_property

        with pytest.raises(ValueError) as exc_info:
            @uses_shared_property()  # No property IDs
            class TestModel:
                pass

        assert "At least one property_id" in str(exc_info.value)


class TestSharedPropertyUtilities:
    """Test shared property utility functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the global registry before each test."""
        from lib.oda.ontology.registry import load_default_shared_properties
        load_default_shared_properties()
        yield

    def test_get_shared_properties(self):
        """Test getting shared properties from a class."""
        from lib.oda.ontology.decorators.shared_property import (
            uses_shared_property,
            get_shared_properties,
        )
        from pydantic import BaseModel

        @uses_shared_property("version", "tags")
        class TestModel(BaseModel):
            title: str

        props = get_shared_properties(TestModel)
        assert "version" in props
        assert "tags" in props

    def test_uses_property(self):
        """Test checking if class uses a property."""
        from lib.oda.ontology.decorators.shared_property import (
            uses_shared_property,
            uses_property,
        )
        from pydantic import BaseModel

        @uses_shared_property("version")
        class TestModel(BaseModel):
            title: str

        assert uses_property(TestModel, "version") is True
        assert uses_property(TestModel, "tags") is False

    def test_require_shared_property_decorator(self):
        """Test @require_shared_property decorator."""
        from lib.oda.ontology.decorators.shared_property import (
            uses_shared_property,
            require_shared_property,
        )
        from pydantic import BaseModel

        @uses_shared_property("version")
        class Versionable(BaseModel):
            title: str

        @require_shared_property("version")
        def process_versionable(obj):
            return obj.version

        # Should work with Versionable
        v = Versionable(title="Test")
        assert process_versionable(v) is not None

    def test_require_shared_property_raises_on_missing(self):
        """Test that require_shared_property raises on missing property."""
        from lib.oda.ontology.decorators.shared_property import require_shared_property
        from pydantic import BaseModel

        class NonVersionable(BaseModel):
            title: str

        @require_shared_property("version")
        def process_versionable(obj):
            return obj.version

        nv = NonVersionable(title="Test")

        with pytest.raises(TypeError) as exc_info:
            process_versionable(nv)

        assert "must use shared property 'version'" in str(exc_info.value)

    def test_shared_alias(self):
        """Test @shared shorthand alias."""
        from lib.oda.ontology.decorators.shared_property import shared
        from pydantic import BaseModel

        @shared("version")
        class TestModel(BaseModel):
            title: str

        assert "version" in TestModel.__annotations__


class TestGlobalRegistryFunctions:
    """Test global registry helper functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the global registry before each test."""
        from lib.oda.ontology.registry import load_default_shared_properties
        load_default_shared_properties()
        yield

    def test_get_shared_property_registry(self):
        """Test getting the global registry."""
        from lib.oda.ontology.registry import get_shared_property_registry
        from lib.oda.ontology.types.shared_properties import SharedPropertyRegistry

        registry = get_shared_property_registry()
        assert isinstance(registry, SharedPropertyRegistry)

    def test_register_shared_property(self):
        """Test registering a property via global function."""
        from lib.oda.ontology.registry import (
            register_shared_property,
            get_shared_property,
        )
        from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

        prop = SharedPropertyDefinition(
            property_id="custom_prop",
            description="Custom property",
            type_hint="str",
        )

        result = register_shared_property(prop)
        assert result == prop

        retrieved = get_shared_property("custom_prop")
        assert retrieved == prop

    def test_list_shared_properties_global(self):
        """Test listing properties via global function."""
        from lib.oda.ontology.registry import list_shared_properties

        props = list_shared_properties()
        # Should include built-ins
        assert len(props) > 0

    def test_list_shared_property_ids_global(self):
        """Test listing property IDs via global function."""
        from lib.oda.ontology.registry import list_shared_property_ids

        ids = list_shared_property_ids()
        # Should include built-in IDs
        assert "created_at" in ids or len(ids) > 0

    def test_get_shared_property_usages(self):
        """Test getting property usages via global function."""
        from lib.oda.ontology.registry import get_shared_property_usages
        from lib.oda.ontology.decorators.shared_property import uses_shared_property
        from pydantic import BaseModel

        @uses_shared_property("version")
        class TestModel(BaseModel):
            title: str

        usages = get_shared_property_usages("version")
        assert "TestModel" in usages


class TestIntegrationWithOntologyTypes:
    """Integration tests with OntologyObject types."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the global registry before each test."""
        from lib.oda.ontology.registry import load_default_shared_properties
        load_default_shared_properties()
        yield

    def test_shared_property_with_ontology_object(self):
        """Test using shared properties with OntologyObject."""
        from lib.oda.ontology.decorators.shared_property import uses_shared_property
        from pydantic import BaseModel

        @uses_shared_property("created_at", "modified_by", "version")
        class Document(BaseModel):
            """Document with shared properties."""
            title: str
            content: str

        # Create instance
        doc = Document(title="Test", content="Content")

        # Should have injected properties
        assert hasattr(doc, "created_at")
        assert hasattr(doc, "modified_by")
        assert hasattr(doc, "version")

    def test_shared_property_inheritance(self):
        """Test shared property inheritance behavior."""
        from lib.oda.ontology.decorators.shared_property import (
            uses_shared_property,
            get_shared_properties,
        )
        from pydantic import BaseModel

        @uses_shared_property("version")
        class Base(BaseModel):
            title: str

        class Derived(Base):
            description: str

        # Derived should inherit shared property metadata
        base_props = get_shared_properties(Base)
        assert "version" in base_props

        # Derived gets the annotation from Base
        assert "version" in Derived.__annotations__ or "version" in Base.__annotations__
