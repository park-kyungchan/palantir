---
name: research-audit
description: |
  [P3·Research·Audit] Artifact inventory and gap analysis specialist. Systematically inventories all research findings, classifies by category, and identifies coverage gaps between architecture needs and available evidence.

  WHEN: After research-codebase and research-external complete or in parallel. Research findings need consolidation and gap analysis.
  DOMAIN: research (skill 3 of 3). Terminal skill in research domain. Runs after codebase and external research.
  INPUT_FROM: research-codebase (local findings), research-external (external findings).
  OUTPUT_TO: plan-decomposition (consolidated research for task planning), design domain (feedback if critical gaps require architecture revision).

  METHODOLOGY: (1) Inventory all findings from codebase and external research, (2) Classify by architecture decision relevance, (3) Map findings to design assumptions, (4) Identify gaps: assumptions without evidence, (5) Produce coverage metrics and gap report.
  CLOSED_LOOP: Audit → Find gaps → Re-research specific areas → Re-audit (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML coverage matrix with counts, L2 markdown gap analysis narrative, L3 detailed finding inventory.
user-invocable: true
disable-model-invocation: false
---

# Research — Audit

## Output

### L1
```yaml
domain: research
skill: audit
total_findings: 0
coverage_pct: 0
gaps: 0
categories:
  - name: ""
    findings: 0
    coverage: complete|partial|missing
```

### L2
- Coverage matrix (architecture decision to evidence mapping)
- Gap analysis with re-research recommendations
- Consolidated finding inventory
