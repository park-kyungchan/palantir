# Audit — Behavioral: Detailed Methodology Reference

## H/M/L Scoring Rubrics

### HIGH Risk — Criteria
A prediction is HIGH when ALL of the following apply:
- The existing observable behavior breaks (users or downstream components see different results)
- No fallback path exists in current code (error handling does not route around the change)
- At least two downstream components are affected (fan-out risk)

Automatic HIGH escalators (any one is sufficient):
- Change touches the primary error-propagation path (top-level try/catch, hook error handlers)
- Component has zero existing test coverage AND is called by 3+ other modules
- Multiple design decisions interact at the same component simultaneously

### MEDIUM Risk — Criteria
A prediction is MEDIUM when:
- Behavior changes in a detectable way but a fallback exists OR impact is contained to one component
- The regression is caught during integration testing (not silently at runtime)
- The side effect is intended by the design decision but requires downstream adaptation

### LOW Risk — Criteria
A prediction is LOW when:
- The behavioral change is minor, easily reversible, and has a blast radius of one component
- The change does not affect external-facing behavior (internal state restructuring only)
- An equivalent fallback path already exists in code

### Risk Factor Scoring Table

| Factor | Weight | Applies When |
|--------|--------|--------------|
| High fan-in (3+ callers) | +1 severity | Component is imported/called by many modules |
| No test coverage | +1 severity | No unit or integration tests for affected behavior |
| Error handling path | +1 severity | Change modifies try/catch, fallback, or retry logic |
| Multi-decision intersection | +1 severity | 2+ ADRs converge on same component |
| Externally visible output | +1 severity | Change affects API response, file output, or UI state |

Score 0: LOW. Score 1-2: MEDIUM. Score 3+: HIGH. Override to HIGH if any automatic escalator applies.

---

## Behavior Change Pattern Taxonomy

### Type 1: Direct API Change
**Definition**: A design decision modifies the interface or contract of a behavior-bearing component.
**Indicators**: Function signature change, return type change, parameter addition/removal, method rename.
**Risk Profile**: HIGH or MEDIUM. Side effects propagate to all callers immediately.
**Evidence Pattern**: `file:line` shows old signature; ADR specifies new signature.

### Type 2: Indirect Side Effect
**Definition**: A design decision modifies component A, which alters the behavior of component B without directly touching B.
**Indicators**: Shared state mutation, event emission change, configuration value change, hook execution order change.
**Risk Profile**: MEDIUM or LOW. Often discovered only during integration testing.
**Evidence Pattern**: `file:line` shows shared state write in A; `file:line` shows read in B.

### Type 3: Emergent Behavior
**Definition**: Multiple design decisions individually safe but collectively produce an unintended behavior at their intersection.
**Indicators**: Two or more ADRs affect the same component. Neither alone would cause a regression.
**Risk Profile**: HIGH (emergent behaviors are the hardest to detect and are rarely covered by existing tests).
**Evidence Pattern**: Reference 2+ ADRs in the prediction. Document the intersection explicitly.

---

## Regression Risk Formula

Regression Risk Score (RRS) = Likelihood × Impact

**Likelihood** (1-3):
- 1 = Design change is additive only (new code path added, existing paths untouched)
- 2 = Design change modifies existing code path but preserves interface
- 3 = Design change removes or replaces existing code path

**Impact** (1-3):
- 1 = Single component, internal state only
- 2 = Single component, externally visible or multiple internal callers
- 3 = Multiple components, externally visible behavior

**RRS → Risk Level**:
- 1-2: LOW
- 3-4: MEDIUM
- 6-9: HIGH

Use RRS to validate H/M/L classifications. Discrepancies between RRS and initial classification require a justification note.

---

## DPS Template for Behavior Analysts

### COMPLEX Tier (2 Parallel Analysts)

**Context (D11 priority: cognitive focus > token efficiency)**:
```
INCLUDE:
  - research-codebase L1/L2 behavior patterns (file paths + summary, not full content)
  - research-external L2 known issues and quirks for external dependencies in assigned subsystem
  - design-architecture L1 components[] with change scope (assigned subsystem only)
  - Assigned subsystem: {subsystem_name}
EXCLUDE:
  - Other audit dimensions' results (static/relational/impact)
  - Pre-design conversation history
  - Full pipeline state (P2 phase only)
  - Components outside assigned subsystem
Budget: Context field ≤ 30% of teammate effective context.
```

**Task**: "Identify all behavior-bearing components within assigned subsystem `{subsystem_name}`. For each: (1) document current behavior with file:line reference, (2) predict side effects and regressions from design decisions in the architecture doc, (3) classify risk HIGH/MEDIUM/LOW with evidence from both current code and the relevant ADR."

**Scope**: Read-only analysis (analyst agent, no Bash). Subsystem boundary is strict — do not analyze components outside it. No prescriptive recommendations. maxTurns: 25.

**Expected Output**:
- L1 YAML: `total_changes`, `risk_high`, `risk_medium`, `risk_low`, `conflicts`, `predictions[]`
- L2: per-component behavior change table, side effect inventory, regression risk matrix

**Delivery**: Write to `tasks/{team}/p2-audit-behavioral-{subsystem}.md`. SendMessage to Lead: `PASS|changes:{N}|risks:{N}|ref:tasks/{team}/p2-audit-behavioral-{subsystem}.md`

### STANDARD Tier (Single Analyst)

Same task structure as COMPLEX. No subsystem partitioning — analyst covers all behavior-bearing components. maxTurns: 25. Output file: `tasks/{team}/p2-audit-behavioral.md`.

### TRIVIAL Tier

Lead-direct inline execution. Read 1-2 behavior-bearing files. Note obvious risks. No formal DPS or file output required. Embed findings in PT metadata directly.

---

## Edge Case Handling

### No Behavior-Bearing Components Found
- **Cause**: Design changes affect only static content (documentation, config values, types with no runtime effect).
- **Action**: Report `changes: 0, risks: 0`. This is valid — document-only changes have no behavioral risk.
- **Route**: Send to research-coordinator with empty prediction set and explanation note.
- **Signal**: `PASS|changes:0|risks:0|ref:tasks/{team}/p2-audit-behavioral.md`

### Design Scope Too Broad
- **Cause**: Architecture decisions affect many components; analyst cannot cover all within turn budget (maxTurns: 25).
- **Action**: Prioritize HIGH-risk components by applying Risk Factor Scoring first. Report partial coverage with explicit list of uncovered components.
- **Route**: research-coordinator with `partial: true` flag and uncovered component list.
- **Signal**: `PASS|changes:{N}|risks:{N}|partial:true|ref:tasks/{team}/p2-audit-behavioral.md`

### Conflicting Predictions
- **Cause**: Two design decisions create contradictory behavior predictions for the same component (e.g., ADR-1 says component X will gain retry logic; ADR-2 removes the error handler X relies on).
- **Action**: Document both predictions with their respective ADR references. Flag as design conflict requiring resolution before plan phase.
- **Route**: research-coordinator with `conflicts: {N}` flag. Do not attempt to resolve the conflict — that is plan-phase work.
- **Signal**: `FAIL|conflicts:{N}|ref:tasks/{team}/p2-audit-behavioral.md`

---

## Failure Protocols

### Analyst Context Pollution (L2 Respawn trigger)
Signs: analyst output mixes analysis from different subsystems, references components outside its scope, or repeats earlier analysis verbatim.
Action: Kill analyst. Spawn fresh instance with DPS that explicitly narrows scope and re-emphasizes subsystem boundary.
DPS adjustment: Add `CONSTRAINTS: Scope strictly to {subsystem_name}. Ignore any behavior-bearing components outside this subsystem even if they appear in research-codebase findings.`

### Subsystem Scope Conflict (L3 Restructure trigger)
Signs: Two parallel analysts each claim a component belongs to their subsystem, producing duplicate predictions.
Action: Lead restructures subsystem boundaries. Assign the contested component to the analyst whose subsystem has more interaction with it (measured by call graph fan-in from research-codebase findings).
DPS adjustment: Explicitly list contested component in one analyst's INCLUDE and the other's EXCLUDE.

### Quality Gate Failure (post-completion)
Signs: Predictions missing file:line evidence, risk classifications without criteria documentation, or prescriptive recommendations embedded in predictions.
Action: L1 Nudge — SendMessage to analyst with specific gaps listed. Analyst revises affected predictions only (does not re-run full analysis).
