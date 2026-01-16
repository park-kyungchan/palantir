"""
ODA Semantic Layer - Auto Embedding (Phase 4.4.2).

This module provides automatic embedding generation for ontology objects
when they are saved or updated.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Protocol, Union, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from lib.oda.semantic.embedding import (
    EmbeddingProvider,
    EmbeddingResult,
    MockEmbeddingProvider,
)
from lib.oda.semantic.vector_store import VectorStore, InMemoryVectorStore, VectorRecord

if TYPE_CHECKING:
    from pydantic import BaseModel as PydanticBaseModel

logger = logging.getLogger(__name__)


class TextExtractor(Protocol):
    """Protocol for extracting text from objects for embedding."""

    def extract_text(self, obj: Any) -> str:
        """Extract searchable text from an object."""
        ...


class EmbeddingResult(BaseModel):
    """Result of an auto-embedding operation."""

    object_id: str = Field(..., description="ID of the embedded object")
    object_type: str = Field(..., description="Type of the embedded object")
    embedding_id: str = Field(default_factory=lambda: str(uuid4()))
    dimension: int = Field(..., ge=1)
    text_length: int = Field(default=0, ge=0)
    embedded_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool = Field(default=True)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingBatchResult(BaseModel):
    """Result of a batch embedding operation."""

    results: List[EmbeddingResult] = Field(default_factory=list)
    total_objects: int = 0
    successful: int = 0
    failed: int = 0
    processing_time_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_objects == 0:
            return 0.0
        return self.successful / self.total_objects


class DefaultTextExtractor:
    """Default text extractor for common object types."""

    # Field names to check for text content (in priority order)
    TEXT_FIELDS = [
        "content",
        "text",
        "description",
        "summary",
        "body",
        "message",
        "title",
        "name",
    ]

    # Fields to include in metadata text
    METADATA_FIELDS = [
        "tags",
        "category",
        "keywords",
        "labels",
    ]

    def extract_text(self, obj: Any) -> str:
        """
        Extract text from an object using multiple strategies.

        Args:
            obj: Object to extract text from

        Returns:
            Extracted text string
        """
        parts: List[str] = []

        # Strategy 1: Check for to_text method
        if hasattr(obj, "to_text") and callable(obj.to_text):
            return obj.to_text()

        # Strategy 2: Check for __str__ representation
        if hasattr(obj, "__str__"):
            str_repr = str(obj)
            if str_repr and not str_repr.startswith("<"):
                parts.append(str_repr)

        # Strategy 3: Check known text fields
        for field in self.TEXT_FIELDS:
            value = self._get_field_value(obj, field)
            if value and isinstance(value, str):
                parts.append(value)
                break  # Use first found text field

        # Strategy 4: Add metadata fields
        for field in self.METADATA_FIELDS:
            value = self._get_field_value(obj, field)
            if value:
                if isinstance(value, list):
                    parts.append(f"{field}: {', '.join(str(v) for v in value)}")
                else:
                    parts.append(f"{field}: {value}")

        # Strategy 5: For Pydantic models, use model_dump
        if hasattr(obj, "model_dump"):
            try:
                dump = obj.model_dump(exclude_none=True)
                for key in self.TEXT_FIELDS:
                    if key in dump and dump[key]:
                        if dump[key] not in parts:
                            parts.append(str(dump[key]))
                        break
            except Exception:
                pass

        # Combine all parts
        return " ".join(parts).strip()

    @staticmethod
    def _get_field_value(obj: Any, field: str) -> Any:
        """Get field value from object using various access methods."""
        # Try attribute access
        if hasattr(obj, field):
            return getattr(obj, field)

        # Try dict-like access
        if isinstance(obj, dict):
            return obj.get(field)

        # Try getattr with None default
        return getattr(obj, field, None)


class AutoEmbedder:
    """
    Automatically embeds objects on save.

    Integrates with ODA ontology to automatically generate and store
    embeddings whenever an object is persisted.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        text_extractor: Optional[TextExtractor] = None,
        auto_index: bool = True,
        batch_size: int = 100
    ):
        """
        Initialize the auto embedder.

        Args:
            embedding_provider: Provider for generating embeddings
            vector_store: Store for embedding vectors
            text_extractor: Extractor for converting objects to text
            auto_index: Whether to automatically add to vector store
            batch_size: Batch size for batch operations
        """
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.text_extractor = text_extractor or DefaultTextExtractor()
        self.auto_index = auto_index
        self.batch_size = batch_size

        # Statistics
        self._embed_count = 0
        self._error_count = 0

    async def embed_object(
        self,
        obj: Any,
        object_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingResult:
        """
        Generate and store embedding for an ontology object.

        Args:
            obj: Object to embed
            object_id: Optional ID (extracted from object if not provided)
            metadata: Additional metadata to store

        Returns:
            EmbeddingResult with embedding details
        """
        import time
        start_time = time.time()

        # Extract object ID
        obj_id = object_id or self._extract_id(obj)
        obj_type = type(obj).__name__

        try:
            # Extract text from object
            text = self.text_extractor.extract_text(obj)
            if not text:
                return EmbeddingResult(
                    object_id=obj_id,
                    object_type=obj_type,
                    dimension=0,
                    text_length=0,
                    success=False,
                    error="No text content to embed"
                )

            # Generate embedding
            embedding = await self.embedding_provider.embed(text)

            # Build metadata
            full_metadata = {
                "type": obj_type,
                "object_id": obj_id,
                "text_preview": text[:200] if len(text) > 200 else text,
                **(metadata or {})
            }

            # Add object fields to metadata
            if hasattr(obj, "model_dump"):
                try:
                    obj_data = obj.model_dump(exclude_none=True)
                    # Add select fields to metadata
                    for key in ["category", "importance", "status", "tags"]:
                        if key in obj_data:
                            full_metadata[key] = obj_data[key]
                except Exception:
                    pass

            # Store in vector store
            if self.auto_index:
                await self.vector_store.add(
                    id=obj_id,
                    vector=embedding.vector,
                    metadata=full_metadata,
                    text=text
                )

            self._embed_count += 1

            return EmbeddingResult(
                object_id=obj_id,
                object_type=obj_type,
                dimension=embedding.dimension,
                text_length=len(text),
                success=True,
                metadata=full_metadata
            )

        except Exception as e:
            self._error_count += 1
            logger.error(f"Auto-embed error for {obj_id}: {e}")
            return EmbeddingResult(
                object_id=obj_id,
                object_type=obj_type,
                dimension=0,
                text_length=0,
                success=False,
                error=str(e)
            )

    async def embed_batch(
        self,
        objects: List[Any],
        object_ids: Optional[List[str]] = None
    ) -> EmbeddingBatchResult:
        """
        Embed multiple objects in batch.

        Args:
            objects: List of objects to embed
            object_ids: Optional list of IDs (must match objects length)

        Returns:
            EmbeddingBatchResult with all results
        """
        import time
        start_time = time.time()

        if object_ids and len(object_ids) != len(objects):
            raise ValueError("object_ids must match objects length")

        results: List[EmbeddingResult] = []
        successful = 0
        failed = 0

        # Process in batches
        for i in range(0, len(objects), self.batch_size):
            batch_objects = objects[i:i + self.batch_size]
            batch_ids = object_ids[i:i + self.batch_size] if object_ids else None

            # Process each object in batch
            tasks = []
            for j, obj in enumerate(batch_objects):
                obj_id = batch_ids[j] if batch_ids else None
                tasks.append(self.embed_object(obj, object_id=obj_id))

            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    results.append(EmbeddingResult(
                        object_id="unknown",
                        object_type="unknown",
                        dimension=0,
                        success=False,
                        error=str(result)
                    ))
                elif isinstance(result, EmbeddingResult):
                    results.append(result)
                    if result.success:
                        successful += 1
                    else:
                        failed += 1

        processing_time_ms = (time.time() - start_time) * 1000

        return EmbeddingBatchResult(
            results=results,
            total_objects=len(objects),
            successful=successful,
            failed=failed,
            processing_time_ms=processing_time_ms
        )

    async def update_embedding(
        self,
        obj: Any,
        object_id: Optional[str] = None
    ) -> EmbeddingResult:
        """
        Update embedding for an existing object.

        Args:
            obj: Updated object
            object_id: Object ID

        Returns:
            EmbeddingResult
        """
        obj_id = object_id or self._extract_id(obj)

        # Delete existing embedding
        await self.vector_store.delete(obj_id)

        # Create new embedding
        return await self.embed_object(obj, object_id=obj_id)

    async def delete_embedding(self, object_id: str) -> bool:
        """
        Delete embedding for an object.

        Args:
            object_id: ID of object to delete

        Returns:
            True if deleted
        """
        return await self.vector_store.delete(object_id)

    async def has_embedding(self, object_id: str) -> bool:
        """
        Check if an object has an embedding stored.

        Args:
            object_id: Object ID to check

        Returns:
            True if embedding exists
        """
        record = await self.vector_store.get(object_id)
        return record is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get auto-embedder statistics."""
        return {
            "total_embedded": self._embed_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / max(1, self._embed_count + self._error_count),
            "embedding_dimension": self.embedding_provider.dimension,
            "auto_index_enabled": self.auto_index,
            "batch_size": self.batch_size
        }

    @staticmethod
    def _extract_id(obj: Any) -> str:
        """Extract ID from an object."""
        # Try common ID attributes
        for attr in ["id", "object_id", "uid", "uuid", "_id"]:
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                if value is not None:
                    return str(value)

        # Try dict access
        if isinstance(obj, dict):
            for key in ["id", "object_id", "uid", "uuid", "_id"]:
                if key in obj:
                    return str(obj[key])

        # Generate a new ID
        return str(uuid4())


class AutoEmbedHook:
    """
    Hook for integrating auto-embedding with ODA action system.

    Can be registered as a post-action hook to automatically
    embed objects after they are saved.
    """

    def __init__(self, auto_embedder: AutoEmbedder):
        self.auto_embedder = auto_embedder
        self._enabled = True

    async def on_object_saved(
        self,
        obj: Any,
        action_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[EmbeddingResult]:
        """
        Hook called after an object is saved.

        Args:
            obj: The saved object
            action_type: Type of action that saved the object
            context: Action context

        Returns:
            EmbeddingResult if embedding was created
        """
        if not self._enabled:
            return None

        # Skip certain action types
        skip_actions = {"DeleteAction", "QueryAction", "ReadAction"}
        if action_type in skip_actions:
            return None

        try:
            result = await self.auto_embedder.embed_object(obj)
            logger.debug(f"Auto-embedded {result.object_id} after {action_type}")
            return result
        except Exception as e:
            logger.warning(f"Auto-embed hook error: {e}")
            return None

    def enable(self) -> None:
        """Enable the auto-embed hook."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the auto-embed hook."""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if hook is enabled."""
        return self._enabled


# Factory function
def create_auto_embedder(
    use_mock: bool = True,
    auto_index: bool = True
) -> AutoEmbedder:
    """
    Factory function to create an AutoEmbedder.

    Args:
        use_mock: Use mock embedding provider
        auto_index: Automatically index embeddings

    Returns:
        Configured AutoEmbedder
    """
    provider = MockEmbeddingProvider() if use_mock else None
    store = InMemoryVectorStore()

    return AutoEmbedder(
        embedding_provider=provider,
        vector_store=store,
        auto_index=auto_index
    )
