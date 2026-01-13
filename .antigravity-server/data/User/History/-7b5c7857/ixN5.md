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

---

## 5. Governance Integration

The protocol framework is integrated into the `GovernanceEngine` (found in `scripts/ontology/actions/__init__.py`) to enforce compliance before any action execution.

### 5.1 `check_protocol_compliance`

The `GovernanceEngine` uses the `ProtocolRegistry` to determine if a required protocol has been successfully executed for a given action.

```python
def check_protocol_compliance(self, action_name: str) -> PolicyResult:
    from scripts.ontology.protocols.decorators import ProtocolRegistry
    
    is_compliant, reason = ProtocolRegistry.is_compliant(action_name)
    
    if not is_compliant:
        return PolicyResult(
            decision="BLOCK",
            reason=reason or f"Protocol compliance check failed for '{action_name}'"
        )
    return PolicyResult(decision="ALLOW_IMMEDIATE", reason="")
```

---

## 6. Verification Results

Successful verification was performed on 2026-01-05, confirming the framework's integrity and enforcement capabilities.

### 6.1 Integration Test Output
```text
✅ AuditProtocol: audit
✅ PlanningProtocol: planning
✅ ExecutionProtocol: execution
✅ AuditProtocol execution: passed=True, stages=3
✅ All protocol tests passed!
✅ GovernanceEngine with check_protocol_compliance imported
```

---

## 7. V6.0 Enhancements: RSIL & Anti-Hallucination

In Kernel v6.0 (Native Edition), the protocol framework was enhanced with programmatic enforcement of the **Recursive-Self-Improvement Loop (RSIL)** and strict **Anti-Hallucination** verification.

### 7.1 `AntiHallucinationError`
A new exception class to block execution when evidence is missing.
```python
class AntiHallucinationError(Exception):
    def __init__(self, stage: str, message: str = "Stage passed without evidence"):
        super().__init__(f"[{stage}] {message}")
```

### 7.2 Programmatic Evidence Validation
`StageResult.validate_evidence(strict=True)` is used to ensure that analysis is grounded in actual file system reads.
- **Strict Mode**: Raises `AntiHallucinationError` if `files_viewed` is empty.
- **Pattern**: Aligned with Palantir's `submissionCriteria` validation.

### 7.3 `execute_with_rsil` (Recursive-Self-Improvement)
The `ThreeStageProtocol` base class now supports automated retry logic (default: 3 retries) for each stage execution, isomorphic to **Palantir Automate** retry patterns.

```python
# Conceptual implementation in ThreeStageProtocol
async def execute_with_rsil(self, context, max_retries=3):
    for attempt in range(max_retries):
        result = await self.execute(context)
        if result.passed:
            return result
        # RSIL Trigger: HALT -> CORRECT -> RESTART
        logger.warning(f"RSIL iteration {attempt + 1} for {self.name}")
    return result
```

### 7.4 Virtual Workflow Mapping
The system treats the 3-stage method as a **Mandatory Virtual Workflow** even when explicit markdown triggers are absent, ensuring consistent governance across all micro-decisions.
