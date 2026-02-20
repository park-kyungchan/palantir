# Validate Coordinator — Methodology Reference

> Skill-local resource for validate-coordinator. Contains analyst DPS templates, cross-axis matrix format, L3 output steps, and failure sub-cases. Read when SKILL.md directs here.

## Analyst DPS Template

### Context (D11 Priority: Cognitive Focus > Token Efficiency)

```
PHASE_CONTEXT: P4|P7

INCLUDE:
  - All 6 validate-* axis L1 YAML files (file paths via $ARGUMENTS)
  - LEAD_OVERRIDES block (if provided — apply only after condition verification)

EXCLUDE:
  - Raw execution artifacts (git diffs, source files)
  - Individual file-level annotation detail from axis outputs
  - Plan-domain L2/L3 detail beyond what axis verifiers surfaced
  - Historical rationale for axis-level decisions

Budget: Context field ≤ 25% of subagent effective context (file-path based, not embedded)
```

**Task**: Read all 6 axis L1 outputs. Perform 4 cross-axis consistency checks. Apply LEAD_OVERRIDES if provided (verify conditions first). Compute overall verdict. Produce tiered output (L1 index + L2 summary + 6 L3 per-axis files).

**Delivery**: Ch2 to `tasks/{work_dir}/{PHASE}-vc-*.md` + Ch3 micro-signal to Lead.

### Tier-Specific DPS Variations

| Tier | Mode | maxTurns | Scope |
|------|------|----------|-------|
| TRIVIAL | Lead-direct inline | — | Merge ≤3 axes, skip cross-checks if all PASS |
| STANDARD | Single analyst | 25 | 6-axis merge + all 4 cross-checks + tiered output |
| COMPLEX | Single analyst | 35 | Deep cross-axis analysis + compound pattern detection + comprehensive L3 |

> See `.claude/resources/dps-construction-guide.md` for full DPS v5 field structure.

---

## Cross-Axis Consistency Matrix Format

Build this matrix after reading all 6 axis L1 outputs:

| Check | Axes Involved | P4 Question | P7 Question | Severity | Finding |
|-------|--------------|-------------|-------------|----------|---------|
| Syntactic-Semantic | syntactic × semantic | Orphan files on predicted behavioral paths? | Structure scores vs quality scores misaligned? | — | — |
| Behavioral-Relational | behavioral × relational | Behavioral predictions cover cross-boundary interactions? | CC feasibility gaps align with reference inconsistencies? | — | — |
| Consumer-Impact | consumer × impact | Consumer contract fields cover full propagation scope? | Output contracts match scope drift? | — | — |
| Traceability | all 6 | Findings covered by < 3 axes? | Findings covered by < 3 axes? | — | — |

**Severity assignment for cross-axis findings**:
- HIGH: Compound pattern where two axis failures reinforce each other (e.g., behavioral FAIL + relational FAIL both point to same boundary)
- MEDIUM: Single cross-axis inconsistency without compound pattern
- LOW: Minor misalignment with no delivery impact

**Under-verified finding** (Traceability check): A finding that appears in fewer than 3 axis outputs is considered under-verified. Flag with `status: UNDER_VERIFIED`. These do not auto-FAIL but require annotation in L2.

---

## L3 Per-Axis File Structure

Each L3 file follows this template:

```markdown
# Validate Coordinator — {PHASE} {AXIS} Axis

## Axis Verdict Summary
[From validate-{axis} L1: verdict + key metric counts]

## Cross-Axis Annotations
[Findings FROM OTHER AXES that intersect this axis's scope]
- {Cross-check name}: {finding} — severity: {HIGH|MEDIUM|LOW}

## Routing Recommendation
[P4: specific plan-* skill | P7: execution-infra / execution-review / Lead]
[Evidence: cite specific findings from axis output]
```

---

## LEAD_OVERRIDES Application Protocol

1. Parse the LEAD_OVERRIDES block from DPS.
2. For each override entry: identify the target axis and failure condition.
3. Read the failing axis's output file.
4. Verify: does the actual failure mode match the override condition exactly?
   - Match → reclassify axis from FAIL to CONDITIONAL_PASS. Document rationale in L2.
   - No match → FAIL stands. Report to Lead: "Override condition '{condition}' did not match actual failure mode '{actual}'."
5. Override applies BEFORE overall verdict computation.
6. Override precedence: Lead D-decisions > internal verdict computation.

---

## Failure Sub-Cases (Verbose)

### 1 Axis Missing
Read 5 available axes. Perform only cross-checks that can be completed with 5 axes (some checks may be unavailable if a required axis is missing — note which checks were skipped). Set `status: PARTIAL` in L1. Route to Lead with: which axis is missing, which cross-checks were skipped, overall verdict with caveat.

### 2+ Axes Missing
Cannot perform meaningful cross-axis analysis. Do NOT attempt partial merge. Report FAIL `reason: insufficient_data` with list of missing axes. Route to Lead for upstream re-run.

### All Axes FAIL
Do not route all to one skill. Build ordered fix list:
- P4: prioritize syntactic first (foundation for other analyses), then semantic, behavioral, consumer, relational, impact.
- P7: prioritize behavioral (delivery blocker), then syntactic, semantic, consumer, relational, impact.

### Conflicting Axis Assumptions
If two axis outputs contain contradictory claims about the same files/behavior (e.g., validate-syntactic says "file A is absent" while validate-semantic says "file A behavior predicted"), flag `reason: conflicting_assumptions`. Route to Lead for arbitration before proceeding.
