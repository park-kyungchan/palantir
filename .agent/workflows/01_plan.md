---
description: Transform User Intent into a Governed Ontology Plan (3-Stage Protocol)
---

# 01_plan: 3-Stage Planning Protocol

> **Protocol:** `PlanningProtocol` from `scripts/ontology/protocols/planning_protocol.py`
> **Enforcement:** All planning must pass Stage A → B → C before execution.

---

## Stage A: BLUEPRINT (Surface Scan)

### Goal
Establish requirements and remove guesswork.

### Actions
1. **Context Check**: Prefer local docs; use external search only if a configured tool is available
2. **Codebase Scan**: Use `read_file` to understand architecture
3. **Scope Definition**: Identify boundaries and constraints
4. **Complexity Assessment**: Small (2-3 phases) / Medium (4-5) / Large (6-7)

### Verification
- [ ] Requirements documented
- [ ] Target files identified
- [ ] Dependencies mapped

### Evidence Required
```python
StageResult.evidence = {
    "files_viewed": [...],
    "requirements": [...],
    "complexity": "medium"
}
```

---

## Stage B: INTEGRATION TRACE (Logic Analysis)

### Goal
Prevent integration failures by tracing actual data flow.

### Actions
1. **Import Verification**: Confirm all imports exist
2. **Signature Matching**: Ensure new code aligns with existing APIs
3. **TDD Breakdown**: Create test-first phases

### Phase Structure
```markdown
### Phase N: [Deliverable Name]
- **Goal**: What working functionality this produces
- **Test Strategy**: 
  - [ ] RED: Write failing tests first
  - [ ] GREEN: Minimal code to pass
  - [ ] REFACTOR: Improve quality
- **Quality Gate**: Build + Lint + Tests pass
```

### Verification
- [ ] Import paths validated
- [ ] Signatures matched
- [ ] Phases defined

---

## Stage C: QUALITY GATE (Verification)

### Goal
Ensure plan is ready for execution.

### Quality Checks

**Build & Tests**:
- [ ] Project builds without errors
- [ ] All existing tests pass
- [ ] Test coverage ≥80%

**Code Quality**:
- [ ] Linting passes
- [ ] Type checking passes

**Risk Assessment**:
| Risk Type | Probability | Impact | Mitigation |
|-----------|-------------|--------|------------|
| Technical | Low/Med/High | Low/Med/High | Action |
| Integration | Low/Med/High | Low/Med/High | Action |

### Approval Gate
- [ ] All Stage A/B/C checks passed
- [ ] User approval received

---

## Ontology Plan Definition (ODA)

### Actions (after Stage C approval)
1. Define `Objective` from user intent
2. Break down into `Jobs`
3. Assign `Role`: Architect Agent / Automation Agent

### Command
```bash
python -m scripts.ontology.handoff --plan ${plan_path} --job ${job_index}
```
**Required params when run via execute_workflow:**
- `workflow_params.plan_path`
- `workflow_params.job_index`


---

## Protocol Enforcement

```python
from scripts.ontology.protocols.planning_protocol import PlanningProtocol
from scripts.ontology.protocols import ProtocolContext

async def run_planning():
    protocol = PlanningProtocol()
    context = ProtocolContext(target_path="target", actor_id="agent")
    result = await protocol.execute(context)
    
    if not result.passed:
        raise ValueError("Planning protocol failed")
    
    return result
```

---

⛔ **DO NOT skip Stage A, B, or C**
