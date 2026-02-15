---
name: verify-content
description: |
  [P8·Verify·Content] Content completeness and quality verifier. Checks description utilization (target >80% of 1024 chars), orchestration map keys (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO), body sections, and L1/L2 format standards.

  WHEN: After description rewrites or new agent/skill creation. Second of 5 verify stages. Can run independently.
  DOMAIN: verify (skill 2 of 5). After verify-structure PASS.
  INPUT_FROM: verify-structure (structural integrity confirmed) or direct invocation.
  OUTPUT_TO: verify-consistency (if PASS) or execution domain (if FAIL, fix required).

  METHODOLOGY: (1) Read all frontmatter descriptions, (2) Measure char utilization (target >80% of 1024), (3) Check orchestration map keys present (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO, METHODOLOGY), (4) Verify body sections present, (5) Check L1/L2 output format defined.
  OUTPUT_FORMAT: L1 YAML utilization percentage per file, L2 markdown content completeness report with missing items.
user-invocable: true
disable-model-invocation: false
---

# Verify — Content

## Execution Model
- **TRIVIAL**: Lead-direct. Quick content check on 1-2 files.
- **STANDARD**: Spawn analyst. Systematic content completeness check.
- **COMPLEX**: Spawn 2 analysts. One for agents, one for skills.

## Methodology

### 1. Read All Descriptions
For each agent and skill file:
- Extract the `description` field from frontmatter
- Measure character count (target: >80% of 1024 = >819 chars)
- Record utilization percentage

### 2. Check Orchestration Map Keys
For each skill description, verify presence of:
- **WHEN**: Trigger condition (when to invoke this skill)
- **DOMAIN**: Domain classification and skill position
- **INPUT_FROM**: Upstream dependencies
- **OUTPUT_TO**: Downstream consumers
- **METHODOLOGY**: Numbered execution steps

### 3. Verify Body Sections
For each skill file with L2 body:
- Execution Model section present (TRIVIAL/STANDARD/COMPLEX)
- Methodology section with numbered steps
- Quality Gate section with pass/fail criteria
- Output section with L1 YAML and L2 markdown templates

### 4. Check L1/L2 Format
For each Output section:
- L1: YAML template with domain, skill, status fields
- L2: Markdown bullet list describing content

### 5. Generate Content Report
Produce utilization rankings:
- Files below 80% threshold flagged
- Missing orchestration keys listed per file
- Missing body sections listed per file

## Quality Gate
- Average description utilization >80%
- All skill descriptions have WHEN + DOMAIN + INPUT_FROM + OUTPUT_TO
- All skills have Output section with L1/L2 templates
- No completely empty body sections

## Output

### L1
```yaml
domain: verify
skill: content
status: PASS|FAIL
total_files: 0
avg_utilization_pct: 0
findings:
  - file: ""
    utilization_pct: 0
    missing_keys: []
```

### L2
- Description utilization percentages
- Missing orchestration map keys per file
- Content completeness assessment
