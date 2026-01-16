"""
ChromaDB Vector Store (4.2.3)
=============================
Implementation of VectorStore using ChromaDB.

ChromaDB is a modern vector database optimized for AI applications,
providing efficient similarity search with metadata filtering.

Requirements:
    pip install chromadb

Usage:
    from lib.oda.semantic.stores.chroma import ChromaDBStore

    store = ChromaDBStore(
        collection_name="embeddings",
        dimension=384,
        persist_directory="./chroma_data"
    )

    await store.add("doc1", vector, metadata={"type": "document"})
    results = await store.search(query_vector, k=10)
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lib.oda.semantic.vector_store import (
    VectorStore,
    VectorStoreConfig,
    VectorRecord,
    VectorSearchResult,
    MetadataFilter,
    FilterOperator,
    DistanceMetric,
    VectorStoreError,
    VectorDimensionError,
    _normalize_vector,
)


class ChromaDBStore(VectorStore):
    """
    ChromaDB vector store implementation.

    Supports persistent and ephemeral storage, metadata filtering,
    and multiple distance metrics.
    """

    # Map our distance metrics to ChromaDB
    METRIC_MAP = {
        DistanceMetric.COSINE: "cosine",
        DistanceMetric.EUCLIDEAN: "l2",
        DistanceMetric.DOT_PRODUCT: "ip",
    }

    def __init__(
        self,
        collection_name: str = "embeddings",
        dimension: int = 384,
        persist_directory: Optional[Union[str, Path]] = None,
        config: Optional[VectorStoreConfig] = None,
        **kwargs
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the ChromaDB collection
            dimension: Vector dimension
            persist_directory: Directory for persistent storage (None for ephemeral)
            config: Optional VectorStoreConfig
        """
        if config is None:
            config = VectorStoreConfig(dimension=dimension)
        super().__init__(config)

        self._collection_name = collection_name
        self._dimension = dimension
        self._persist_directory = str(persist_directory) if persist_directory else None
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None
        self._executor = ThreadPoolExecutor(max_workers=1)

        # Initialize client
        self._init_client()

    def _init_client(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise VectorStoreError(
                "chromadb package is required. Install with: pip install chromadb"
            )

        # Create client
        if self._persist_directory:
            Path(self._persist_directory).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self._persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self._client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )

        # Get distance metric
        metric = self.METRIC_MAP.get(
            self._config.metric if self._config else DistanceMetric.COSINE,
            "cosine"
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": metric}
        )

    def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous function in the executor."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            self._executor,
            lambda: func(*args, **kwargs)
        )

    async def add(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> None:
        """Add a vector to the store."""
        # Validate dimension
        if len(vector) != self._dimension:
            raise VectorDimensionError(
                f"Vector dimension {len(vector)} does not match "
                f"store dimension {self._dimension}"
            )

        # Normalize if configured
        if self._config and self._config.normalize_vectors:
            vector = _normalize_vector(vector)

        await self._run_sync(
            self._add_sync, id, vector, metadata, text
        )

    def _add_sync(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]],
        text: Optional[str]
    ) -> None:
        """Synchronous add operation."""
        # Prepare metadata (ChromaDB has restrictions on types)
        safe_metadata = self._sanitize_metadata(metadata or {})
        safe_metadata["_created_at"] = datetime.now(timezone.utc).isoformat()

        # Add or update
        self._collection.upsert(
            ids=[id],
            embeddings=[vector],
            metadatas=[safe_metadata],
            documents=[text] if text else None
        )

    async def add_batch(self, records: List[VectorRecord]) -> int:
        """Add multiple vectors."""
        if not records:
            return 0

        # Validate dimensions
        for record in records:
            if len(record.vector) != self._dimension:
                raise VectorDimensionError(
                    f"Vector dimension {len(record.vector)} does not match "
                    f"store dimension {self._dimension}"
                )

        return await self._run_sync(self._add_batch_sync, records)

    def _add_batch_sync(self, records: List[VectorRecord]) -> int:
        """Synchronous batch add."""
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for record in records:
            vector = record.vector
            if self._config and self._config.normalize_vectors:
                vector = _normalize_vector(vector)

            ids.append(record.id)
            embeddings.append(vector)

            safe_metadata = self._sanitize_metadata(record.metadata or {})
            safe_metadata["_created_at"] = record.created_at.isoformat()
            metadatas.append(safe_metadata)

            documents.append(record.text)

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
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
        """Search for similar vectors."""
        # Validate dimension
        if len(query_vector) != self._dimension:
            raise VectorDimensionError(
                f"Query vector dimension {len(query_vector)} does not match "
                f"store dimension {self._dimension}"
            )

        # Normalize if configured
        if self._config and self._config.normalize_vectors:
            query_vector = _normalize_vector(query_vector)

        return await self._run_sync(
            self._search_sync,
            query_vector, k, filters, include_vectors, include_metadata, score_threshold
        )

    def _search_sync(
        self,
        query_vector: List[float],
        k: int,
        filters: Optional[Union[Dict[str, Any], List[MetadataFilter]]],
        include_vectors: bool,
        include_metadata: bool,
        score_threshold: Optional[float]
    ) -> List[VectorSearchResult]:
        """Synchronous search operation."""
        # Build where clause for filters
        where = None
        if filters:
            where = self._build_where_clause(filters)

        # Build include list
        include = ["documents", "distances"]
        if include_metadata:
            include.append("metadatas")
        if include_vectors:
            include.append("embeddings")

        # Query collection
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where,
            include=include
        )

        # Parse results
        search_results = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            distances = results.get("distances", [[]])[0]
            embeddings = results.get("embeddings", [[]])[0] if include_vectors else [None] * len(ids)
            metadatas = results.get("metadatas", [[]])[0] if include_metadata else [{}] * len(ids)
            documents = results.get("documents", [[]])[0]

            for i, id in enumerate(ids):
                # Convert distance to score (ChromaDB returns distance, lower is better)
                distance = distances[i] if i < len(distances) else 0.0
                score = self._distance_to_score(distance)

                # Apply threshold
                if score_threshold is not None and score < score_threshold:
                    continue

                # Clean metadata
                metadata = dict(metadatas[i]) if i < len(metadatas) and metadatas[i] else {}
                # Remove internal fields
                metadata.pop("_created_at", None)

                result = VectorSearchResult(
                    id=id,
                    score=score,
                    distance=distance,
                    vector=list(embeddings[i]) if embeddings[i] else None,
                    metadata=metadata,
                    text=documents[i] if i < len(documents) else None
                )
                search_results.append(result)

        return search_results

    def _distance_to_score(self, distance: float) -> float:
        """Convert ChromaDB distance to similarity score."""
        metric = self._config.metric if self._config else DistanceMetric.COSINE

        if metric == DistanceMetric.COSINE:
            # Cosine distance in ChromaDB is 1 - cosine_similarity
            return max(0.0, min(1.0, 1.0 - distance))
        elif metric == DistanceMetric.DOT_PRODUCT:
            # Inner product: higher is better, but ChromaDB returns negative
            return max(0.0, min(1.0, (1.0 - distance) / 2.0))
        else:
            # Euclidean: use exponential decay
            import math
            return math.exp(-distance)

    def _build_where_clause(
        self,
        filters: Union[Dict[str, Any], List[MetadataFilter]]
    ) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters."""
        if isinstance(filters, dict):
            # Simple equality filters
            if len(filters) == 1:
                key, value = next(iter(filters.items()))
                return {key: {"$eq": value}}
            else:
                return {
                    "$and": [
                        {key: {"$eq": value}}
                        for key, value in filters.items()
                    ]
                }

        # MetadataFilter list
        conditions = []
        for f in filters:
            op_map = {
                FilterOperator.EQ: "$eq",
                FilterOperator.NE: "$ne",
                FilterOperator.GT: "$gt",
                FilterOperator.GTE: "$gte",
                FilterOperator.LT: "$lt",
                FilterOperator.LTE: "$lte",
                FilterOperator.IN: "$in",
                FilterOperator.NIN: "$nin",
            }

            if f.operator in op_map:
                conditions.append({
                    f.field: {op_map[f.operator]: f.value}
                })
            elif f.operator == FilterOperator.CONTAINS:
                # ChromaDB doesn't have contains, use $eq for exact match
                conditions.append({
                    f.field: {"$eq": f.value}
                })

        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    @staticmethod
    def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata for ChromaDB.

        ChromaDB only supports str, int, float, bool in metadata.
        """
        result = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                result[key] = value
            elif isinstance(value, (list, dict)):
                # Convert complex types to JSON string
                import json
                result[key] = json.dumps(value)
            elif value is None:
                result[key] = ""
            else:
                result[key] = str(value)
        return result

    async def get(self, id: str) -> Optional[VectorRecord]:
        """Get a specific vector by ID."""
        return await self._run_sync(self._get_sync, id)

    def _get_sync(self, id: str) -> Optional[VectorRecord]:
        """Synchronous get operation."""
        results = self._collection.get(
            ids=[id],
            include=["embeddings", "metadatas", "documents"]
        )

        if not results or not results.get("ids"):
            return None

        if not results["ids"]:
            return None

        metadata = results["metadatas"][0] if results.get("metadatas") else {}
        created_at_str = metadata.pop("_created_at", None)
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc)

        return VectorRecord(
            id=results["ids"][0],
            vector=list(results["embeddings"][0]) if results.get("embeddings") else [],
            metadata=metadata,
            text=results["documents"][0] if results.get("documents") else None,
            created_at=created_at
        )

    async def get_batch(self, ids: List[str]) -> List[VectorRecord]:
        """Get multiple vectors by IDs."""
        return await self._run_sync(self._get_batch_sync, ids)

    def _get_batch_sync(self, ids: List[str]) -> List[VectorRecord]:
        """Synchronous batch get."""
        results = self._collection.get(
            ids=ids,
            include=["embeddings", "metadatas", "documents"]
        )

        records = []
        if results and results.get("ids"):
            for i, id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                created_at_str = metadata.pop("_created_at", None)
                created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc)

                records.append(VectorRecord(
                    id=id,
                    vector=list(results["embeddings"][i]) if results.get("embeddings") else [],
                    metadata=metadata,
                    text=results["documents"][i] if results.get("documents") else None,
                    created_at=created_at
                ))

        return records

    async def delete(self, id: str) -> bool:
        """Delete a vector by ID."""
        return await self._run_sync(self._delete_sync, id)

    def _delete_sync(self, id: str) -> bool:
        """Synchronous delete operation."""
        # Check if exists first
        results = self._collection.get(ids=[id])
        if not results or not results.get("ids"):
            return False

        self._collection.delete(ids=[id])
        return True

    async def delete_batch(self, ids: List[str]) -> int:
        """Delete multiple vectors."""
        return await self._run_sync(self._delete_batch_sync, ids)

    def _delete_batch_sync(self, ids: List[str]) -> int:
        """Synchronous batch delete."""
        # Get existing IDs
        results = self._collection.get(ids=ids)
        existing_ids = results.get("ids", []) if results else []

        if existing_ids:
            self._collection.delete(ids=existing_ids)

        return len(existing_ids)

    async def update(
        self,
        id: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> bool:
        """Update an existing vector."""
        return await self._run_sync(
            self._update_sync, id, vector, metadata, text
        )

    def _update_sync(
        self,
        id: str,
        vector: Optional[List[float]],
        metadata: Optional[Dict[str, Any]],
        text: Optional[str]
    ) -> bool:
        """Synchronous update operation."""
        # Get current record
        results = self._collection.get(
            ids=[id],
            include=["embeddings", "metadatas", "documents"]
        )

        if not results or not results.get("ids"):
            return False

        # Prepare update data
        update_embeddings = None
        update_metadatas = None
        update_documents = None

        if vector is not None:
            if self._config and self._config.normalize_vectors:
                vector = _normalize_vector(vector)
            update_embeddings = [vector]

        if metadata is not None:
            current_metadata = results["metadatas"][0] if results.get("metadatas") else {}
            current_metadata.update(self._sanitize_metadata(metadata))
            update_metadatas = [current_metadata]

        if text is not None:
            update_documents = [text]

        # Update
        self._collection.update(
            ids=[id],
            embeddings=update_embeddings,
            metadatas=update_metadatas,
            documents=update_documents
        )

        return True

    async def count(self) -> int:
        """Count total vectors."""
        return await self._run_sync(self._count_sync)

    def _count_sync(self) -> int:
        """Synchronous count."""
        return self._collection.count()

    async def close(self) -> None:
        """Close the store."""
        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None

    async def reset(self) -> None:
        """Reset the collection (delete all data)."""
        await self._run_sync(self._reset_sync)

    def _reset_sync(self) -> None:
        """Synchronous reset."""
        self._client.delete_collection(self._collection_name)
        metric = self.METRIC_MAP.get(
            self._config.metric if self._config else DistanceMetric.COSINE,
            "cosine"
        )
        self._collection = self._client.create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": metric}
        )
