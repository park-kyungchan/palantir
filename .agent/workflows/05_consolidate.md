---
description: Trigger the Consolidation Engine to mine patterns from traces and update Semantic Memory.
---
# Consolidation Workflow

1. **Verify Traces**: Check if there are new traces to process.
   ```bash
   ls -F .agent/traces/
   ```

2. **Run Consolidation Engine**: Execute the `consolidate.py` orchestrator.
   // turbo
   ```bash
   /home/palantir/.venv/bin/python scripts/consolidate.py
   ```

3. **Verify Output**: Check if new patterns were saved to memory.
   ```bash
   ls -F .agent/memory/pattern/
   ```
