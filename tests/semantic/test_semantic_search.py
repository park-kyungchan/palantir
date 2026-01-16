"""
Tests for ODA Semantic Layer (Phase 4.3-4.4).

Tests cover:
- SemanticQuery and SearchResult models
- SemanticSearchEngine (vector, keyword, hybrid modes)
- SemanticRanker (multiple strategies)
- SemanticMemoryManager integration
- AutoEmbedder functionality
"""

import pytest
import asyncio
from typing import List, Dict, Any

from lib.oda.semantic.query import (
    SemanticQuery,
    SearchResult,
    SearchResultBatch,
    SearchMode,
    FilterOperator,
    FilterCondition,
)
from lib.oda.semantic.search import (
    SemanticSearchEngine,
    SearchEngineBuilder,
    InMemoryKeywordStore,
)
from lib.oda.semantic.ranking import (
    SemanticRanker,
    RankingConfig,
    RankingStrategy,
    RankerPipeline,
    DiversityRanker,
)
from lib.oda.semantic.embedding import (
    MockEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingResult,
)
from lib.oda.semantic.vector_store import InMemoryVectorStore
from lib.oda.semantic.auto_embed import (
    AutoEmbedder,
    DefaultTextExtractor,
    AutoEmbedHook,
    create_auto_embedder,
)
from lib.oda.memory.semantic_memory import (
    SemanticMemoryManager,
    MemoryEntry,
    RecallResult,
    create_semantic_memory_manager,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_embedding_provider():
    """Create mock embedding provider."""
    return MockEmbeddingProvider(mock_dimension=384)


@pytest.fixture
def vector_store():
    """Create in-memory vector store."""
    return InMemoryVectorStore()


@pytest.fixture
def keyword_store():
    """Create in-memory keyword store."""
    return InMemoryKeywordStore()


@pytest.fixture
def search_engine(mock_embedding_provider, vector_store, keyword_store):
    """Create search engine with all components."""
    return SemanticSearchEngine(
        embedding_provider=mock_embedding_provider,
        vector_store=vector_store,
        keyword_store=keyword_store,
        default_mode=SearchMode.HYBRID
    )


@pytest.fixture
def sample_documents() -> List[Dict[str, Any]]:
    """Sample documents for testing."""
    return [
        {
            "id": "doc1",
            "text": "Python is a programming language known for its simplicity.",
            "metadata": {"category": "programming", "language": "python"}
        },
        {
            "id": "doc2",
            "text": "Machine learning uses algorithms to learn patterns from data.",
            "metadata": {"category": "ml", "topic": "algorithms"}
        },
        {
            "id": "doc3",
            "text": "Deep learning is a subset of machine learning using neural networks.",
            "metadata": {"category": "ml", "topic": "neural_networks"}
        },
        {
            "id": "doc4",
            "text": "Natural language processing enables computers to understand human language.",
            "metadata": {"category": "nlp", "language": "english"}
        },
        {
            "id": "doc5",
            "text": "JavaScript is a programming language for web development.",
            "metadata": {"category": "programming", "language": "javascript"}
        },
    ]


@pytest.fixture
def indexed_search_engine(mock_embedding_provider, vector_store, keyword_store, sample_documents):
    """Search engine with indexed documents (sync fixture using run_until_complete)."""
    import asyncio
    engine = SemanticSearchEngine(
        embedding_provider=mock_embedding_provider,
        vector_store=vector_store,
        keyword_store=keyword_store,
        default_mode=SearchMode.HYBRID
    )

    async def setup():
        for doc in sample_documents:
            await engine.index_document(
                id=doc["id"],
                text=doc["text"],
                metadata=doc["metadata"]
            )

    loop = asyncio.new_event_loop()
    loop.run_until_complete(setup())
    loop.close()
    return engine


# ============================================================================
# Query Model Tests
# ============================================================================


class TestSemanticQuery:
    """Tests for SemanticQuery model."""

    def test_default_query(self):
        """Test query with default values."""
        query = SemanticQuery(text="test query")
        assert query.text == "test query"
        assert query.mode == SearchMode.HYBRID
        assert query.k == 10
        assert query.min_score == 0.0
        assert query.include_metadata is True

    def test_query_with_filters(self):
        """Test query with filters."""
        query = SemanticQuery(
            text="test",
            filters={"category": "ml"},
            k=5
        )
        assert query.filters["category"] == "ml"
        assert query.k == 5

    def test_query_with_filter_conditions(self):
        """Test query with advanced filter conditions."""
        conditions = [
            FilterCondition(field="score", operator=FilterOperator.GTE, value=0.5),
            FilterCondition(field="category", operator=FilterOperator.EQ, value="ml")
        ]
        query = SemanticQuery(
            text="test",
            filter_conditions=conditions
        )
        assert len(query.filter_conditions) == 2

    def test_query_weight_normalization(self):
        """Test weight normalization."""
        query = SemanticQuery(
            text="test",
            vector_weight=0.8,
            keyword_weight=0.2
        )
        normalized = query.normalize_weights()
        assert abs(normalized.vector_weight + normalized.keyword_weight - 1.0) < 0.01

    def test_filter_condition_matches(self):
        """Test filter condition matching."""
        metadata = {"score": 0.7, "category": "ml"}

        cond1 = FilterCondition(field="score", operator=FilterOperator.GTE, value=0.5)
        assert cond1.matches(metadata) is True

        cond2 = FilterCondition(field="score", operator=FilterOperator.GT, value=0.8)
        assert cond2.matches(metadata) is False

        cond3 = FilterCondition(field="category", operator=FilterOperator.IN, value=["ml", "nlp"])
        assert cond3.matches(metadata) is True


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_from_vector_result(self):
        """Test creating result from vector search."""
        result = SearchResult.from_vector_result(
            id="doc1",
            score=0.85,
            text="Test content",
            metadata={"key": "value"}
        )
        assert result.vector_score == 0.85
        assert result.keyword_score is None
        assert result.score == 0.85

    def test_from_keyword_result(self):
        """Test creating result from keyword search."""
        result = SearchResult.from_keyword_result(
            id="doc1",
            score=0.75,
            text="Test content"
        )
        assert result.keyword_score == 0.75
        assert result.vector_score is None

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = SearchResult(
            id="doc1",
            score=0.8,
            text="test",
            metadata={"key": "value"}
        )
        d = result.to_dict()
        assert d["id"] == "doc1"
        assert d["score"] == 0.8


# ============================================================================
# Search Engine Tests
# ============================================================================


class TestSemanticSearchEngine:
    """Tests for SemanticSearchEngine."""

    @pytest.mark.asyncio
    async def test_index_document(self, search_engine):
        """Test document indexing."""
        await search_engine.index_document(
            id="test1",
            text="This is a test document",
            metadata={"type": "test"}
        )
        stats = await search_engine.get_stats()
        assert stats["vector_count"] == 1

    @pytest.mark.asyncio
    async def test_vector_search(self, indexed_search_engine):
        """Test pure vector search."""
        query = SemanticQuery(
            text="programming language",
            mode=SearchMode.VECTOR,
            k=3
        )
        results = await indexed_search_engine.search(query)
        assert len(results.results) <= 3
        assert results.mode_used == SearchMode.VECTOR

    @pytest.mark.asyncio
    async def test_keyword_search(self, indexed_search_engine):
        """Test pure keyword search."""
        query = SemanticQuery(
            text="machine learning algorithms",
            mode=SearchMode.KEYWORD,
            k=3
        )
        results = await indexed_search_engine.search(query)
        assert len(results.results) <= 3
        assert results.mode_used == SearchMode.KEYWORD

    @pytest.mark.asyncio
    async def test_hybrid_search(self, indexed_search_engine):
        """Test hybrid search."""
        query = SemanticQuery(
            text="deep learning neural networks",
            mode=SearchMode.HYBRID,
            k=3
        )
        results = await indexed_search_engine.search(query)
        assert len(results.results) <= 3
        assert results.mode_used == SearchMode.HYBRID
        # Check that results have both scores
        for result in results.results:
            # At least one score should be set
            assert result.vector_score is not None or result.keyword_score is not None

    @pytest.mark.asyncio
    async def test_search_with_filters(self, indexed_search_engine):
        """Test search with metadata filters."""
        query = SemanticQuery(
            text="programming",
            mode=SearchMode.HYBRID,
            filters={"category": "programming"},
            k=5
        )
        results = await indexed_search_engine.search(query)
        # All results should have matching category
        for result in results.results:
            if result.metadata.get("category"):
                assert result.metadata["category"] == "programming"

    @pytest.mark.asyncio
    async def test_search_min_score(self, indexed_search_engine):
        """Test minimum score filtering."""
        query = SemanticQuery(
            text="test query",
            mode=SearchMode.VECTOR,
            min_score=0.9,  # High threshold
            k=10
        )
        results = await indexed_search_engine.search(query)
        for result in results.results:
            assert result.score >= 0.9

    @pytest.mark.asyncio
    async def test_batch_index(self, search_engine, sample_documents):
        """Test batch document indexing."""
        docs = [(d["id"], d["text"], d["metadata"]) for d in sample_documents]
        count = await search_engine.batch_index(docs)
        assert count == len(sample_documents)

        stats = await search_engine.get_stats()
        assert stats["vector_count"] == len(sample_documents)


class TestSearchEngineBuilder:
    """Tests for SearchEngineBuilder."""

    def test_build_with_defaults(self):
        """Test building with default components."""
        engine = SearchEngineBuilder().build()
        assert engine is not None
        assert engine.default_mode == SearchMode.HYBRID

    def test_build_with_custom_mode(self):
        """Test building with custom default mode."""
        engine = SearchEngineBuilder() \
            .with_default_mode(SearchMode.VECTOR) \
            .build()
        assert engine.default_mode == SearchMode.VECTOR


# ============================================================================
# Ranking Tests
# ============================================================================


class TestSemanticRanker:
    """Tests for SemanticRanker."""

    @pytest.fixture
    def sample_results(self) -> List[SearchResult]:
        """Create sample search results."""
        return [
            SearchResult(id="r1", score=0.9, text="Python programming basics", vector_score=0.9, keyword_score=0.7),
            SearchResult(id="r2", score=0.8, text="Advanced Python techniques", vector_score=0.75, keyword_score=0.85),
            SearchResult(id="r3", score=0.7, text="Machine learning with Python", vector_score=0.7, keyword_score=0.6),
            SearchResult(id="r4", score=0.6, text="Data science fundamentals", vector_score=0.5, keyword_score=0.7),
        ]

    @pytest.mark.asyncio
    async def test_linear_combination_rerank(self, sample_results):
        """Test linear combination reranking."""
        config = RankingConfig(
            strategy=RankingStrategy.LINEAR_COMBINATION,
            score_weights={"vector": 0.6, "keyword": 0.4}
        )
        ranker = SemanticRanker(config)
        reranked = await ranker.rerank("python", sample_results)

        assert len(reranked) == len(sample_results)
        # All results should have rerank_score
        for r in reranked:
            assert r.rerank_score is not None

    @pytest.mark.asyncio
    async def test_bm25_rerank(self, sample_results):
        """Test BM25 reranking."""
        config = RankingConfig(strategy=RankingStrategy.BM25_RERANK)
        ranker = SemanticRanker(config)
        reranked = await ranker.rerank("python programming", sample_results)

        assert len(reranked) == len(sample_results)

    @pytest.mark.asyncio
    async def test_mmr_rerank(self, sample_results):
        """Test MMR diversity reranking."""
        config = RankingConfig(
            strategy=RankingStrategy.MMR,
            diversity_lambda=0.5
        )
        ranker = SemanticRanker(config)
        reranked = await ranker.rerank("python", sample_results)

        assert len(reranked) == len(sample_results)

    @pytest.mark.asyncio
    async def test_rerank_with_top_k(self, sample_results):
        """Test reranking with top_k limit."""
        ranker = SemanticRanker()
        reranked = await ranker.rerank("test", sample_results, top_k=2)

        assert len(reranked) == 2


class TestRankerPipeline:
    """Tests for RankerPipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """Test multi-stage ranking pipeline."""
        results = [
            SearchResult(id=f"r{i}", score=0.5 + i*0.1, text=f"Document {i}")
            for i in range(5)
        ]

        pipeline = RankerPipeline()
        pipeline.add_stage(SemanticRanker(RankingConfig(strategy=RankingStrategy.BM25_RERANK)))
        pipeline.add_stage(SemanticRanker(RankingConfig(strategy=RankingStrategy.LINEAR_COMBINATION)))

        reranked = await pipeline.run("test query", results, top_k=3)
        assert len(reranked) == 3


class TestDiversityRanker:
    """Tests for DiversityRanker."""

    @pytest.mark.asyncio
    async def test_diversity_enforcement(self):
        """Test diversity enforcement in results."""
        # Create similar documents
        results = [
            SearchResult(id="r1", score=0.9, text="Python programming tutorial for beginners"),
            SearchResult(id="r2", score=0.85, text="Python programming guide for beginners"),
            SearchResult(id="r3", score=0.8, text="Machine learning fundamentals"),
            SearchResult(id="r4", score=0.75, text="Deep learning neural networks"),
        ]

        ranker = DiversityRanker(diversity_threshold=0.7)
        reranked = await ranker.rerank("programming", results)

        assert len(reranked) >= 2


# ============================================================================
# Memory Integration Tests
# ============================================================================


class TestSemanticMemoryManager:
    """Tests for SemanticMemoryManager."""

    @pytest.fixture
    def memory_manager(self):
        """Create semantic memory manager synchronously for fixture."""
        # Return a new manager for each test
        return SemanticMemoryManager(auto_embed=True)

    @pytest.mark.asyncio
    async def test_remember_and_recall(self, memory_manager):
        """Test basic remember and recall."""
        # Remember something
        mem_id = await memory_manager.remember(
            content="Python is great for data science",
            memory_type="insight",
            importance=0.8
        )
        assert mem_id is not None

        # Recall it
        result = await memory_manager.recall("data science programming", k=5)
        assert result.total_found >= 1
        assert any(m.id == mem_id for m in result.memories)

    @pytest.mark.asyncio
    async def test_remember_with_metadata(self, memory_manager):
        """Test remembering with metadata."""
        mem_id = await memory_manager.remember(
            content="Important pattern discovered",
            memory_type="pattern",
            importance=0.9,
            metadata={"tags": ["important", "discovery"], "context": "analysis"}
        )

        memory = await memory_manager.get_memory(mem_id)
        assert memory is not None
        assert memory.metadata.get("tags") == ["important", "discovery"]

    @pytest.mark.asyncio
    async def test_recall_with_type_filter(self, memory_manager):
        """Test recall with memory type filter."""
        await memory_manager.remember("Insight 1", memory_type="insight")
        await memory_manager.remember("Pattern 1", memory_type="pattern")

        result = await memory_manager.recall(
            "test",
            memory_types=["insight"]
        )
        for mem in result.memories:
            assert mem.memory_type == "insight"

    @pytest.mark.asyncio
    async def test_forget(self, memory_manager):
        """Test forgetting a memory."""
        mem_id = await memory_manager.remember("To be forgotten")
        assert await memory_manager.get_memory(mem_id) is not None

        deleted = await memory_manager.forget(mem_id)
        assert deleted is True
        assert await memory_manager.get_memory(mem_id) is None

    @pytest.mark.asyncio
    async def test_importance_decay(self, memory_manager):
        """Test importance decay."""
        mem_id = await memory_manager.remember(
            "Test memory",
            importance=1.0
        )
        memory = await memory_manager.get_memory(mem_id)
        original_importance = memory.importance

        affected = await memory_manager.decay_importance(decay_rate=0.1)
        assert affected >= 1

        memory = await memory_manager.get_memory(mem_id)
        assert memory.importance < original_importance

    @pytest.mark.asyncio
    async def test_strengthen_memory(self, memory_manager):
        """Test memory strengthening."""
        mem_id = await memory_manager.remember(
            "Test memory",
            importance=0.5
        )

        strengthened = await memory_manager.strengthen_memory(mem_id, boost=0.2)
        assert strengthened is not None
        assert strengthened.importance == 0.7
        assert strengthened.access_count == 1

    @pytest.mark.asyncio
    async def test_stats(self, memory_manager):
        """Test getting stats."""
        await memory_manager.remember("Memory 1", memory_type="insight")
        await memory_manager.remember("Memory 2", memory_type="pattern")

        stats = await memory_manager.get_stats()
        assert stats["total_memories"] == 2
        assert "memories_by_type" in stats


# ============================================================================
# Auto-Embedding Tests
# ============================================================================


class TestAutoEmbedder:
    """Tests for AutoEmbedder."""

    @pytest.fixture
    def auto_embedder(self):
        """Create auto embedder."""
        return create_auto_embedder(use_mock=True)

    @pytest.mark.asyncio
    async def test_embed_dict_object(self, auto_embedder):
        """Test embedding a dict object."""
        obj = {
            "id": "obj1",
            "content": "This is test content for embedding",
            "category": "test"
        }
        result = await auto_embedder.embed_object(obj)

        assert result.success is True
        assert result.object_id == "obj1"
        assert result.dimension > 0

    @pytest.mark.asyncio
    async def test_embed_pydantic_object(self, auto_embedder):
        """Test embedding a Pydantic object."""
        entry = MemoryEntry(
            id="mem1",
            content="Test memory content",
            memory_type="test"
        )
        result = await auto_embedder.embed_object(entry)

        assert result.success is True
        assert result.object_type == "MemoryEntry"

    @pytest.mark.asyncio
    async def test_embed_batch(self, auto_embedder):
        """Test batch embedding."""
        objects = [
            {"id": f"obj{i}", "content": f"Content {i}"}
            for i in range(5)
        ]
        batch_result = await auto_embedder.embed_batch(objects)

        assert batch_result.total_objects == 5
        assert batch_result.successful == 5
        assert batch_result.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_update_embedding(self, auto_embedder):
        """Test updating an embedding."""
        obj = {"id": "update_test", "content": "Original content"}
        await auto_embedder.embed_object(obj)

        updated_obj = {"id": "update_test", "content": "Updated content"}
        result = await auto_embedder.update_embedding(updated_obj)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_has_embedding(self, auto_embedder):
        """Test checking for embedding existence."""
        obj = {"id": "check_test", "content": "Test"}
        await auto_embedder.embed_object(obj)

        assert await auto_embedder.has_embedding("check_test") is True
        assert await auto_embedder.has_embedding("nonexistent") is False

    def test_stats(self, auto_embedder):
        """Test getting embedder stats."""
        stats = auto_embedder.get_stats()
        assert "total_embedded" in stats
        assert "embedding_dimension" in stats


class TestDefaultTextExtractor:
    """Tests for DefaultTextExtractor."""

    def test_extract_from_dict(self):
        """Test extracting text from dict."""
        extractor = DefaultTextExtractor()
        obj = {"content": "Main content", "tags": ["tag1", "tag2"]}
        text = extractor.extract_text(obj)

        assert "Main content" in text
        assert "tag1" in text

    def test_extract_from_object_with_to_text(self):
        """Test extracting from object with to_text method."""
        class CustomObj:
            def to_text(self):
                return "Custom text representation"

        extractor = DefaultTextExtractor()
        text = extractor.extract_text(CustomObj())
        assert text == "Custom text representation"


class TestAutoEmbedHook:
    """Tests for AutoEmbedHook."""

    @pytest.mark.asyncio
    async def test_hook_on_save(self):
        """Test hook triggered on save."""
        embedder = create_auto_embedder()
        hook = AutoEmbedHook(embedder)

        obj = {"id": "hook_test", "content": "Test content"}
        result = await hook.on_object_saved(obj, "SaveAction")

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_hook_skip_delete_action(self):
        """Test hook skips delete actions."""
        embedder = create_auto_embedder()
        hook = AutoEmbedHook(embedder)

        obj = {"id": "skip_test", "content": "Test"}
        result = await hook.on_object_saved(obj, "DeleteAction")

        assert result is None

    def test_hook_enable_disable(self):
        """Test hook enable/disable."""
        embedder = create_auto_embedder()
        hook = AutoEmbedHook(embedder)

        assert hook.is_enabled is True
        hook.disable()
        assert hook.is_enabled is False
        hook.enable()
        assert hook.is_enabled is True


# ============================================================================
# Integration Tests
# ============================================================================


class TestSemanticLayerIntegration:
    """Integration tests for the full semantic layer."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: index, search, rank, recall."""
        # Create components
        engine = SearchEngineBuilder().build()
        ranker = SemanticRanker()
        memory = SemanticMemoryManager(search_engine=engine, ranker=ranker)

        # Index documents through memory
        await memory.remember("Python is a versatile programming language", memory_type="fact")
        await memory.remember("Machine learning requires good data", memory_type="insight")
        await memory.remember("Deep learning uses neural networks", memory_type="insight")

        # Recall with reranking
        result = await memory.recall(
            query="programming languages",
            k=3,
            mode=SearchMode.HYBRID,
            rerank=True
        )

        assert result.total_found >= 1
        assert all(r.id in result.relevance_scores for r in result.memories)

    @pytest.mark.asyncio
    async def test_auto_embed_with_search(self):
        """Test auto-embedding followed by search."""
        provider = MockEmbeddingProvider()
        store = InMemoryVectorStore()
        embedder = AutoEmbedder(
            embedding_provider=provider,
            vector_store=store
        )

        # Embed objects
        objects = [
            {"id": "int1", "content": "Database optimization techniques"},
            {"id": "int2", "content": "Query performance tuning"},
            {"id": "int3", "content": "Index design patterns"},
        ]
        for obj in objects:
            await embedder.embed_object(obj)

        # Create search engine with same store
        engine = SemanticSearchEngine(
            embedding_provider=provider,
            vector_store=store
        )

        # Search
        query = SemanticQuery(text="database performance", mode=SearchMode.VECTOR, k=3)
        results = await engine.search(query)

        assert len(results.results) >= 1
