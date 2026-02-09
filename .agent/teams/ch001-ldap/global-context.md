---
version: GC-v1
project: CH-001 LDAP Implementation
pipeline: Simplified Infrastructure (Phase 1 → 6 → 6.V → 9)
current_phase: 6
---

# Global Context — CH-001 LDAP

## Project Summary
Upgrade DIA Enforcement from v2.0 (2-layer: CIP + DIAVP) to v3.0 (3-layer: CIP + DIAVP + LDAP).
LDAP = Lead Devil's Advocate Protocol. Adds adversarial challenge step (Layer 3) within Gate A
to verify systemic impact awareness (GAP-003).

## Design Reference
- Approved design: `docs/plans/2026-02-07-ch001-ldap-design.yaml`
- Implementation plan: `docs/plans/2026-02-07-ch001-ldap-implementation.md`

## Key Design Decisions
- GAP-003a (Interconnection Blindness) + GAP-003b (Ripple Blindness)
- 7 challenge categories: INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE,
  FAILURE_MODE, DEPENDENCY_RISK, ASSUMPTION_PROBE, ALTERNATIVE_DEMAND
- Shift-Left intensity: MAXIMUM(P3/P4), HIGH(P6/P8), MEDIUM(P2/P7), EXEMPT(P5), NONE(P1/P9)
- Implementation: Option A (Within Gate A) + Option D (task-context.md persistence)
- Enforcement: IDLE-WAKE turn-based cycle via SendMessage

## Scope
- 7 files modified, 0 files created, 0 hooks added
- CLAUDE.md: v2.0 → v3.0
- task-api-guideline.md: v2.0 → v3.0
- 5 agent .md files: add Phase 1.5 section
- devils-advocate.md: NO change (TIER 0 exempt)

## Cross-Reference Integrity Requirement [CRITICAL]
All 7 files share these exact strings — they MUST match across all files:
- Message format: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
- Message format: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense}`
- 7 category IDs: INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE, FAILURE_MODE,
  DEPENDENCY_RISK, ASSUMPTION_PROBE, ALTERNATIVE_DEMAND
- Intensity levels: NONE, MEDIUM, HIGH, MAXIMUM, EXEMPT

## Active Teammates
- implementer-1: Sole implementer. Owns all 7 target files.

## Phase Status
- Phase 1 (Discovery): COMPLETE
- Phase 6 (Implementation): IN_PROGRESS
- Phase 6.V (Verification): PENDING
- Phase 9 (Delivery): PENDING
