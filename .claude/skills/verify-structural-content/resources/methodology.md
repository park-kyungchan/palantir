# Verify Structural Content — Detailed Methodology
> On-demand reference. Contains verification templates, section format examples, inventory targets, and structure check algorithms.

---

## 1. Inventory Target Files

Use Glob to discover all `.claude/` components.

**Expected File Counts** (validate against CLAUDE.md declarations):

| Component | Glob Pattern | Expected Count | Location |
|-----------|-------------|----------------|----------|
| Agent definitions | `.claude/agents/*.md` | 8 | Direct children of agents/ (7 pipeline + agent-organizer) |
| Skill definitions | `.claude/skills/*/SKILL.md` | 48 | One per skill directory (INFRA scope) |
| Settings | `.claude/settings.json` | 1 | .claude/ root |
| Constitution | `.claude/CLAUDE.md` | 1 | .claude/ root |
| Hook scripts | `.claude/hooks/*.sh` | 16 | Direct children of hooks/ (14 global + 2 MCP enforce) |
| Agent memory dirs | `.claude/agent-memory/*/` | varies | Per-agent persistent storage |
| Rules directory | `.claude/rules/*.md` | 0+ | Optional path-scoped rules |

**Expected Agent Files** (8 total):
- `analyst.md`, `researcher.md`, `coordinator.md`, `implementer.md`
- `infra-implementer.md`, `delivery-agent.md`, `pt-manager.md`, `agent-organizer.md`

**Expected Skill Directories**: Validate count matches CLAUDE.md §1 declarations (currently 48 INFRA across 10 domains + project skills). Cross-reference exact names with `l2-ce-pe-reference.md` Appendix.

---

## 2. Structural Integrity Checks (per file)

### A. YAML Frontmatter Parseability

Parse YAML between `---` markers. Check parsing succeeds without errors. Report parse failures with file:line location.

**Known Limitation**: Analysts perform visual/heuristic YAML validation (indentation, colons, quoting). No programmatic YAML parser available.

**Common YAML Errors** (heuristic detection):
- Missing colon (`key value` instead of `key: value`)
- Bad indentation (mixed tabs/spaces)
- Unclosed quotes
- Pipe scalar without newline (`|text` vs `|` + newline)
- Missing space after colon (`name:value`)
- Unquoted booleans in value fields
- Trailing content on `---` delimiter lines

### B. Required Fields Present

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

### C. Naming Conventions

| Component | Regex Pattern | Examples (Valid) | Examples (Invalid) |
|-----------|--------------|-----------------|-------------------|
| Agent files | `/^[a-z][a-z0-9-]*\.md$/` | `analyst.md`, `infra-implementer.md` | `Analyst.md`, `infra_impl.md` |
| Skill directories | `/^[a-z][a-z0-9-]*$/` | `execution-code`, `verify-structure` | `ExecutionCode`, `verify_structure` |
| Skill files | Must be exactly `SKILL.md` | `SKILL.md` | `skill.md`, `Skill.md` |
| Hook scripts | `/^[a-z][a-z0-9-]*\.sh$/` | `on-file-change.sh` | `onFileChange.sh` |
| Settings | Must be exactly `settings.json` | `settings.json` | `Settings.json` |

### D. Directory Structure Compliance

- No orphan files in skills/ (outside skill dirs)
- No empty skill dirs (missing SKILL.md)
- agents/ and hooks/ are flat dirs (no subdirs)
- No unexpected top-level .claude/ files
- Expected top-level: CLAUDE.md, settings.json, agents/, skills/, hooks/, agent-memory/, rules/, plugins/

---

## 3. Content Completeness Checks (per file)

### A. Description Utilization

Extract `description` field. Measure character count. Target: >80% of 1024 = >819 chars.

| Category | Utilization Range | Status |
|---|---|---|
| Excellent | >90% (>921 chars) | PASS |
| Good | 80-90% (819-921 chars) | PASS |
| Below Target | 70-80% (716-819 chars) | WARN (if all 5 keys present) or FAIL |
| Critical | <70% (<716 chars) | FAIL |

### B. Orchestration Key Extraction

Grep each description for `/^(WHEN|DOMAIN|INPUT_FROM|OUTPUT_TO|METHODOLOGY):/m`. All 5 must be present.

**Quality Assessment per Key:**

| Key | Quality Check | Good Example | Bad Example |
|---|---|---|---|
| WHEN | Specific trigger with upstream skill name | "After execution-code complete" | "When needed" |
| DOMAIN | Domain name + position + sequence | "execution (skill 1 of 5)" | "execution" |
| INPUT_FROM | Named skill + data type | "orchestrate-coordinator (validated matrix)" | "upstream" |
| OUTPUT_TO | Named skill + trigger condition | "verify domain (if PASS)" | "next phase" |
| METHODOLOGY | Numbered steps (1)-(5) with actions | "(1) Read assignments, (2) Spawn..." | "Analyze and report" |

### C. Body Sections Required by Skill Type

| Skill Type | Required Body Sections | Optional Body Sections |
|---|---|---|
| Pipeline skills (P0-P7) | Execution Model, Methodology, Quality Gate, Output | Decision Points, Anti-Patterns, Transitions |
| Verify skills (P7) | Execution Model, Methodology, Quality Gate, Output | DPS templates |
| Homeostasis skills | Execution Model, Methodology, Quality Gate, Output | Scope Boundary, Error Handling |
| Cross-cutting skills | Execution Model, Operations/Methodology, Quality Gate, Output | Fork Execution |

For each skill file with L2 body, check for required `##` headings: Execution Model, Methodology, Quality Gate, Output. Under Output, require `### L1` and `### L2` sub-headings.

### D. L1/L2 Output Format

- **L1**: YAML template with `domain`, `skill`, `status` fields (always required). `findings[]` required if FAIL.
- **L2**: Markdown bullet list describing content.
- Agent files: only `name` + `description` required. No METHODOLOGY key, no L2 body sections.

---

## 4. Combined Scoring Algorithm

For each file, compute two independent scores:

- **Structure score (0-100)**: YAML parseability (25) + required fields present (25) + naming conventions (25) + directory compliance (25)
- **Content score (0-100)**: description utilization (25) + orchestration keys (25) + body sections (25) + L1/L2 format (25)
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

---

## 5. DPS Construction for Analyst Spawn

For STANDARD/COMPLEX tiers, construct delegation prompt (DPS) for each analyst with:

**Context (D11 priority: cognitive focus > token efficiency):**

INCLUDE:
- Glob results — complete list of discovered .claude/ files
- CLAUDE.md declared counts (agents: 8, skills: 48 INFRA, hooks: 16)
- Common YAML errors checklist (tab/space mixing, missing colons, unclosed quotes, pipe scalar errors)
- Target thresholds: description >80% of 1024 chars, all 5 orchestration keys required (WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY)
- Body section requirements per skill type (pipeline/verify/homeostasis/cross-cutting)
- File paths within this analyst's ownership boundary

EXCLUDE:
- L2 body content (check section headings only, not content quality)
- Non-.claude/ source files
- Historical rationale for thresholds
- Other analyst's partial results when in 2-analyst split mode

Budget: Context field ≤ 30% of analyst effective context.

**Task**: "For each file: (1) Read and parse YAML between --- markers, check required fields present, (2) Verify naming conventions (lowercase-hyphen for agents/dirs, SKILL.md uppercase for files), (3) Check directory structure (no orphans, no empty dirs), (4) Measure description char count and utilization %, (5) Check for WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY keys in description, (6) Verify body has Execution Model, Methodology, Quality Gate, Output sections. Report per-file PASS/FAIL with structure+content scores."

**Constraints**: Read-only. Use Read to examine each file. No modifications. YAML validation is heuristic. Do NOT fix issues found.

**Expected Output**: L1 YAML with total_files, structure_pass, content_pass, findings[]. L2 per-file combined integrity report with structure score + content score.

**Delivery**: Micro-signal to Lead: `"{STATUS}|files:{total_files}|pass:{structure_pass}|ref:tasks/{work_dir}/p7-structural-content.md"`.

---

## 6. Failure Sub-cases

### Low Utilization File
- Flag with improvement suggestion (which orchestration keys to add or expand)
- Include current char count and target char count
- Severity: WARN if all 5 keys present and utilization >70%, FAIL otherwise

### Missing Orchestration Keys
- FAIL with specific missing keys listed per file
- Include which keys ARE present for context
- Route to `execution-infra` for description rewrite

### Pipeline Impact Rules
- FAIL → execution-infra (blocked), WARNING → PASS with warnings → verify-consistency, INFO → PASS → verify-consistency
- Same as Combined Scoring verdict logic
