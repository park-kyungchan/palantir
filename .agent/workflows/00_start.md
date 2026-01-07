---
description: Initialize the Orion V3 Workspace and Ontology Layer
---
# 00_start: Initialization & Context Loading

> **Protocol Framework:** This workflow initializes 3-Stage Protocol context for all subsequent operations.

---

## 1. Environment Health Check (MCP)
- **Goal**: Ensure all Agent Tools are functional.
- **Action**: Run MCP Preflight script.
```bash
timeout 30 bash -lc "source .venv/bin/activate && python scripts/mcp_preflight.py --auto-disable-failed"
```

---

## 2. Ontology & Database Initialization
- **Goal**: Ensure SQLite DB is ready and schema is valid.
- **Action**: Run DB initialization check.
```bash
mkdir -p .agent/tmp
timeout 30 bash -lc "source .venv/bin/activate && ORION_DB_INIT_MODE=sync ORION_DB_PATH=.agent/tmp/ontology.db python -c \"import asyncio; from scripts.ontology.storage.database import initialize_database; asyncio.run(initialize_database()); print('✅ DB Initialized')\""
```

---

## 3. Protocol Framework Initialization
- **Goal**: Initialize 3-Stage Protocol context for session.
- **Action**: Verify protocol imports are functional.
```bash
timeout 30 bash -lc "source .venv/bin/activate && python -c \"from scripts.ontology.protocols import ThreeStageProtocol, ProtocolContext, Stage; print('✅ Protocol Framework Ready')\""
```
- **Context Setup**:
```python
from scripts.ontology.protocols import ProtocolContext
context = ProtocolContext(
    target_path="/home/palantir/park-kyungchan/palantir",
    actor_id="orion_agent"
)
```

---

## 4. Active Memory Recall (Context Injection)
- **Goal**: Load relevant LTM into System Context.
- **Action**: Scan for recent topics.
```bash
timeout 10 bash -lc "source .venv/bin/activate && python scripts/memory/recall.py \"Orion Architecture\" --limit 3" || true
```

---

## 5. Status Report
- **Goal**: Confirm readiness with protocol status.
- **Report Format**:
    > "Orion V3 Workspace Initialized."
    > - MCP Tools: [Status]
    > - DB: [Status]
    > - Protocol Framework: [Ready]
    > - Memory: [Injected]
