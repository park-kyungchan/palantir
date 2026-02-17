---
name: verify-structural-content
description: >-
  Inspects YAML frontmatter, naming conventions, and L2 body
  sections for completeness. First of four sequential verify
  stages: structure, consistency, quality, cc-feasibility. Use
  after execution-review PASS or any INFRA file creation or
  modification. Reads from execution-review PASS verdict and
  implementation artifacts. Produces structure and content scores
  per file for verify-consistency on PASS, or routes back to
  execution-infra on FAIL.
user-invocable: true
disable-model-invocation: false
allowed-tools: "Read Glob Grep Write"
metadata:
  category: verify
  tags: [frontmatter-inspection, naming-conventions, structural-completeness]
  version: 2.0.0
---

# Verify — Structural Content (Unified)

## Execution Model
- **TRIVIAL**: Lead-direct. Quick check on 1-3 files. Read files directly, validate frontmatter and content inline.
- **STANDARD**: Spawn 1 analyst (maxTurns: 25). Systematic structural + content check on 4-15 files. Single-pass per file.
- **COMPLEX**: Spawn 2 analysts (maxTurns: 30 each). One for structural checks (YAML, naming, dirs), one for content checks (utilization, keys, sections). 16+ files.

---

## Decision Points

### Tier Classification

| Tier | File Count | Scope | Analyst Spawn |
|------|-----------|-------|---------------|
| TRIVIAL | 1-3 files | Spot-check structure + descriptions | None (Lead-direct) |
| STANDARD | 4-15 files | Full structural + content audit | 1 analyst |
| COMPLEX | 16+ files or full INFRA | All skills + agents | 2 analysts (structure / content) |

### Scope Decision

```
IF major restructuring OR new release OR first-time setup:
  -> Full Scan: All .claude/ components (structure + content)
ELIF specific file creation/modification:
  -> Targeted Scan: Only affected files
  -> Still validate cross-references (e.g., new skill dir has SKILL.md)
```

### Skip Conditions

Structural-content verification MAY be skipped when ALL hold: no `.claude/` files created/deleted, changes are L2-body-only (no frontmatter), no directory additions/removals/renames, only hook `.sh` or non-`.claude/` source files changed. If ANY frontmatter field changed, verification is REQUIRED.

### Analyst Spawn vs Lead-Direct

```
IF tier == TRIVIAL:
  Lead reads 1-3 files directly via Read tool
  Validates frontmatter + content inline
  No agent spawn needed
ELIF tier == STANDARD:
  Spawn 1 analyst with full file list
  Single DPS prompt covering all structure + content checks
ELIF tier == COMPLEX:
  Spawn 2 analysts:
    Analyst-A: Structural checks (YAML, naming, directory, required fields)
    Analyst-B: Content checks (utilization, orchestration keys, body sections, L1/L2 format)
  Lead merges results and computes combined scores
```

### Utilization Threshold Flexibility

The 80% target (>819 chars of 1024) is a guideline:
- Utilization ≥80%: PASS
- Utilization 70-80% AND all 5 orchestration keys present: WARN (not FAIL)
- Utilization 70-80% AND missing keys: FAIL
- Utilization <70%: FAIL regardless of key presence

### Body Section Requirements by Skill Type

| Skill Type | Required Body Sections | Optional Body Sections |
|---|---|---|
| Pipeline skills (P0-P7) | Execution Model, Methodology, Quality Gate, Output | Decision Points, Anti-Patterns, Transitions |
| Verify skills (P7) | Execution Model, Methodology, Quality Gate, Output | DPS templates |
| Homeostasis skills | Execution Model, Methodology, Quality Gate, Output | Scope Boundary, Error Handling |
| Cross-cutting skills | Execution Model, Operations/Methodology, Quality Gate, Output | Fork Execution |

### Known Limitation Handling

Analysts perform heuristic YAML validation (no parser tool). Key edge cases: tab/space mixing (HIGH risk), embedded colons in values (MEDIUM), deeply nested YAML 3+ levels (MEDIUM). Multi-line scalars and trailing whitespace are LOW risk.

---

## Methodology

### 1. Inventory Target Files

Use Glob to discover all `.claude/` components.

**Expected File Counts** (validate against CLAUDE.md declarations):

| Component | Glob Pattern | Expected Count | Location |
|-----------|-------------|----------------|----------|
| Agent definitions | `.claude/agents/*.md` | 6 | Direct children of agents/ |
| Skill definitions | `.claude/skills/*/SKILL.md` | 40 | One per skill directory |
| Settings | `.claude/settings.json` | 1 | .claude/ root |
| Constitution | `.claude/CLAUDE.md` | 1 | .claude/ root |
| Hook scripts | `.claude/hooks/*.sh` | 5 | Direct children of hooks/ |
| Agent memory dirs | `.claude/agent-memory/*/` | varies | Per-agent persistent storage |
| Rules directory | `.claude/rules/*.md` | 0+ | Optional path-scoped rules |

**Expected Agent Files** (6 total):
- `analyst.md`, `researcher.md`, `implementer.md`
- `infra-implementer.md`, `delivery-agent.md`, `pt-manager.md`

**Expected Skill Directories**: Validate count matches CLAUDE.md §1 declarations (currently 44 INFRA across 10 domains + project skills). Cross-reference exact names with `l2-ce-pe-reference.md` Appendix.

### 2. Structural Integrity Checks (per file)

For each agent and skill file, perform structural validation:

**A. YAML Frontmatter Parseability**
- Parse YAML between `---` markers
- Check parsing succeeds without errors
- Report parse failures with file:line location

**Known Limitation**: Analysts perform visual/heuristic YAML validation (indentation, colons, quoting). No programmatic YAML parser available. Subtle syntax errors may pass verification.

**Common YAML Errors** (heuristic detection): Missing colon (`key value`), bad indentation (mixed tabs/spaces), unclosed quotes, pipe scalar without newline (`|text` vs `|` + newline), missing space after colon (`name:value`), unquoted booleans in value fields, trailing content on `---` delimiter lines.

**B. Required Fields Present**

| File Type | Required Fields | Optional Fields |
|-----------|----------------|-----------------|
| SKILL.md | `name`, `description`, `user-invocable`, `disable-model-invocation` | `argument-hint`, `model`, `context`, `agent`, `hooks`, `allowed-tools` |
| Agent .md | `name`, `description` | `tools`, `model`, `permissionMode`, `maxTurns`, `memory`, `color`, `skills`, `mcpServers`, `hooks`, `disallowedTools` |

```
FOR each file:
  IF file is SKILL.md:
    ASSERT name present AND non-empty
    ASSERT description present AND non-empty
    ASSERT user-invocable present (boolean)
    ASSERT disable-model-invocation present (boolean)
  ELIF file is agent .md:
    ASSERT name present AND non-empty
    ASSERT description present AND non-empty
  RECORD: PASS if all assertions hold, FAIL with missing field list otherwise
```

**C. Naming Conventions**

| Component | Regex Pattern | Examples (Valid) | Examples (Invalid) |
|-----------|--------------|-----------------|-------------------|
| Agent files | `/^[a-z][a-z0-9-]*\.md$/` | `analyst.md`, `infra-implementer.md` | `Analyst.md`, `infra_impl.md` |
| Skill directories | `/^[a-z][a-z0-9-]*$/` | `execution-code`, `verify-structure` | `ExecutionCode`, `verify_structure` |
| Skill files | Must be exactly `SKILL.md` | `SKILL.md` | `skill.md`, `Skill.md` |
| Hook scripts | `/^[a-z][a-z0-9-]*\.sh$/` | `on-file-change.sh` | `onFileChange.sh` |
| Settings | Must be exactly `settings.json` | `settings.json` | `Settings.json` |

**D. Directory Structure Compliance**

**Structural Checks**: No orphan files in skills/ (outside skill dirs), no empty skill dirs (missing SKILL.md), agents/hooks as flat dirs (no subdirs), no unexpected top-level .claude/ files. Expected top-level: CLAUDE.md, settings.json, agents/, skills/, hooks/, agent-memory/, rules/, plugins/.

### 3. Content Completeness Checks (per file)

For each agent and skill file, perform content validation:

**A. Description Utilization**
- Extract `description` field from frontmatter
- Measure character count (target: >80% of 1024 = >819 chars)
- Record utilization percentage and categorize

| Category | Utilization Range | Status |
|---|---|---|
| Excellent | >90% (>921 chars) | PASS |
| Good | 80-90% (819-921 chars) | PASS |
| Below Target | 70-80% (716-819 chars) | WARN (if all 5 keys present) or FAIL |
| Critical | <70% (<716 chars) | FAIL |

**B. Orchestration Map Keys**
For each skill description, verify presence of:
- **WHEN**: Trigger condition (when to invoke this skill)
- **DOMAIN**: Domain classification and skill position
- **INPUT_FROM**: Upstream dependencies
- **OUTPUT_TO**: Downstream consumers
- **METHODOLOGY**: Numbered execution steps

**Orchestration Key Extraction**: Grep each description for `/^(WHEN|DOMAIN|INPUT_FROM|OUTPUT_TO|METHODOLOGY):/m`. All 5 must be present.

**Quality Assessment per Key:**

| Key | Quality Check | Good Example | Bad Example |
|---|---|---|---|
| WHEN | Specific trigger with upstream skill name | "After execution-code complete" | "When needed" |
| DOMAIN | Domain name + position + sequence | "execution (skill 1 of 5)" | "execution" |
| INPUT_FROM | Named skill + data type | "orchestration-verify (validated matrix)" | "upstream" |
| OUTPUT_TO | Named skill + trigger condition | "verify domain (if PASS)" | "next phase" |
| METHODOLOGY | Numbered steps (1)-(5) with actions | "(1) Read assignments, (2) Spawn..." | "Analyze and report" |

**C. Body Sections Present**
For each skill file with L2 body, check for required `##` headings: Execution Model, Methodology, Quality Gate, Output. Under Output, require `### L1` and `### L2` sub-headings. Optional `##` headings: Decision Points, Anti-Patterns, Transitions, Failure Handling.

**D. L1/L2 Output Format**
For each Output section:
- L1: YAML template with domain, skill, status fields
- L2: Markdown bullet list describing content

**L1 YAML Required Fields**: `domain`, `skill`, `status` (always required). `findings[]` required if FAIL. Domain-specific fields recommended (e.g., total_files, avg_utilization_pct). Agent files: only `name` + `description` required (no METHODOLOGY key, no L2 body sections).

### 4. Combined Scoring

For each file, compute two independent scores:

- **Structure score (0-100)**: YAML parseability (25), required fields present (25), naming conventions (25), directory compliance (25)
- **Content score (0-100)**: description utilization (25), orchestration keys (25), body sections (25), L1/L2 format (25)
- **Combined score** = average of structure + content scores
- **FAIL** if any file has structure OR content score < 50

**Overall Verdict Logic:**

```
IF any FAIL-level findings (structure or content):
  overall_status = FAIL
  Route to execution-infra with fix requests
  Pipeline blocked at verify stage
ELIF only WARNING-level findings:
  overall_status = PASS (with warnings)
  Proceed to verify-consistency
  Include warnings in L2 for future cleanup
ELIF only INFO or no findings:
  overall_status = PASS
  Proceed to verify-consistency
```

Overall PASS also requires: average utilization >80% AND no file below 60%.

### 5. Generate Combined Report

Produce unified report with per-file results showing both dimensions:
- Structure: YAML validity, naming, directory compliance
- Content: Utilization %, key presence, section presence
- Combined scores and overall PASS/FAIL per file
- Files below 80% utilization threshold flagged with improvement suggestions
- Missing orchestration keys listed per file
- Missing body sections listed per file with required vs optional classification

For STANDARD/COMPLEX tiers, construct the delegation prompt (DPS) for each analyst with:
- **Context**: List of all discovered files from Step 1 (Glob results). Include expected directory structure, common YAML errors checklist, target thresholds (description >80% of 1024, required orchestration keys WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY), and body section requirements per skill type.
- **Task**: "For each file: (1) Read and parse YAML between --- markers, check required fields present, (2) Verify naming conventions (lowercase-hyphen for agents/dirs, SKILL.md uppercase for files), (3) Check directory structure (no orphans, no empty dirs), (4) Measure description char count and utilization %, (5) Check for WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY keys in description, (6) Verify body has Execution Model, Methodology, Quality Gate, Output sections. Report per-file PASS/FAIL with structure+content scores."
- **Constraints**: Read-only. Use Read to examine each file. No modifications. YAML validation is heuristic (no parser tool). Do NOT attempt to fix any issues found.
- **Expected Output**: L1 YAML with total_files, structure_pass, content_pass, findings[]. L2 per-file combined integrity report with structure score + content score.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

---

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|---|---|---|
| execution-review | All PASS verdict, implementation artifacts ready | L1 YAML: `status: PASS`, changed file paths list |
| Direct user invocation | Manual verification request | `/verify-structural-content` with optional target path |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| verify-consistency | Structural + content integrity confirmed | PASS verdict -- all files structurally sound and content complete |
| execution-infra | Fix instructions for .claude/ files | FAIL verdict on `.claude/` files |

### Failure Routes

| Failure Type | Route To | Data Passed |
|---|---|---|
| YAML frontmatter corruption | execution-infra | File path + error location + suggested fix |
| Missing required fields | execution-infra | File path + missing field list |
| Directory structure violation | execution-infra | Expected vs actual structure diff |
| Naming convention violation (blocking) | execution-infra | File path + expected name pattern |
| Missing orchestration keys | execution-infra | File paths + missing keys per file |
| Missing required body sections | execution-infra | File paths + missing section names |
| Low utilization (critical, <70%) | execution-infra | File path + current utilization + suggestions |

---

## Failure Handling

### Severity Classification

| Failure Type | Severity | Blocking? | Action |
|---|---|---|---|
| YAML parse failure | FAIL | YES | Flag file with `file:line` error location. Route to execution-infra |
| Missing required field | FAIL | YES | Flag with specific field name(s). Route to execution-infra |
| Naming violation (breaks auto-loading) | FAIL | YES | E.g., `skill.md` instead of `SKILL.md` prevents CC discovery |
| Missing orchestration keys | FAIL | YES | List specific missing keys. Route to execution-infra |
| Missing required body sections | FAIL | YES | List missing sections. Route to execution-infra |
| Critical utilization (<70%) | FAIL | YES | Include current char count and target. Route to execution-infra |
| Naming violation (cosmetic) | WARNING | NO | E.g., underscore in agent name. Include in report for cleanup |
| Below-target utilization (70-80%) | WARNING | NO | WARN if all 5 keys present. Suggest key expansion |
| Missing optional body sections | WARNING | NO | Note in L2 for future enrichment |
| Orphan file/directory | WARNING | NO | Include in L2 for cleanup recommendation |
| Empty L1/L2 templates | FAIL | YES | Output section must define both L1 and L2 formats |
| Missing optional field | INFO | NO | Note in L2 report, no action required |

### Pipeline Impact Rules

Same as Combined Scoring verdict logic (Step 4): FAIL → execution-infra (blocked), WARNING → PASS with warnings → verify-consistency, INFO → PASS → verify-consistency.

### Low Utilization File
- Flag with improvement suggestion (which orchestration keys to add or expand)
- Include current char count and target char count
- Severity: WARN if all 5 keys present and utilization >70%, FAIL otherwise

### Missing Orchestration Keys
- FAIL with specific missing keys listed per file. Include which keys ARE present for context. Route to `execution-infra` for description rewrite.

---

## Anti-Patterns

| Rule | Rationale |
|------|-----------|
| DO NOT attempt programmatic YAML parsing | Analysts have no YAML parser tool. Use heuristic checks (indentation, colons, quoting). Accept the limitation. |
| DO NOT modify files during verification | Verify is strictly read-only. All fixes route through execution-infra skill. |
| DO NOT validate field VALUES or semantic quality | Structure checks field PRESENCE. Content checks key PRESENCE. Whether the WHEN condition is correct is verify-quality's job. |
| DO NOT verify cross-references here | Bidirectionality checking (INPUT_FROM/OUTPUT_TO matching) is verify-consistency's job. |
| DO NOT read full L2 bodies for content quality | Only check L2 section HEADINGS exist, not their content quality. |
| DO NOT scan outside `.claude/` directory | Scope is strictly `.claude/` components. Source code structure is not this skill's concern. |
| DO NOT block pipeline on naming warnings | Only YAML parse failures, missing required fields, and missing keys are blocking. Naming cosmetics are WARNING-level. |
| DO NOT penalize short descriptions that are complete | A 750-char description with all 5 orchestration keys is better than a 1000-char description missing WHEN. |
| DO NOT treat agent files same as skill files | Agents require only name + description. No METHODOLOGY key, no L2 body sections required. |

---

## Quality Gate

### Pass Criteria

| Criterion | Check Method | Threshold |
|-----------|-------------|-----------|
| YAML frontmatter parses without heuristic errors | All files pass heuristic YAML checks | 100% of files |
| Required fields present and non-empty | Field presence check per file type table | 100% of files |
| Naming conventions match regex patterns | Regex validation per component type | 100% (FAIL-level only) |
| No orphaned files or empty directories | Directory tree scan | 0 orphans |
| Expected file counts match CLAUDE.md | Compare Glob results vs declared counts | agents: 6, skills: 40, hooks: 5 |
| Average description utilization | Char count measurement | >80% across all files |
| No file below utilization floor | Per-file minimum check | No file <60% |
| Orchestration keys present | Key extraction regex | All 5 keys in all skills |
| Required body sections present | Heading detection regex | Execution Model, Methodology, Quality Gate, Output |
| L1/L2 output format defined | Sub-heading detection | Both L1 and L2 present in Output |

### Overall Verdict Logic

PASS: All criteria met, no FAIL findings (warnings acceptable). FAIL: Any FAIL-level finding present — pipeline blocked. FAIL output must include: file path, error type, line number, structure+content scores, suggested remediation, route target (execution-infra).

---

## Output

### L1
```yaml
domain: verify
skill: structural-content
status: PASS|FAIL
total_files: 0
structure_pass: 0
content_pass: 0
avg_utilization_pct: 0
below_threshold_count: 0
missing_keys_count: 0
missing_sections_count: 0
warnings: 0
findings:
  - file: ""
    structure_score: 0
    content_score: 0
    utilization_pct: 0
    missing_keys: []
    missing_sections: []
    issues: []
```

### L2
- File inventory with expected vs actual counts comparison
- Per-file combined report:
  - Structure: YAML validity, naming conventions, directory compliance
  - Content: Utilization % with ranking category, key presence, section presence
  - Combined score and per-file PASS/FAIL/WARNING
- Structural issues with file:line evidence
- Description utilization rankings with improvement suggestions
- Missing orchestration keys per file with specific key names
- Missing body sections per file with required vs optional classification
- Orphan/empty directory report (if any)
- Overall PASS/FAIL verdict with routing recommendation
- Next: verify-consistency (if PASS)
