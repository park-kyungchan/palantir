---
name: validate-consumer
description: >-
  Validates consumer fitness of artifacts — checks that
  outputs are usable by intended downstream consumers.
  P4: verifies plan outputs contain all data fields
  required by orchestrate-* consumers with correct format
  and granularity. P7: verifies execution outputs match
  DPS-declared output contracts and micro-signal formats.
  Verdict: PASS (all consumer data requirements met),
  FAIL (missing required fields or format mismatch).
  NEW axis — no legacy predecessor. Parallel with other
  validate-* axis skills. Use after plan domain complete
  (P4) or execution-review PASS (P7). Reads from upstream
  outputs + downstream INPUT_FROM declarations (P4) or
  execution outputs + declared output contracts (P7).
  Produces consumer fitness verdict for
  validate-coordinator. On FAIL, routes to owning plan-*
  (P4) or execution-* (P7) skill. DPS needs PHASE_CONTEXT
  + consumer declarations. Exclude internal artifact
  details beyond declared contracts.
user-invocable: true
disable-model-invocation: true
---

# Validate — Consumer Fitness

## Execution Model
- **TRIVIAL**: Lead-direct. Quick field cross-reference on 1-2 plan or execution outputs. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic consumer field mapping across 3-6 outputs.
- **COMPLEX**: Spawn analyst (maxTurns:30). Full cross-domain consumer fitness audit — all plan-*/execution-* output contracts vs downstream declarations.

## Phase Context

| Phase | Artifacts | Thresholds | Failure Route |
|-------|-----------|------------|---------------|
| P4 | Plan outputs + orchestrate-* INPUT_FROM declarations | All declared consumer fields present with correct format and granularity | Owning plan-* skill |
| P7 | Execution outputs + skill description output contracts | All L1 YAML contract fields present; micro-signal format matches signal_format | Owning execution-* skill |

Note: NEW axis — no legacy predecessor. PHASE_CONTEXT in DPS determines which row applies.

## Phase-Aware Execution
- **Spawn**: Spawn agent (`run_in_background:true`, `context:fork`). Agent writes output to file.
- **Delivery**: Agent writes result to `tasks/{work_dir}/{phase}-validate-consumer.md`, micro-signal: `PASS|phase:{P4|P7}|gaps:{N}|ref:tasks/{work_dir}/{phase}-validate-consumer.md`.

→ See `.claude/resources/phase-aware-execution.md` for team spawn pattern detail.

## Decision Points

### P4 — Plan Output Consumer Fitness
- **All orchestrate-* INPUT_FROM fields present in upstream plan outputs at declared granularity**: PASS.
- **Any required consumer field missing or wrong granularity**: FAIL. Route to the owning plan-* skill (e.g., missing field from plan-static → route to plan-static).
- **Field present but format mismatch** (e.g., string vs list): FAIL. Owning plan-* skill must fix.
- Only explicit INPUT_FROM declarations count. Do not infer implicit consumer requirements.

### P7 — Execution Output Contract Fitness
- **All L1 YAML fields from skill description output contract present in execution outputs**: PASS.
- **Any declared L1 field absent from output**: FAIL. Route to owning execution-* skill.
- **Micro-signal format deviates from declared signal_format**: FAIL. Route to owning execution-* skill.
- If no output contract is declared in skill description → WARN Lead (undeclared contract gap), do not FAIL.

### Consumer Attribution
When a gap is found, attribute it to the owning skill, not the consumer:
- P4 gap: owning plan-* skill (producer) must add/fix the field.
- P7 gap: owning execution-* skill must correct its output contract compliance.

## Methodology

P4 steps: (1) Inventory plan outputs — collect all L1 YAML fields produced by plan-static, plan-behavioral, plan-relational, plan-impact. (2) Extract consumer INPUT_FROM declarations from orchestrate-* skill descriptions. (3) Cross-reference: for each declared consumer field, verify plan output contains it at correct format and granularity. (4) Report gaps with owning plan-* skill attribution.

P7 steps: (1) Inventory execution outputs — collect all files produced by execution-* skills. (2) Extract declared output contracts from skill description L1 YAML specs (signal_format + L1 fields). (3) Verify format conformance — each output's L1 fields match declared spec; micro-signal matches signal_format template. (4) Report gaps with owning execution-* skill attribution.

→ See `resources/methodology.md` for analyst DPS templates, consumer field mapping tables, and contract verification format.
→ See `.claude/resources/dps-construction-guide.md` for DPS v5 template fields.

## Iteration Tracking (D15)
- Lead manages `metadata.iterations.validate-consumer: N` in PT before each invocation.
- Iteration 1: strict mode — FAIL returns to owning skill with field gap evidence.
- Iteration 2: relaxed mode — proceed with risk flags, document gaps in phase_signals.
- Max iterations: 2.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Upstream outputs missing or INPUT_FROM declarations unavailable | L0 Retry | Re-invoke same agent, same DPS |
| Field mapping incomplete or declarations partially extracted | L1 Nudge | Respawn with refined DPS adding missing skill descriptions |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with reduced scope per domain |
| Consumer contract schema changed or upstream skill descriptions stale | L3 Restructure | Rebuild consumer field inventory from current skill descriptions |
| No output contracts declared across multiple skills | L4 Escalate | AskUserQuestion — missing contract specification is strategic gap |

→ See `.claude/resources/failure-escalation-ladder.md` for full L0–L4 escalation protocol.

## Anti-Patterns

### DO NOT: Infer Implicit Consumer Requirements
Only check fields explicitly declared in INPUT_FROM or output contract specs. Do not flag "likely needed" fields that no consumer has declared.

### DO NOT: Check Internal Artifact Details
Validate declared contract boundaries only. Structural correctness of L2 artifact bodies belongs to validate-syntactic.

### DO NOT: Mix P4 and P7 Consumer Logic
P4 checks plan→orchestrate data flow. P7 checks execution→downstream output contracts. Never apply P4 consumer declarations as P7 criteria or vice versa.

### DO NOT: Flag Undeclared Gaps as FAIL
If a consumer has no INPUT_FROM declaration, or an execution skill has no output contract in its description, WARN Lead and document the undeclared gap. FAIL requires an explicit declaration to fail against.

### DO NOT: Route All Gaps to Validate-Coordinator
FAIL routes to the owning upstream skill, not the coordinator. Only a PASS verdict proceeds to validate-coordinator.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-static / plan-behavioral / plan-relational / plan-impact (P4) | Plan L1 YAML outputs | L1 YAML fields per skill |
| orchestrate-* skill descriptions (P4) | INPUT_FROM declarations | Frontmatter description text |
| execution-review (P7) | PASS signal + execution output file list | L1 YAML: status:PASS, files[] |
| execution-* skill descriptions (P7) | Declared output contracts (L1 YAML spec + signal_format) | Frontmatter description + Output section |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| validate-coordinator | Consumer fitness verdict with gap evidence | Always (parallel axis → coordinator consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing consumer field in plan output (P4) | Owning plan-* skill | Field name, consumer skill, expected format/granularity |
| Format/granularity mismatch in plan output (P4) | Owning plan-* skill | Field name, current format, expected format |
| L1 YAML field absent from execution output (P7) | Owning execution-* skill | Field name, declared spec source, output file path |
| Micro-signal format deviation (P7) | Owning execution-* skill | Actual signal, declared signal_format template |
| Missing declaration source | Lead | Which skill lacks INPUT_FROM or output contract |

→ See `.claude/resources/transitions-template.md` for standard transition format.

## Quality Gate
- All orchestrate-* INPUT_FROM declarations inventoried and cross-referenced (P4)
- All plan-* output L1 YAML fields checked against consumer declarations (P4)
- All execution-* output contracts extracted from skill descriptions (P7)
- All execution outputs checked against declared L1 field specs and signal_format (P7)
- Every gap attributed to owning upstream skill with evidence
- Verdict (PASS/FAIL) with explicit gap count and consumer attribution

→ See `.claude/resources/quality-gate-checklist.md` for standard quality gate protocol.

## Output

### L1
```yaml
domain: validate
skill: validate-consumer
phase: P4|P7
verdict: PASS|CONDITIONAL_PASS|FAIL
pt_signal: "metadata.phase_signals.{phase}_validate_consumer"
signal_format: "{VERDICT}|phase:{P4|P7}|gaps:{N}|ref:tasks/{work_dir}/{phase}-validate-consumer.md"
consumer_declarations_checked: 0
gaps_found: 0
findings:
  - type: missing_field|format_mismatch|granularity_mismatch|signal_format_deviation|undeclared_contract
    owning_skill: ""
    field: ""
    consumer: ""
    evidence: ""
```

### L2
- P4: consumer field mapping table (orchestrate-* declaration vs plan-* output field status)
- P4: gap list with owning plan-* skill and field specification detail
- P7: execution output contract compliance table (declared field vs actual output)
- P7: micro-signal format comparison (declared signal_format vs actual)
- Undeclared contract warnings per skill (WARN, not FAIL)
- Verdict justification with explicit gap count

→ See `.claude/resources/output-micro-signal-format.md` for micro-signal format spec.
