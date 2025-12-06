---
description: Inspect the Immutable Audit Log (Ontology DB)
---

# ⚖️ Workflow 04: Governance Audit

## 1. Objective
Inspect the `audit_log` table in SQLite to verify:
*   Who performed an action?
*   When was it performed?
*   Was it authorized (Status)?
*   What were the parameters?

## 2. Access Mechanism
Use `sqlite3` CLI to query the `.agent/logs/ontology.db`.

## 3. Common Queries

### List Recent Actions
```bash
sqlite3 .agent/logs/ontology.db "SELECT timestamp, event_type, status, user FROM audit_log ORDER BY timestamp DESC LIMIT 5;"
```

### Inspect Specific Failure
```bash
sqlite3 .agent/logs/ontology.db "SELECT result FROM audit_log WHERE status='FAILED';"
```

### Count Actions by Type
```bash
sqlite3 .agent/logs/ontology.db "SELECT action_type, COUNT(*) FROM audit_log GROUP BY action_type;"
```

## 4. Integrity Check
Ensure that every `COMMITTED` action has a corresponding `ACTION_START` and `ACTION_END` event pair.
