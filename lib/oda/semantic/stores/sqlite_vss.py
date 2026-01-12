"""
SQLite-VSS Vector Store (4.2.2)
===============================
Implementation of VectorStore using SQLite with sqlite-vss extension.

SQLite-VSS provides vector similarity search capabilities directly in SQLite,
making it ideal for local, embedded vector storage without external services.

Requirements:
    pip install sqlite-vss

Usage:
    from lib.oda.semantic.stores.sqlite_vss import SQLiteVSSStore

    store = SQLiteVSSStore(
        db_path="vectors.db",
        dimension=384,
        table_name="embeddings"
    )

    await store.add("doc1", vector, metadata={"type": "document"})
    results = await store.search(query_vector, k=10)
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
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
    DistanceMetric,
    VectorStoreError,
    VectorDimensionError,
    _normalize_vector,
)


class SQLiteVSSStore(VectorStore):
    """
    SQLite-VSS vector store implementation.

    Uses sqlite-vss extension for efficient vector similarity search.
    Supports cosine similarity, L2 distance, and metadata filtering.
    """

    def __init__(
        self,
        db_path: Union[str, Path] = ":memory:",
        dimension: int = 384,
        table_name: str = "vectors",
        config: Optional[VectorStoreConfig] = None,
        **kwargs
    ):
        """
        Initialize SQLite-VSS vector store.

        Args:
            db_path: Path to SQLite database file (":memory:" for in-memory)
            dimension: Vector dimension
            table_name: Name of the vector table
            config: Optional VectorStoreConfig
        """
        if config is None:
            config = VectorStoreConfig(dimension=dimension)
        super().__init__(config)

        self._db_path = str(db_path)
        self._table_name = table_name
        self._dimension = dimension
        self._conn: Optional[sqlite3.Connection] = None
        self._vss_loaded = False
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = threading.RLock()

        # Initialize synchronously
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database and load VSS extension."""
        with self._lock:
            self._conn = sqlite3.connect(
                self._db_path,
                check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row

            # Try to load VSS extension
            try:
                self._conn.enable_load_extension(True)
                # Try different extension paths
                vss_paths = [
                    "vss0",
                    "sqlite-vss",
                    "/usr/local/lib/sqlite-vss/vss0",
                    "/usr/lib/sqlite-vss/vss0",
                ]
                for path in vss_paths:
                    try:
                        self._conn.load_extension(path)
                        self._vss_loaded = True
                        break
                    except sqlite3.OperationalError:
                        continue

            except Exception:
                # VSS extension not available, use fallback
                self._vss_loaded = False

            # Create tables
            self._create_tables()

    def _create_tables(self) -> None:
        """Create necessary tables."""
        # Main data table
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                id TEXT PRIMARY KEY,
                vector_json TEXT NOT NULL,
                metadata_json TEXT,
                text_content TEXT,
                created_at REAL NOT NULL,
                updated_at REAL
            )
        """)

        # Create VSS virtual table if extension is loaded
        if self._vss_loaded:
            try:
                self._conn.execute(f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS {self._table_name}_vss
                    USING vss0(vector({self._dimension}))
                """)
            except sqlite3.OperationalError:
                # VSS table creation failed, use fallback
                self._vss_loaded = False

        # Create index for faster lookups
        self._conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self._table_name}_created
            ON {self._table_name}(created_at)
        """)

        self._conn.commit()

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
        with self._lock:
            now = datetime.now(timezone.utc).timestamp()

            # Insert into main table
            self._conn.execute(f"""
                INSERT OR REPLACE INTO {self._table_name}
                (id, vector_json, metadata_json, text_content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                id,
                json.dumps(vector),
                json.dumps(metadata) if metadata else None,
                text,
                now,
                now
            ))

            # Insert into VSS table if available
            if self._vss_loaded:
                # Get rowid of inserted record
                cursor = self._conn.execute(f"""
                    SELECT rowid FROM {self._table_name} WHERE id = ?
                """, (id,))
                row = cursor.fetchone()
                if row:
                    rowid = row[0]
                    # Delete existing VSS entry
                    self._conn.execute(f"""
                        DELETE FROM {self._table_name}_vss WHERE rowid = ?
                    """, (rowid,))
                    # Insert new VSS entry
                    vector_str = json.dumps(vector)
                    self._conn.execute(f"""
                        INSERT INTO {self._table_name}_vss (rowid, vector)
                        VALUES (?, ?)
                    """, (rowid, vector_str))

            self._conn.commit()

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
        with self._lock:
            now = datetime.now(timezone.utc).timestamp()
            count = 0

            for record in records:
                vector = record.vector
                if self._config and self._config.normalize_vectors:
                    vector = _normalize_vector(vector)

                self._conn.execute(f"""
                    INSERT OR REPLACE INTO {self._table_name}
                    (id, vector_json, metadata_json, text_content, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record.id,
                    json.dumps(vector),
                    json.dumps(record.metadata) if record.metadata else None,
                    record.text,
                    now,
                    now
                ))
                count += 1

            # Rebuild VSS index if available
            if self._vss_loaded:
                self._rebuild_vss_index()

            self._conn.commit()
            return count

    def _rebuild_vss_index(self) -> None:
        """Rebuild the VSS index from main table."""
        # Clear VSS table
        self._conn.execute(f"DELETE FROM {self._table_name}_vss")

        # Reinsert all vectors
        cursor = self._conn.execute(f"""
            SELECT rowid, vector_json FROM {self._table_name}
        """)
        for row in cursor:
            self._conn.execute(f"""
                INSERT INTO {self._table_name}_vss (rowid, vector)
                VALUES (?, ?)
            """, (row[0], row[1]))

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
        with self._lock:
            if self._vss_loaded:
                return self._search_vss(
                    query_vector, k, filters, include_vectors,
                    include_metadata, score_threshold
                )
            else:
                return self._search_brute_force(
                    query_vector, k, filters, include_vectors,
                    include_metadata, score_threshold
                )

    def _search_vss(
        self,
        query_vector: List[float],
        k: int,
        filters: Optional[Union[Dict[str, Any], List[MetadataFilter]]],
        include_vectors: bool,
        include_metadata: bool,
        score_threshold: Optional[float]
    ) -> List[VectorSearchResult]:
        """Search using VSS extension."""
        vector_str = json.dumps(query_vector)

        # Get more results than k to account for filtering
        fetch_k = k * 3 if filters else k

        cursor = self._conn.execute(f"""
            SELECT
                v.id,
                v.vector_json,
                v.metadata_json,
                v.text_content,
                vss.distance
            FROM {self._table_name}_vss vss
            JOIN {self._table_name} v ON vss.rowid = v.rowid
            WHERE vss_search(vss.vector, ?)
            LIMIT ?
        """, (vector_str, fetch_k))

        results = []
        for row in cursor:
            # Parse metadata
            metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}

            # Apply filters
            if filters:
                if not self._matches_filters(metadata, filters):
                    continue

            # Convert distance to score
            distance = row["distance"]
            score = 1.0 / (1.0 + distance)  # Convert to 0-1 score

            # Apply threshold
            if score_threshold is not None and score < score_threshold:
                continue

            result = VectorSearchResult(
                id=row["id"],
                score=score,
                distance=distance,
                vector=json.loads(row["vector_json"]) if include_vectors else None,
                metadata=metadata if include_metadata else {},
                text=row["text_content"]
            )
            results.append(result)

            if len(results) >= k:
                break

        return results

    def _search_brute_force(
        self,
        query_vector: List[float],
        k: int,
        filters: Optional[Union[Dict[str, Any], List[MetadataFilter]]],
        include_vectors: bool,
        include_metadata: bool,
        score_threshold: Optional[float]
    ) -> List[VectorSearchResult]:
        """Brute-force search fallback."""
        cursor = self._conn.execute(f"""
            SELECT id, vector_json, metadata_json, text_content
            FROM {self._table_name}
        """)

        results = []
        for row in cursor:
            # Parse metadata
            metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}

            # Apply filters
            if filters:
                if not self._matches_filters(metadata, filters):
                    continue

            # Parse vector and calculate similarity
            vector = json.loads(row["vector_json"])
            distance = self._cosine_distance(query_vector, vector)
            score = 1.0 - distance  # Cosine distance to score

            # Apply threshold
            if score_threshold is not None and score < score_threshold:
                continue

            result = VectorSearchResult(
                id=row["id"],
                score=score,
                distance=distance,
                vector=vector if include_vectors else None,
                metadata=metadata if include_metadata else {},
                text=row["text_content"]
            )
            results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    @staticmethod
    def _cosine_distance(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine distance."""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 1.0
        similarity = dot_product / (magnitude1 * magnitude2)
        return 1.0 - similarity

    @staticmethod
    def _matches_filters(
        metadata: Dict[str, Any],
        filters: Union[Dict[str, Any], List[MetadataFilter]]
    ) -> bool:
        """Check if metadata matches filters."""
        if isinstance(filters, dict):
            return all(
                metadata.get(k) == v
                for k, v in filters.items()
            )
        else:
            return all(f.matches(metadata) for f in filters)

    async def get(self, id: str) -> Optional[VectorRecord]:
        """Get a specific vector by ID."""
        return await self._run_sync(self._get_sync, id)

    def _get_sync(self, id: str) -> Optional[VectorRecord]:
        """Synchronous get operation."""
        with self._lock:
            cursor = self._conn.execute(f"""
                SELECT id, vector_json, metadata_json, text_content, created_at, updated_at
                FROM {self._table_name}
                WHERE id = ?
            """, (id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return VectorRecord(
                id=row["id"],
                vector=json.loads(row["vector_json"]),
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                text=row["text_content"],
                created_at=datetime.fromtimestamp(row["created_at"], tz=timezone.utc),
                updated_at=datetime.fromtimestamp(row["updated_at"], tz=timezone.utc) if row["updated_at"] else None
            )

    async def get_batch(self, ids: List[str]) -> List[VectorRecord]:
        """Get multiple vectors by IDs."""
        return await self._run_sync(self._get_batch_sync, ids)

    def _get_batch_sync(self, ids: List[str]) -> List[VectorRecord]:
        """Synchronous batch get."""
        with self._lock:
            placeholders = ",".join("?" * len(ids))
            cursor = self._conn.execute(f"""
                SELECT id, vector_json, metadata_json, text_content, created_at, updated_at
                FROM {self._table_name}
                WHERE id IN ({placeholders})
            """, ids)

            results = []
            for row in cursor:
                results.append(VectorRecord(
                    id=row["id"],
                    vector=json.loads(row["vector_json"]),
                    metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                    text=row["text_content"],
                    created_at=datetime.fromtimestamp(row["created_at"], tz=timezone.utc),
                    updated_at=datetime.fromtimestamp(row["updated_at"], tz=timezone.utc) if row["updated_at"] else None
                ))
            return results

    async def delete(self, id: str) -> bool:
        """Delete a vector by ID."""
        return await self._run_sync(self._delete_sync, id)

    def _delete_sync(self, id: str) -> bool:
        """Synchronous delete operation."""
        with self._lock:
            # Get rowid for VSS table
            if self._vss_loaded:
                cursor = self._conn.execute(f"""
                    SELECT rowid FROM {self._table_name} WHERE id = ?
                """, (id,))
                row = cursor.fetchone()
                if row:
                    self._conn.execute(f"""
                        DELETE FROM {self._table_name}_vss WHERE rowid = ?
                    """, (row[0],))

            # Delete from main table
            cursor = self._conn.execute(f"""
                DELETE FROM {self._table_name} WHERE id = ?
            """, (id,))
            self._conn.commit()
            return cursor.rowcount > 0

    async def delete_batch(self, ids: List[str]) -> int:
        """Delete multiple vectors."""
        return await self._run_sync(self._delete_batch_sync, ids)

    def _delete_batch_sync(self, ids: List[str]) -> int:
        """Synchronous batch delete."""
        with self._lock:
            placeholders = ",".join("?" * len(ids))

            # Delete from VSS table if available
            if self._vss_loaded:
                cursor = self._conn.execute(f"""
                    SELECT rowid FROM {self._table_name} WHERE id IN ({placeholders})
                """, ids)
                rowids = [row[0] for row in cursor]
                if rowids:
                    rowid_placeholders = ",".join("?" * len(rowids))
                    self._conn.execute(f"""
                        DELETE FROM {self._table_name}_vss WHERE rowid IN ({rowid_placeholders})
                    """, rowids)

            # Delete from main table
            cursor = self._conn.execute(f"""
                DELETE FROM {self._table_name} WHERE id IN ({placeholders})
            """, ids)
            self._conn.commit()
            return cursor.rowcount

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
        with self._lock:
            # Get current record
            cursor = self._conn.execute(f"""
                SELECT rowid, vector_json, metadata_json, text_content
                FROM {self._table_name}
                WHERE id = ?
            """, (id,))
            row = cursor.fetchone()

            if row is None:
                return False

            rowid = row[0]
            current_vector = json.loads(row["vector_json"])
            current_metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
            current_text = row["text_content"]

            # Update values
            new_vector = vector if vector is not None else current_vector
            if vector is not None and self._config and self._config.normalize_vectors:
                new_vector = _normalize_vector(new_vector)

            new_metadata = current_metadata
            if metadata is not None:
                new_metadata.update(metadata)

            new_text = text if text is not None else current_text

            now = datetime.now(timezone.utc).timestamp()

            # Update main table
            self._conn.execute(f"""
                UPDATE {self._table_name}
                SET vector_json = ?, metadata_json = ?, text_content = ?, updated_at = ?
                WHERE id = ?
            """, (
                json.dumps(new_vector),
                json.dumps(new_metadata),
                new_text,
                now,
                id
            ))

            # Update VSS table if vector changed
            if vector is not None and self._vss_loaded:
                self._conn.execute(f"""
                    DELETE FROM {self._table_name}_vss WHERE rowid = ?
                """, (rowid,))
                self._conn.execute(f"""
                    INSERT INTO {self._table_name}_vss (rowid, vector)
                    VALUES (?, ?)
                """, (rowid, json.dumps(new_vector)))

            self._conn.commit()
            return True

    async def count(self) -> int:
        """Count total vectors."""
        return await self._run_sync(self._count_sync)

    def _count_sync(self) -> int:
        """Synchronous count."""
        with self._lock:
            cursor = self._conn.execute(f"""
                SELECT COUNT(*) FROM {self._table_name}
            """)
            return cursor.fetchone()[0]

    async def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None

    @property
    def vss_available(self) -> bool:
        """Check if VSS extension is loaded."""
        return self._vss_loaded
