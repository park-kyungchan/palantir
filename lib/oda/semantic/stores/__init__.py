"""
ODA Semantic Stores
===================
Vector store implementations for different backends.

Available Stores:
- SQLiteVSSStore: SQLite with VSS extension (sqlite-vss)
- ChromaDBStore: ChromaDB vector database

Usage:
    from lib.oda.semantic.stores import SQLiteVSSStore, ChromaDBStore

    # SQLite-VSS store
    store = SQLiteVSSStore(db_path="vectors.db", dimension=384)

    # ChromaDB store
    store = ChromaDBStore(collection_name="embeddings", dimension=384)
"""

from lib.oda.semantic.stores.sqlite_vss import SQLiteVSSStore
from lib.oda.semantic.stores.chroma import ChromaDBStore

__all__ = [
    "SQLiteVSSStore",
    "ChromaDBStore",
]
