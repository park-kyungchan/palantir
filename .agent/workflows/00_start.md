---
description: Initialize the Orion V3 Workspace and Ontology Layer
---
# 00_start: Initialization & Context Loading

## 1. Environment Health Check (MCP)
- **Goal**: Ensure all Agent Tools are functional.
- **Action**: Run MCP Preflight script.
```bash
python3 scripts/mcp_preflight.py --auto-disable-failed
```

## 2. Ontology & Database Initialization
- **Goal**: Ensure SQLite DB is ready and schema is valid.
- **Action**: Run DB initialization check.
```bash
python3 -c "import asyncio; from scripts.ontology.storage.database import initialize_database; asyncio.run(initialize_database())"
```

## 3. Active Memory Recall (Context Injection)
- **Goal**: Load relevant LTM into System Context.
- **Action**: Scan for recent topics.
```bash
python3 scripts/memory/recall.py "Orion Architecture" --limit 3
```

## 4. Status Report
- **Goal**: Confirm readiness.
- **Action**:
    > "Orion V3 Workspace Initialized. MCP Tools: [Status], DB: [Status], Memory: [Injected]."
