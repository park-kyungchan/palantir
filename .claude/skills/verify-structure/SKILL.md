---
name: verify-structure
description: |
  [P7·Verify·Structure] Structural integrity verifier. Checks file existence, YAML frontmatter parseability, directory structure compliance, and naming conventions for all .claude/ components.

  WHEN: After any INFRA file creation or modification. First of 5 verify stages. Can run independently.
  DOMAIN: verify (skill 1 of 5). Sequential: structure -> content -> consistency -> quality -> cc-feasibility.
  INPUT_FROM: execution domain (implementation artifacts) or any file modification trigger.
  OUTPUT_TO: verify-content (if PASS) or execution-infra (if FAIL on .claude/ files) or execution-code (if FAIL on source files).

  METHODOLOGY: (1) Glob .claude/agents/*.md and .claude/skills/*/SKILL.md, (2) Validate YAML frontmatter parses without errors, (3) Check required fields present (name, description), (4) Verify naming (lowercase-hyphen, correct prefixes), (5) Check directory structure matches expected layout.
  OUTPUT_FORMAT: L1 YAML PASS/FAIL per file, L2 structural integrity report with file:line evidence.
user-invocable: true
disable-model-invocation: false
---

# Verify — Structure

## Execution Model
- **TRIVIAL**: Lead-direct. Quick check on 1-2 files.
- **STANDARD**: Spawn analyst. Systematic structural verification.
- **COMPLEX**: Spawn 2 analysts. One for agents, one for skills.

---

## Decision Points

### Tier Classification for Structure Verification

| Tier | Criteria | Action |
|------|----------|--------|
| TRIVIAL | 1-2 files changed, single directory | Lead reads files directly, checks inline |
| STANDARD | 3-10 files across agents + skills | Spawn 1 analyst for full structural scan |
| COMPLEX | 11+ files or new directory creation | Spawn 2 analysts: one for agents, one for skills |

### Scope Decision

```
IF major restructuring OR new release OR first-time setup:
  -> Full Scan: All .claude/ components
ELIF specific file creation/modification:
  -> Targeted Scan: Only affected directories
  -> Still validate cross-references (e.g., new skill dir has SKILL.md)
```

### Skip Conditions

Structure verification MAY be skipped when ALL of these hold:
1. No `.claude/` files were created or deleted
2. Changes are L2-body-only edits (no frontmatter modifications)
3. No directory additions or removals
4. No file renames

If ANY frontmatter field changed, structure verification is REQUIRED.

### Analyst Spawn vs Lead-Direct

```
IF tier == TRIVIAL:
  Lead reads 1-2 files directly via Read tool
  Validates frontmatter inline
  No agent spawn needed
ELIF tier == STANDARD:
  Spawn 1 analyst with full file list
  Single DPS prompt covering all checks
ELIF tier == COMPLEX:
  Spawn 2 analysts:
    Analyst-A: .claude/agents/*.md (agent definitions)
    Analyst-B: .claude/skills/*/SKILL.md (skill definitions)
  Lead validates hooks + settings.json + CLAUDE.md directly
```

### Known Limitation Handling

Since analysts perform heuristic YAML validation (no parser tool available):

| Edge Case | Detection Strategy | Risk Level |
|-----------|-------------------|------------|
| Multi-line strings with special chars | Check `\|` or `>` scalar indicator present | LOW — usually caught by indentation check |
| Deeply nested YAML (3+ levels) | Count indentation levels, verify consistency | MEDIUM — indentation errors harder to spot |
| Pipe/block scalars (`\|`, `>`, `\|+`, `\|-`) | Verify whitespace after scalar indicator | LOW — pattern is simple |
| Embedded colons in values | Check if value is quoted when containing `:` | MEDIUM — false positives possible |
| Tab vs space mixing | Look for tab characters in frontmatter region | HIGH — visually identical, breaks YAML |
| Trailing whitespace after `---` | Check line content is exactly `---` | LOW — easy to detect |

---

## Methodology

### 1. Inventory All Files

Use Glob to discover all `.claude/` components.

**Expected File Counts** (validate against CLAUDE.md declarations):

| Component | Glob Pattern | Expected Count | Location |
|-----------|-------------|----------------|----------|
| Agent definitions | `.claude/agents/*.md` | 6 | Direct children of agents/ |
| Skill definitions | `.claude/skills/*/SKILL.md` | 35 | One per skill directory |
| Settings | `.claude/settings.json` | 1 | .claude/ root |
| Constitution | `.claude/CLAUDE.md` | 1 | .claude/ root |
| Hook scripts | `.claude/hooks/*.sh` | 5 | Direct children of hooks/ |
| Agent memory dirs | `.claude/agent-memory/*/` | varies | Per-agent persistent storage |
| Rules directory | `.claude/rules/*.md` | 0+ | Optional path-scoped rules |

**Expected Agent Files** (6 total):
- `analyst.md`, `researcher.md`, `implementer.md`
- `infra-implementer.md`, `delivery-agent.md`, `pt-manager.md`

**Expected Skill Directories** (35 total, 8 pipeline + 4 homeostasis + 3 cross-cutting):

| Domain | Skill Directories |
|--------|-------------------|
| pre-design | `pre-design-brainstorm`, `pre-design-validate`, `pre-design-feasibility` |
| design | `design-architecture`, `design-interface`, `design-risk` |
| research | `research-codebase`, `research-external`, `research-audit` |
| plan | `plan-decomposition`, `plan-interface`, `plan-strategy` |
| plan-verify | `plan-verify-correctness`, `plan-verify-completeness`, `plan-verify-robustness` |
| orchestration | `orchestration-decompose`, `orchestration-assign`, `orchestration-verify` |
| execution | `execution-code`, `execution-infra`, `execution-impact`, `execution-cascade`, `execution-review` |
| verify | `verify-structure`, `verify-content`, `verify-consistency`, `verify-quality`, `verify-cc-feasibility` |
| homeostasis | `manage-infra`, `manage-skills`, `manage-codebase`, `self-improve` |
| cross-cutting | `delivery-pipeline`, `pipeline-resume`, `task-management` |

### 2. Validate YAML Frontmatter

For each agent and skill file:
- Parse YAML between `---` markers
- Check parsing succeeds without errors
- Report parse failures with file:line location

**Known Limitation**: Analysts perform visual/heuristic YAML validation (indentation, colons, quoting). No programmatic YAML parser available. Subtle syntax errors may pass verification.

**Common YAML Errors Checklist**:

| Error Type | Invalid Pattern | Valid Pattern | Detection Method |
|------------|----------------|---------------|------------------|
| Missing colon | `key value` | `key: value` | Grep for lines without `:` between `---` markers |
| Bad indentation | Mixed tabs/spaces | Consistent 2-space indent | Visual inspection in Read output |
| Unclosed quotes | `description: "text...` | `description: "text"` | Check quote pairing per line |
| Pipe scalar without newline | `description: \|text` | `description: \|` + newline + indented text | Check whitespace after `\|` |
| Missing space after colon | `name:value` | `name: value` | Grep for `[a-z]:[^ \n]` pattern |
| Boolean unquoted | `description: true` | `description: "true"` | Flag if value field contains bare boolean |
| Trailing `---` content | `--- extra` | `---` | Check delimiter lines are exactly 3 dashes |

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: List of all discovered files from Step 1 (Glob results). Include expected directory structure: agents in `.claude/agents/*.md`, skills in `.claude/skills/*/SKILL.md`. Include the common YAML errors checklist table above for reference.
- **Task**: "For each file: (1) Read and parse YAML between --- markers, (2) Check required fields (name, description present and non-empty; skills: user-invocable present), (3) Verify naming (lowercase-hyphen for agents/dirs, SKILL.md uppercase for files), (4) Check directory structure (no orphans, no empty dirs). Report per-file PASS/FAIL with file:line evidence."
- **Constraints**: Read-only. Use Read to examine each file. No modifications. Note: YAML validation is heuristic (no parser tool) — check for common errors (missing colons, bad indentation, unclosed quotes). Do NOT attempt to fix any issues found.
- **Expected Output**: L1 YAML with total_files, pass, fail, findings[] (file, check, status). L2 per-file structural integrity report.

### 3. Check Required Fields

**Required Fields by File Type**:

| File Type | Required Fields | Optional Fields |
|-----------|----------------|-----------------|
| SKILL.md | `name`, `description`, `user-invocable`, `disable-model-invocation` | `argument-hint`, `model`, `context`, `agent`, `hooks`, `allowed-tools` |
| Agent .md | `name`, `description` | `tools`, `model`, `permissionMode`, `maxTurns`, `memory`, `color`, `skills`, `mcpServers`, `hooks`, `disallowedTools` |

For each parsed frontmatter, verify:

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

### 4. Verify Naming Conventions

**Regex Validation Patterns**:

| Component | Regex Pattern | Examples (Valid) | Examples (Invalid) |
|-----------|--------------|-----------------|-------------------|
| Agent files | `/^[a-z][a-z0-9-]*\.md$/` | `analyst.md`, `infra-implementer.md` | `Analyst.md`, `infra_impl.md` |
| Skill directories | `/^[a-z][a-z0-9-]*$/` | `execution-code`, `verify-structure` | `ExecutionCode`, `verify_structure` |
| Skill files | Must be exactly `SKILL.md` | `SKILL.md` | `skill.md`, `Skill.md` |
| Hook scripts | `/^[a-z][a-z0-9-]*\.sh$/` | `on-file-change.sh` | `onFileChange.sh` |
| Settings | Must be exactly `settings.json` | `settings.json` | `Settings.json` |

### 5. Check Directory Structure

**Expected Directory Tree**:

```
.claude/
  CLAUDE.md                          # Constitution (1 file)
  settings.json                      # Settings (1 file)
  agents/                            # Agent definitions (6 files)
    analyst.md
    researcher.md
    implementer.md
    infra-implementer.md
    delivery-agent.md
    pt-manager.md
  skills/                            # Skill definitions (35 directories)
    pre-design-brainstorm/SKILL.md
    pre-design-validate/SKILL.md
    pre-design-feasibility/SKILL.md
    ...                              # (32 more skill directories)
  hooks/                             # Hook scripts (5 files)
    on-subagent-start.sh
    on-session-compact.sh
    on-implementer-done.sh
    on-file-change.sh
    on-pre-compact.sh
  agent-memory/                      # Per-agent persistent memory (varies)
    analyst/
    infra-implementer/
    ...
  rules/                             # Optional path-scoped rules (0+ files)
  plugins/                           # Optional plugin configs (0+ files)
```

**Structural Checks**:
- No orphan files in `.claude/skills/` (files outside skill dirs)
- No empty skill directories (dir without SKILL.md)
- Agent files directly under `.claude/agents/` (no subdirectories)
- Hook scripts directly under `.claude/hooks/` (no subdirectories)
- No unexpected top-level files in `.claude/` (only CLAUDE.md, settings.json, and known dirs)

---

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|---|---|---|
| execution domain (code, infra) | Implementation artifacts | Changed file paths list |
| execution-infra | `.claude/` file changes | L1 YAML: `files_changed[]` |
| Any trigger | File modification event | File paths |
| Direct user invocation | Manual verification request | `/verify-structure` with optional target path |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| verify-content | Structural integrity confirmed | PASS verdict — all files structurally sound |
| execution-infra | Structural fix requests | FAIL verdict on `.claude/` files |
| execution-code | Structural fix requests | FAIL verdict on source files |

### Failure Routes

| Failure Type | Route To | Data Passed |
|---|---|---|
| YAML frontmatter corruption | execution-infra | File path + error location + suggested fix |
| Missing required fields | execution-infra | File path + missing field list |
| Directory structure violation | execution-infra | Expected vs actual structure diff |
| Naming convention violation (blocking) | execution-infra | File path + expected name pattern |

---

## Failure Handling

### Severity Classification

| Failure Type | Severity | Blocking? | Action |
|---|---|---|---|
| YAML parse failure | FAIL | YES — blocks pipeline | Flag file with `file:line` error location. Route to execution-infra for fix |
| Missing required field | FAIL | YES — blocks pipeline | Flag with specific field name(s). Route to execution-infra |
| Naming violation (breaks auto-loading) | FAIL | YES — blocks pipeline | E.g., `skill.md` instead of `SKILL.md` prevents CC discovery |
| Naming violation (cosmetic) | WARNING | NO — non-blocking | E.g., underscore in agent name. Include in report for cleanup |
| Orphan file/directory | WARNING | NO — non-blocking | Include in L2 for cleanup recommendation |
| Missing optional field | INFO | NO — non-blocking | Note in L2 report, no action required |

### Pipeline Impact Rules

```
IF any FAIL findings:
  overall_status = FAIL
  Route to execution-infra with fix requests
  Pipeline blocked at verify stage
ELIF only WARNING findings:
  overall_status = PASS (with warnings)
  Proceed to verify-content
  Include warnings in L2 for future cleanup
ELIF only INFO or no findings:
  overall_status = PASS
  Proceed to verify-content
```

---

## Anti-Patterns

| Rule | Rationale |
|------|-----------|
| DO NOT attempt programmatic YAML parsing | Analysts have no YAML parser tool. Use heuristic checks (indentation, colons, quoting). Accept the limitation. |
| DO NOT modify files during verification | Verify is strictly read-only. All fixes route through execution-infra skill. |
| DO NOT check L2 body content | Content quality is verify-content's responsibility, not structure's. Only check that body EXISTS below frontmatter. |
| DO NOT validate field values | Structure checks field PRESENCE, not value correctness. Value semantics are verified by verify-content and verify-cc-feasibility. |
| DO NOT scan outside `.claude/` directory | Scope is strictly `.claude/` components. Source code structure is not this skill's concern. |
| DO NOT block pipeline on naming warnings | Only YAML parse failures and missing required fields are blocking (FAIL). Naming cosmetics are WARNING-level only. |

---

## Quality Gate

### Pass Criteria

| Criterion | Check Method | Threshold |
|-----------|-------------|-----------|
| YAML frontmatter parses without heuristic errors | All files pass heuristic YAML checks | 100% of files |
| Required fields present and non-empty | Field presence check per file type table | 100% of files |
| Naming conventions match regex patterns | Regex validation per component type | 100% of files (FAIL-level only) |
| No orphaned files or empty directories | Directory tree scan | 0 orphans |
| Expected file counts match CLAUDE.md | Compare Glob results vs declared counts | agents: 6, skills: 35, hooks: 5 |
| No unexpected top-level `.claude/` files | Inventory check | Only known files/dirs present |

### Overall Verdict Logic

```yaml
PASS: All criteria met. No FAIL findings. Warnings acceptable.
FAIL: Any FAIL-level finding present. Pipeline blocked.
      Must include: file path, error type, line number (if applicable),
      suggested remediation, route target (execution-infra or execution-code).
```

---

## Output

### L1
```yaml
domain: verify
skill: structure
status: PASS|FAIL
total_files: 0
pass: 0
fail: 0
warnings: 0
findings:
  - file: ""
    check: frontmatter|required-fields|naming|directory
    status: PASS|FAIL|WARNING
    detail: ""
```

### L2
- File inventory with PASS/FAIL/WARNING per check
- Structural issues with file:line evidence
- Expected vs actual file counts comparison
- Orphan/empty directory report (if any)
- Naming violation details with regex pattern reference
- Next: verify-content (if PASS)
