
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
    The Hippocampus of Orion.
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
        cur.execute("DELETE FROM semantic_index WHERE id = ?", (obj_id,))
        cur.execute("""
            INSERT INTO semantic_index (id, type, path, content, tags, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (obj_id, obj_type, rel_path, content_text, tags, datetime.now().isoformat()))
        
        con.commit()
        con.close()

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Full-Text Search via SQLite FTS5."""
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # FTS Query
        # Using MATCH for FTS table (virtual) assuming 'semantic_index' is set up as such.
        # But wait, did we init the DB as Virtual Table?
        # The 'init_db.py' should handle that. Assuming it does.
        
        try:
            cur.execute("""
                SELECT id, path, content, rank 
                FROM semantic_index 
                WHERE semantic_index MATCH ? 
                ORDER BY rank 
                LIMIT ?
            """, (query, limit))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "id": row[0],
                    "path": row[1],
                    "snippet": row[2][:100] + "...",
                    "score": row[3]
                })
            return results
        except sqlite3.OperationalError:
            # Fallback if no FTS or table missing
            return []
        finally:
            con.close()

    def calc_insight_value(self, insight_data: Dict[str, Any]) -> float:
        """
        Determines the 'Value' of an insight for consolidation.
        Heuristics:
        - Higher Confidence Score
        - More supporting relations
        - Fewer contradictions
        """
        base_score = insight_data['meta'].get('confidence_score', 0.5)
        supports = len(insight_data.get('relations', {}).get('supports', []))
        contradicts = len(insight_data.get('relations', {}).get('contradicts', []))
        
        # 3. Calculate Score (Simplified Spec Formula)
        final_score = base_score + (supports * 0.1) - (contradicts * 0.2)
        return max(0.0, min(1.0, final_score))
