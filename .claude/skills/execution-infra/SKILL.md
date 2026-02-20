---
name: execution-infra
description: >-
  Deploys infra-implementers for .claude/ files with Write/Edit
  only, no Bash. Validates YAML/JSON post-completion, handles
  failures with max 3 retries. Parallel with execution-code. Use
  after orchestrate-coordinator complete with PASS and infra
  tasks assigned in unified plan. Reads from
  orchestrate-coordinator unified execution plan L3 with infra
  task assignments and .claude/ file paths. Produces infra change
  manifest and config change summary for execution-impact and
  execution-review. All spawns model:sonnet. On FAIL, routes to
  execution-review with partial infra manifest and schema
  violations noted. DPS needs orchestrate-coordinator infra
  task_id/files/change_type + CC native fields ref. Exclude
  source code context and non-.claude/ implementation details.
user-invocable: true
disable-model-invocation: true
---

# Execution — Infra

## Execution Model
- **TRIVIAL**: Lead-direct. Single infra-implementer for 1-2 config files.
- **STANDARD**: Spawn 1 infra-implementer (maxTurns:20). Systematic .claude/ changes.
- **COMPLEX**: Spawn 2 infra-implementers (maxTurns:30). Each owns non-overlapping .claude/ subtrees.

## Decision Points

### Tier Classification
- **TRIVIAL**: Single .claude/ file, simple field update (e.g., description, model field), no cross-file references affected
- **STANDARD**: 2-4 .claude/ files in same directory, related changes sharing a pattern
- **COMPLEX**: 5+ .claude/ files across multiple directories (skills + agents + settings + hooks), structural changes (new skill, agent rewiring, hook modification)

### Spawn vs Lead-Direct
- **Lead-direct**: NEVER for infra changes. Lead has no Edit/Write tools per CLAUDE.md constitution.
- **Spawn infra-implementer** (always): Even single-field changes require a spawn — hard architectural constraint.
- **Key constraint**: Infra-implementers have NO Bash. Cannot run `yamllint`/`jq`. Schema validation is Lead's responsibility after completion.

### Input Validation Before Proceeding
Before spawning, verify:
1. orchestrate-coordinator L1 shows `status: PASS` for infra assignments
2. Target file paths exist (modifications) or parent directories exist (creation)
3. Frontmatter changes: verify field names against CC native fields (`ref_agents.md` §2)
4. settings.json changes: verify JSON key path exists or is valid new addition
5. No `.claude/` file appears in multiple infra-implementer assignments

If validation fails: route back to orchestrate-coordinator with specific failure reason.

### Parallel vs Sequential
- **Parallel** (default): Infra-implementers modify non-overlapping files in different `.claude/` subdirectories
- **Sequential**: Changes have reference dependencies (e.g., create skill → update CLAUDE.md reference)
- **Always sequential**: settings.json changes run LAST (references agents/skills that must exist first)

### Scope Boundary (Inviolable)
This skill handles ONLY `.claude/` directory files:
- `.claude/agents/*.md` — agent definition files
- `.claude/skills/*/SKILL.md` — skill definition files
- `.claude/settings.json` — project settings
- `.claude/hooks/*.sh` — hook scripts (Edit only, no Bash execution)
- `.claude/CLAUDE.md` — team constitution
- `.claude/projects/*/memory/*.md` — memory files

Files outside `.claude/` MUST route to execution-code.

## Methodology

### 1. Read Validated Assignments
Load orchestrate-coordinator PASS report for infra tasks.
Extract `.claude/` file assignments: agents, skills, settings, hooks, CLAUDE.md.

### 2. Spawn Infra-Implementers
For each infra task group, create Task with `subagent_type: infra-implementer`.

Construct each DPS with (D11 — cognitive focus first):
- **INCLUDE**: Exact `.claude/` file paths. For frontmatter changes: which YAML fields to add/modify/remove with exact values. CC native fields ref at `ref_agents.md` §2.
- **EXCLUDE**: Source code details. Other implementers' tasks. Historical rationale. Non-.claude/ pipeline context.
- **Task field**: Precise per-file change description with before→after for field values. Include one completed example for STANDARD/COMPLEX patterns.
- **Constraints field**: Write/Edit tools only — no Bash. Cannot delete files. `description` ≤1024 chars. YAML/JSON must remain valid. No non-native frontmatter fields.
- **Delivery (2-channel)**: Ch2 → `{work_dir}/p6-infra-{task_id}-output.md`; Ch3 → micro-signal to Lead `"PASS|files:{N}|ref:{work_dir}/p6-infra-{task_id}-output.md"`.

> For tier-specific DPS variations (context inclusions, maxTurns per tier): read `resources/methodology.md`

### 3. Monitor Progress
Read infra-implementer completion summary from output file.
Verify YAML frontmatter remains valid. Track file count vs expected.

> For monitoring heuristics table (schema violation, overflow, JSON corruption signals): read `resources/methodology.md`

### 4. Validate Schema Compliance
After each infra-implementer completes:
- Check YAML frontmatter parses correctly
- Verify required fields preserved (`name`, `description`)
- Confirm no non-native fields introduced

### 5. Consolidate Results
Collect L1 YAML from each implementer. Build unified infra change manifest. Report to execution-review.

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.execution_infra: N` in PT before each invocation
- Iteration 1-2: strict mode (FAIL → return to execution-review for re-assessment)
- Iteration 3+: auto-PASS with documented gaps; L4 escalate if critical findings remain
- Max iterations: 2

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error, write failure, file lock | L0 Retry | Re-invoke same infra-implementer with same DPS |
| YAML invalid or non-native fields | L1 Nudge | Respawn with refined DPS targeting CC native fields ref + correction |
| Schema corruption or context exhausted | L2 Respawn | Kill → fresh infra-implementer with original content + corrective DPS |
| settings.json corrupted, blocking all infra | L3 Restructure | Restore from backup, reassign settings.json as last sequential task |
| All retries failed, architectural schema conflict | L4 Escalate | AskUserQuestion with situation summary + options |

- **Partial changes applied**: Route to execution-review for assessment of partial infra state
- **No changes possible**: Report to Lead for alternative approach or manual intervention
- **Pipeline impact**: Non-blocking for code pipeline. If infra changes are code prerequisites, Lead re-sequences

## Anti-Patterns

### DO NOT: Assume Infra-Implementer Has Bash
Infra-implementers have Read, Glob, Grep, Edit, Write, and sequential-thinking only. Do not include "run `yamllint`" or "verify with `jq`" in DPS. Schema validation is Lead's responsibility post-completion.

### DO NOT: Assign Non-.claude/ Files to Infra-Implementer
Application source code (Python, TypeScript, etc.) must go through execution-code. Infra-implementers lack the Bash tool needed for testing source code changes.

### DO NOT: Edit settings.json in Parallel
settings.json is a single shared file. Last-write-wins semantics will corrupt earlier changes. Always assign to exactly one infra-implementer, sequenced last.

### DO NOT: Create Skills Without Full Frontmatter
Every new SKILL.md requires: `name`, `description` (≤1024 chars), `user-invocable`, `disable-model-invocation`. Missing fields break Lead's L1 routing. DPS must specify all required fields explicitly.

### DO NOT: Modify Hook Logic Without Understanding Execution Context
Hook `.sh` files execute in specific contexts (PreToolUse, PostToolUse, SubagentStop). Editing hook logic requires understanding the event type and matcher conditions. See `resources/methodology.md` for hook script conventions.

### DO NOT: Change Agent Memory Settings Casually
Agent `memory` field (`project` vs `none`) affects context received. Changing from `project` to `none` removes MEMORY.md and cc-reference access. Only change with explicit architectural reasoning.

## Phase-Aware Execution

All modes. Communication via 2-channel protocol (Ch2 disk + Ch3 micro-signal to Lead). File ownership: only modify assigned files. No overlapping edits with parallel subagents.

> D17 Note: Two-Channel protocol — Ch2 output file in work directory, Ch3 micro-signal to Lead.
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`
> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestrate-coordinator | Unified execution plan with infra task assignments | L1 YAML: `tasks[].{task_id, files[], change_type}` |
| plan-relational | Interface contracts for infra components (if applicable) | L2 markdown: field specifications, schema requirements |
| design-architecture | Component structure for new skill/agent creation | L2 markdown: domain assignment, routing requirements |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-impact | Infra file change manifest | Always (even if partial). SRC hook auto-triggers for .claude/ changes. |
| execution-review | Infra change artifacts + L1/L2 per implementer | After all infra-implementers complete |
| validate-syntactic | Modified .claude/ files for structural+content validation | Via execution-review routing |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| YAML frontmatter corruption | Re-spawn infra-implementer | Original file content + error location |
| JSON settings corruption | Re-spawn infra-implementer | Original settings.json backup + error details |
| Non-native fields | Re-spawn with CC native fields reference | List of non-native fields to remove |
| File not found | orchestrate-coordinator | Missing file path, expected location |
| All retries failed | execution-review (FAIL) | Failed tasks, error logs, impact assessment |

## Quality Gate
- All assigned `.claude/` files modified correctly
- YAML frontmatter valid in all modified files
- No non-native fields introduced
- settings.json remains valid JSON

## Output

### L1
```yaml
domain: execution
skill: infra
status: complete|in-progress|failed
files_changed: 0
implementers: 0
pt_signal: "metadata.phase_signals.p6_infra"
signal_format: "{STATUS}|files:{N}|implementers:{N}|ref:{work_dir}/p6-infra.md"
```

### L2
- Infra change manifest per implementer
- Configuration change summary
- Schema validation results
