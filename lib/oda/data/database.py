from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy import text
from lib.oda.ontology.storage.database import Database
from .source import DataSource

class SQLAlchemyDataSource(DataSource):
    """
    DataSource backed by a SQLAlchemy Database.
    Supports executing SQL queries for read, and table inserts for write.
    """

    def __init__(self, db: Database, query: str = None, table: str = None):
        """
        Args:
            db: Initialized Database instance.
            query: SQL query for read() (e.g. "SELECT * FROM my_table")
            table: Table name for write() (e.g. "my_table")
        """
        self.db = db
        self.query_str = query
        self.table_name = table

    @property
    def name(self) -> str:
        target = self.table_name if self.write else (self.query_str or "SQL")
        return f"SQL({target})"

    async def read(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute the configured query or override with 'query' kwarg.
        Returns result as list of dicts.
        """
        q = kwargs.get("query", self.query_str)
        if not q:
            raise ValueError("No query provided for SQL read.")

        async with self.db.transaction() as session:
            result = await session.execute(text(q))
            # Convert RowMappings to dicts
            return [dict(row) for row in result.mappings().all()]

    async def write(self, data: List[Dict[str, Any]], **kwargs) -> None:
        """
        Insert data into the configured table.
        Uses SQLAlchemy Core generic insert if possible, or text-based if models unavailable.
        For this generic implementation, we assume column names match keys.
        """
        table = kwargs.get("table", self.table_name)
        if not table:
            raise ValueError("No table specified for SQL write.")
        if not data:
            return

        # Basic Check: All rows should have same keys for batch insert
        keys = data[0].keys()
        
        # We use text() with bindparams for safety, but constructing the INSERT statement dynamically
        # Validation checks are minimal here; production would use Table reflection.
        columns = ", ".join(keys)
        placeholders = ", ".join([f":{k}" for k in keys])
        stmt = text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")

        async with self.db.transaction() as session:
            await session.execute(stmt, data)
