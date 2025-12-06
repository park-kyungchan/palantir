
import os
import sys
import json
import sqlite3
import re
import jsonschema
from typing import Dict, Any, List, Optional
from datetime import datetime

# --- Configuration ---
# Moved to scripts/memory/manager.py, so root is ../../
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(WORKSPACE_ROOT) # Fix ModuleNotFoundError
AGENT_DIR = os.path.join(WORKSPACE_ROOT, ".agent")
SCHEMAS_DIR = os.path.join(AGENT_DIR, "schemas")
MEMORY_DIR = os.path.join(AGENT_DIR, "memory", "semantic")
INDEXES_DIR = os.path.join(AGENT_DIR, "indexes")
DB_PATH = os.path.join(INDEXES_DIR, "fts_index.db")

class MemoryManager:
    """
    The Hippocampus of Orion V3.
    Manages the lifecycle of Semantic Memory Objects (Insights/Patterns).
    Handles: Validation -> Storage (JSON) -> Indexing (SQLite).
    """
    
    def __init__(self):
        self.schemas = self._load_schemas()
        
    def _load_schemas(self) -> Dict[str, Any]:
        """Load JSON Schemas for validation."""
        schemas = {}
        for name in ["insight", "pattern"]:
            path = os.path.join(SCHEMAS_DIR, f"{name}.schema.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    schemas[name] = json.load(f)
        return schemas

    def validate(self, data: Dict[str, Any], schema_type: str):
        """Strict Validation against strict Pydantic/JSONSchema."""
        if schema_type not in self.schemas:
            raise ValueError(f"Unknown schema type: {schema_type}")
        jsonschema.validate(instance=data, schema=self.schemas[schema_type])

    def save_object(self, obj_type: str, data: Dict[str, Any]):
        """
        Atomic Write: Validate -> JSON Save -> FTS Index.
        obj_type: 'insight' or 'pattern'
        """
        # 1. Validation
        self.validate(data, obj_type)
        
        # 2. Determine Path
        obj_id = data.get("id") or data.get("@id")
        if not obj_id:
            raise ValueError("Object missing 'id' field.")
            
        subfolder = "insights" if obj_type == "insight" else "patterns"
        
        # Heuristic Clustering: Store insights in domain folders if possible
        domain = "general"
        if obj_type == "insight":
            domain = f"domain_{data['content'].get('domain', 'general')}"
            
        target_dir = os.path.join(MEMORY_DIR, subfolder)
        if obj_type == "insight":
             target_dir = os.path.join(target_dir, domain)
             
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, f"{obj_id}.json")
        
        # 3. Write JSON (Source of Truth)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        # 4. Update FTS Index (Ephemeral)
        self._update_index(obj_id, file_path, obj_type, data)
        
        return file_path

    def _update_index(self, obj_id: str, file_path: str, obj_type: str, data: Dict[str, Any]):
        """Update SQLite FTS5 Index."""
        rel_path = os.path.relpath(file_path, WORKSPACE_ROOT)
        
        # Extract Text Content for Indexing
        content_text = ""
        tags = ""
        
        if obj_type == "insight":
            content_text = f"{data['content'].get('summary', '')} {data['content'].get('domain', '')}"
            tags = ",".join(data['content'].get('tags', []))
        elif obj_type == "pattern":
            content_text = f"{data['structure'].get('trigger', '')} {' '.join(data['structure'].get('steps', []))}"
            
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # Upsert Logic (Delete then Insert)
        cur.execute("DELETE FROM memory_index WHERE object_id = ?", (obj_id,))
        cur.execute("""
            INSERT INTO memory_index (object_id, file_path, type, content, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (obj_id, rel_path, obj_type, content_text, tags))
        
        con.commit()
        con.close()

    def rebuild_index(self):
        """Full Re-Index from Disk (Source of Truth Recovery)."""
        print("🔄 Rebuilding FTS Index from Filesystem...")
        
        # Clear DB
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        from scripts.memory.init_db import init_fts_db
        init_fts_db()
        
        count = 0
        # Walk Semantic Memory
        for root, dirs, files in os.walk(MEMORY_DIR):
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r') as f:
                            data = json.load(f)
                        
                        # Determine Type
                        obj_type = "insight" if "INS-" in data.get("id", "") else "pattern"
                        if "PAT-" in data.get("id", ""): obj_type = "pattern"
                        
                        self._update_index(data["id"], path, obj_type, data)
                        count += 1
                    except Exception as e:
                        print(f"⚠️ Failed to index {file}: {e}")
                        
        print(f"✅ Rebuild Complete. Indexed {count} objects.")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Sparse Access Retrieval: FTS5 Query -> Temporal Ranking.
        Returns explicit JSON objects.
        """
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # 1. FTS Match (Lexical Search)
        # Using a simple MATCH query. Sanitize aggressively to prevent FTS5 syntax errors (e.g. '?').
        sanitized_query = re.sub(r'[^a-zA-Z0-9 ]', '', query)
        
        sql = """
            SELECT object_id, file_path, content, type, rank 
            FROM memory_index 
            WHERE memory_index MATCH ? 
            ORDER BY rank 
            LIMIT 20
        """
        try:
            cur.execute(sql, (sanitized_query,))
        except sqlite3.OperationalError:
            # Fallback for simple tokens if complex query fails (e.g. empty string)
            # If empty after safe, return empty
            if not sanitized_query.strip():
                con.close()
                return []
            cur.execute(sql, (sanitized_query.replace(" ", " OR "),))
            
        rows = cur.fetchall()
        con.close()
        
        results = []
        for row in rows:
            try:
                # 2. Load Metadata for Re-Ranking
                full_path = os.path.join(WORKSPACE_ROOT, row['file_path'])
                with open(full_path, 'r') as f:
                    data = json.load(f)
                
                # 3. Calculate Score (Simplified V3 Spec Formula)
                # Rank = (BM25 * 0.6) + (Recency * 0.3) + (Confidence * 0.1)
                # Note: SQLite rank is usually negative (lower is better) or positive depending on config.
                # Here we assume SQLite native rank (smaller is better).
                
                # Recency Decay
                updated_at = datetime.fromisoformat(data['meta']['updated_at'])
                hours_elapsed = (datetime.now() - updated_at).total_seconds() / 3600
                recency_score = 1 / (1 + (hours_elapsed / 24)) # 1.0 is fresh, 0.5 is 24h old (approx)
                
                conf_score = data['meta'].get('confidence_score', 0.5)
                
                # Composite Score (Higher is better)
                # BM25 proxy: 1 / (sqlite_rank + epsilon). For now, just use Recency + Confidence dominated.
                final_score = (recency_score * 0.7) + (conf_score * 0.3)
                
                results.append({
                    "data": data,
                    "score": final_score,
                    "preview": row['content'][:100]
                })
            except Exception as e:
                print(f"⚠️ Retrieval Error for {row['object_id']}: {e}")
                continue
                
        # 4. Sort & Limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return [r['data'] for r in results[:limit]]

if __name__ == "__main__":
    mm = MemoryManager()
    mm.rebuild_index()
    # Test Search
    # print(mm.search("python"))
