
import sys
import sqlite3
from scripts.ontology.manager import ObjectManager
from scripts.ontology.db import DB_PATH
from scripts.ontology.schemas.memory import OrionInsight, OrionPattern

def run_test():
    print("=== STARTING PHASE 4 FTS VERIFICATION ===")
    
    om = ObjectManager()
    om.register_type(OrionInsight)
    om.register_type(OrionPattern)
    
    # 1. Connect to DB Raw
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # 2. Check FTS Content Count
    # We FTS-indexed everything via save()
    # Note: 'objects' table uses 'fts_content' column directly?
    # No, 'objects' table is a normal table.
    # Did we create an FTS Virtual Table?
    # Phase 1 DB plan said "Universal Object Table".
    # Phase 2 Added 'fts_content' column to 'objects'.
    # This column allows standard LIKE or FTS5 explicit indexing.
    # To use FTS5 properly, we usually need a virtual table.
    # BUT for now, we just verify the COLUMN is populated.
    
    cur.execute("SELECT id, type, fts_content FROM objects WHERE type IN ('OrionInsight', 'OrionPattern') AND fts_content IS NOT NULL LIMIT 5")
    rows = cur.fetchall()
    
    print(f"[Info] Found {len(rows)} rows with FTS content populated.")
    assert len(rows) > 0, "No FTS content found! Migration failed to index?"
    
    for r in rows:
        oid, otype, content = r
        print(f"[Inspect] ID={oid} Type={otype} Content_Len={len(content)}")
        # print(f"Content: {content}")
        assert len(content) > 10, "FTS Content too short"

    # 3. Retrieve Object via Manager
    test_id = rows[0][0]
    test_type_str = rows[0][1]
    
    # Map string type to class
    type_cls = OrionInsight if test_type_str == "OrionInsight" else OrionPattern
    
    obj = om.get(type_cls, test_id)
    assert obj is not None, "Failed to hydrating migrated object"
    assert obj.id == test_id
    print(f"[PASS] Hydrated {obj.__class__.__name__} {obj.id}")
    
    print("=== PHASE 4 FTS VERIFICATION COMPLETED ===")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"!!! FAILURE !!! {e}")
        sys.exit(1)
