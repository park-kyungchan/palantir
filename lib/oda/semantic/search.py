"""
ODA Semantic Layer - Search Engine (Phase 4.3.2-4.3.3).

This module provides the main semantic search engine combining
vector similarity search, keyword search, and hybrid approaches.
"""

import time
from typing import List, Optional, Dict, Any, Tuple, Protocol
from collections import defaultdict
import re
import math

from lib.oda.semantic.query import (
    SemanticQuery,
    SearchResult,
    SearchResultBatch,
    SearchMode,
    QueryContext,
)
from lib.oda.semantic.embedding import EmbeddingProvider, EmbeddingResult
from lib.oda.semantic.vector_store import VectorStore, VectorSearchResult


class KeywordStore(Protocol):
    """Protocol for keyword search backends."""

    async def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Optional[str], Dict[str, Any]]]:
        """Search using keyword matching. Returns (id, score, text, metadata)."""
        ...

    async def index(self, id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Index a document for keyword search."""
        ...


class InMemoryKeywordStore:
    """Simple in-memory keyword store using TF-IDF-like scoring."""

    def __init__(self):
        self._documents: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        self._term_index: Dict[str, set] = defaultdict(set)
        self._doc_freqs: Dict[str, int] = defaultdict(int)

    async def index(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Index a document for keyword search."""
        self._documents[id] = (text, metadata or {})

        # Tokenize and index terms
        terms = self._tokenize(text)
        unique_terms = set(terms)

        for term in unique_terms:
            self._term_index[term].add(id)
            self._doc_freqs[term] += 1

    async def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Optional[str], Dict[str, Any]]]:
        """Search using BM25-like scoring."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        scores: Dict[str, float] = defaultdict(float)
        total_docs = len(self._documents)

        # BM25 parameters
        k1 = 1.5
        b = 0.75
        avg_doc_len = sum(
            len(self._tokenize(doc[0]))
            for doc in self._documents.values()
        ) / max(1, total_docs)

        for term in query_terms:
            if term not in self._term_index:
                continue

            # Calculate IDF
            df = self._doc_freqs[term]
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)

            for doc_id in self._term_index[term]:
                doc_text, doc_metadata = self._documents[doc_id]

                # Apply filters
                if filters and not self._matches_filters(doc_metadata, filters):
                    continue

                doc_terms = self._tokenize(doc_text)
                doc_len = len(doc_terms)
                tf = doc_terms.count(term)

                # BM25 score
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                scores[doc_id] += idf * numerator / denominator

        # Normalize scores to 0-1 range
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {k: v / max_score for k, v in scores.items()}

        # Sort and return top k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

        return [
            (doc_id, score, self._documents[doc_id][0], self._documents[doc_id][1])
            for doc_id, score in sorted_results
        ]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenization."""
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        # Remove stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                     'from', 'as', 'into', 'through', 'during', 'before', 'after',
                     'above', 'below', 'between', 'under', 'again', 'further',
                     'then', 'once', 'here', 'there', 'when', 'where', 'why',
                     'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                     'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                     'than', 'too', 'very', 'and', 'but', 'if', 'or', 'because',
                     'until', 'while', 'although', 'though', 'after', 'before'}
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    @staticmethod
    def _matches_filters(metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filters."""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True


class SemanticSearchEngine:
    """
    Main semantic search engine combining vector and keyword search.

    Supports three modes:
    - VECTOR: Pure vector similarity search using embeddings
    - KEYWORD: Pure keyword/BM25 search
    - HYBRID: Combined vector + keyword with score fusion
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        keyword_store: Optional[KeywordStore] = None,
        default_mode: SearchMode = SearchMode.HYBRID
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.keyword_store = keyword_store or InMemoryKeywordStore()
        self.default_mode = default_mode

    async def search(
        self,
        query: SemanticQuery,
        context: Optional[QueryContext] = None
    ) -> SearchResultBatch:
        """
        Execute semantic search based on query mode.

        Args:
            query: The semantic query to execute
            context: Optional execution context

        Returns:
            SearchResultBatch with ranked results
        """
        start_time = time.time()
        context = context or QueryContext.create()

        # Determine effective mode
        mode = query.mode

        # Execute search based on mode
        if mode == SearchMode.VECTOR:
            results = await self._vector_search(query)
        elif mode == SearchMode.KEYWORD:
            results = await self._keyword_search(query)
        else:  # HYBRID
            results = await self._hybrid_search(query)

        # Apply minimum score filter
        if query.min_score > 0:
            results = [r for r in results if r.score >= query.min_score]

        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i

        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000

        return SearchResultBatch(
            results=results[:query.k],
            query=query,
            total_found=len(results),
            search_time_ms=search_time_ms,
            mode_used=mode
        )

    async def _vector_search(self, query: SemanticQuery) -> List[SearchResult]:
        """Execute pure vector similarity search."""
        # Generate query embedding
        query_embedding = await self.embedding_provider.embed(query.text)

        # Search vector store
        vector_results = await self.vector_store.search(
            query_vector=query_embedding.vector,
            k=query.k * 2 if query.rerank else query.k,  # Over-fetch for reranking
            filters=query.get_effective_filters()
        )

        # Convert to SearchResult
        results = []
        for vr in vector_results:
            results.append(SearchResult.from_vector_result(
                id=vr.id,
                score=vr.score,
                text=vr.text,
                metadata=vr.metadata if query.include_metadata else {},
                rank=len(results)
            ))

        return results

    async def _keyword_search(self, query: SemanticQuery) -> List[SearchResult]:
        """Execute pure keyword/BM25 search."""
        keyword_results = await self.keyword_store.search(
            query=query.text,
            k=query.k * 2 if query.rerank else query.k,
            filters=query.get_effective_filters()
        )

        results = []
        for doc_id, score, text, metadata in keyword_results:
            results.append(SearchResult.from_keyword_result(
                id=doc_id,
                score=score,
                text=text,
                metadata=metadata if query.include_metadata else {},
                rank=len(results)
            ))

        return results

    async def _hybrid_search(self, query: SemanticQuery) -> List[SearchResult]:
        """
        Execute hybrid search combining vector and keyword results.

        Uses Reciprocal Rank Fusion (RRF) or weighted combination
        based on query weights.
        """
        # Normalize weights
        normalized_query = query.normalize_weights()

        # Fetch more results for fusion
        fetch_k = query.k * 3

        # Execute both searches in parallel (simulated)
        vector_results = await self._vector_search(
            query.model_copy(update={"k": fetch_k, "mode": SearchMode.VECTOR})
        )
        keyword_results = await self._keyword_search(
            query.model_copy(update={"k": fetch_k, "mode": SearchMode.KEYWORD})
        )

        # Score fusion using RRF
        fused_results = self._reciprocal_rank_fusion(
            vector_results=vector_results,
            keyword_results=keyword_results,
            vector_weight=normalized_query.vector_weight,
            keyword_weight=normalized_query.keyword_weight,
            rrf_k=60  # Standard RRF constant
        )

        return fused_results

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        rrf_k: int = 60
    ) -> List[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).

        RRF formula: score = sum(1 / (k + rank)) for each result list

        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            vector_weight: Weight for vector scores
            keyword_weight: Weight for keyword scores
            rrf_k: RRF constant (default 60)

        Returns:
            Fused and sorted results
        """
        # Build score maps
        rrf_scores: Dict[str, float] = defaultdict(float)
        result_data: Dict[str, SearchResult] = {}

        # Process vector results
        for rank, result in enumerate(vector_results):
            rrf_score = vector_weight * (1 / (rrf_k + rank + 1))
            rrf_scores[result.id] += rrf_score

            if result.id not in result_data:
                result_data[result.id] = result.model_copy()
                result_data[result.id].vector_score = result.score
            else:
                result_data[result.id].vector_score = result.score

        # Process keyword results
        for rank, result in enumerate(keyword_results):
            rrf_score = keyword_weight * (1 / (rrf_k + rank + 1))
            rrf_scores[result.id] += rrf_score

            if result.id not in result_data:
                result_data[result.id] = result.model_copy()
                result_data[result.id].keyword_score = result.score
            else:
                result_data[result.id].keyword_score = result.score

        # Normalize RRF scores to 0-1 range
        if rrf_scores:
            max_rrf = max(rrf_scores.values())
            if max_rrf > 0:
                rrf_scores = {k: v / max_rrf for k, v in rrf_scores.items()}

        # Create final results
        final_results = []
        for doc_id, rrf_score in rrf_scores.items():
            result = result_data[doc_id]
            result.score = rrf_score
            final_results.append(result)

        # Sort by fused score
        final_results.sort(key=lambda x: x.score, reverse=True)

        return final_results

    async def index_document(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Index a document for both vector and keyword search.

        Args:
            id: Unique document identifier
            text: Document text content
            metadata: Optional metadata
        """
        # Generate and store embedding
        embedding = await self.embedding_provider.embed(text)
        await self.vector_store.add(
            id=id,
            vector=embedding.vector,
            metadata=metadata,
            text=text
        )

        # Index for keyword search
        await self.keyword_store.index(id, text, metadata)

    async def batch_index(
        self,
        documents: List[Tuple[str, str, Optional[Dict[str, Any]]]]
    ) -> int:
        """
        Index multiple documents.

        Args:
            documents: List of (id, text, metadata) tuples

        Returns:
            Number of documents indexed
        """
        count = 0
        for doc_id, text, metadata in documents:
            await self.index_document(doc_id, text, metadata)
            count += 1
        return count

    async def delete_document(self, id: str) -> bool:
        """Delete a document from the index."""
        return await self.vector_store.delete(id)

    async def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        vector_count = await self.vector_store.count()
        return {
            "vector_count": vector_count,
            "embedding_dimension": self.embedding_provider.dimension,
            "default_mode": self.default_mode.value
        }


class SearchEngineBuilder:
    """Builder for creating SemanticSearchEngine instances."""

    def __init__(self):
        self._embedding_provider: Optional[EmbeddingProvider] = None
        self._vector_store: Optional[VectorStore] = None
        self._keyword_store: Optional[KeywordStore] = None
        self._default_mode: SearchMode = SearchMode.HYBRID

    def with_embedding_provider(self, provider: EmbeddingProvider) -> "SearchEngineBuilder":
        """Set embedding provider."""
        self._embedding_provider = provider
        return self

    def with_vector_store(self, store: VectorStore) -> "SearchEngineBuilder":
        """Set vector store."""
        self._vector_store = store
        return self

    def with_keyword_store(self, store: KeywordStore) -> "SearchEngineBuilder":
        """Set keyword store."""
        self._keyword_store = store
        return self

    def with_default_mode(self, mode: SearchMode) -> "SearchEngineBuilder":
        """Set default search mode."""
        self._default_mode = mode
        return self

    def build(self) -> SemanticSearchEngine:
        """Build the search engine."""
        if not self._embedding_provider:
            from lib.oda.semantic.embedding import MockEmbeddingProvider
            self._embedding_provider = MockEmbeddingProvider()

        if not self._vector_store:
            from lib.oda.semantic.vector_store import InMemoryVectorStore
            self._vector_store = InMemoryVectorStore()

        return SemanticSearchEngine(
            embedding_provider=self._embedding_provider,
            vector_store=self._vector_store,
            keyword_store=self._keyword_store,
            default_mode=self._default_mode
        )
