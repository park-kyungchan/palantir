"""
ODA Semantic Layer - Vector Store (Phase 4.2).

This module provides abstract interfaces and implementations for vector storage.
Supports multiple backends: SQLite-VSS, ChromaDB, in-memory.

Components:
- VectorRecord: A vector record with metadata
- SearchResult: Result from similarity search
- VectorStoreConfig: Configuration for vector stores
- VectorStore: Abstract base class for vector storage
- InMemoryVectorStore: In-memory implementation for testing

Usage:
    from lib.oda.semantic.vector_store import VectorStore, VectorRecord
    from lib.oda.semantic.stores.sqlite_vss import SQLiteVSSStore

    store = SQLiteVSSStore(db_path="vectors.db", dimension=384)
    await store.add("doc1", vector, metadata={"type": "document"})
    results = await store.search(query_vector, k=10)
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator


class DistanceMetric(str, Enum):
    """Distance metrics for vector similarity."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


class VectorStoreConfig(BaseModel):
    """Configuration for vector stores."""

    dimension: int = Field(
        ...,
        ge=1,
        description="Dimension of vectors to store"
    )
    metric: DistanceMetric = Field(
        default=DistanceMetric.COSINE,
        description="Distance metric for similarity"
    )
    normalize_vectors: bool = Field(
        default=True,
        description="Normalize vectors before storage"
    )
    index_type: str = Field(
        default="flat",
        description="Index type (flat, ivf, hnsw)"
    )
    ef_construction: int = Field(
        default=200,
        ge=1,
        description="HNSW construction parameter"
    )
    ef_search: int = Field(
        default=100,
        ge=1,
        description="HNSW search parameter"
    )
    m: int = Field(
        default=16,
        ge=2,
        description="HNSW M parameter"
    )
    nlist: int = Field(
        default=100,
        ge=1,
        description="IVF nlist parameter"
    )


class VectorRecord(BaseModel):
    """Record stored in vector store."""

    id: str = Field(
        ...,
        description="Unique identifier"
    )
    vector: List[float] = Field(
        ...,
        description="Embedding vector"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    text: Optional[str] = Field(
        default=None,
        description="Original text content"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )

    @property
    def dimension(self) -> int:
        """Get vector dimension."""
        return len(self.vector)


# Alias for backward compatibility
SearchResult = "VectorSearchResult"


class VectorSearchResult(BaseModel):
    """Result from vector similarity search."""

    id: str = Field(
        ...,
        description="Record identifier"
    )
    score: float = Field(
        ...,
        description="Similarity score (higher is more similar)"
    )
    distance: Optional[float] = Field(
        default=None,
        description="Raw distance value"
    )
    vector: Optional[List[float]] = Field(
        default=None,
        description="The vector (if requested)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Record metadata"
    )
    text: Optional[str] = Field(
        default=None,
        description="Original text content"
    )

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is in valid range."""
        return max(0.0, min(1.0, v))


class FilterOperator(str, Enum):
    """Filter operators for metadata queries."""
    EQ = "eq"      # Equal
    NE = "ne"      # Not equal
    GT = "gt"      # Greater than
    GTE = "gte"    # Greater than or equal
    LT = "lt"      # Less than
    LTE = "lte"    # Less than or equal
    IN = "in"      # In list
    NIN = "nin"    # Not in list
    CONTAINS = "contains"  # String contains


class MetadataFilter(BaseModel):
    """Filter for metadata queries."""
    field: str = Field(..., description="Metadata field name")
    operator: FilterOperator = Field(
        default=FilterOperator.EQ,
        description="Comparison operator"
    )
    value: Any = Field(..., description="Value to compare")

    def matches(self, metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches this filter."""
        if self.field not in metadata:
            return self.operator == FilterOperator.NE

        field_value = metadata[self.field]

        if self.operator == FilterOperator.EQ:
            return field_value == self.value
        elif self.operator == FilterOperator.NE:
            return field_value != self.value
        elif self.operator == FilterOperator.GT:
            return field_value > self.value
        elif self.operator == FilterOperator.GTE:
            return field_value >= self.value
        elif self.operator == FilterOperator.LT:
            return field_value < self.value
        elif self.operator == FilterOperator.LTE:
            return field_value <= self.value
        elif self.operator == FilterOperator.IN:
            return field_value in self.value
        elif self.operator == FilterOperator.NIN:
            return field_value not in self.value
        elif self.operator == FilterOperator.CONTAINS:
            return self.value in str(field_value)

        return False


class VectorStore(ABC):
    """
    Abstract base class for vector storage backends.

    Implementations must provide methods for adding, searching, and managing
    vectors with associated metadata.

    Example usage:
        from lib.oda.semantic.stores.sqlite_vss import SQLiteVSSStore

        store = SQLiteVSSStore(db_path="vectors.db", dimension=384)
        await store.add("doc1", vector, metadata={"type": "document"})
        results = await store.search(query_vector, k=10)
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None):
        """
        Initialize the vector store.

        Args:
            config: Optional configuration
        """
        self._config = config

    @property
    def config(self) -> Optional[VectorStoreConfig]:
        """Get store configuration."""
        return self._config

    @abstractmethod
    async def add(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> None:
        """
        Add a vector to the store.

        Args:
            id: Unique identifier
            vector: Embedding vector
            metadata: Optional metadata dictionary
            text: Optional original text
        """
        pass

    @abstractmethod
    async def add_batch(self, records: List[VectorRecord]) -> int:
        """
        Add multiple vectors to the store.

        Args:
            records: List of VectorRecord objects

        Returns:
            Number of records successfully added
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        k: int = 10,
        filters: Optional[Union[Dict[str, Any], List[MetadataFilter]]] = None,
        include_vectors: bool = False,
        include_metadata: bool = True,
        score_threshold: Optional[float] = None
    ) -> List[VectorSearchResult]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            filters: Metadata filters (dict for simple eq, or list of MetadataFilter)
            include_vectors: Whether to include vectors in results
            include_metadata: Whether to include metadata in results
            score_threshold: Minimum score threshold

        Returns:
            List of VectorSearchResult sorted by similarity
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[VectorRecord]:
        """
        Get a specific vector by ID.

        Args:
            id: Vector identifier

        Returns:
            VectorRecord if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_batch(self, ids: List[str]) -> List[VectorRecord]:
        """
        Get multiple vectors by IDs.

        Args:
            ids: List of vector identifiers

        Returns:
            List of found VectorRecords
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete a vector by ID.

        Args:
            id: Vector identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def delete_batch(self, ids: List[str]) -> int:
        """
        Delete multiple vectors by IDs.

        Args:
            ids: List of vector identifiers

        Returns:
            Number of records deleted
        """
        pass

    @abstractmethod
    async def update(
        self,
        id: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> bool:
        """
        Update an existing vector.

        Args:
            id: Vector identifier
            vector: New vector (optional)
            metadata: New metadata (optional)
            text: New text (optional)

        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Count total vectors in store.

        Returns:
            Total number of vectors
        """
        pass

    async def exists(self, id: str) -> bool:
        """
        Check if a vector exists.

        Args:
            id: Vector identifier

        Returns:
            True if exists
        """
        return await self.get(id) is not None

    async def upsert(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> bool:
        """
        Insert or update a vector.

        Args:
            id: Vector identifier
            vector: Embedding vector
            metadata: Optional metadata
            text: Optional text

        Returns:
            True if inserted, False if updated
        """
        exists = await self.exists(id)
        if exists:
            await self.update(id, vector, metadata, text)
            return False
        else:
            await self.add(id, vector, metadata, text)
            return True

    async def close(self) -> None:
        """Close the store and release resources."""
        pass

    async def __aenter__(self) -> "VectorStore":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


class InMemoryVectorStore(VectorStore):
    """
    In-memory vector store for testing and small datasets.

    Uses brute-force search with configurable distance metric.
    Not suitable for large datasets.
    """

    def __init__(
        self,
        config: Optional[VectorStoreConfig] = None,
        dimension: Optional[int] = None
    ):
        """
        Initialize in-memory vector store.

        Args:
            config: Optional configuration
            dimension: Vector dimension (can also be in config)
        """
        if config is None and dimension is not None:
            config = VectorStoreConfig(dimension=dimension)
        super().__init__(config)
        self._vectors: Dict[str, VectorRecord] = {}

    async def add(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> None:
        """Add a vector to the store."""
        # Validate dimension
        if self._config and len(vector) != self._config.dimension:
            raise ValueError(
                f"Vector dimension {len(vector)} does not match "
                f"store dimension {self._config.dimension}"
            )

        # Normalize if configured
        if self._config and self._config.normalize_vectors:
            vector = _normalize_vector(vector)

        self._vectors[id] = VectorRecord(
            id=id,
            vector=vector,
            metadata=metadata or {},
            text=text
        )

    async def add_batch(self, records: List[VectorRecord]) -> int:
        """Add multiple vectors."""
        for record in records:
            vector = record.vector
            if self._config and self._config.normalize_vectors:
                vector = _normalize_vector(vector)

            self._vectors[record.id] = VectorRecord(
                id=record.id,
                vector=vector,
                metadata=record.metadata,
                text=record.text,
                created_at=record.created_at
            )
        return len(records)

    async def search(
        self,
        query_vector: List[float],
        k: int = 10,
        filters: Optional[Union[Dict[str, Any], List[MetadataFilter]]] = None,
        include_vectors: bool = False,
        include_metadata: bool = True,
        score_threshold: Optional[float] = None
    ) -> List[VectorSearchResult]:
        """Search using configurable distance metric."""
        # Normalize query if configured
        if self._config and self._config.normalize_vectors:
            query_vector = _normalize_vector(query_vector)

        # Convert dict filters to MetadataFilter list
        if isinstance(filters, dict):
            filters = [
                MetadataFilter(field=k, value=v)
                for k, v in filters.items()
            ]

        # Get distance function
        metric = self._config.metric if self._config else DistanceMetric.COSINE
        distance_fn = _get_distance_function(metric)

        results = []
        for record in self._vectors.values():
            # Apply filters
            if filters:
                if not all(f.matches(record.metadata) for f in filters):
                    continue

            # Calculate distance and score
            distance = distance_fn(query_vector, record.vector)
            score = _distance_to_score(distance, metric)

            # Apply threshold
            if score_threshold is not None and score < score_threshold:
                continue

            results.append(VectorSearchResult(
                id=record.id,
                score=score,
                distance=distance,
                vector=record.vector if include_vectors else None,
                metadata=record.metadata if include_metadata else {},
                text=record.text
            ))

        # Sort by score descending and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    async def get(self, id: str) -> Optional[VectorRecord]:
        """Get a specific vector."""
        return self._vectors.get(id)

    async def get_batch(self, ids: List[str]) -> List[VectorRecord]:
        """Get multiple vectors."""
        return [
            self._vectors[id] for id in ids
            if id in self._vectors
        ]

    async def delete(self, id: str) -> bool:
        """Delete a vector."""
        if id in self._vectors:
            del self._vectors[id]
            return True
        return False

    async def delete_batch(self, ids: List[str]) -> int:
        """Delete multiple vectors."""
        deleted = 0
        for id in ids:
            if id in self._vectors:
                del self._vectors[id]
                deleted += 1
        return deleted

    async def update(
        self,
        id: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> bool:
        """Update an existing vector."""
        if id not in self._vectors:
            return False

        record = self._vectors[id]

        if vector is not None:
            if self._config and self._config.normalize_vectors:
                vector = _normalize_vector(vector)
            record.vector = vector

        if metadata is not None:
            record.metadata.update(metadata)

        if text is not None:
            record.text = text

        record.updated_at = datetime.now(timezone.utc)
        return True

    async def count(self) -> int:
        """Count vectors."""
        return len(self._vectors)

    async def clear(self) -> None:
        """Clear all vectors."""
        self._vectors.clear()


# ============================================================================
# Utility Functions
# ============================================================================


def _normalize_vector(vector: List[float]) -> List[float]:
    """Normalize a vector to unit length."""
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude == 0:
        return vector
    return [v / magnitude for v in vector]


def _cosine_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine distance (1 - cosine_similarity)."""
    if len(vec1) != len(vec2):
        return 1.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 1.0

    similarity = dot_product / (magnitude1 * magnitude2)
    return 1.0 - similarity


def _euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Euclidean distance."""
    if len(vec1) != len(vec2):
        return float("inf")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def _dot_product_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate negative dot product (for similarity ranking)."""
    if len(vec1) != len(vec2):
        return float("inf")
    return -sum(a * b for a, b in zip(vec1, vec2))


def _manhattan_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Manhattan (L1) distance."""
    if len(vec1) != len(vec2):
        return float("inf")
    return sum(abs(a - b) for a, b in zip(vec1, vec2))


def _get_distance_function(metric: DistanceMetric) -> Callable:
    """Get the distance function for a metric."""
    return {
        DistanceMetric.COSINE: _cosine_distance,
        DistanceMetric.EUCLIDEAN: _euclidean_distance,
        DistanceMetric.DOT_PRODUCT: _dot_product_distance,
        DistanceMetric.MANHATTAN: _manhattan_distance,
    }[metric]


def _distance_to_score(distance: float, metric: DistanceMetric) -> float:
    """Convert distance to similarity score (0-1, higher is better)."""
    if metric == DistanceMetric.COSINE:
        # Cosine distance is already 0-2, convert to 0-1 score
        return max(0.0, 1.0 - distance)
    elif metric == DistanceMetric.DOT_PRODUCT:
        # Dot product was negated, so negate again and normalize
        # Assuming vectors are normalized, dot product is in [-1, 1]
        return ((-distance) + 1.0) / 2.0
    else:
        # For Euclidean and Manhattan, use exponential decay
        return math.exp(-distance)


class VectorStoreError(Exception):
    """Base exception for vector store operations."""
    pass


class VectorNotFoundError(VectorStoreError):
    """Vector not found in store."""
    pass


class VectorDimensionError(VectorStoreError):
    """Vector dimension mismatch."""
    pass
