---
name: validate-behavioral
description: >-
  Validates runtime behavior correctness of artifacts via
  phase-parameterized DPS. P4: verifies behavior prediction
  completeness and rollback trigger specificity against
  audit-behavioral L3. P7: validates CC native field
  compliance and runtime feasibility against cc-reference
  cache. Verdict: PASS (P4 all HIGH behaviors predicted +
  rollbacks specified; P7 zero non-native fields), FAIL
  (P4 HIGH behavior unpredicted; P7 non-native field
  detected). Parallel with other validate-* axis skills.
  Use after plan domain complete (P4) or execution-review
  PASS (P7). Reads from plan-behavioral predictions (P4)
  or execution artifacts + cc-reference (P7). Produces
  behavioral verdict for validate-coordinator. On FAIL,
  routes to plan-behavioral (P4) or execution-infra (P7).
  DPS needs PHASE_CONTEXT + upstream outputs. Exclude
  other axis results.
user-invocable: true
disable-model-invocation: true
---

# Validate — Behavioral

## Execution Model
- **TRIVIAL**: Lead-direct. Inline prediction and field check. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of predictions (P4) or frontmatter fields (P7).
- **COMPLEX**: Spawn analyst (maxTurns:30). P7 may spawn claude-code-guide if cc-reference cache stale > 30 days or field unknown.

## Phase Context

| Phase | Artifacts | Thresholds | Failure Route |
|-------|-----------|------------|---------------|
| P4 | plan-behavioral predictions + audit-behavioral L3 | All HIGH behaviors predicted; all HIGH rollback triggers specific | plan-behavioral |
| P7 | Execution artifact frontmatter + cc-reference cache | Zero non-native fields; all value types match | execution-infra |

Note: PHASE_CONTEXT in DPS determines which row applies. Never mix P4 and P7 verdict logic in a single invocation.

## Phase-Aware Execution
- **Spawn**: Spawn agent (`run_in_background:true`, `context:fork`). Agent writes output to file.
- **Delivery**: Agent writes result to `tasks/{work_dir}/{phase}-validate-behavioral.md`, micro-signal: `PASS|phase:{P4|P7}|ref:tasks/{work_dir}/{phase}-validate-behavioral.md`.

→ See `.claude/resources/phase-aware-execution.md` for team spawn pattern detail.

## Decision Points

### P4 — Prediction Completeness
- **All HIGH-risk behavior changes have predictions AND specific rollback triggers**: PASS.
- **Any HIGH behavior unpredicted OR rollback trigger is generic** ("rollback if something goes wrong"): FAIL. Route to plan-behavioral.
- **Only MEDIUM behaviors unpredicted**: CONDITIONAL_PASS with risk annotation.
- Specificity test: trigger must describe what failure looks like for THAT specific change.

### P7 — CC Native Field Compliance
- **Zero non-native fields across all files**: PASS.
- **Any non-native field detected**: FAIL (BLOCKING). Route to execution-infra for removal.
- Field ambiguity: check cc-reference cache first. If absent and cache < 30 days → FAIL conservative. If cache stale → spawn claude-code-guide.
- Value type mismatch (e.g., `model: "fast"`) is FAIL equivalent to non-native field.

## Methodology
P4 steps: (1) Build prediction inventory from audit-behavioral L3. (2) Identify all HIGH-risk behavior changes. (3) For each HIGH change, verify prediction exists with specific rollback trigger. (4) Report verdict with evidence per change.

P7 steps: (1) Extract frontmatter fields from execution artifacts. (2) Check each field against cc-reference native skill/agent table. (3) Validate value types. (4) Report compliance verdict per file.

→ See `resources/methodology.md` for analyst DPS templates, field ambiguity decision tree, and phase-specific evidence formats.
→ See `.claude/resources/dps-construction-guide.md` for DPS v5 template fields.

## Iteration Tracking (D15)
- Lead manages `metadata.iterations.validate-behavioral: N` in PT before each invocation.
- Iteration 1: strict mode — FAIL returns to upstream with gap evidence.
- Iteration 2: relaxed mode — proceed with risk flags, document in phase_signals.
- Max iterations: 2.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Upstream missing (audit-behavioral L3 or cc-reference) | L0 Retry | Re-invoke same agent, same DPS |
| Prediction inventory incomplete or fields partially checked | L1 Nudge | Respawn with refined DPS targeting gap context |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS |
| Behavioral model stale or CC version changed | L3 Restructure | Modify task graph, re-run audit-behavioral or refresh cc-reference |
| 3+ L2 failures or conflicting field classification | L4 Escalate | AskUserQuestion with options |

→ See `.claude/resources/failure-escalation-ladder.md` for full L0–L4 escalation protocol.

## Anti-Patterns

### DO NOT: Verify Test Implementation
P4 verifies behavior prediction completeness, not test code. Check that HIGH behaviors have predictions and rollback triggers. Do not assess test quality or framework usage.

### DO NOT: Accept Generic Rollback Triggers
"Rollback if something goes wrong" fails the specificity test. Each HIGH-risk change needs a trigger condition naming the observable failure for that specific change.

### DO NOT: Auto-Remove Non-Native Fields
P7 is read-only verification. Report findings with evidence. Actual field removal routes to execution-infra.

### DO NOT: Mix Phase Logic
P4 verdict is about prediction coverage. P7 verdict is about field compliance. Never apply P4 thresholds when PHASE_CONTEXT = P7 or vice versa.

### DO NOT: Check L2 Body Content (P7)
Only frontmatter fields need CC compliance validation. L2 body checking belongs to validate-syntactic.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-behavioral (P4) | Behavior predictions with rollback triggers | L1 YAML: predictions[] with risk, rollback.trigger |
| research-coordinator (P4) | Audit-behavioral L3 behavior predictions | L3: changes[] with risk_level, component |
| execution-review (P7) | PASS signal + artifact file list | L1 YAML: status:PASS, files[] |
| execution-infra (P7) | Changed INFRA file list | L1: modified file paths |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| validate-coordinator | Behavioral verdict with evidence | Always (parallel axis → coordinator consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| HIGH behavior unpredicted (P4) | plan-behavioral | Unpredicted change IDs and risk level |
| Generic/missing rollback trigger (P4) | plan-behavioral | Change ID + trigger specificity gap |
| Non-native field detected (P7) | execution-infra | File path + field name + recommended removal |
| Missing upstream artifacts | Lead | Which upstream skill is missing output |

→ See `.claude/resources/transitions-template.md` for standard transition format.

## Quality Gate
- Every HIGH-risk behavior change checked for prediction existence (P4)
- Every HIGH-risk rollback trigger checked for specificity (P4)
- Every frontmatter field checked against cc-reference native table (P7)
- All value types validated for native fields (P7)
- Every finding has evidence citing specific change IDs or field names
- Verdict (PASS/FAIL) with explicit threshold comparison per phase

→ See `.claude/resources/quality-gate-checklist.md` for standard quality gate protocol.

## Output

### L1
```yaml
domain: validate
skill: validate-behavioral
phase: P4|P7
verdict: PASS|CONDITIONAL_PASS|FAIL
pt_signal: "metadata.phase_signals.{phase}_validate_behavioral"
signal_format: "{VERDICT}|phase:{P4|P7}|ref:tasks/{work_dir}/{phase}-validate-behavioral.md"
findings:
  - type: unpredicted_behavior|missing_rollback|weak_trigger|non_native_field|value_type_error
    item: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
```

### L2
- P4: prediction coverage matrix (HIGH/MEDIUM/LOW per change) with rollback trigger quality assessment
- P4: unpredicted change list with risk levels and evidence
- P7: per-file compliance breakdown with field-level status (native/non-native/wrong-type)
- P7: non-native field removal recommendations with file paths
- Verdict justification with explicit threshold comparison

→ See `.claude/resources/output-micro-signal-format.md` for micro-signal format spec.
