---
description: Trigger the Consolidation Engine to mine patterns from traces and update Semantic Memory.
---
# 05_consolidate: Memory Consolidation

## 1. Run Consolidation Engine
- **Goal**: Analyze recent traces, extract patterns (FP-Growth), and save to LTM.
- **Action**:
```bash
python3 scripts/consolidate.py
```

## 2. Review New Patterns
- **Goal**: Check what was learned.
- **Action**:
    - Check `.agent/memory/semantic/patterns/` for new files.
    - Read the output summary in the terminal.
