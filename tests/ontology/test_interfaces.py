"""
Orion ODA V4.0 - Interface System Tests
=======================================

Unit tests for Phase 1: Interfaces (ObjectType Polymorphism):
- InterfaceDefinition Pydantic models
- InterfaceRegistry operations
- @implements_interface decorator
- Interface validation
- Interface actions

Tests cover:
- PropertySpec and MethodSpec creation/validation
- InterfaceDefinition model validation
- InterfaceRegistry registration and lookup
- Interface inheritance resolution
- Implementation validation
- Decorator-based interface declaration
- Interface-related actions

Schema Version: 4.0.0
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from lib.oda.ontology.ontology_types import OntologyObject


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def fresh_interface_registry():
    """Create a fresh InterfaceRegistry for each test."""
    from lib.oda.ontology.registry import InterfaceRegistry

    return InterfaceRegistry()


@pytest.fixture
def sample_property_specs():
    """Create sample property specifications."""
    from lib.oda.ontology.types.interface_types import PropertySpec

    return [
        PropertySpec(name="version", type_hint="int", description="Version number"),
        PropertySpec(name="version_history", type_hint="List[str]", required=False),
    ]


@pytest.fixture
def sample_method_specs():
    """Create sample method specifications."""
    from lib.oda.ontology.types.interface_types import MethodSpec

    return [
        MethodSpec(
            name="bump_version",
            signature="(self) -> int",
            description="Increment version",
        ),
        MethodSpec(
            name="get_version_info",
            signature="(self) -> Dict[str, Any]",
            is_async=False,
        ),
    ]


@pytest.fixture
def versionable_interface(sample_property_specs, sample_method_specs):
    """Create a sample IVersionable interface."""
    from lib.oda.ontology.types.interface_types import InterfaceDefinition

    return InterfaceDefinition(
        interface_id="IVersionable",
        description="Objects that support versioning",
        required_properties=sample_property_specs,
        required_methods=sample_method_specs,
    )


# =============================================================================
# PROPERTY SPEC TESTS
# =============================================================================


class TestPropertySpec:
    """Tests for PropertySpec model."""

    def test_create_basic_property(self):
        """Test creating a basic property specification."""
        from lib.oda.ontology.types.interface_types import PropertySpec

        prop = PropertySpec(name="version", type_hint="int")

        assert prop.name == "version"
        assert prop.type_hint == "int"
        assert prop.required is True
        assert prop.description is None

    def test_create_full_property(self):
        """Test creating a fully specified property."""
        from lib.oda.ontology.types.interface_types import PropertySpec

        prop = PropertySpec(
            name="tags",
            type_hint="List[str]",
            description="List of tags",
            required=False,
            default_allowed=True,
        )

        assert prop.name == "tags"
        assert prop.type_hint == "List[str]"
        assert prop.description == "List of tags"
        assert prop.required is False

    def test_invalid_name_double_underscore(self):
        """Test that double underscore names are rejected."""
        from lib.oda.ontology.types.interface_types import PropertySpec

        with pytest.raises(ValueError, match="double underscore"):
            PropertySpec(name="__private", type_hint="str")

    def test_name_pattern_validation(self):
        """Test name follows Python naming conventions."""
        from lib.oda.ontology.types.interface_types import PropertySpec

        # Valid names
        PropertySpec(name="version", type_hint="int")
        PropertySpec(name="version_number", type_hint="int")
        PropertySpec(name="_internal", type_hint="int")

        # Invalid names
        with pytest.raises(ValueError):
            PropertySpec(name="123invalid", type_hint="int")


# =============================================================================
# METHOD SPEC TESTS
# =============================================================================


class TestMethodSpec:
    """Tests for MethodSpec model."""

    def test_create_basic_method(self):
        """Test creating a basic method specification."""
        from lib.oda.ontology.types.interface_types import MethodSpec

        method = MethodSpec(
            name="bump_version",
            signature="(self) -> int",
        )

        assert method.name == "bump_version"
        assert method.signature == "(self) -> int"
        assert method.is_async is False

    def test_create_async_method(self):
        """Test creating an async method specification."""
        from lib.oda.ontology.types.interface_types import MethodSpec

        method = MethodSpec(
            name="fetch_data",
            signature="(self, url: str) -> Dict[str, Any]",
            is_async=True,
        )

        assert method.is_async is True

    def test_signature_validation_missing_parenthesis(self):
        """Test signature must start with parenthesis."""
        from lib.oda.ontology.types.interface_types import MethodSpec

        with pytest.raises(ValueError, match="start with"):
            MethodSpec(name="bad", signature="self -> int")

    def test_signature_validation_missing_return_type(self):
        """Test signature must include return type."""
        from lib.oda.ontology.types.interface_types import MethodSpec

        with pytest.raises(ValueError, match="return type"):
            MethodSpec(name="bad", signature="(self)")


# =============================================================================
# INTERFACE DEFINITION TESTS
# =============================================================================


class TestInterfaceDefinition:
    """Tests for InterfaceDefinition model."""

    def test_create_minimal_interface(self):
        """Test creating a minimal interface."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition

        iface = InterfaceDefinition(
            interface_id="IMinimal",
            description="A minimal interface",
        )

        assert iface.interface_id == "IMinimal"
        assert iface.description == "A minimal interface"
        assert iface.required_properties == []
        assert iface.required_methods == []
        assert iface.extends is None

    def test_create_full_interface(self, sample_property_specs, sample_method_specs):
        """Test creating a fully specified interface."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition

        iface = InterfaceDefinition(
            interface_id="IVersionable",
            description="Versionable objects",
            required_properties=sample_property_specs,
            required_methods=sample_method_specs,
            extends=["IBase"],
            is_abstract=False,
        )

        assert len(iface.required_properties) == 2
        assert len(iface.required_methods) == 2
        assert iface.extends == ["IBase"]

    def test_interface_cannot_extend_self(self):
        """Test interface cannot extend itself."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition

        with pytest.raises(ValueError, match="cannot extend itself"):
            InterfaceDefinition(
                interface_id="ISelfRef",
                description="Self-referencing",
                extends=["ISelfRef"],
            )

    def test_get_all_property_names(self, versionable_interface):
        """Test getting all property names."""
        names = versionable_interface.get_all_property_names()
        assert "version" in names
        assert "version_history" in names

    def test_get_all_method_names(self, versionable_interface):
        """Test getting all method names."""
        names = versionable_interface.get_all_method_names()
        assert "bump_version" in names
        assert "get_version_info" in names


# =============================================================================
# INTERFACE REGISTRY TESTS
# =============================================================================


class TestInterfaceRegistry:
    """Tests for InterfaceRegistry."""

    def test_register_interface(self, fresh_interface_registry, versionable_interface):
        """Test registering an interface."""
        registry = fresh_interface_registry
        registry.register_interface(versionable_interface)

        assert registry.get_interface("IVersionable") is not None

    def test_register_duplicate_raises(
        self, fresh_interface_registry, versionable_interface
    ):
        """Test registering duplicate interface raises error."""
        registry = fresh_interface_registry
        registry.register_interface(versionable_interface)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_interface(versionable_interface)

    def test_list_interfaces(self, fresh_interface_registry, versionable_interface):
        """Test listing all interfaces."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition

        registry = fresh_interface_registry
        registry.register_interface(versionable_interface)
        registry.register_interface(
            InterfaceDefinition(
                interface_id="IAuditable",
                description="Auditable objects",
            )
        )

        interfaces = registry.list_interfaces()
        assert len(interfaces) == 2

    def test_interface_inheritance(self, fresh_interface_registry):
        """Test interface inheritance resolution."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceDefinition,
            PropertySpec,
            MethodSpec,
        )

        registry = fresh_interface_registry

        # Register base interface
        base = InterfaceDefinition(
            interface_id="IBase",
            description="Base interface",
            required_properties=[
                PropertySpec(name="id", type_hint="str"),
            ],
            required_methods=[
                MethodSpec(name="get_id", signature="(self) -> str"),
            ],
        )
        registry.register_interface(base)

        # Register child interface
        child = InterfaceDefinition(
            interface_id="IChild",
            description="Child interface",
            required_properties=[
                PropertySpec(name="name", type_hint="str"),
            ],
            extends=["IBase"],
        )
        registry.register_interface(child)

        # Get full interface (with inherited members)
        full_child = registry.get_full_interface("IChild")

        assert len(full_child.required_properties) == 2  # id + name
        assert "id" in full_child.get_all_property_names()
        assert "name" in full_child.get_all_property_names()

    def test_validate_implementation_success(self, fresh_interface_registry):
        """Test successful implementation validation."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceDefinition,
            PropertySpec,
            MethodSpec,
        )

        registry = fresh_interface_registry

        # Register interface
        iface = InterfaceDefinition(
            interface_id="ISimple",
            description="Simple interface",
            required_properties=[
                PropertySpec(name="name", type_hint="str"),
            ],
            required_methods=[
                MethodSpec(name="get_name", signature="(self) -> str"),
            ],
        )
        registry.register_interface(iface)

        # Create implementing class
        class SimpleObject(OntologyObject):
            name: str = "default"

            def get_name(self) -> str:
                return self.name

        # Validate
        result = registry.validate_implementation(SimpleObject, "ISimple")
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_implementation_missing_property(self, fresh_interface_registry):
        """Test validation fails for missing property."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceDefinition,
            PropertySpec,
        )

        registry = fresh_interface_registry

        iface = InterfaceDefinition(
            interface_id="IRequiresName",
            description="Requires name",
            required_properties=[
                PropertySpec(name="name", type_hint="str"),
            ],
        )
        registry.register_interface(iface)

        class MissingNameObject(OntologyObject):
            pass  # Missing 'name' property

        result = registry.validate_implementation(MissingNameObject, "IRequiresName")
        assert result.is_valid is False
        assert any("missing_property" in e.error_type for e in result.errors)

    def test_validate_implementation_missing_method(self, fresh_interface_registry):
        """Test validation fails for missing method."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceDefinition,
            MethodSpec,
        )

        registry = fresh_interface_registry

        iface = InterfaceDefinition(
            interface_id="IRequiresMethod",
            description="Requires method",
            required_methods=[
                MethodSpec(name="do_something", signature="(self) -> None"),
            ],
        )
        registry.register_interface(iface)

        class MissingMethodObject(OntologyObject):
            pass  # Missing 'do_something' method

        result = registry.validate_implementation(MissingMethodObject, "IRequiresMethod")
        assert result.is_valid is False
        assert any("missing_method" in e.error_type for e in result.errors)

    def test_register_implementation(self, fresh_interface_registry):
        """Test registering an implementation."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition

        registry = fresh_interface_registry

        iface = InterfaceDefinition(
            interface_id="IEmpty",
            description="Empty interface",
        )
        registry.register_interface(iface)

        class EmptyImpl(OntologyObject):
            pass

        registry.register_implementation(EmptyImpl, "IEmpty")

        assert "EmptyImpl" in registry.get_implementations("IEmpty")
        assert "IEmpty" in registry.get_interfaces_for_object("EmptyImpl")

    def test_export_json(self, fresh_interface_registry, versionable_interface):
        """Test exporting registry to JSON."""
        registry = fresh_interface_registry
        registry.register_interface(versionable_interface)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "interfaces.json"
            registry.export_json(path)

            assert path.exists()
            data = json.loads(path.read_text())

            assert "interfaces" in data
            assert "IVersionable" in data["interfaces"]
            assert "statistics" in data


# =============================================================================
# DECORATOR TESTS
# =============================================================================


class TestImplementsInterfaceDecorator:
    """Tests for @implements_interface decorator."""

    def test_decorator_registers_implementation(self, fresh_interface_registry):
        """Test decorator registers the implementation."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition
        from lib.oda.ontology.decorators.interface_decorator import implements_interface

        # Patch the global registry
        import lib.oda.ontology.registry as registry_module

        original_registry = registry_module._INTERFACE_REGISTRY
        registry_module._INTERFACE_REGISTRY = fresh_interface_registry

        try:
            # Register interface
            iface = InterfaceDefinition(
                interface_id="IDecorated",
                description="For decorator test",
            )
            fresh_interface_registry.register_interface(iface)

            # Apply decorator
            @implements_interface("IDecorated")
            class DecoratedObject(OntologyObject):
                pass

            # Verify registration
            assert "DecoratedObject" in fresh_interface_registry.get_implementations(
                "IDecorated"
            )
            assert hasattr(DecoratedObject, "_implements")
            assert "IDecorated" in DecoratedObject._implements

        finally:
            registry_module._INTERFACE_REGISTRY = original_registry

    def test_decorator_validation_failure_strict(self, fresh_interface_registry):
        """Test decorator raises on validation failure in strict mode."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceDefinition,
            PropertySpec,
        )
        from lib.oda.ontology.decorators.interface_decorator import (
            implements_interface,
            InterfaceImplementationError,
        )

        import lib.oda.ontology.registry as registry_module

        original_registry = registry_module._INTERFACE_REGISTRY
        registry_module._INTERFACE_REGISTRY = fresh_interface_registry

        try:
            iface = InterfaceDefinition(
                interface_id="IStrict",
                description="Strict interface",
                required_properties=[
                    PropertySpec(name="required_field", type_hint="str"),
                ],
            )
            fresh_interface_registry.register_interface(iface)

            with pytest.raises(InterfaceImplementationError):

                @implements_interface("IStrict", strict=True)
                class MissingField(OntologyObject):
                    pass  # Missing required_field

        finally:
            registry_module._INTERFACE_REGISTRY = original_registry

    def test_decorator_non_strict_mode(self, fresh_interface_registry):
        """Test decorator warns but doesn't raise in non-strict mode."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceDefinition,
            PropertySpec,
        )
        from lib.oda.ontology.decorators.interface_decorator import implements_interface

        import lib.oda.ontology.registry as registry_module

        original_registry = registry_module._INTERFACE_REGISTRY
        registry_module._INTERFACE_REGISTRY = fresh_interface_registry

        try:
            iface = InterfaceDefinition(
                interface_id="INonStrict",
                description="Non-strict interface",
                required_properties=[
                    PropertySpec(name="required_field", type_hint="str"),
                ],
            )
            fresh_interface_registry.register_interface(iface)

            # Should not raise
            @implements_interface("INonStrict", strict=False)
            class MissingField(OntologyObject):
                pass

            # But should not register the implementation
            assert "MissingField" not in fresh_interface_registry.get_implementations(
                "INonStrict"
            )

        finally:
            registry_module._INTERFACE_REGISTRY = original_registry

    def test_multiple_interfaces(self, fresh_interface_registry):
        """Test implementing multiple interfaces."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition
        from lib.oda.ontology.decorators.interface_decorator import implements_interface

        import lib.oda.ontology.registry as registry_module

        original_registry = registry_module._INTERFACE_REGISTRY
        registry_module._INTERFACE_REGISTRY = fresh_interface_registry

        try:
            # Register multiple interfaces
            fresh_interface_registry.register_interface(
                InterfaceDefinition(interface_id="IFirst", description="First")
            )
            fresh_interface_registry.register_interface(
                InterfaceDefinition(interface_id="ISecond", description="Second")
            )

            @implements_interface("IFirst", "ISecond")
            class MultiImpl(OntologyObject):
                pass

            assert "IFirst" in MultiImpl._implements
            assert "ISecond" in MultiImpl._implements

        finally:
            registry_module._INTERFACE_REGISTRY = original_registry


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================


class TestInterfaceUtilities:
    """Tests for interface utility functions."""

    def test_check_interface(self, fresh_interface_registry):
        """Test check_interface function."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition
        from lib.oda.ontology.decorators.interface_decorator import (
            implements_interface,
            check_interface,
        )

        import lib.oda.ontology.registry as registry_module

        original_registry = registry_module._INTERFACE_REGISTRY
        registry_module._INTERFACE_REGISTRY = fresh_interface_registry

        try:
            fresh_interface_registry.register_interface(
                InterfaceDefinition(interface_id="ICheckable", description="Checkable")
            )

            @implements_interface("ICheckable")
            class CheckableObject(OntologyObject):
                pass

            assert check_interface(CheckableObject, "ICheckable") is True
            assert check_interface(CheckableObject, "IOther") is False

        finally:
            registry_module._INTERFACE_REGISTRY = original_registry

    def test_get_implemented_interfaces(self, fresh_interface_registry):
        """Test get_implemented_interfaces function."""
        from lib.oda.ontology.types.interface_types import InterfaceDefinition
        from lib.oda.ontology.decorators.interface_decorator import (
            implements_interface,
            get_implemented_interfaces,
        )

        import lib.oda.ontology.registry as registry_module

        original_registry = registry_module._INTERFACE_REGISTRY
        registry_module._INTERFACE_REGISTRY = fresh_interface_registry

        try:
            fresh_interface_registry.register_interface(
                InterfaceDefinition(interface_id="IA", description="A")
            )
            fresh_interface_registry.register_interface(
                InterfaceDefinition(interface_id="IB", description="B")
            )

            @implements_interface("IA", "IB")
            class ABImpl(OntologyObject):
                pass

            interfaces = get_implemented_interfaces(ABImpl)
            assert "IA" in interfaces
            assert "IB" in interfaces

        finally:
            registry_module._INTERFACE_REGISTRY = original_registry


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================


class TestInterfaceValidationResult:
    """Tests for InterfaceValidationResult model."""

    def test_success_result(self):
        """Test creating success result."""
        from lib.oda.ontology.types.interface_types import InterfaceValidationResult

        result = InterfaceValidationResult.success("MyObject", "ITest")

        assert result.is_valid is True
        assert result.object_type == "MyObject"
        assert result.interface_id == "ITest"
        assert len(result.errors) == 0

    def test_failure_result(self):
        """Test creating failure result."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceValidationResult,
            InterfaceValidationError,
        )

        errors = [
            InterfaceValidationError(
                error_type="missing_property",
                interface_id="ITest",
                detail="Missing property 'name'",
                property_name="name",
            )
        ]
        result = InterfaceValidationResult.failure("MyObject", "ITest", errors)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].property_name == "name"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestInterfaceIntegration:
    """Integration tests for the interface system."""

    def test_full_workflow(self, fresh_interface_registry):
        """Test complete interface workflow."""
        from lib.oda.ontology.types.interface_types import (
            InterfaceDefinition,
            PropertySpec,
            MethodSpec,
        )
        from lib.oda.ontology.decorators.interface_decorator import (
            implements_interface,
            check_interface,
        )

        import lib.oda.ontology.registry as registry_module

        original_registry = registry_module._INTERFACE_REGISTRY
        registry_module._INTERFACE_REGISTRY = fresh_interface_registry

        try:
            # 1. Define interface
            iface = InterfaceDefinition(
                interface_id="IFullWorkflow",
                description="Full workflow test",
                required_properties=[
                    PropertySpec(name="data", type_hint="Dict[str, Any]"),
                ],
                required_methods=[
                    MethodSpec(name="process", signature="(self) -> bool"),
                ],
            )
            fresh_interface_registry.register_interface(iface)

            # 2. Create implementing class
            @implements_interface("IFullWorkflow")
            class WorkflowObject(OntologyObject):
                data: Dict[str, Any] = {}

                def process(self) -> bool:
                    return True

            # 3. Verify implementation
            assert check_interface(WorkflowObject, "IFullWorkflow")

            # 4. Use the object
            obj = WorkflowObject(data={"key": "value"})
            assert obj.process() is True

            # 5. Verify registry state
            assert "WorkflowObject" in fresh_interface_registry.get_implementations(
                "IFullWorkflow"
            )

        finally:
            registry_module._INTERFACE_REGISTRY = original_registry


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TestPropertySpec",
    "TestMethodSpec",
    "TestInterfaceDefinition",
    "TestInterfaceRegistry",
    "TestImplementsInterfaceDecorator",
    "TestInterfaceUtilities",
    "TestInterfaceValidationResult",
    "TestInterfaceIntegration",
]
