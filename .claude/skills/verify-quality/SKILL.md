---
name: verify-quality
description: >-
  Assesses artifact quality across specificity, concreteness,
  completeness, and utilization dimensions. Scores artifacts 0-100
  and identifies bottom-5 for improvement. Third of four sequential
  verify stages. Use after verify-consistency PASS or after routing
  failures requiring investigation. Reads from verify-consistency
  relationship integrity confirmation. Produces quality scores per
  file for verify-cc-feasibility on PASS, or routes to the relevant
  execution skill on FAIL. On FAIL, routes bottom-5 artifacts with
  scores and improvement instructions. Scoring rubric is
  DPS-parameterized per artifact type. Default rubric (INFRA skills):
  WHEN specificity 30% + METHODOLOGY concreteness 30% + OUTPUT
  completeness 20% + utilization 20%. For non-INFRA artifacts,
  caller provides rubric and dimension weights via DPS. TRIVIAL:
  Lead-direct spot check. STANDARD: 1 analyst full scoring audit.
  COMPLEX: 2 analysts — specificity/concreteness vs
  completeness/utilization split. DPS context: all artifact
  description texts + scoring rubric. Exclude L2 body content and
  cross-artifact consistency checks (verify-consistency domain).
user-invocable: true
disable-model-invocation: true
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

When reviewing many files, prioritize:
1. Recently modified skills (highest risk of regression)
2. Skills involved in recent routing failures (direct evidence of quality issues)
3. Skills with known low scores from previous runs (persistent quality debt)
4. Newly created skills (no prior quality baseline)

### Routing Failure Investigation Mode
When invoked after a routing failure: (1) identify the failed and correct skills, (2) compare WHEN conditions side-by-side, (3) check for ambiguous overlap, (4) weight WHEN Specificity at 50%, (5) produce disambiguation recommendations.

### Skip Conditions
Skip when: only L2 body changed (no frontmatter edits); documentation-only changes (no `.claude/skills/` touched); previous run scored >90 avg and no new skills added since.

## Methodology

### 1. Assess WHEN Condition Specificity
Read WHEN clause per skill. Check for concrete trigger (not vague "when needed"). Score 0-100. For STANDARD/COMPLEX: analyst DPS includes all description texts + scoring rubric; exclude L2 body.

### 2. Evaluate METHODOLOGY Concreteness
Check steps are numbered (1), (2), (3). Each step must name a concrete tool or action, not "analyze." Score 0-100.

### 3. Check Output Format Completeness
Verify L1 YAML with `domain`, `skill`, `status` present. Verify L2 markdown description present. Score 0-100.

### 4. Measure Description Utilization
Calculate char count / 1024. Target >80%. Weighted at 20% — a concise, specific description outperforms padded, vague content.

### 5. Generate Quality Rankings
Combined score = (specificity * 0.30) + (concreteness * 0.30) + (completeness * 0.20) + (utilization * 0.20). Rank all skills. Identify bottom-5.

> For WHEN decision trees, domain examples, concreteness checklist, completeness scoring table, DPS construction detail, improvement priority matrix, and bottom-5 report format: read `resources/methodology.md`

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| Analyst tool error reading descriptions | L0 Retry | Re-invoke analyst with same DPS and rubric |
| Analyst scoring incomplete, bottom-5 list missing | L1 Nudge | Respawn with refined DPS targeting rubric reminder and remaining file list |
| Analyst exhausted turns before full scoring, context polluted | L2 Respawn | Kill analyst → spawn fresh with reduced file batch |
| Routing failure investigation requires restructuring analyst split | L3 Restructure | Separate WHEN/METHODOLOGY analyst from OUTPUT/utilization analyst |
| 3+ L2 failures or scoring rubric ambiguous for cross-cutting skills | L4 Escalate | AskUserQuestion with situation summary + options |

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

> For FAIL output structure YAML template: read `resources/methodology.md`

## Anti-Patterns

**DO NOT: Conflate Quality with Consistency** — Quality measures per-skill routing effectiveness; consistency measures cross-skill relationship integrity. Leave cross-skill checks to verify-consistency.

**DO NOT: Score Based on L2 Body Quality** — L2 is loaded on-demand, not part of routing intelligence. Score only L1 description/frontmatter. L2 body quality is verify-structural-content's domain.

**DO NOT: Penalize Cross-Cutting Skills for Generic WHEN** — Homeostasis/cross-cutting skills legitimately have broader triggers. Apply domain-adjusted expectations: cross-cutting WHEN scores start at 50 baseline.

**DO NOT: Require DPS in Non-Spawning Skills** — Lead-direct skills do not need DPS templates. Score DPS presence only for STANDARD/COMPLEX tiers with agent spawning.

**DO NOT: Over-Weight Utilization** — A concise, specific description outperforms a padded, vague one. Utilization is weighted at 20%. Never let high utilization compensate for low specificity.

**DO NOT: Auto-Fix Low Scores** — Quality check is read-only. Produce improvement instructions only. Fixes go through execution-infra with specific data.

## Phase-Aware Execution

This skill runs via subagent:
- **Communication**: Two-Channel protocol — Ch2 output file in work directory + Ch3 micro-signal to Lead.
- **Coordination**: Read upstream outputs from work directory files. File ownership: no overlapping edits.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

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

> **D17 Note**: Two-Channel protocol — Ch2 output file in work directory, Ch3 micro-signal to Lead.
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

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
pt_signal: "metadata.phase_signals.p7_quality"
signal_format: "{STATUS}|files:{N}|avg_score:{N}|ref:{work_dir}/p7-quality.md"
total_files: 0
avg_score: 0
```

> Full L1 template with `findings[]` and `bottom_5[]` fields: read `resources/methodology.md`

### L2
- Quality score per file (0-100) with per-dimension breakdown
- WHEN condition specificity check with disambiguation test results
- METHODOLOGY concreteness assessment with checklist status
- OUTPUT format completeness with missing field identification
- Utilization measurement with semantic quality cross-reference
- Bottom-5 priority improvement list with specific fix instructions
- Domain-adjusted scoring notes for cross-cutting/homeostasis skills
