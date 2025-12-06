---
description: Manually inject Insights and Patterns into the Semantic Memory
---

# 🧠 Workflow 02: Semantic Memory Injection

## 1. Objective
Manually teach the Orion Agent by injecting **Insights** (Declarative Knowledge) or **Patterns** (Procedural Knowledge) into the Long-Term Memory (LTM).

## 2. Concept
*   **Insight**: "What is true?" (Fact, Preference, Constraint).
    *   Stored in: `.agent/memory/semantic/insights/`
*   **Pattern**: "How to do it?" (Workflow, Checklist, Anti-pattern).
    *   Stored in: `.agent/memory/semantic/patterns/`

## 3. Mechanism
Use the `MemoryManager` API via a Python script.

## 4. Execution Template

Create a script `inject_memory.py`:

```python
from scripts.memory_manager import MemoryManager
from datetime import datetime
import uuid

mm = MemoryManager()

# Define Insight
data = {
    "id": f"INS-{uuid.uuid4().hex[:6]}",
    "type": "Insight",
    "meta": {
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "confidence_score": 1.0, # 1.0 = Axiom
        "decay_factor": 0.0      # 0.0 = Never forget
    },
    "provenance": { "method": "manual_entry" },
    "content": {
        "summary": "Always use 'scripts/impact.py' before major changes.",
        "domain": "governance",
        "tags": ["rules", "safety", "protocol"]
    },
    "relations": {}
}

# Save & Index
path = mm.save_object("insight", data)
print(f"✅ Injected: {path}")
```

Run it:
```bash
/home/palantir/.venv/bin/python inject_memory.py
```

## 5. Verification
Query the engine to see if it recalls the new knowledge:
```bash
/home/palantir/.venv/bin/python scripts/engine.py dispatch "governance protocols"
```
