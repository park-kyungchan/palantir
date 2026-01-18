"""
ODA Storage Package
===================

This package contains persistence primitives (database + repositories).

Only the database wrapper is guaranteed to exist in minimal installs; repository
modules may be added incrementally as the ODA storage layer evolves.
"""

from lib.oda.ontology.storage.database import Database, DatabaseManager, get_database, initialize_database

__all__ = [
    "Database",
    "DatabaseManager",
    "get_database",
    "initialize_database",
]

