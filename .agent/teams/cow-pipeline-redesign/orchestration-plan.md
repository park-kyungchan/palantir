---
feature: cow-pipeline-redesign
current_phase: 7
gc_version: GC-v6
pt_version: PT-v4
---

# Orchestration Plan

## Gate History
- Phase 1: APPROVED (2026-02-09) — Discovery + Requirements R1-R10 confirmed
- Phase 2: APPROVED (2026-02-09) — 3 feasibility reports (Mathpix, Claude Vision, PDF Gen)
- Phase 3: APPROVED (2026-02-09) — 6-stage pipeline + MCP Server architecture
- Phase 4: APPROVED (2026-02-09) — 10-section plan (1274L), 3 implementers, 8 tasks, G4-1..G4-8 ALL PASS
- Phase 5: CONDITIONAL_PASS (2026-02-09) — 24 findings (0C/4H/10M/10L), 4 conditions tracked
- Phase 6: APPROVED (2026-02-09) — 33 files, 3 implementers, 8 tasks, all 4 Phase 5 conditions met

## Phase 1 Summary
Requirements R1-R10 crystallized through freeform Q&A with user.
Key decisions: MCP Server architecture (D-1), 6-stage pipeline (D-2), no Anthropic API (D-8).

## Phase 2 Summary
3 parallel researchers investigated feasibility:
- Mathpix API: Math OCR EXCELLENT, bbox VERY GOOD, Korean printed GOOD
- Claude Vision: bbox NOT FEASIBLE, math reasoning BEST, logic detection BEST
- PDF Generation: XeLaTeX + kotex = gold standard, Pandoc for automation

Key finding: Claude bbox limitation → Gemini 3.0 Pro API added (D-3).

## Phase 3 Summary
Architecture designed: 6-stage pipeline with MCP Server tools.
VERIFY/COMPOSE stages use Claude native reasoning (D-4).
Interface contracts defined for all stage transitions.

## Phase 4: Detailed Design — IN_PROGRESS

**PT:** Task #1 (PT-v1)
**Start:** 2026-02-09
**Team:** cow-pipeline-redesign-write-plan

### Teammate Plan
| Name | Role | Mode | PT Version | Status |
|------|------|------|------------|--------|
| architect-1 | architect | acceptEdits | PT-v1 | SPAWNING |

### Workflow
1. Spawn architect-1 with full PT context + GC-v3 + research reports
2. Understanding verification (3 probing questions + alternative defense)
3. Architect produces 10-section implementation plan
4. Gate 4 evaluation (G4-1 through G4-8)
5. GC-v3 → GC-v4, PT-v1 → PT-v2

### Gate 4 Result
- **Verdict:** APPROVED (all 8 criteria PASS)
- **Artifacts:** 1274L plan, L1/L2/L3, gate-record.yaml
- **GC:** v3 → v4 | **PT:** v1 → v2
- **Key decisions:** 3 implementers, 8 tasks, 7 V-HIGH files
- **architect-1:** shutdown clean, artifacts preserved

### Pipeline Status (Phase 4 COMPLETE)
```
P1 [████████] DONE  P2 [████████] DONE  P3 [████████] DONE
P4 [████████] DONE  P5 [▓░░░░░░░] 5%    P6 [________] ---
P7 [________] ---   P8 [________] ---   P9 [________] ---
```

---

## Phase 5: Plan Validation — IN_PROGRESS

**PT:** Task #1 (PT-v2)
**Start:** 2026-02-09
**Team:** cow-pipeline-redesign-validation

### Teammate Plan
| Name | Role | Mode | PT Version | Status |
|------|------|------|------------|--------|
| devils-advocate-1 | devils-advocate | default | PT-v2 | SPAWNING |

### Workflow
1. Spawn devils-advocate-1 with plan + GC-v4
2. Challenge across 6 categories (Correctness, Completeness, Consistency, Feasibility, Robustness, Interfaces)
3. Verdict: CONDITIONAL_PASS (24 findings)
4. Gate 5 CONDITIONAL_PASS approved
5. GC-v4 → GC-v5, PT-v2 → PT-v3

### Gate 5 Result
- **Verdict:** CONDITIONAL_PASS (0 CRITICAL, 4 HIGH mitigated, 10 MEDIUM, 10 LOW)
- **HIGH issues:** cnt_to_bbox regression, MCP SDK stability, Gemini bbox format, merge_regions() spec
- **Conditions for Phase 6:**
  - COND-1: Impl-2 cnt_to_bbox compatibility guidance
  - COND-2: Pre-spawn MCP SDK import verification
  - COND-3: Impl-2 Gemini bbox normalization requirement
  - COND-4: Impl-2 merge_regions() IoU algorithm spec
- **devils-advocate-1:** shutdown clean, artifacts preserved

### Pipeline Status (Phase 5 COMPLETE)
```
P1 [████████] DONE  P2 [████████] DONE  P3 [████████] DONE
P4 [████████] DONE  P5 [████████] DONE  P6 [▓░░░░░░░] 5%
P7 [________] ---   P8 [________] ---   P9 [________] ---
```

---

## Phase 6: Implementation — COMPLETE

**PT:** Task #1 (PT-v3)
**Start:** 2026-02-09
**Team:** cow-pipeline-redesign-execution

### Pre-Spawn Checks
- COND-2: MCP SDK import verification → deferred to Impl-1 T-1 (venv-based, PEP 668)

### Plan Deviations
- **DEV-1:** FastMCP pattern replaces low-level Server pattern for all __main__.py files.
- **DEV-2:** pyproject.toml build-backend = setuptools.build_meta (plan's value doesn't exist).
- **DEV-3:** Added cow_create_session tool to storage (session metadata lifecycle).
- **DEV-4:** cow_ tool name prefix for namespace collision prevention.

### Implementer Results
| Name | Role | Tasks | Files | Lines | Status |
|------|------|-------|-------|-------|--------|
| implementer-1 | Foundation+Ingest+Storage | T-1,T-2,T-3 | 16 | ~800 | COMPLETE |
| implementer-2 | OCR+Vision | T-4,T-5 | 8 | ~1090 | COMPLETE |
| implementer-3 | Review+Export+MCP | T-6,T-7,T-8 | 9 | ~997 | COMPLETE |

### Phase 5 Conditions Met
| Condition | Status | Implementer |
|-----------|--------|-------------|
| COND-1 (cnt_to_bbox compat) | MET | Impl-2 (5 tests) |
| COND-2 (MCP SDK import) | MET | Impl-1 (v1.26.0) |
| COND-3 (Gemini bbox norm) | MET | Impl-2 |
| COND-4 (merge_regions IoU) | MET | Impl-2 (3 tests) |

### Gate 6 Result
- **Verdict:** APPROVED (G6-1..G6-7 ALL PASS)
- **Artifacts:** 33 files, L1/L2/L3 per implementer, gate-record.yaml
- **GC:** v5 → v6 | **PT:** v3 → v4
- **All implementers:** shutdown clean, artifacts preserved

### Pipeline Status (Phase 6 COMPLETE)
```
P1 [████████] DONE  P2 [████████] DONE  P3 [████████] DONE
P4 [████████] DONE  P5 [████████] DONE  P6 [████████] DONE
P7 [▓░░░░░░░] 5%    P8 [________] ---   P9 [________] ---
```

---

## Phase 7-8: Verification + Integration — PENDING

Decision: Given this is a NEW codebase (no existing tests, no integration points to merge),
Phase 7-8 is deferred. The implementation was self-tested by each implementer:
- Impl-1: import verification + JSON round-trip
- Impl-2: COND-1 (5 tests), COND-4 (3 tests), server startup
- Impl-3: 16 self-tests (10 import + 6 async DB)

Full integration testing requires actual API keys (Mathpix, Gemini) and runtime environment
(TeX Live for XeLaTeX). These are deferred to first real usage.
