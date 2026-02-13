# RSIL Meta-Cognition Review — INFRA Constitution & References

> **Reviewer:** rsil-agent | **Date:** 2026-02-13 | **Scope:** CLAUDE.md + 9 reference files
> **AD-15 Filter:** Applied (Layer 1 NL findings only, no hook proposals)

---

## Executive Summary

| Lens | Score | Notes |
|------|:-----:|-------|
| 1. ARE (Structural) | 8/10 | Naming consistent; worker count mismatch in CLAUDE.md |
| 2. RELATE (Relational) | 7/10 | impact-verifier placement conflict; category numbering drift |
| 3. DO (Behavioral) | 9/10 | Lifecycle and protocol chains well-defined |
| 4. IMPACT (Impact) | 9/10 | Rollback protocol, cascade analysis procedures sound |
| 5. Completeness | 8/10 | Two agents missing from CLAUDE.md summary table |
| 6. Consistency | 7/10 | 13 vs 14 category count conflict; "38 workers" error |
| 7. Accuracy | 7/10 | Three factual count errors across files |
| 8. Clarity | 9/10 | Instructions are precise; minor ambiguity in coordinator scope |

**Overall INFRA Score: 8.0/10**

The constitution and reference files are structurally sound with excellent protocol coverage.
Three factual count errors and one cross-file organizational conflict (impact-verifier
placement) are the primary issues. All findings are Layer 1 (NL-correctable).

---

## Findings Table

| ID | Sev | Lens | File(s) | Description | Recommendation |
|----|-----|------|---------|-------------|----------------|
| MC-01 | FIX | Accuracy, Consistency | CLAUDE.md:60 | **"38 workers" is factually wrong.** The "All Agents" table lists 33 agents (excluding claude-code-guide). Adding architect + plan-writer (missing from table) = 35 workers. The heading should say "35 workers" to match §1 line 113 and agent-catalog.md. | Change line 60 to "**All Agents** (35 workers across 14 categories):" |
| MC-02 | FIX | Completeness, ARE | CLAUDE.md:60-77 | **architect and plan-writer missing from "All Agents" table.** Both are Lead-Direct agents listed in agent-catalog.md (Categories 4 and 5) but absent from CLAUDE.md's summary table. Lead routing decisions depend on this table. | Add rows for architect (Category 4, Architecture, P3-4, STANDARD tier) and plan-writer (Category 5, Planning, P4, STANDARD tier). |
| MC-03 | FIX | Consistency, RELATE | CLAUDE.md:40 vs agent-catalog.md:86-87 | **impact-verifier coordinator assignment conflict.** CLAUDE.md lists impact-verifier under verification-coordinator (line 40). Agent-catalog places impact-verifier in "Category 3: Impact" (line 663-691), separate from verification-coordinator which manages only 3 workers (static, relational, behavioral -- line 86-87). | Align: either (a) move impact-verifier under verification-coordinator in agent-catalog, or (b) remove impact-verifier from CLAUDE.md's verification-coordinator row and list it separately as Lead-direct or under its own Impact category. Option (a) is simpler and matches CLAUDE.md intent. |
| MC-04 | WARN | Consistency, Accuracy | agent-common-protocol.md:3, CLAUDE.md:4, agent-catalog.md:4 | **Category count conflict: 13 vs 14.** agent-common-protocol.md says "13 categories." CLAUDE.md and agent-catalog.md say "14 categories." The actual count from agent-catalog's ### Category headers is 10 main + 3 sub-variants (3b, 4b, 5b) = 13. If counting sub-variants as separate categories, it's 13. The "14" likely counted claude-code-guide as a category (Built-in). | Reconcile to a single number. If 14 includes "Built-in" as a pseudo-category, update agent-common-protocol.md to 14. If 13 is correct, update CLAUDE.md and agent-catalog.md. Recommend: 14 categories (including Built-in row in CLAUDE.md table). Update agent-common-protocol.md line 3 from "13" to "14". |
| MC-05 | WARN | RELATE | CLAUDE.md:85 | **Coordinated categories routing rule says "(1-5, 7-10)" but category numbering in "All Agents" table goes 1-12 plus unnumbered.** The routing rule "categories 1-5, 7-10" does not map cleanly to the table's numbering (which goes 1-12). The table uses different numbering than the routing reference. | Consider either (a) aligning the routing rule to actual table row numbers, or (b) using category names instead of numbers in routing rules for clarity. |
| MC-06 | WARN | Consistency | CLAUDE.md:86 | **"Lead-direct categories (6, 11)" routing reference is ambiguous.** Category 6 in the "All Agents" table is "Review" which includes devils-advocate + 4 reviewers. But reviewers are dispatched by execution-coordinator in P6 (line 57-58). The dual-mode nature of review agents makes the "6 = Lead-direct" shorthand misleading. | Add a note: "Category 6 is Lead-direct outside P6; reviewers are dispatched by execution-coordinator within P6." |
| MC-07 | INFO | Accuracy | CLAUDE.md:16, agent-catalog.md:4 | **"43 agents" excludes 3 fork agents.** Total agent .md files = 46 (35 workers + 8 coordinators + 3 fork agents). The "43" count is technically correct if fork agents are considered extensions of Lead rather than independent agents, per CLAUDE.md section 10. But this could confuse readers who count files. | Consider noting "(43 + 3 fork agents = 46 agent files)" or keeping as-is with a note that fork agents are Lead extensions. |
| MC-08 | INFO | ARE | coordinator-shared-protocol.md:3 | **Header references "5 coordinators + 3 new D-005" but there are 8 coordinators total.** The "(5 + 3 new)" wording reflects historical evolution. Now that all 8 are established, the header is unnecessarily historical. | Simplify to "Referenced by: All 8 coordinator .md files". |
| MC-09 | INFO | Clarity | layer-boundary-model.md:38, 157 | **"Five coordinators" at line 157 is stale.** The document says "Five coordinators replace what would traditionally require a message bus" but there are now 8 coordinators. | Update to "Eight coordinators". |
| MC-10 | INFO | Completeness | CLAUDE.md:89-101 | **Skill Reference Table lists 9 skills but MEMORY.md says "10 total: 5 coordinator-based + 4 fork-based + 1 solo."** The MEMORY.md count of 10 does not match the 9 listed in CLAUDE.md. The 10th might be /permanent-tasks counted as fork-based (it is listed). Counting: 5 coordinator (brainstorming, write-plan, validation, execution, verification) + 3 fork (delivery, rsil-review, rsil-global) + 1 fork (permanent-tasks) = 9. If rsil-global and rsil-review share an agent but are separate skills, that's still 9 rows in the table. | Verify MEMORY.md count. If 9 is correct, update MEMORY.md. The CLAUDE.md table appears accurate with 9 entries. |
| MC-11 | INFO | DO | gate-evaluation-standard.md:67-74 | **G2b verification gate shows STANDARD and COMPLEX columns but CLAUDE.md Pipeline Tiers table (line 29) says STANDARD skips P2b.** If STANDARD skips Phase 2b entirely, then the G2b gate should only show COMPLEX criteria. Having STANDARD criteria in G2b is either an error or indicates STANDARD can optionally run P2b. | Clarify: either remove STANDARD column from G2b gate, or update CLAUDE.md tier table to indicate P2b is optional for STANDARD. |

---

## Statistics

| Metric | Count |
|--------|:-----:|
| **Total findings** | 11 |
| **FIX** (must correct) | 3 |
| **WARN** (should address) | 3 |
| **INFO** (note for awareness) | 5 |

### By Lens

| Lens | Findings |
|------|:--------:|
| Accuracy | 3 (MC-01, MC-04, MC-07) |
| Consistency | 4 (MC-01, MC-03, MC-04, MC-06) |
| Completeness | 3 (MC-02, MC-10, MC-11) |
| RELATE (Relational) | 2 (MC-03, MC-05) |
| ARE (Structural) | 2 (MC-02, MC-08) |
| Clarity | 1 (MC-09) |
| DO (Behavioral) | 1 (MC-11) |

### Files Affected

| File | Findings |
|------|:--------:|
| CLAUDE.md | 7 (MC-01, MC-02, MC-03, MC-05, MC-06, MC-07, MC-10) |
| agent-catalog.md | 3 (MC-03, MC-04, MC-07) |
| agent-common-protocol.md | 1 (MC-04) |
| coordinator-shared-protocol.md | 1 (MC-08) |
| layer-boundary-model.md | 1 (MC-09) |
| gate-evaluation-standard.md | 1 (MC-11) |

---

## Cross-Reference Verification Summary

| Check | Result |
|-------|--------|
| CLAUDE.md skill list vs `.claude/skills/` directory | PASS (9/9) |
| CLAUDE.md hook list vs `settings.json` hooks | PASS (4/4) |
| Agent-catalog worker count vs `.claude/agents/` files | PASS (35+8+3=46 files) |
| Coordinator-shared-protocol sections vs coordinator .md files | PASS |
| Gate-evaluation-standard gates vs pipeline phases | PASS with MC-11 note |
| Ontological-lenses agent mapping vs agent-catalog | PASS |
| Task-api-guideline fork exception vs CLAUDE.md section 10 | PASS |
| Pipeline-rollback-protocol paths vs phase pipeline | PASS |
| Layer-boundary-model 5 dimensions vs INFRA analyst agents | PASS |
| Ontology-communication-protocol (domain doc, not INFRA) | N/A (out of scope) |

---

## Recommended Fix Priority

1. **MC-01 + MC-02** (FIX): Correct worker count and add missing agents to CLAUDE.md table -- single edit session
2. **MC-03** (FIX): Resolve impact-verifier placement -- requires design decision (option a or b)
3. **MC-04** (WARN): Reconcile category count across 3 files
4. **MC-09** (INFO): Update stale coordinator count in layer-boundary-model.md

All findings are Layer 1 (NL-correctable). No Layer 2 structural changes needed. AD-15 compliant.
