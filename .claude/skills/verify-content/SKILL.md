---
name: verify-content
description: |
  [P7·Verify·Content] Content completeness and quality verifier. Checks description utilization (target >80% of 1024 chars), orchestration map keys (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO), body sections, and L1/L2 format standards.

  WHEN: After description rewrites or new agent/skill creation. Second of 5 verify stages. Can run independently.
  DOMAIN: verify (skill 2 of 5). After verify-structure PASS.
  INPUT_FROM: verify-structure (structural integrity confirmed) or direct invocation.
  OUTPUT_TO: verify-consistency (if PASS) or execution-infra (if FAIL on .claude/ files) or execution-code (if FAIL on source files).

  METHODOLOGY: (1) Read all frontmatter descriptions, (2) Measure char utilization (target >80% of 1024), (3) Check orchestration map keys present (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO, METHODOLOGY), (4) Verify body sections present, (5) Check L1/L2 output format defined.
  OUTPUT_FORMAT: L1 YAML utilization percentage per file, L2 markdown content completeness report with missing items.
user-invocable: true
disable-model-invocation: false
---

# Verify — Content

## Execution Model
- **TRIVIAL**: Lead-direct. Quick content check on 1-3 files. Spot-check descriptions.
- **STANDARD**: Spawn analyst. Systematic content completeness check on 4-15 files. Full description audit.
- **COMPLEX**: Spawn 2 analysts. One for agents, one for skills. Full INFRA audit across all 35 skills + 6 agents (16+ files).

---

## Decision Points

### Tier Classification for Content Verification

| Tier | File Count | Scope | Analyst Spawn |
|------|-----------|-------|---------------|
| TRIVIAL | 1-3 files | Spot-check descriptions only | None (Lead-direct) |
| STANDARD | 4-15 files | Full description audit | 1 analyst |
| COMPLEX | 16+ files or full INFRA | All skills + agents | 2 analysts (agents / skills) |

### Utilization Threshold Flexibility

The 80% target (>819 chars of 1024) is a guideline. Some skills legitimately have shorter descriptions if their L1 routing information is complete.

```
Decision Tree: Utilization Assessment
======================================

File utilization < 80%?
  |
  +-- YES --> Check orchestration keys
  |             |
  |             +-- All 5 keys present and specific?
  |             |     |
  |             |     +-- YES --> Allow 70% minimum (WARN, not FAIL)
  |             |     +-- NO  --> FAIL (missing keys + low utilization)
  |             |
  +-- NO  --> PASS (utilization acceptable)
```

### Body Section Requirements by Skill Type

| Skill Type | Required Body Sections | Optional Body Sections |
|---|---|---|
| Pipeline skills (P0-P7) | Execution Model, Methodology, Quality Gate, Output | Decision Points, Anti-Patterns, Transitions |
| Verify skills (P7) | Execution Model, Methodology, Quality Gate, Output | DPS templates |
| Homeostasis skills | Execution Model, Methodology, Quality Gate, Output | Scope Boundary, Error Handling |
| Cross-cutting skills | Execution Model, Operations/Methodology, Quality Gate, Output | Fork Execution |

### Skip Conditions

Content verification can be skipped when:
- Only hook `.sh` files changed (no frontmatter to verify)
- Only non-`.claude/` source files changed (no skill/agent content)
- verify-structure already reported FAIL (fix structure first)

### Scoring vs Binary

Content check uses a **scoring system** (utilization %), not binary PASS/FAIL per file.

| Category | Utilization Range | Status |
|---|---|---|
| Excellent | >90% (>921 chars) | PASS |
| Good | 80-90% (819-921 chars) | PASS |
| Below Target | 70-80% (716-819 chars) | WARN (if all 5 keys present) or FAIL |
| Critical | <70% (<716 chars) | FAIL |

Overall PASS requires: average >80% AND no file below 60%.

---

## Methodology

### 1. Read All Descriptions
For each agent and skill file:
- Extract the `description` field from frontmatter
- Measure character count (target: >80% of 1024 = >819 chars)
- Record utilization percentage

**Orchestration Key Extraction Patterns:**

```yaml
# Regex patterns for key extraction from description text
WHEN: '/WHEN:.*$/m'
DOMAIN: '/DOMAIN:.*$/m'
INPUT_FROM: '/INPUT_FROM:.*$/m'
OUTPUT_TO: '/OUTPUT_TO:.*$/m'
METHODOLOGY: '/METHODOLOGY:.*$/m'
```

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: List of all skill and agent files to verify (from verify-structure PASS results or Glob). Include the target thresholds: description >80% of 1024 chars (>819 chars), required orchestration keys (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO, METHODOLOGY).
- **Task**: "For each file: (1) Extract description field, measure char count and utilization %, (2) Check for WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO, METHODOLOGY keys in description, (3) Verify body has Execution Model, Methodology (numbered steps), Quality Gate, and Output (L1/L2) sections. Flag files below 80% utilization or missing required keys."
- **Constraints**: Read-only. No modifications.
- **Expected Output**: L1 YAML with avg_utilization_pct, findings[] (file, utilization_pct, missing_keys). L2 utilization rankings and missing content report.

### 2. Check Orchestration Map Keys
For each skill description, verify presence of:
- **WHEN**: Trigger condition (when to invoke this skill)
- **DOMAIN**: Domain classification and skill position
- **INPUT_FROM**: Upstream dependencies
- **OUTPUT_TO**: Downstream consumers
- **METHODOLOGY**: Numbered execution steps

**Quality Assessment per Key:**

| Key | Quality Check | Good Example | Bad Example |
|---|---|---|---|
| WHEN | Specific trigger with upstream skill name | "After execution-code complete" | "When needed" |
| DOMAIN | Domain name + position + sequence | "execution (skill 1 of 5)" | "execution" |
| INPUT_FROM | Named skill + data type | "orchestration-verify (validated matrix)" | "upstream" |
| OUTPUT_TO | Named skill + trigger condition | "verify domain (if PASS)" | "next phase" |
| METHODOLOGY | Numbered steps (1)-(5) with actions | "(1) Read assignments, (2) Spawn..." | "Analyze and report" |

### 3. Verify Body Sections
For each skill file with L2 body:
- Execution Model section present (TRIVIAL/STANDARD/COMPLEX)
- Methodology section with numbered steps
- Quality Gate section with pass/fail criteria
- Output section with L1 YAML and L2 markdown templates

**Section Detection Patterns:**

```yaml
# Required headings (## level)
execution_model: '/^## Execution Model/m'
methodology: '/^## Methodology/m'
quality_gate: '/^## Quality Gate/m'
output: '/^## Output/m'

# Required sub-headings (### level under Output)
l1_template: '/^### L1/m'
l2_template: '/^### L2/m'

# Optional headings (## level)
decision_points: '/^## Decision Points/m'
anti_patterns: '/^## Anti-Patterns/m'
transitions: '/^## Transitions/m'
failure_handling: '/^## Failure Handling/m'
```

### 4. Check L1/L2 Format
For each Output section:
- L1: YAML template with domain, skill, status fields
- L2: Markdown bullet list describing content

**L1 YAML Required Fields Checklist:**

| Field | Required | Description |
|---|---|---|
| `domain` | YES | Pipeline domain name |
| `skill` | YES | Skill name within domain |
| `status` | YES | PASS or FAIL verdict |
| `findings` | YES (if FAIL) | Array of specific findings |
| Domain-specific fields | RECOMMENDED | e.g., total_files, avg_utilization_pct |

### 5. Generate Content Report
Produce utilization rankings:
- Files below 80% threshold flagged
- Missing orchestration keys listed per file
- Missing body sections listed per file

**Utilization Ranking Categories:**

| Category | Range | Action |
|---|---|---|
| Excellent | >90% | No action needed |
| Good | 80-90% | No action needed |
| Below Target | 70-80% | WARN — suggest key expansion |
| Critical | <70% | FAIL — route to execution-infra |

---

## Failure Handling

### Low Utilization File
- Flag with improvement suggestion (which orchestration keys to add or expand)
- Include current char count and target char count
- Severity: WARN if all 5 keys present and utilization >70%, FAIL otherwise

### Missing Orchestration Keys
- FAIL with specific missing keys listed per file
- Route to `execution-infra` for description rewrite
- Include which keys are present for context

```
Example finding:
  file: skills/research-codebase/SKILL.md
  utilization_pct: 72
  missing_keys: [INPUT_FROM, OUTPUT_TO]
  action: Route to execution-infra for description expansion
```

### Missing Body Sections
- WARN if optional section missing (Decision Points, Anti-Patterns, Transitions)
- FAIL if required section missing (Execution Model, Methodology, Quality Gate, Output)
- List all missing sections per file

### Empty L1/L2 Templates
- FAIL if Output section exists but L1 YAML schema or L2 markdown format is absent
- Output section must define both L1 and L2 formats

### Pipeline Impact

| Failure Type | Blocking? | Next Action |
|---|---|---|
| Missing required body sections | YES (blocking) | Route to execution-infra |
| Missing orchestration keys | YES (blocking) | Route to execution-infra |
| Low utilization (WARN) | NO (non-blocking) | Continue to verify-consistency with warning |
| Missing optional body sections | NO (non-blocking) | Continue to verify-consistency with note |

---

## Anti-Patterns

- **DO NOT: Penalize Short Descriptions That Are Complete** -- a 750-char description with all 5 orchestration keys is better than a 1000-char description missing WHEN
- **DO NOT: Check Description Semantic Quality** -- content checks structural completeness, not whether the WHEN condition is actually correct (that is verify-quality's job)
- **DO NOT: Verify Cross-References Here** -- bidirectionality checking (INPUT_FROM/OUTPUT_TO matching) is verify-consistency's job
- **DO NOT: Read Full L2 Bodies for Content Check** -- only check L2 section HEADINGS exist, not their content quality
- **DO NOT: Modify Files to Fix Utilization** -- content is read-only verification; fixes route through execution-infra
- **DO NOT: Treat Agent Files Same as Skill Files** -- agents have different required fields (name, description only; no METHODOLOGY key, no L2 body sections required)

---

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|---|---|---|
| verify-structure | Structural integrity confirmed | L1 YAML: PASS verdict, file inventory |
| Direct invocation | Specific files to check | File paths list |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| verify-consistency | Content completeness confirmed | PASS verdict |
| execution-infra | Content fix requests for .claude/ files | FAIL verdict |
| execution-code | Content fix requests for source files | FAIL verdict |

### Failure Routes

| Failure Type | Route To | Data Passed |
|---|---|---|
| Missing orchestration keys | execution-infra | File paths + missing keys per file |
| Missing required body sections | execution-infra | File paths + missing section names |
| Below-threshold utilization (warning) | verify-consistency (continue) | Warning in L1 findings |

---

## Quality Gate
- Average description utilization >80% across all files
- Zero files missing any of the 5 orchestration keys (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO, METHODOLOGY)
- All skills have required body sections: Execution Model, Methodology, Quality Gate, Output
- L1 YAML template includes at minimum: domain, skill, status fields
- No completely empty body sections (heading present but no content)

## Output

### L1
```yaml
domain: verify
skill: content
status: PASS|FAIL
total_files: 0
avg_utilization_pct: 0
below_threshold_count: 0
missing_keys_count: 0
missing_sections_count: 0
findings:
  - file: ""
    utilization_pct: 0
    char_count: 0
    missing_keys: []
    missing_sections: []
    category: "excellent|good|below_target|critical"
```

### L2
- Description utilization percentages per file with ranking category
- Missing orchestration map keys per file with specific key names
- Missing body sections per file with required vs optional classification
- Content completeness assessment with overall PASS/FAIL verdict
- Improvement suggestions for files below threshold
- Routing recommendations for FAIL findings (execution-infra or execution-code)
