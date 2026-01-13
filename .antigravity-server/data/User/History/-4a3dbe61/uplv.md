# ODA Agent Workflow Restructuring (v6.0)

**Date:** 2026-01-05
**Target Directory:** `.agent/workflows/`
**Protocol Alignment:** ANTIGRAVITY_ARCHITECT_V6.0 (Native Edition)

---

## 1. Overview

To eliminate ambiguity and ensure 100% operational consistency, the core ODA workflows were restructured from basic "checklist" runbooks into **Native Workflows** programmatically interpreted by the Kernel. This transformation ensures that every major agent command is intrinsically bound to a 3-Stage Protocol and enforced via a **Recursive-Self-Improvement Loop (RSIL)**.

---

## 2. Redesigned Workflows

### 2.1 `/00_start` (Initialization)
- **Change:** Added a explicit "Protocol Framework Initialization" phase.
- **Impact:** Ensures the `ProtocolContext` and actor identity are injected at the start of every session.
- **Key Pattern:** Initialization check for `scripts.ontology.protocols`.

### 2.2 `@/01_plan` (Planning)
- **Change:** Total restructuring based on `PlanningProtocol` (Stage A: Blueprint, Stage B: Trace, Stage C: Quality Gate).
- **Impact:** Forces requirements gathering and integration tracing *before* generating a test-driven plan.
- **Pattern:** Explicit "Evidence Required" block for the agent to fill.

### 2.3 `/05_consolidate` (Execution)
- **Change:** Wrapped in `ExecutionProtocol` (Pre-Check, Execute, Validate).
- **Impact:** Ensures the environment is ready for memory mining and verifies the patterns were correctly saved post-execution.

### 2.4 `/deep-audit` (New Workflow)
- **Purpose:** A standalone workflow for the `AuditProtocol`.
- **Method:** Enforces the RECURSIVE-SELF-IMPROVEMENT LOOP (RSIL) at each stage.
- **Result:** Produces a Machine-Readable Audit Report (v5.0).

### 2.5 Governance Rules Integration (`.agent/rules/governance/`)
- **`protocol_required.md`**: Defines which action types require which 3-stage protocol and the enforcement policy (BLOCK/WARN).
- **`three_stage_protocol.md`**: Documents the methodology (Stage A, B, C) as a governing rule for the agent.

### 2.6 Implementation Confirmation
Final implementation was completed on 2026-01-05. All files were successfully created and verified via E2E tests (test_monolith.py).

---

## 3. Workflow-to-Protocol Mapping

| Workflow | Command | Protocol Class | State Transition |
| :--- | :--- | :--- | :--- |
| Initialization | `/00_start` | `SystemInit` | `[CONTEXT_NULL]` -> `[READY]` |
| Planning | `@/01_plan` | `PlanningProtocol` | `[INTENT]` -> `[VALID_PLAN]` |
| Consolidation | `/05_consolidate` | `ExecutionProtocol` | `[DIRTY]` -> `[SYNCHRONIZED]` |
| Deep Audit | `/deep-audit` | `AuditProtocol` | `[UNKNOWN]` -> `[CONTEXT_INJECTED]` |

---

## 4. Implementation Patterns for Agent Prompts

When executing these workflows, the agent must now provide **evidence** strings as specified in the restructured markdown files:

```markdown
### Evidence (Stage A: Blueprint)
- Files Viewed: [scripts/ontology/actions/__init__.py]
- Lines Referenced: [242, 315]
- Ground Truth: "ActionType.submission_criteria is enforced in GovernanceEngine."
```

This pattern is verified programmatically by the `GovernanceEngine.check_protocol_compliance()` check.
