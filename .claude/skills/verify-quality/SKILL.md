---
name: verify-quality
description: |
  [P7·Verify·Quality] Audits routing effectiveness via WHEN specificity, INPUT_FROM/OUTPUT_TO clarity, and description utilization. Scores skills 0-100, identifies bottom-5. Third of 4 sequential verify stages.

  WHEN: After verify-consistency PASS. Also after routing failures requiring investigation.
  DOMAIN: verify (skill 3 of 4, sequential).
  INPUT_FROM: verify-consistency (relationship integrity confirmed).
  OUTPUT_TO: verify-cc-feasibility (PASS) | execution-infra (FAIL). Quality scores per file.

  METHODOLOGY: (1) Score WHEN specificity, (2) Score INPUT_FROM/OUTPUT_TO clarity, (3) Score description utilization, (4) Score canonical structure compliance, (5) Identify bottom-5 for improvement.
  OUTPUT_FORMAT: L1 YAML (quality score 0-100 per file with dimension breakdown), L2 quality report.
user-invocable: true
disable-model-invocation: false
---

# Verify — Quality

## Execution Model
- **TRIVIAL**: Lead-direct. Quick quality check on 1-3 files. Spot check only.
- **STANDARD**: Spawn analyst (maxTurns: 25). Systematic routing quality assessment on 4-15 files. Full scoring audit.
- **COMPLEX**: Spawn 2 analysts (maxTurns: 30 each). One for WHEN/METHODOLOGY quality, one for output format quality. 16+ files or post-routing-failure investigation.

## Decision Points

### Tier Classification for Quality Verification

| Tier | File Count | Scope | Approach |
|------|-----------|-------|----------|
| TRIVIAL | 1-3 files | Spot check | Lead reads descriptions, applies rubric inline |
| STANDARD | 4-15 files | Full scoring audit | Spawn analyst with complete rubric and all descriptions |
| COMPLEX | 16+ files OR routing failure | Deep investigation | Spawn 2 analysts: WHEN/METHODOLOGY + OUTPUT/utilization |

### Scoring Rubric

| Dimension | Weight | 100 | 75 | 50 | 25 | 0 |
|-----------|--------|-----|----|----|----|----|
| WHEN Specificity | 30% | Exact upstream skill + trigger event | Named phase + condition | Generic phase | Vague "when needed" | Missing |
| METHODOLOGY Concreteness | 30% | Numbered steps + tool/agent names + DPS | Numbered steps + actions | Numbered steps only | Generic actions | Missing |
| OUTPUT Completeness | 20% | L1 YAML + L2 markdown templates | L1 template only | Partial template | Mentioned but no template | Missing |
| Utilization | 20% | >90% of 1024 chars | 80-90% | 70-80% | 60-70% | <60% |

**Weighted formula**: `score = (WHEN * 0.30) + (METHODOLOGY * 0.30) + (OUTPUT * 0.20) + (UTILIZATION * 0.20)`

### Priority File Selection

When reviewing many files, prioritize in this order:
1. Recently modified skills (highest risk of regression)
2. Skills involved in recent routing failures (direct evidence of quality issues)
3. Skills with known low scores from previous runs (persistent quality debt)
4. Newly created skills (no prior quality baseline)

### Routing Failure Investigation Mode

When invoked after a routing failure:
1. Identify the failed skill and the skill that should have been selected
2. Compare WHEN conditions of both skills side-by-side
3. Check for ambiguous overlap in WHEN clauses within the same domain
4. Focus scoring on WHEN Specificity dimension (weight increases to 50%)
5. Produce disambiguation recommendations in L2 output

### Skip Conditions

Quality verification can be skipped when:
- Only L2 body changes made (no frontmatter/description edits)
- Changes are documentation-only (no `.claude/skills/` files touched)
- Previous quality run scored >90 average and no new skills added since

## Methodology

### 1. Assess WHEN Condition Specificity

For each skill description:
- Read the WHEN clause
- Check it specifies a concrete trigger (not vague "when needed")
- Good: "After design-architecture produces component structure"
- Bad: "When the user wants to design"
- Score specificity 0-100

**Domain-Specific WHEN Examples:**

| Domain | Good WHEN Example | Bad WHEN Example |
|--------|-------------------|------------------|
| execution | "After orchestration-verify PASS. Validated assignments ready." | "When code needs implementing" |
| verify | "After verify-structural-content PASS. Second of 4 stages." | "When verification needed" |
| homeostasis | "After pipeline completion, periodic health check." | "When infrastructure changes" |
| pre-design | "User invokes /brainstorm with topic. First pipeline phase." | "When brainstorming" |
| design | "After feasibility PASS. Requirements validated." | "When design is needed" |
| research | "After design phase PASS. Architecture decisions finalized." | "When research required" |
| plan | "After research-audit PASS. Full codebase understanding." | "When planning" |

**WHEN Disambiguation Test:**

> "Can Lead distinguish this skill from every other skill in the same domain based solely on the WHEN clause?"

Decision tree:
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

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: All skill descriptions (paste each description text). Include scoring rubric: Specificity (0-100): 100=exact trigger with upstream skill name, 50=vague condition, 0=missing. Concreteness (0-100): 100=numbered steps with tool/agent refs, 50=generic steps, 0=no methodology. Completeness (0-100): 100=L1+L2 defined, 50=partial, 0=missing.
- **Task**: "Score each skill across 4 dimensions: WHEN specificity, METHODOLOGY concreteness, OUTPUT FORMAT completeness, description utilization (>80%). Produce combined score per skill. Rank all skills. Identify bottom 5 for priority improvement."
- **Constraints**: Read-only. No modifications. Score objectively using the rubric.
- **Expected Output**: L1 YAML with avg_score, findings[] (file, score, issues). L2 quality rankings and improvement suggestions.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

### 2. Evaluate METHODOLOGY Concreteness

For each skill description:
- Check steps are numbered (1), (2), (3)...
- Verify each step references a concrete tool or action
- Good: "Spawn analyst for design compliance check"
- Bad: "Analyze the results"
- Score concreteness 0-100

**Concreteness Checklist:**

- [ ] Steps are numbered (1), (2), (3)
- [ ] Each step names a specific action (Read, Spawn, Grep, not "analyze")
- [ ] Agent-spawning steps include DPS structure (Context/Task/Constraints/Expected Output)
- [ ] Tool names referenced where applicable (Glob, Grep, Read, Edit, Write)
- [ ] Tier-specific variations described (TRIVIAL/STANDARD/COMPLEX)

**Concreteness Decision Tree:**
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

### 3. Check Output Format Completeness

For each skill:
- L1 YAML template defined with domain, skill, status
- L2 markdown description defined
- Output section present in body
- Score completeness 0-100

**L1 Output Minimum Requirements:**

```yaml
# Required fields (all skills)
domain: <skill_domain>
skill: <skill_name>
status: PASS|FAIL

# Recommended fields (context-dependent)
total_files: 0
findings: []
```

**L2 Output Requirements:**
- Markdown format described (bullet points, tables, or structured report)
- For skills that produce files: output file path must be specified
- For skills that produce data: field names and types documented

**Completeness Scoring:**

| Present | Score |
|---------|-------|
| L1 YAML with all required fields + L2 markdown format described | 100 |
| L1 YAML with required fields only | 75 |
| Partial L1 (missing status or domain) | 50 |
| Output mentioned but no template | 25 |
| No output section | 0 |

### 4. Measure Description Utilization

For each skill description:
- Calculate char count / 1024
- Target: >80% utilization (aligned with verify-structural-content threshold)
- Flag descriptions below threshold with improvement suggestions

**Cross-Reference with verify-structural-content**: Quality adds semantic assessment on top of structural-content's combined assessment. verify-structural-content checks char count, key presence, and structural integrity; verify-quality checks whether those chars carry routing intelligence.

**Utilization vs Quality Trade-off:**
- A 700-char description (68%) with all 5 orchestration keys and high specificity scores HIGHER than a 1020-char (99%) description with vague, padded content
- Utilization score is weighted at 20% precisely because length alone does not indicate quality

### 5. Generate Quality Rankings

Produce quality score per file:
- Combined score = (specificity * 0.30) + (concreteness * 0.30) + (completeness * 0.20) + (utilization * 0.20)
- Rank all skills by combined score
- Identify bottom 5 for priority improvement

**Improvement Priority Matrix:**

| Score Range | Priority | Action |
|-------------|----------|--------|
| 0-50 | CRITICAL | Immediate rewrite via execution-infra |
| 51-70 | HIGH | Schedule rewrite in next maintenance cycle |
| 71-85 | MEDIUM | Note for incremental improvement |
| 86-100 | LOW | No action needed |

**Bottom-5 Report Format:**

```yaml
bottom_5:
  - skill: <name>
    score: <combined>
    weakest_dimension: <WHEN|METHODOLOGY|OUTPUT|UTILIZATION>
    suggested_fix: "<specific improvement instruction>"
```

## Failure Handling

### FAIL Conditions

| Condition | Threshold | Severity | Route To |
|-----------|-----------|----------|----------|
| Average score below threshold | avg < 75 | FAIL | execution-infra with bottom-5 list |
| WHEN specificity critically low | any skill WHEN < 50 | FAIL | execution-infra with rewrite target |
| Missing numbered METHODOLOGY | unnumbered steps found | FAIL | execution-infra with skill path |
| Missing L1/L2 output format | no output template | FAIL | execution-infra with skill path |

### Pipeline Impact

- **Semi-blocking**: Quality failures do not halt the pipeline entirely
- **CRITICAL scores (<50)**: Blocking. Must be resolved before pipeline proceeds past P7.
- **HIGH scores (51-70)**: Warnings that accumulate. Three or more HIGH warnings trigger a blocking FAIL.
- **MEDIUM/LOW scores (71+)**: Logged for future maintenance. Non-blocking.

### FAIL Output Structure

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

## Anti-Patterns

### DO NOT: Conflate Quality with Consistency
Quality measures individual skill routing effectiveness (per-skill scoring). Consistency measures cross-skill relationship integrity (bidirectionality). Keep them separate — leave cross-skill checks to verify-consistency.

### DO NOT: Score Based on L2 Body Quality
L2 is loaded on-demand, not part of routing intelligence. Score only L1 (description/frontmatter). L2 body quality is verify-structural-content's domain.

### DO NOT: Penalize Cross-Cutting Skills for Generic WHEN
Homeostasis and cross-cutting skills legitimately have broader WHEN conditions. Apply domain-adjusted expectations: cross-cutting WHEN scores start at 50 baseline.

### DO NOT: Require DPS in Non-Spawning Skills
Lead-direct skills (no agent spawn) do not need DPS templates. Check execution model: only score DPS presence for STANDARD/COMPLEX tiers with agent spawning.

### DO NOT: Over-Weight Utilization
A concise, specific description outperforms a padded, vague one. Utilization is weighted at 20%. Never let high utilization compensate for low specificity.

### DO NOT: Auto-Fix Low Scores
Quality check is read-only. Mixing assessment and modification introduces bias. Produce improvement instructions only. Fixes go through execution-infra with specific data.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| verify-consistency | Relationship integrity confirmed | L1 YAML: `status: PASS`, consistency findings |
| Direct invocation | Specific files or routing failure context | File paths list or failure report with skill names |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| verify-cc-feasibility | Routing quality confirmed | PASS verdict (avg > 75, no CRITICAL items) |
| execution-infra | Quality improvement requests for .claude/ files | FAIL verdict with specific scores and fix instructions |
| execution-code | Quality improvement requests for source files | FAIL verdict on non-.claude/ files (rare) |

### Failure Routes

| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Average score < 75 | execution-infra | Bottom-5 skills with scores and improvement suggestions |
| Individual skill WHEN < 50 | execution-infra | Skill path + current WHEN + suggested rewrite |
| Missing METHODOLOGY numbers | execution-infra | Skill path + current methodology text |
| Missing output template | execution-infra | Skill path + expected output structure |

## Quality Gate

- Average quality score >75/100 across all verified files
- No skill with WHEN specificity <50 (disambiguation test passes for all)
- All skills have numbered METHODOLOGY steps with concrete actions
- All skills have L1/L2 output format defined
- Bottom-5 skills identified with specific improvement paths
- Scoring rubric applied consistently with documented weights (30/30/20/20)

## Output

### L1
```yaml
domain: verify
skill: quality
status: PASS|FAIL
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

### L2
- Quality score per file (0-100) with per-dimension breakdown
- WHEN condition specificity check with disambiguation test results
- METHODOLOGY concreteness assessment with checklist status
- OUTPUT format completeness with missing field identification
- Utilization measurement with semantic quality cross-reference
- Bottom-5 priority improvement list with specific fix instructions
- Domain-adjusted scoring notes for cross-cutting/homeostasis skills
