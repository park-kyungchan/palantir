# Execution Infra — Detailed Methodology

> On-demand reference. Contains tier-specific DPS variations, monitoring heuristics, and
> configuration format notes for infra-implementer spawning.

## Tier-Specific DPS Variations

### TRIVIAL DPS Additions
- **Context**: Include the FULL current content of the target file (infra files are typically small, <200 lines).
- **Task**: Specify exact field-level change: "In `.claude/skills/X/SKILL.md`, change `description` field line 4 from `old text` to `new text`". Include before/after for the specific field.
- **Constraints**: Single file modification only. If the change logically requires updating a second file, report it rather than modifying both.
- **maxTurns**: 10 (infra changes are precise, not exploratory)

### STANDARD DPS Additions
- **Context**: Include full content of all target files. For frontmatter changes, include the CC native fields reference for valid field names. For description changes, include the 1024-char budget constraint.
- **Task**: Describe the pattern to apply across files: "Add `INPUT_FROM: execution-code` and `OUTPUT_TO: execution-review` to the description field of each skill listed." Provide one completed example for the first file, then specify "Apply the same pattern to remaining files."
- **Constraints**: All files must be in `.claude/` scope. Maintain valid YAML in all frontmatter. Maintain valid JSON in settings.json. Description field ≤1024 characters.
- **maxTurns**: 20

### COMPLEX DPS Additions
- **Context**: Include all target files plus related files that provide context (e.g., when creating a new skill, include an existing skill in the same domain as a template). Include CLAUDE.md for reference counts that may need updating.
- **Task**: Describe structural intent: "Create new skill `.claude/skills/new-skill/SKILL.md` following the template of `existing-skill`. Then update `.claude/CLAUDE.md` skill count. Then update `.claude/settings.json` to add permission for the new skill."
- **Constraints**: Follow existing conventions exactly (frontmatter field order, markdown heading style, indentation). New files must have all required frontmatter fields: `name`, `description`, `user-invocable`, `disable-model-invocation`.
- **maxTurns**: 30

## Monitoring Heuristics for Infra Changes

| Signal | Indicator | Action |
|--------|-----------|--------|
| `files_changed` matches expected count, no YAML errors | Healthy | Continue pipeline |
| Non-native frontmatter field introduced | Schema violation | Flag for correction, L1 Nudge |
| `description` field > 1024 chars | Overflow — L1 truncated | Flag for trimming, L1 Nudge |
| settings.json edit breaks JSON syntax | Critical failure | L2 Respawn with JSON fix prompt |
| Skill/agent name changed without reference updates | Cross-reference break | Flag for cascade check via execution-impact |

## Configuration Format Notes

### Required Frontmatter Fields (new SKILL.md)
All new skill files must include exactly these fields (no others):
```yaml
name: skill-name
description: >-
  [WHEN/DOMAIN/METHODOLOGY content, ≤1024 chars]
user-invocable: true|false
disable-model-invocation: true|false
```

### Agent Profile Update Format
When modifying `.claude/agents/*.md` frontmatter:
- `name`: matches filename without `.md`
- `description`: ≤1024 chars, role summary
- `model`: `sonnet` (never `opus` for non-lead agents)
- `tools`: explicit array of tool names (no `allowed-tools` — BUG-006 not enforced at runtime)

### settings.json Key Paths
Common modification targets:
- `env.CLAUDE_CODE_TASK_LIST_ID` — shared task list ID
- `permissions.allow[]` — tool permission grants
- `hooks[]` — hook event registrations

### Hook Script Conventions
Files in `.claude/hooks/*.sh`:
- First line: `#!/bin/bash`
- Exit 0 = success (tool use proceeds), exit 1 = block (with message to stderr)
- Input: JSON on stdin (hook event data)
- Scope guards: check `session_id` env var to avoid firing in all contexts (BUG-007 workaround)
