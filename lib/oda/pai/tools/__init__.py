"""
ODA PAI Tools - Tool Category System
=====================================

Provides tool categorization and registry for Claude Code tools.

This module implements AIP-02: Tool Category System, which enables:
- Classification of tools by category (FILE_READ, FILE_WRITE, etc.)
- Safety metadata (is_read_only, is_hazardous, requires_approval)
- Tool registry with lookup and filtering capabilities
- Effort level integration for tool availability

Public API:
    - ToolCategory: Enum for tool classification
    - CATEGORY_DEFAULT_TOOLS: Default tool-to-category mapping
    - ToolDefinition: ObjectType for tool metadata
    - ToolRegistryService: Registry service class
    - get_tool_registry(): Get global registry instance
    - register_tool(): Register a tool definition
    - tool_definition(): Decorator for tool registration

Usage:
    ```python
    from lib.oda.pai.tools import (
        ToolCategory,
        ToolDefinition,
        get_tool_registry,
        register_tool,
    )

    # Create and register a tool
    my_tool = register_tool(ToolDefinition(
        name="my_tool",
        display_name="My Tool",
        category=ToolCategory.ANALYSIS,
        api_name="MyTool",
        is_read_only=True,
    ))

    # Query the registry
    registry = get_tool_registry()
    read_only_tools = registry.list_read_only()
    file_tools = registry.list_by_category(ToolCategory.FILE_READ)
    ```

Phase: AIP-02 Tool Category System
Schema Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Orion ODA Team"

# Categories
from .categories import (
    ToolCategory,
    CATEGORY_DEFAULT_TOOLS,
)

# Registry
from .registry import (
    ToolDefinition,
    ToolRegistryService,
    get_tool_registry,
    register_tool,
    tool_definition,
)

__all__ = [
    # Enums
    "ToolCategory",
    # Constants
    "CATEGORY_DEFAULT_TOOLS",
    # ObjectTypes
    "ToolDefinition",
    # Services
    "ToolRegistryService",
    # Functions
    "get_tool_registry",
    "register_tool",
    "tool_definition",
]
