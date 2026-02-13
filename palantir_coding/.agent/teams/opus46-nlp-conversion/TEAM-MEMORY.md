# Team Memory — opus46-nlp-conversion (Phase 3 Revision)

## Lead
- [Decision] Full NLP conversion approved by user. Mechanical enforcement deferred to Ontology layer.
- [Finding] claude-code-guide research: Opus 4.6 responds worse to rigid protocol markers than natural language.
- [Pattern] Anthropic C compiler case study: conversational guidance > formal gates.
- [Warning] task-api-guideline.md is being modified concurrently — do not touch.
- [Decision] L3 revision triggered by upstream PERMANENT Task design (2026-02-08-permanent-tasks-design.md)
- [Decision] GC → PERMANENT Task (Task API). This is ARCHITECTURE_CHANGE level.
- [Warning] ALL GC-v{N} references in L3 must become PT-v{N}. CIP changes from embedding to TaskGet.
- [Finding] Original L3 NLP conversion approach preserved — only context delivery mechanism changes.

## researcher-1
(awaiting assignment)

## architect-1
- [Decision] AD-1: Deduplication strategy — 6 duplicated concepts → single authoritative location each. Saves ~22 lines from CLAUDE.md alone.
- [Decision] AD-2: [PERMANENT] 40 lines → §10 Integrity Principles 18 lines. Most content was already in §3/§6.
- [Decision] AD-3: Communication table: 13 rows → 3 flow-direction groups. All types preserved.
- [Decision] AD-5: DIA v6.0: RC checklists and LDAP categories removed. Role-appropriate open-ended questions. 2-level probing (Standard/Deep).
- [Decision] AD-6: Agent template: Phase numbering → natural sections (Role, Before Starting, How to Work, Constraints).
- [Finding] Semantic preservation verified: 28/28 CLAUDE.md behaviors, 13/13 common-protocol behaviors.
- [Finding] Line count: 847 → 525 (38% reduction, exceeds 37% target).
- [Pattern] Full rewritten text provided for all files — implementers need minimal interpretation.
- [Warning] DIA v6.0 trusts Lead judgment more — Lead quality matters more than before.
- [Decision] Gate 3 APPROVED. LDAP MAXIMUM passed (3Q + alternative). All artifacts in phase-3/architect-1/.
- [Decision] Alternative rejected: Dual-Mode Architecture — no machine consumers of bracket markers, dual representation = synchronization burden with zero benefit.
