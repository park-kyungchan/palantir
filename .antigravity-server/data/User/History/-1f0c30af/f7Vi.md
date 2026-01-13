# ODA Protocol Framework: Native Edition v6.0

## 1. Overview
The ODA 3-Stage Protocol is a mandatory verification framework for all cognitive and automated operations. In V6.0, it is enforced as a **Native Virtual Workflow** with programmatic checks for evidence and recursive self-improvement.

---

## 2. Core Protocol Sequence
Every action or audit follows the strict **Scan-Trace-Verify** sequence:

### Stage A: SURFACE SCAN (Landscape)
- **Goal**: Establish structural reality and remove guesswork.
- **Actions**: File structure analysis, legacy artifact sweep, pattern identification.
- **Evidence**: `files_viewed`, `structure_map`.

### Stage B: LOGIC TRACE (Deep-Dive)
- **Goal**: Prevent integration failures by tracing actual data flow.
- **Actions**: Import path verification, call stack trace (Input → Middleware → Service → DB), signature matching.
- **Evidence**: `call_stack_diagram`, `dependency_mapping`.

### Stage C: QUALITY GATE (Microscopic Audit)
- **Goal**: Ensure micro-to-macro consistency.
- **Actions**: Pattern fidelity check (vs. Palantir ODA patterns), safety audit (type hints, null validation), SOLID principles check.
- **Evidence**: `findings_list`, `pass_fail_verdict`.

---

## 3. Enforcement Mechanisms

### 3.1 @require_protocol
A class-level decorator that mandates a specific protocol before an `ActionType` can execute.
- **BLOCK policy**: Execution is halted unless a valid `ProtocolResult` is found in the registry.

### 3.2 Anti-Hallucination Gate
- **`AntiHallucinationError`**: Raised if a stage is marked `passed=True` but contains zero `files_viewed` in the evidence dictionary.
- **Logic**: Programmatically validates that the agent actually "read" the files it claims to have analyzed.

---

## 4. RSIL: Recursive-Self-Improvement Loop
Framework-level support for automated correction cycles.

```
Execution → [Fail/Low Evidence] → RSIL Trigger → [Context Flush] → Re-Analysis → Re-Execution
```

- **Pattern**: `HALT → CORRECT → RESTART`.
- **Implementation**: Managed by `ThreeStageProtocol.execute_with_rsil(max_retries=3)`.
- **Alignment**: Isomorphic to Palantir Automate's retry behavior.

### 4.1 Meta-Level RSIL (Architectural Improvement)
In addition to task-level correction, the Framework supports **Meta-Level Improvement** where the agent audits the entire codebase for structural debt.
- **Large Class Refactoring**: Breaking down monolithic builders (e.g., `HwpxDocumentBuilder`) into feature-specific mixins (Text, Table, Control).
- **Utility Centralization**: Identifying duplicated logic (e.g., HWPUNIT conversions) and migrating to shared libraries.
- **Ground-Truth Verification**: Automated regression suites comparing generated output against officially produced artifacts.

---

## 5. 1-Layer Audit (Outer Shell) Protocol
Specialized protocol for E2E system integrity checks before deeper architectural audits.

- **Purpose**: Verify system prompts and ODA alignment at the configuration layer.
- **Non-Negotiables**:
    - `ORION_SYSTEM_PROMPT` and `ORION_WORKSPACE_ROOT` treated as canonical.
    - LLM access must route through `scripts/llm/config.py` (no vendor hard-coding).
    - ObjectTypes must be sourced from the central registry.

---

## 6. Implementation Reference
- **Core ABCs**: `scripts/ontology/protocols/base.py`
- **Audit Implementation**: `scripts/ontology/protocols/audit_protocol.py`
- **Governance Hook**: `GovernanceEngine.check_protocol_compliance()`
