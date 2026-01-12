"""
Orion ODA v4.0 - FunctionCallTool
=================================

OpenAI function calling format compatible wrapper for ODA actions.
Converts ODA action schemas to function call schemas and handles responses.

This module enables integration with:
- OpenAI Function Calling API
- Claude Tool Use
- Other LLM function calling interfaces
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import (
    ActionType,
    ActionRegistry,
    action_registry,
    RequiredField,
    MaxLength,
    AllowedValues,
    ArraySizeValidator,
    StringLengthValidator,
    RangeValidator,
)
from lib.oda.ontology.registry import get_registry

logger = logging.getLogger(__name__)


# =============================================================================
# FUNCTION CALL SCHEMAS
# =============================================================================


class FunctionParameter(BaseModel):
    """OpenAI-compatible function parameter definition."""

    type: str = Field(description="JSON Schema type")
    description: Optional[str] = Field(default=None)
    enum: Optional[List[str]] = Field(default=None)
    items: Optional[Dict[str, Any]] = Field(default=None)
    properties: Optional[Dict[str, Any]] = Field(default=None)
    required: Optional[List[str]] = Field(default=None)
    default: Optional[Any] = Field(default=None)
    minimum: Optional[float] = Field(default=None)
    maximum: Optional[float] = Field(default=None)
    minLength: Optional[int] = Field(default=None)
    maxLength: Optional[int] = Field(default=None)
    minItems: Optional[int] = Field(default=None)
    maxItems: Optional[int] = Field(default=None)


class FunctionDefinition(BaseModel):
    """OpenAI-compatible function definition."""

    name: str = Field(description="Function name (action api_name)")
    description: str = Field(description="Function description")
    parameters: Dict[str, Any] = Field(description="JSON Schema for parameters")


class ToolDefinition(BaseModel):
    """OpenAI-compatible tool definition."""

    type: str = Field(default="function")
    function: FunctionDefinition


class FunctionCallRequest(BaseModel):
    """Parsed function call request from LLM."""

    name: str = Field(description="Function name to call")
    arguments: Dict[str, Any] = Field(description="Function arguments")


class FunctionCallResponse(BaseModel):
    """Response to be sent back to LLM."""

    role: str = Field(default="tool")
    tool_call_id: Optional[str] = Field(default=None)
    name: str = Field(description="Function name")
    content: str = Field(description="JSON-encoded result")


# =============================================================================
# SCHEMA CONVERTER
# =============================================================================


class ActionToFunctionConverter:
    """
    Converts ODA ActionType schemas to OpenAI function calling format.

    Handles:
    - Parameter type mapping
    - Constraint extraction
    - Required field identification
    - Enum value extraction
    """

    # Python/Pydantic type to JSON Schema type mapping
    TYPE_MAP = {
        "str": "string",
        "string": "string",
        "int": "integer",
        "integer": "integer",
        "float": "number",
        "double": "number",
        "bool": "boolean",
        "boolean": "boolean",
        "list": "array",
        "array": "array",
        "dict": "object",
        "object": "object",
        "datetime": "string",
        "date": "string",
    }

    @classmethod
    def convert_action(cls, action_cls: Type[ActionType]) -> FunctionDefinition:
        """
        Convert an ActionType class to OpenAI function definition.

        Args:
            action_cls: ActionType class to convert

        Returns:
            FunctionDefinition compatible with OpenAI API
        """
        api_name = action_cls.api_name
        description = (action_cls.__doc__ or "").strip()

        # If no docstring, generate from name
        if not description:
            description = f"Execute {api_name} action"

        # Build parameters schema from submission_criteria
        parameters = cls._build_parameters_schema(action_cls)

        return FunctionDefinition(
            name=api_name,
            description=description,
            parameters=parameters,
        )

    @classmethod
    def _build_parameters_schema(cls, action_cls: Type[ActionType]) -> Dict[str, Any]:
        """Build JSON Schema for action parameters."""
        properties: Dict[str, Any] = {}
        required: List[str] = []
        constraints: Dict[str, Dict[str, Any]] = {}

        # Extract from submission_criteria
        criteria = getattr(action_cls, "submission_criteria", [])

        for criterion in criteria:
            if isinstance(criterion, RequiredField):
                required.append(criterion.field_name)
                if criterion.field_name not in properties:
                    properties[criterion.field_name] = {"type": "string"}

            elif isinstance(criterion, AllowedValues):
                if criterion.field_name not in properties:
                    properties[criterion.field_name] = {"type": "string"}
                properties[criterion.field_name]["enum"] = criterion.allowed

            elif isinstance(criterion, MaxLength):
                if criterion.field_name not in properties:
                    properties[criterion.field_name] = {"type": "string"}
                properties[criterion.field_name]["maxLength"] = criterion.max_length

            elif isinstance(criterion, StringLengthValidator):
                if criterion.field_name not in properties:
                    properties[criterion.field_name] = {"type": "string"}
                if criterion.min_length is not None:
                    properties[criterion.field_name]["minLength"] = criterion.min_length
                if criterion.max_length is not None:
                    properties[criterion.field_name]["maxLength"] = criterion.max_length

            elif isinstance(criterion, ArraySizeValidator):
                if criterion.field_name not in properties:
                    properties[criterion.field_name] = {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                if criterion.min_size is not None:
                    properties[criterion.field_name]["minItems"] = criterion.min_size
                if criterion.max_size is not None:
                    properties[criterion.field_name]["maxItems"] = criterion.max_size

            elif isinstance(criterion, RangeValidator):
                if criterion.field_name not in properties:
                    properties[criterion.field_name] = {"type": "number"}
                if criterion.min_value is not None:
                    properties[criterion.field_name]["minimum"] = criterion.min_value
                if criterion.max_value is not None:
                    properties[criterion.field_name]["maximum"] = criterion.max_value

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    @classmethod
    def convert_to_tool(cls, action_cls: Type[ActionType]) -> ToolDefinition:
        """Convert ActionType to OpenAI tool definition."""
        function_def = cls.convert_action(action_cls)
        return ToolDefinition(type="function", function=function_def)


# =============================================================================
# FUNCTION CALL TOOL
# =============================================================================


class FunctionCallTool:
    """
    OpenAI function calling format compatible tool wrapper.

    Provides:
    1. Schema export - Convert all ODA actions to function definitions
    2. Request parsing - Parse LLM function call requests
    3. Response formatting - Format results for LLM consumption

    Example Usage:
        ```python
        tool = FunctionCallTool()

        # Get all available functions for OpenAI
        functions = tool.get_all_functions()

        # Parse a function call from LLM
        request = tool.parse_function_call({
            "name": "file.read",
            "arguments": '{"path": "/etc/config.yaml"}'
        })

        # Execute and format response
        result = await executor.execute_action(request.name, request.arguments)
        response = tool.format_response(request.name, result)
        ```
    """

    TOOL_NAME = "function_call"
    TOOL_DESCRIPTION = (
        "Convert ODA actions to OpenAI function calling format "
        "for seamless LLM integration."
    )

    def __init__(self, registry: Optional[ActionRegistry] = None) -> None:
        """
        Initialize FunctionCallTool.

        Args:
            registry: ActionRegistry to use (defaults to global)
        """
        self._registry = registry or action_registry
        self._converter = ActionToFunctionConverter()
        self._function_cache: Dict[str, FunctionDefinition] = {}

    # =========================================================================
    # SCHEMA EXPORT
    # =========================================================================

    def get_function(self, action_type: str) -> Optional[FunctionDefinition]:
        """
        Get function definition for a specific action.

        Args:
            action_type: Action API name

        Returns:
            FunctionDefinition or None if not found
        """
        if action_type in self._function_cache:
            return self._function_cache[action_type]

        action_cls = self._registry.get(action_type)
        if not action_cls:
            return None

        func_def = self._converter.convert_action(action_cls)
        self._function_cache[action_type] = func_def
        return func_def

    def get_all_functions(
        self,
        namespace: Optional[str] = None,
        include_hazardous: bool = True,
    ) -> List[FunctionDefinition]:
        """
        Get all available functions as OpenAI-compatible definitions.

        Args:
            namespace: Optional namespace filter (e.g., 'file', 'llm')
            include_hazardous: Whether to include hazardous actions

        Returns:
            List of FunctionDefinition objects
        """
        functions = []
        hazardous = set(self._registry.get_hazardous_actions())

        for action_name in self._registry.list_actions():
            # Apply namespace filter
            if namespace and not action_name.startswith(namespace):
                continue

            # Apply hazardous filter
            if not include_hazardous and action_name in hazardous:
                continue

            func_def = self.get_function(action_name)
            if func_def:
                functions.append(func_def)

        return functions

    def get_all_tools(
        self,
        namespace: Optional[str] = None,
        include_hazardous: bool = True,
    ) -> List[ToolDefinition]:
        """
        Get all available tools in OpenAI tools format.

        Args:
            namespace: Optional namespace filter
            include_hazardous: Whether to include hazardous actions

        Returns:
            List of ToolDefinition objects
        """
        functions = self.get_all_functions(namespace, include_hazardous)
        return [
            ToolDefinition(type="function", function=func)
            for func in functions
        ]

    def export_to_json(self, path: Optional[str] = None) -> str:
        """
        Export all function definitions to JSON.

        Args:
            path: Optional file path to write to

        Returns:
            JSON string of function definitions
        """
        tools = self.get_all_tools()
        data = [tool.model_dump(exclude_none=True) for tool in tools]
        json_str = json.dumps(data, indent=2)

        if path:
            with open(path, "w") as f:
                f.write(json_str)

        return json_str

    # =========================================================================
    # REQUEST HANDLING
    # =========================================================================

    def parse_function_call(
        self, raw_call: Union[str, Dict[str, Any]]
    ) -> FunctionCallRequest:
        """
        Parse a function call from LLM output.

        Args:
            raw_call: Either a JSON string or dict with name and arguments

        Returns:
            FunctionCallRequest with parsed data

        Raises:
            ValueError: If parsing fails
        """
        # Parse JSON if string
        if isinstance(raw_call, str):
            try:
                raw_call = json.loads(raw_call)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in function call: {e}")

        # Extract name
        name = raw_call.get("name") or raw_call.get("function", {}).get("name")
        if not name:
            raise ValueError("Function call missing 'name' field")

        # Extract arguments
        arguments = raw_call.get("arguments") or raw_call.get(
            "function", {}
        ).get("arguments", {})

        # Parse arguments if string
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                # Some LLMs return non-JSON arguments
                arguments = {"raw": arguments}

        return FunctionCallRequest(name=name, arguments=arguments)

    def validate_arguments(
        self, action_type: str, arguments: Dict[str, Any]
    ) -> List[str]:
        """
        Validate function call arguments against schema.

        Args:
            action_type: Action API name
            arguments: Arguments to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        func_def = self.get_function(action_type)
        if not func_def:
            return [f"Unknown action: {action_type}"]

        errors = []
        params = func_def.parameters
        properties = params.get("properties", {})
        required = params.get("required", [])

        # Check required fields
        for field in required:
            if field not in arguments:
                errors.append(f"Missing required field: {field}")

        # Check field constraints
        for field, value in arguments.items():
            if field not in properties:
                errors.append(f"Unknown field: {field}")
                continue

            prop = properties[field]

            # Type checking (basic)
            expected_type = prop.get("type")
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"Field '{field}' must be an array")
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(f"Field '{field}' must be an object")

            # Enum checking
            if "enum" in prop and value not in prop["enum"]:
                errors.append(
                    f"Field '{field}' must be one of: {prop['enum']}"
                )

            # Length checking
            if isinstance(value, str):
                if "minLength" in prop and len(value) < prop["minLength"]:
                    errors.append(
                        f"Field '{field}' must be at least {prop['minLength']} characters"
                    )
                if "maxLength" in prop and len(value) > prop["maxLength"]:
                    errors.append(
                        f"Field '{field}' must be at most {prop['maxLength']} characters"
                    )

            # Range checking
            if isinstance(value, (int, float)):
                if "minimum" in prop and value < prop["minimum"]:
                    errors.append(
                        f"Field '{field}' must be >= {prop['minimum']}"
                    )
                if "maximum" in prop and value > prop["maximum"]:
                    errors.append(
                        f"Field '{field}' must be <= {prop['maximum']}"
                    )

        return errors

    # =========================================================================
    # RESPONSE FORMATTING
    # =========================================================================

    def format_response(
        self,
        function_name: str,
        result: Any,
        tool_call_id: Optional[str] = None,
    ) -> FunctionCallResponse:
        """
        Format action result as LLM-compatible function call response.

        Args:
            function_name: The called function name
            result: Action result (can be dict, Pydantic model, or primitive)
            tool_call_id: Optional tool call ID for OpenAI

        Returns:
            FunctionCallResponse ready for LLM
        """
        # Serialize result to JSON
        if hasattr(result, "model_dump"):
            content = result.model_dump(mode="json")
        elif hasattr(result, "to_dict"):
            content = result.to_dict()
        elif isinstance(result, dict):
            content = result
        else:
            content = {"result": result}

        # Handle datetime serialization
        content = self._serialize_for_json(content)

        return FunctionCallResponse(
            tool_call_id=tool_call_id,
            name=function_name,
            content=json.dumps(content),
        )

    def format_error(
        self,
        function_name: str,
        error: str,
        error_code: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> FunctionCallResponse:
        """
        Format error as LLM-compatible function call response.

        Args:
            function_name: The called function name
            error: Error message
            error_code: Optional error code
            tool_call_id: Optional tool call ID

        Returns:
            FunctionCallResponse with error information
        """
        content = {
            "success": False,
            "error": error,
        }
        if error_code:
            content["error_code"] = error_code

        return FunctionCallResponse(
            tool_call_id=tool_call_id,
            name=function_name,
            content=json.dumps(content),
        )

    def _serialize_for_json(self, obj: Any) -> Any:
        """Recursively serialize object for JSON."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj


# =============================================================================
# CLAUDE TOOL USE ADAPTER
# =============================================================================


class ClaudeToolAdapter:
    """
    Adapter for Claude's tool_use format.

    Claude uses a slightly different format than OpenAI:
    - tool_use blocks in messages
    - tool_result blocks for responses
    """

    @staticmethod
    def to_claude_tools(functions: List[FunctionDefinition]) -> List[Dict[str, Any]]:
        """
        Convert function definitions to Claude tool format.

        Args:
            functions: List of OpenAI-style function definitions

        Returns:
            List of Claude-style tool definitions
        """
        claude_tools = []
        for func in functions:
            claude_tools.append({
                "name": func.name,
                "description": func.description,
                "input_schema": func.parameters,
            })
        return claude_tools

    @staticmethod
    def parse_tool_use(tool_use_block: Dict[str, Any]) -> FunctionCallRequest:
        """
        Parse a Claude tool_use block.

        Args:
            tool_use_block: Claude tool_use content block

        Returns:
            FunctionCallRequest
        """
        return FunctionCallRequest(
            name=tool_use_block["name"],
            arguments=tool_use_block.get("input", {}),
        )

    @staticmethod
    def format_tool_result(
        tool_use_id: str,
        result: Any,
        is_error: bool = False,
    ) -> Dict[str, Any]:
        """
        Format result as Claude tool_result block.

        Args:
            tool_use_id: The tool_use block ID
            result: Result content
            is_error: Whether this is an error response

        Returns:
            Claude tool_result content block
        """
        if isinstance(result, str):
            content = result
        elif hasattr(result, "model_dump"):
            content = json.dumps(result.model_dump(mode="json"))
        elif isinstance(result, dict):
            content = json.dumps(result)
        else:
            content = str(result)

        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": content,
            "is_error": is_error,
        }


# =============================================================================
# TOOL EXPORT
# =============================================================================


def get_tool_definition() -> Dict[str, Any]:
    """Get OpenAI-compatible tool definition for FunctionCallTool itself."""
    return {
        "type": "function",
        "function": {
            "name": "get_oda_functions",
            "description": (
                "Get available ODA action functions for calling. "
                "Returns function definitions in OpenAI format."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Filter by action namespace (e.g., 'file', 'llm')",
                    },
                    "include_hazardous": {
                        "type": "boolean",
                        "description": "Include hazardous actions that require proposals",
                        "default": True,
                    },
                },
                "required": [],
            },
        },
    }
