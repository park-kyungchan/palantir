# 3-Stage Protocol: Core Implementation

**Date:** 2026-01-05
**Package:** `scripts/ontology/protocols/`

---

## 1. Core Abstractions (`base.py`)

The framework uses several typed data models to enforce evidence-based analysis.

### 1.1 `StageResult`
Every stage MUST produce a result with evidence.
```python
@dataclass
class StageResult:
    stage: Stage
    passed: bool
    findings: List[Finding] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```
**Anti-Hallucination:** If `passed=True` but `evidence` is empty, a warning is logged by the system.

### 1.2 `ThreeStageProtocol` ABC
The base class for all protocol implementations.
```python
class ThreeStageProtocol(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    async def stage_a(self, context: ProtocolContext) -> StageResult: pass

    @abstractmethod
    async def stage_b(self, context, stage_a_result) -> StageResult: pass

    @abstractmethod
    async def stage_c(self, context, stage_b_result) -> StageResult: pass

    async def execute(self, context: ProtocolContext) -> ProtocolResult:
        # Executes A -> B -> C in sequence; short-circuits on failure.
```

---

## 2. Enforcement & Decorators (`decorators.py`)

### 2.1 `ProtocolRegistry`
A global registry that tracks which `ActionType` requires which protocol.
- `register(action_name, protocol_class, policy)`
- `is_compliant(action_name)` -> returns `(bool, reason)`

### 2.2 `@require_protocol`
Class decorator used to mandate compliance at the action level.
```python
@require_protocol(AuditProtocol, policy=ProtocolPolicy.BLOCK)
class DeepAuditAction(ActionType):
    pass
```

---

## 3. Standard Protocol Implementations

| Protocol Class | Implementation File | Key Focus |
|----------------|---------------------|-----------|
| `AuditProtocol` | `audit_protocol.py` | Surface Scan, Logic Trace, Quality Audit |
| `PlanningProtocol` | `planning_protocol.py` | Blueprint, Integration, Quality Gate |
| `ExecutionProtocol` | `execution_protocol.py` | Pre-Check, Execute, Validate |

---

## 4. Evidence Tracking Pattern

Evidence is tracked in the `ProtocolContext` and must include:
- `files_viewed`: List of absolute paths.
- `lines_referenced`: Dict of file -> line number list.
- `code_snippets`: Exact snippets as proof of reading.
