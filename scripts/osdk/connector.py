from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Type, Any, Optional, Dict, TypeVar

from scripts.ontology.ontology_types import OntologyObject

T = TypeVar("T", bound=OntologyObject)

class DataConnector(ABC):
    """
    Abstract Base Class for OSDK Data Connectors.
    Bridges the Query Builder API to actual storage backends.
    """

    @abstractmethod
    async def query(
        self, 
        object_type: Type[T], 
        filters: List[Any], 
        selected_properties: List[str],
        order_by: Optional[Dict[str, str]],
        limit: int
    ) -> List[T]:
        """
        Execute a query against the backend.
        
        Args:
            object_type: The Pydantic model class (Domain Object)
            filters: List of PropertyFilter objects
            selected_properties: List of field names to fetch
            order_by: Dict with 'property' and 'direction'
            limit: Max results
            
        Returns:
            List of domain objects
        """
        ...
    
    @abstractmethod
    async def get_by_id(self, object_type: Type[T], object_id: str) -> Optional[T]:
        """Fetch a single object by ID."""
        ...
