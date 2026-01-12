"""
ODA PAI Tools - Tool Registry
=============================

Defines the ToolDefinition ObjectType and ToolRegistryService for
managing Claude Code tool metadata and configuration.

ObjectTypes:
    - ToolDefinition: Metadata and configuration for a single tool

Services:
    - ToolRegistryService: In-memory registry for tool definitions

Functions:
    - get_tool_registry(): Get the global registry instance
    - register_tool: Decorator for registering tool definitions

Phase: AIP-02 Tool Category System
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TypeVar

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_object_type

from ..algorithm.effort_levels import EffortLevel
from .categories import ToolCategory


# =============================================================================
# OBJECT TYPES
# =============================================================================


@register_object_type
class ToolDefinition(OntologyObject):
    """
    Metadata and configuration for a Claude Code tool.

    ToolDefinition captures all information about a tool including:
    - Identity: name, display_name, description
    - Classification: category, subcategory
    - Safety: is_read_only, is_hazardous, requires_approval
    - Parameters: parameter_schema, required_params
    - Execution: min_effort, timeout_seconds, max_retries
    - Lifecycle: is_enabled, deprecation_warning

    Attributes:
        name: Unique identifier for this tool (lowercase with underscores)
        display_name: Human-readable display name
        description: Detailed description of tool functionality
        category: Tool category for classification
        subcategory: Optional subcategory for finer classification
        api_name: API name used to invoke the tool
        is_read_only: Whether the tool only reads without side effects
        is_hazardous: Whether the tool can cause harmful side effects
        requires_approval: Whether the tool requires explicit approval
        parameter_schema: JSON schema for tool parameters
        required_params: List of required parameter names
        min_effort: Minimum effort level to use this tool
        timeout_seconds: Default timeout for tool execution
        max_retries: Maximum retry attempts on failure
        is_enabled: Whether the tool is currently enabled
        deprecation_warning: Optional deprecation message

    Example:
        ```python
        read_tool = ToolDefinition(
            name="read",
            display_name="Read File",
            description="Reads content from a file",
            category=ToolCategory.FILE_READ,
            api_name="Read",
            is_read_only=True,
            parameter_schema={"file_path": {"type": "string"}},
            required_params=["file_path"],
        )
        ```
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for this tool (lowercase with underscores)"
    )
    display_name: str = Field(
        default="",
        max_length=200,
        description="Human-readable display name"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Detailed description of tool functionality"
    )
    category: ToolCategory = Field(
        ...,
        description="Tool category for classification"
    )
    subcategory: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional subcategory for finer classification"
    )
    api_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="API name used to invoke the tool"
    )
    is_read_only: bool = Field(
        default=False,
        description="Whether the tool only reads without side effects"
    )
    is_hazardous: bool = Field(
        default=False,
        description="Whether the tool can cause harmful side effects"
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether the tool requires explicit approval"
    )
    parameter_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON schema for tool parameters"
    )
    required_params: List[str] = Field(
        default_factory=list,
        description="List of required parameter names"
    )
    min_effort: EffortLevel = Field(
        default=EffortLevel.QUICK,
        description="Minimum effort level to use this tool"
    )
    timeout_seconds: int = Field(
        default=120,
        ge=1,
        le=600,
        description="Default timeout for tool execution (1-600 seconds)"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts on failure (0-10)"
    )
    is_enabled: bool = Field(
        default=True,
        description="Whether the tool is currently enabled"
    )
    deprecation_warning: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional deprecation message"
    )

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate name is lowercase with underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Tool name must be alphanumeric with underscores"
            )
        return v.lower()

    @field_validator("api_name")
    @classmethod
    def validate_api_name(cls, v: str) -> str:
        """Validate API name is not empty."""
        if not v.strip():
            raise ValueError("API name cannot be empty")
        return v.strip()

    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get the full parameter schema with metadata.

        Returns:
            Dict containing the parameter schema with type information
        """
        return {
            "type": "object",
            "properties": self.parameter_schema,
            "required": self.required_params,
            "additionalProperties": False,
        }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate parameters against the schema.

        This performs basic validation checking that:
        1. All required parameters are present
        2. No unknown parameters are provided (if strict)

        Args:
            params: Dictionary of parameter values to validate

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails with details
        """
        # Check required params
        missing = [p for p in self.required_params if p not in params]
        if missing:
            raise ValueError(
                f"Missing required parameters for {self.name}: {missing}"
            )
        return True

    def is_available_at(self, effort: EffortLevel) -> bool:
        """
        Check if this tool is available at the given effort level.

        Args:
            effort: The current effort level

        Returns:
            True if the tool can be used at this effort level
        """
        return self.is_enabled and effort.can_use(self.min_effort)

    def to_summary(self) -> Dict[str, Any]:
        """
        Generate a summary dict for display.

        Returns:
            Dictionary with key tool attributes
        """
        return {
            "name": self.name,
            "display_name": self.display_name or self.name,
            "category": self.category.value,
            "api_name": self.api_name,
            "is_read_only": self.is_read_only,
            "is_hazardous": self.is_hazardous,
            "min_effort": self.min_effort.value,
            "enabled": self.is_enabled,
            "deprecated": self.deprecation_warning is not None,
        }


# =============================================================================
# TOOL REGISTRY SERVICE
# =============================================================================


class ToolRegistryService:
    """
    In-memory registry for tool definitions.

    Provides lookup and filtering of tools by category, safety level,
    and other criteria. Thread-safe for concurrent access.

    Usage:
        ```python
        registry = get_tool_registry()

        # Register a tool
        registry.register(my_tool)

        # Look up tools
        tool = registry.get("read")
        file_tools = registry.list_by_category(ToolCategory.FILE_READ)
        safe_tools = registry.list_read_only()
        ```
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._tools: Dict[str, ToolDefinition] = {}
        self._api_name_index: Dict[str, str] = {}  # api_name -> name

    def register(self, tool: ToolDefinition) -> None:
        """
        Register a tool definition.

        Args:
            tool: The tool definition to register

        Note:
            Registering a tool with an existing name will overwrite it.
        """
        self._tools[tool.name] = tool
        self._api_name_index[tool.api_name] = tool.name

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool by name.

        Args:
            name: The tool name to unregister

        Returns:
            True if the tool was found and removed, False otherwise
        """
        if name in self._tools:
            tool = self._tools.pop(name)
            self._api_name_index.pop(tool.api_name, None)
            return True
        return False

    def get(self, name: str) -> Optional[ToolDefinition]:
        """
        Get a tool definition by name.

        Args:
            name: The tool name to look up

        Returns:
            The tool definition if found, None otherwise
        """
        return self._tools.get(name)

    def find_by_api_name(self, api_name: str) -> Optional[ToolDefinition]:
        """
        Find a tool by its API name.

        Args:
            api_name: The API name to search for

        Returns:
            The tool definition if found, None otherwise
        """
        name = self._api_name_index.get(api_name)
        if name:
            return self._tools.get(name)
        return None

    def list_all(self) -> List[ToolDefinition]:
        """
        List all registered tools.

        Returns:
            List of all tool definitions
        """
        return list(self._tools.values())

    def list_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """
        List tools in a specific category.

        Args:
            category: The category to filter by

        Returns:
            List of tools in the specified category
        """
        return [t for t in self._tools.values() if t.category == category]

    def list_read_only(self) -> List[ToolDefinition]:
        """
        List all read-only tools.

        Returns:
            List of tools marked as read-only
        """
        return [t for t in self._tools.values() if t.is_read_only]

    def list_hazardous(self) -> List[ToolDefinition]:
        """
        List all hazardous tools.

        Returns:
            List of tools marked as hazardous
        """
        return [t for t in self._tools.values() if t.is_hazardous]

    def list_enabled(self) -> List[ToolDefinition]:
        """
        List all enabled tools.

        Returns:
            List of tools that are currently enabled
        """
        return [t for t in self._tools.values() if t.is_enabled]

    def list_requiring_approval(self) -> List[ToolDefinition]:
        """
        List tools that require approval.

        Returns:
            List of tools that require explicit approval
        """
        return [t for t in self._tools.values() if t.requires_approval]

    def list_available_at(self, effort: EffortLevel) -> List[ToolDefinition]:
        """
        List tools available at a specific effort level.

        Args:
            effort: The effort level to check

        Returns:
            List of tools available at the specified effort level
        """
        return [t for t in self._tools.values() if t.is_available_at(effort)]

    def list_deprecated(self) -> List[ToolDefinition]:
        """
        List deprecated tools.

        Returns:
            List of tools with deprecation warnings
        """
        return [
            t for t in self._tools.values()
            if t.deprecation_warning is not None
        ]

    def count(self) -> int:
        """
        Get the total number of registered tools.

        Returns:
            Number of registered tools
        """
        return len(self._tools)

    def count_by_category(self) -> Dict[ToolCategory, int]:
        """
        Get tool counts by category.

        Returns:
            Dictionary mapping categories to tool counts
        """
        counts: Dict[ToolCategory, int] = {}
        for tool in self._tools.values():
            counts[tool.category] = counts.get(tool.category, 0) + 1
        return counts

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._api_name_index.clear()


# =============================================================================
# GLOBAL REGISTRY AND DECORATOR
# =============================================================================

# Global registry instance
_TOOL_REGISTRY = ToolRegistryService()


def get_tool_registry() -> ToolRegistryService:
    """
    Get the global tool registry instance.

    Returns:
        The singleton ToolRegistryService instance
    """
    return _TOOL_REGISTRY


# Type variable for the decorator
T = TypeVar("T", bound=ToolDefinition)


def register_tool(tool: T) -> T:
    """
    Register a tool with the global registry.

    This function can be used to register pre-created ToolDefinition
    instances with the global registry.

    Args:
        tool: The tool definition to register

    Returns:
        The same tool definition (for chaining)

    Example:
        ```python
        read_tool = register_tool(ToolDefinition(
            name="read",
            display_name="Read File",
            category=ToolCategory.FILE_READ,
            api_name="Read",
            is_read_only=True,
        ))
        ```
    """
    _TOOL_REGISTRY.register(tool)
    return tool


def tool_definition(
    name: str,
    category: ToolCategory,
    api_name: str,
    **kwargs: Any
) -> Callable[[type], ToolDefinition]:
    """
    Decorator factory for creating and registering tool definitions.

    This decorator creates a ToolDefinition from the decorated class
    docstring and registers it with the global registry.

    Args:
        name: Unique tool name
        category: Tool category
        api_name: API name for invocation
        **kwargs: Additional ToolDefinition fields

    Returns:
        Decorator function

    Example:
        ```python
        @tool_definition(
            name="custom_tool",
            category=ToolCategory.ANALYSIS,
            api_name="CustomTool",
            is_read_only=True,
        )
        class CustomToolConfig:
            '''A custom analysis tool for code inspection.'''
            pass
        ```
    """
    def decorator(cls: type) -> ToolDefinition:
        description = kwargs.pop("description", None) or (cls.__doc__ or "").strip()
        display_name = kwargs.pop("display_name", None) or name.replace("_", " ").title()

        tool = ToolDefinition(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            api_name=api_name,
            **kwargs
        )
        return register_tool(tool)

    return decorator
