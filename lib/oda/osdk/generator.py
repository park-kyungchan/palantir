from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel
import textwrap

class GeneratedSDK(BaseModel):
    files: Dict[str, str]  # filename -> content
    summary: str

class OSDKGenerator:
    """
    Generator for type-safe SDK code based on Ontology Definitions.
    Transforms Ontology Schema (Dict) into Python Source Code.
    """

    def generate_from_ontology(self, ontology_definition: Dict[str, Any]) -> GeneratedSDK:
        """
        Generate SDK code (Typescript/Python) from ontology definition.
        
        Args:
            ontology_definition: Dict containing 'objects' list.
                Example: {"objects": [{"name": "Task", "properties": [{"name": "status"}]}]}
            
        Returns:
            GeneratedSDK object containing file contents map.
        """
        files = {}
        objects = ontology_definition.get("objects", [])
        generated_count = 0

        for obj in objects:
            obj_name = obj["name"]
            class_name = f"{obj_name}Query"
            properties = obj.get("properties", [])
            
            # Generate the class code
            code = self._generate_query_class(obj_name, class_name, properties)
            filename = f"{obj_name.lower()}_query.py"
            files[filename] = code
            generated_count += 1
            
        summary = f"Generated {generated_count} OSDK files."
        return GeneratedSDK(files=files, summary=summary)

    def _generate_query_class(self, obj_name: str, class_name: str, properties: List[Dict]) -> str:
        """Helper to generate the source code for a single ObjectQuery class."""
        
        # 1. Imports and Header
        header = [
            "from lib.oda.osdk import ObjectQuery",
            "# Placeholder import - in real usage, would import the actual domain model",
            "try:",
            f"    from lib.oda.ontology.objects.{obj_name.lower()} import {obj_name}",
            "except ImportError:",
            "    # Fallback for dynamic/test environments",
            "    from lib.oda.ontology.ontology_types import OntologyObject",
            f"    class {obj_name}(OntologyObject): pass",
            "",
            f"class {class_name}(ObjectQuery[{obj_name}]):"
        ]
        
        # 2. Methods
        methods_code = []
        for prop in properties:
            prop_name = prop["name"]
            if not prop_name.isidentifier():
                continue
                
            method = (
                f"    @classmethod\n"
                f"    def by_{prop_name}(cls, {prop_name}: str) -> \"{class_name}\":\n"
                f"        return cls({obj_name}).where(\"{prop_name}\", \"eq\", {prop_name})"
            )
            methods_code.append(method)

        if not methods_code:
            methods_code.append("    pass")
            
        # 3. Assemble
        full_code = "\n".join(header) + "\n" + "\n\n".join(methods_code)
        
        return full_code.strip()
