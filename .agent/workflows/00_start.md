---
description: Initialize the Orion V3 Workspace and Ontology Layer
---

# 🚀 Workflow 00: System Initialization

## 1. Objective
Bootstrap the **Orion V3 Neuro-Symbolic Agent Environment**.
This initializes the Physical Layer (Directories), Storage Layer (SQLiteFTS + AuditDB), and verifies Codebase Integrity.

## 2. Pre-requisites
*   Python 3.8+ Environment
*   Required Packages: `pydantic`, `jsonschema`
*   No existing conflicting `.agent/logs/ontology.db` (Script handles cleanup if prompted, but fresh start preferred).

## 3. Execution Steps

### Step 3.1: Install Dependencies
Ensure the runtime environment has the governance primitives.
```bash
/home/palantir/.venv/bin/pip install pydantic jsonschema
```

### Step 3.2: Initialize Memory & Audit Systems
This script creates the FTS5 Index (`fts_index.db`) and Governance Ledger (`ontology.db`).
// turbo
```bash
/home/palantir/.venv/bin/python scripts/init_memory_db.py
```

### Step 3.3: Verify Structure
Run the status check to confirm all systems are GO.
```bash
ls -R .agent/indexes .agent/logs
```

## 4. Expected Output
*   `✅ FTS5 Table 'memory_index' ready`
*   `✅ Audit Table 'audit_log' ready`
*   `✨ Memory System Storage Layer Initialized Successfully`
