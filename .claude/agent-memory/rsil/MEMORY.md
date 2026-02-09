# RSIL Agent Memory

## 1. Configuration
- Last review: 2026-02-09
- Total reviews: 5 (global: 1, narrow: 4)
- Cumulative findings: 28 (accepted: 23, rejected: 2, deferred: 3)
- Acceptance rate: 82%
- Active lenses: L1-L8

## 2. Lens Performance
| Lens | Applied | Findings | Accepted | Rate |
|------|---------|----------|----------|------|
| L1 TRANSITION INTEGRITY | 5 | 4 | 4 | 100% |
| L2 EVALUATION GRANULARITY | 3 | 2 | 2 | 100% |
| L3 EVIDENCE OBLIGATION | 5 | 5 | 5 | 100% |
| L4 ESCALATION PATHS | 3 | 2 | 2 | 100% |
| L5 SCOPE BOUNDARIES | 5 | 5 | 5 | 100% |
| L6 CLEANUP ORDERING | 2 | 1 | 1 | 100% |
| L7 INTERRUPTION RESILIENCE | 3 | 2 | 1 | 50% |
| L8 NAMING CLARITY | 3 | 2 | 2 | 100% |

Top performers: L3, L5 (highest finding yield with 100% acceptance)
Improving: L7 (2 findings, 50% acceptance — up from 0%)

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
