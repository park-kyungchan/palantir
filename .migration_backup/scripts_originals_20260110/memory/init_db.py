
import sqlite3
import os
import sys

# Configuration
# Moved to scripts/memory/init_db.py, so root is ../../
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INDEXES_DIR = os.path.join(WORKSPACE_ROOT, ".agent", "indexes")
DB_PATH = os.path.join(INDEXES_DIR, "fts_index.db")
LOGS_DB_PATH = os.path.join(WORKSPACE_ROOT, ".agent", "logs", "ontology.db")

def init_fts_db():
    """Initialize the SQLite FTS5 Inverted Index."""
    os.makedirs(INDEXES_DIR, exist_ok=True)
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # 1. Create FTS5 Virtual Table
    # Porter tokenizer for stemming (running -> run)
    print("🛠️  Initializing FTS5 Memory Index...")
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_index USING fts5(
            object_id UNINDEXED,   -- e.g., "INS-7a8b9c"
            file_path UNINDEXED,   -- e.g., "semantic/insights/INS-7a8b9c.json"
            type,                  -- "Insight", "Pattern"
            content,               -- Full text content for indexing
            tags,                  -- Explicit tags
            tokenize='porter unicode61'
        );
    """)
    
    # 2. Verify Table
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_index'")
    if cur.fetchone():
        print(f"✅ FTS5 Table 'memory_index' ready in {DB_PATH}")
    else:
        print(f"❌ Failed to create FTS5 table.")
        sys.exit(1)
        
    con.commit()
    con.close()

def init_audit_db():
    """Initialize the Immutable Audit Log."""
    log_dir = os.path.dirname(LOGS_DB_PATH)
    os.makedirs(log_dir, exist_ok=True)
    
    con = sqlite3.connect(LOGS_DB_PATH)
    cur = con.cursor()
    
    # Standard Relational Table for Audit (Matched with scripts/governance.py)
    print("🛠️  Initializing Ontology Audit Log...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            action_type TEXT NOT NULL,
            action_id TEXT NOT NULL,
            parameters TEXT NOT NULL, -- JSON String
            user TEXT NOT NULL,
            result TEXT, -- JSON String (Updated on commit)
            status TEXT DEFAULT 'PENDING'
        );
    """)
    con.commit()
    print(f"✅ Audit Table 'audit_log' ready in {LOGS_DB_PATH}")
    con.close()

if __name__ == "__main__":
    try:
        init_fts_db()
        init_audit_db()
        print("\n✨ Memory System Storage Layer Initialized Successfully.")
    except Exception as e:
        print(f"\n❌ Initialization Failed: {e}")
        sys.exit(1)
