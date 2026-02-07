"""
Foundry Importer - Import ontology definitions from Palantir Foundry JSON format.

This importer reads JSON output from Palantir Foundry's Ontology Manager API
and creates corresponding ontology_definition models.

Supports:
    - Single type imports (ObjectType, LinkType, ActionType, Interface)
    - Bulk imports from combined ontology files
    - Automatic registration to OntologyRegistry
    - Validation during import

Example:
    from ontology_definition.import_ import FoundryImporter

    importer = FoundryImporter()

    # Import from JSON string
    object_type = importer.import_object_type(json_string)

    # Import from file
    object_type = importer.import_object_type_from_file("employee.json")

    # Import entire ontology
    result = importer.import_ontology_from_file("ontology_full.json")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from ontology_definition.types.object_type import ObjectType
    from ontology_definition.types.link_type import LinkType
    from ontology_definition.types.action_type import ActionType
    from ontology_definition.types.interface import Interface
    from ontology_definition.registry.ontology_registry import OntologyRegistry


@dataclass
class ImportError:
    """Details of an import error."""

    type_name: str  # e.g., "ObjectType"
    api_name: str  # e.g., "Employee"
    message: str
    source: str = ""  # File or path info


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    imported_count: int = 0
    errors: list[ImportError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    imported_types: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "imported_count": self.imported_count,
            "errors": [
                {
                    "type_name": e.type_name,
                    "api_name": e.api_name,
                    "message": e.message,
                    "source": e.source,
                }
                for e in self.errors
            ],
            "warnings": self.warnings,
            "imported_types": self.imported_types,
        }


class FoundryImporter:
    """
    Importer for Palantir Foundry JSON format.

    Converts Foundry-format JSON to ontology_definition models.
    """

    def __init__(
        self,
        auto_register: bool = False,
        validate_on_import: bool = True,
        strict_mode: bool = False,
    ) -> None:
        """
        Initialize the FoundryImporter.

        Args:
            auto_register: Automatically register imported types to registry.
            validate_on_import: Run validation after import.
            strict_mode: Fail on warnings (not just errors).
        """
        self._auto_register = auto_register
        self._validate_on_import = validate_on_import
        self._strict_mode = strict_mode

    def _parse_json(self, json_input: Union[str, dict[str, Any]]) -> dict[str, Any]:
        """Parse JSON string or pass through dict."""
        if isinstance(json_input, str):
            return json.loads(json_input)
        return json_input

    def import_object_type(
        self,
        json_input: Union[str, dict[str, Any]],
        register: Optional[bool] = None,
    ) -> "ObjectType":
        """
        Import an ObjectType from Foundry JSON format.

        Args:
            json_input: JSON string or dictionary.
            register: Override auto_register for this import.

        Returns:
            Imported ObjectType instance.

        Raises:
            ValueError: If import or validation fails.
        """
        from ontology_definition.types.object_type import ObjectType

        data = self._parse_json(json_input)

        # Remove metadata if present
        data.pop("_metadata", None)

        object_type = ObjectType.from_foundry_dict(data)

        # Validate if enabled
        if self._validate_on_import:
            self._validate_model(object_type)

        # Register if enabled
        should_register = register if register is not None else self._auto_register
        if should_register:
            from ontology_definition.registry.ontology_registry import get_registry

            get_registry().register_object_type(object_type)

        return object_type

    def import_link_type(
        self,
        json_input: Union[str, dict[str, Any]],
        register: Optional[bool] = None,
    ) -> "LinkType":
        """
        Import a LinkType from Foundry JSON format.

        Args:
            json_input: JSON string or dictionary.
            register: Override auto_register for this import.

        Returns:
            Imported LinkType instance.

        Raises:
            ValueError: If import or validation fails.
        """
        from ontology_definition.types.link_type import LinkType

        data = self._parse_json(json_input)
        data.pop("_metadata", None)

        link_type = LinkType.from_foundry_dict(data)

        if self._validate_on_import:
            self._validate_model(link_type)

        should_register = register if register is not None else self._auto_register
        if should_register:
            from ontology_definition.registry.ontology_registry import get_registry

            get_registry().register_link_type(link_type)

        return link_type

    def import_action_type(
        self,
        json_input: Union[str, dict[str, Any]],
        register: Optional[bool] = None,
    ) -> "ActionType":
        """
        Import an ActionType from Foundry JSON format.

        Args:
            json_input: JSON string or dictionary.
            register: Override auto_register for this import.

        Returns:
            Imported ActionType instance.

        Raises:
            ValueError: If import or validation fails.
        """
        from ontology_definition.types.action_type import ActionType

        data = self._parse_json(json_input)
        data.pop("_metadata", None)

        action_type = ActionType.from_foundry_dict(data)

        if self._validate_on_import:
            self._validate_model(action_type)

        should_register = register if register is not None else self._auto_register
        if should_register:
            from ontology_definition.registry.ontology_registry import get_registry

            get_registry().register_action_type(action_type)

        return action_type

    def import_interface(
        self,
        json_input: Union[str, dict[str, Any]],
        register: Optional[bool] = None,
    ) -> "Interface":
        """
        Import an Interface from Foundry JSON format.

        Args:
            json_input: JSON string or dictionary.
            register: Override auto_register for this import.

        Returns:
            Imported Interface instance.

        Raises:
            ValueError: If import or validation fails.
        """
        from ontology_definition.types.interface import Interface

        data = self._parse_json(json_input)
        data.pop("_metadata", None)

        interface = Interface.from_foundry_dict(data)

        if self._validate_on_import:
            self._validate_model(interface)

        should_register = register if register is not None else self._auto_register
        if should_register:
            from ontology_definition.registry.ontology_registry import get_registry

            get_registry().register_interface(interface)

        return interface

    def import_ontology(
        self,
        json_input: Union[str, dict[str, Any]],
        register: Optional[bool] = None,
    ) -> ImportResult:
        """
        Import a complete ontology from Foundry JSON format.

        Expects format:
        {
            "ontology": {
                "objectTypes": [...],
                "linkTypes": [...],
                "actionTypes": [...],
                "interfaces": [...]
            }
        }

        Args:
            json_input: JSON string or dictionary.
            register: Override auto_register for this import.

        Returns:
            ImportResult with counts and any errors.
        """
        data = self._parse_json(json_input)
        data.pop("_metadata", None)

        ontology_data = data.get("ontology", data)
        errors: list[ImportError] = []
        warnings: list[str] = []
        imported_types: dict[str, list[str]] = {
            "object_types": [],
            "link_types": [],
            "action_types": [],
            "interfaces": [],
        }
        imported_count = 0

        # Import Interfaces first (they may be referenced by ObjectTypes)
        for iface_data in ontology_data.get("interfaces", []):
            try:
                interface = self.import_interface(iface_data, register=register)
                imported_types["interfaces"].append(interface.api_name)
                imported_count += 1
            except Exception as e:
                api_name = iface_data.get("apiName", "unknown")
                errors.append(
                    ImportError(
                        type_name="Interface",
                        api_name=api_name,
                        message=str(e),
                    )
                )

        # Import ObjectTypes
        for ot_data in ontology_data.get("objectTypes", []):
            try:
                object_type = self.import_object_type(ot_data, register=register)
                imported_types["object_types"].append(object_type.api_name)
                imported_count += 1
            except Exception as e:
                api_name = ot_data.get("apiName", "unknown")
                errors.append(
                    ImportError(
                        type_name="ObjectType",
                        api_name=api_name,
                        message=str(e),
                    )
                )

        # Import LinkTypes (they reference ObjectTypes)
        for lt_data in ontology_data.get("linkTypes", []):
            try:
                link_type = self.import_link_type(lt_data, register=register)
                imported_types["link_types"].append(link_type.api_name)
                imported_count += 1
            except Exception as e:
                api_name = lt_data.get("apiName", "unknown")
                errors.append(
                    ImportError(
                        type_name="LinkType",
                        api_name=api_name,
                        message=str(e),
                    )
                )

        # Import ActionTypes (they reference ObjectTypes)
        for at_data in ontology_data.get("actionTypes", []):
            try:
                action_type = self.import_action_type(at_data, register=register)
                imported_types["action_types"].append(action_type.api_name)
                imported_count += 1
            except Exception as e:
                api_name = at_data.get("apiName", "unknown")
                errors.append(
                    ImportError(
                        type_name="ActionType",
                        api_name=api_name,
                        message=str(e),
                    )
                )

        success = len(errors) == 0 or (not self._strict_mode and imported_count > 0)

        return ImportResult(
            success=success,
            imported_count=imported_count,
            errors=errors,
            warnings=warnings,
            imported_types=imported_types,
        )

    def import_object_type_from_file(
        self,
        path: Union[str, Path],
        register: Optional[bool] = None,
    ) -> "ObjectType":
        """Import ObjectType from file."""
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        return self.import_object_type(content, register=register)

    def import_link_type_from_file(
        self,
        path: Union[str, Path],
        register: Optional[bool] = None,
    ) -> "LinkType":
        """Import LinkType from file."""
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        return self.import_link_type(content, register=register)

    def import_action_type_from_file(
        self,
        path: Union[str, Path],
        register: Optional[bool] = None,
    ) -> "ActionType":
        """Import ActionType from file."""
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        return self.import_action_type(content, register=register)

    def import_interface_from_file(
        self,
        path: Union[str, Path],
        register: Optional[bool] = None,
    ) -> "Interface":
        """Import Interface from file."""
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        return self.import_interface(content, register=register)

    def import_ontology_from_file(
        self,
        path: Union[str, Path],
        register: Optional[bool] = None,
    ) -> ImportResult:
        """Import complete ontology from file."""
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        return self.import_ontology(content, register=register)

    def import_directory(
        self,
        directory: Union[str, Path],
        register: Optional[bool] = None,
    ) -> ImportResult:
        """
        Import all ontology files from a directory.

        Expected structure:
        - directory/object_types/*.json
        - directory/link_types/*.json
        - directory/action_types/*.json
        - directory/interfaces/*.json

        Args:
            directory: Directory containing ontology files.
            register: Override auto_register for this import.

        Returns:
            ImportResult with counts and any errors.
        """
        directory = Path(directory)
        errors: list[ImportError] = []
        imported_types: dict[str, list[str]] = {
            "object_types": [],
            "link_types": [],
            "action_types": [],
            "interfaces": [],
        }
        imported_count = 0

        # Import Interfaces first
        interfaces_dir = directory / "interfaces"
        if interfaces_dir.exists():
            for file_path in interfaces_dir.glob("*.json"):
                try:
                    interface = self.import_interface_from_file(file_path, register=register)
                    imported_types["interfaces"].append(interface.api_name)
                    imported_count += 1
                except Exception as e:
                    errors.append(
                        ImportError(
                            type_name="Interface",
                            api_name=file_path.stem,
                            message=str(e),
                            source=str(file_path),
                        )
                    )

        # Import ObjectTypes
        object_types_dir = directory / "object_types"
        if object_types_dir.exists():
            for file_path in object_types_dir.glob("*.json"):
                try:
                    object_type = self.import_object_type_from_file(file_path, register=register)
                    imported_types["object_types"].append(object_type.api_name)
                    imported_count += 1
                except Exception as e:
                    errors.append(
                        ImportError(
                            type_name="ObjectType",
                            api_name=file_path.stem,
                            message=str(e),
                            source=str(file_path),
                        )
                    )

        # Import LinkTypes
        link_types_dir = directory / "link_types"
        if link_types_dir.exists():
            for file_path in link_types_dir.glob("*.json"):
                try:
                    link_type = self.import_link_type_from_file(file_path, register=register)
                    imported_types["link_types"].append(link_type.api_name)
                    imported_count += 1
                except Exception as e:
                    errors.append(
                        ImportError(
                            type_name="LinkType",
                            api_name=file_path.stem,
                            message=str(e),
                            source=str(file_path),
                        )
                    )

        # Import ActionTypes
        action_types_dir = directory / "action_types"
        if action_types_dir.exists():
            for file_path in action_types_dir.glob("*.json"):
                try:
                    action_type = self.import_action_type_from_file(file_path, register=register)
                    imported_types["action_types"].append(action_type.api_name)
                    imported_count += 1
                except Exception as e:
                    errors.append(
                        ImportError(
                            type_name="ActionType",
                            api_name=file_path.stem,
                            message=str(e),
                            source=str(file_path),
                        )
                    )

        success = len(errors) == 0 or (not self._strict_mode and imported_count > 0)

        return ImportResult(
            success=success,
            imported_count=imported_count,
            errors=errors,
            imported_types=imported_types,
        )

    def _validate_model(self, model: Any) -> None:
        """Validate a model using RuntimeValidator."""
        from ontology_definition.validation.runtime_validator import RuntimeValidator

        validator = RuntimeValidator(strict_mode=self._strict_mode)
        result = validator.validate_model(model)

        if not result.is_valid:
            error_msgs = [f"{e.field}: {e.message}" for e in result.errors]
            raise ValueError(f"Validation failed: {'; '.join(error_msgs)}")


# Convenience functions
def import_object_type(json_input: Union[str, dict[str, Any]]) -> "ObjectType":
    """Import ObjectType using default importer."""
    return FoundryImporter().import_object_type(json_input)


def import_ontology(json_input: Union[str, dict[str, Any]]) -> ImportResult:
    """Import complete ontology using default importer."""
    return FoundryImporter().import_ontology(json_input)


def import_ontology_from_file(path: Union[str, Path]) -> ImportResult:
    """Import ontology from file using default importer."""
    return FoundryImporter().import_ontology_from_file(path)
