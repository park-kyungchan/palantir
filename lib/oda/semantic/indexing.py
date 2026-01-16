"""
Vector Index Management (4.2.4)
===============================
Manages vector indices, including creation, optimization, and maintenance.

Features:
- Index configuration management
- Index lifecycle operations (create, optimize, rebuild)
- Index statistics and health monitoring
- Multi-store index synchronization

Usage:
    from lib.oda.semantic.indexing import VectorIndexManager, IndexConfig

    config = IndexConfig(
        dimension=384,
        metric="cosine",
        index_type="hnsw"
    )
    manager = VectorIndexManager(config)

    # Create index
    await manager.create_index("embeddings")

    # Get index stats
    stats = await manager.get_index_stats("embeddings")
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from lib.oda.semantic.vector_store import (
    VectorStore,
    VectorStoreConfig,
    DistanceMetric,
)


class IndexType(str, Enum):
    """Types of vector indices."""
    FLAT = "flat"           # Brute-force, exact search
    IVF = "ivf"             # Inverted file index
    HNSW = "hnsw"           # Hierarchical Navigable Small World
    PQ = "pq"               # Product Quantization
    IVF_PQ = "ivf_pq"       # IVF with PQ
    SCANN = "scann"         # ScaNN index


class IndexState(str, Enum):
    """State of a vector index."""
    UNINITIALIZED = "uninitialized"
    BUILDING = "building"
    READY = "ready"
    OPTIMIZING = "optimizing"
    ERROR = "error"
    STALE = "stale"


class IndexConfig(BaseModel):
    """Configuration for vector index."""

    dimension: int = Field(
        ...,
        ge=1,
        description="Vector dimension"
    )
    metric: DistanceMetric = Field(
        default=DistanceMetric.COSINE,
        description="Distance metric"
    )
    index_type: IndexType = Field(
        default=IndexType.FLAT,
        description="Type of index"
    )

    # HNSW parameters
    hnsw_m: int = Field(
        default=16,
        ge=2,
        le=100,
        description="HNSW M parameter (edges per node)"
    )
    hnsw_ef_construction: int = Field(
        default=200,
        ge=10,
        le=1000,
        description="HNSW ef_construction parameter"
    )
    hnsw_ef_search: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="HNSW ef_search parameter"
    )

    # IVF parameters
    ivf_nlist: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="IVF number of clusters"
    )
    ivf_nprobe: int = Field(
        default=10,
        ge=1,
        description="IVF number of clusters to probe"
    )

    # PQ parameters
    pq_m: int = Field(
        default=8,
        ge=1,
        description="PQ number of subvectors"
    )
    pq_nbits: int = Field(
        default=8,
        ge=4,
        le=12,
        description="PQ bits per code"
    )

    # General parameters
    auto_optimize: bool = Field(
        default=True,
        description="Automatically optimize index"
    )
    optimize_threshold: int = Field(
        default=10000,
        ge=100,
        description="Optimize after this many vectors"
    )
    rebuild_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Rebuild if fragmentation exceeds this"
    )


class IndexStats(BaseModel):
    """Statistics for a vector index."""

    name: str = Field(..., description="Index name")
    dimension: int = Field(..., description="Vector dimension")
    vector_count: int = Field(default=0, description="Number of vectors")
    index_type: IndexType = Field(default=IndexType.FLAT, description="Index type")
    metric: DistanceMetric = Field(default=DistanceMetric.COSINE, description="Distance metric")
    state: IndexState = Field(default=IndexState.UNINITIALIZED, description="Index state")

    # Performance metrics
    avg_search_time_ms: float = Field(default=0.0, description="Average search time")
    last_search_time_ms: float = Field(default=0.0, description="Last search time")
    total_searches: int = Field(default=0, description="Total searches performed")

    # Health metrics
    fragmentation: float = Field(default=0.0, ge=0.0, le=1.0, description="Index fragmentation")
    memory_usage_mb: float = Field(default=0.0, description="Memory usage in MB")
    disk_usage_mb: float = Field(default=0.0, description="Disk usage in MB")

    # Timestamps
    created_at: Optional[datetime] = Field(default=None, description="Creation time")
    last_optimized_at: Optional[datetime] = Field(default=None, description="Last optimization")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last access")

    @property
    def needs_optimization(self) -> bool:
        """Check if index needs optimization."""
        return self.fragmentation > 0.2

    @property
    def needs_rebuild(self) -> bool:
        """Check if index needs full rebuild."""
        return self.fragmentation > 0.5


@dataclass
class IndexOperation:
    """Record of an index operation."""
    operation: str
    index_name: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class VectorIndexManager:
    """
    Manages vector indices across different stores.

    Provides unified interface for index operations, monitoring, and maintenance.
    """

    def __init__(
        self,
        config: Optional[IndexConfig] = None,
        store: Optional[VectorStore] = None,
        data_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize the index manager.

        Args:
            config: Default index configuration
            store: Optional vector store to manage
            data_dir: Directory for index metadata
        """
        self._config = config or IndexConfig(dimension=384)
        self._store = store
        self._data_dir = Path(data_dir) if data_dir else None

        # Index registry
        self._indices: Dict[str, IndexStats] = {}
        self._operations: List[IndexOperation] = []

        # Callbacks
        self._on_index_ready: List[Callable[[str], None]] = []
        self._on_index_error: List[Callable[[str, str], None]] = []

    async def create_index(
        self,
        name: str,
        config: Optional[IndexConfig] = None,
        store: Optional[VectorStore] = None
    ) -> IndexStats:
        """
        Create a new vector index.

        Args:
            name: Index name
            config: Optional index configuration
            store: Optional vector store (uses manager's store if not provided)

        Returns:
            IndexStats for the created index
        """
        cfg = config or self._config
        target_store = store or self._store

        if target_store is None:
            raise ValueError("No vector store provided")

        # Create stats
        stats = IndexStats(
            name=name,
            dimension=cfg.dimension,
            index_type=cfg.index_type,
            metric=cfg.metric,
            state=IndexState.BUILDING,
            created_at=datetime.now(timezone.utc)
        )

        operation = IndexOperation(
            operation="create",
            index_name=name
        )

        try:
            # Index creation is handled by the store
            # This manager just tracks metadata
            stats.state = IndexState.READY
            stats.vector_count = await target_store.count()
            operation.success = True

            # Notify callbacks
            for callback in self._on_index_ready:
                callback(name)

        except Exception as e:
            stats.state = IndexState.ERROR
            operation.error = str(e)
            operation.success = False

            # Notify error callbacks
            for callback in self._on_index_error:
                callback(name, str(e))

        finally:
            operation.completed_at = datetime.now(timezone.utc)
            operation.duration_ms = (
                operation.completed_at - operation.started_at
            ).total_seconds() * 1000
            self._operations.append(operation)

        self._indices[name] = stats
        return stats

    async def optimize_index(
        self,
        name: str,
        store: Optional[VectorStore] = None
    ) -> IndexStats:
        """
        Optimize an existing index.

        Args:
            name: Index name
            store: Optional vector store

        Returns:
            Updated IndexStats
        """
        if name not in self._indices:
            raise ValueError(f"Index '{name}' not found")

        stats = self._indices[name]
        stats.state = IndexState.OPTIMIZING

        operation = IndexOperation(
            operation="optimize",
            index_name=name
        )

        try:
            # Optimization logic depends on the store type
            # For now, this is a placeholder that updates stats
            target_store = store or self._store

            if target_store is not None:
                # Refresh count
                stats.vector_count = await target_store.count()

            # Simulate optimization
            stats.fragmentation = max(0.0, stats.fragmentation * 0.5)
            stats.state = IndexState.READY
            stats.last_optimized_at = datetime.now(timezone.utc)
            operation.success = True

        except Exception as e:
            stats.state = IndexState.ERROR
            operation.error = str(e)
            operation.success = False

        finally:
            operation.completed_at = datetime.now(timezone.utc)
            operation.duration_ms = (
                operation.completed_at - operation.started_at
            ).total_seconds() * 1000
            self._operations.append(operation)

        return stats

    async def rebuild_index(
        self,
        name: str,
        store: Optional[VectorStore] = None
    ) -> IndexStats:
        """
        Rebuild an index from scratch.

        Args:
            name: Index name
            store: Optional vector store

        Returns:
            Updated IndexStats
        """
        if name not in self._indices:
            raise ValueError(f"Index '{name}' not found")

        stats = self._indices[name]
        stats.state = IndexState.BUILDING

        operation = IndexOperation(
            operation="rebuild",
            index_name=name
        )

        try:
            target_store = store or self._store

            if target_store is not None:
                stats.vector_count = await target_store.count()

            # Reset fragmentation after rebuild
            stats.fragmentation = 0.0
            stats.state = IndexState.READY
            stats.last_optimized_at = datetime.now(timezone.utc)
            operation.success = True

        except Exception as e:
            stats.state = IndexState.ERROR
            operation.error = str(e)
            operation.success = False

        finally:
            operation.completed_at = datetime.now(timezone.utc)
            operation.duration_ms = (
                operation.completed_at - operation.started_at
            ).total_seconds() * 1000
            self._operations.append(operation)

        return stats

    async def delete_index(self, name: str) -> bool:
        """
        Delete an index.

        Args:
            name: Index name

        Returns:
            True if deleted
        """
        if name not in self._indices:
            return False

        operation = IndexOperation(
            operation="delete",
            index_name=name
        )

        try:
            del self._indices[name]
            operation.success = True
            return True

        except Exception as e:
            operation.error = str(e)
            operation.success = False
            return False

        finally:
            operation.completed_at = datetime.now(timezone.utc)
            operation.duration_ms = (
                operation.completed_at - operation.started_at
            ).total_seconds() * 1000
            self._operations.append(operation)

    async def get_index_stats(
        self,
        name: str,
        store: Optional[VectorStore] = None
    ) -> Optional[IndexStats]:
        """
        Get statistics for an index.

        Args:
            name: Index name
            store: Optional vector store

        Returns:
            IndexStats if found
        """
        if name not in self._indices:
            return None

        stats = self._indices[name]
        target_store = store or self._store

        # Refresh stats from store
        if target_store is not None:
            stats.vector_count = await target_store.count()
            stats.last_accessed_at = datetime.now(timezone.utc)

        return stats

    async def list_indices(self) -> List[IndexStats]:
        """
        List all managed indices.

        Returns:
            List of IndexStats
        """
        return list(self._indices.values())

    async def check_health(self, name: str) -> Dict[str, Any]:
        """
        Check health of an index.

        Args:
            name: Index name

        Returns:
            Health check results
        """
        stats = await self.get_index_stats(name)
        if stats is None:
            return {
                "healthy": False,
                "error": f"Index '{name}' not found"
            }

        issues = []

        if stats.state == IndexState.ERROR:
            issues.append("Index is in error state")

        if stats.needs_rebuild:
            issues.append(f"High fragmentation: {stats.fragmentation:.1%}")
        elif stats.needs_optimization:
            issues.append(f"Fragmentation: {stats.fragmentation:.1%}")

        if stats.vector_count == 0:
            issues.append("Index is empty")

        return {
            "healthy": len(issues) == 0 and stats.state == IndexState.READY,
            "state": stats.state.value,
            "vector_count": stats.vector_count,
            "fragmentation": stats.fragmentation,
            "issues": issues,
            "recommendations": self._get_recommendations(stats)
        }

    def _get_recommendations(self, stats: IndexStats) -> List[str]:
        """Get recommendations for index maintenance."""
        recommendations = []

        if stats.needs_rebuild:
            recommendations.append(
                f"Consider rebuilding index (fragmentation: {stats.fragmentation:.1%})"
            )
        elif stats.needs_optimization:
            recommendations.append(
                f"Consider optimizing index (fragmentation: {stats.fragmentation:.1%})"
            )

        if stats.index_type == IndexType.FLAT and stats.vector_count > 10000:
            recommendations.append(
                "Consider using HNSW index for better performance with large datasets"
            )

        return recommendations

    def record_search(
        self,
        index_name: str,
        duration_ms: float,
        results_count: int = 0
    ) -> None:
        """
        Record a search operation for metrics.

        Args:
            index_name: Index name
            duration_ms: Search duration in milliseconds
            results_count: Number of results returned
        """
        if index_name not in self._indices:
            return

        stats = self._indices[index_name]
        stats.total_searches += 1
        stats.last_search_time_ms = duration_ms
        stats.last_accessed_at = datetime.now(timezone.utc)

        # Update rolling average
        if stats.total_searches == 1:
            stats.avg_search_time_ms = duration_ms
        else:
            # Exponential moving average
            alpha = 0.1
            stats.avg_search_time_ms = (
                alpha * duration_ms +
                (1 - alpha) * stats.avg_search_time_ms
            )

    def update_fragmentation(
        self,
        index_name: str,
        deleted_count: int,
        total_count: int
    ) -> None:
        """
        Update fragmentation estimate after deletions.

        Args:
            index_name: Index name
            deleted_count: Number of deleted vectors
            total_count: Total vectors including deleted
        """
        if index_name not in self._indices or total_count == 0:
            return

        stats = self._indices[index_name]
        stats.fragmentation = deleted_count / total_count

        if stats.fragmentation > stats.fragmentation:
            stats.state = IndexState.STALE

    def on_index_ready(self, callback: Callable[[str], None]) -> None:
        """Register callback for when index becomes ready."""
        self._on_index_ready.append(callback)

    def on_index_error(self, callback: Callable[[str, str], None]) -> None:
        """Register callback for index errors."""
        self._on_index_error.append(callback)

    def get_operations_history(
        self,
        index_name: Optional[str] = None,
        limit: int = 100
    ) -> List[IndexOperation]:
        """
        Get history of index operations.

        Args:
            index_name: Optional filter by index name
            limit: Maximum number of operations to return

        Returns:
            List of IndexOperation
        """
        ops = self._operations
        if index_name:
            ops = [op for op in ops if op.index_name == index_name]
        return ops[-limit:]


class IndexBuilder:
    """
    Builder for creating vector indices with fluent API.

    Usage:
        index = (IndexBuilder()
            .with_dimension(384)
            .with_metric(DistanceMetric.COSINE)
            .with_hnsw(m=32, ef_construction=400)
            .build())
    """

    def __init__(self):
        """Initialize builder with defaults."""
        self._dimension: int = 384
        self._metric: DistanceMetric = DistanceMetric.COSINE
        self._index_type: IndexType = IndexType.FLAT
        self._hnsw_m: int = 16
        self._hnsw_ef_construction: int = 200
        self._hnsw_ef_search: int = 100
        self._ivf_nlist: int = 100
        self._ivf_nprobe: int = 10
        self._pq_m: int = 8
        self._pq_nbits: int = 8

    def with_dimension(self, dimension: int) -> "IndexBuilder":
        """Set vector dimension."""
        self._dimension = dimension
        return self

    def with_metric(self, metric: DistanceMetric) -> "IndexBuilder":
        """Set distance metric."""
        self._metric = metric
        return self

    def with_flat(self) -> "IndexBuilder":
        """Use flat (brute-force) index."""
        self._index_type = IndexType.FLAT
        return self

    def with_hnsw(
        self,
        m: int = 16,
        ef_construction: int = 200,
        ef_search: int = 100
    ) -> "IndexBuilder":
        """Use HNSW index with parameters."""
        self._index_type = IndexType.HNSW
        self._hnsw_m = m
        self._hnsw_ef_construction = ef_construction
        self._hnsw_ef_search = ef_search
        return self

    def with_ivf(
        self,
        nlist: int = 100,
        nprobe: int = 10
    ) -> "IndexBuilder":
        """Use IVF index with parameters."""
        self._index_type = IndexType.IVF
        self._ivf_nlist = nlist
        self._ivf_nprobe = nprobe
        return self

    def with_pq(
        self,
        m: int = 8,
        nbits: int = 8
    ) -> "IndexBuilder":
        """Use PQ compression with parameters."""
        self._index_type = IndexType.PQ
        self._pq_m = m
        self._pq_nbits = nbits
        return self

    def build(self) -> IndexConfig:
        """Build the index configuration."""
        return IndexConfig(
            dimension=self._dimension,
            metric=self._metric,
            index_type=self._index_type,
            hnsw_m=self._hnsw_m,
            hnsw_ef_construction=self._hnsw_ef_construction,
            hnsw_ef_search=self._hnsw_ef_search,
            ivf_nlist=self._ivf_nlist,
            ivf_nprobe=self._ivf_nprobe,
            pq_m=self._pq_m,
            pq_nbits=self._pq_nbits
        )
