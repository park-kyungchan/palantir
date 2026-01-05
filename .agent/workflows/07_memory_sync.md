---
description: Sync Gemini CLI memories to Orion Semantic Memory
---

# Memory Sync Workflow

## Steps

### 1. Run Memory Sync
// turbo
```bash
cd /home/palantir/park-kyungchan/palantir && source .venv/bin/activate && python scripts/ontology/memory_sync.py
```

### 2. Verify Sync
```bash
cat .agent/memory/gemini_facts.md
```
