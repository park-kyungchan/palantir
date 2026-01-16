from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterable

class DataSource(ABC):
    """
    Abstract Base Class for Data Integration Sources.
    Represents a connection to an external data system (File, DB, API).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source."""
        pass

    @abstractmethod
    async def read(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Read data from the source.
        Returns a list of dictionaries (records).
        """
        pass

    @abstractmethod
    async def write(self, data: List[Dict[str, Any]], **kwargs) -> None:
        """
        Write data to the source.
        """
        pass
