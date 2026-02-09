# Team Memory — COA E2E Integration

## Meta
- GC Version: GC-v1
- Created: 2026-02-08
- Feature: COA E2E Integration Design

## Lead
- [Decision] 7 GAPs identified: COA-1~7
- [Decision] Option B: Parallel Domain Split (2 researchers → 1 architect)
- [Decision] L3 completeness mandated for all researchers
- [Decision] Lead Meta-Cognition: MEMORY + sequential-thinking for every orchestration decision
- [Finding] Prior audit (opus46-compatibility-audit.md) identified ISSUE-001/002/003 in hooks
- [Finding] BUG-001 (plan mode blocks MCP), BUG-002 (auto-compact), RTDI-009 (plan mode disabled) NOT in CLAUDE.md

## researcher-protocol
- [Finding] COA-1~5 are NOT independent — form a layered system with 7 inter-COA relationships
- [Pattern] Layered Architecture: COA-2 (signal) → COA-1 (dashboard) → COA-3 (evidence) → COA-4 (framework) → COA-5 (specialization)
- [Decision] Will design unified interconnected system, NOT 5 independent protocols
- [Finding] COA-2 (Self-Location) is the foundational "heartbeat pulse" — triggers COA-3 (documentation) and COA-4 (re-verification)
- [Finding] COA-5 (MCP verification) is a specific check TYPE within COA-4's framework, not parallel
- [Finding] COA-3 (documentation) produces evidence that COA-4 (re-verification) consumes — hard dependency
- [Finding] COA-1 (sub-workflow) detects anomalies that trigger COA-4 on-demand re-verification
- DIA: RC 5/5 PASS, LDAP INTERCONNECTION_MAP STRONG → [IMPACT_VERIFIED]
- [Decision] D-R1: 3 new format strings only: [SELF-LOCATE], [REVERIFY], [REVERIFY-RESPONSE]. Minimal §4 additions.
- [Decision] D-R2: COA-5 is NOT standalone — check type within COA-4's framework, uses COA-2 MCP field as data.
- [Decision] D-R3: COA-4 re-verification has 3 levels (RV-1 ping, RV-2 question, RV-3 abbreviated IA) with escalation.
- [Finding] Zero conflicts with existing DIA layers 1-4. All protocols EXTEND current infrastructure.
- [Finding] COA-3 replaces vague "proactively" with 6 concrete checkpoint triggers tied to COA-2 events.
- [Warning] COA-1 sub-workflow table depends entirely on COA-2 signals — COA-2 must be implemented first.
- [Dependency] Design order: COA-2 first → COA-1/3/4 parallel → COA-5 as COA-4 specialization.

## researcher-code-audit
- [Finding] Current hook code EXACTLY matches audit doc "Current Code (BROKEN)" — no drift, fix specs remain valid
- [Finding] 5 working hooks confirmed (TeammateIdle, TaskCompleted, TaskUpdate, PreCompact, SessionStart)
- [Finding] settings.json: all 8 hook configs structurally valid
- [Decision] Placement Architecture: Gate (S-*) vs Constraint (SC-*) taxonomy
  - BUG-002: stays ONLY in §6 Pre-Spawn Checklist Gates (S-2/S-3) — no duplication
  - BUG-001 + RTDI-009: NEW subsection "Spawn Constraints (Permanent)" within §6
  - SC-1: Mode Override (always mode: "default") — BUG-001
  - SC-2: Plan Mode Disabled — RTDI-009
  - CLAUDE.md = authority for RULE; MEMORY.md = diagnostic HISTORY (cross-ref, no duplication)
- DIA: RC 5/5 PASS, LDAP SCOPE_BOUNDARY STRONG → [IMPACT_VERIFIED]
- [STATUS] COMPLETE — all L1/L2/L3 delivered.
- [Finding] 7 L3 artifacts: CLAUDE.md placement spec, 3 hook fixes (copy-paste-ready), change rationale, hooks reference, 7 E2E scenarios.
- [Finding] Zero additional undocumented constraints or hook issues beyond known BUG-001/002/RTDI-009/ISSUE-001/002/003.

## architect-1
(awaiting spawn)
