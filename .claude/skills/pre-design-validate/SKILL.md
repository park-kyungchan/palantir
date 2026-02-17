---
name: pre-design-validate
description: >-
  Validates requirement completeness across 5 dimensions and
  classifies gaps as critical, recommended, or nice-to-have.
  Returns to brainstorm on critical gaps. Use after
  pre-design-brainstorm completes when requirements exist but
  completeness is unverified. Reads from pre-design-brainstorm
  structured requirements with tier estimate. Produces
  completeness verdict for pre-design-feasibility on PASS, or
  gap report back to pre-design-brainstorm on FAIL.
user-invocable: true
disable-model-invocation: false
allowed-tools: "Read Glob Grep Write"
metadata:
  category: pre-design
  tags: [requirement-validation, completeness-check, gap-analysis]
  version: 2.0.0
---

# Pre-Design — Validate

## Execution Model
- **TRIVIAL**: Lead-direct. Quick completeness check against 5-dimension matrix.
- **STANDARD**: Launch analyst (run_in_background, maxTurns: 15). Systematic dimension-by-dimension validation.
- **COMPLEX**: Launch 2 background agents (run_in_background, maxTurns: 15). Split: functional (scope+criteria) vs non-functional (constraints+errors+integration).

## Decision Points

### Tier Assessment for Validation
- **TRIVIAL**: ≤5 requirements, single module scope. Lead checks completeness matrix directly.
- **STANDARD**: 6-12 requirements, 1-2 modules. Launch 1 analyst for systematic dimension validation.
- **COMPLEX**: 13+ requirements, 3+ modules. Launch 2 background analysts: functional (scope+criteria) vs non-functional (constraints+errors+integration).

### Validation Strictness Level
- **Strict** (default): All 5 dimensions must PASS. Any FAIL returns to brainstorm.
- **Relaxed** (after 2 iterations): If 4 of 5 dimensions PASS, proceed with documented gap. Prevents infinite brainstorm-validate loops.
- **Auto-PASS after 3 iterations**: If brainstorm has been re-invoked 3 times, accept current requirements with all gaps documented. Pipeline continues with explicit risk acknowledgment.

### When to Return to Brainstorm vs Proceed
- **Return when**: Critical dimension FAIL (scope or criteria missing). These are foundational — proceeding without them creates cascading failures.
- **Proceed when**: Non-critical dimension FAIL (constraints, error_handling, or integration partially covered). These can be addressed during design phase.
- **Heuristic**: If the FAIL dimension can be inferred from context (e.g., integration points are obvious from scope), add inferred requirements and proceed.

### P0-P1 Execution Context
This skill runs in P0-P1:
- TRIVIAL/STANDARD: Lead with local agents (run_in_background), no Team infrastructure
- COMPLEX: Team infrastructure available (TeamCreate, TaskCreate/Update, SendMessage)
- Validation is READ-ONLY (does not modify requirements, only checks them)
- If re-brainstorm needed: Lead invokes brainstorm, not validate

## Methodology

### 1. Read Brainstorm Output
Load requirement document from pre-design-brainstorm output.
Identify which dimensions were covered during brainstorm.

### 2. Check Completeness Matrix

| Dimension | Check | PASS Condition |
|-----------|-------|---------------|
| Scope | Feature boundaries defined | ≥1 inclusion AND ≥1 exclusion statement |
| Constraints | Limits identified | Technical OR resource limits stated |
| Criteria | Success measurable | ≥1 testable acceptance criterion |
| Error Handling | Failure modes considered | ≥1 error scenario with recovery |
| Integration | Touchpoints mapped | All external dependencies listed |

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: Paste the full requirements document from pre-design-brainstorm L1/L2 output. Include the 5-dimension completeness matrix with PASS conditions from Step 2. If re-validation, include previous L1 showing which dimensions failed.
- **Task**: "Evaluate each requirement against the 5-dimension completeness matrix. For each dimension: extract evidence from requirements, compare against PASS condition, report PASS or FAIL with evidence. For FAIL dimensions: actionable gap description with suggested clarifying questions."
- **Constraints**: Read-only analysis. No file modifications. Use sequential-thinking for nuanced gap reasoning. Do not invent requirements.
- **Expected Output**: L1 YAML completeness matrix with status per dimension and gaps count. L2 markdown per-dimension evidence and gap descriptions.
- **Delivery**: Lead reads background agent output directly (P0-P1 mode, no SendMessage)

#### Step 2 Tier-Specific DPS Variations
**TRIVIAL**: Lead checks completeness matrix directly — no analyst spawn. Quick inline 5-dimension check.
**STANDARD**: Single analyst per DPS above. maxTurns: 15. Full dimension-by-dimension validation.
**COMPLEX**: 2 analysts split: functional (scope+criteria) vs non-functional (constraints+errors+integration). maxTurns: 15 per analyst.

#### Completeness Matrix Scoring Guide

**Scope Dimension:**
- PASS if: >=1 inclusion statement ("this feature will...") AND >=1 exclusion statement ("this will NOT...")
- FAIL if: Only vague scope ("improve the system") or missing exclusions
- Edge case: Single-file changes (TRIVIAL) may have implicit exclusion ("only this file")

**Constraints Dimension:**
- PASS if: At least 1 technical OR resource limit stated (e.g., "max 4 teammates", "must work with Opus 4.6", "<=200K context")
- FAIL if: No limits mentioned (every project has constraints -- missing means not explored)
- Common missing: Context window limits, file count limits, time constraints

**Criteria Dimension:**
- PASS if: >=1 testable acceptance criterion ("when X, then Y", "output matches Z")
- FAIL if: Only subjective criteria ("make it better", "improve quality")
- Good test: Can an analyst verify the criterion without asking the user?

**Error Handling Dimension:**
- PASS if: >=1 error scenario with stated recovery approach
- FAIL if: No failure modes considered at all
- Relaxation: For TRIVIAL tasks, "if it fails, report error" is sufficient

**Integration Dimension:**
- PASS if: All external dependencies listed (other skills, agents, APIs, files)
- FAIL if: Task mentions external components without listing them
- Self-contained tasks: "Integration: none (self-contained)" is valid PASS

### 3. Identify Gaps
For each FAIL dimension:
- State what's missing
- Explain why it matters
- Suggest specific questions to resolve

#### Gap Report Template
For each FAIL dimension:
```
Dimension: {name}
Status: FAIL
Missing: {what specific information is missing}
Impact: {what happens if we proceed without this}
Suggested Question: {what to ask user to resolve this gap}
Priority: {critical | recommended | nice-to-have}
```

#### Gap Priority Classification
| Priority | Definition | Action |
|----------|-----------|--------|
| Critical | Missing info prevents any design | Must return to brainstorm |
| Recommended | Missing info may cause issues in design | Return if within iteration budget |
| Nice-to-have | Missing info is supplementary | Document and proceed |

### 4. Report or Iterate
- If all PASS → forward to pre-design-feasibility
- If any FAIL → report gaps to Lead for re-brainstorm
- Max 3 iterations before proceeding with documented gaps

#### Iteration Tracking
| Iteration | Dimensions Checked | PASS | FAIL | Action |
|-----------|-------------------|------|------|--------|
| 1 | 5 | 3 | 2 (constraints, integration) | Return to brainstorm |
| 2 | 5 (re-check) | 4 | 1 (integration) | Return or proceed? |
| 3 | 5 (final) | 4 | 1 | Proceed with documented gap |

Decision at iteration boundary:
- Iteration 1-2: Return to brainstorm if any critical FAIL
- Iteration 3: Accept current state, document all remaining gaps
- After iteration 3: Auto-PASS (max iterations reached)

## Failure Handling

### Brainstorm Output Missing or Malformed
- **Cause**: pre-design-brainstorm didn't produce structured L1/L2 output
- **Action**: Cannot validate without requirements. Route to Lead to re-invoke brainstorm.
- **Prevention**: Brainstorm skill always produces L1 YAML even on partial completion

### All 5 Dimensions FAIL
- **Cause**: Requirements are extremely sparse (user gave 1-sentence request)
- **Action**: Return to brainstorm with ALL 5 gaps documented. Lead should use deep exploration question strategy.
- **Risk**: If this persists after 3 iterations, the task may be fundamentally unclear -- Lead escalates to user.

### Circular Requirement Detected
- **Cause**: Requirement A depends on requirement B which depends on A
- **Action**: Flag in L2 as contradiction. Route to brainstorm for user clarification on priority.
- **Example**: "Must be simple" + "Must handle every edge case" -- mutually exclusive

### Analyst Disagrees with Lead's Assessment
- **Cause**: COMPLEX-tier analyst finds gaps Lead didn't see
- **Action**: Trust analyst findings (fresh perspective). Add analyst-found gaps to the gap report.
- **Exception**: If analyst flags a dimension as FAIL that Lead considers PASS, include both assessments in L2.

### Validation Takes Too Long (Analyst Exhausted)
- **Cause**: Too many requirements for analyst turns
- **Action**: Partial validation. Report checked dimensions, flag unchecked as `status: SKIP`.
- **Routing**: Proceed with partial validation if critical dimensions (scope, criteria) are checked.

## Anti-Patterns

### DO NOT: Invent Requirements to Fill Gaps
Validation checks EXISTING requirements for completeness. If a dimension is FAIL, report the gap -- don't create fake requirements to make it PASS.

### DO NOT: Validate Twice Without Re-Brainstorming
If validate returns FAIL and routes to brainstorm, the NEXT validate should check the UPDATED requirements, not the old ones. Re-validating unchanged requirements is a wasted iteration.

### DO NOT: Apply COMPLEX Strictness to TRIVIAL Tasks
For TRIVIAL tasks (fix a typo, rename a variable), requiring all 5 dimensions is overkill. Apply relaxed strictness: scope + criteria sufficient, other dimensions optional.

### DO NOT: Block Pipeline After 3 Iterations
After 3 brainstorm-validate iterations, the requirements are as good as they'll get through automated questioning. Accept and proceed -- continued iteration has diminishing returns.

### DO NOT: Treat All Dimensions Equally
Scope and Criteria are critical (must PASS for meaningful pipeline). Constraints, Error Handling, and Integration are important but can be inferred or added during design if missing.

### DO NOT: Validate Without Reading Full Requirements
Analysts must receive the COMPLETE requirements document, not a summary. Validating against a summary misses details that may satisfy dimension checks.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| pre-design-brainstorm | Structured requirements document | L1 YAML: `requirement_count`, `open_questions`, L2: requirements by category |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| pre-design-feasibility | Validated requirements (all PASS) | All 5 dimensions PASS or max iterations reached |
| pre-design-brainstorm | Gap report (FAIL dimensions) | Any critical dimension FAIL, iterations < 3 |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Critical dimension FAIL | pre-design-brainstorm | Gap report with suggested questions |
| Non-critical dimension FAIL (iter 3) | pre-design-feasibility (proceed) | Requirements + documented gaps |
| Brainstorm output missing | Lead (re-invoke brainstorm) | Error details |
| All dimensions FAIL | pre-design-brainstorm (deep exploration) | Full 5-dimension gap report |

## Quality Gate
- Completeness matrix has explicit PASS/FAIL per dimension
- Every FAIL has actionable gap description
- No dimension left unchecked

## Output

### L1
```yaml
domain: pre-design
skill: validate
status: PASS|FAIL
completeness:
  scope: PASS|FAIL
  constraints: PASS|FAIL
  criteria: PASS|FAIL
  error_handling: PASS|FAIL
  integration: PASS|FAIL
gaps: 0
```

### L2
- Completeness matrix with per-dimension evidence
- Gap analysis for FAIL dimensions
- Iteration count and resolution status
