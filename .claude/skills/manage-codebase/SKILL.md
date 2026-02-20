---
name: manage-codebase
description: >-
  Analyzes project source files for tech debt, dead code, and refactoring
  opportunities outside the .claude/ INFRA directory. Executes automated
  cleanup and refactoring with test verification. Distinct from manage-infra
  (which targets .claude/ files) and self-implement (which applies RSIL
  improvements to INFRA). Use when codebase health audit identifies source
  files needing cleanup, or when user requests project file maintenance.
  Reads from project directory structure and test suite results. Produces
  refactoring report with before/after diff and test pass confirmation.
  On FAIL (tests fail after refactor), reverts change and reports to Lead.
  TRIVIAL: Lead-direct for single file. STANDARD: 1 implementer (maxTurns:
  30). COMPLEX: 2 implementers split by module. DPS needs project root path,
  target file patterns, and test command. Exclude .claude/ directory.
user-invocable: true
disable-model-invocation: true
argument-hint: "[project_root] [--target=pattern] [--test-cmd=command]"
---

# Manage — Codebase

## Execution Model
- **TRIVIAL**: Lead-direct. Single file cleanup, no spawn. Apply Edit inline, verify manually.
- **STANDARD**: Spawn 1 implementer (maxTurns:30). 3–10 files, 1–2 modules.
- **COMPLEX**: Spawn 2 implementers (maxTurns:30 each). Split by module/domain boundary.

## Phase-Aware Execution
Runs outside the linear pipeline (homeostasis). Team mode applies when called in P2+ context.
- Two-Channel Protocol: Ch2 (disk file) + Ch3 (micro-signal to Lead)
- Write to `tasks/{work_dir}/homeostasis-manage-codebase.md`. Micro-signal: `{STATUS}|files:{N}|reverted:{R}|ref:tasks/{work_dir}/homeostasis-manage-codebase.md`.
- For phase-aware routing details: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### Refactor vs. Report Only
- **Refactor** (default): Tests exist and pass before any changes. Scope is ≤10 files. No cross-module renames.
- **Report only**: No test suite available, or scope exceeds 10 files. List candidates with severity for user decision.

### Scope Determination
- User provides `--target=pattern` → restrict Glob to that pattern.
- No pattern → scan all source files in project root excluding `.claude/`, `node_modules/`, `.git/`, `dist/`, `build/`.
- File count >30 → split by top-level directory and assign one implementer per segment (COMPLEX tier).

### Safety Gate (Pre-Execution Check)
Before applying any change: verify test command runs successfully on unmodified code.
If baseline tests fail → abort, report in L1 as `tests_passed: false`, `files_refactored: 0`.

## Methodology

### Step 1: Scan
Glob project source files (`.ts`, `.tsx`, `.js`, `.py`, `.html`, `.css`, and user-specified patterns).
Exclude: `.claude/`, `node_modules/`, `.git/`, `dist/`, `build/`, `coverage/`, binary files.
Flag candidates meeting any threshold: file >800 lines, duplicate function signature patterns, unreachable exports.
> For language-specific detection patterns and tech debt criteria: read `resources/methodology.md`

### Step 2: Analyze
Read each candidate file. Assess:
- **Dead code**: Unexported symbols with zero cross-file references.
- **Large files**: Files >800L that can be split by cohesion boundary.
- **Duplicate patterns**: Repeated code blocks (>10 identical lines across files).
- **Risk**: Files with >5 importers have high blast radius — flag for report-only unless isolated.
> For risk scoring matrix and blast-radius calculation: read `resources/methodology.md`

### Step 3: Plan
Produce a change plan listing each action:
- `DELETE {symbol}` — dead code removal
- `EXTRACT {symbol} → {new_file}` — split large file
- `INLINE {call_site}` — remove unnecessary abstraction
- `RENAME {old} → {new}` — clarity improvement
Confirm with user before executing changes in report-only mode.

### Step 4: Execute
Apply changes file-by-file using Edit (targeted changes) or Write (rewrites).
After each file: read back to verify edit applied correctly. Log original content for revert.
Never touch `.claude/` directory — scope enforcement is mandatory.

### Step 5: Test
Run the test command provided in DPS. If `--test-cmd` not supplied, use auto-detected command
(`pnpm test`, `npm test`, `pytest`, in that priority order).
- **Pass**: Record `tests_passed: true`. Commit changes.
- **Fail**: Restore original content (Write original back to each modified file). Record `files_reverted: N`.
> For revert procedure and test runner auto-detection logic: read `resources/methodology.md`

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| Glob timeout or partial read | L0 Retry | Re-invoke same implementer with same DPS |
| Test fail after refactor | L1 Nudge | Revert changes → narrow scope to 1 file, retry |
| Implementer stuck or maxTurns exhausted | L2 Respawn | Kill → fresh implementer with reduced file set |
| Multiple modules fail repeatedly | L3 Restructure | Switch to report-only mode, generate candidate list |
| 3+ L2 failures or scope structurally blocked | L4 Escalate | AskUserQuestion with partial findings and options |

- **No test suite**: Immediately switch to report-only mode. Never refactor without tests.
- **Scope exceeds 30 files**: Pause, split into waves (max 10 files per wave), await user approval.
- **Pipeline impact**: Non-blocking (homeostasis). Partial report is actionable.
- For escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

### DO NOT: Refactor Without a Passing Test Baseline
If tests fail before any changes, the codebase state is unknown. Applying refactors compounds the problem. Always confirm baseline test pass before executing Step 4.

### DO NOT: Touch .claude/ Directory Files
manage-codebase scope is project source code only. .claude/ files are managed by manage-infra and execution-infra. Scope violation = immediate abort.

### DO NOT: Auto-Apply High-Blast-Radius Changes
Files imported by 5+ other files require manual user review. Auto-refactoring these risks cascading breakage across modules. Flag for report-only even when tests exist.

### DO NOT: Apply Multiple Refactoring Types in One Pass
Mix of DELETE + EXTRACT + RENAME in a single pass makes revert ambiguous. Apply one type per implementer turn, test after each type, then proceed.

### DO NOT: Confuse Roles
- **manage-codebase**: Project source files (TypeScript, Python, HTML, etc.)
- **manage-infra**: .claude/ INFRA files (skills, agents, hooks, resources)
- **self-implement**: Applying RSIL-generated improvements to INFRA

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| self-diagnose | Tech debt item list from Category 8 (code quality) | L1 YAML with file paths and issue types |
| (user-invoked) | Project root, target pattern, test command | CLI arguments via $ARGUMENTS |
| delivery-pipeline | Post-delivery cleanup request | L1 YAML with changed file manifest |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (user) | Refactoring report with before/after diff and test confirmation | Always (terminal) |
| manage-infra | Notification if .claude/ references in source files are discovered | When cross-boundary references found |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Tests fail after refactor | (user) | Revert confirmation + original failure diff |
| No test suite detected | (user) | Report-only candidate list with severity |
| Scope exceeds safe threshold | (user) | Candidate list with blast-radius scores |

> D17 Note: Two-Channel protocol — use 2-channel protocol.
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
1. All modified files pass test suite after refactoring (or reverted to original state on fail).
2. Zero .claude/ directory files modified (scope boundary enforced).
3. Baseline test pass confirmed before any refactoring applied.
4. Each refactored file read-back verified after Edit/Write.
5. L1 output includes accurate counts: `files_scanned`, `files_refactored`, `files_reverted`, `tech_debt_items`.

## Output

### L1
```yaml
domain: homeostasis
skill: manage-codebase
status: PASS|FAIL
files_scanned: 0
files_refactored: 0
files_reverted: 0
tech_debt_items: 0
tests_passed: true|false
pt_signal: "metadata.phase_signals.homeostasis"
signal_format: "{STATUS}|files:{N}|reverted:{R}|ref:tasks/{work_dir}/homeostasis-manage-codebase.md"
```

### L2
- Tech debt scan results (candidates per category: dead code, large files, duplicates)
- Per-file refactoring plan with action type and rationale
- Before/after diff summary for each modified file
- Test execution results (pass/fail per test file, total count)
- Revert log if any files were restored (file path + reason)
