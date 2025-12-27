from __future__ import annotations

from typing import Generic, List, TypeVar, Optional, Type, Any, Dict
from pydantic import BaseModel

from scripts.ontology.ontology_types import OntologyObject
# Circular import avoidance: Import Connector lazily or definition only
# from scripts.osdk.connector import DataConnector

T = TypeVar("T", bound=OntologyObject)


class PropertyFilter(BaseModel):
    property: str
    operator: str  # "eq", "gt", "contains", etc.
    value: Any


class ObjectQuery(Generic[T]):
    """
    Builder for querying Ontology Objects.
    Mimics Palantir OSDK fluent interface.
    """

    def __init__(self, object_type: Type[T], connector: Any = None):
        self.object_type = object_type
        self.connector = connector
        self._filters: List[PropertyFilter] = []
        self._selected_properties: List[str] = []
        self._order_by: Optional[Dict[str, str]] = None
        self._limit: int = 100

    def where(self, property: str, operator: str, value: Any) -> ObjectQuery[T]:
        """Add a filter condition."""
        self._filters.append(PropertyFilter(property=property, operator=operator, value=value))
        return self

    def select(self, *properties: str) -> ObjectQuery[T]:
        """Select specific properties to return."""
        self._selected_properties.extend(properties)
        return self

    def order_by(self, property: str, ascending: bool = True) -> ObjectQuery[T]:
        """Set ordering."""
        direction = "asc" if ascending else "desc"
        self._order_by = {"property": property, "direction": direction}
        return self

    def limit(self, n: int) -> ObjectQuery[T]:
        """Set result limit."""
        self._limit = n
        return self

    async def execute(self) -> List[T]:
        """
        Execute the query using the configured Connector.
        If no connector is set, tries to load the default SQLiteConnector.
        """
        if self.connector is None:
            from scripts.osdk.sqlite_connector import SQLiteConnector
            self.connector = SQLiteConnector()

        return await self.connector.query(
            object_type=self.object_type,
            filters=self._filters,
            selected_properties=self._selected_properties,
            order_by=self._order_by,
            limit=self._limit
        )
