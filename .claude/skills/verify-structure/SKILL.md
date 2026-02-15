---
name: verify-structure
description: |
  [P8·Verify·Structure] File-level structural integrity verifier. Checks file existence, YAML frontmatter parse-ability, directory structure compliance, and naming conventions for all .claude/ components.

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

## Methodology

### 1. Inventory All Files
Use Glob to discover:
- `.claude/agents/*.md` — agent definition files
- `.claude/skills/*/SKILL.md` — skill definition files
- `.claude/settings.json`, `.claude/hooks/*`, `.claude/CLAUDE.md`

### 2. Validate YAML Frontmatter
For each agent and skill file:
- Parse YAML between `---` markers
- Check parsing succeeds without errors
- Report parse failures with file:line location

**Known Limitation**: Analysts perform visual/heuristic YAML validation (indentation, colons, quoting). No programmatic YAML parser available. Subtle syntax errors may pass verification.

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: List of all discovered files from Step 1 (Glob results). Include expected directory structure: agents in `.claude/agents/*.md`, skills in `.claude/skills/*/SKILL.md`.
- **Task**: "For each file: (1) Read and parse YAML between --- markers, (2) Check required fields (name, description present and non-empty; skills: user-invocable present), (3) Verify naming (lowercase-hyphen for agents/dirs, SKILL.md uppercase for files), (4) Check directory structure (no orphans, no empty dirs). Report per-file PASS/FAIL with file:line evidence."
- **Constraints**: Read-only. Use Read to examine each file. No modifications. Note: YAML validation is heuristic (no parser tool) — check for common errors (missing colons, bad indentation, unclosed quotes).
- **Expected Output**: L1 YAML with total_files, pass, fail, findings[] (file, check, status). L2 per-file structural integrity report.

### 3. Check Required Fields
For each parsed frontmatter:
- `name` field present and non-empty
- `description` field present and non-empty
- Skill-specific: `user-invocable` field present

### 4. Verify Naming Conventions
- Agent files: lowercase with hyphens (e.g., `infra-implementer.md`)
- Skill directories: lowercase with hyphens (e.g., `execution-code/`)
- Skill files: always named `SKILL.md` (uppercase)

### 5. Check Directory Structure
- No orphan files in `.claude/skills/` (files outside skill dirs)
- No empty skill directories (dir without SKILL.md)
- Agent files directly under `.claude/agents/`

## Quality Gate
- All files have valid YAML frontmatter
- All files have required fields
- Naming conventions followed consistently
- No structural anomalies

## Output

### L1
```yaml
domain: verify
skill: structure
status: PASS|FAIL
total_files: 0
pass: 0
fail: 0
findings:
  - file: ""
    check: frontmatter|naming|directory
    status: PASS|FAIL
```

### L2
- File inventory with PASS/FAIL per check
- Structural issues with file:line evidence
- Next: verify-content (if PASS)
