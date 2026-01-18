"""
Orion ODA v4.0 - Interface Action Types
=======================================

This module implements interface-related ActionTypes for the ODA governance layer.

ActionTypes:
- interface.register: Register a new interface definition (non-hazardous)
- interface.validate: Validate an ObjectType against an interface (non-hazardous)
- interface.export: Export interface registry to JSON (non-hazardous)
- interface.list: List all registered interfaces (non-hazardous)
- interface.get_implementations: Get all implementations of an interface (non-hazardous)

All interface actions are non-hazardous as they don't modify system state
in a destructive manner. Interface registration is additive-only.

Schema Version: 4.0.0
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    register_action,
)
from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import (
    get_interface_registry,
    get_registry,
)
from lib.oda.ontology.types.interface_types import (
    InterfaceDefinition,
    InterfaceValidationResult,
    PropertySpec,
    MethodSpec,
)

logger = logging.getLogger(__name__)


# =============================================================================
# RESULT MODELS
# =============================================================================


class InterfaceRegistrationResult(OntologyObject):
    """
    Result object for interface registration.
    """

    interface_id: str = Field(..., description="ID of the registered interface")
    description: str = Field(..., description="Interface description")
    property_count: int = Field(default=0, description="Number of required properties")
    method_count: int = Field(default=0, description="Number of required methods")
    extends: Optional[List[str]] = Field(default=None, description="Parent interfaces")


class InterfaceListResult(OntologyObject):
    """
    Result object for listing interfaces.
    """

    interfaces: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of interface summaries"
    )
    total_count: int = Field(default=0, description="Total number of interfaces")


class ImplementationListResult(OntologyObject):
    """
    Result object for listing implementations.
    """

    interface_id: str = Field(..., description="Interface ID")
    implementations: List[str] = Field(
        default_factory=list, description="ObjectType names implementing the interface"
    )
    count: int = Field(default=0, description="Number of implementations")


class InterfaceExportResult(OntologyObject):
    """
    Result object for interface export.
    """

    export_path: str = Field(..., description="Path where export was written")
    interface_count: int = Field(default=0, description="Number of interfaces exported")
    implementation_count: int = Field(
        default=0, description="Number of implementations exported"
    )


# =============================================================================
# ACTION TYPES
# =============================================================================


@register_action
class InterfaceRegisterAction(ActionType[InterfaceRegistrationResult]):
    """
    Register a new interface definition.

    Parameters:
        interface_id: Unique interface identifier (e.g., 'IVersionable')
        description: Human-readable description
        required_properties: List of property specifications
        required_methods: List of method specifications
        extends: Optional list of parent interface IDs

    Example:
        ```python
        result = await action.execute({
            "interface_id": "IVersionable",
            "description": "Objects that support versioning",
            "required_properties": [
                {"name": "version", "type_hint": "int"},
            ],
            "required_methods": [
                {"name": "bump_version", "signature": "(self) -> int"},
            ],
        }, context)
        ```
    """

    api_name = "interface.register"
    object_type = InterfaceRegistrationResult
    submission_criteria = [
        RequiredField("interface_id"),
        RequiredField("description"),
    ]
    requires_proposal = False  # Non-hazardous: additive only

    async def apply_edits(
        self, params: Dict[str, Any], context: ActionContext
    ) -> tuple[Optional[InterfaceRegistrationResult], List[EditOperation]]:
        """Register interface in the InterfaceRegistry."""
        interface_id = params["interface_id"]
        description = params["description"]

        # Build property specs
        required_properties = []
        for prop_data in params.get("required_properties", []):
            if isinstance(prop_data, dict):
                required_properties.append(PropertySpec(**prop_data))
            elif isinstance(prop_data, PropertySpec):
                required_properties.append(prop_data)

        # Build method specs
        required_methods = []
        for method_data in params.get("required_methods", []):
            if isinstance(method_data, dict):
                required_methods.append(MethodSpec(**method_data))
            elif isinstance(method_data, MethodSpec):
                required_methods.append(method_data)

        # Create interface definition
        interface = InterfaceDefinition(
            interface_id=interface_id,
            description=description,
            required_properties=required_properties,
            required_methods=required_methods,
            extends=params.get("extends"),
            is_abstract=params.get("is_abstract", False),
        )

        # Register with global registry
        registry = get_interface_registry()
        registry.register_interface(interface)

        # Create result
        result = InterfaceRegistrationResult(
            interface_id=interface_id,
            description=description,
            property_count=len(required_properties),
            method_count=len(required_methods),
            extends=params.get("extends"),
            created_by=context.actor_id,
        )

        # Create edit operation for audit
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="InterfaceDefinition",
            object_id=interface_id,
            changes={
                "interface_id": interface_id,
                "description": description,
                "property_count": len(required_properties),
                "method_count": len(required_methods),
            },
        )

        logger.info(f"Registered interface: {interface_id}")
        return result, [edit]


@register_action
class InterfaceValidateAction(ActionType[OntologyObject]):
    """
    Validate that an ObjectType implements an interface.

    Parameters:
        object_type_name: Name of the ObjectType to validate
        interface_id: ID of the interface to validate against

    Returns:
        InterfaceValidationResult with validation status and any errors
    """

    api_name = "interface.validate"
    object_type = OntologyObject
    submission_criteria = [
        RequiredField("object_type_name"),
        RequiredField("interface_id"),
    ]
    requires_proposal = False

    async def apply_edits(
        self, params: Dict[str, Any], context: ActionContext
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """Validate ObjectType against interface."""
        object_type_name = params["object_type_name"]
        interface_id = params["interface_id"]

        # Get the ObjectType class from registry
        ontology_registry = get_registry()
        object_def = ontology_registry.list_objects().get(object_type_name)

        if object_def is None:
            # Try to find by importing common locations
            try:
                from lib.oda.ontology.objects import task_types

                object_type_cls = getattr(task_types, object_type_name, None)
            except ImportError:
                object_type_cls = None

            if object_type_cls is None:
                return ActionResult(
                    action_type=self.api_name,
                    success=False,
                    error=f"ObjectType '{object_type_name}' not found",
                )

        # Validate against interface
        interface_registry = get_interface_registry()
        result = interface_registry.validate_implementation(
            object_type_cls, interface_id
        )

        # Return validation result as ActionResult
        return ActionResult(
            action_type=self.api_name,
            success=True,
            data=result.model_dump(),
            message=f"Validation {'passed' if result.is_valid else 'failed'} for {object_type_name} -> {interface_id}",
        )


@register_action
class InterfaceListAction(ActionType[InterfaceListResult]):
    """
    List all registered interfaces.

    Parameters:
        include_implementations: If True, include implementation counts
        filter_by_property: Optional property name to filter by
        filter_by_method: Optional method name to filter by
    """

    api_name = "interface.list"
    object_type = InterfaceListResult
    submission_criteria = []
    requires_proposal = False

    async def apply_edits(
        self, params: Dict[str, Any], context: ActionContext
    ) -> tuple[Optional[InterfaceListResult], List[EditOperation]]:
        """List all interfaces."""
        include_implementations = params.get("include_implementations", False)
        filter_by_property = params.get("filter_by_property")
        filter_by_method = params.get("filter_by_method")

        registry = get_interface_registry()
        interfaces = registry.list_interfaces()

        interface_summaries = []
        for iface in interfaces:
            # Apply filters
            if filter_by_property:
                if filter_by_property not in iface.get_all_property_names():
                    continue
            if filter_by_method:
                if filter_by_method not in iface.get_all_method_names():
                    continue

            summary = {
                "interface_id": iface.interface_id,
                "description": iface.description,
                "property_count": len(iface.required_properties),
                "method_count": len(iface.required_methods),
                "extends": iface.extends,
            }

            if include_implementations:
                summary["implementations"] = registry.get_implementations(
                    iface.interface_id
                )
                summary["implementation_count"] = len(summary["implementations"])

            interface_summaries.append(summary)

        result = InterfaceListResult(
            interfaces=interface_summaries,
            total_count=len(interface_summaries),
        )

        return result, []


@register_action
class InterfaceGetImplementationsAction(ActionType[ImplementationListResult]):
    """
    Get all ObjectTypes that implement a specific interface.

    Parameters:
        interface_id: ID of the interface
    """

    api_name = "interface.get_implementations"
    object_type = ImplementationListResult
    submission_criteria = [
        RequiredField("interface_id"),
    ]
    requires_proposal = False

    async def apply_edits(
        self, params: Dict[str, Any], context: ActionContext
    ) -> tuple[Optional[ImplementationListResult], List[EditOperation]]:
        """Get implementations for an interface."""
        interface_id = params["interface_id"]

        registry = get_interface_registry()
        implementations = registry.get_implementations(interface_id)

        result = ImplementationListResult(
            interface_id=interface_id,
            implementations=implementations,
            count=len(implementations),
        )

        return result, []


@register_action
class InterfaceExportAction(ActionType[InterfaceExportResult]):
    """
    Export interface registry to JSON file.

    Parameters:
        output_path: Path where to write the export
        include_statistics: If True, include statistics section
    """

    api_name = "interface.export"
    object_type = InterfaceExportResult
    submission_criteria = [
        RequiredField("output_path"),
    ]
    requires_proposal = False

    async def apply_edits(
        self, params: Dict[str, Any], context: ActionContext
    ) -> tuple[Optional[InterfaceExportResult], List[EditOperation]]:
        """Export interface registry."""
        output_path = Path(params["output_path"])

        registry = get_interface_registry()
        registry.export_json(output_path)

        # Count totals
        interfaces = registry.list_interfaces()
        total_implementations = sum(
            len(registry.get_implementations(iface.interface_id))
            for iface in interfaces
        )

        result = InterfaceExportResult(
            export_path=str(output_path),
            interface_count=len(interfaces),
            implementation_count=total_implementations,
        )

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="InterfaceExport",
            object_id=str(output_path),
            changes={
                "path": str(output_path),
                "interface_count": len(interfaces),
                "implementation_count": total_implementations,
            },
        )

        logger.info(f"Exported {len(interfaces)} interfaces to {output_path}")
        return result, [edit]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Result models
    "InterfaceRegistrationResult",
    "InterfaceListResult",
    "ImplementationListResult",
    "InterfaceExportResult",
    # Action types
    "InterfaceRegisterAction",
    "InterfaceValidateAction",
    "InterfaceListAction",
    "InterfaceGetImplementationsAction",
    "InterfaceExportAction",
]
