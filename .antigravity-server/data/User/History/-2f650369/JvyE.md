# Workflow & Rule Integration Audit: ODA 3-Stage Protocol

**Date:** 2026-01-05
**Status:** BLUEPRINT_SCAN_COMPLETE
**Framework Integration Level:** LOW (Manual reference only)

---

## 1. Objective
Verify if the `.agent/workflows/` and `.agent/rules/` directories are aligned with the **ODA 3-Stage Protocol Framework** (Scan, Trace, Verify) and identify specific code/instruction blocks that require automation.

---

## 2. Workflow Integration Analysis (.agent/workflows/)

| Workflow | Current State | Protocol Alignment | Required Action |
| :--- | :--- | :--- | :--- |
| `00_start.md` | Session init, DB check. | None. | Add `AuditProtocol` pre-check for environment health. |
| `01_plan.md` | TDD-Enhanced phases. | High (Conceptual). | Explicitly link Phase 1-3 to `PlanningProtocol` (Stage A, B, C). |
| `04_governance_audit.md` | Audit log inspection. | Partial. | Integrate with `AuditProtocol` to verify historical traces. |
| `05_consolidate.md` | Consolidation engine call. | Low. | Wrap with `ExecutionProtocol` to ensure pre/post-state safety. |

### Gap: Lack of Direct Command Integration
Current workflows use basic `bash` commands. They do not yet invoke the programmatic `check_protocol_compliance()` check before executing the underlying python scripts (e.g., `scripts/consolidate.py`).

---

## 3. Rule Integration Analysis (.agent/rules/)

| Rule Category | Alignment Status | Integration Requirement (v3.1) |
| :--- | :--- | :--- |
| **Governance** | High (Conceptual). | Rules should trigger `ProtocolViolation` if actions are attempted without a passed protocol. |
| **Domain** | Medium. | Subscriptions and API key rules should be mandatory checks in `AuditProtocol` Stage A. |

### Missing Rules
- **`enforce_3stage_protocol.md`**: No specific rule file exists to warn the agent in real-time when it skips the 3-stage methodology outside of Python-based actions.

---

## 4. Requirement for "No Ambiguity" Integration

To satisfy the user's requirement for "no ambiguity or error," the following must be implemented:

1.  **Command Aliases**: Mapping `@/01_plan` to a command that first initializes the `PlanningProtocol`.
2.  **Stateful Tracking**: Protocols must persist their results in the ODA database so workflows can verify the `ProtocolResult.passed` status.
3.  **Active Warning**: The agent must be instructed (via Rules) to HALT if it tries to execute a workflow step without the required protocol evidence.

---

## 5. Next Steps (Roadmap)
1.  **Phase 3.1**: Update `01_plan.md` to strictly follow `PlanningProtocol`.
2.  **Phase 3.2**: Create `enforce_3stage_protocol.md` in `.agent/rules/governance/`.
3.  **Phase 3.3**: Modify `scripts/ontology/handoff.py` to require a successful protocol pass.
