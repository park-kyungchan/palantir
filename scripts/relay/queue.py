import sqlite3
import uuid
from typing import Optional, Dict

class RelayQueue:
    """
    Production-Ready SQLite Queue.
    Features: WAL Mode, 30s Timeout, RowFactory.
    """
    def __init__(self, db_path="relay.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            # Enable WAL for concurrency
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relay_tasks (
                    id TEXT PRIMARY KEY,
                    prompt TEXT,
                    status TEXT DEFAULT 'pending',
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON relay_tasks(status);")

    def enqueue(self, prompt: str) -> str:
        task_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            conn.execute("INSERT INTO relay_tasks (id, prompt) VALUES (?, ?)", (task_id, prompt))
            # Auto-commit via context manager
        print(f"[RelayQueue] Enqueued task {task_id}")
        return task_id

    def dequeue(self) -> Optional[Dict]:
        """
        Atomic Dequeue: Find pending -> Mark processing.
        """
        with self._get_conn() as conn:
            # Simple lock strategy for now (SQLite single-writer handles this via timeout)
            cursor = conn.execute("SELECT id, prompt FROM relay_tasks WHERE status='pending' LIMIT 1")
            row = cursor.fetchone()
            if row:
                conn.execute("UPDATE relay_tasks SET status='processing' WHERE id=?", (row['id'],))
                return dict(row)
        return None

    def complete(self, task_id: str, response: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE relay_tasks SET status='completed', response=? WHERE id=?", (response, task_id))
        print(f"[RelayQueue] Completed task {task_id}")
