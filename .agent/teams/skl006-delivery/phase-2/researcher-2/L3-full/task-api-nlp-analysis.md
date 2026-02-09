# L3: task-api-guideline.md NLP Conversion Analysis

## Current State (536 lines, Version 5.0)

### Protocol Marker Inventory

| Marker | Count | Location (§) |
|--------|-------|-------------|
| [DIRECTIVE] | 6 | §6, §11, §14 |
| [INJECTION] | 4 | §6, §11 |
| [STATUS] | 5 | §5, §6, §8, §11 |
| [IMPACT-ANALYSIS] | 4 | §6, §11 |
| [IMPACT_VERIFIED] | 3 | §6, §11 |
| [VERIFICATION-QA] | 3 | §6, §11 |
| [CHALLENGE] | 3 | §11 |
| [CHALLENGE-RESPONSE] | 1 | §11 |
| [ACK-UPDATE] | 2 | §11, §14 |
| [CONTEXT-UPDATE] | 3 | §11, §14 |
| [RE-EDUCATION] | 1 | §11 |
| [IMPACT_REJECTED] | 2 | §11 |
| [IMPACT_ABORT] | 1 | §11 |
| [PLAN] | 1 | §11 |
| [APPROVED] | 1 | §11 |
| **TOTAL** | **~40** | |

### Section Analysis

#### §1-§5 (Pre-Call, Storage, TaskCreate, Dependencies, Lifecycle) — ~145 lines
**Status:** Mostly clean. Valuable operational content. Minor protocol marker usage in §5 (`[CAUTION]`).
**Action:** Keep with minor NLP cleanup.

#### §6 (Semantic Integrity Integration) — ~30 lines
**Status:** Heavy protocol marker usage. References [DIRECTIVE], [IMPACT-ANALYSIS], [IMPACT_VERIFIED], [VERIFICATION-QA].
**Analysis:** The Lead-Level checklist (7 steps) is valuable but uses old terminology. Teammate-Level (5 steps) references [INJECTION], [STATUS], which are now embedded naturally in skills.
**Action:** Rewrite in NLP. Keep the operational checklists, drop the marker notation.

#### §7 (Anti-Patterns) — ~20 lines
**Status:** Clean. No markers. Valuable content.
**Action:** Keep as-is.

#### §8 (Known Issues) — ~40 lines
**Status:** Clean. ISS-001~005 are well-documented operational cautions.
**Action:** Keep as-is. These are facts, not protocol.

#### §9 (Sub-Orchestrator) — ~15 lines
**Status:** Clean. Valuable guidance.
**Action:** Keep as-is.

#### §10 (Metadata) — ~10 lines
**Status:** Clean.
**Action:** Keep as-is.

#### §11 (DIA Enforcement Protocol) — ~220 lines — THE BIG ONE
**Status:** Heaviest protocol marker concentration. Contains:

1. **CIP (Context Injection Protocol)** — IP-001~010 table (~30 lines)
   - Value: HIGH. The injection point table is a useful quick reference.
   - Markers: [DIRECTIVE], [INJECTION], [CONTEXT-UPDATE]
   - Action: Convert to NLP. Keep the table structure, drop markers.

2. **Context Delta Protocol** (~20 lines within §11)
   - Value: MEDIUM. Duplicated in §14.
   - Action: Consolidate with §14.

3. **DIAVP (Impact Awareness Verification Protocol)** (~80 lines)
   - Verification Tiers (TIER 0-3): Obsolete. Skills now embed phase-appropriate verification naturally.
   - RC-01~10 Checklist: Partially valuable. The criteria themselves are good, but the formal checklist is replaced by CLAUDE.md §6 "Verifying Understanding."
   - Verification Flow: Obsolete. Replaced by natural verification in skills.
   - Value: LOW. The substance is already in CLAUDE.md §6 and individual skills.
   - Action: Remove formal tiers/checklists. Optionally keep a condensed "what to verify" reference.

4. **LDAP (Adversarial Challenge Protocol)** (~90 lines)
   - GAP-003a/003b definitions: Conceptually valuable but over-formalized.
   - Challenge Categories (7): Already embedded in CLAUDE.md §6 "Focus on interconnection awareness, failure reasoning, and interface impact."
   - Challenge Intensity by Phase table: Already embedded in skill files (each skill specifies its own probing question count).
   - Challenge Flow: Obsolete — skills handle this natively.
   - Two-Gate Flow: Simplified in skills to "understand → plan → execute."
   - Value: LOW. All substance exists in NLP form elsewhere.
   - Action: Remove entirely. The CLAUDE.md §6 natural language covers the intent.

#### §12 (CLAUDE_CODE_TASK_LIST_ID) — ~20 lines
**Status:** Clean. Useful operational guidance.
**Action:** Keep as-is.

#### §13 (Team Memory Protocol) — ~40 lines
**Status:** Clean. Useful reference.
**Action:** Keep as-is.

#### §14 (Context Delta Protocol) — ~40 lines
**Status:** Protocol markers but useful content.
**Action:** Merge with CIP from §11. Convert to NLP.

## Proposed Restructured task-api-guideline.md

**Target: ~200-250 lines**

```
§1 Pre-Call Protocol (15L)
§2 Task Storage Architecture (40L)
§3 Comprehensive Task Creation (50L)
§4 Dependency Chain Rules (20L)
§5 Task Lifecycle (20L)
§6 Lead Integration Checklist (20L — NLP rewrite of old §6)
§7 Anti-Patterns (20L)
§8 Known Issues (40L — ISS-001~005)
§9 Sub-Orchestrator Patterns (15L)
§10 Metadata Operations (10L)
§11 Context Management Reference (30L — merged CIP table + delta format, NLP)
§12 Task List Configuration (20L — TASK_LIST_ID)
§13 Team Memory Protocol (40L)
```

**Removed:** DIAVP tiers, RC-01~10 formal checklist, LDAP challenge protocol, GAP-003 formal definitions, Two-Gate Flow formal spec, Challenge Intensity table, Enhanced ACK format, Compaction Recovery challenge state.

**Rationale:** All removed content is either:
1. Already present in NLP form in CLAUDE.md §6 and skill files (verification, probing questions)
2. Over-formalized ceremony that doesn't add value over natural language (TIER system, RC codes)
3. Duplicated between §11 and §14 (delta protocol)

## Impact Assessment

Converting task-api-guideline.md affects:
- **No downstream impact on skills** — skills already use NLP for all verification
- **No downstream impact on agents** — agents reference task-api-guideline but the operational content (§1-§10) stays
- **Hook impact:** None — hooks don't reference task-api-guideline
- **CLAUDE.md impact:** None — CLAUDE.md already NLP v6.0

The conversion is essentially removing dead code — the formal protocols that skills and CLAUDE.md have already superseded.
