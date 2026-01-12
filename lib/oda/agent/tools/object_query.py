"""
Orion ODA v4.0 - ObjectQueryTool
================================

Tool wrapper for querying ObjectTypes from the ontology.
Provides LLM-friendly interfaces for object discovery and retrieval.

This tool enables agents to:
- Get individual objects by ID
- List objects with filtering
- Search objects by criteria

All results are JSON-serializable for LLM consumption.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject, ObjectStatus
from lib.oda.ontology.registry import get_registry, ObjectDefinition

logger = logging.getLogger(__name__)


# =============================================================================
# INPUT MODELS (Pydantic validation for LLM inputs)
# =============================================================================


class GetObjectInput(BaseModel):
    """Input schema for get_object operation."""

    object_type: str = Field(
        ...,
        description="The ObjectType name (e.g., 'Task', 'Proposal')",
        min_length=1,
    )
    object_id: str = Field(
        ...,
        description="The unique ID of the object to retrieve",
        min_length=1,
    )

    @field_validator("object_type")
    @classmethod
    def validate_object_type(cls, v: str) -> str:
        """Validate that object_type is a valid identifier."""
        if not v[0].isupper():
            raise ValueError("object_type must be PascalCase (e.g., 'Task')")
        return v


class ListObjectsInput(BaseModel):
    """Input schema for list_objects operation."""

    object_type: str = Field(
        ...,
        description="The ObjectType name to list",
        min_length=1,
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filters as key-value pairs",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip (pagination)",
    )
    order_by: Optional[str] = Field(
        default=None,
        description="Field name to sort by",
    )
    order_direction: str = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction: 'asc' or 'desc'",
    )

    @field_validator("object_type")
    @classmethod
    def validate_object_type(cls, v: str) -> str:
        if not v[0].isupper():
            raise ValueError("object_type must be PascalCase")
        return v


class SearchObjectsInput(BaseModel):
    """Input schema for search_objects operation."""

    object_type: str = Field(
        ...,
        description="The ObjectType name to search",
        min_length=1,
    )
    query: str = Field(
        ...,
        description="Search query string",
        min_length=1,
    )
    search_fields: Optional[List[str]] = Field(
        default=None,
        description="Specific fields to search in (defaults to all string fields)",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of results",
    )


# =============================================================================
# OUTPUT MODELS (Structured responses for LLM)
# =============================================================================


class ObjectQueryResult(BaseModel):
    """Result of an object query operation."""

    success: bool = Field(description="Whether the operation succeeded")
    object_type: str = Field(description="The queried ObjectType")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The retrieved object data (if single object)",
    )
    objects: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of objects (if list/search operation)",
    )
    total_count: Optional[int] = Field(
        default=None,
        description="Total number of matching objects (for pagination)",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if operation failed",
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code",
    )

    def to_llm_format(self) -> Dict[str, Any]:
        """Convert to LLM-friendly format."""
        return self.model_dump(exclude_none=True)


class SchemaQueryResult(BaseModel):
    """Result of a schema query operation."""

    success: bool
    object_type: str
    schema: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# =============================================================================
# OBJECT QUERY TOOL
# =============================================================================


class ObjectQueryTool:
    """
    Tool wrapper for querying ObjectTypes from the ontology.

    This tool provides LLM agents with structured access to ontology data.
    All methods return JSON-serializable results suitable for LLM consumption.

    Example Usage:
        ```python
        tool = ObjectQueryTool()

        # Get a single object
        result = await tool.get_object(GetObjectInput(
            object_type="Task",
            object_id="abc-123"
        ))

        # List objects with filters
        result = await tool.list_objects(ListObjectsInput(
            object_type="Proposal",
            filters={"status": "pending"},
            limit=10
        ))

        # Search objects
        result = await tool.search_objects(SearchObjectsInput(
            object_type="Task",
            query="security audit"
        ))
        ```
    """

    # Tool metadata for LLM discovery
    TOOL_NAME = "object_query"
    TOOL_DESCRIPTION = (
        "Query ObjectTypes from the ODA ontology. "
        "Supports get by ID, list with filters, and search operations."
    )

    def __init__(self) -> None:
        """Initialize the ObjectQueryTool."""
        self._registry = get_registry()
        self._object_cache: Dict[str, Dict[str, OntologyObject]] = {}

    # =========================================================================
    # SCHEMA DISCOVERY
    # =========================================================================

    def get_available_types(self) -> List[str]:
        """
        List all available ObjectTypes in the ontology.

        Returns:
            List of ObjectType names
        """
        return list(self._registry.list_objects().keys())

    def get_object_schema(self, object_type: str) -> SchemaQueryResult:
        """
        Get the schema definition for an ObjectType.

        Args:
            object_type: Name of the ObjectType

        Returns:
            SchemaQueryResult with schema definition
        """
        objects = self._registry.list_objects()
        if object_type not in objects:
            return SchemaQueryResult(
                success=False,
                object_type=object_type,
                error=f"ObjectType '{object_type}' not found in registry",
            )

        obj_def = objects[object_type]
        schema = {
            "name": obj_def.name,
            "description": obj_def.description,
            "properties": {
                name: {
                    "type": prop.property_type.value,
                    "required": prop.required,
                    "description": prop.description,
                }
                for name, prop in obj_def.properties.items()
            },
            "links": {
                name: {
                    "target": link.target,
                    "cardinality": link.cardinality,
                    "description": link.description,
                }
                for name, link in obj_def.links.items()
            },
        }

        return SchemaQueryResult(
            success=True,
            object_type=object_type,
            schema=schema,
        )

    # =========================================================================
    # OBJECT RETRIEVAL
    # =========================================================================

    async def get_object(self, input_data: GetObjectInput) -> ObjectQueryResult:
        """
        Get a single object by ID.

        Args:
            input_data: Validated input with object_type and object_id

        Returns:
            ObjectQueryResult with the object data or error
        """
        try:
            # Validate object type exists
            available_types = self.get_available_types()
            if input_data.object_type not in available_types:
                return ObjectQueryResult(
                    success=False,
                    object_type=input_data.object_type,
                    error=f"ObjectType '{input_data.object_type}' not found. "
                    f"Available types: {available_types}",
                    error_code="OBJECT_TYPE_NOT_FOUND",
                )

            # Attempt to retrieve from storage
            obj = await self._fetch_object(
                input_data.object_type, input_data.object_id
            )

            if obj is None:
                return ObjectQueryResult(
                    success=False,
                    object_type=input_data.object_type,
                    error=f"Object '{input_data.object_id}' not found",
                    error_code="OBJECT_NOT_FOUND",
                )

            return ObjectQueryResult(
                success=True,
                object_type=input_data.object_type,
                data=self._serialize_object(obj),
            )

        except Exception as e:
            logger.exception(f"Error getting object: {input_data}")
            return ObjectQueryResult(
                success=False,
                object_type=input_data.object_type,
                error=str(e),
                error_code="QUERY_ERROR",
            )

    async def list_objects(self, input_data: ListObjectsInput) -> ObjectQueryResult:
        """
        List objects with optional filtering.

        Args:
            input_data: Validated input with filters and pagination

        Returns:
            ObjectQueryResult with list of objects
        """
        try:
            # Validate object type
            available_types = self.get_available_types()
            if input_data.object_type not in available_types:
                return ObjectQueryResult(
                    success=False,
                    object_type=input_data.object_type,
                    error=f"ObjectType '{input_data.object_type}' not found",
                    error_code="OBJECT_TYPE_NOT_FOUND",
                )

            # Fetch objects
            objects = await self._fetch_objects(
                object_type=input_data.object_type,
                filters=input_data.filters,
                limit=input_data.limit,
                offset=input_data.offset,
                order_by=input_data.order_by,
                order_direction=input_data.order_direction,
            )

            total = await self._count_objects(
                input_data.object_type, input_data.filters
            )

            return ObjectQueryResult(
                success=True,
                object_type=input_data.object_type,
                objects=[self._serialize_object(obj) for obj in objects],
                total_count=total,
            )

        except Exception as e:
            logger.exception(f"Error listing objects: {input_data}")
            return ObjectQueryResult(
                success=False,
                object_type=input_data.object_type,
                error=str(e),
                error_code="QUERY_ERROR",
            )

    async def search_objects(self, input_data: SearchObjectsInput) -> ObjectQueryResult:
        """
        Search objects by text query.

        Args:
            input_data: Validated input with search query

        Returns:
            ObjectQueryResult with matching objects
        """
        try:
            # Validate object type
            available_types = self.get_available_types()
            if input_data.object_type not in available_types:
                return ObjectQueryResult(
                    success=False,
                    object_type=input_data.object_type,
                    error=f"ObjectType '{input_data.object_type}' not found",
                    error_code="OBJECT_TYPE_NOT_FOUND",
                )

            # Perform search
            objects = await self._search_objects(
                object_type=input_data.object_type,
                query=input_data.query,
                search_fields=input_data.search_fields,
                limit=input_data.limit,
            )

            return ObjectQueryResult(
                success=True,
                object_type=input_data.object_type,
                objects=[self._serialize_object(obj) for obj in objects],
                total_count=len(objects),
            )

        except Exception as e:
            logger.exception(f"Error searching objects: {input_data}")
            return ObjectQueryResult(
                success=False,
                object_type=input_data.object_type,
                error=str(e),
                error_code="SEARCH_ERROR",
            )

    # =========================================================================
    # PRIVATE METHODS (Storage abstraction)
    # =========================================================================

    async def _fetch_object(
        self, object_type: str, object_id: str
    ) -> Optional[OntologyObject]:
        """
        Fetch a single object from storage.

        Override this method to integrate with actual storage backend.
        """
        # Default implementation uses cache (in-memory)
        type_cache = self._object_cache.get(object_type, {})
        return type_cache.get(object_id)

    async def _fetch_objects(
        self,
        object_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
    ) -> List[OntologyObject]:
        """
        Fetch multiple objects with filtering.

        Override this method to integrate with actual storage backend.
        """
        type_cache = self._object_cache.get(object_type, {})
        objects = list(type_cache.values())

        # Apply filters
        if filters:
            objects = [
                obj
                for obj in objects
                if all(
                    getattr(obj, k, None) == v
                    for k, v in filters.items()
                )
            ]

        # Apply sorting
        if order_by:
            reverse = order_direction == "desc"
            objects.sort(
                key=lambda o: getattr(o, order_by, None) or "",
                reverse=reverse,
            )

        # Apply pagination
        return objects[offset : offset + limit]

    async def _count_objects(
        self, object_type: str, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count objects matching filters."""
        type_cache = self._object_cache.get(object_type, {})
        objects = list(type_cache.values())

        if filters:
            objects = [
                obj
                for obj in objects
                if all(
                    getattr(obj, k, None) == v
                    for k, v in filters.items()
                )
            ]

        return len(objects)

    async def _search_objects(
        self,
        object_type: str,
        query: str,
        search_fields: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[OntologyObject]:
        """
        Search objects by text query.

        Override this method to integrate with actual search backend.
        """
        type_cache = self._object_cache.get(object_type, {})
        objects = list(type_cache.values())
        query_lower = query.lower()

        # Get string fields if not specified
        if search_fields is None:
            schema = self.get_object_schema(object_type)
            if schema.schema:
                search_fields = [
                    name
                    for name, prop in schema.schema.get("properties", {}).items()
                    if prop.get("type") == "string"
                ]
            else:
                search_fields = []

        # Simple text matching
        results = []
        for obj in objects:
            for field in search_fields:
                value = getattr(obj, field, None)
                if value and isinstance(value, str):
                    if query_lower in value.lower():
                        results.append(obj)
                        break

        return results[:limit]

    def _serialize_object(self, obj: OntologyObject) -> Dict[str, Any]:
        """Serialize an OntologyObject to JSON-compatible dict."""
        data = obj.model_dump(mode="json")

        # Convert enum values to strings
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat()

        return data

    # =========================================================================
    # CACHE MANAGEMENT (for testing/development)
    # =========================================================================

    def register_object(self, obj: OntologyObject) -> None:
        """
        Register an object in the cache.

        This is useful for testing and development.
        In production, objects would be stored in a database.
        """
        type_name = obj.__class__.__name__
        if type_name not in self._object_cache:
            self._object_cache[type_name] = {}
        self._object_cache[type_name][obj.id] = obj

    def clear_cache(self, object_type: Optional[str] = None) -> None:
        """Clear the object cache."""
        if object_type:
            self._object_cache.pop(object_type, None)
        else:
            self._object_cache.clear()


# =============================================================================
# TOOL EXPORT (for LLM function calling)
# =============================================================================


def get_tool_definition() -> Dict[str, Any]:
    """
    Get the OpenAI-compatible tool definition for ObjectQueryTool.

    Returns:
        Tool definition dict for function calling
    """
    return {
        "type": "function",
        "function": {
            "name": "object_query",
            "description": ObjectQueryTool.TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["get", "list", "search", "schema"],
                        "description": "The query operation to perform",
                    },
                    "object_type": {
                        "type": "string",
                        "description": "The ObjectType name (e.g., 'Task', 'Proposal')",
                    },
                    "object_id": {
                        "type": "string",
                        "description": "Object ID (required for 'get' operation)",
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filter criteria for 'list' operation",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for 'search' operation",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 100,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Results to skip (pagination)",
                        "default": 0,
                    },
                },
                "required": ["operation", "object_type"],
            },
        },
    }
