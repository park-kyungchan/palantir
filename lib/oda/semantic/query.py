"""
ODA Semantic Layer - Query Models (Phase 4.3.1).

This module defines the query and result models for semantic search operations.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime


class SearchMode(str, Enum):
    """Search mode for semantic queries."""

    VECTOR = "vector"       # Pure vector similarity search
    KEYWORD = "keyword"     # Pure keyword/BM25 search
    HYBRID = "hybrid"       # Combined vector + keyword search


class FilterOperator(str, Enum):
    """Operators for metadata filtering."""

    EQ = "eq"           # Equals
    NE = "ne"           # Not equals
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    IN = "in"           # In list
    NOT_IN = "not_in"   # Not in list
    CONTAINS = "contains"  # String contains


class FilterCondition(BaseModel):
    """Single filter condition for search."""

    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(default=FilterOperator.EQ)
    value: Any = Field(..., description="Value to compare against")

    def matches(self, metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches this condition."""
        if self.field not in metadata:
            return False

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
        elif self.operator == FilterOperator.NOT_IN:
            return field_value not in self.value
        elif self.operator == FilterOperator.CONTAINS:
            return self.value in str(field_value)

        return False


class SemanticQuery(BaseModel):
    """Query model for semantic search operations."""

    text: str = Field(..., min_length=1, description="Query text")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Search mode")
    k: int = Field(default=10, ge=1, le=100, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Simple key-value filters for metadata"
    )
    filter_conditions: Optional[List[FilterCondition]] = Field(
        None,
        description="Advanced filter conditions"
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum score threshold"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata in results"
    )
    include_vectors: bool = Field(
        default=False,
        description="Include vectors in results"
    )
    rerank: bool = Field(
        default=False,
        description="Apply reranking to results"
    )
    rerank_top_k: Optional[int] = Field(
        None,
        ge=1,
        description="Rerank only top K results (for efficiency)"
    )
    vector_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for vector scores in hybrid mode"
    )
    keyword_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for keyword scores in hybrid mode"
    )
    namespaces: Optional[List[str]] = Field(
        None,
        description="Restrict search to specific namespaces"
    )

    @field_validator("vector_weight", "keyword_weight")
    @classmethod
    def validate_weights(cls, v: float) -> float:
        """Ensure weights are between 0 and 1."""
        return max(0.0, min(1.0, v))

    def get_effective_filters(self) -> Optional[Dict[str, Any]]:
        """Get combined filters from simple and condition-based."""
        result = dict(self.filters) if self.filters else {}

        if self.filter_conditions:
            for condition in self.filter_conditions:
                # For simple equality conditions, add to dict
                if condition.operator == FilterOperator.EQ:
                    result[condition.field] = condition.value

        return result if result else None

    def normalize_weights(self) -> "SemanticQuery":
        """Return a copy with normalized weights summing to 1."""
        total = self.vector_weight + self.keyword_weight
        if total == 0:
            return self.model_copy(update={
                "vector_weight": 0.5,
                "keyword_weight": 0.5
            })
        return self.model_copy(update={
            "vector_weight": self.vector_weight / total,
            "keyword_weight": self.keyword_weight / total
        })


class SearchResult(BaseModel):
    """Single search result."""

    id: str = Field(..., description="Document/object ID")
    score: float = Field(..., ge=0.0, le=1.0, description="Combined relevance score")
    text: Optional[str] = Field(None, description="Original text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Associated metadata")
    vector_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Score from vector similarity"
    )
    keyword_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Score from keyword matching"
    )
    rank: Optional[int] = Field(None, ge=0, description="Result rank (0-indexed)")
    rerank_score: Optional[float] = Field(
        None,
        description="Score after reranking"
    )
    matched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of match"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "score": self.score,
            "text": self.text,
            "metadata": self.metadata,
            "vector_score": self.vector_score,
            "keyword_score": self.keyword_score,
            "rank": self.rank,
        }

    @classmethod
    def from_vector_result(
        cls,
        id: str,
        score: float,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        rank: Optional[int] = None
    ) -> "SearchResult":
        """Create from vector search result."""
        return cls(
            id=id,
            score=score,
            vector_score=score,
            text=text,
            metadata=metadata or {},
            rank=rank
        )

    @classmethod
    def from_keyword_result(
        cls,
        id: str,
        score: float,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        rank: Optional[int] = None
    ) -> "SearchResult":
        """Create from keyword search result."""
        return cls(
            id=id,
            score=score,
            keyword_score=score,
            text=text,
            metadata=metadata or {},
            rank=rank
        )


class SearchResultBatch(BaseModel):
    """Batch of search results with metadata."""

    results: List[SearchResult] = Field(default_factory=list)
    query: SemanticQuery
    total_found: int = Field(default=0, ge=0)
    search_time_ms: float = Field(default=0.0, ge=0.0)
    mode_used: SearchMode = Field(default=SearchMode.HYBRID)

    @property
    def count(self) -> int:
        """Number of results returned."""
        return len(self.results)

    @property
    def top_result(self) -> Optional[SearchResult]:
        """Get the top result if available."""
        return self.results[0] if self.results else None

    def filter_by_score(self, min_score: float) -> "SearchResultBatch":
        """Return batch with results above minimum score."""
        filtered = [r for r in self.results if r.score >= min_score]
        return self.model_copy(update={
            "results": filtered,
            "total_found": len(filtered)
        })

    def to_list(self) -> List[Dict[str, Any]]:
        """Convert results to list of dicts."""
        return [r.to_dict() for r in self.results]


class QueryContext(BaseModel):
    """Context for query execution."""

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    include_debug: bool = False
    max_latency_ms: Optional[float] = None
    fallback_mode: SearchMode = SearchMode.VECTOR

    @classmethod
    def create(
        cls,
        session_id: Optional[str] = None,
        debug: bool = False
    ) -> "QueryContext":
        """Create query context."""
        import uuid
        return cls(
            session_id=session_id,
            trace_id=str(uuid.uuid4()),
            include_debug=debug
        )
