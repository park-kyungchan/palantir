---
description: Initialize ODA workspace and verify system health
allowed-tools: Bash, Read, TodoWrite
---

# /init Command

Initialize Orion ODA workspace and verify all components are functional.

## Pre-Execution: Initialize Progress Tracking

Before starting, create a todo list to track initialization progress:

```
TodoWrite([
  {"content": "Check environment and activate venv", "status": "pending", "activeForm": "Checking environment"},
  {"content": "Initialize database", "status": "pending", "activeForm": "Initializing database"},
  {"content": "Verify protocol framework", "status": "pending", "activeForm": "Verifying protocols"},
  {"content": "Export registry", "status": "pending", "activeForm": "Exporting registry"},
  {"content": "Generate initialization report", "status": "pending", "activeForm": "Generating report"}
])
```

## Execution Steps

**Update TodoWrite status as each step progresses (in_progress → completed).**

1. **Environment Check**
   ```bash
   cd /home/palantir/park-kyungchan/palantir
   source .venv/bin/activate 2>/dev/null || echo "No venv"
   ```

2. **Database Initialization**
   ```bash
   mkdir -p .agent/tmp
   ORION_DB_PATH=.agent/tmp/ontology.db python -c "
   import asyncio
   from scripts.ontology.storage.database import initialize_database
   asyncio.run(initialize_database())
   print('DB: Ready')
   "
   ```

3. **Protocol Framework Check**
   ```bash
   python -c "
   from scripts.ontology.protocols import ThreeStageProtocol, ProtocolContext, Stage
   print('Protocols: Ready')
   "
   ```

4. **Registry Export**
   ```bash
   python -m scripts.ontology.registry 2>/dev/null && echo "Registry: Exported" || echo "Registry: Check manually"
   ```

## Output Format
```
Orion ODA Workspace Initialized
================================
- Database: Ready
- Protocols: Ready
- Registry: Exported
- Workspace: /home/palantir/park-kyungchan/palantir

Ready for ODA operations.
```

## Post-Initialization
After /init, you can use:
- `/plan <요구사항>` - Create implementation plan
- `/audit <path>` - Run code audit
- `/governance` - Check compliance
