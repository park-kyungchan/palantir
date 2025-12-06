---
description: Maintenance tasks for Database Rebuilding and Schema Validation
---

# 🛠️ Workflow 03: System Maintenance

## 1. Objective
Maintain the integrity of the Orion V3 System by rebuilding indexes and validating data consistency.

## 2. Rebuilding the Search Index (FTS5)
Since `fts_index.db` is ephemeral (gitignored), you must rebuild it if:
1.  You cloned the repo fresh.
2.  You manually edited JSON files in `.agent/memory/`.
3.  The DB file is corrupted.

**Command:**
```bash
/home/palantir/.venv/bin/python -c "from scripts.memory_manager import MemoryManager; MemoryManager().rebuild_index()"
```

## 3. Resetting the Audit Log
If the Governance Ledger (`ontology.db`) is corrupted or Schema Mismatch occurs:

1.  **Delete the DB** (Safe, as logs are also in `traces/` as JSON):
    ```bash
    rm .agent/logs/ontology.db
    ```
2.  **Re-Initialize**:
    ```bash
    /home/palantir/.venv/bin/python scripts/init_memory_db.py
    ```
