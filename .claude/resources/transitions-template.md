# Transitions Template

> Shared resource for pipeline skills. Documents the standard Receives From / Sends To / Failure Routes table format.

## Standard Transitions Table

Every pipeline skill must document three transition tables:

### Receives From

| Source Skill | Data Expected | Format |
|---|---|---|
| {upstream-skill-name} | {what data this skill needs} | {L1 YAML fields or L2 section reference} |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| {downstream-skill-name} | {what this skill produces} | {when to send: always, on PASS, on FAIL} |

### Failure Routes

| Failure Type | Route To | Data Passed |
|---|---|---|
| {failure description} | {Lead or specific skill} | {what info to include for recovery} |

## Pipeline Phase Transition Map

| Phase | Skills | Sends To (on PASS) |
|---|---|---|
| P0 Pre-Design | brainstorm, validate, feasibility | → P1 Design |
| P1 Design | architecture, interface, risk | → P2 Research |
| P2 Research | codebase, external, cc-verify, 4× audit, evaluation-criteria, coordinator | → P3 Plan |
| P3 Plan | static, behavioral, relational, impact | → P4 Plan-Verify |
| P4 Plan-Verify | static, behavioral, relational, impact, coordinator | → P5 Orchestrate |
| P5 Orchestrate | static, behavioral, relational, impact, coordinator | → P6 Execution |
| P6 Execution | code, infra, impact, review, cascade | → P7 Verify |
| P7 Verify | structural-content, consistency, quality, cc-feasibility | → P8 Delivery |
| P8 Delivery | delivery-pipeline | → END |

## Cross-Phase Data Flow Rules

1. **Forward only**: Data flows P0→P8. No backward references except via failure routes.
2. **Adjacent phases**: Skills primarily consume from the immediately preceding phase.
3. **Skip references**: Some skills reference 2+ phases back (e.g., execution-code reads plan-relational contracts). Document these explicitly.
4. **Parallel within phase**: Skills in the same phase (e.g., 4× audit-*) run in parallel and do NOT read each other's output.
