"""
ODA Semantic Layer - Semantic Ranking (Phase 4.3.4).

This module provides reranking capabilities for search results
using cross-encoder models or other ranking strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from pydantic import BaseModel, Field
import math

from lib.oda.semantic.query import SearchResult


class RankingStrategy(str, Enum):
    """Available ranking strategies."""

    CROSS_ENCODER = "cross_encoder"     # Use cross-encoder model
    BM25_RERANK = "bm25_rerank"         # BM25-based reranking
    SEMANTIC_SIMILARITY = "semantic"     # Re-score with embeddings
    MMR = "mmr"                          # Maximal Marginal Relevance
    LINEAR_COMBINATION = "linear"        # Linear score combination
    LEARNED = "learned"                  # Learned ranking model


class RankingConfig(BaseModel):
    """Configuration for ranking operations."""

    strategy: RankingStrategy = Field(
        default=RankingStrategy.LINEAR_COMBINATION,
        description="Ranking strategy to use"
    )
    top_k: Optional[int] = Field(
        None,
        ge=1,
        description="Limit reranking to top K results"
    )
    diversity_lambda: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Diversity factor for MMR (0=relevance, 1=diversity)"
    )
    model_name: Optional[str] = Field(
        None,
        description="Cross-encoder model name if using cross_encoder strategy"
    )
    score_weights: Dict[str, float] = Field(
        default_factory=lambda: {"vector": 0.5, "keyword": 0.5},
        description="Weights for score combination"
    )


class RankingResult(BaseModel):
    """Result of a ranking operation."""

    original_results: List[SearchResult]
    reranked_results: List[SearchResult]
    strategy_used: RankingStrategy
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SemanticRanker:
    """
    Reranks search results using various strategies.

    Supports:
    - Cross-encoder reranking (when model is available)
    - BM25-based reranking
    - Maximal Marginal Relevance (MMR) for diversity
    - Linear score combination
    """

    def __init__(
        self,
        config: Optional[RankingConfig] = None,
        cross_encoder: Optional[Any] = None  # Optional cross-encoder model
    ):
        self.config = config or RankingConfig()
        self.cross_encoder = cross_encoder

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: Optional[int] = None,
        strategy: Optional[RankingStrategy] = None
    ) -> List[SearchResult]:
        """
        Rerank search results.

        Args:
            query: Original query text
            results: Initial search results
            top_k: Limit to top K after reranking
            strategy: Override default strategy

        Returns:
            Reranked list of SearchResult
        """
        if not results:
            return []

        effective_strategy = strategy or self.config.strategy
        effective_top_k = top_k or self.config.top_k

        # Apply strategy
        if effective_strategy == RankingStrategy.CROSS_ENCODER:
            reranked = await self._cross_encoder_rerank(query, results)
        elif effective_strategy == RankingStrategy.BM25_RERANK:
            reranked = self._bm25_rerank(query, results)
        elif effective_strategy == RankingStrategy.MMR:
            reranked = self._mmr_rerank(query, results)
        elif effective_strategy == RankingStrategy.SEMANTIC_SIMILARITY:
            reranked = await self._semantic_rerank(query, results)
        elif effective_strategy == RankingStrategy.LINEAR_COMBINATION:
            reranked = self._linear_combination_rerank(results)
        else:
            reranked = results

        # Apply top_k limit
        if effective_top_k:
            reranked = reranked[:effective_top_k]

        # Update ranks and rerank scores
        for i, result in enumerate(reranked):
            result.rank = i
            if result.rerank_score is None:
                result.rerank_score = result.score

        return reranked

    async def _cross_encoder_rerank(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Rerank using cross-encoder model.

        Cross-encoders score query-document pairs together
        for more accurate relevance estimation.
        """
        if self.cross_encoder is None:
            # Fallback to linear combination if no cross-encoder
            return self._linear_combination_rerank(results)

        # Score all query-document pairs
        scores = []
        for result in results:
            if result.text:
                # Cross-encoder would compute: score = model(query, result.text)
                # Placeholder for actual cross-encoder call
                score = await self._compute_cross_encoder_score(query, result.text)
            else:
                score = result.score
            scores.append((result, score))

        # Sort by cross-encoder score
        scores.sort(key=lambda x: x[1], reverse=True)

        # Update results with rerank scores
        reranked = []
        for result, score in scores:
            result_copy = result.model_copy()
            result_copy.rerank_score = score
            result_copy.score = score
            reranked.append(result_copy)

        return reranked

    async def _compute_cross_encoder_score(
        self,
        query: str,
        document: str
    ) -> float:
        """Compute cross-encoder score for query-document pair."""
        # Placeholder - actual implementation would call the model
        # For now, use a simple heuristic based on word overlap
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())

        if not query_words or not doc_words:
            return 0.0

        overlap = len(query_words & doc_words)
        return overlap / len(query_words)

    def _bm25_rerank(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Rerank using BM25 scoring."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return results

        # BM25 parameters
        k1 = 1.5
        b = 0.75

        # Calculate average document length
        doc_lengths = []
        for r in results:
            if r.text:
                doc_lengths.append(len(self._tokenize(r.text)))
        avg_doc_len = sum(doc_lengths) / max(1, len(doc_lengths)) if doc_lengths else 1

        # Score each result
        scored = []
        for result in results:
            if not result.text:
                scored.append((result, result.score))
                continue

            doc_terms = self._tokenize(result.text)
            doc_len = len(doc_terms)

            bm25_score = 0.0
            for term in query_terms:
                tf = doc_terms.count(term)
                if tf == 0:
                    continue

                # IDF approximation (would need corpus stats for real IDF)
                idf = math.log(len(results) + 1)

                # BM25 term score
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                bm25_score += idf * numerator / denominator

            # Normalize and combine with existing score
            normalized_bm25 = min(1.0, bm25_score / (len(query_terms) * 10))
            combined = 0.5 * result.score + 0.5 * normalized_bm25
            scored.append((result, combined))

        scored.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for result, score in scored:
            result_copy = result.model_copy()
            result_copy.rerank_score = score
            result_copy.score = score
            reranked.append(result_copy)

        return reranked

    def _mmr_rerank(
        self,
        query: str,
        results: List[SearchResult],
        lambda_param: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Rerank using Maximal Marginal Relevance for diversity.

        MMR = lambda * Sim(query, doc) - (1 - lambda) * max(Sim(doc, selected))

        Args:
            query: Original query
            results: Initial results
            lambda_param: Diversity factor (0=diversity, 1=relevance)

        Returns:
            Reranked results with diversity
        """
        if not results:
            return []

        lambda_val = lambda_param or self.config.diversity_lambda

        # Initialize with first result (highest relevance)
        selected: List[SearchResult] = [results[0].model_copy()]
        selected[0].rerank_score = selected[0].score
        remaining = [r.model_copy() for r in results[1:]]

        while remaining and len(selected) < len(results):
            best_score = float('-inf')
            best_idx = 0

            for i, candidate in enumerate(remaining):
                # Relevance to query (use existing score)
                relevance = candidate.score

                # Maximum similarity to already selected documents
                max_sim = 0.0
                for sel in selected:
                    sim = self._text_similarity(candidate.text or "", sel.text or "")
                    max_sim = max(max_sim, sim)

                # MMR score
                mmr_score = lambda_val * relevance - (1 - lambda_val) * max_sim

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            # Move best candidate to selected
            best = remaining.pop(best_idx)
            best.rerank_score = best_score
            best.score = max(0, min(1, (best_score + 1) / 2))  # Normalize to 0-1
            selected.append(best)

        return selected

    async def _semantic_rerank(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Rerank by recalculating semantic similarity."""
        # Placeholder - would use embedding provider to recalculate similarities
        # For now, use existing vector scores if available
        scored = []
        for result in results:
            if result.vector_score is not None:
                score = result.vector_score
            else:
                score = result.score
            scored.append((result, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for result, score in scored:
            result_copy = result.model_copy()
            result_copy.rerank_score = score
            result_copy.score = score
            reranked.append(result_copy)

        return reranked

    def _linear_combination_rerank(
        self,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Rerank using weighted linear combination of scores."""
        weights = self.config.score_weights

        scored = []
        for result in results:
            vector_score = result.vector_score or 0.0
            keyword_score = result.keyword_score or 0.0

            combined = (
                weights.get("vector", 0.5) * vector_score +
                weights.get("keyword", 0.5) * keyword_score
            )

            # If neither score is available, use the original score
            if result.vector_score is None and result.keyword_score is None:
                combined = result.score

            scored.append((result, combined))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Normalize scores
        if scored:
            max_score = max(s[1] for s in scored)
            if max_score > 0:
                scored = [(r, s / max_score) for r, s in scored]

        reranked = []
        for result, score in scored:
            result_copy = result.model_copy()
            result_copy.rerank_score = score
            result_copy.score = score
            reranked.append(result_copy)

        return reranked

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenization."""
        import re
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """Calculate simple text similarity using Jaccard."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / max(1, union)


class RankerPipeline:
    """
    Pipeline for chaining multiple ranking stages.

    Example:
        pipeline = RankerPipeline()
        pipeline.add_stage(SemanticRanker(config=RankingConfig(strategy=RankingStrategy.BM25_RERANK)))
        pipeline.add_stage(SemanticRanker(config=RankingConfig(strategy=RankingStrategy.MMR)))
        results = await pipeline.run(query, initial_results)
    """

    def __init__(self):
        self.stages: List[SemanticRanker] = []

    def add_stage(self, ranker: SemanticRanker) -> "RankerPipeline":
        """Add a ranking stage to the pipeline."""
        self.stages.append(ranker)
        return self

    async def run(
        self,
        query: str,
        results: List[SearchResult],
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """Run all ranking stages in sequence."""
        current_results = results

        for stage in self.stages:
            current_results = await stage.rerank(
                query=query,
                results=current_results,
                top_k=None  # Apply top_k only at the end
            )

        if top_k:
            current_results = current_results[:top_k]

        return current_results


class DiversityRanker(SemanticRanker):
    """
    Specialized ranker focused on result diversity.

    Ensures search results cover different aspects/topics
    rather than returning many similar results.
    """

    def __init__(
        self,
        diversity_threshold: float = 0.7,
        min_diversity_ratio: float = 0.3
    ):
        """
        Args:
            diversity_threshold: Similarity threshold for considering items diverse
            min_diversity_ratio: Minimum ratio of diverse items in results
        """
        config = RankingConfig(strategy=RankingStrategy.MMR)
        super().__init__(config)
        self.diversity_threshold = diversity_threshold
        self.min_diversity_ratio = min_diversity_ratio

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: Optional[int] = None,
        strategy: Optional[RankingStrategy] = None
    ) -> List[SearchResult]:
        """Rerank with diversity enforcement."""
        if len(results) <= 1:
            return results

        # First pass: MMR reranking
        mmr_results = self._mmr_rerank(query, results)

        # Second pass: ensure minimum diversity
        diverse_results = self._ensure_diversity(mmr_results)

        if top_k:
            diverse_results = diverse_results[:top_k]

        return diverse_results

    def _ensure_diversity(
        self,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Ensure minimum diversity in results."""
        if len(results) <= 1:
            return results

        diverse = [results[0]]

        for candidate in results[1:]:
            is_diverse = True
            for existing in diverse:
                sim = self._text_similarity(candidate.text or "", existing.text or "")
                if sim > self.diversity_threshold:
                    is_diverse = False
                    break

            if is_diverse:
                diverse.append(candidate)

        # If not enough diverse results, add remaining by score
        if len(diverse) < len(results) * self.min_diversity_ratio:
            remaining = [r for r in results if r not in diverse]
            diverse.extend(remaining)

        return diverse
