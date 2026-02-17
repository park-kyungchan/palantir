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
  execution-review.
user-invocable: true
disable-model-invocation: false
metadata:
  category: execution
  tags: [infra-implementation, config-deployment, yaml-validation]
  version: 2.0.0
---

# Execution — Infra

## Execution Model
- **TRIVIAL**: Lead-direct. Single infra-implementer for 1-2 config files.
- **STANDARD**: Spawn 1 infra-implementer. Systematic .claude/ changes.
- **COMPLEX**: Spawn 2 infra-implementers. Each owns non-overlapping .claude/ subtrees.

## Decision Points

### Tier Classification for Infra Execution
Lead determines tier based on orchestration-verify output:
- **TRIVIAL indicators**: Single .claude/ file change, simple field update (e.g., update a description, change a model field), no cross-file references affected
- **STANDARD indicators**: 2-4 .claude/ files across same directory (e.g., 3 skills in same domain), related changes that share a pattern (e.g., adding INPUT_FROM to multiple skills)
- **COMPLEX indicators**: 5+ .claude/ files across multiple directories (skills + agents + settings + hooks), structural changes (new skill creation, agent rewiring, hook modification)

### Spawn vs Lead-Direct Decision
- **Lead-direct**: NEVER for infra changes. Lead has no Edit/Write tools per CLAUDE.md constitution.
- **Spawn infra-implementer** (always): Even single-field changes require an infra-implementer spawn. This is a hard architectural constraint.
- **Key difference from execution-code**: Code implementers have Bash for testing; infra-implementers do NOT have Bash. They cannot validate their changes by running commands. Lead must verify schema compliance post-completion.

### Input Validation Before Proceeding
Before spawning infra-implementers, verify:
1. orchestration-verify L1 shows `status: PASS` for infra assignments
2. All target file paths exist (for modifications) or parent directories exist (for creation)
3. For frontmatter changes: verify field names against CC native fields list (.claude/projects/-home-palantir/memory/ref_agents.md, Section 2: Frontmatter Fields)
4. For settings.json changes: verify the JSON key path exists or is a valid new addition
5. No .claude/ file appears in multiple infra-implementer assignments

If validation fails: route back to orchestration-verify with specific failure reason.

### Parallel vs Sequential Infra Spawning
- **Parallel** (default): When infra-implementers modify non-overlapping files in different .claude/ subdirectories
- **Sequential**: When changes have reference dependencies (e.g., creating a new skill then updating CLAUDE.md to reference it, or updating agent file then modifying settings.json permission for that agent)
- **Always sequential**: Any change to settings.json should be the LAST infra-implementer to run (settings references agents/skills that must exist first)

### Scope Boundary Enforcement
This skill handles ONLY `.claude/` directory files:
- `.claude/agents/*.md` -- agent definition files
- `.claude/skills/*/SKILL.md` -- skill definition files
- `.claude/settings.json` -- project settings
- `.claude/hooks/*.sh` -- hook scripts (Edit only, no Bash execution)
- `.claude/CLAUDE.md` -- team constitution
- `.claude/projects/*/memory/*.md` -- memory files

Files outside `.claude/` MUST route to execution-code instead. This boundary is inviolable.

## Methodology

### 1. Read Validated Assignments
Load orchestration-verify PASS report for infra tasks.
Extract .claude/ file assignments: agents, skills, settings, hooks, CLAUDE.md.

### 2. Spawn Infra-Implementers
For each infra task group:
- Create Task with `subagent_type: infra-implementer`

Construct each delegation prompt with:
- **Context**: List exact `.claude/` file paths to modify (e.g., `.claude/skills/foo/SKILL.md`, `.claude/agents/bar.md`). For frontmatter changes, specify which YAML fields to add/modify/remove and their exact values. Reference CC native field list at `.claude/projects/-home-palantir/memory/ref_agents.md` (Section 2: Frontmatter Fields) for valid fields.
- **Task**: For each file, describe the precise change: "In `.claude/skills/X/SKILL.md`, update the `description` field to include INPUT_FROM/OUTPUT_TO references" or "Add `model: haiku` to `.claude/agents/Y.md` frontmatter." For description edits, provide the new text or the specific substring to replace.
- **Constraints**: Write and Edit tools only — NO Bash (cannot run shell commands, cannot validate by execution). Cannot delete files. Skill `description` field max 1024 characters (count before writing). YAML frontmatter must remain valid. Settings.json must remain valid JSON. Do not introduce non-native frontmatter fields.
- **Expected Output**: Report completion as L1 YAML with `files_changed` (array of paths), `status` (complete|failed). Provide L2 markdown listing each file modified, what changed (before→after for field values), and any issues encountered.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

#### Tier-Specific DPS Variations

**TRIVIAL DPS Additions:**
- Context: Include the FULL current content of the target file (infra files are typically small, <200 lines).
- Task: Specify exact field-level change: "In `.claude/skills/X/SKILL.md`, change `description` field line 4 from `old text` to `new text`". Include before/after for the specific field.
- Constraints: Single file modification only. If the change logically requires updating a second file, report it rather than modifying both.
- maxTurns: 10 (infra changes are precise, not exploratory)

**STANDARD DPS Additions:**
- Context: Include full content of all target files. For frontmatter changes, include the CC native fields reference for valid field names. For description changes, include the 1024-char budget constraint.
- Task: Describe the pattern to apply across files: "Add `INPUT_FROM: execution-code` and `OUTPUT_TO: execution-review` to the description field of each skill listed." Provide one completed example for the first file, then specify "Apply the same pattern to remaining files."
- Constraints: All files must be in `.claude/` scope. Maintain valid YAML in all frontmatter. Maintain valid JSON in settings.json. Description field ≤1024 characters.
- maxTurns: 20

**COMPLEX DPS Additions:**
- Context: Include all target files plus related files that provide context (e.g., when creating a new skill, include an existing skill in the same domain as a template). Include CLAUDE.md for reference counts that may need updating.
- Task: Describe structural intent: "Create new skill `.claude/skills/new-skill/SKILL.md` following the template of `existing-skill`. Then update `.claude/CLAUDE.md` skill count. Then update `.claude/settings.json` to add permission for the new skill."
- Constraints: Follow existing conventions exactly (frontmatter field order, markdown heading style, indentation). New files must have all required frontmatter fields: name, description, user-invocable, disable-model-invocation.
- maxTurns: 30

### 3. Monitor Progress
During implementation:
- Receive infra-implementer completion summary via SendMessage
- Verify YAML frontmatter remains valid after changes
- Track file count against expected changes

#### Monitoring Heuristics for Infra Changes
- **Healthy**: Infra-implementer reports files_changed matching expected count, no YAML parse errors
- **Schema violation**: Infra-implementer introduces non-native frontmatter field -- flag for correction
- **Description overflow**: Infra-implementer writes description >1024 chars -- L1 will be truncated, flag for trimming
- **JSON corruption**: settings.json edit breaks JSON syntax -- critical failure, must fix before any other changes
- **Cross-reference break**: Infra-implementer changes a skill/agent name without updating all references -- flag for cascade check via execution-impact

### 4. Validate Schema Compliance
After each infra-implementer completes:
- Check YAML frontmatter parses correctly
- Verify required fields preserved (name, description)
- Confirm no non-native fields introduced

### 5. Consolidate Results
After all infra-implementers complete:
- Collect L1 YAML from each
- Build unified infra change manifest
- Report to execution-review for validation

## Failure Handling
- **Retries exhausted**: Set skill `status: failed`, report failed files and error details in `blockers` array
- **Partial changes applied**: Route to execution-review for assessment of partial infra state
- **No changes possible** (e.g., schema conflict, invalid target): Report to Lead for alternative approach or manual intervention
- **Pipeline impact**: Non-blocking for code pipeline. If infra changes are prerequisites for code, Lead re-sequences

## Anti-Patterns

### DO NOT: Assume Infra-Implementer Has Bash
Infra-implementers have Read, Glob, Grep, Edit, Write, and sequential-thinking. They CANNOT run shell commands. Do not include instructions like "run `yamllint`" or "verify with `jq`" in their DPS prompts. Schema validation must be done by Lead after the implementer returns.

### DO NOT: Assign Non-.claude/ Files to Infra-Implementer
Application source code (Python, TypeScript, etc.) must go through execution-code with a regular implementer. Infra-implementers lack the Bash tool needed for testing source code changes.

### DO NOT: Edit settings.json in Parallel
settings.json is a single shared file. Never assign it to multiple infra-implementers simultaneously. Last-write-wins semantics will corrupt earlier changes. Always assign settings.json to exactly one infra-implementer, sequenced last.

### DO NOT: Create Skills Without Full Frontmatter
Every new SKILL.md requires: `name`, `description` (≤1024 chars with WHEN/DOMAIN/METHODOLOGY), `user-invocable`, `disable-model-invocation`. Missing fields break Lead's L1 routing. The infra-implementer DPS must specify all required fields explicitly.

### DO NOT: Modify Hook Logic Without Understanding Execution Context
Hook .sh files execute in specific contexts (PreToolUse, PostToolUse, SubagentStop). Editing hook logic requires understanding the event type, input format, and matcher conditions. See `memory/cc-reference/hook-events.md` for hook event specifications. When in doubt, route hook changes to a separate specialist review.

### DO NOT: Change Agent Memory Settings Casually
Agent `memory` field (`project` vs `none`) affects what context the agent receives. Changing from `project` to `none` removes access to MEMORY.md and cc-reference. Only change memory settings with explicit architectural reasoning.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestrate-coordinator | Unified execution plan with infra task assignments | L1 YAML: `tasks[].{task_id, files[], change_type}` |
| plan-interface | Interface contracts for infra components (if applicable) | L2 markdown: field specifications, schema requirements |
| design-architecture | Component structure for new skill/agent creation | L2 markdown: domain assignment, routing requirements |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-impact | Infra file change manifest | Always (even if partial). SRC hook auto-triggers for .claude/ changes. |
| execution-review | Infra change artifacts + L1/L2 per implementer | After all infra-implementers complete |
| verify-structural-content | Modified .claude/ files for structural+content validation | Via execution-review routing |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| YAML frontmatter corruption | Re-spawn infra-implementer with corrective prompt | Original file content + error location |
| JSON settings corruption | Re-spawn infra-implementer with JSON fix prompt | Original settings.json backup + error details |
| Schema non-compliance (non-native fields) | Re-spawn with CC native fields reference | List of non-native fields to remove |
| File not found (target doesn't exist) | orchestration-verify | Missing file path, expected location |
| All retries failed | execution-review (FAIL) | Failed tasks, error logs, impact assessment |

## Quality Gate
- All assigned .claude/ files modified correctly
- YAML frontmatter valid in all modified files
- No non-native fields introduced
- Settings.json remains valid JSON

## Output

### L1
```yaml
domain: execution
skill: infra
status: complete|in-progress|failed
files_changed: 0
implementers: 0
```

### L2
- Infra change manifest per implementer
- Configuration change summary
- Schema validation results
