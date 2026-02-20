# Verify Quality — Detailed Methodology

> On-demand reference. Contains quality rubrics, scoring templates, assessment format, and benchmark examples.
> Loaded by: verify-quality SKILL.md (Stage 3 progressive disclosure).

---

## WHEN Condition Specificity — Detail

### Domain-Specific WHEN Examples

| Domain | Good WHEN Example | Bad WHEN Example |
|--------|-------------------|------------------|
| execution | "After orchestrate-coordinator PASS. Validated assignments ready." | "When code needs implementing" |
| verify | "After verify-structural-content PASS. Second of 4 stages." | "When verification needed" |
| homeostasis | "After pipeline completion, periodic health check." | "When infrastructure changes" |
| pre-design | "User invokes /brainstorm with topic. First pipeline phase." | "When brainstorming" |
| design | "After feasibility PASS. Requirements validated." | "When design is needed" |
| research | "After design phase PASS. Architecture decisions finalized." | "When research required" |
| plan | "After research-audit PASS. Full codebase understanding." | "When planning" |

### WHEN Disambiguation Decision Tree

> "Can Lead distinguish this skill from every other skill in the same domain based solely on the WHEN clause?"

```
WHEN clause present?
├── NO → Score = 0
└── YES → Names upstream skill or exact trigger?
    ├── YES → Names phase position (e.g., "third of 5")?
    │   ├── YES → Score = 100
    │   └── NO → Score = 75
    └── NO → References specific phase?
        ├── YES → Score = 50
        └── NO → Vague/generic?
            ├── YES → Score = 25
            └── NO (missing context) → Score = 0
```

If disambiguation test fails (answer is NO) → score capped at 50 regardless of other factors.

---

## DPS Construction for Analysts (STANDARD/COMPLEX)

For STANDARD/COMPLEX tiers, construct the delegation prompt with:
- **Context** (D11 priority: cognitive focus > token efficiency):
  - INCLUDE: All skill description texts (paste each). Scoring rubric (Specificity/Concreteness/Completeness 0-100). Routing failure context if investigating. File paths within this analyst's ownership boundary.
  - EXCLUDE: L2 body content (not part of routing scoring). Cross-skill consistency data (verify-consistency domain). Other subagents' task details. Full pipeline state beyond current file set.
  - Budget: Context field ≤ 30% of analyst effective context.
- **Task**: "Score each skill across 4 dimensions: WHEN specificity, METHODOLOGY concreteness, OUTPUT FORMAT completeness, description utilization (>80%). Produce combined score per skill. Rank all skills. Identify bottom 5 for priority improvement."
- **Constraints**: Read-only. No modifications. Score objectively using the rubric.
- **Expected Output**: L1 YAML with avg_score, findings[] (file, score, issues). L2 quality rankings and improvement suggestions.
- **Delivery**: Upon completion, send L1 summary to Lead via file-based signal format: `"{STATUS}|files:{total_files}|avg_score:{avg_score}|ref:tasks/{work_dir}/p7-quality.md"`. L2 detail stays in agent context.

---

## METHODOLOGY Concreteness — Detail

### Concreteness Checklist

- [ ] Steps are numbered (1), (2), (3)
- [ ] Each step names a specific action (Read, Spawn, Grep, not "analyze")
- [ ] Agent-spawning steps include DPS structure (Context/Task/Constraints/Expected Output)
- [ ] Tool names referenced where applicable (Glob, Grep, Read, Edit, Write)
- [ ] Tier-specific variations described (TRIVIAL/STANDARD/COMPLEX)

### Concreteness Decision Tree

```
Steps numbered?
├── NO → Score ≤ 25
└── YES → Each step has specific action verb?
    ├── NO → Score = 50
    └── YES → Tool/agent names referenced?
        ├── NO → Score = 75
        └── YES → DPS templates for spawn steps?
            ├── NO → Score = 85
            └── YES → Tier variations described?
                ├── NO → Score = 90
                └── YES → Score = 100
```

---

## Output Format Completeness — Detail

### L1 Output Minimum Requirements

```yaml
# Required fields (all skills)
domain: <skill_domain>
skill: <skill_name>
status: PASS|FAIL

# Recommended fields (context-dependent)
total_files: 0
findings: []
```

### L2 Output Requirements
- Markdown format described (bullet points, tables, or structured report)
- For skills that produce files: output file path must be specified
- For skills that produce data: field names and types documented

### Completeness Scoring Table

| Present | Score |
|---------|-------|
| L1 YAML with all required fields + L2 markdown format described | 100 |
| L1 YAML with required fields only | 75 |
| Partial L1 (missing status or domain) | 50 |
| Output mentioned but no template | 25 |
| No output section | 0 |

---

## Utilization Measurement — Detail

### Cross-Reference with verify-structural-content

Quality adds semantic assessment on top of structural-content's combined assessment. verify-structural-content checks char count, key presence, and structural integrity; verify-quality checks whether those chars carry routing intelligence.

### Utilization vs Quality Trade-off

- A 700-char description (68%) with all 5 orchestration keys and high specificity scores HIGHER than a 1020-char (99%) description with vague, padded content
- Utilization score is weighted at 20% precisely because length alone does not indicate quality

---

## Quality Rankings — Detail

### Improvement Priority Matrix

| Score Range | Priority | Action |
|-------------|----------|--------|
| 0-50 | CRITICAL | Immediate rewrite via execution-infra |
| 51-70 | HIGH | Schedule rewrite in next maintenance cycle |
| 71-85 | MEDIUM | Note for incremental improvement |
| 86-100 | LOW | No action needed |

### Bottom-5 Report Format

```yaml
bottom_5:
  - skill: <name>
    score: <combined>
    weakest_dimension: <WHEN|METHODOLOGY|OUTPUT|UTILIZATION>
    suggested_fix: "<specific improvement instruction>"
```

---

## Full L1 Output Template (PASS)

```yaml
domain: verify
skill: quality
status: PASS|FAIL
pt_signal: "metadata.phase_signals.p7_quality"
signal_format: "{STATUS}|files:{total_files}|avg_score:{avg_score}|ref:tasks/{work_dir}/p7-quality.md"
total_files: 0
avg_score: 0
dimension_averages:
  when_specificity: 0
  methodology_concreteness: 0
  output_completeness: 0
  utilization: 0
findings:
  - file: ""
    score: 0
    when_score: 0
    methodology_score: 0
    output_score: 0
    utilization_score: 0
    issues: []
bottom_5:
  - skill: ""
    score: 0
    weakest_dimension: ""
    suggested_fix: ""
```

---

## FAIL Output Structure

```yaml
domain: verify
skill: quality
status: FAIL
total_files: 0
avg_score: 0
fail_reason: "<specific threshold violated>"
blocking_items:
  - file: "<skill path>"
    score: 0
    dimension: "<weakest dimension>"
    current_value: "<current text>"
    suggested_fix: "<improvement instruction>"
route_to: execution-infra
```
