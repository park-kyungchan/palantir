# Skills Inventory — Complete (10 Skills)

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total skills | 10 |
| Pipeline skills (P0-P9) | 7 |
| Cross-cutting skills | 2 (rsil-global, permanent-tasks) |
| Standalone skills | 1 (palantir-dev) |
| Total lines | ~3,374 |
| Largest skill | agent-teams-execution-plan (511L) |
| Smallest skill | palantir-dev (97L) |

## Skill Details

### SKL-001: brainstorming-pipeline

| Property | Value |
|----------|-------|
| Path | `.claude/skills/brainstorming-pipeline/SKILL.md` |
| Lines | 490 |
| Phase | P0-3 (PT Check, Discovery, Research, Architecture) |
| Coordinator(s) | research-coordinator (P2), architecture-coordinator (COMPLEX P3) |
| Agents spawned | codebase-researcher, external-researcher, auditor, structure/interface/risk-architect |
| Trigger | New feature idea needing research + architecture |
| Tier routing | Yes (D-001: TRIVIAL/STANDARD/COMPLEX) |
| Description | Transforms feature idea into researched, validated architecture through structured team collaboration |

### SKL-002: agent-teams-write-plan

| Property | Value |
|----------|-------|
| Path | `.claude/skills/agent-teams-write-plan/SKILL.md` |
| Lines | 262 |
| Phase | P0 + P4 (Detailed Design) |
| Coordinator(s) | planning-coordinator (COMPLEX) |
| Agents spawned | decomposition-planner, interface-planner, strategy-planner (COMPLEX); plan-writer/architect (STANDARD) |
| Trigger | Architecture output from brainstorming-pipeline ready |
| Tier routing | Yes |
| Description | Architecture to concrete implementation plan through verified planner teammates |

### SKL-003: plan-validation-pipeline

| Property | Value |
|----------|-------|
| Path | `.claude/skills/plan-validation-pipeline/SKILL.md` |
| Lines | 313 |
| Phase | P0 + P5 (Plan Validation) |
| Coordinator(s) | validation-coordinator (COMPLEX), devils-advocate (TRIVIAL/STANDARD) |
| Agents spawned | correctness/completeness/robustness-challenger (COMPLEX); devils-advocate (STANDARD) |
| Trigger | Implementation plan from write-plan ready |
| Tier routing | Yes |
| Description | Last checkpoint before implementation — structured critique of plan |

### SKL-004: agent-teams-execution-plan

| Property | Value |
|----------|-------|
| Path | `.claude/skills/agent-teams-execution-plan/SKILL.md` |
| Lines | 511 |
| Phase | P0 + P6 (Implementation) |
| Coordinator(s) | execution-coordinator |
| Agents spawned | implementer(s), infra-implementer, spec-reviewer, code-reviewer, contract-reviewer, regression-reviewer |
| Trigger | Implementation plan ready (P4 complete) |
| Features | Adaptive parallelism, two-stage review, fix loops, D-012/D-014 integration |
| Description | Plan to working code through verified implementer teammates with integrated review |

### SKL-005: verification-pipeline

| Property | Value |
|----------|-------|
| Path | `.claude/skills/verification-pipeline/SKILL.md` |
| Lines | 419 |
| Phase | P7-8 (Testing + Integration) |
| Coordinator(s) | testing-coordinator |
| Agents spawned | tester, contract-tester, integrator (conditional) |
| Trigger | Phase 6 implementation complete |
| Features | D-001 tier awareness, contract-tester for interface tests |
| Description | Verifies implementation via tester teammates, then integrator for cross-boundary merges |

### SKL-006: delivery-pipeline

| Property | Value |
|----------|-------|
| Path | `.claude/skills/delivery-pipeline/SKILL.md` |
| Lines | 341 |
| Phase | P9 (Delivery) |
| Coordinator(s) | Lead-only (no teammates) |
| Trigger | Phase 7/8 complete, gate approved |
| Description | Consolidates pipeline output, git commit, archive session artifacts, MEMORY.md migration |

### SKL-007: rsil-global

| Property | Value |
|----------|-------|
| Path | `.claude/skills/rsil-global/SKILL.md` |
| Lines | 337 |
| Phase | Post-pipeline |
| Coordinator(s) | Lead-only (lightweight) |
| Trigger | Auto-invoked after pipeline delivery or .claude/ changes (>=2 files) |
| Features | Three-Tier Observation Window, ~2000 token budget, findings-only output |
| Description | INFRA health assessment with 8 universal lenses |

### SKL-008: rsil-review

| Property | Value |
|----------|-------|
| Path | `.claude/skills/rsil-review/SKILL.md` |
| Lines | 406 |
| Phase | Any (on-demand) |
| Coordinator(s) | Lead-only |
| Trigger | Manual invocation for targeted quality review |
| Features | 8 universal research lenses, Layer 1/2 boundary analysis, AD-15 filter |
| Description | Meta-Cognition quality review for any .claude/ INFRA component |

### SKL-009: permanent-tasks

| Property | Value |
|----------|-------|
| Path | `.claude/skills/permanent-tasks/SKILL.md` |
| Lines | 198 |
| Phase | Cross-cutting |
| Coordinator(s) | Lead-only |
| Trigger | Pipeline start, requirement changes, or auto-invoked from Phase 0 |
| Description | Creates/updates PERMANENT Task via TaskList search + Read-Merge-Write |

### SKL-010: palantir-dev

| Property | Value |
|----------|-------|
| Path | `.claude/skills/palantir-dev/SKILL.md` |
| Lines | 97 |
| Phase | Standalone (not part of pipeline) |
| Coordinator(s) | N/A |
| Trigger | Explicit `/palantir-dev` invocation only |
| Features | 6-language comparison (Java, Python, TypeScript, Go, C++, SQL) |
| Description | Programming language learning support for Palantir Dev/Delta |

## Pipeline Phase Coverage

```
P0 ─── brainstorming-pipeline, agent-teams-write-plan, plan-validation-pipeline,
       agent-teams-execution-plan, verification-pipeline (all do PT Check)
P1 ─── brainstorming-pipeline
P2 ─── brainstorming-pipeline
P3 ─── brainstorming-pipeline
P4 ─── agent-teams-write-plan
P5 ─── plan-validation-pipeline
P6 ─── agent-teams-execution-plan
P7 ─── verification-pipeline
P8 ─── verification-pipeline
P9 ─── delivery-pipeline
Post ─ rsil-global, rsil-review
X-cut  permanent-tasks
```

Every pipeline phase (P0-P9) is covered by exactly one skill. No gaps, no overlaps (except P0 which is a shared prerequisite check).
