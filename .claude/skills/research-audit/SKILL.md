---
name: research-audit
description: |
  [P3·Research·Audit] Artifact inventory and gap analysis specialist. Inventories all research findings, classifies by category, identifies coverage gaps between architecture needs and available evidence.

  WHEN: After research-codebase and research-external complete. Findings need consolidation and gap analysis.
  DOMAIN: research (skill 3 of 3). Terminal skill. Runs after codebase and external research.
  INPUT_FROM: research-codebase (local findings), research-external (external findings).
  OUTPUT_TO: plan-decomposition (consolidated research for task planning), design domain (if critical gaps need architecture revision).

  METHODOLOGY: (1) Inventory all findings from codebase and external research, (2) Classify by architecture decision relevance, (3) Map findings to design assumptions, (4) Identify gaps: assumptions without evidence, (5) Produce coverage metrics and gap report. Max 3 iterations.
  OUTPUT_FORMAT: L1 YAML coverage matrix with counts, L2 markdown gap analysis, L3 finding inventory.
user-invocable: true
disable-model-invocation: false
---

# Research — Audit

## Execution Model
- **TRIVIAL**: Lead-direct. Quick merge of codebase + external findings.
- **STANDARD**: Spawn analyst. Systematic gap analysis across all findings.
- **COMPLEX**: Spawn 2 analysts. One for finding consolidation, one for gap analysis.

## Methodology

### 1. Inventory All Findings
Collect outputs from research-codebase and research-external:
- Codebase patterns and anti-patterns
- External dependency validations
- Cross-reference findings (same topic from both sources)

### 2. Classify by Architecture Relevance
Map each finding to architecture decisions:

| Finding | Architecture Decision | Support Level |
|---------|----------------------|--------------|
| {finding} | {ADR-N} | supports/contradicts/neutral |

### 3. Identify Coverage Gaps
For each architecture decision, check:
- Is there codebase evidence? (from research-codebase)
- Is there external validation? (from research-external)
- Are there contradictions between sources?

### 4. Produce Coverage Matrix
| Architecture Decision | Codebase Evidence | External Evidence | Gap? |
|----------------------|-------------------|-------------------|------|
| ADR-1 | check: pattern found | check: docs confirm | No |
| ADR-2 | missing: novel approach | check: docs available | Partial |
| ADR-3 | missing | missing | Critical |

### 5. Recommend Actions for Gaps
- **Critical gaps**: Require re-research or architecture revision
- **Partial gaps**: Acceptable with documented risk
- **No gaps**: Proceed with confidence

## Quality Gate
- Every architecture decision mapped to findings
- Coverage matrix complete with no unchecked decisions
- Critical gaps have actionable recommendations
- Max 3 re-research iterations for gap closure

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
