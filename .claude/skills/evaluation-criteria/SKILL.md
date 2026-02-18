---
name: evaluation-criteria
description: >-
  Establishes weighted evaluation criteria via structured user
  dialogue using CDST 4-phase methodology. Use at P2 entry
  when pipeline requires evaluation, comparison, analysis, or
  selection of alternatives. First P2 skill invoked before
  research-codebase and research-external to set decision
  framework upfront. Anti-pattern guard: prevents post-hoc
  rationalization, equal-weight defaults, and undefined anchors.
  Reads from user requirements, domain context, and pipeline
  tier from PERMANENT task. Produces criteria spec with H/M/L
  weights, 0-10 score anchors, pass/fail threshold, and golden
  example for research-codebase and research-external scoring,
  plan-* decision framework, and execution-review rubric.
  On FAIL (user rejects all criteria or cannot converge),
  Lead re-invokes with refined domain context. DPS needs
  user requirements summary and pipeline tier from PERMANENT
  task. Exclude full pipeline state and technical
  implementation detail.
user-invocable: true
disable-model-invocation: false
---

# Research — Evaluation Criteria

## Execution Model
- **TRIVIAL**: Lead-direct. Quick AskUserQuestion (1-2 questions). 3-5 criteria with default H/M/L weights. Skip calibration.
- **STANDARD**: Lead-direct. Full DEFINE phase via AskUserQuestion (3-4 rounds). 3-7 criteria with explicit weights, anchors, threshold. Calibrate after P2 research returns.
- **COMPLEX**: Lead-direct for DEFINE + spawn analyst for CALIBRATE (stress-test criteria against research findings). Full CDST cycle with iterative refinement.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Methodology

### 1. Extract Decision Objective

From PT metadata and user request, identify: what is being evaluated, decision type (comparison/threshold/ranking), and scope (how many alternatives). Ask via AskUserQuestion if unclear: "What decision does this criteria set need to support?" Skip to Step 2 if the objective is explicit in context.

### 2. DEFINE — Construct Criteria Set

Build 3-7 MECE criteria collaboratively with the user.

**2a. Lead recommends criteria.** For each: **Name** (noun phrase), **Description** (one-line), **Weight** (H/M/L with rationale), **0-anchor** (unambiguous failure), **10-anchor** (unambiguous success).

**2b. User selects via AskUserQuestion.** Options: (1) Use recommended set, (2) Modify weights, (3) Add/remove criteria, (4) Custom criteria.

**2c. Set threshold:** "What's the minimum acceptable score? (Recommended: 70% of maximum)"

**2d. Optional golden example (STANDARD/COMPLEX):** "Can you describe the ideal outcome? This helps calibrate scoring."

> Tier-specific DEFINE behavior, calibration DPS template: read `resources/methodology.md`

### 3. CALIBRATE — Validate Criteria Before Scoring

Run after P2 research returns (STANDARD/COMPLEX only).

**3a. Stress test:** Apply 0-anchor and 10-anchor to a concrete finding for each criterion.
**3b. MECE check:** Overlap detection (duplicate dimensions) + gap detection (uncaptured critical factors).
**3c. Sensitivity analysis:** For each H-weight criterion, test if downgrading to L changes the likely verdict.
**3d. Refinement:** If issues found, ask user: "Calibration found [issue]. Recommended: [change]. Approve?"

> COMPLEX calibration DPS template: read `resources/methodology.md`

### 4. Package Criteria Specification

Produce final criteria spec as structured YAML for PT metadata under `evaluation_criteria` key. Store via task-management skill.

> Full YAML spec template, PT transport protocol: read `resources/methodology.md`

### 5. Embed Downstream Consumer Instructions

Criteria spec is self-contained. Consumers access via `TaskGet [PERMANENT]`:
- **research-codebase/external**: Prioritize patterns relevant to H-weight criteria
- **plan-* skills**: Use as decision framework for implementation choices
- **execution-review**: Use as evaluation rubric
- **audit-* skills**: Weight findings by criterion relevance

## Decision Points

### When to Invoke
- **Always**: Pipeline involves choosing between alternatives or pass/fail evaluation
- **Skip**: Pipeline is purely additive with no evaluation needed
- **Skip**: Criteria already in PT metadata — check `evaluation_criteria` key before invoking

### Criteria Count
- **3**: Minimum. TRIVIAL tier or binary decisions.
- **5**: Sweet spot. Covers most evaluation dimensions without cognitive overload.
- **7**: Maximum recommended. COMPLEX tier with multi-dimensional decisions only.
- **>7**: Anti-pattern. Decompose into sub-evaluations or merge overlapping criteria.

### Weight Distribution
- **Decisive (1H, rest M/L)**: One criterion clearly dominates (e.g., security for auth decisions).
- **Balanced (2-3H, 2-3M, 1-2L)**: Most common. Reflects genuine multi-criteria importance.
- **Flat (all M)**: Anti-pattern. Challenge user: "Are all criteria truly equally important?"

### Calibration Depth
- **TRIVIAL**: Skip entirely. Criteria adequate for simple decisions.
- **STANDARD**: Quick pass: MECE check + one anchor test against a research finding.
- **COMPLEX**: Full analyst spawn. Stress-test all criteria, full sensitivity analysis.

### Criteria Evolution
- **Refineable in P2**: CALIBRATE is the controlled evolution mechanism.
- **Frozen at P3 entry**: No structural changes once plan skills consume criteria.
- **User approval required**: Any change after DEFINE requires explicit AskUserQuestion consent.

### Re-Invocation Detection
- `evaluation_criteria` absent → first invocation, execute full DEFINE.
- `phase=define` → research complete, execute CALIBRATE.
- `phase=calibrate|final` → already done, skip unless user explicitly requests re-evaluation.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| AskUserQuestion timeout or user unavailable | L0 Retry | Re-invoke same AskUserQuestion round |
| User provides partial criteria, criteria incomplete | L1 Nudge | SendMessage with refined options presentation |
| Calibration analyst exhausted turns | L2 Respawn | Kill → fresh analyst with full criteria spec and research findings |
| MECE violation unresolvable, criteria conflict with domain | L3 Restructure | Re-invoke DEFINE with revised objective scope |
| User rejects all criteria after 3 rounds, 3+ L2 failures | L4 Escalate | AskUserQuestion with decision deadlock summary and alternatives |

Failures are **soft-blocking**: pipeline can proceed without criteria but downstream evaluation quality degrades significantly.

> Severity classification, feedback loops, error recovery routes: read `resources/methodology.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

- **Post-hoc rationalization**: Criteria MUST be established BEFORE research findings are available. This is the single most critical sequencing constraint.
- **Equal weights**: Every weight assignment must include a rationale. "All equally important" is the exception — document why explicitly.
- **Missing anchors**: A criterion without 0-anchor and 10-anchor is unusable for consistent scoring. Always define both before proceeding.
- **>7 criteria**: Cognitive overload degrades discrimination quality. Decompose into sub-evaluations with 3-5 criteria each.
- **Frozen-too-early or never-frozen**: Evolve during P2 (calibration). Freeze at P3 entry. Post-P3 changes constitute post-hoc rationalization.
- **Agent-unilateral criteria**: Always use AskUserQuestion for selection. User explicit approval is the quality gate, even when user accepts Lead's recommendation unchanged.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| pre-design-feasibility | Approved requirements, decision scope | L1 YAML: feasibility verdict with requirement list |
| PT metadata | Pipeline tier, architecture decisions | TaskGet: tier, requirements, design outputs |
| User | Domain context, evaluation preferences | AskUserQuestion responses |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| research-codebase | Criteria spec for pattern evaluation focus | PT metadata: `evaluation_criteria` key |
| research-external | Criteria spec for community research focus | PT metadata: `evaluation_criteria` key |
| plan-* skills | Decision framework for planning choices | PT metadata: `evaluation_criteria` key |
| execution-review | Evaluation rubric for implementation review | PT metadata: `evaluation_criteria` key |

> D17 Note: Lead-direct skill, no team channel. Criteria transported via PT metadata (compaction-safe).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`
> Feedback loops and error recovery routes: read `resources/methodology.md`

## Quality Gate
- 3-7 MECE criteria defined with names, descriptions, weights, and both anchors
- No equal-weight default without explicit documented justification
- Pass/fail threshold set with rationale
- Scoring and synthesis instructions embedded in criteria spec
- Criteria established BEFORE any P2 research findings available (anti-post-hoc sequencing verified)
- User explicitly approved criteria set via AskUserQuestion
- STANDARD/COMPLEX: Calibration pass completed after P2 research
- Criteria spec version tracked (1=define, 2+=calibrate)
- PT metadata updated with `evaluation_criteria` key

## Output

### L1
```yaml
domain: research
skill: evaluation-criteria
status: PASS|FAIL
criteria_count: 0
weight_distribution: "H:0 M:0 L:0"
threshold: 0
threshold_percent: 70
max_score: 0
has_golden_example: false
phase: define|calibrate|final
version: 1
pt_signal: "metadata.phase_signals.p2_criteria"
signal_format: "PASS|criteria:{N}|phase:{phase}|ref:tasks/{team}/p2-evaluation-criteria.md"
criteria:
  - name: ""
    weight: H|M|L
    anchor_0: ""
    anchor_10: ""
```

### L2
- Full criteria specification YAML (see `resources/methodology.md` for template)
- Per-criterion design rationale: why chosen, why this weight, tradeoff pairs identified
- Calibration results (STANDARD/COMPLEX): MECE check outcome, sensitivity analysis, anchor validation
- User interaction log: questions asked, options presented, user selections
- Anti-pattern compliance check: post-hoc guard, weight justification, anchor completeness
