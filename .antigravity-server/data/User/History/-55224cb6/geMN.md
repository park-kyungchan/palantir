# ODA Agent Governance & Workflows

**Date:** 2026-01-05
**Protocol:** ANTIGRAVITY_ARCHITECT_V5.0
**Target:** Governance Layer Synchronization

---

## 1. Slash Command Workflows

The ODA uses procedural markdown "runbooks" in `.agent/workflows/` to guide high-level behavior while maximizing token efficiency.

### Workflow Inventory
| Command | Purpose |
| :--- | :--- |
| `/00_start` | Session initialization & protocol injection. |
| `/01_plan` | Strategic planning & task decomposition. |
| `/02_manage_memory` | Working memory & episodic recall optimization. |
| `/04_governance` | Verification of protocol compliance (Kernel v5.0). |
| `/deep-audit` | Implementation of the 3-Stage Deep-Dive-Audit. |
| `/fde-learn` | Activation of the Palantir FDE Learning Protocol. |

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

To ensure consistency between audit results and actual code changes, ODA enforces a 3-stage protocol for **Implementation/Coding** as well.

### Rationale
1. **Anti-Hallucination**: Forces the agent to read existing blueprint/import paths before writing code.
2. **Integration Safety**: Identifies side effects on existing modules before mutation.
3. **Pattern Fidelity**: Verifies alignment with Palantir/Clean Architecture standards at every step.

### Stages
- **🔍 STAGE A: Blueprint Scan**: Re-verify API specs (e.g., Palantir docs) and existing folder structure.
- **🔬 STAGE B: Integration Trace**: Track import paths and function signatures to ensure compatibility.
- **🧬 STAGE C: Quality Gate**: Code execution with type hints, docstrings, validation, and test verification.
