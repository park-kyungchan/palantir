---
name: verify-structural-content
description: >-
  Inspects file structure and content quality: required metadata
  fields, naming conventions, section completeness, and description
  utilization. First of four sequential verify stages: structure,
  consistency, quality, cc-feasibility. Use after execution-review
  PASS or any file creation or modification requiring structural
  validation. Reads from execution-review PASS verdict and
  implementation artifacts. Produces structure and content scores
  per file for verify-consistency on PASS, or routes to the relevant
  execution skill on FAIL. On FAIL, routes file path + error location
  + suggested fix. Scores 0-100 per file: structure (parse validity,
  required fields, naming, directory compliance) + content
  (utilization %, key presence, body section presence, format).
  DPS-parameterized: caller specifies artifact type, required fields,
  naming rules, and declared counts. Default scope: .claude/ INFRA
  files (skills, agents, hooks). TRIVIAL: Lead-direct on 1-3 files.
  STANDARD: 1 analyst maxTurns 25. COMPLEX: 2 analysts — structural
  vs content split. DPS context: Glob results + DPS-declared counts.
  Exclude files outside DPS-specified scope.
user-invocable: true
disable-model-invocation: true
---

# Verify — Structural Content (Unified)

## Execution Model
- **TRIVIAL**: Lead-direct. Quick check on 1-3 files. Read files directly, validate frontmatter and content inline.
- **STANDARD**: Spawn 1 analyst (maxTurns: 25). Systematic structural + content check on 4-15 files.
- **COMPLEX**: Spawn 2 analysts (maxTurns: 30 each). Analyst-A: structural checks. Analyst-B: content checks. 16+ files.

---

## Decision Points

### Tier Classification

| Tier | File Count | Scope | Analyst Spawn |
|------|-----------|-------|---------------|
| TRIVIAL | 1-3 files | Spot-check structure + descriptions | None (Lead-direct) |
| STANDARD | 4-15 files | Full structural + content audit | 1 analyst |
| COMPLEX | 16+ files or full INFRA | All skills + agents | 2 analysts (structure / content) |

### Scope Decision

Full scan (major restructuring / new release / first-time setup). Targeted scan (specific file change — still validate cross-references). Skip when ALL hold: no `.claude/` files created/deleted, L2-body-only changes (no frontmatter), no directory changes, only hook `.sh` or non-`.claude/` files changed. If ANY frontmatter field changed: verification REQUIRED.

### Utilization Threshold

- Utilization ≥80%: PASS
- Utilization 70-80% AND all 5 orchestration keys present: WARN
- Utilization 70-80% AND missing keys: FAIL
- Utilization <70%: FAIL regardless of key presence

### Body Section Requirements by Skill Type

| Skill Type | Required Sections | Optional |
|---|---|---|
| Pipeline (P0-P7) | Execution Model, Methodology, Quality Gate, Output | Decision Points, Anti-Patterns, Transitions |
| Verify (P7) | Execution Model, Methodology, Quality Gate, Output | DPS templates |
| Homeostasis | Execution Model, Methodology, Quality Gate, Output | Scope Boundary, Error Handling |
| Cross-cutting | Execution Model, Operations/Methodology, Quality Gate, Output | Fork Execution |

**Known Limitation**: Analysts use heuristic YAML validation only (no parser tool). Edge cases: tab/space mixing (HIGH risk), embedded colons in values (MEDIUM), nested YAML 3+ levels (MEDIUM).

---

## Methodology

5-step execution. For full templates, section format examples, and structure check algorithms, read `resources/methodology.md`.

1. **Inventory** — Glob `.claude/` components; compare counts against CLAUDE.md declarations (agents: 8, skills: 48, hooks: 16)
2. **Structural Checks** — Per-file: YAML parseability, required fields, naming conventions, directory compliance
3. **Content Checks** — Per-file: description utilization %, orchestration keys (WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY), body section headings, L1/L2 format
4. **Combined Scoring** — Structure score (0-100) + content score (0-100). FAIL if either < 50. PASS requires avg utilization >80% and no file <60%.
5. **Report** — Per-file scores with PASS/FAIL/WARN; overall verdict; routes FAIL to execution-infra with file:line evidence

> For DPS construction details, inclusion/exclusion rules, and per-failure sub-cases: read `resources/methodology.md`

---

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|---|---|---|
| execution-review | All PASS verdict, implementation artifacts ready | L1 YAML: `status: PASS`, changed file paths list |
| Direct user invocation | Manual verification request | `/verify-structural-content` with optional target path |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| verify-consistency | Structural + content integrity confirmed | PASS verdict — all files structurally sound and content complete |
| execution-infra | Fix instructions for .claude/ files | FAIL verdict on `.claude/` files |

### Failure Routes

All FAIL-level findings route to **execution-infra** with: file path + error type + line location + suggested fix. Data per type: YAML corruption → error location; missing fields → field list; naming violation → expected pattern; missing keys → key list; missing sections → section list; low utilization → char count + target.

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

---

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| Analyst tool error or timeout during scan | L0 Retry | Re-invoke analyst with same DPS and file list |
| Analyst output missing scores or incomplete coverage | L1 Nudge | SendMessage with refined scope + scoring rubric reminder |
| Analyst exhausted turns, context polluted mid-scan | L2 Respawn | Kill analyst → spawn fresh with refined DPS, reduced scope |
| Tier misclassification discovered (split wrong) | L3 Restructure | Reclassify tier → resplit analyst ownership |
| 3+ L2 failures or verify pipeline strategy unclear | L4 Escalate | AskUserQuestion with situation summary + options |

### Severity Classification

**FAIL (blocking)**: YAML parse failure, missing required field, naming violation (auto-loading breaks, e.g. `skill.md` not `SKILL.md`), missing orchestration keys, missing required body sections, critical utilization (<70%), empty L1/L2 templates.

**WARNING (non-blocking)**: Cosmetic naming violation (e.g. underscore), below-target utilization (70-80%) with all 5 keys, missing optional sections, orphan file/directory.

**INFO**: Missing optional field — note in L2, no action.

---

## Anti-Patterns

| Rule | Rationale |
|------|-----------|
| DO NOT attempt programmatic YAML parsing | Analysts have no YAML parser tool. Use heuristic checks. |
| DO NOT modify files during verification | Verify is strictly read-only. All fixes route through execution-infra. |
| DO NOT validate field VALUES or semantic quality | Structure checks field PRESENCE. Content checks key PRESENCE only. |
| DO NOT verify cross-references here | Bidirectionality checking is verify-consistency's job. |
| DO NOT read full L2 bodies for content quality | Only check L2 section HEADINGS exist, not content quality. |
| DO NOT scan outside `.claude/` directory | Scope is strictly `.claude/` components. |
| DO NOT block pipeline on naming warnings | Only YAML failures, missing required fields, and missing keys are blocking. |
| DO NOT penalize short descriptions that are complete | 750-char with all 5 keys is better than 1000-char missing WHEN. |
| DO NOT treat agent files same as skill files | Agents require only name + description. No METHODOLOGY key required. |

---

## Quality Gate

PASS = all criteria met, no FAIL findings (warnings acceptable). FAIL = any FAIL-level finding — pipeline blocked. FAIL output includes: file path, error type, line number, structure+content scores, suggested remediation.

| Criterion | Threshold |
|-----------|-----------|
| YAML frontmatter heuristic check | 100% of files |
| Required fields present and non-empty | 100% of files |
| Naming conventions (FAIL-level violations) | 0 violations |
| No orphaned files or empty directories | 0 orphans |
| Expected file counts match CLAUDE.md | agents: 8, skills: 48, hooks: 16 |
| Average description utilization | >80% across all files, no file <60% |
| All 5 orchestration keys present | All skills |
| Required body sections present | Execution Model, Methodology, Quality Gate, Output |
| L1/L2 output format defined | Both present in Output section |

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

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
missing_keys_count: 0
missing_sections_count: 0
warnings: 0
signal_format: "{STATUS}|files:{N}|pass:{N}|ref:tasks/{team}/p7-structural-content.md"
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
- File inventory (expected vs actual counts), per-file combined report: structure + content scores + PASS/FAIL/WARN
- Structural issues with file:line evidence, utilization rankings with improvement suggestions
- Missing orchestration keys and body sections per file, orphan/empty directory report
- Overall PASS/FAIL verdict with routing recommendation. Next: verify-consistency (if PASS)
