---
name: validate-relational
description: >-
  Validates cross-component consistency of artifacts via
  phase-parameterized DPS. P4: checks contract integrity
  against relationship graph — asymmetric or missing
  contracts. P7: verifies bidirectional cross-file reference
  integrity, sequence ordering, and declared counts.
  Verdict: PASS (P4 zero HIGH gaps; P7 all references
  bidirectional and counts match), FAIL (P4 HIGH asymmetric
  or >5 gaps; P7 inconsistency detected). Parallel with
  other validate-* axis skills. Use after plan domain
  complete (P4) or execution-review PASS (P7). Reads from
  plan-relational + audit-relational L3 (P4) or execution
  artifacts + CLAUDE.md counts (P7). Produces relational
  verdict for validate-coordinator. On FAIL, routes to
  plan-relational (P4) or execution-infra (P7). DPS needs
  PHASE_CONTEXT + upstream outputs. Exclude other axis
  results.
user-invocable: true
disable-model-invocation: true
---

# Validate — Relational Integrity

## Execution Model
- **TRIVIAL**: Lead-direct. Inline edge and reference check on 2-3 files. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Full contract-vs-graph cross-reference (P4) or relationship graph construction (P7).
- **COMPLEX**: Spawn analyst (maxTurns:30). P7 may spawn 2 analysts — bidirectionality split from sequence/count verification.

## Phase Context

| Phase | Artifacts | Thresholds | Failure Route |
|-------|-----------|------------|---------------|
| P4 | plan-relational contracts + audit-relational L3 graph | Zero HIGH gaps; total gaps ≤ 2 | plan-relational |
| P7 | Execution artifacts + skill descriptions (INPUT_FROM/OUTPUT_TO) + CLAUDE.md counts | All references bidirectional; counts match filesystem; phase sequence P0→P8 | execution-infra |

Note: PHASE_CONTEXT in DPS determines which row applies. Gap types differ per phase — do not mix.

## Phase-Aware Execution
- **Spawn**: Spawn agent (`run_in_background:true`, `context:fork`). Agent writes output to file.
- **Delivery**: Agent writes result to `tasks/{work_dir}/{phase}-validate-relational.md`, micro-signal: `PASS|phase:{P4|P7}|gaps:{N}|ref:tasks/{work_dir}/{phase}-validate-relational.md`.

→ See `.claude/resources/phase-aware-execution.md` for team spawn pattern detail.

## Decision Points

### P4 — Contract Integrity
- **Zero HIGH gaps AND total gaps ≤ 2**: PASS. Route to validate-coordinator.
- **Only MEDIUM gaps AND total ≤ 5**: CONDITIONAL_PASS. Route with risk annotation.
- **Any HIGH gap OR total > 5**: FAIL. Route to plan-relational with gap evidence.
- **> 50% relationships lack contracts**: Always FAIL (plan-audit misalignment).

Gap types:
- **ASYMMETRIC**: Bidirectional relationship with contract covering only one direction. HIGH if mutation-direction uncovered; MEDIUM if read-only uncovered.
- **MISSING**: Relationship with no contract. HIGH if cross-boundary, MEDIUM if intra-module.
- **ORPHAN**: Contract with no matching relationship. MEDIUM severity.

### P7 — Reference Consistency
- **All INPUT_FROM/OUTPUT_TO references bidirectional AND CLAUDE.md counts match filesystem AND phase sequence valid**: PASS.
- **Any unidirectional reference OR count drift OR unauthorized backward phase reference**: FAIL. Route to execution-infra.
- Phase sequence exemptions (never flag): homeostasis skills, cross-cutting skills, explicit FAIL routes.
- Coordinator pattern: skill-A → coordinator → skill-B creates valid indirect link. Do NOT flag as broken bidirectionality.

### Scope (P7)
Derived from change type: single skill frontmatter → that skill's INPUT_FROM/OUTPUT_TO only; domain-wide edit → all skills in domain + adjacent; CLAUDE.md edit → full count consistency; new skill creation → full bidirectionality + phase sequence + count.

## Methodology

P4 steps: (1) Build contract inventory from plan-relational outputs. (2) Build relationship inventory from audit-relational L3. (3) Cross-reference each relationship edge for contract existence and bidirectionality — build consistency matrix. (4) Classify gaps (ASYMMETRIC/MISSING/ORPHAN) by severity. (5) Report integrity verdict with evidence.

P7 steps: (1) Parse INPUT_FROM and OUTPUT_TO from all in-scope skill description frontmatter. Build directed reference graph. (2) Verify bidirectionality for each pair — exemptions: homeostasis, cross-cutting, FAIL routes. (3) Detect coordinator indirect links and exempt from broken-bidirectionality flags. (4) Verify CLAUDE.md declared counts (agents, skills, domains) against filesystem actuals. (5) Report consistency verdict with violations list.

→ See `resources/methodology.md` for analyst DPS templates, consistency matrix format, gap evidence template, and coordinator pattern algorithm.
→ See `.claude/resources/dps-construction-guide.md` for DPS v5 template fields.

## Iteration Tracking (D15)
- Lead manages `metadata.iterations.validate-relational: N` in PT before each invocation.
- Iteration 1: strict mode — FAIL returns to upstream with gap evidence.
- Iteration 2: relaxed mode — proceed with risk flags, document in phase_signals.
- Max iterations: 2.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Audit-relational L3 missing or tool error reading skill descriptions | L0 Retry | Re-invoke same agent, same DPS |
| Consistency matrix incomplete or relationships partially verified | L1 Nudge | Respawn with refined DPS targeting corrected file list + exemption docs |
| Analyst exhausted turns or stuck on circular dependency | L2 Respawn | Kill → fresh agent with reduced scope per domain |
| Relationship graph stale or plan-audit scope diverged | L3 Restructure | Modify task graph; re-run audit-relational or refresh CLAUDE.md counts |
| 3+ L2 failures or graph construction strategy unclear | L4 Escalate | AskUserQuestion with summary + options |

→ See `.claude/resources/failure-escalation-ladder.md` for full L0–L4 escalation protocol.

## Anti-Patterns

### DO NOT: Verify Contract Implementation
P4 verifies plan contract existence and bidirectionality, not implementation correctness. Check existence, not implementability.

### DO NOT: Require Bidirectionality for FAIL Routes
FAIL routes are inherently unidirectional error recovery paths. Never flag these as bidirectionality violations.

### DO NOT: Flag Homeostasis/Cross-Cutting for Phase Violations
manage-infra, self-diagnose, delivery-pipeline, pipeline-resume, and task-management are always exempt from forward-only phase sequence enforcement.

### DO NOT: Auto-Update CLAUDE.md Counts
This skill is strictly read-only. Filesystem always wins. Count fixes route to execution-infra.

### DO NOT: Assume Unidirectional Relationships
Many apparent one-way imports are bidirectional at runtime. Trust audit-relational L3 classification (P4) or coordinator pattern recognition (P7).

### DO NOT: Create or Modify Contracts
Report gaps with evidence. Contract revision is the plan domain's responsibility (P4). Reference fixes route to execution-infra (P7).

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-relational (P4) | Interface contracts with producer/consumer/type/direction | L1 YAML: contracts[] |
| research-coordinator (P4) | Audit-relational L3 relationship graph | L3: edges[] with source, target, type, bidirectional flag |
| execution-review (P7) | PASS signal + artifact file list | L1 YAML: status:PASS, files[] |
| CLAUDE.md + filesystem (P7) | Declared counts + actual skill/agent/domain counts | Direct read |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| validate-coordinator | Relational verdict with evidence | Always (parallel axis → coordinator consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| HIGH asymmetric or missing gap (P4) | plan-relational | Gap type, edge, severity, evidence |
| Plan-audit misalignment >50% (P4) | Lead | Divergence statistics |
| Bidirectionality violation (P7) | execution-infra | source, target, direction, missing_reverse |
| Phase sequence violation (P7) | Lead → execution-infra | source_phase, target, target_phase |
| CLAUDE.md count drift (P7) | execution-infra | component, declared, actual, diff |

→ See `.claude/resources/transitions-template.md` for standard transition format.

## Quality Gate
- Every relationship edge in the audit graph checked for contract existence (P4)
- All bidirectional relationships verified for contracts in both directions (P4)
- All gaps classified by type (ASYMMETRIC/MISSING/ORPHAN) and severity (P4)
- All INPUT_FROM/OUTPUT_TO references verified for bidirectionality with exemptions applied (P7)
- Phase sequence follows P0→P8 with coordinator indirect links recognized (P7)
- CLAUDE.md component counts match filesystem exactly (P7)
- Every finding has evidence citing specific edges, skill pairs, or count fields

→ See `.claude/resources/quality-gate-checklist.md` for standard quality gate protocol.

## Output

### L1
```yaml
domain: validate
skill: validate-relational
phase: P4|P7
verdict: PASS|CONDITIONAL_PASS|FAIL
pt_signal: "metadata.phase_signals.{phase}_validate_relational"
signal_format: "{VERDICT}|phase:{P4|P7}|gaps:{N}|ref:tasks/{work_dir}/{phase}-validate-relational.md"
findings:
  - type: asymmetric|missing|orphan|bidirectionality_violation|phase_sequence_violation|count_drift
    item: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
```

### L2
- P4: consistency matrix (relationship edge vs contract mapping) with gap classification
- P4: asymmetric contract analysis with direction and mutation details
- P4: coverage statistics (covered/asymmetric/missing/orphan counts)
- P7: relationship graph with bidirectionality status per pair
- P7: phase sequence violations with source/target phase comparison
- P7: CLAUDE.md count comparison (declared vs actual per component)
- Verdict justification with explicit gap counts and severity thresholds

→ See `.claude/resources/output-micro-signal-format.md` for micro-signal format spec.
