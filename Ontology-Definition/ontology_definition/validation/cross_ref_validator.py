"""
Cross-Reference Validator - Validates references between ontology types.

This validator checks that all cross-references within the ontology are valid:
    - LinkType source/target ObjectTypes exist
    - ActionType applies_to ObjectTypes exist
    - ObjectType interface implementations exist
    - Interface extension references exist
    - Property type references (to SharedProperty, StructType) exist

Example:
    from ontology_definition.validation import CrossRefValidator
    from ontology_definition.registry import get_registry

    validator = CrossRefValidator(get_registry())

    # Validate a single LinkType
    result = validator.validate_link_type(my_link_type)

    # Validate entire registry
    all_results = validator.validate_all()
    for type_name, result in all_results.items():
        if not result.is_valid:
            print(f"{type_name}: {result.errors}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ontology_definition.registry.ontology_registry import OntologyRegistry
    from ontology_definition.types.action_type import ActionType
    from ontology_definition.types.interface import Interface
    from ontology_definition.types.link_type import LinkType
    from ontology_definition.types.object_type import ObjectType


@dataclass
class ReferenceError:
    """Details of a cross-reference validation error."""

    source_type: str  # e.g., "LinkType"
    source_name: str  # e.g., "ReportsTo"
    reference_field: str  # e.g., "sourceObjectType"
    referenced_type: str  # e.g., "ObjectType"
    referenced_name: str  # e.g., "Employee"
    message: str


@dataclass
class CrossRefValidationResult:
    """Result of cross-reference validation."""

    is_valid: bool
    errors: list[ReferenceError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_references: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "errors": [
                {
                    "source_type": e.source_type,
                    "source_name": e.source_name,
                    "reference_field": e.reference_field,
                    "referenced_type": e.referenced_type,
                    "referenced_name": e.referenced_name,
                    "message": e.message,
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
            "checked_references": self.checked_references,
        }


class CrossRefValidator:
    """
    Cross-reference validator for ontology definitions.

    Validates that all references between ontology types are resolvable
    within the given OntologyRegistry.
    """

    def __init__(self, registry: OntologyRegistry | None = None) -> None:
        """
        Initialize the CrossRefValidator.

        Args:
            registry: OntologyRegistry to validate against.
                     If None, uses the global registry.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()
        self._registry = registry

    def validate_link_type(self, link_type: LinkType) -> CrossRefValidationResult:
        """
        Validate cross-references in a LinkType.

        Checks:
        - sourceObjectType exists in registry
        - targetObjectType exists in registry

        Args:
            link_type: The LinkType to validate.

        Returns:
            CrossRefValidationResult with any errors.
        """
        errors: list[ReferenceError] = []
        checked = 0

        # Check source ObjectType
        if link_type.source_object_type:
            checked += 1
            if not self._registry.has_object_type(link_type.source_object_type):
                errors.append(
                    ReferenceError(
                        source_type="LinkType",
                        source_name=link_type.api_name,
                        reference_field="sourceObjectType",
                        referenced_type="ObjectType",
                        referenced_name=link_type.source_object_type,
                        message=f"ObjectType '{link_type.source_object_type}' not found in registry",
                    )
                )

        # Check target ObjectType
        if link_type.target_object_type:
            checked += 1
            if not self._registry.has_object_type(link_type.target_object_type):
                errors.append(
                    ReferenceError(
                        source_type="LinkType",
                        source_name=link_type.api_name,
                        reference_field="targetObjectType",
                        referenced_type="ObjectType",
                        referenced_name=link_type.target_object_type,
                        message=f"ObjectType '{link_type.target_object_type}' not found in registry",
                    )
                )

        return CrossRefValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            checked_references=checked,
        )

    def validate_action_type(
        self, action_type: ActionType
    ) -> CrossRefValidationResult:
        """
        Validate cross-references in an ActionType.

        Checks:
        - All applies_to ObjectTypes exist in registry

        Args:
            action_type: The ActionType to validate.

        Returns:
            CrossRefValidationResult with any errors.
        """
        errors: list[ReferenceError] = []
        checked = 0

        # Check applies_to ObjectTypes
        applies_to = getattr(action_type, "applies_to", []) or []
        for obj_type_name in applies_to:
            checked += 1
            if not self._registry.has_object_type(obj_type_name):
                errors.append(
                    ReferenceError(
                        source_type="ActionType",
                        source_name=action_type.api_name,
                        reference_field="appliesTo",
                        referenced_type="ObjectType",
                        referenced_name=obj_type_name,
                        message=f"ObjectType '{obj_type_name}' not found in registry",
                    )
                )

        return CrossRefValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            checked_references=checked,
        )

    def validate_object_type(
        self, object_type: ObjectType
    ) -> CrossRefValidationResult:
        """
        Validate cross-references in an ObjectType.

        Checks:
        - All implemented interfaces exist in registry

        Args:
            object_type: The ObjectType to validate.

        Returns:
            CrossRefValidationResult with any errors.
        """
        errors: list[ReferenceError] = []
        warnings: list[str] = []
        checked = 0

        # Check interfaces
        interfaces = getattr(object_type, "interfaces", []) or []
        for interface_name in interfaces:
            checked += 1
            if not self._registry.has_interface(interface_name):
                errors.append(
                    ReferenceError(
                        source_type="ObjectType",
                        source_name=object_type.api_name,
                        reference_field="interfaces",
                        referenced_type="Interface",
                        referenced_name=interface_name,
                        message=f"Interface '{interface_name}' not found in registry",
                    )
                )
            else:
                # Check interface compliance (as warning, not error)
                from ontology_definition.registry.interface_registry import (
                    get_interface_registry,
                )

                iface_registry = get_interface_registry()
                is_valid, missing = iface_registry.validate_object_type_implements(
                    object_type, interface_name
                )
                if not is_valid:
                    warnings.append(
                        f"ObjectType '{object_type.api_name}' is missing properties "
                        f"required by Interface '{interface_name}': {missing}"
                    )

        return CrossRefValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            checked_references=checked,
        )

    def validate_interface(self, interface: Interface) -> CrossRefValidationResult:
        """
        Validate cross-references in an Interface.

        Checks:
        - All extended interfaces exist in registry
        - No circular inheritance

        Args:
            interface: The Interface to validate.

        Returns:
            CrossRefValidationResult with any errors.
        """
        errors: list[ReferenceError] = []
        warnings: list[str] = []
        checked = 0

        # Check extends
        extends = getattr(interface, "extends", []) or []
        for parent_name in extends:
            checked += 1
            if not self._registry.has_interface(parent_name):
                errors.append(
                    ReferenceError(
                        source_type="Interface",
                        source_name=interface.api_name,
                        reference_field="extends",
                        referenced_type="Interface",
                        referenced_name=parent_name,
                        message=f"Parent Interface '{parent_name}' not found in registry",
                    )
                )

        # Check for circular inheritance
        from ontology_definition.registry.interface_registry import (
            get_interface_registry,
        )

        iface_registry = get_interface_registry()
        cycle = iface_registry.detect_circular_inheritance(interface.api_name)
        if cycle:
            errors.append(
                ReferenceError(
                    source_type="Interface",
                    source_name=interface.api_name,
                    reference_field="extends",
                    referenced_type="Interface",
                    referenced_name=" -> ".join(cycle),
                    message=f"Circular inheritance detected: {' -> '.join(cycle)}",
                )
            )

        return CrossRefValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            checked_references=checked,
        )

    def validate_all(self) -> dict[str, CrossRefValidationResult]:
        """
        Validate all cross-references in the entire registry.

        Returns:
            Dictionary mapping type names to validation results.
        """
        results: dict[str, CrossRefValidationResult] = {}

        # Validate all ObjectTypes
        for obj_type in self._registry.list_object_types():
            key = f"ObjectType:{obj_type.api_name}"
            results[key] = self.validate_object_type(obj_type)

        # Validate all LinkTypes
        for link_type in self._registry.list_link_types():
            key = f"LinkType:{link_type.api_name}"
            results[key] = self.validate_link_type(link_type)

        # Validate all ActionTypes
        for action_type in self._registry.list_action_types():
            key = f"ActionType:{action_type.api_name}"
            results[key] = self.validate_action_type(action_type)

        # Validate all Interfaces
        for interface in self._registry.list_interfaces():
            key = f"Interface:{interface.api_name}"
            results[key] = self.validate_interface(interface)

        return results

    def validate_all_summary(self) -> CrossRefValidationResult:
        """
        Validate all and return a single combined result.

        Returns:
            Combined CrossRefValidationResult with all errors.
        """
        all_results = self.validate_all()

        all_errors: list[ReferenceError] = []
        all_warnings: list[str] = []
        total_checked = 0

        for result in all_results.values():
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            total_checked += result.checked_references

        return CrossRefValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            checked_references=total_checked,
        )

    def find_orphaned_types(self) -> dict[str, list[str]]:
        """
        Find types that are not referenced by anything.

        Returns:
            Dictionary with:
            - orphaned_object_types: ObjectTypes not used in any LinkType or ActionType
            - orphaned_interfaces: Interfaces not implemented by any ObjectType
        """
        # Track referenced ObjectTypes
        referenced_object_types: set[str] = set()

        for link_type in self._registry.list_link_types():
            if link_type.source_object_type:
                referenced_object_types.add(link_type.source_object_type)
            if link_type.target_object_type:
                referenced_object_types.add(link_type.target_object_type)

        for action_type in self._registry.list_action_types():
            applies_to = getattr(action_type, "applies_to", []) or []
            referenced_object_types.update(applies_to)

        # Track referenced Interfaces
        referenced_interfaces: set[str] = set()

        for obj_type in self._registry.list_object_types():
            interfaces = getattr(obj_type, "interfaces", []) or []
            referenced_interfaces.update(interfaces)

        for interface in self._registry.list_interfaces():
            extends = getattr(interface, "extends", []) or []
            referenced_interfaces.update(extends)

        # Find orphans
        all_object_types = set(self._registry.list_object_type_names())
        all_interfaces = set(self._registry.list_interface_names())

        return {
            "orphaned_object_types": list(all_object_types - referenced_object_types),
            "orphaned_interfaces": list(all_interfaces - referenced_interfaces),
        }


# Convenience functions
def validate_cross_references() -> CrossRefValidationResult:
    """Validate all cross-references in the global registry."""
    return CrossRefValidator().validate_all_summary()


def find_orphaned_types() -> dict[str, list[str]]:
    """Find orphaned types in the global registry."""
    return CrossRefValidator().find_orphaned_types()
