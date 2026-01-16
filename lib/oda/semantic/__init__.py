"""
ODA Semantic Layer - Vector Embeddings and Semantic Search (Phase 4.1-4.2).

This module provides semantic search capabilities using vector embeddings,
with support for multiple embedding providers and vector storage backends.

Phase 4.1 - Embedding Infrastructure:
- EmbeddingProvider: Abstract interface for embedding generation
- EmbeddingConfig: Configuration for embedding providers
- EmbeddingResult: Result of an embedding operation
- EmbeddingCache: Caching layer for embedding results
- OpenAIEmbeddingProvider: OpenAI API embeddings
- LocalEmbeddingProvider: Local sentence-transformers models

Phase 4.2 - Vector Storage:
- VectorStore: Abstract interface for vector storage
- VectorRecord: Record stored in vector store
- VectorSearchResult: Result from similarity search
- SQLiteVSSStore: SQLite with VSS extension
- ChromaDBStore: ChromaDB vector database
- VectorIndexManager: Index management for vector stores

Usage:
    from lib.oda.semantic import (
        EmbeddingConfig,
        EmbeddingCache,
        VectorStore,
        VectorIndexManager,
    )
    from lib.oda.semantic.providers import OpenAIEmbeddingProvider, LocalEmbeddingProvider
    from lib.oda.semantic.stores import SQLiteVSSStore, ChromaDBStore
"""

# Phase 4.1: Embedding Infrastructure
from lib.oda.semantic.embedding import (
    EmbeddingProvider,
    EmbeddingConfig,
    EmbeddingResult,
    EmbeddingVector,  # Alias for backward compatibility
    EmbeddingBatchResult,
    EmbeddingModel,
    EmbeddingError,
    EmbeddingRateLimitError,
    EmbeddingTokenLimitError,
    EmbeddingConnectionError,
    EmbeddingValidationError,
    MockEmbeddingProvider,
    MODEL_DIMENSIONS,
    MODEL_MAX_TOKENS,
)

from lib.oda.semantic.cache import (
    EmbeddingCache,
    CacheConfig,
    CacheStats,
    CachedEmbeddingProvider,
)

# Phase 4.2: Vector Storage
from lib.oda.semantic.vector_store import (
    VectorStore,
    VectorStoreConfig,
    VectorRecord,
    VectorSearchResult,
    MetadataFilter,
    FilterOperator,
    DistanceMetric,
    InMemoryVectorStore,
    VectorStoreError,
    VectorNotFoundError,
    VectorDimensionError,
)

from lib.oda.semantic.indexing import (
    VectorIndexManager,
    IndexConfig,
    IndexStats,
    IndexType,
    IndexState,
    IndexBuilder,
)

__all__ = [
    # Phase 4.1: Embedding Infrastructure
    "EmbeddingProvider",
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingVector",
    "EmbeddingBatchResult",
    "EmbeddingModel",
    "EmbeddingError",
    "EmbeddingRateLimitError",
    "EmbeddingTokenLimitError",
    "EmbeddingConnectionError",
    "EmbeddingValidationError",
    "MockEmbeddingProvider",
    "MODEL_DIMENSIONS",
    "MODEL_MAX_TOKENS",
    # Cache
    "EmbeddingCache",
    "CacheConfig",
    "CacheStats",
    "CachedEmbeddingProvider",
    # Phase 4.2: Vector Storage
    "VectorStore",
    "VectorStoreConfig",
    "VectorRecord",
    "VectorSearchResult",
    "MetadataFilter",
    "FilterOperator",
    "DistanceMetric",
    "InMemoryVectorStore",
    "VectorStoreError",
    "VectorNotFoundError",
    "VectorDimensionError",
    # Indexing
    "VectorIndexManager",
    "IndexConfig",
    "IndexStats",
    "IndexType",
    "IndexState",
    "IndexBuilder",
]

__version__ = "4.1.0"
