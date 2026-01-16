"""
ODA Semantic Layer - Embedding Provider (Phase 4.1).

This module provides abstract interfaces and implementations for embedding generation.
Supports multiple providers: OpenAI, local sentence-transformers models.

Components:
- EmbeddingConfig: Configuration for embedding providers
- EmbeddingResult: Result of an embedding operation
- EmbeddingProvider: Abstract base class for embedding providers
- MockEmbeddingProvider: Mock provider for testing

Usage:
    from lib.oda.semantic.embedding import EmbeddingProvider, EmbeddingConfig
    from lib.oda.semantic.providers.openai import OpenAIEmbeddingProvider

    config = EmbeddingConfig(model_name="text-embedding-3-small")
    provider = OpenAIEmbeddingProvider(config)
    result = await provider.embed("Hello, world!")
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class EmbeddingModel(str, Enum):
    """Standard embedding model identifiers."""
    # OpenAI models
    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    # Local sentence-transformers models
    MINILM_L6_V2 = "all-MiniLM-L6-v2"
    MPNET_BASE_V2 = "all-mpnet-base-v2"
    BGE_SMALL_EN = "BAAI/bge-small-en-v1.5"
    BGE_BASE_EN = "BAAI/bge-base-en-v1.5"
    # Mock/Testing
    MOCK = "mock-embedding"


# Model dimension mappings
MODEL_DIMENSIONS: Dict[str, int] = {
    EmbeddingModel.OPENAI_ADA_002.value: 1536,
    EmbeddingModel.OPENAI_3_SMALL.value: 1536,
    EmbeddingModel.OPENAI_3_LARGE.value: 3072,
    EmbeddingModel.MINILM_L6_V2.value: 384,
    EmbeddingModel.MPNET_BASE_V2.value: 768,
    EmbeddingModel.BGE_SMALL_EN.value: 384,
    EmbeddingModel.BGE_BASE_EN.value: 768,
    EmbeddingModel.MOCK.value: 384,
}

# Model max tokens mappings
MODEL_MAX_TOKENS: Dict[str, int] = {
    EmbeddingModel.OPENAI_ADA_002.value: 8191,
    EmbeddingModel.OPENAI_3_SMALL.value: 8191,
    EmbeddingModel.OPENAI_3_LARGE.value: 8191,
    EmbeddingModel.MINILM_L6_V2.value: 512,
    EmbeddingModel.MPNET_BASE_V2.value: 512,
    EmbeddingModel.BGE_SMALL_EN.value: 512,
    EmbeddingModel.BGE_BASE_EN.value: 512,
    EmbeddingModel.MOCK.value: 8191,
}


class EmbeddingConfig(BaseModel):
    """Configuration for embedding provider."""

    model_name: str = Field(
        default=EmbeddingModel.OPENAI_3_SMALL.value,
        description="Model identifier for embeddings"
    )
    dimension: int = Field(
        default=1536,
        ge=1,
        description="Embedding dimension (auto-detected from model if not set)"
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=2048,
        description="Maximum batch size for embedding requests"
    )
    normalize: bool = Field(
        default=True,
        description="Whether to normalize embeddings to unit length"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Whether to enable embedding caching"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed requests"
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="Request timeout in seconds"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for provider (if required)"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Custom base URL for API (if applicable)"
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific parameters"
    )

    def get_dimension(self) -> int:
        """Get dimension from model if not explicitly set."""
        return MODEL_DIMENSIONS.get(self.model_name, self.dimension)

    def get_max_tokens(self) -> int:
        """Get max tokens for the configured model."""
        return MODEL_MAX_TOKENS.get(self.model_name, 8191)


class EmbeddingResult(BaseModel):
    """Result of an embedding operation."""

    vector: List[float] = Field(
        ...,
        description="The embedding vector"
    )
    dimension: int = Field(
        ...,
        ge=1,
        description="Dimensionality of the embedding vector"
    )
    model: str = Field(
        ...,
        description="Model used to generate the embedding"
    )
    text_hash: str = Field(
        ...,
        description="Hash of input text for cache key"
    )
    token_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of tokens in the input text"
    )
    normalized: bool = Field(
        default=False,
        description="Whether the vector is normalized"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from the provider"
    )

    @classmethod
    def from_text(
        cls,
        text: str,
        vector: List[float],
        model: str = "text-embedding-3-small",
        token_count: Optional[int] = None,
        normalized: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "EmbeddingResult":
        """Create embedding result from text and vector."""
        return cls(
            vector=vector,
            dimension=len(vector),
            model=model,
            text_hash=hashlib.sha256(text.encode()).hexdigest()[:16],
            token_count=token_count,
            normalized=normalized,
            metadata=metadata or {}
        )

    def __len__(self) -> int:
        """Return the dimensionality of the embedding."""
        return self.dimension

    def cosine_similarity(self, other: "EmbeddingResult") -> float:
        """Calculate cosine similarity with another embedding."""
        if self.dimension != other.dimension:
            raise ValueError(f"Dimension mismatch: {self.dimension} vs {other.dimension}")
        return _cosine_similarity(self.vector, other.vector)


# Alias for backward compatibility
EmbeddingVector = EmbeddingResult


class EmbeddingBatchResult(BaseModel):
    """Result of a batch embedding operation."""

    results: List[EmbeddingResult] = Field(
        ...,
        description="List of embedding results"
    )
    model: str = Field(
        ...,
        description="Model used for batch embeddings"
    )
    total_tokens: int = Field(
        default=0,
        ge=0,
        description="Total tokens processed in the batch"
    )
    success_count: int = Field(
        default=0,
        ge=0,
        description="Number of successful embeddings"
    )
    failure_count: int = Field(
        default=0,
        ge=0,
        description="Number of failed embeddings"
    )

    def __len__(self) -> int:
        """Return the number of results."""
        return len(self.results)

    def __iter__(self):
        """Iterate over results."""
        return iter(self.results)


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    Implementations must provide methods for generating embeddings
    from text inputs, both single and batch operations.

    Example usage:
        from lib.oda.semantic.providers.openai import OpenAIEmbeddingProvider

        config = EmbeddingConfig(model_name="text-embedding-3-small")
        provider = OpenAIEmbeddingProvider(config)
        result = await provider.embed("Hello, world!")
        print(result.vector)  # [0.123, -0.456, ...]
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize the embedding provider.

        Args:
            config: Optional configuration for the provider
        """
        self._config = config or EmbeddingConfig()

    @property
    def config(self) -> EmbeddingConfig:
        """Return the provider configuration."""
        return self._config

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Return the embedding dimensions for this provider.

        Returns:
            Integer dimensionality of embeddings
        """
        pass

    @property
    def model_name(self) -> str:
        """
        Return the model identifier.

        Returns:
            String model name/identifier
        """
        return self._config.model_name

    @property
    def max_tokens(self) -> int:
        """
        Return the maximum input tokens supported.

        Returns:
            Maximum token count
        """
        return self._config.get_max_tokens()

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            EmbeddingResult containing the vector and metadata

        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass

    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
        *,
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress indicator

        Returns:
            List of EmbeddingResult containing all embedding results

        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass

    async def embed_with_cache(self, text: str) -> EmbeddingResult:
        """
        Generate embedding with caching support.

        Default implementation just calls embed().
        Subclasses can override to implement caching.

        Args:
            text: The text to embed

        Returns:
            EmbeddingResult from cache or freshly generated
        """
        return await self.embed(text)

    async def embed_if_needed(
        self,
        text: str,
        existing_embedding: Optional[List[float]] = None
    ) -> EmbeddingResult:
        """
        Generate embedding only if not already available.

        Args:
            text: The text to embed
            existing_embedding: Optional existing embedding to reuse

        Returns:
            EmbeddingResult (new or constructed from existing)
        """
        if existing_embedding is not None:
            return EmbeddingResult.from_text(
                text=text,
                vector=existing_embedding,
                model=self.model_name,
                normalized=self._config.normalize
            )
        return await self.embed(text)

    def validate_text(self, text: str) -> bool:
        """
        Validate that text is suitable for embedding.

        Args:
            text: Text to validate

        Returns:
            True if text is valid
        """
        if not text or not text.strip():
            return False
        # Basic length check (approximate ~4 chars per token)
        if len(text) > self.max_tokens * 4:
            return False
        return True

    async def close(self) -> None:
        """
        Clean up provider resources.

        Override in implementations that need cleanup.
        """
        pass

    async def __aenter__(self) -> "EmbeddingProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing and development."""

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        mock_dimension: int = 384
    ):
        """
        Initialize mock embedding provider.

        Args:
            config: Optional configuration
            mock_dimension: Dimension of generated mock embeddings
        """
        super().__init__(config)
        self._mock_dimension = mock_dimension

    @property
    def dimension(self) -> int:
        """Return mock dimension."""
        return self._mock_dimension

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate deterministic mock embedding based on text hash."""
        import random

        # Use text hash as seed for reproducible embeddings
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        random.seed(seed)

        vector = [random.uniform(-1, 1) for _ in range(self._mock_dimension)]

        # Normalize if configured
        if self.config.normalize:
            vector = _normalize_vector(vector)

        return EmbeddingResult.from_text(
            text=text,
            vector=vector,
            model="mock-embedding",
            normalized=self.config.normalize
        )

    async def embed_batch(
        self,
        texts: List[str],
        *,
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        return [await self.embed(text) for text in texts]


# ============================================================================
# Utility Functions
# ============================================================================


def _normalize_vector(vector: List[float]) -> List[float]:
    """Normalize a vector to unit length."""
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude == 0:
        return vector
    return [v / magnitude for v in vector]


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


# ============================================================================
# Exceptions
# ============================================================================


class EmbeddingError(Exception):
    """Base exception for embedding operations."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.details = details or {}


class EmbeddingRateLimitError(EmbeddingError):
    """Rate limit exceeded for embedding API."""
    pass


class EmbeddingTokenLimitError(EmbeddingError):
    """Input exceeds maximum token limit."""
    pass


class EmbeddingConnectionError(EmbeddingError):
    """Connection error to embedding service."""
    pass


class EmbeddingValidationError(EmbeddingError):
    """Input validation error."""
    pass
