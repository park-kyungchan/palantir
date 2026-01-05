---
description: Trigger the Consolidation Engine with ExecutionProtocol
---
# 05_consolidate: Memory Consolidation (3-Stage)

> **Protocol:** `ExecutionProtocol` from `scripts/ontology/protocols/execution_protocol.py`

---

## Stage A: PRE-CHECK

### Goal
Validate environment before consolidation.

### Actions
- [ ] Verify trace files exist in `.agent/traces/`
- [ ] Check database connectivity
- [ ] Confirm no conflicting operations

---

## Stage B: EXECUTE

### Goal
Run consolidation engine.

### Action
```bash
python3 scripts/consolidate.py
```

---

## Stage C: VALIDATE

### Goal
Verify consolidation results.

### Actions
- [ ] Check `.agent/memory/semantic/patterns/` for new files
- [ ] Review output summary
- [ ] Verify no errors in logs

---

## Protocol Enforcement

```python
from scripts.ontology.protocols.execution_protocol import ExecutionProtocol
from scripts.ontology.protocols import ProtocolContext

async def run_consolidation():
    protocol = ExecutionProtocol()
    context = ProtocolContext(target_path="consolidation", actor_id="agent")
    result = await protocol.execute(context)
    
    if result.passed:
        # Actually run consolidation
        import subprocess
        subprocess.run(["python3", "scripts/consolidate.py"])
```
