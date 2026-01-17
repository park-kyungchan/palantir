"""
Schemas module - Bundled JSON Schema files.

Contains canonical JSON Schema definitions for:
    - ObjectType.schema.json
    - LinkType.schema.json
    - ActionType.schema.json
    - Property.schema.json
    - Metadata.schema.json
    - Interaction.schema.json
"""

from pathlib import Path

SCHEMA_DIR = Path(__file__).parent

def get_schema_path(schema_name: str) -> Path:
    """Get the path to a bundled JSON Schema file."""
    return SCHEMA_DIR / f"{schema_name}.schema.json"

__all__ = ["SCHEMA_DIR", "get_schema_path"]
