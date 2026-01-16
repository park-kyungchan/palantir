"""
ODA Semantic Memory Manager (Phase 4.4.1).

This module integrates the semantic search engine with the memory subsystem,
providing semantic recall and memory storage with automatic embedding.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from lib.oda.semantic.query import (
    SemanticQuery,
    SearchResult,
    SearchResultBatch,
    SearchMode,
)
from lib.oda.semantic.search import SemanticSearchEngine, SearchEngineBuilder
from lib.oda.semantic.ranking import SemanticRanker, RankingConfig, RankingStrategy
from lib.oda.semantic.embedding import EmbeddingProvider, MockEmbeddingProvider
from lib.oda.semantic.vector_store import VectorStore, InMemoryVectorStore

if TYPE_CHECKING:
    from lib.oda.ontology.objects.memory_types import Insight, Pattern

logger = logging.getLogger(__name__)


class MemoryEntry(BaseModel):
    """A memory entry that can be semantically searched."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(..., description="Text content of the memory")
    memory_type: str = Field(default="generic", description="Type of memory (insight, pattern, etc.)")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = Field(default=0, ge=0)
    embedding_stored: bool = Field(default=False)

    def to_text(self) -> str:
        """Convert memory entry to searchable text."""
        parts = [self.content]
        if self.metadata.get("tags"):
            parts.append(f"Tags: {', '.join(self.metadata['tags'])}")
        if self.metadata.get("context"):
            parts.append(f"Context: {self.metadata['context']}")
        return " ".join(parts)


class RecallResult(BaseModel):
    """Result of a memory recall operation."""

    memories: List[MemoryEntry] = Field(default_factory=list)
    query: str
    search_mode: SearchMode = SearchMode.HYBRID
    total_found: int = 0
    recall_time_ms: float = 0.0
    relevance_scores: Dict[str, float] = Field(default_factory=dict)

    @property
    def top_memory(self) -> Optional[MemoryEntry]:
        """Get the most relevant memory."""
        return self.memories[0] if self.memories else None

    def to_context_string(self, max_items: int = 5) -> str:
        """Convert recall results to context string for LLM."""
        lines = ["Relevant memories:"]
        for i, mem in enumerate(self.memories[:max_items]):
            score = self.relevance_scores.get(mem.id, 0.0)
            lines.append(f"{i+1}. [{score:.2f}] {mem.content[:200]}...")
        return "\n".join(lines)


class SemanticMemoryManager:
    """
    Manages semantic memory with automatic embedding and recall.

    Features:
    - Automatic embedding generation on memory storage
    - Semantic search with multiple modes (vector, keyword, hybrid)
    - Memory importance decay over time
    - Access-based memory strengthening
    """

    def __init__(
        self,
        search_engine: Optional[SemanticSearchEngine] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        auto_embed: bool = True,
        ranker: Optional[SemanticRanker] = None
    ):
        """
        Initialize the semantic memory manager.

        Args:
            search_engine: Pre-configured search engine (creates default if None)
            embedding_provider: Provider for generating embeddings
            vector_store: Store for vectors (creates InMemory if None)
            auto_embed: Whether to automatically embed on save
            ranker: Optional ranker for result reranking
        """
        self.auto_embed = auto_embed

        # Initialize components
        if search_engine:
            self.search_engine = search_engine
        else:
            self._embedding_provider = embedding_provider or MockEmbeddingProvider()
            self._vector_store = vector_store or InMemoryVectorStore()
            self.search_engine = SearchEngineBuilder() \
                .with_embedding_provider(self._embedding_provider) \
                .with_vector_store(self._vector_store) \
                .with_default_mode(SearchMode.HYBRID) \
                .build()

        self.ranker = ranker or SemanticRanker(
            RankingConfig(strategy=RankingStrategy.LINEAR_COMBINATION)
        )

        # In-memory cache of memory entries
        self._memories: Dict[str, MemoryEntry] = {}

    async def remember(
        self,
        content: str,
        memory_type: str = "generic",
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        entry_id: Optional[str] = None
    ) -> str:
        """
        Store a memory with automatic embedding.

        Args:
            content: Text content to remember
            memory_type: Type of memory (insight, pattern, fact, etc.)
            importance: Importance score (0-1)
            metadata: Additional metadata
            entry_id: Optional specific ID

        Returns:
            ID of the stored memory
        """
        entry = MemoryEntry(
            id=entry_id or str(uuid4()),
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {},
            embedding_stored=False
        )

        # Store in local cache
        self._memories[entry.id] = entry

        # Index for search
        if self.auto_embed:
            await self.search_engine.index_document(
                id=entry.id,
                text=entry.to_text(),
                metadata={
                    "memory_type": memory_type,
                    "importance": importance,
                    "created_at": entry.created_at.isoformat(),
                    **entry.metadata
                }
            )
            entry.embedding_stored = True

        logger.debug(f"Remembered: {entry.id} (type={memory_type})")
        return entry.id

    async def remember_insight(
        self,
        insight: "Insight"
    ) -> str:
        """
        Store an Insight object in semantic memory.

        Args:
            insight: Insight object to remember

        Returns:
            ID of the stored memory
        """
        # Extract text from insight
        content = insight.content if hasattr(insight, 'content') else str(insight)
        metadata = {
            "source": getattr(insight, 'source', 'unknown'),
            "category": getattr(insight, 'category', None),
            "tags": getattr(insight, 'tags', []),
            "original_id": str(insight.id) if hasattr(insight, 'id') else None
        }

        return await self.remember(
            content=content,
            memory_type="insight",
            importance=getattr(insight, 'importance', 0.5),
            metadata=metadata,
            entry_id=str(insight.id) if hasattr(insight, 'id') else None
        )

    async def remember_pattern(
        self,
        pattern: "Pattern"
    ) -> str:
        """
        Store a Pattern object in semantic memory.

        Args:
            pattern: Pattern object to remember

        Returns:
            ID of the stored memory
        """
        content = pattern.description if hasattr(pattern, 'description') else str(pattern)
        metadata = {
            "pattern_name": getattr(pattern, 'name', None),
            "pattern_type": getattr(pattern, 'pattern_type', None),
            "confidence": getattr(pattern, 'confidence', 0.0),
            "original_id": str(pattern.id) if hasattr(pattern, 'id') else None
        }

        return await self.remember(
            content=content,
            memory_type="pattern",
            importance=getattr(pattern, 'confidence', 0.5),
            metadata=metadata,
            entry_id=str(pattern.id) if hasattr(pattern, 'id') else None
        )

    async def recall(
        self,
        query: str,
        k: int = 5,
        mode: SearchMode = SearchMode.HYBRID,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0,
        rerank: bool = False
    ) -> RecallResult:
        """
        Recall relevant memories using semantic search.

        Args:
            query: Search query text
            k: Number of memories to recall
            mode: Search mode (vector, keyword, hybrid)
            memory_types: Filter by memory types
            min_importance: Minimum importance threshold
            rerank: Whether to apply reranking

        Returns:
            RecallResult with matching memories
        """
        import time
        start_time = time.time()

        # Build filters
        filters = {}
        if memory_types:
            filters["memory_type"] = memory_types[0] if len(memory_types) == 1 else None

        # Create search query
        semantic_query = SemanticQuery(
            text=query,
            mode=mode,
            k=k * 2 if rerank else k,  # Fetch more for reranking
            filters=filters if filters else None,
            min_score=0.0,
            include_metadata=True,
            rerank=rerank
        )

        # Execute search
        search_batch = await self.search_engine.search(semantic_query)

        # Apply reranking if requested
        results = search_batch.results
        if rerank and results:
            results = await self.ranker.rerank(query, results, top_k=k)
        else:
            results = results[:k]

        # Convert search results to memories
        memories = []
        relevance_scores = {}

        for result in results:
            # Retrieve from local cache or create from search result
            if result.id in self._memories:
                memory = self._memories[result.id]
                # Update access tracking
                memory.last_accessed = datetime.utcnow()
                memory.access_count += 1
            else:
                # Reconstruct from search result metadata
                memory = MemoryEntry(
                    id=result.id,
                    content=result.text or result.metadata.get("content", ""),
                    memory_type=result.metadata.get("memory_type", "unknown"),
                    importance=result.metadata.get("importance", 0.5),
                    metadata=result.metadata
                )

            # Apply importance filter
            if memory.importance >= min_importance:
                # Apply memory type filter
                if memory_types is None or memory.memory_type in memory_types:
                    memories.append(memory)
                    relevance_scores[memory.id] = result.score

        recall_time_ms = (time.time() - start_time) * 1000

        return RecallResult(
            memories=memories,
            query=query,
            search_mode=mode,
            total_found=len(memories),
            recall_time_ms=recall_time_ms,
            relevance_scores=relevance_scores
        )

    async def recall_insights(
        self,
        query: str,
        k: int = 5
    ) -> List[MemoryEntry]:
        """
        Convenience method to recall only insight memories.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of matching insight memories
        """
        result = await self.recall(
            query=query,
            k=k,
            memory_types=["insight"]
        )
        return result.memories

    async def recall_patterns(
        self,
        query: str,
        k: int = 5
    ) -> List[MemoryEntry]:
        """
        Convenience method to recall only pattern memories.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of matching pattern memories
        """
        result = await self.recall(
            query=query,
            k=k,
            memory_types=["pattern"]
        )
        return result.memories

    async def forget(self, memory_id: str) -> bool:
        """
        Remove a memory from the system.

        Args:
            memory_id: ID of memory to remove

        Returns:
            True if successfully removed
        """
        # Remove from vector store
        deleted = await self.search_engine.delete_document(memory_id)

        # Remove from local cache
        if memory_id in self._memories:
            del self._memories[memory_id]
            deleted = True

        return deleted

    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID."""
        return self._memories.get(memory_id)

    async def list_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        """List memories, optionally filtered by type."""
        memories = list(self._memories.values())

        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        # Sort by importance and recency
        memories.sort(
            key=lambda m: (m.importance, m.created_at),
            reverse=True
        )

        return memories[:limit]

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics."""
        type_counts: Dict[str, int] = {}
        for mem in self._memories.values():
            type_counts[mem.memory_type] = type_counts.get(mem.memory_type, 0) + 1

        search_stats = await self.search_engine.get_stats()

        return {
            "total_memories": len(self._memories),
            "memories_by_type": type_counts,
            "auto_embed_enabled": self.auto_embed,
            **search_stats
        }

    async def decay_importance(
        self,
        decay_rate: float = 0.01,
        min_importance: float = 0.1
    ) -> int:
        """
        Apply time-based importance decay to all memories.

        Args:
            decay_rate: Rate of decay per call
            min_importance: Minimum importance to preserve

        Returns:
            Number of memories affected
        """
        affected = 0
        for memory in self._memories.values():
            if memory.importance > min_importance:
                memory.importance = max(
                    min_importance,
                    memory.importance * (1 - decay_rate)
                )
                affected += 1
        return affected

    async def strengthen_memory(
        self,
        memory_id: str,
        boost: float = 0.1
    ) -> Optional[MemoryEntry]:
        """
        Strengthen a memory's importance (reinforcement).

        Args:
            memory_id: ID of memory to strengthen
            boost: Amount to boost importance

        Returns:
            Updated memory entry
        """
        if memory_id not in self._memories:
            return None

        memory = self._memories[memory_id]
        memory.importance = min(1.0, memory.importance + boost)
        memory.last_accessed = datetime.utcnow()
        memory.access_count += 1

        return memory


# Factory function for creating semantic memory manager
async def create_semantic_memory_manager(
    embedding_provider: Optional[EmbeddingProvider] = None,
    use_mock: bool = True
) -> SemanticMemoryManager:
    """
    Factory function to create a SemanticMemoryManager.

    Args:
        embedding_provider: Custom embedding provider
        use_mock: Whether to use mock provider (for testing)

    Returns:
        Configured SemanticMemoryManager
    """
    if embedding_provider is None and use_mock:
        embedding_provider = MockEmbeddingProvider()

    manager = SemanticMemoryManager(
        embedding_provider=embedding_provider,
        auto_embed=True
    )

    return manager
