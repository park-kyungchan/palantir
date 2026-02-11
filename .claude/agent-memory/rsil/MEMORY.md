# RSIL Agent Memory

## 1. Configuration
- Last review: 2026-02-11
- Total reviews: 11 (global: 1, narrow: 4, retroactive: 6)
- Cumulative findings: 92 (accepted: 86, rejected: 2, deferred: 4)
- Acceptance rate: 93%
- Active lenses: L1-L8

## 2. Lens Performance
| Lens | Applied | Findings | Accepted | Rate |
|------|---------|----------|----------|------|
| L1 TRANSITION INTEGRITY | 8 | 7 | 7 | 100% |
| L2 EVALUATION GRANULARITY | 5 | 4 | 4 | 100% |
| L3 EVIDENCE OBLIGATION | 9 | 9 | 9 | 100% |
| L4 ESCALATION PATHS | 6 | 5 | 5 | 100% |
| L5 SCOPE BOUNDARIES | 13 | 16 | 16 | 100% |
| L6 CLEANUP ORDERING | 3 | 2 | 2 | 100% |
| L7 INTERRUPTION RESILIENCE | 6 | 5 | 4 | 80% |
| L8 NAMING CLARITY | 10 | 11 | 11 | 100% |

Top performers: L5 (16 findings, 100% — highest yield), L8 (11), L3 (9)
Improving: L7 (5 findings, 80% — up from 75%)

## 3. Cross-Cutting Patterns
Patterns applicable across ANY target. One-off findings stay in tracker.

### P-1: Evidence Sources in All L2 Outputs
- Origin: P5-R1
- Scope: All teammate types producing L2 output
- Principle: Require "Evidence Sources" section in every L2-summary.md
- Applied in: plan-validation-pipeline, agent-common-protocol.md

### P-2: Explicit Checkpoint Steps in Directives
- Origin: P4-R1
- Scope: All skills that spawn teammates requiring understanding verification
- Principle: Structure as "Step 1: Read+Explain → Wait → Step 2: Execute"
- Applied in: agent-teams-write-plan (S-2), agent-teams-execution-plan

### P-3: Cross-File Integration Audit as Standard Step
- Origin: P6 (full RSIL review)
- Scope: All pipeline skill reviews
- Principle: Bidirectional consistency audit catches drift that single-file review misses
- Applied in: rsil-review methodology (standard)

### P-4: Rejection Cascade Specification
- Origin: P9-R1
- Scope: Skills with 2+ user confirmation gates
- Principle: Document which artifacts preserved, which ops skipped, what cleanup needed on rejection
- Applied in: delivery-pipeline

### P-5: Phase 0 Documentation Gap (Confirmed)
- Origin: RA-R1-1, RA-R1-2 (retroactive audit S-1)
- Scope: All pipeline skills with Phase 0 + CLAUDE.md §2
- Principle: Phase 0 (PT Check) must be reflected in CLAUDE.md §2. Done in S-6.

### P-6: Cross-File Naming Consistency
- Origin: IA-3 (S-7 integration audit), F-S6-05 (S-6)
- Scope: All cross-references between CLAUDE.md, skills, and reference docs
- Principle: Section names referenced in cross-file instructions must exactly match target section headers. A rename in one file requires grep + update in all referencing files.
- Applied in: CLAUDE.md §6 → agent-catalog.md "Spawn Quick Reference"

## 4. Lens Evolution
No new lens candidates from S-6/S-7. L5 continues highest yield. L7 improving steadily (80%).
