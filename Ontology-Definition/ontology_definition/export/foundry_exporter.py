"""
Foundry Exporter - Export ontology definitions to Palantir Foundry JSON format.

This exporter produces JSON output compatible with Palantir Foundry's
Ontology Manager API and ontology definition files. (GAP-003 P2-HIGH)

Output Format:
    - Uses camelCase field names (Foundry convention)
    - Includes all required metadata fields
    - Preserves RID/apiName relationships
    - Compatible with Foundry's ontology import

Example:
    from ontology_definition.export import FoundryExporter
    from ontology_definition.registry import get_registry

    exporter = FoundryExporter()

    # Export a single ObjectType
    json_str = exporter.export_object_type(my_object_type)

    # Export entire registry
    full_export = exporter.export_registry(get_registry())

    # Export to file
    exporter.export_to_file(my_object_type, "object_type.json")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from ontology_definition.registry.ontology_registry import OntologyRegistry
    from ontology_definition.types.object_type import ObjectType
    from ontology_definition.types.link_type import LinkType
    from ontology_definition.types.action_type import ActionType
    from ontology_definition.types.interface import Interface


@dataclass
class ExportMetadata:
    """Metadata included in export files."""

    export_version: str = "1.0.0"
    export_timestamp: str = ""
    source_package: str = "ontology_definition"
    target_format: str = "palantir-foundry-v2"

    def __post_init__(self) -> None:
        if not self.export_timestamp:
            self.export_timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict[str, Any]:
        return {
            "exportVersion": self.export_version,
            "exportTimestamp": self.export_timestamp,
            "sourcePackage": self.source_package,
            "targetFormat": self.target_format,
        }


class FoundryExporter:
    """
    Exporter for Palantir Foundry JSON format.

    Converts ontology definitions to Foundry-compatible JSON structures
    that can be imported into Foundry's Ontology Manager.
    """

    def __init__(
        self,
        include_metadata: bool = True,
        pretty_print: bool = True,
        indent: int = 2,
    ) -> None:
        """
        Initialize the FoundryExporter.

        Args:
            include_metadata: Include export metadata in output.
            pretty_print: Format JSON with indentation.
            indent: Indentation level for pretty printing.
        """
        self._include_metadata = include_metadata
        self._pretty_print = pretty_print
        self._indent = indent

    def _serialize_json(self, data: dict[str, Any]) -> str:
        """Serialize dictionary to JSON string."""
        if self._pretty_print:
            return json.dumps(data, indent=self._indent, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    def export_object_type(
        self, object_type: "ObjectType", as_dict: bool = False
    ) -> Union[str, dict[str, Any]]:
        """
        Export an ObjectType to Foundry JSON format.

        Args:
            object_type: The ObjectType to export.
            as_dict: If True, return dict instead of JSON string.

        Returns:
            JSON string or dictionary in Foundry format.
        """
        data = object_type.to_foundry_dict()

        if self._include_metadata:
            data["_metadata"] = ExportMetadata().to_dict()

        if as_dict:
            return data
        return self._serialize_json(data)

    def export_link_type(
        self, link_type: "LinkType", as_dict: bool = False
    ) -> Union[str, dict[str, Any]]:
        """
        Export a LinkType to Foundry JSON format.

        Args:
            link_type: The LinkType to export.
            as_dict: If True, return dict instead of JSON string.

        Returns:
            JSON string or dictionary in Foundry format.
        """
        data = link_type.to_foundry_dict()

        if self._include_metadata:
            data["_metadata"] = ExportMetadata().to_dict()

        if as_dict:
            return data
        return self._serialize_json(data)

    def export_action_type(
        self, action_type: "ActionType", as_dict: bool = False
    ) -> Union[str, dict[str, Any]]:
        """
        Export an ActionType to Foundry JSON format.

        Args:
            action_type: The ActionType to export.
            as_dict: If True, return dict instead of JSON string.

        Returns:
            JSON string or dictionary in Foundry format.
        """
        data = action_type.to_foundry_dict()

        if self._include_metadata:
            data["_metadata"] = ExportMetadata().to_dict()

        if as_dict:
            return data
        return self._serialize_json(data)

    def export_interface(
        self, interface: "Interface", as_dict: bool = False
    ) -> Union[str, dict[str, Any]]:
        """
        Export an Interface to Foundry JSON format.

        Args:
            interface: The Interface to export.
            as_dict: If True, return dict instead of JSON string.

        Returns:
            JSON string or dictionary in Foundry format.
        """
        data = interface.to_foundry_dict()

        if self._include_metadata:
            data["_metadata"] = ExportMetadata().to_dict()

        if as_dict:
            return data
        return self._serialize_json(data)

    def export_registry(
        self,
        registry: Optional["OntologyRegistry"] = None,
        as_dict: bool = False,
    ) -> Union[str, dict[str, Any]]:
        """
        Export entire registry to Foundry JSON format.

        Args:
            registry: OntologyRegistry to export. Uses global if None.
            as_dict: If True, return dict instead of JSON string.

        Returns:
            JSON string or dictionary containing all ontology definitions.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        data: dict[str, Any] = {
            "ontology": {
                "objectTypes": [
                    ot.to_foundry_dict() for ot in registry.list_object_types()
                ],
                "linkTypes": [
                    lt.to_foundry_dict() for lt in registry.list_link_types()
                ],
                "actionTypes": [
                    at.to_foundry_dict() for at in registry.list_action_types()
                ],
                "interfaces": [
                    i.to_foundry_dict() for i in registry.list_interfaces()
                ],
            },
            "statistics": registry.stats(),
        }

        if self._include_metadata:
            data["_metadata"] = ExportMetadata().to_dict()

        if as_dict:
            return data
        return self._serialize_json(data)

    def export_to_file(
        self,
        obj: Union["ObjectType", "LinkType", "ActionType", "Interface"],
        path: Union[str, Path],
    ) -> Path:
        """
        Export a single ontology type to a file.

        Args:
            obj: The ontology type to export.
            path: File path to write to.

        Returns:
            Path to the written file.
        """
        path = Path(path)
        class_name = obj.__class__.__name__

        if class_name == "ObjectType":
            json_str = self.export_object_type(obj)  # type: ignore
        elif class_name == "LinkType":
            json_str = self.export_link_type(obj)  # type: ignore
        elif class_name == "ActionType":
            json_str = self.export_action_type(obj)  # type: ignore
        elif class_name == "Interface":
            json_str = self.export_interface(obj)  # type: ignore
        else:
            raise ValueError(f"Unknown ontology type: {class_name}")

        path.write_text(json_str, encoding="utf-8")  # type: ignore
        return path

    def export_registry_to_file(
        self,
        path: Union[str, Path],
        registry: Optional["OntologyRegistry"] = None,
    ) -> Path:
        """
        Export entire registry to a file.

        Args:
            path: File path to write to.
            registry: OntologyRegistry to export. Uses global if None.

        Returns:
            Path to the written file.
        """
        path = Path(path)
        json_str = self.export_registry(registry)
        path.write_text(json_str, encoding="utf-8")  # type: ignore
        return path

    def export_by_category(
        self,
        output_dir: Union[str, Path],
        registry: Optional["OntologyRegistry"] = None,
    ) -> dict[str, list[Path]]:
        """
        Export registry contents to separate files by category.

        Creates:
        - output_dir/object_types/{api_name}.json
        - output_dir/link_types/{api_name}.json
        - output_dir/action_types/{api_name}.json
        - output_dir/interfaces/{api_name}.json

        Args:
            output_dir: Directory to write files to.
            registry: OntologyRegistry to export. Uses global if None.

        Returns:
            Dictionary mapping category names to lists of created file paths.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        output_dir = Path(output_dir)
        created_files: dict[str, list[Path]] = {
            "object_types": [],
            "link_types": [],
            "action_types": [],
            "interfaces": [],
        }

        # Create directories
        (output_dir / "object_types").mkdir(parents=True, exist_ok=True)
        (output_dir / "link_types").mkdir(parents=True, exist_ok=True)
        (output_dir / "action_types").mkdir(parents=True, exist_ok=True)
        (output_dir / "interfaces").mkdir(parents=True, exist_ok=True)

        # Export ObjectTypes
        for ot in registry.list_object_types():
            file_path = output_dir / "object_types" / f"{ot.api_name}.json"
            self.export_to_file(ot, file_path)
            created_files["object_types"].append(file_path)

        # Export LinkTypes
        for lt in registry.list_link_types():
            file_path = output_dir / "link_types" / f"{lt.api_name}.json"
            self.export_to_file(lt, file_path)
            created_files["link_types"].append(file_path)

        # Export ActionTypes
        for at in registry.list_action_types():
            file_path = output_dir / "action_types" / f"{at.api_name}.json"
            self.export_to_file(at, file_path)
            created_files["action_types"].append(file_path)

        # Export Interfaces
        for iface in registry.list_interfaces():
            file_path = output_dir / "interfaces" / f"{iface.api_name}.json"
            self.export_to_file(iface, file_path)
            created_files["interfaces"].append(file_path)

        return created_files


class FoundryBatchExporter:
    """
    Batch exporter for large ontology exports with progress tracking.
    """

    def __init__(
        self,
        exporter: Optional[FoundryExporter] = None,
    ) -> None:
        """
        Initialize the batch exporter.

        Args:
            exporter: FoundryExporter to use. Creates default if None.
        """
        self._exporter = exporter or FoundryExporter()
        self._progress: dict[str, int] = {}

    def export_all(
        self,
        output_dir: Union[str, Path],
        registry: Optional["OntologyRegistry"] = None,
        on_progress: Optional[callable] = None,
    ) -> dict[str, Any]:
        """
        Export all ontology types with progress tracking.

        Args:
            output_dir: Directory to write files to.
            registry: OntologyRegistry to export. Uses global if None.
            on_progress: Callback function(type, name, index, total).

        Returns:
            Export summary with counts and file paths.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        output_dir = Path(output_dir)
        stats = registry.stats()

        # Create single combined file
        combined_path = output_dir / "ontology_full.json"
        combined_path.parent.mkdir(parents=True, exist_ok=True)
        self._exporter.export_registry_to_file(combined_path, registry)

        # Create individual files
        files = self._exporter.export_by_category(output_dir, registry)

        return {
            "combined_file": str(combined_path),
            "individual_files": {
                k: [str(p) for p in v] for k, v in files.items()
            },
            "statistics": stats,
        }


# Convenience functions
def export_to_foundry(
    obj: Union["ObjectType", "LinkType", "ActionType", "Interface"],
) -> str:
    """Export a single ontology type to Foundry JSON format."""
    return FoundryExporter().export_to_file(obj, "/dev/stdout")  # type: ignore


def export_registry_to_foundry(
    registry: Optional["OntologyRegistry"] = None,
) -> str:
    """Export entire registry to Foundry JSON format."""
    return FoundryExporter().export_registry(registry)  # type: ignore
