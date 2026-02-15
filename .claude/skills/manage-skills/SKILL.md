---
name: manage-skills
description: |
  [Homeostasis·Manager·Skills] Session-aware skill lifecycle manager. Detects codebase changes via git diff, maps changed files to domains, determines CREATE/UPDATE/DELETE actions across all 8 pipeline domains.

  WHEN: After implementing features with new patterns, after modifying skills, before PR, or periodic drift detection. AI can auto-invoke.
  DOMAIN: Homeostasis (cross-cutting, operates on .claude/skills/).

  DETECTION_RULES: .claude/agents/ -> design domain, .claude/skills/ -> self-management, docs/plans/ -> plan domain, 3+ uncovered files in same domain -> CREATE.
  METHODOLOGY: (1) Git diff to detect changes, (2) Map files to domains via detection rules, (3) Check skill coverage per domain, (4) Propose CREATE/UPDATE/DELETE actions, (5) Execute after approval, (6) Run verify-cc-feasibility on results.
  OUTPUT_FORMAT: L1 YAML action list (CREATE/UPDATE/DELETE per skill), L2 markdown change analysis with rationale.
user-invocable: true
disable-model-invocation: false
---

# Manage — Skills

## Execution Model
- **TRIVIAL**: Lead-direct. Quick scan for 1-2 domain changes.
- **STANDARD**: Spawn analyst. Full domain coverage analysis.
- **COMPLEX**: Spawn 2 analysts. One for change detection, one for coverage analysis.

## Methodology

### 1. Detect Changes
**Executor: Lead-direct** (requires Bash for git commands).

Run git diff to identify modified files:
- `git diff --name-only HEAD` for unstaged changes
- `git diff --name-only --cached` for staged changes
- Categorize each changed file by domain

Lead runs git diff and passes the output as context to analysts spawned in subsequent steps.

### 2. Map Changes to Domains
Apply detection rules:
- `.claude/agents/` changes → design domain skills
- `.claude/skills/` changes → self-management (this skill)
- `docs/plans/` changes → plan domain skills
- Source code changes → execution domain skills
- 3+ uncovered files in same domain → signal for CREATE new skill

### 3. Check Domain Coverage
For all domains (8 pipeline + homeostasis + cross-cutting = 35 skills):
- List existing skills in that domain
- Identify if the domain change is covered by an existing skill
- If not covered: propose CREATE action with suggested skill name and description

### 4. Propose Actions
Generate action list:
- **CREATE**: New skill needed (domain gap detected)
- **UPDATE**: Existing skill needs description/body changes (methodology evolved)
- **DELETE**: Skill no longer serves a purpose (domain removed or merged)
Include rationale for each action.

### 5. Execute and Verify
**Executor: spawn infra-implementer** for file modifications. Lead coordinates.

After user approval:
- For CREATE: generate SKILL.md with frontmatter + L2 body
- For UPDATE: edit existing SKILL.md
- For DELETE: remove skill directory
- Run verify-cc-feasibility on all changed skills

## Quality Gate
- All domains (8 pipeline + homeostasis + cross-cutting) have ≥1 skill
- All proposed actions have clear rationale
- No domain left uncovered after actions applied
- Changed skills pass CC feasibility check

## Output

### L1
```yaml
domain: homeostasis
skill: manage-skills
status: complete
actions:
  - skill: ""
    action: CREATE|UPDATE|DELETE
    domain: ""
    reason: ""
```

### L2
- Git diff analysis summary
- Domain coverage report
- Proposed action rationale per skill
