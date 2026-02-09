# RSIL Agent Memory

## 1. Configuration
- Last review: 2026-02-08
- Total reviews: 4 (global: 0, narrow: 4)
- Cumulative findings: 24 (accepted: 19, rejected: 2, deferred: 3)
- Acceptance rate: 79%
- Active lenses: L1-L8

## 2. Lens Performance
| Lens | Applied | Findings | Accepted | Rate |
|------|---------|----------|----------|------|
| L1 TRANSITION INTEGRITY | 4 | 3 | 3 | 100% |
| L2 EVALUATION GRANULARITY | 3 | 2 | 2 | 100% |
| L3 EVIDENCE OBLIGATION | 4 | 3 | 3 | 100% |
| L4 ESCALATION PATHS | 3 | 2 | 2 | 100% |
| L5 SCOPE BOUNDARIES | 4 | 4 | 4 | 100% |
| L6 CLEANUP ORDERING | 2 | 1 | 1 | 100% |
| L7 INTERRUPTION RESILIENCE | 2 | 1 | 0 | 0% |
| L8 NAMING CLARITY | 3 | 2 | 2 | 100% |

Top performers: L1, L3, L5 (highest finding yield with 100% acceptance)
Low yield: L7 (1 finding, 0% acceptance — deferred to Layer 2)

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
- Applied in: agent-teams-write-plan, agent-teams-execution-plan

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

## 4. Lens Evolution
No candidates yet. Monitoring for patterns from future reviews.
