# adapters/repository/base.py
"""
Abstract Repository Base Classes (ODA-Aligned)

This module defines the abstract repository interface following:
1. Palantir ODA DAO patterns (UserDao, WorldDao interfaces)
2. Clean Architecture's repository pattern
3. Python Generic typing for type safety

Key Design Decisions:
- Generic[T] enables type-safe operations across entity types
- All methods are async for I/O-bound operations
- Pydantic BaseModel constraint ensures serializable entities
- Optional return types model absence without exceptions

References:
- Palantir Foundry Developer Foundations (FoundryClient pattern)
- Orion ODA v3.6 ProposalRepository pattern
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel
from datetime import datetime


# Type variable bound to Pydantic BaseModel for serialization
T = TypeVar('T', bound=BaseModel)


class Repository(ABC, Generic[T]):
    """
    Abstract Repository interface for domain entity persistence.
    
    This interface mirrors Palantir's DAO pattern used in OSDK:
    - Strongly typed entity operations
    - Async-first design for scalability
    - CRUD + query operations
    
    Implementations should handle:
    - Connection management
    - Transaction boundaries
    - Error translation to domain exceptions
    
    Example:
        class UserRepository(Repository[User]):
            async def save(self, entity: User) -> User: ...
    """
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Persist an entity (create or update).
        
        If entity exists (by ID), updates it.
        If entity doesn't exist, creates it.
        
        Args:
            entity: The domain entity to persist
            
        Returns:
            The persisted entity (may have updated timestamps)
            
        Raises:
            RepositoryError: On persistence failure
        """
        ...
    
    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by its primary identifier.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        ...
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Retrieve all entities with pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities (may be empty)
        """
        ...
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        Remove an entity by ID.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            True if entity was deleted, False if not found
        """
        ...
    
    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists without loading it.
        
        More efficient than find_by_id() when you only need existence check.
        
        Args:
            entity_id: The unique identifier to check
            
        Returns:
            True if entity exists, False otherwise
        """
        ...
    
    @abstractmethod
    async def count(self) -> int:
        """
        Count total number of entities.
        
        Returns:
            Total count of entities in the repository
        """
        ...


class AuditableRepository(Repository[T]):
    """
    Extended repository with audit trail support.
    
    This mirrors Orion ODA's Proposal history pattern where
    all state transitions are recorded for audit purposes.
    
    Use this for entities requiring:
    - Change tracking
    - Compliance requirements
    - Version history
    """
    
    @abstractmethod
    async def find_history(self, entity_id: str) -> List[dict[str, Any]]:
        """
        Retrieve the change history for an entity.
        
        Args:
            entity_id: The entity to get history for
            
        Returns:
            List of historical records with timestamps
        """
        ...
    
    @abstractmethod
    async def find_at_timestamp(self, entity_id: str, timestamp: datetime) -> Optional[T]:
        """
        Retrieve entity state at a specific point in time.
        
        Args:
            entity_id: The entity identifier
            timestamp: Point in time to retrieve state for
            
        Returns:
            Entity state at that timestamp, or None
        """
        ...


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an expected entity is not found."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} not found: {entity_id}")


class ConcurrencyError(RepositoryError):
    """Raised on optimistic locking failures (stale data)."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"Concurrent modification detected for {entity_type}: {entity_id}")
