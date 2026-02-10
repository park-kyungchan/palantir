# RSIL Agent Memory

## 1. Configuration
- Last review: 2026-02-10
- Total reviews: 9 (global: 1, narrow: 4, retroactive: 4)
- Cumulative findings: 72 (accepted: 66, rejected: 2, deferred: 4)
- Acceptance rate: 92%
- Active lenses: L1-L8

## 2. Lens Performance
| Lens | Applied | Findings | Accepted | Rate |
|------|---------|----------|----------|------|
| L1 TRANSITION INTEGRITY | 8 | 7 | 7 | 100% |
| L2 EVALUATION GRANULARITY | 4 | 3 | 3 | 100% |
| L3 EVIDENCE OBLIGATION | 7 | 7 | 7 | 100% |
| L4 ESCALATION PATHS | 4 | 3 | 3 | 100% |
| L5 SCOPE BOUNDARIES | 11 | 13 | 13 | 100% |
| L6 CLEANUP ORDERING | 2 | 1 | 1 | 100% |
| L7 INTERRUPTION RESILIENCE | 5 | 4 | 3 | 75% |
| L8 NAMING CLARITY | 8 | 8 | 8 | 100% |

Top performers: L5 (13 findings, 100% acceptance — highest yield by far), L8 (8), L3/L1 (7 each)
Improving: L7 (4 findings, 75% acceptance — up from 50%)

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

### P-5: Phase 0 Documentation Gap (Candidate)
- Origin: RA-R1-1, RA-R1-2 (retroactive audit S-1)
- Scope: All pipeline skills with Phase 0 + CLAUDE.md §2
- Principle: Phase 0 (PT Check) is functional in all 7 skills but was absent from CLAUDE.md §2. Infrastructure documentation must reflect actual execution phases.
- Status: Confirmed for CLAUDE.md; needs S-6 (R4 CLAUDE.md) validation

## 4. Lens Evolution
No candidates yet. L2 (Evaluation Granularity) produced only 1 finding in S-1, but this may change with core targets (S-4, S-6). Monitoring.
