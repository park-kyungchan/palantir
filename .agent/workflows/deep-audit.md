---
description: Execute Progressive Deep-Dive Audit with 3-Stage Protocol (ANTIGRAVITY_ARCHITECT_V5.0)
---

# deep-audit: 3-Stage Audit Protocol

> **Protocol:** `AuditProtocol` from `scripts/ontology/protocols/audit_protocol.py`
> **Method:** RECURSIVE-SELF-IMPROVEMENT LOOP (RSIL)
> **Enforcement:** BLOCK - Cannot proceed without passing all stages

---

## Prerequisites

```bash
# Verify Protocol Framework
source .venv/bin/activate && python -c "from scripts.ontology.protocols.audit_protocol import AuditProtocol; print('✅ AuditProtocol Ready')"
```

---

## Stage A: SURFACE SCAN (Landscape)

### Goal
Establish Structural Reality & Remove Guesswork.

### Actions
1. **File Structure Analysis**: Map target directory structure
2. **Legacy Artifact Sweep**: Check for `AIP-KEY` remnants, deprecated paths
3. **Pattern Identification**: Identify key components and modules
4. **Palantir API Check**: Verify against OSDK documentation

### Verification Checklist
- [ ] All target files identified
- [ ] Legacy artifacts: CLEAN / DETECTED
- [ ] Structure mapped

### Evidence Required
```python
evidence = {
    "files_viewed": [...],
    "legacy_artifacts": "CLEAN",
    "structure": {...}
}
```

---

## Stage B: LOGIC TRACE (Deep-Dive)

### Goal
Prevent Integration Failures by Tracing Actual Data Flow.

### Actions
1. **Import Path Verification**: Confirm all imports exist
2. **Call Stack Trace**: Map `Input → Middleware → Controller → Service → DB`
3. **Signature Matching**: Verify function signatures align
4. **Dependency Mapping**: Identify integration points

### Trace Format
```
[EntryPoint] function_name() file.py:line
    │
    ├── [Dependency] import_path
    │       ↓
    │   Called function: signature
    │
    └── [Output] return type
```

### RSIL Trigger
If signature mismatch found → HALT → CORRECT → RESTART Stage B

### Verification Checklist
- [ ] Import paths validated
- [ ] Call stack documented
- [ ] Signatures matched

---

## Stage C: QUALITY GATE (Microscopic Audit)

### Goal
Ensure Micro-to-Macro Consistency.

### Quality Checks
1. **Pattern Fidelity**: Does code match Palantir ODA patterns?
2. **Safety Audit**: Type hints, docstrings, null validation
3. **Clean Architecture**: Layer separation (Sec 3.5)
4. **SOLID Principles**: Single responsibility, etc.

### Findings Format
```
[File:Line] [Severity] - Description
```

### Severity Levels
| Level | Action |
|-------|--------|
| CRITICAL | Block execution |
| HIGH | Require fix before merge |
| MEDIUM | Recommend fix |
| LOW | Informational |

### Verification Checklist
- [ ] No critical findings
- [ ] High findings documented
- [ ] Quality gate: PASS / FAIL

---

## Machine-Readable Report Output

After completing all stages, output:

```markdown
### 📠 AUDIT REPORT (v5.0)

#### Stage_A_Blueprint
- Target_Files: [list]
- Legacy_Artifacts: CLEAN/DETECTED
- Palantir_API_Check: CONFIRMED

#### Stage_B_Trace
- Import_Verification: VALID
- Critical_Path: documented
- Signature_Match: PASS

#### Stage_C_Quality
- Pattern_Fidelity: ALIGNED
- Findings: [count by severity]
- Quality_Gate: PASS/FAIL

#### Status
- Current_State: [CONTEXT_INJECTED]
- Ready_to_Execute: TRUE/FALSE
```

---

## Protocol Enforcement

```python
from scripts.ontology.protocols.audit_protocol import AuditProtocol
from scripts.ontology.protocols import ProtocolContext

async def run_deep_audit(target_path: str):
    protocol = AuditProtocol()
    context = ProtocolContext(
        target_path=target_path,
        actor_id="orion_agent"
    )
    
    result = await protocol.execute(context)
    
    if not result.passed:
        print(f"❌ Audit failed: {result.total_findings} findings")
        for stage in result.stages:
            if not stage.passed:
                print(f"  Stage {stage.stage}: {stage.message}")
        return None
    
    print(f"✅ Audit passed in {result.duration_seconds:.2f}s")
    return result
```

---

⛔ **ZERO-TRUST: Do NOT execute code until audit passes**
