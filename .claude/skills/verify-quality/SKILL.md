---
name: verify-quality
description: |
  [P8·Verify·Quality] Routing effectiveness and description clarity verifier. Checks WHEN specificity, methodology concreteness with tool/agent refs, output format L1/L2 presence, and full protocol flow coverage.

  WHEN: Before committing description changes or after routing failures. Fourth of 5 verify stages. Can run independently.
  DOMAIN: verify (skill 4 of 5). After verify-consistency PASS.
  INPUT_FROM: verify-consistency (relationship integrity confirmed) or direct invocation.
  OUTPUT_TO: verify-cc-feasibility (if PASS) or execution-infra (if FAIL on .claude/ files) or execution-code (if FAIL on source files).

  METHODOLOGY: (1) Read WHEN conditions, check specificity (reject vague "when needed"), (2) Read METHODOLOGY steps, check numbered concrete steps with tool names, (3) Check OUTPUT_FORMAT has L1/L2 structure, (4) Check utilization >80% of 1024 chars (aligned with verify-content), (5) Score and rank by routing effectiveness.
  OUTPUT_FORMAT: L1 YAML quality score per file (0-100), L2 markdown quality report with improvement suggestions.
user-invocable: true
disable-model-invocation: false
---

# Verify — Quality

## Execution Model
- **TRIVIAL**: Lead-direct. Quick quality check on 1-2 files.
- **STANDARD**: Spawn analyst. Systematic routing quality assessment.
- **COMPLEX**: Spawn 2 analysts. One for WHEN/METHODOLOGY quality, one for output format quality.

## Methodology

### 1. Assess WHEN Condition Specificity
For each skill description:
- Read the WHEN clause
- Check it specifies a concrete trigger (not vague "when needed")
- Good: "After design-architecture produces component structure"
- Bad: "When the user wants to design"
- Score specificity 0-100

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: All skill descriptions (paste each description text). Include scoring rubric: Specificity (0-100): 100=exact trigger with upstream skill name, 50=vague condition, 0=missing. Concreteness (0-100): 100=numbered steps with tool/agent refs, 50=generic steps, 0=no methodology. Completeness (0-100): 100=L1+L2 defined, 50=partial, 0=missing.
- **Task**: "Score each skill across 4 dimensions: WHEN specificity, METHODOLOGY concreteness, OUTPUT FORMAT completeness, description utilization (>80%). Produce combined score per skill. Rank all skills. Identify bottom 5 for priority improvement."
- **Constraints**: Read-only. No modifications. Score objectively using the rubric.
- **Expected Output**: L1 YAML with avg_score, findings[] (file, score, issues). L2 quality rankings and improvement suggestions.

### 2. Evaluate METHODOLOGY Concreteness
For each skill description:
- Check steps are numbered (1), (2), (3)...
- Verify each step references a concrete tool or action
- Good: "Spawn analyst for design compliance check"
- Bad: "Analyze the results"
- Score concreteness 0-100

### 3. Check Output Format Completeness
For each skill:
- L1 YAML template defined with domain, skill, status
- L2 markdown description defined
- Output section present in body
- Score completeness 0-100

### 4. Measure Description Utilization
For each skill description:
- Calculate char count / 1024
- Target: >80% utilization (aligned with verify-content threshold)
- Flag descriptions below threshold with improvement suggestions

### 5. Generate Quality Rankings
Produce quality score per file:
- Combined score = (specificity + concreteness + completeness + utilization) / 4
- Rank all skills by combined score
- Identify bottom 5 for priority improvement

## Quality Gate
- Average quality score >75/100
- No skill with WHEN specificity <50
- All skills have numbered METHODOLOGY steps
- All skills have L1/L2 output format defined

## Output

### L1
```yaml
domain: verify
skill: quality
status: PASS|FAIL
total_files: 0
avg_score: 0
findings:
  - file: ""
    score: 0
    issues: []
```

### L2
- Quality score per file (0-100)
- WHEN condition specificity check
- METHODOLOGY concreteness assessment
