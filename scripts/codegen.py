import json
import os
from typing import Dict, Any, List, Set

SCHEMA_DIRS = [
    ".agent/schemas"
]
OUTPUT_FILE = "scripts/ontology.py"

TYPE_MAPPING = {
    "string": "str",
    "integer": "int",
    "boolean": "bool",
    "array": "List",
    "object": "Dict[str, Any]"
}

def parse_property(prop_name: str, prop_def: Dict[str, Any], classes: List[str], enum_registry: Set[str]) -> str:
    prop_type = prop_def.get("type")
    enum_values = prop_def.get("enum")
    
    if enum_values:
        # Create Enum Class
        enum_name = prop_name.capitalize() + "Enum"
        if enum_name not in enum_registry:
            generate_enum(enum_name, enum_values, classes)
            enum_registry.add(enum_name)
        return enum_name
    
    if prop_type == "array":
        items = prop_def.get("items", {})
        item_type = items.get("type")
        if item_type == "object":
            # Nested object in array -> Create a new class
            class_name = prop_name.capitalize().rstrip('s') # jobs -> Job
            # For now, treating nested objects as Dict for simplicity in recursion, 
            # or we can generate nested classes. For robustness, let's stick to known types or Dict.
            return "List[Dict[str, Any]]" 
        else:
            py_type = TYPE_MAPPING.get(item_type, "Any")
            return f"List[{py_type}]"
            
    elif prop_type == "object":
        # For deeply nested objects not defined in top-level schemas, use Dict
        return "Dict[str, Any]"
        
    else:
        return TYPE_MAPPING.get(prop_type, "Any")

def generate_enum(enum_name: str, values: List[str], classes: List[str]):
    lines = [f"class {enum_name}(str, Enum):"]
    for v in values:
        safe_name = v.upper().replace(" ", "_").replace("-", "_").replace(".", "_")
        # Handle numeric starting enums
        if safe_name[0].isdigit():
            safe_name = "_" + safe_name
        lines.append(f"    {safe_name} = '{v}'")
    lines.append("")
    classes.append("\n".join(lines))

def generate_class(class_name: str, schema: Dict[str, Any], classes: List[str], enum_registry: Set[str], is_base: bool = False):
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    description = schema.get("description", "")
    
    # Determine Base Class
    base_class = "BaseModel"
    if not is_base and class_name != "OrionObject":
        base_class = "OrionObject"

    lines = [f"class {class_name}({base_class}):"]
    if description:
        lines.append(f'    """{description}"""')
    
    # Pydantic V2 Config
    lines.append("    model_config = ConfigDict(extra='forbid', populate_by_name=True)")
    
    if not properties:
        lines.append("    pass")
    
    for prop_name, prop_def in properties.items():
        # Skip fields inherited from OrionObject (unless it IS OrionObject)
        if not is_base and prop_name in ["id", "type", "created_at", "updated_at", "provenance"]:
            continue
            
        py_type = parse_property(prop_name, prop_def, classes, enum_registry)
        is_optional = prop_name not in required
        
        field_args = []
        if description := prop_def.get("description"):
            field_args.append(f'description="{description}"')
            
        field_str = f"Field(..., {', '.join(field_args)})" if field_args else "Field(...)"
        
        if is_optional:
            lines.append(f"    {prop_name}: Optional[{py_type}] = Field(None, description='{prop_def.get('description', '')}')")
        else:
            lines.append(f"    {prop_name}: {py_type} = {field_str}")
    
    lines.append("")
    classes.append("\n".join(lines))

def main():
    print("⚙️  Generating Ontology-Driven Pydantic Models...")
    
    classes = []
    enum_registry = set()
    
    # 1. First, generate OrionObject (Meta-Schema)
    meta_path = ".agent/schemas/meta.schema.json"
    if os.path.exists(meta_path):
        print(f"   Loading Meta-Schema: {meta_path}")
        with open(meta_path, 'r') as f:
            schema = json.load(f)
        generate_class("OrionObject", schema, classes, enum_registry, is_base=True)
    else:
        print("⚠️  Meta-Schema not found! Skipping inheritance.")

    # 2. Generate other schemas
    for d in SCHEMA_DIRS:
        if not os.path.exists(d):
            continue
            
        for filename in os.listdir(d):
            if filename.endswith(".schema.json") and filename != "meta.schema.json":
                filepath = os.path.join(d, filename)
                print(f"   Reading {filepath}...")
                with open(filepath, 'r') as f:
                    schema = json.load(f)
                    
                class_name = filename.replace(".schema.json", "").capitalize()
                # Fix naming conflict if any
                if class_name == "Meta": continue
                
                generate_class(class_name, schema, classes, enum_registry)
    
    # Write Header
    content = [
        "# 🤖 AUTO-GENERATED BY scripts/codegen.py",
        "# DO NOT EDIT MANUALLY",
        "# This file serves as the 'Digital Twin' of the Ontology.",
        "",
        "from typing import List, Optional, Dict, Any",
        "from enum import Enum",
        "from pydantic import BaseModel, Field, ConfigDict",
        "from datetime import datetime",
        "",
    ]
    
    content.extend(classes)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write("\n".join(content))
        
    print(f"✅ Generated {OUTPUT_FILE} with {len(classes)} models.")

if __name__ == "__main__":
    main()