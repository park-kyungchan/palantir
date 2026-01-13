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

---

## 7. Memory Lifecycle & Self-Improvement

The Orion ODA differentiates between raw findings and actionable, generalized knowledge to manage its recursive self-improvement.

### 7.1 Insight-to-Pattern Lifecycle
1. **Generation (Insight)**: Discoveries made during tasks (e.g., `/deep-audit`) are saved as `OrionInsight` JSON files via `/02_manage_memory`. These are specific to a context (e.g., "Bare except found in file X").
2. **Consolidation (Pattern)**: The `/05_consolidate` workflow processes multiple Insights to identify recurring themes, promoting them to `OrionPattern`.
3. **Inference (Active Knowledge)**: Patterns are loaded during `/00_start` (Recall) to guide the agent's behavior in future tasks.

### 7.2 Guided vs. Autonomous Improvement
As of January 2026, the ODA improvement loop is **Guided**:
- The agent identifies potential improvements and records them as Insights.
- The user or a specific consolidation trigger is required to "lock in" these changes as permanent Patterns.
- **Autonomous Goal**: Future iterations aim to automate the promotion of high-confidence Insights to Patterns without user intervention, once the `scripts/memory/manager.py` (Pattern Search) is fully implemented.

---

## 8. Agent Handoff & Job Orchestration

The Orion ODA utilizes a **Relay Execution Pattern** to decouple architectural planning from low-level automation.

- **Orchestrator Role**: Manages the SVDOM, conducts Deep Audits, and generates Job Manifests.
- **Automation Specialist Role**: Receives Job Manifests (JSON/Markdown) and executes atomic implementation tasks within restricted constraints (e.g., "OWPML-only").
- **Audit Requirement**: Every handoff JOB must be initialized with a `/deep-audit` (Stage A/B/C) to ensure the specialist has full landscape awareness before modifying the codebase.
