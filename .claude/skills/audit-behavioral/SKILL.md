---
name: audit-behavioral
description: |
  [P2·Research·Behavioral] Predicts runtime behavior changes and regression risks.

  WHEN: After research-codebase AND research-external complete. Wave 2 parallel audit.
  DOMAIN: research (skill 4 of 7). Parallel: static ∥ behavioral ∥ relational ∥ impact.
  INPUT_FROM: research-codebase (existing behaviors), research-external (known issues/workarounds), design-architecture (change scope).
  OUTPUT_TO: research-coordinator (behavior predictions for cross-dimensional consolidation).

  METHODOLOGY: (1) Ingest Wave 1 findings, (2) Identify behavior-bearing components affected by design, (3) Predict side effects and regressions per component, (4) Classify risk (HIGH/MEDIUM/LOW) with evidence, (5) Report predictions + risk matrix with file:line references.
  OUTPUT_FORMAT: L1 YAML behavior change summary, L2 markdown prediction report with risk matrix.
user-invocable: false
disable-model-invocation: false
---

# Audit — Behavioral (Runtime Behavior Prediction)

## Execution Model
- **TRIVIAL**: Lead-direct. Inline assessment of 1-2 behavior-bearing files. No agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns:25). Map design changes to existing behaviors. Predict side effects.
- **COMPLEX**: Spawn 2 analysts scoped by subsystem (maxTurns:25 each). Each predicts behavior changes within assigned component boundaries.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p2-audit-behavioral.md`, sends micro-signal: `PASS|changes:{N}|risks:{N}|ref:/tmp/pipeline/p2-audit-behavioral.md`.

## Decision Points

### Component Scope Strategy
Based on design-architecture change scope breadth.
- **≤5 behavior-bearing components**: Single analyst covers all. maxTurns: 20.
- **6-15 components**: Single analyst, prioritize by risk. maxTurns: 25.
- **>15 components**: Spawn 2 analysts scoped by subsystem. maxTurns: 25 each.
- **Default**: Single analyst (STANDARD tier).

### Risk Escalation Threshold
- **Conservative (escalate at MEDIUM)**: When design changes affect error handling or fallback paths.
- **Standard (escalate at HIGH only)**: Default for most changes.

## Methodology

### 1. Ingest Wave 1 Findings
Read research-codebase L1/L2 to extract:
- Existing runtime behaviors (hook execution order, event handling, file processing flows)
- Current error handling patterns and their expected behavior
- State management patterns (configuration loading, caching, persistence)

Read research-external L2 for:
- Known issues and workarounds in external dependencies
- Documented behavioral quirks that design changes might interact with

Read design-architecture L1/L2 for:
- Which components are being added, modified, or removed
- Architecture decisions that change existing control flow

### 2. Identify Behavior-Bearing Components
A behavior-bearing component is any file/module whose execution produces observable effects:
- **Control flow**: Files that determine execution order (hooks, routers, dispatchers)
- **State mutation**: Files that read/write configuration, cache, or persistent state
- **External interaction**: Files that call external services, tools, or MCP servers
- **Error handling**: Files with try/catch, error propagation, or fallback logic

For each component, document:
- Current behavior (what it does now, with file:line reference)
- Design change affecting it (which architecture decision modifies this component)
- Overlap zone: where current behavior and design change intersect

### 3. Predict Side Effects and Regressions
For each affected behavior-bearing component, predict:

**Side Effects** (new behaviors introduced by the design change):
- What new behavior will this component exhibit?
- Which other components will be affected by this new behavior?
- Is the side effect intended by the architecture decision or unintended?

**Regressions** (existing behaviors that may break):
- Which current behavior is at risk of breaking?
- What is the regression mechanism? (removed dependency, changed interface, altered timing)
- Is the regression detectable during implementation or only at runtime?

Evidence requirement: Every prediction must reference both the current behavior (file:line) and the design decision (ADR or component spec) that creates the risk.

### 4. Classify Risk Levels
Apply risk classification to each prediction:

| Risk Level | Criteria | Action Guidance |
|-----------|---------|-----------------|
| HIGH | Breaks existing observable behavior, no fallback exists, affects multiple downstream components | Must be addressed in plan phase. Block implementation if unmitigated. |
| MEDIUM | Changes behavior in detectable ways, fallback exists or impact is contained to one component | Document in plan. Implementation should include regression test. |
| LOW | Minor behavioral change, easily reversible, limited blast radius | Note in plan. No special handling required. |

Risk factors that increase severity:
- Component is a hotspot (high fan-in from audit-static perspective)
- No existing test coverage for the affected behavior
- Change affects error handling or fallback paths
- Multiple design decisions interact at the same component

### 5. Report Predictions and Risk Classification
Produce final output with:
- Per-component behavior change table with current vs predicted behavior
- Side effect inventory with intended/unintended classification
- Regression risk matrix sorted by risk level (HIGH first)
- Cross-component interaction warnings (when multiple predictions affect the same downstream)
- Summary: total changes predicted, risk distribution (HIGH/MEDIUM/LOW counts)

### Delegation Prompt Specification

#### COMPLEX Tier (2 parallel analysts)
- **Context**: Paste research-codebase L1/L2 behavior patterns. Paste research-external L2 known issues. Paste design-architecture L1 `components[]` with change scope. Assign subsystem: `{subsystem_name}`.
- **Task**: "Identify all behavior-bearing components within assigned subsystem. For each: document current behavior (file:line), predict side effects and regressions from design changes, classify risk (HIGH/MEDIUM/LOW) with evidence from both current code and design decisions."
- **Constraints**: Read-only analysis (analyst agent, no Bash). Scope to assigned subsystem only. No prescriptive recommendations. maxTurns: 25.
- **Expected Output**: L1 YAML: total_changes, risk_high/medium/low, conflicts. L2: per-component behavior change table, side effect inventory, regression risk matrix.
- **Delivery**: SendMessage to Lead: `PASS|changes:{N}|risks:{N}|ref:/tmp/pipeline/p2-audit-behavioral.md`

#### STANDARD Tier (single analyst)
Same as COMPLEX but single analyst covering all components. No subsystem partitioning.

#### TRIVIAL Tier
Lead-direct inline. Read 1-2 behavior-bearing files, note obvious risk. No formal DPS.

## Failure Handling

### No Behavior-Bearing Components Found
- **Cause**: Design changes only affect static content (documentation, configuration values)
- **Action**: Report `changes: 0, risks: 0`. This is valid for documentation-only changes.
- **Route**: research-coordinator with empty prediction set

### Design Scope Too Broad
- **Cause**: Architecture decisions affect many components, analyst cannot cover all within turn budget
- **Action**: Prioritize HIGH-risk components. Report partial coverage with uncovered component list.
- **Route**: research-coordinator with partial flag

### Conflicting Predictions
- **Cause**: Two design decisions create contradictory behavior predictions for the same component
- **Action**: Document both predictions. Flag as design conflict requiring resolution.
- **Route**: research-coordinator with conflict flag for escalation

## Anti-Patterns

### DO NOT: Prescribe Solutions
Behavioral audit predicts what will happen, not what should be done about it. Statements like "refactor component X to avoid regression" are plan-phase work. Report the prediction and let plan skills determine the response.

### DO NOT: Predict Without Evidence
Every prediction must cite both the current behavior (file:line) and the design decision creating the change. Speculation without grounding in concrete code or architecture decisions is not a valid prediction.

### DO NOT: Conflate Static and Behavioral Analysis
Import chains and file dependencies are audit-static's domain. Behavioral audit focuses on runtime effects: what happens when code executes, not which files reference which. If you find a dependency issue, note it for audit-static cross-reference but do not analyze it here.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-codebase | Existing behaviors, patterns, conventions | L1 YAML: pattern inventory, L2: behavior descriptions with file:line |
| research-external | Known issues, workarounds, behavioral quirks | L2: issue descriptions with source URLs |
| design-architecture | Change scope, component modifications | L1 YAML: components list, L2: ADRs with change details |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-coordinator | Behavior predictions + risk classification | Always (Wave 2 -> Wave 2.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| No behavior-bearing components | research-coordinator | Empty prediction set with explanation |
| Analyst exhausted | research-coordinator | Partial predictions + uncovered component list |
| Design conflict detected | research-coordinator | Conflicting predictions with both ADR references |

## Quality Gate
- Every prediction cites current behavior (file:line) AND triggering design decision (ADR)
- Risk classification applied to all predictions with criteria documented
- No prescriptive recommendations (predictions only, not solutions)
- Side effects classified as intended or unintended
- Cross-component interactions identified when multiple predictions share downstream targets
- Summary statistics: total changes, HIGH/MEDIUM/LOW distribution

## Output

### L1
```yaml
domain: research
skill: audit-behavioral
total_changes: 0
risk_high: 0
risk_medium: 0
risk_low: 0
conflicts: 0
predictions:
  - component: ""
    change_type: side_effect|regression
    risk: HIGH|MEDIUM|LOW
    design_decision: ""
```

### L2
- Per-component behavior change table (current vs predicted)
- Side effect inventory with intended/unintended classification
- Regression risk matrix sorted by severity
- Cross-component interaction warnings
- Design conflict report (if any)
- Evidence trail: file:line references for all predictions
