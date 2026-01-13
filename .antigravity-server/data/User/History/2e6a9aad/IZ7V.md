# Dual-Layer Governance Enforcement Model (ODA)

This document explains how the ODA system "forces" behavior across two distinct layers: the **Cognitive Layer** (Agent's internal reasoning) and the **Execution Layer** (System's programmatic kernel).

## 1. The Cognitive Layer (Agent-Level Awareness)
Enforcement at this layer happens via system prompts and configuration files that the Agent is required to read and follow.

### A. Core Directives (`GEMINI.md` / `CLAUDE.md`)
- **Internal Alignment**: These files transform the Agent from a "Chatbot" into a "Principal Architect".
- **ODA Compliance**: Mandatory sections like `<oda_compliance_v3>` force the Agent to use `scripts/ontology/` and `scripts/ontology/storage/proposal_repository.py` for all state changes.
- **Context Snapshots**: The requirement to output an XML `<cli_context_snapshot>` or `<system_context_snapshot>` at the start of every message ensures the Agent is grounded in reality.
- **Workflow Mandates**: Instructions to read the `Plan` (Handoff) and perform a "Read-Think-Act" loop.

### B. Impact Analysis (`DYNAMIC_IMPACT_ANALYSIS.xml`)
- **Contextual Reasoning**: The Agent uses this XML as a reasoning template to simulate the "Butterfly Effect" of any change before proposing or implementing it.
- **Domain Constraints**: Hard constraints like `DC_01 (SUBSCRIPTION_ENFORCEMENT)` and `DC_02 (LEGACY_KEY_ERADICATION)` serve as "Cerebral Blockers".

## 2. The Execution Layer (Kernel-Level Enforcement)
Enforcement at this layer is **LLM-Independent** and handled by the Python codebase. Even if the LLM attempts a non-compliant action, the Kernel will block it.

### A. Programmatic Rule Enforcement (`.agent/rules/`)
- **GovernanceEngine**: Every action request is intercepted and validated against the rules loaded from `.agent/rules/`.
- **Rule Structure**: Defined in Markdown with YAML frontmatter specifying `enforcement` level (`BLOCKING`, `STRICT`, `LOG_ONLY`).
- **Gate Checks**: Rules can include Python `gate_check` code tags.
- **Implementation (scripts/ontology/actions/__init__.py)**:
  ```python
  def _check_rule_compliance(self, action_name, params):
      for rule in self._agent_rules:
          if rule.gate_check:
              # Sandboxed exec looks for check_* functions
              exec(rule.gate_check, namespace)
              if not namespace["check_"](state):
                  return BLOCK
  ```
- **Enforcement Levels**:
  - `BLOCKING`: Prevents the action immediately.
  - `STRICT`: Requires specific conditions (e.g., specific metadata).
  - `LOG_ONLY`: Defaults for rules without explicit metadata.

### B. Workflow Lifecycle Management (`.agent/workflows/`)
- **WorkflowExecutor**: Manages the progression of phases (e.g., the 7-phase flow of `01_plan`).
- **Quality Gates**: Each phase has mandatory gates that must be satisfied before the system allows moving to the next phase.

## 3. Symbiosis: How Behavioral "Force" is Achieved
Behavioral force is the result of the misalignment between these layers being impossible to maintain.

1.  **Alignment**: `GEMINI.md` directs the Agent to follow ODA.
2.  **Reasoning**: `DYNAMIC_IMPACT_ANALYSIS.xml` guides the Agent's simulation.
3.  **Validation**: `GovernanceEngine` programmatically checks the Agent's output against the physical rules in `.agent/rules/`.
4.  **Correction**: If the Agent (Cognitive Layer) proposes a change that violates a `BLOCKING` rule, the Kernel (Execution Layer) returns an error, forcing the Agent to recalculate and align.

| Layer | Medium | Goal | Implementation |
|-------|--------|------|----------------|
| **Cognitive** | Prompts / XML | Intent & Reasoning | LLM Behavioral Guidance |
| **Execution** | Python Code | Safety & Integrity | Programmatic Runtime Enforcement |

## 4. Cross-LLM Synchronization
To prevent protocol drift when switching between models (e.g., Gemini ↔ Claude), the system employs a **Unified Protocol** (`.agent/CROSS_LLM_PROTOCOL.md`). This file serves as the definitive source of truth that both models must ingest at the start of a session (via `/00_start`) to ensure their Cognitive Layer remains perfectly aligned with the Kernel's Execution Layer.

## 5. Session Startup Handshake (`/00_start`)
The `/00_start` workflow acts as the physical bridge that synchronizes the layers. It forces the following:
1.  **Programmatic Sync**: Kernel loads rules into the `GovernanceEngine`.
2.  **Cognitive Sync**: Agent reads the `CROSS_LLM_PROTOCOL.md` and acknowledges `BLOCKING` rules.
3.  **State Verification**: Confirms that the environment matches the ODA v3 requirements.
## 6. Verification Audit Findings (Jan 2026)
The enforcement model was subjected to a baseline audit to ensure code-level adherence:

- **Audit Objective**: Verify that ontology mutations are blocked until `CONTEXT_INJECTED` state is achieved.
- **Findings**:
    - **`GovernanceEngine`**: Confirmed implementation in `scripts/ontology/actions/__init__.py`.
    - **Reality Check**: Only `kernel_v5` rules had explicit `BLOCKING` metadata; others correctly default to `LOG_ONLY`.
- **Strategic Refactoring**: Completed implementation of `AgentConfigLoader` and `WorkflowExecutor` to natively support `.agent/` rules.
- **Verdict**: [VERIFIED & COMPLIANT]. The system enforces Kernel v5.0 protocols programmatically.
