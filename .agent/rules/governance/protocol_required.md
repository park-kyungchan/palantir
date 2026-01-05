---
description: Actions requiring 3-Stage Protocol completion before execution
---

# Protocol Required Actions

> **Framework:** `scripts/ontology/protocols/`
> **Enforcement:** `GovernanceEngine.check_protocol_compliance()`

---

## Criteria

| Action Type | Required Protocol | Policy |
|-------------|-------------------|--------|
| `@require_protocol(AuditProtocol)` | AuditProtocol | BLOCK |
| `@require_protocol(PlanningProtocol)` | PlanningProtocol | BLOCK |
| `@require_protocol(ExecutionProtocol)` | ExecutionProtocol | WARN |

---

## Workflows Requiring Protocol

| Workflow | Protocol | Enforcement |
|----------|----------|-------------|
| `/deep-audit` | AuditProtocol | BLOCK |
| `/01_plan` | PlanningProtocol | BLOCK |
| `/05_consolidate` | ExecutionProtocol | WARN |

---

## Enforcement Flow

```
[User Request] → [GovernanceEngine.check_protocol_compliance()]
    │
    ├── No protocol required → ALLOW
    ├── Protocol not executed → BLOCK/WARN
    └── Protocol executed → PASS/FAIL
```

## Code Reference

```python
from scripts.ontology.protocols.decorators import require_protocol
from scripts.ontology.protocols.audit_protocol import AuditProtocol

@require_protocol(AuditProtocol)
class DeepAuditAction(ActionType):
    api_name = "deep_audit"
```
