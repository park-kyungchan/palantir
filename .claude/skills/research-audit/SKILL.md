---
name: research-audit
description: |
  [P2·Research·Audit] Artifact inventory and gap analysis specialist. Inventories all research findings, classifies by category, identifies coverage gaps between architecture needs and available evidence.

  WHEN: After research-codebase and research-external complete. Findings need consolidation and gap analysis.
  DOMAIN: research (skill 3 of 3). Terminal skill. Runs after codebase and external research.
  INPUT_FROM: research-codebase (local findings), research-external (external findings).
  OUTPUT_TO: plan-decomposition (consolidated research for task planning), design domain (if critical gaps need architecture revision).

  METHODOLOGY: (1) Inventory all findings from codebase and external research, (2) Classify by architecture decision relevance, (3) Map findings to design assumptions, (4) Identify gaps: assumptions without evidence, (5) Produce coverage metrics and gap report. Max 3 iterations.
  OUTPUT_FORMAT: L1 YAML coverage matrix with counts, L2 markdown gap analysis.
user-invocable: true
disable-model-invocation: false
---

# Research — Audit

## Execution Model
- **TRIVIAL**: Lead-direct. Quick merge of codebase + external findings. Produce simple coverage list against architecture decisions. No analyst spawn needed when findings are sparse and non-contradictory.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic gap analysis across all findings. Cross-reference codebase findings against external findings. For each architecture decision, determine support level and evidence strength.
- **COMPLEX**: Spawn 2 analysts in sequence. Analyst-1 (consolidation): merge, deduplicate, cross-reference all findings into unified inventory. Analyst-2 (gap analysis): take consolidated inventory, map to architecture decisions, classify gaps, recommend actions.

## Methodology

### 1. Inventory All Findings
Collect outputs from research-codebase and research-external:
- Codebase patterns and anti-patterns
- External dependency validations
- Cross-reference findings (same topic from both sources)
- Tag each finding with its source skill (codebase vs external) for traceability

Pre-inventory validation: before proceeding, confirm both upstream outputs exist. If either research-codebase or research-external produced no output, stop and route to Failure Handling (Missing Upstream Research Output).

### 2. Classify by Architecture Relevance
Map each finding to architecture decisions. Use the tier-appropriate approach below.

#### TRIVIAL DPS (Lead-Direct)
Lead performs manually without analyst spawn:
1. Merge finding lists from codebase and external into single inventory
2. For each architecture decision, scan inventory for supporting/contradicting evidence
3. Classify gaps (critical/partial/none) based on evidence presence
4. Produce simple coverage list (no full matrix needed)
5. If any critical gaps found, escalate to STANDARD approach

#### STANDARD DPS (Analyst Spawn)
- **Context**: Paste research-codebase L1 (pattern inventory: names, file locations, relevance) and research-external L1 (dependency validation: names, versions, status). Paste design-architecture L1 (components, ADR list) as the mapping target.
- **Task**: "Inventory all findings from codebase and external research. For each finding, map to architecture decisions with support level (supports/contradicts/neutral). Build coverage matrix: per decision, check codebase evidence + external evidence. Classify gaps as critical (no evidence), partial (one source only), or none. Cross-reference codebase findings against external findings. For each architecture decision, determine support level and evidence strength. Note agreements and disagreements between sources explicitly."
- **Constraints**: Read-only analysis. No file modifications. Cross-reference between input sources. maxTurns:20.
- **Expected Output**: L1 YAML with finding_count, coverage_percent, coverage[] (decision, codebase, external, gap). L2 coverage matrix and gap recommendations.

#### COMPLEX DPS (2 Analysts)
**Analyst-1 (Consolidation):**
- **Context**: Paste ALL research-codebase L2 findings and ALL research-external L2 findings.
- **Task**: "Merge all findings into a unified inventory. Deduplicate findings that appear in both sources. For each finding, note: source(s), file references, confidence level, and whether both sources agree. Produce a consolidated finding list with cross-source annotations."
- **Constraints**: Read-only. Preserve original finding IDs for traceability. Do not classify gaps yet.
- **Expected Output**: Consolidated finding inventory with deduplication notes and cross-source agreement markers.

**Analyst-2 (Gap Analysis):**
- **Context**: Paste Analyst-1 consolidated inventory and design-architecture L1 (ADR list).
- **Task**: "Map every consolidated finding to architecture decisions. For each ADR, score evidence using the Evidence Scoring Rubric (0-3). Classify gaps. Produce full coverage matrix with scores, gap classifications, and recommended actions."
- **Constraints**: Read-only. Use scoring rubric strictly. Flag all score=0 and score=1 decisions.
- **Expected Output**: L1 YAML coverage matrix. L2 detailed gap analysis with per-ADR evidence scores.

#### Finding-to-ADR Mapping Table
| Finding | Architecture Decision | Support Level | Source |
|---------|----------------------|--------------|--------|
| {finding} | {ADR-N} | supports/contradicts/neutral | codebase/external/both |

### 3. Identify Coverage Gaps
For each architecture decision, check:
- Is there codebase evidence? (from research-codebase)
- Is there external validation? (from research-external)
- Are there contradictions between sources?
- What is the combined evidence score? (see Evidence Scoring Rubric below)

When both sources provide evidence for the same decision, note whether they agree or disagree. Agreement increases confidence; disagreement requires resolution before proceeding.

### 4. Produce Coverage Matrix

#### Evidence Scoring Rubric

| Evidence Level | Score | Meaning | Action |
|----------------|-------|---------|--------|
| Both sources confirm | 3 | Strong evidence, high confidence | Proceed with confidence |
| One source confirms, other neutral | 2 | Moderate evidence, acceptable | Proceed, note single-source risk |
| One source confirms, other contradicts | 1 | Conflicting evidence, needs resolution | Trigger contradiction resolution (see Decision Points) |
| Neither source has evidence | 0 | Critical gap, decision unsupported | Block or re-research (see Re-Research Decision) |

#### Coverage Matrix Template
| Architecture Decision | Codebase Evidence | External Evidence | Score | Gap Classification |
|----------------------|-------------------|-------------------|-------|-------------------|
| ADR-1 | FOUND: pattern in src/x.ts | FOUND: docs confirm approach | 3 | None |
| ADR-2 | MISSING: novel approach | FOUND: docs available | 2 | Partial |
| ADR-3 | FOUND: pattern A | FOUND: docs recommend pattern B | 1 | Contradiction |
| ADR-4 | MISSING | MISSING | 0 | Critical |

#### Coverage Metrics
After completing the matrix, calculate:
- **Coverage percentage**: (decisions with score >= 2) / (total decisions) * 100
- **Critical gap count**: decisions with score = 0
- **Contradiction count**: decisions with score = 1
- **Strong evidence count**: decisions with score = 3

These metrics feed directly into the L1 output and determine PASS/FAIL verdict.

### 5. Recommend Actions for Gaps
- **Critical gaps (score=0)**: Require re-research or architecture revision. See Re-Research Decision in Decision Points.
- **Contradictions (score=1)**: Require resolution per Contradiction Resolution in Decision Points. Do not auto-resolve.
- **Partial gaps (score=2)**: Acceptable with documented risk. Note in L2 as single-source findings.
- **No gaps (score=3)**: Proceed with confidence. Both sources agree.

For each recommended action, specify:
1. Which architecture decision is affected
2. What evidence is missing or conflicting
3. Which skill should be re-invoked (research-codebase, research-external, or design-architecture)
4. Expected outcome of the recommended action

## Decision Points

### Tier Classification for Research Audit

| Tier | Finding Count | Scope | Approach |
|------|-------------|-------|----------|
| TRIVIAL | <10 findings from 1-2 sources | Quick merge | Lead consolidates findings inline, produces simple coverage list |
| STANDARD | 10-30 findings across both codebase and external | Full gap analysis | Spawn analyst with architecture decisions and all findings |
| COMPLEX | 30+ findings OR critical gaps detected early | Deep investigation | Spawn 2 analysts: one for consolidation, one for gap analysis |

### Gap Severity Classification

How to classify coverage gaps:
- **Critical**: Architecture decision has NO supporting evidence from either source. Decision is based entirely on assumptions.
- **Partial**: Architecture decision has evidence from one source (codebase OR external) but not both. Decision has single-source risk.
- **None**: Architecture decision has evidence from both codebase AND external sources. Decision is well-supported.

Decision for critical gaps:
```
Critical gap detected for ADR-N
├── Is the decision reversible at low cost?
│   ├── YES → Proceed with documented risk (partial gap acceptable)
│   └── NO → Route back to design domain for architecture revision
│       └── Max 1 revision cycle before escalating to Lead
```

### Contradiction Resolution

When codebase and external findings contradict each other:
- **Codebase says X works, external docs say X is deprecated**: Favor external docs (codebase may be using legacy patterns)
- **Codebase says X is complex, external docs say X is simple**: Favor codebase evidence (local context is more specific)
- **Both sources disagree on approach**: Document both perspectives. Flag for Lead decision. Do not resolve unilaterally.

### Re-Research Decision

When to trigger additional research vs accepting gaps:
- **Trigger re-research**: Critical gap on irreversible decision, OR finding contradicts a core architecture assumption
- **Accept gap**: Partial gap on low-risk decision, OR gap is in an area that will be validated during implementation
- **Max iterations**: 3 re-research cycles total (not per gap). If gaps remain after 3, document as known risks and proceed.

Re-research routing:
- If research-codebase missed it: re-invoke research-codebase with a targeted question referencing the specific ADR and what evidence is needed. Max 1 re-research per audit for codebase.
- If research-external missed it: re-invoke research-external with the specific dependency name, version, and what documentation is needed.
- If both missed it: escalate to design-architecture for potential revision of the ADR itself. The assumption may be unfounded.

### When to Skip Audit

Conditions where audit adds no value and should be bypassed:
- **TRIVIAL tier with 0 findings from both sources**: Both research skills ran but found nothing relevant. Skip audit, report empty coverage matrix with 0% coverage, and let Lead decide whether to proceed or loop back to design.
- **Single-file TRIVIAL pipeline with no external dependencies**: If the pipeline has no external library references and modifies a single file, skip the external coverage check entirely. Only validate codebase evidence.
- **Re-audit after successful re-research**: If a previous audit triggered re-research and the re-research filled all critical gaps, the second audit pass can be abbreviated to verify only the previously-critical decisions rather than re-auditing everything.

## Failure Handling

### Failure Classification Table

| Failure Type | Severity | Blocking? | Route To | Data Passed |
|---|---|---|---|---|
| Missing upstream research output | HIGH | Yes | research-codebase or research-external | Which source missing, which ADRs need evidence |
| Critical gap found (score=0 for core ADR) | HIGH | Yes | design-architecture | ADR details, missing evidence type, what was searched |
| All findings are novel (no codebase patterns) | MEDIUM | No | plan-decomposition with "greenfield" flag | Coverage matrix showing all novel items |
| Partial gap found (score=1-2 for non-core ADR) | MEDIUM | No | plan-strategy with risk annotation | Gap details, risk increase estimate |
| Contradiction found (codebase vs external) | MEDIUM | Conditional | design-architecture if fundamental | Both findings with file:line refs and doc URLs |
| Re-research exhausted (3 iterations, still gaps) | HIGH | No | plan-strategy with residual risk list | Gap list, re-research attempts log |
| Analyst produced incomplete coverage matrix | LOW | No | Self (re-spawn analyst) | Unmapped decisions list, existing partial matrix |

### Detailed Failure Handling

#### Missing Upstream Research Output
- **Cause**: research-codebase or research-external did not produce output (agent failed, no findings)
- **Action**: FAIL with identification of which upstream source is missing. Route back to the missing research skill for re-execution.
- **Never proceed**: with audit when one research source is completely absent. Single-source audit produces unreliable coverage metrics.

#### Critical Gap on Core ADR
- **Cause**: An architecture decision that is central to the system design (e.g., data model, primary framework choice, core integration pattern) has zero evidence from either research source.
- **Action**: FAIL with gap report specifying exactly what evidence was expected and what was searched. Route to design-architecture for potential ADR revision.
- **Escalation**: If this is the second critical gap on the same ADR after re-research, the ADR itself may be unfounded. Recommend Lead assess whether the architecture decision should be withdrawn.

#### All Architecture Decisions Have Critical Gaps
- **Cause**: Research was too narrow or architecture is fundamentally misaligned with codebase reality
- **Action**: FAIL with full gap report. Route to design domain (design-architecture) for architecture revision with research findings as evidence.
- **Note**: This typically indicates a design-research feedback loop is needed (COMPLEX tier behavior).

#### Contradictory Findings Without Resolution
- **Cause**: Codebase evidence directly contradicts external documentation for the same architecture decision
- **Action**: Document contradiction with evidence from both sides. Route to Lead for disposition decision. Do NOT auto-resolve contradictions.
- **Report in L2**: Both findings, their sources, and the specific contradiction point.
- **Conditional blocking**: If the contradiction affects a core ADR (data model, primary integration), this is blocking. If it affects a peripheral decision (logging format, test strategy), it is non-blocking with risk annotation.

#### All Findings Are Novel (Greenfield Scenario)
- **Cause**: research-codebase found no existing patterns matching the architecture decisions. This is expected for greenfield projects or entirely new modules.
- **Action**: Mark all codebase evidence as "novel/absent" in coverage matrix. Pass to plan-decomposition with a "greenfield" flag so task planning does not assume existing patterns to build on.
- **Not a failure**: This is an expected outcome for new projects. Coverage percentage will be lower but this does not block the pipeline.

#### Re-Research Exhausted
- **Cause**: 3 re-research iterations completed but critical gaps remain unfilled
- **Action**: Document all remaining gaps as residual risks. Pass gap list and re-research attempt log to plan-strategy for risk mitigation planning. Do not block pipeline indefinitely.
- **Lead decision**: Lead must explicitly accept residual risk before proceeding past this point.

#### Analyst Produced Incomplete Coverage Matrix
- **Cause**: Analyst did not map all architecture decisions to findings (partial matrix)
- **Action**: Check if unmapped decisions exist in architecture output. If yes: re-spawn analyst with explicit list of unmapped decisions. If analyst was given all decisions: Lead completes remaining mappings inline.

### Pipeline Impact Summary
- **Blocking failures**: Missing upstream research and critical gaps on core ADRs block the pipeline until the upstream skill re-executes or design revises the ADR. The pipeline cannot safely proceed to plan-decomposition without evidence for core decisions.
- **Non-blocking failures**: Partial gaps, greenfield scenarios, and re-research exhaustion are passed forward as risk annotations. They increase risk but do not prevent forward progress.
- **Conditional blocking**: Contradictions are blocking only when they affect core architecture decisions. Peripheral contradictions are annotated and passed forward.

## Anti-Patterns

### DO NOT: Audit Without Architecture Decisions as Input
Research audit maps findings TO architecture decisions. Without the architecture decision list, audit becomes an unstructured dump of findings. Always read design-architecture output first to establish the mapping target.

### DO NOT: Create New Findings During Audit
Audit consolidates and analyzes EXISTING findings from research-codebase and research-external. If audit discovers new information, it should be documented as a gap recommendation, not a new finding. New research goes through the research skills.

### DO NOT: Auto-Close Critical Gaps
Critical gaps (no evidence from either source) require explicit action: re-research or architecture revision. Marking a critical gap as "acceptable" without documented justification masks real risk.

### DO NOT: Merge Contradictory Findings
When codebase and external sources contradict, report BOTH findings separately with their support levels. Merging contradictions into a single finding loses the disagreement signal.

### DO NOT: Skip Coverage Metrics
Every audit must produce a coverage percentage and per-decision status. Even if all decisions are well-covered, the metrics confirm completeness. Skipping metrics makes it impossible to track research quality trends.

### DO NOT: Treat Quantity as Coverage
50 findings does not mean high coverage. Coverage is measured by architecture decision mapping, not finding count. A single finding that validates a critical ADR is more valuable than 20 findings about irrelevant patterns. Always measure coverage as (decisions with evidence / total decisions), never as raw finding count.

### DO NOT: Ignore Cross-Source Validation
When both codebase and external sources agree on a finding, it has higher confidence than a single-source finding. When they disagree, confidence is lower. Always note agreement/disagreement in the coverage matrix. Cross-source agreement is a signal of evidence strength; cross-source disagreement is a signal that further investigation may be warranted.

## Transitions

### Receives From
| Source Skill | Data Expected | Format | Required? |
|-------------|---------------|--------|-----------|
| research-codebase | Local codebase patterns and findings | L1 YAML: pattern inventory with file locations and relevance scores. L2: detailed findings with file:line references. | Yes (blocking if absent) |
| research-external | External documentation and dependency validation | L1 YAML: dependency status, version info, compatibility findings. L2: doc summaries with URLs. | Yes (blocking if absent) |
| design-architecture | Architecture decisions (mapping target) | L1 YAML: components list, ADR identifiers. L2: full ADR descriptions with rationale. | Yes (required for gap mapping) |

Data flow: research-codebase and research-external run in parallel, both feed into research-audit. design-architecture output is read as the mapping target (not modified by audit).

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-decomposition | Consolidated research with coverage metrics and gap annotations | PASS verdict (no critical gaps, or gaps accepted with documentation) |
| design-architecture | Critical gap report requiring architecture revision | FAIL verdict with critical gaps on irreversible decisions |
| plan-strategy | Risk annotations for partial gaps and accepted contradictions | PASS with partial gaps (non-blocking risks to carry forward) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing upstream research | research-codebase or research-external | Which source is missing, what decisions need evidence |
| Critical gap on core ADR | design-architecture | ADR identifier, missing evidence type, search terms used |
| All decisions have critical gaps | design-architecture | Full gap report with evidence status per decision |
| Contradictions on core ADR | design-architecture | Both findings with source refs and contradiction details |
| Contradictions on peripheral ADR | plan-strategy | Both findings, annotated as accepted risk |
| Re-research exhausted | plan-strategy | Residual risk list with gap details and attempt log |
| Incomplete coverage matrix | Self (re-spawn analyst) | Unmapped decisions list, existing partial matrix |

## Quality Gate
1. Every architecture decision mapped to at least one finding (or explicitly marked as gap)
2. Coverage matrix complete with no unchecked decisions -- every ADR has a score (0-3)
3. Critical gaps (score=0) have actionable recommendations specifying which skill to re-invoke
4. Max 3 re-research iterations for gap closure -- iteration count tracked in L2
5. Contradictions (score=1) classified and either resolved or escalated with both-sides evidence
6. Cross-source validation noted for all findings where both sources provide evidence (agreement/disagreement)
7. Coverage percentage calculated: (decisions with score >= 2) / (total decisions) * 100 -- reported in L1

## Output

### L1
```yaml
domain: research
skill: audit
finding_count: 0
coverage_percent: 0
critical_gaps: 0
coverage:
  - decision: ""
    codebase: true|false
    external: true|false
    gap: none|partial|critical
```

### L2
- Finding inventory by architecture decision
- Coverage matrix with gap analysis
- Recommendations for gap closure
