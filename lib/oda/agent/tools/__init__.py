"""
Orion ODA v4.0 - Agent Tools Registry
=====================================

Central registry for all agent tools with discovery mechanism.
Provides unified access to ObjectQuery, ActionExecutor, and FunctionCall tools.

This module implements:
- Tool registration and discovery
- Unified tool interface
- Export for LLM function calling

Usage:
    ```python
    from lib.oda.agent.tools import (
        get_all_tools,
        get_tool,
        ObjectQueryTool,
        ActionExecutorTool,
        FunctionCallTool,
    )

    # Get all registered tools
    tools = get_all_tools()

    # Get specific tool
    query_tool = get_tool("object_query")

    # Export all tool definitions for LLM
    definitions = export_tool_definitions()
    ```
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

# Import tool classes
from lib.oda.agent.tools.object_query import (
    ObjectQueryTool,
    GetObjectInput,
    ListObjectsInput,
    SearchObjectsInput,
    ObjectQueryResult,
    SchemaQueryResult,
    get_tool_definition as get_object_query_definition,
)
from lib.oda.agent.tools.action_executor import (
    ActionExecutorTool,
    ExecuteActionInput,
    GetActionSchemaInput,
    ListActionsInput,
    ActionExecutionResult,
    ActionSchemaResult,
    ActionListResult,
    get_tool_definition as get_action_executor_definition,
)
from lib.oda.agent.tools.function_call import (
    FunctionCallTool,
    FunctionDefinition,
    ToolDefinition,
    FunctionCallRequest,
    FunctionCallResponse,
    ActionToFunctionConverter,
    ClaudeToolAdapter,
    get_tool_definition as get_function_call_definition,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL REGISTRY
# =============================================================================


class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""

    name: str = Field(description="Tool identifier")
    description: str = Field(description="Tool description")
    tool_class: str = Field(description="Fully qualified class name")
    version: str = Field(default="1.0.0")
    category: str = Field(default="general")
    is_async: bool = Field(default=True)


class ToolRegistry:
    """
    Central registry for agent tools.

    Provides:
    - Tool registration
    - Tool discovery
    - Tool instantiation
    - Definition export

    Example:
        ```python
        registry = ToolRegistry()

        # Register custom tool
        registry.register(MyCustomTool, metadata={...})

        # Get all tools
        for name, meta in registry.list_tools().items():
            print(f"{name}: {meta.description}")

        # Instantiate a tool
        tool = registry.get_instance("object_query")
        ```
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Type] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._instances: Dict[str, Any] = {}

    def register(
        self,
        tool_class: Type,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a tool class.

        Args:
            tool_class: Tool class to register
            name: Optional name override (defaults to TOOL_NAME attribute)
            metadata: Optional metadata override
        """
        # Get tool name
        tool_name = name or getattr(tool_class, "TOOL_NAME", tool_class.__name__)

        # Build metadata
        meta = ToolMetadata(
            name=tool_name,
            description=getattr(
                tool_class,
                "TOOL_DESCRIPTION",
                tool_class.__doc__ or "No description",
            ),
            tool_class=f"{tool_class.__module__}.{tool_class.__name__}",
            **(metadata or {}),
        )

        self._tools[tool_name] = tool_class
        self._metadata[tool_name] = meta

        logger.debug(f"Registered tool: {tool_name}")

    def get(self, name: str) -> Optional[Type]:
        """Get a tool class by name."""
        return self._tools.get(name)

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name."""
        return self._metadata.get(name)

    def get_instance(self, name: str, **kwargs) -> Any:
        """
        Get or create a tool instance.

        Args:
            name: Tool name
            **kwargs: Arguments passed to tool constructor

        Returns:
            Tool instance

        Raises:
            KeyError: If tool not found
        """
        # Check cache if no kwargs
        if not kwargs and name in self._instances:
            return self._instances[name]

        tool_class = self._tools.get(name)
        if not tool_class:
            raise KeyError(f"Tool '{name}' not registered")

        instance = tool_class(**kwargs)

        # Cache if no kwargs
        if not kwargs:
            self._instances[name] = instance

        return instance

    def list_tools(self) -> Dict[str, ToolMetadata]:
        """List all registered tools with metadata."""
        return dict(self._metadata)

    def list_names(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def clear_instances(self) -> None:
        """Clear cached tool instances."""
        self._instances.clear()


# =============================================================================
# GLOBAL REGISTRY
# =============================================================================


_registry = ToolRegistry()


def _register_builtin_tools() -> None:
    """Register built-in ODA tools."""
    _registry.register(
        ObjectQueryTool,
        metadata={"category": "query", "version": "4.0.0"},
    )
    _registry.register(
        ActionExecutorTool,
        metadata={"category": "execution", "version": "4.0.0"},
    )
    _registry.register(
        FunctionCallTool,
        metadata={"category": "integration", "version": "4.0.0"},
    )


# Initialize on import
_register_builtin_tools()


# =============================================================================
# PUBLIC API
# =============================================================================


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry


def get_tool(name: str) -> Any:
    """
    Get a tool instance by name.

    Args:
        name: Tool name

    Returns:
        Tool instance
    """
    return _registry.get_instance(name)


def get_all_tools() -> Dict[str, Any]:
    """
    Get instances of all registered tools.

    Returns:
        Dict mapping tool names to instances
    """
    return {name: _registry.get_instance(name) for name in _registry.list_names()}


def list_tools() -> List[str]:
    """List all registered tool names."""
    return _registry.list_names()


def register_tool(
    tool_class: Type,
    name: Optional[str] = None,
    **metadata,
) -> Type:
    """
    Register a tool class with the global registry.

    Can be used as a decorator:
        ```python
        @register_tool
        class MyTool:
            TOOL_NAME = "my_tool"
            ...
        ```

    Args:
        tool_class: Tool class to register
        name: Optional name override
        **metadata: Additional metadata

    Returns:
        The tool class (for decorator use)
    """
    _registry.register(tool_class, name=name, metadata=metadata or None)
    return tool_class


# =============================================================================
# DEFINITION EXPORT
# =============================================================================


def export_tool_definitions(
    format: str = "openai",
    include: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Export tool definitions for LLM function calling.

    Args:
        format: Export format ("openai" or "claude")
        include: Optional list of tool names to include (all if None)

    Returns:
        List of tool definitions
    """
    definitions = []

    tool_defs = {
        "object_query": get_object_query_definition,
        "action_executor": get_action_executor_definition,
        "function_call": get_function_call_definition,
    }

    for name, get_def in tool_defs.items():
        if include is None or name in include:
            definitions.append(get_def())

    if format == "claude":
        # Convert to Claude format
        return [
            {
                "name": d["function"]["name"],
                "description": d["function"]["description"],
                "input_schema": d["function"]["parameters"],
            }
            for d in definitions
        ]

    return definitions


def get_openai_tools() -> List[Dict[str, Any]]:
    """Get all tool definitions in OpenAI format."""
    return export_tool_definitions(format="openai")


def get_claude_tools() -> List[Dict[str, Any]]:
    """Get all tool definitions in Claude format."""
    return export_tool_definitions(format="claude")


# =============================================================================
# UNIFIED TOOL INTERFACE
# =============================================================================


class UnifiedToolInterface:
    """
    Unified interface for all ODA agent tools.

    Provides a single entry point for tool operations,
    routing requests to appropriate tools.

    Example:
        ```python
        interface = UnifiedToolInterface()

        # Query objects
        result = await interface.call(
            "object_query",
            operation="list",
            object_type="Task",
            filters={"status": "active"}
        )

        # Execute action
        result = await interface.call(
            "action_executor",
            operation="execute",
            action_type="file.read",
            params={"path": "/etc/config"}
        )
        ```
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Any] = {}

    def _get_tool(self, name: str) -> Any:
        """Get or create tool instance."""
        if name not in self._tools:
            self._tools[name] = get_tool(name)
        return self._tools[name]

    async def call(
        self,
        tool_name: str,
        operation: str,
        **params,
    ) -> Dict[str, Any]:
        """
        Call a tool operation.

        Args:
            tool_name: Name of the tool
            operation: Operation to perform
            **params: Operation parameters

        Returns:
            Operation result as dict
        """
        tool = self._get_tool(tool_name)

        if tool_name == "object_query":
            return await self._call_object_query(tool, operation, params)
        elif tool_name == "action_executor":
            return await self._call_action_executor(tool, operation, params)
        elif tool_name == "function_call":
            return self._call_function_call(tool, operation, params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _call_object_query(
        self,
        tool: ObjectQueryTool,
        operation: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Route object query operations."""
        if operation == "get":
            input_data = GetObjectInput(**params)
            result = await tool.get_object(input_data)
        elif operation == "list":
            input_data = ListObjectsInput(**params)
            result = await tool.list_objects(input_data)
        elif operation == "search":
            input_data = SearchObjectsInput(**params)
            result = await tool.search_objects(input_data)
        elif operation == "schema":
            result = tool.get_object_schema(params["object_type"])
        elif operation == "types":
            return {"types": tool.get_available_types()}
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return result.model_dump(exclude_none=True)

    async def _call_action_executor(
        self,
        tool: ActionExecutorTool,
        operation: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Route action executor operations."""
        if operation == "execute":
            input_data = ExecuteActionInput(**params)
            result = await tool.execute_action(input_data)
        elif operation == "list":
            input_data = ListActionsInput(**params)
            result = tool.list_actions(input_data)
        elif operation == "schema":
            input_data = GetActionSchemaInput(**params)
            result = tool.get_action_schema(input_data)
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return result.model_dump(exclude_none=True)

    def _call_function_call(
        self,
        tool: FunctionCallTool,
        operation: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Route function call operations."""
        if operation == "get_functions":
            functions = tool.get_all_functions(**params)
            return {"functions": [f.model_dump() for f in functions]}
        elif operation == "get_tools":
            tools = tool.get_all_tools(**params)
            return {"tools": [t.model_dump() for t in tools]}
        elif operation == "parse":
            result = tool.parse_function_call(params["raw_call"])
            return result.model_dump()
        elif operation == "validate":
            errors = tool.validate_arguments(
                params["action_type"],
                params["arguments"],
            )
            return {"valid": len(errors) == 0, "errors": errors}
        else:
            raise ValueError(f"Unknown operation: {operation}")


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Registry
    "ToolRegistry",
    "ToolMetadata",
    "get_registry",
    "get_tool",
    "get_all_tools",
    "list_tools",
    "register_tool",
    # Definition export
    "export_tool_definitions",
    "get_openai_tools",
    "get_claude_tools",
    # Unified interface
    "UnifiedToolInterface",
    # ObjectQueryTool
    "ObjectQueryTool",
    "GetObjectInput",
    "ListObjectsInput",
    "SearchObjectsInput",
    "ObjectQueryResult",
    "SchemaQueryResult",
    # ActionExecutorTool
    "ActionExecutorTool",
    "ExecuteActionInput",
    "GetActionSchemaInput",
    "ListActionsInput",
    "ActionExecutionResult",
    "ActionSchemaResult",
    "ActionListResult",
    # FunctionCallTool
    "FunctionCallTool",
    "FunctionDefinition",
    "ToolDefinition",
    "FunctionCallRequest",
    "FunctionCallResponse",
    "ActionToFunctionConverter",
    "ClaudeToolAdapter",
]
