# Evaluation Criteria — Detailed Methodology

> On-demand reference. Contains criteria YAML spec, tier-specific DEFINE behavior, calibration DPS, failure classification tables, and design rationale.

## Full Criteria Specification YAML

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

## Tier-Specific DEFINE Behavior

**TRIVIAL**: Recommend 3-5 criteria based on domain heuristics. Single AskUserQuestion round. Accept user selection, skip golden example. Total: 1-2 AskUserQuestion calls.

**STANDARD**: Recommend 5-7 criteria with detailed anchors. 2-3 AskUserQuestion rounds: criteria selection, weight adjustment, threshold setting. Include golden example if user provides one. Total: 2-4 AskUserQuestion calls.

**COMPLEX**: Same as STANDARD for DEFINE, but prepare for CALIBRATE. Document tradeoff pairs (criteria that may conflict). Explicitly note domain-specific vs universal criteria. Total: 3-4 AskUserQuestion calls for DEFINE alone.

## Calibration DPS for Analyst (COMPLEX only)

- **Context** (D11 priority: cognitive focus > token efficiency):
  - INCLUDE: Current criteria spec YAML (from DEFINE). Research findings from research-codebase and research-external L1 summaries. Pipeline tier.
  - EXCLUDE: Full P2 audit outputs. Pre-design conversation history. Other pipeline phase data.
- **Task**: "Stress-test each criterion against research findings. For each: (1) apply 0-anchor and 10-anchor to a concrete finding, (2) check MECE against other criteria, (3) run sensitivity analysis on H-weight criteria. Report issues found."
- **Constraints**: Read-only analysis. maxTurns: 15. Do not modify criteria — report findings only.
- **Expected Output**: Per-criterion validation result (PASS/ISSUE), MECE matrix, sensitivity flags.
- **Delivery**: Send L1 summary to Lead via SendMessage with: issues found count, MECE status, sensitivity flags.

## Failure Severity Classification

| Failure | Severity | Blocking? | Route |
|---------|----------|-----------|-------|
| User cannot decide after 3 AskUserQuestion rounds | MEDIUM | Yes (temporary) | Pause pipeline, save partial spec to PT |
| MECE violation (fundamental) | HIGH | Yes | Re-invoke DEFINE with MECE gap/overlap data |
| <3 criteria produced | LOW | No | Proceed with minimum set, note in PT |
| Criteria conflict with domain constraints | HIGH | Yes | Escalate to design-architecture |
| No golden example available | LOW | No | Skip calibration anchor test, proceed analytically |
| Calibration analyst exhausted | MEDIUM | No | Lead completes calibration manually with partial findings |

**Pipeline Impact**: Evaluation-criteria failures are soft-blocking. Pipeline can proceed without criteria, but downstream quality degrades. Strongly prefer resolving before advancing to research skills.

## Feedback Loops

| Trigger | Source | Action | Output |
|---------|--------|--------|--------|
| P2 research complete | research-codebase, research-external | Lead re-invokes CALIBRATE phase | Refined criteria spec (version incremented) |
| MECE violation detected | Calibration analyst or Lead | Re-invoke DEFINE with gap/overlap data | Restructured criteria with user approval |
| User requests change | User via AskUserQuestion | Re-invoke DEFINE with change request | Updated criteria with user approval |
| Plan reveals new dimension | plan-* skills | Annotate criteria spec (no structural change after P3) | Annotated criteria |

## Error Recovery Routes

| Failure | Route To | Data Passed |
|---------|----------|-------------|
| User unable to decide | Pipeline pause | Partial criteria spec saved to PT for later resumption |
| MECE violation unresolvable | design-architecture | Constraint conflict requiring architecture-level resolution |
| Calibration analyst exhausted | Lead continues manually | Partial calibration findings from analyst L1 summary |
| Criteria invalid for domain | pre-design-brainstorm | Domain mismatch report for scope renegotiation |
| No criteria after 3 rounds | Pipeline proceeds without | Downstream skills use unstructured qualitative assessment |

## Design Rationale

### Why P2 (Research Domain)?
Evaluation criteria establishment is a research prerequisite. Design produces architecture; research validates it against criteria. Placing criteria at P2 entry ensures "measure before you observe" — analogous to pre-registration in experimental research. This prevents post-hoc rationalization, which every framework surveyed (MCDA, EDD, Rubric Design, Weighted Decision Matrix) warns against.

### Why Lead-Direct?
AskUserQuestion is Lead-only. This skill is fundamentally interactive — user must approve criteria before downstream consumption. The only agent spawn is the calibration analyst in COMPLEX tier, which operates on already-defined criteria and reports back to Lead for user confirmation.

### Why CDST Over Full MCDA/AHP?
Full MCDA with AHP pairwise comparison requires N-squared comparisons — too heavyweight for pipeline integration. CDST preserves MCDA's core value while being practical for LLM-agent workflows:
- H/M/L weights instead of percentage allocation (simpler user decisions)
- Descriptive anchors instead of pure numeric scales (natural language scoring)
- Built-in anti-patterns synthesized from 6 cross-framework analysis
- 4-phase structure maps cleanly to pipeline phases: DEFINE at P2 entry, CALIBRATE mid-P2, SCORE/SYNTHESIZE consumed by P3+

### Why Evolving Criteria with P3 Freeze?
EDD research shows criteria should be adaptive, not static. Research findings in P2 may reveal evaluation dimensions not visible at criteria-setting time. The CALIBRATE phase provides a controlled evolution mechanism: criteria can change during P2 (with user approval), but freeze at P3 entry to prevent post-hoc rationalization.

### Why PT Metadata Transport?
Criteria specs are small (<2KB YAML) and accessed by many downstream skills. PT metadata survives compaction and is queryable via TaskGet. File-based transport would require path conventions, cleanup, and risk stale-file bugs. PT metadata is the natural carrier for cross-phase decision artifacts.
