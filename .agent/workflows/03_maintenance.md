---
description: Maintenance tasks for Database Rebuilding and Schema Validation
---
# 03_maintenance: System Maintenance

## 1. Database Rebuild (Destructive)
- **Goal**: Wipe and recreate the Ontology Database.
- **Action**:
```bash
# WARNING: This deletes all data!
echo "y" | python3 scripts/maintenance/rebuild_db.py
```

## 2. Schema Validation
- **Goal**: Verify ORM Models match DB Tables.
- **Action**: (Future) Run Alembic check.
