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

## Methodology

### 1. Extract Decision Objective

From PT metadata and user request, identify:
- **What is being evaluated**: Tool selection? Architecture pattern? Plugin value? Code quality?
- **Decision type**: Comparison (pick best from N), threshold (pass/fail against standard), ranking (order by fitness)
- **Scope**: How many alternatives? Single-item or multi-item?

Ask the user via AskUserQuestion if the decision objective is not already clear from pipeline context:
> "What decision does this criteria set need to support? What are we evaluating?"

If the objective is explicit in the user request or PT requirements, skip directly to Step 2.

### 2. DEFINE — Construct Criteria Set

Build 3-7 MECE criteria collaboratively with the user.

**2a. Lead recommends criteria:**
For each proposed criterion, provide:
- **Name**: Noun or noun phrase (not a question or verb)
- **Description**: One-line explaining what this dimension measures
- **Weight**: H (high, x3) / M (medium, x2) / L (low, x1) with rationale
- **0-anchor**: What a score of 0 looks like (unambiguous failure description)
- **10-anchor**: What a score of 10 looks like (unambiguous success description)

**2b. User selects via AskUserQuestion:**
Present recommended criteria as options:
> "Which criteria should we use for evaluating [objective]?"

Options format:
1. "Use recommended set (N criteria)" — Lead's full recommendation
2. "Modify weights" — Keep criteria, adjust importance
3. "Add/remove criteria" — Change the criteria set
4. (Other — user provides custom criteria)

**2c. Set threshold:**
Ask via AskUserQuestion:
> "What's the minimum acceptable score? (Recommended: 70% of maximum)"

**2d. Optional golden example (STANDARD/COMPLEX only):**
> "Can you describe the ideal outcome? This helps calibrate scoring later."

#### Tier-Specific DEFINE Behavior

**TRIVIAL**: Recommend 3-5 criteria based on domain heuristics. Single AskUserQuestion round with all criteria presented. Accept user selection, skip golden example. Total: 1-2 AskUserQuestion calls.

**STANDARD**: Recommend 5-7 criteria with detailed anchors. 2-3 AskUserQuestion rounds: criteria selection, weight adjustment, threshold setting. Include golden example if user provides one. Total: 2-4 AskUserQuestion calls.

**COMPLEX**: Same as STANDARD for DEFINE, but prepare for CALIBRATE phase. Document tradeoff pairs (criteria that may conflict). Explicitly note which criteria are domain-specific vs universal. Total: 3-4 AskUserQuestion calls for DEFINE alone.

### 3. CALIBRATE — Validate Criteria Before Scoring

Run after P2 research skills return initial findings (STANDARD/COMPLEX only). Lead re-invokes this skill's CALIBRATE phase after research-codebase and research-external complete.

**3a. Stress test each criterion:**
- "If criterion X scores 10 for this candidate, is that clearly the right conclusion?"
- "If criterion X scores 0, is that clearly a failure?"
- Apply anchors to a concrete example (golden example or first research finding)

**3b. MECE check:**
- Overlap detection: Do any two criteria measure the same underlying dimension?
- Gap detection: Is there a critical factor not captured by any criterion?

**3c. Sensitivity analysis:**
- For each H-weight criterion: "If we downgrade to L, does the likely verdict change?"
- If yes: The criterion is decisive — validate it deserves H weight
- If no for all H criteria: Weights may be too flat — consider stronger differentiation

**3d. Refinement via AskUserQuestion (if issues found):**
> "Calibration found [issue]. Recommended adjustment: [change]. Approve?"

**COMPLEX calibration DPS** — Spawn analyst with:
- **Context (D11 priority: cognitive focus > token efficiency)**:
  - INCLUDE: Current criteria spec YAML (from DEFINE). Research findings from research-codebase and research-external L1 summaries. Pipeline tier.
  - EXCLUDE: Full P2 audit outputs. Pre-design conversation history. Other pipeline phase data.
- **Task**: "Stress-test each criterion against research findings. For each: (1) apply 0-anchor and 10-anchor to a concrete finding, (2) check MECE against other criteria, (3) run sensitivity analysis on H-weight criteria. Report issues found."
- **Constraints**: Read-only analysis. maxTurns: 15. Do not modify criteria — report findings only.
- **Expected Output**: Per-criterion validation result (PASS/ISSUE), MECE matrix, sensitivity flags.
- **Delivery**: Send L1 summary to Lead via SendMessage. Include: issues found count, MECE status, sensitivity flags.

### 4. Package Criteria Specification

Produce the final criteria spec as structured YAML for PT metadata:

```yaml
evaluation_criteria:
  decision_objective: ""
  decision_type: comparison|threshold|ranking
  criteria:
    - name: ""
      description: ""
      weight: H|M|L
      weight_numeric: 3|2|1
      anchor_0: ""
      anchor_10: ""
  threshold: 0
  threshold_percent: 70
  max_score: 0
  golden_example: ""
  scoring_instructions: |
    Per criterion: score 0-10 against anchors.
    Note evidence (file:line, URL, observation) per score.
    Weighted total = sum(weight_numeric * score).
    Verdict: PASS if weighted_total >= threshold, FAIL otherwise.
    Flag borderline scores (within 1 point of changing verdict).
  synthesis_instructions: |
    After scoring: identify tradeoff pairs (criteria that scored inversely).
    Assess confidence: is verdict sensitive to +/-1 point changes?
    Document: what would flip the verdict? (ADR-style rationale)
  version: 1
  phase: define|calibrate|final
  pt_signal: "metadata.phase_signals.p2_criteria"
  signal_format: "PASS|criteria:{N}|phase:{phase}|ref:tasks/{team}/p2-evaluation-criteria.md"
```

Store in PT metadata under `evaluation_criteria` key via task-management skill.

### 5. Embed Downstream Consumer Instructions

The criteria spec is self-contained. Downstream skills consume it without reading this skill's L2:
- **research-codebase/external**: Use criteria to focus research scope — prioritize patterns relevant to H-weight criteria
- **plan-* skills**: Use criteria as decision framework when choosing between implementation alternatives
- **execution-review**: Use criteria as evaluation rubric for implementation quality assessment
- **audit-* skills**: Use criteria to weight findings by criterion relevance

Transport mechanism: PT metadata `evaluation_criteria` key. All downstream skills access via `TaskGet [PERMANENT]`.

## Decision Points

### When to Invoke This Skill
- **Always invoke**: Pipeline involves choosing between alternatives (tools, patterns, architectures, approaches)
- **Always invoke**: Pipeline involves pass/fail evaluation against quality standards
- **Skip**: Pipeline is purely additive (create new feature with no evaluation needed) and user has not requested criteria
- **Skip**: Criteria already established from a previous pipeline run (check PT metadata for existing `evaluation_criteria`)

### Criteria Count Selection
- **3 criteria**: Minimum for meaningful evaluation. Use for TRIVIAL tier or binary decisions.
- **5 criteria**: Sweet spot. Covers most evaluation dimensions without cognitive overload.
- **7 criteria**: Maximum recommended. Only for COMPLEX tier with multi-dimensional decisions.
- **>7 criteria**: Anti-pattern. Decompose into sub-evaluations or merge overlapping criteria.

### Weight Distribution Strategy
- **Decisive (1H, rest M/L)**: When one criterion clearly dominates the decision (e.g., security for auth decisions)
- **Balanced (2-3H, 2-3M, 1-2L)**: Most common. Reflects genuine multi-criteria importance.
- **Flat (all M)**: Anti-pattern unless genuinely justified. Challenge the user: "Are all criteria truly equally important?"

### Calibration Depth
- **TRIVIAL**: Skip calibration entirely. Criteria are adequate for simple decisions.
- **STANDARD**: Quick calibration after P2 research. Single pass: MECE check, test one anchor against a finding.
- **COMPLEX**: Full calibration with analyst spawn. Stress-test all criteria, full sensitivity analysis.

### Criteria Evolution Policy
- **Refineable in P2**: Research findings may reveal new dimensions or invalidate criteria. Calibration is the controlled mechanism.
- **Frozen at P3 entry**: Once plan skills consume criteria, no further changes allowed. This prevents post-hoc rationalization.
- **User approval required**: Any criteria change after initial DEFINE requires explicit user consent via AskUserQuestion.

### Re-Invocation Detection
Before executing, Lead checks PT metadata for existing `evaluation_criteria`:
- **Key absent**: First invocation. Execute full DEFINE flow.
- **Key present, phase=define**: Research complete, execute CALIBRATE flow.
- **Key present, phase=calibrate or final**: Already calibrated. Skip unless user explicitly requests re-evaluation.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| AskUserQuestion timeout or user unavailable | L0 Retry | Re-invoke same AskUserQuestion round |
| User provides partial criteria, criteria incomplete | L1 Nudge | SendMessage to user with refined options presentation |
| Calibration analyst exhausted turns | L2 Respawn | Kill → fresh analyst with full criteria spec and research findings |
| MECE violation unresolvable, criteria conflict with domain | L3 Restructure | Re-invoke DEFINE with revised objective scope |
| User rejects all criteria after 3 rounds, 3+ L2 failures | L4 Escalate | AskUserQuestion with decision deadlock summary and alternatives |

### Severity Classification

| Failure | Severity | Blocking? | Route |
|---------|----------|-----------|-------|
| User cannot decide on criteria after 3 AskUserQuestion rounds | MEDIUM | Yes (temporary) | Pause pipeline, save partial spec to PT |
| Calibration reveals fundamental MECE violation | HIGH | Yes | Re-invoke DEFINE with MECE gap/overlap data |
| <3 criteria produced | LOW | No | Proceed with minimum set, note limitation in PT |
| Criteria conflict with domain constraints | HIGH | Yes | Escalate to design-architecture for constraint review |
| No golden example available | LOW | No | Skip calibration anchor test, proceed with analytical calibration |
| Calibration analyst exhausted (maxTurns) | MEDIUM | No | Lead completes calibration manually with partial findings |

### Pipeline Impact
Evaluation-criteria failures are **soft-blocking**: the pipeline can technically proceed without criteria, but downstream evaluation quality degrades significantly. Lead should strongly prefer resolving criteria issues before advancing to research skills. If criteria are absent, downstream skills fall back to unstructured qualitative assessment (acceptable for TRIVIAL, problematic for STANDARD/COMPLEX).

## Anti-Patterns

### DO NOT: Set Criteria After Seeing Results (Post-Hoc Rationalization)
Criteria MUST be established BEFORE research-codebase and research-external produce findings. Setting criteria after seeing results enables unconscious bias toward confirming pre-existing preferences. The entire value of this skill depends on criteria-before-analysis sequencing. This is the single most important anti-pattern to prevent.

### DO NOT: Default to Equal Weights
Equal weights (all M or all H) indicate insufficient analysis of criterion importance. Every weight assignment must include a rationale. If genuinely all criteria are equally important, document why explicitly — this is the exception, not the default. Challenge the user when they accept equal weights without reasoning.

### DO NOT: Skip Score Anchors
A criterion without 0-anchor and 10-anchor definitions is unusable for consistent scoring. "Rate security 0-10" means nothing without defining what 0 (complete exposure, no authentication) and 10 (zero known vulnerabilities, defense in depth, audit trail) look like. Always define both anchors before proceeding.

### DO NOT: Use More Than 7 Criteria
Cognitive load research (MCDA literature) shows >7 criteria degrades discrimination quality. The temptation to add "one more criterion" leads to criteria bloat where every score converges toward the mean. If >7 dimensions seem necessary, decompose into sub-evaluations each with 3-5 criteria.

### DO NOT: Freeze Criteria Permanently
Criteria should evolve during P2 (calibration) but freeze before P3 (plan). Never-revised criteria miss insights gained from research. However, criteria that change after scoring begins constitute post-hoc rationalization (see anti-pattern 1). The freeze point is P3 entry — explicit and non-negotiable.

### DO NOT: Let Agent Set Criteria Without User
This skill is fundamentally user-collaborative. The agent recommends with reasoning and the user decides. An agent setting criteria unilaterally violates the decision-support pattern specified in user requirements. Always use AskUserQuestion for criteria selection, even if the user accepts the recommendation unchanged. The user's explicit approval is the quality gate.

## Phase-Aware Execution

This skill is **Lead-direct in all tiers** because it requires AskUserQuestion (user interaction). Agents cannot interact with users. Agent Teams coordination applies only for the COMPLEX calibration analyst:
- **Communication**: Lead holds criteria spec in context. Calibration analyst receives criteria + research findings via DPS.
- **Task tracking**: Update PT metadata with criteria spec at DEFINE and CALIBRATE milestones.
- **Re-invocation**: Lead re-invokes CALIBRATE after P2 research wave completes. Not a separate task — a continuation of the same skill with phase advancement.

## Transitions

### Normal Flow
| Source/Target | Skill | Data | Format |
|---------------|-------|------|--------|
| Receives from | pre-design-feasibility | Approved requirements, decision scope | L1 YAML: feasibility verdict with requirement list |
| Receives from | PT metadata | Pipeline tier, architecture decisions | TaskGet: tier, requirements, design outputs |
| Receives from | User | Domain context, evaluation preferences | AskUserQuestion responses |
| Sends to | research-codebase | Criteria spec for pattern evaluation focus | PT metadata: `evaluation_criteria` key |
| Sends to | research-external | Criteria spec for community research focus | PT metadata: `evaluation_criteria` key |
| Sends to | plan-* skills | Decision framework for planning choices | PT metadata: `evaluation_criteria` key |
| Sends to | execution-review | Evaluation rubric for implementation review | PT metadata: `evaluation_criteria` key |

### Feedback Loops
| Trigger | Source | Action | Output |
|---------|--------|--------|--------|
| P2 research complete | research-codebase, research-external | Lead re-invokes CALIBRATE phase | Refined criteria spec (version incremented) |
| MECE violation detected | Calibration analyst or Lead analysis | Re-invoke DEFINE with gap/overlap data | Restructured criteria set with user approval |
| User requests criteria change | User via AskUserQuestion | Re-invoke DEFINE with change request | Updated criteria spec with user approval |
| Plan phase reveals new dimension | plan-* skills | Lead evaluates: add criterion or note limitation | Annotated criteria spec (frozen — no structural changes after P3) |

### Error Recovery
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| User unable to decide | Pipeline pause | Partial criteria spec saved to PT metadata for later resumption |
| MECE violation unresolvable | design-architecture | Constraint conflict description requiring architecture-level resolution |
| Calibration analyst exhausted | Lead continues manually | Partial calibration findings from analyst L1 summary |
| Criteria invalid for domain | pre-design-brainstorm | Domain mismatch report for scope renegotiation |
| No criteria produced after 3 rounds | Pipeline proceeds without | Downstream skills use unstructured qualitative assessment |

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
- All downstream consumers can read criteria spec from PT without additional context

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
- Full criteria specification YAML (as defined in Methodology Step 4)
- Per-criterion design rationale: why this criterion was chosen, why this weight
- Tradeoff pairs identified: which criteria tend to score inversely
- Calibration results (STANDARD/COMPLEX): MECE check outcome, sensitivity analysis, anchor validation
- User interaction log: questions asked, options presented, user selections
- Downstream consumer instructions: how research/plan/execution skills should use the criteria
- Anti-pattern compliance check: post-hoc guard, weight justification, anchor completeness

---

## Design Rationale

### Why P2 (Research Domain)?
Evaluation criteria establishment is a **research prerequisite**, not a design artifact. Design produces architecture; research validates it against criteria. Criteria define *how* validation is measured. Placing criteria at P2 entry ensures the "measure before you observe" principle — analogous to pre-registration in experimental research. This prevents post-hoc rationalization, which every framework surveyed (MCDA, EDD, Rubric Design, Weighted Decision Matrix) explicitly warns against.

### Why Lead-Direct (Not Agent-Spawned)?
AskUserQuestion is a Lead-only capability. This skill is fundamentally interactive — the user must approve criteria before downstream consumption. Making it Lead-direct also keeps the criteria spec in Lead's context for efficient PT metadata updates without file I/O round-trips. The only agent spawn is the calibration analyst in COMPLEX tier, which operates on the already-defined criteria and reports back to Lead for user confirmation.

### Why CDST Over Full MCDA/AHP?
Full MCDA with AHP pairwise comparison requires N-squared comparisons — too heavyweight for pipeline integration. CDST preserves MCDA's core value (explicit weights, calibrated anchors, sensitivity testing) while being practical for LLM-agent workflows:
- H/M/L weights instead of percentage allocation (simpler user decisions via AskUserQuestion)
- Descriptive anchors instead of pure numeric scales (natural language scoring by agents)
- Built-in anti-patterns synthesized from 6 cross-framework analysis (MCDA, ATAM, EDD, Rubric, Decision Matrix, community patterns)
- 4-phase structure maps cleanly to pipeline phases: DEFINE at P2 entry, CALIBRATE mid-P2, SCORE/SYNTHESIZE consumed by P3+

### Why Evolving Criteria with P3 Freeze?
EDD (Evaluation-Driven Development) research shows criteria should be adaptive, not static. Research findings in P2 may reveal evaluation dimensions not visible at criteria-setting time. The CALIBRATE phase provides a controlled evolution mechanism: criteria can change during P2 (with user approval), but freeze at P3 entry to prevent post-hoc rationalization. This balances the tension between "criteria before analysis" (anti-pattern 1) and "criteria informed by evidence" (anti-pattern 5: frozen criteria).

### Why Embedded Instructions in Criteria Spec?
Downstream skills (research-codebase, plan-*, execution-review) need to know HOW to use criteria, not just WHAT criteria exist. Embedding `scoring_instructions` and `synthesis_instructions` in the spec makes it self-contained — any consumer can apply the criteria by reading PT metadata alone, without loading this skill's L2 body. This follows the DPS self-containment principle from CLAUDE.md section 5.

### Why PT Metadata Transport (Not File I/O)?
Criteria specifications are small (typically <2KB YAML) and accessed by many downstream skills across phases. PT metadata is the pipeline's single source of truth, survives compaction, and is queryable via TaskGet. File-based transport would require path conventions, cleanup, and risk stale-file bugs. PT metadata is the natural carrier for cross-phase decision artifacts.
