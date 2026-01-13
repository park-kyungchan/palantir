# ODA Agent Governance & Workflows

**Date:** 2026-01-05
**Protocol:** ANTIGRAVITY_ARCHITECT_V5.1 (SCRIPT-ENFORCED)
**Target:** Governance Layer Synchronization

---

## 1. Slash Command Workflows

The ODA uses procedural markdown "runbooks" in `.agent/workflows/` to guide high-level behavior while maximizing token efficiency.

### Workflow Inventory
| `/00_start` | Session initialization & protocol injection. | `SystemInit` (Pre-flight Audit) |
| `@/01_plan` | Strategic planning & task decomposition. | `PlanningProtocol` |
| `/02_manage_memory` | Working memory & episodic recall optimization. | `ExecutionProtocol` |
| `/04_governance` | Verification of protocol compliance (Kernel v5.1). | `AuditProtocol` |
| `/deep-audit` | Implementation of the 3-Stage Deep-Dive-Audit. | `AuditProtocol` (STRICT) |
| `/fde-learn` | Activation of the Palantir FDE Learning Protocol. | `PlanningProtocol` |

### Command-Protocol Mapping (v5.1 Integration)
To eliminate ambiguity, all `@/command` entries are programmatically mapped to specific 3-Stage Protocol classes. No command can proceed to "Phase 2" of its runbook without a `ProtocolResult.passed` status from Stage A.

### Token Economy Strategy
- **Traditional Approach**: Boilerplate prompts (1500+ tokens/turn).
- **ODA Approach**: Slash commands reading specific Markdown files (~20 tokens/turn).
- **Result**: ~95% reduction in redundant token overhead.

---

## 2. Dual-Layer Enforcement Model

ODA "forces" behavior by synchronizing the **Cognitive Layer** (Agent reasoning) with the **Execution Layer** (System kernel).

| Layer | Medium | Implementation |
|-------|--------|----------------|
| **Cognitive** | Prompts / XML | LLM Behavioral Guidance (GEMINI.md, DYNAMIC_IMPACT_ANALYSIS.xml). |
| **Execution** | Python Code | Programmatic Kernel Enforcement (GovernanceEngine, WorkflowExecutor). |

### Enforcement Mechanics
1. **Rule Parsing**: `GovernanceEngine` (in `actions/__init__.py`) intercepting actions.
2. **Metadata Levels**: `BLOCKING` (immediate error), `STRICT` (requires metadata), `LOG_ONLY` (default).
3. **Quality Gates**: `WorkflowExecutor` enforcing phase dependencies (PENDING → IN_PROGRESS → COMPLETED).

---

## 3. Recursive Self-Improvement Loop (RSIL)

RSIL is a meta-cognitive audit methodology enforced by the `ANTIGRAVITY_ARCHITECT_V5.0` protocol.

### The 5-Iteration Process
1. **Pattern Discovery**: Identify architectural alignments (e.g., Action Types).
2. **Code Verification**: Trace implementation to specific line numbers.
3. **Side Effect Analysis**: Audit post-commit hooks and resilience.
4. **Governance Review**: Audit state-machine transitions and policy gaps.
5. **Final Synthesis**: Butterfly Effect simulation and architectural verdict.

### RSIL Principles
- **Anti-Hallucination**: Every iteration MUST reference actual code artifacts.
- **Traceability**: All iterations are documented via Sequential Thinking logs.
- **Verification**: Audit findings are converted into actionable remediation tasks or test cases.

---

## 4. 3-Stage Deep-Dive Implementation Method

To ensure consistency between audit results and actual code changes, ODA enforces a 3-stage protocol for **Implementation/Coding** and all core operations.

### Rationale
1. **Anti-Hallucination**: Forces the agent to read existing blueprint/import paths before writing code.
2. **Integration Safety**: Identifies side effects on existing modules before mutation.
3. **Pattern Fidelity**: Verifies alignment with Palantir/Clean Architecture standards at every step.

### Enforcement
This method is transitioning from a behavioral guideline to a **script-level enforced framework**. For technical details on the programmatic enforcement, evidence tracking, and base class design, see the [Three-Stage Protocol Framework](./three_stage_protocol_framework.md).
