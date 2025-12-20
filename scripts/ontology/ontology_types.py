
from typing import Type, TypeVar, List, Optional, Any, Generic, Dict, Callable
from abc import ABC, abstractmethod
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, PrivateAttr

T = TypeVar('T')

class Property(Generic[T]):
    """
    Represents a Palantir Ontology Property.
    Holds metadata like 'display_name', 'description', 'type'.
    """
    def __init__(self, type_: Type[T], display_name: str, description: str = ""):
        self.type = type_
        self.display_name = display_name
        self.description = description

class Link(Generic[T]):
    """
    Represents a LinkType (Relationship).
    Cardinality: 1:1, 1:N, N:N managed by the Semantic Engine.
    """
    def __init__(self, target: Type[T], link_type_id: str, cardinality: str = "ONE_TO_MANY"):
        self.target = target
        self.link_type_id = link_type_id
        self.cardinality = cardinality

class BaseObject(BaseModel):
    """
    The atom of the Ontology.
    Uses Pydantic for schema validation (Sufficient Implementation).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Primary Key (UUIDv7-like)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata for the ObjectType
    _title_key: str = PrivateAttr(default="id")
    
    class Config:
        validate_assignment = True

    def get_title(self) -> str:
        return getattr(self, self._title_key, self.id)
