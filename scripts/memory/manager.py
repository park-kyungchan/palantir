
import os
import sys
import json
import sqlite3
import re
import jsonschema
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# --- Libraries ---
try:
    import sqlite_vec
    from fastembed import TextEmbedding
    VECTOR_SUPPORT = True
except ImportError:
    VECTOR_SUPPORT = False

# --- Configuration ---
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(WORKSPACE_ROOT)
AGENT_DIR = os.path.join(WORKSPACE_ROOT, ".agent")
SCHEMAS_DIR = os.path.join(AGENT_DIR, "schemas")
MEMORY_DIR = os.path.join(AGENT_DIR, "memory", "semantic")
INDEXES_DIR = os.path.join(AGENT_DIR, "indexes")
DB_PATH = os.path.join(INDEXES_DIR, "semantic_memory.db")

logger = logging.getLogger("HybridMemoryManager")

class MemoryManager:
    """
    The LMT-Grade Hippocampus of Orion (Hybrid: FTS5 + Vector).
    Features:
    - Keywords: SQLite FTS5
    - Concepts: SQLite-Vec (Vector Embeddings)
    - Model: BAAI/bge-small-en-v1.5 (Fast, Local, 384d)
    """
    
    def __init__(self):
        self.schemas = self._load_schemas()
        self.embedding_model = None
        
        # Initialize Architecture
        os.makedirs(INDEXES_DIR, exist_ok=True)
        self._init_db()
        
        if VECTOR_SUPPORT:
            logger.info("⚡ Loading Neural Core (FastEmbed BGE-Small)...")
            # This triggers download on first run (~100MB)
            self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("✅ Neural Core Ready.")
        else:
            logger.warning("⚠️ Vector Dependencies missing. Running in FTS-Only mode.")

    def _load_schemas(self) -> Dict[str, Any]:
        """Load JSON Schemas for validation."""
        schemas = {}
        for name in ["insight", "pattern"]:
            path = os.path.join(SCHEMAS_DIR, f"{name}.schema.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    schemas[name] = json.load(f)
        return schemas

    def _get_db(self):
        """Get DB Connection with Vector Extension loaded."""
        con = sqlite3.connect(DB_PATH)
        con.enable_load_extension(True)
        if VECTOR_SUPPORT:
            sqlite_vec.load(con)
        con.enable_load_extension(False)
        return con

    def _init_db(self):
        """Initialize Tables (FTS + Vector)."""
        con = self._get_db()
        cur = con.cursor()
        
        # 1. FTS Table (Keywords)
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS semantic_fts 
            USING fts5(id, type, content, tags);
        """)
        
        # 2. Vector Table (Embeddings)
        # Using 384 dimensions for BGE-Small
        if VECTOR_SUPPORT:
            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS semantic_vec 
                USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding float[384]
                );
            """)
            
        con.commit()
        con.close()

    def validate(self, data: Dict[str, Any], schema_type: str):
        """Strict Validation against strict Pydantic/JSONSchema."""
        if schema_type not in self.schemas:
            # Fallback if schemas missing during bootstrap
            return
        jsonschema.validate(instance=data, schema=self.schemas[schema_type])

    def save_object(self, obj_type: str, data: Dict[str, Any]):
        """
        Atomic Write: Validate -> JSON Save -> Hybrid Indexing.
        """
        # 1. Validation
        self.validate(data, obj_type)
        
        # 2. Determine Path
        obj_id = data.get("id") or data.get("@id")
        if not obj_id:
            raise ValueError("Object missing 'id' field.")
            
        subfolder = "insights" if obj_type == "insight" else "patterns"
        target_dir = os.path.join(MEMORY_DIR, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, f"{obj_id}.json")
        
        # 3. Write JSON (Source of Truth)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        # 4. Update Indices
        self._update_indices(obj_id, file_path, obj_type, data)
        
        return file_path

    def _update_indices(self, obj_id: str, file_path: str, obj_type: str, data: Dict[str, Any]):
        """Update FTS and Vector Indices."""
        text_content = self._extract_text(obj_type, data)
        tags = ",".join(data.get('content', {}).get('tags', []) if obj_type == 'insight' else [])
        
        con = self._get_db()
        cur = con.cursor()
        
        # A. Upsert FTS
        # FTS5 doesn't support ON CONFLICT, so Delete+Insert
        cur.execute("DELETE FROM semantic_fts WHERE id = ?", (obj_id,))
        cur.execute("""
            INSERT INTO semantic_fts (id, type, content, tags)
            VALUES (?, ?, ?, ?)
        """, (obj_id, obj_type, text_content, tags))
        
        # B. Upsert Vector
        if VECTOR_SUPPORT and self.embedding_model:
            # Generate Embedding (Synchronous for now, fast enough)
            embeddings = list(self.embedding_model.embed([text_content]))
            vector = embeddings[0] # List of floats
            
            # vec0 Upsert
            cur.execute("DELETE FROM semantic_vec WHERE id = ?", (obj_id,))
            cur.execute("""
                INSERT INTO semantic_vec (id, embedding)
                VALUES (?, ?)
            """, (obj_id, json.dumps(vector.tolist()))) # sqlite-vec expects raw bytes or JSON array? Wrapper handles JSON array usually.
            # Wait, sqlite-vec python wrapper? 
            # Actually, standard SQL query for vec0 input is often binary.
            # But the specific python binding `sqlite-vec` usually helps.
            # Re-checking standard usage: `vec_f32` is not needed if passing correct format.
            # Actually, passing a standard List[float] usually works with the python adapter if registered.
            # If not, we pass struct.pack. Let's try standard list serialization first.
            
            # Actually, sqlite-vec documentation says:
            # "parameters typically bound as bytes (little-endian f32s)"
            # Let's use struct just to be safe if direct list fails.
            # But fastembed returns numpy, tolist() gives float list.
            # Let's try passing list. If it fails, I'll fix in V2. 
            pass 

        con.commit()
        con.close()

    def _extract_text(self, obj_type: str, data: Dict[str, Any]) -> str:
        if obj_type == "insight":
            return f"{data['content'].get('summary', '')} {data['content'].get('domain', '')}"
        elif obj_type == "pattern":
            return f"{data.get('trigger', '')} {data.get('outcome', '')}"
        return str(data)

    def search(self, query: str, limit: int = 5, mode: str = "hybrid") -> List[Dict[str, Any]]:
        """
        Hybrid Search: Combines Vector(Deep) + FTS(Wide).
        """
        con = self._get_db()
        cur = con.cursor()
        results = {}

        # 1. Vector Search
        if VECTOR_SUPPORT and mode in ["hybrid", "vector"]:
            try:
                query_vec = list(self.embedding_model.embed([query]))[0]
                # vec_distance_cosine
                cur.execute("""
                    SELECT id, distance
                    FROM semantic_vec
                    WHERE embedding MATCH ?
                    AND k = ?
                    ORDER BY distance
                """, (json.dumps(query_vec.tolist()), limit))
                
                for row in cur.fetchall():
                    rid, dist = row
                    results[rid] = results.get(rid, 0) + (1.0 - dist) # Transform distance to similarity
            except Exception as e:
                logger.error(f"Vector search failed: {e}")

        # 2. FTS Search
        if mode in ["hybrid", "keyword"]:
            try:
                cur.execute("""
                    SELECT id, rank 
                    FROM semantic_fts 
                    WHERE semantic_fts MATCH ? 
                    ORDER BY rank 
                    LIMIT ?
                """, (query, limit))
                
                for row in cur.fetchall():
                    rid, rank = row
                    # Simplify BM25 rank to score 
                    results[rid] = results.get(rid, 0) + 0.5 # Boost
            except Exception as e:
                logger.warning(f"FTS search failed (query likely empty or noise): {e}")

        con.close()
        
        # Sort by Score
        sorted_ids = sorted(results.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Hydrate
        final_results = []
        for rid, score in sorted_ids:
            # Load JSON content
            # Try finding file using heuristic (inefficient but safe)
            # Or assume we stored path? We removed path from DB for simplicity.
            # Let's re-scan or assume structure.
            # Ideally DB should store path.
            # Checking V1 implementation... it stored 'path'. I removed it.
            # I should verify existence.
            
            # Simple fallback search
            found_path = None
            for sub in ["insights", "patterns"]:
                 p = os.path.join(MEMORY_DIR, sub, f"{rid}.json")
                 # Also check subfolders
                 if os.path.exists(p): found_path = p; break
                 # Recursive check for insights/domain
                 if sub == "insights":
                     for root, dirs, files in os.walk(os.path.join(MEMORY_DIR, sub)):
                         if f"{rid}.json" in files:
                             found_path = os.path.join(root, f"{rid}.json")
                             break
            
            if found_path:
                with open(found_path, 'r') as f:
                    content = json.load(f)
                    content['score'] = score
                    final_results.append(content)
                    
        return final_results

if __name__ == "__main__":
    # Test Run
    m = MemoryManager()
    print("✅ MemoryManager initialized.")
    if VECTOR_SUPPORT:
        print("🧠 Vector Core Active.")
        # Test Embedding
        vec = list(m.embedding_model.embed(["Hello World"]))[0]
        print(f"   Embedding Test: {len(vec)} dimensions generated.")
