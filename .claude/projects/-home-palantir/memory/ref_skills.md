# Skill System — Fields, Invocation & Routing

> Verified: 2026-02-16 via claude-code-guide, cross-referenced with code.claude.com

---

## 1. Overview & File Structure

Skills are the primary mechanism for teaching Claude Code domain-specific workflows without permanently consuming context.

```
.claude/skills/
├── backend-dev/
│   ├── SKILL.md          ← YAML frontmatter + instructions
│   ├── patterns.md       ← Reference materials
│   └── template.ts       ← Code templates
└── security-audit/
    └── SKILL.md
```

Locations:
- `~/.claude/skills/` — Global (user scope, all projects)
- `.claude/skills/` — Project scope (shared via git)
- Flat structure ONLY: `.claude/skills/{name}/SKILL.md` (nested NOT supported)
- Discovery: `.claude/skills/*/SKILL.md` (one glob level)
- Max name: 64 chars, lowercase + numbers + hyphens only

---

## 2. Frontmatter Fields (SKILL.md)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | no | directory name | Lowercase, numbers, hyphens. Max 64 chars |
| description | string | recommended | none | L1 routing intelligence. Multi-line via YAML `\|`. If omitted, first paragraph of body used |
| argument-hint | string | no | none | Shown in `/` autocomplete. E.g., `[topic]`, `[file] [format]` |
| user-invocable | boolean | no | true | If false, hidden from `/` menu. Claude can still auto-invoke |
| disable-model-invocation | boolean | no | false | If true, description NOT loaded into context |
| allowed-tools | list | no | all | CSV list of tools allowed during skill execution |
| model | enum | no | inherit | Values: sonnet, opus, haiku, inherit |
| context | enum | no | none | Values: fork. Forks subagent with skill L2 as task |
| agent | string | no | general-purpose | Subagent type when context=fork |
| hooks | object | no | none | Skill-scoped hooks (cleaned up when skill finishes) |

### Flag Combinations

| disable-model-invocation | user-invocable | Result |
|--------------------------|----------------|--------|
| false (default) | true (default) | Claude + user can both invoke |
| true | true | User-only (L1 not loaded) |
| false | false | Claude-only (hidden from / menu) |
| true | false | Dead skill (nobody can invoke) |

### Non-Native Fields (Silently Ignored)

input_schema, confirm, working_dir, timeout, env, and any custom YAML keys — parsed but NOT consumed by CC runtime.

---

## 3. On-Demand Loading & context:fork

Claude sees skill descriptions at session start, but FULL SKILL.md content only loads when used. For manual-only skills, set `disable-model-invocation: true` to exclude descriptions from context.

### The context:fork Bridge

When set, skill runs as subagent (not in main context). The `agent` field specifies which type:
- **Explore**: Read-only codebase navigation
- **Plan**: Structured planning
- **general-purpose**: Full tool access
- Custom subagent from `.claude/agents/`

**Caveat (GitHub #17283)**: Skill tool auto-invoke may not reliably honor `context: fork` and `agent:` fields. Works reliably via /slash-command only. When auto-invoked, may run inline instead of spawning subagent.

### Skill Invocation Flow

1. Claude sees Skill tool with all eligible L1 descriptions (budget-constrained)
2. Semantic matching: user request mapped to skill description (transformer reasoning)
3. Claude calls Skill tool with name + arguments
4. L2 body loaded into context
5. Shell preprocessing (`` !`commands` ``) executed, output replaces placeholders
6. `$ARGUMENTS` substituted in L2 body
7. Skill executes (only ONE skill active at a time)
8. After completion: L2 body removed, L1 description remains

---

## 4. Arguments & Substitution

### $ARGUMENTS

- `$ARGUMENTS`: replaced with entire user input string (in-place)
- `$ARGUMENTS[0]`, `$ARGUMENTS[1]`: positional access (0-indexed, space-delimited)
- `$0`, `$1`, `$2`: shorthand for positional access
- Can appear multiple times in body (all replaced)
- If NOT found in body: `ARGUMENTS: <user_input>` appended at end
- If IS found: replaced in-place, nothing appended
- No arguments provided: replaced with empty string
- Works in skill body ONLY, NOT in frontmatter

### Shell Preprocessing (Dynamic Context Injection)

- Syntax: `` !`shell-command` `` (backtick with `!` prefix)
- Executes at skill load time, BEFORE $ARGUMENTS substitution
- Output replaces placeholder inline
- Commands run in project root directory
- Failed commands: error replaces placeholder (non-blocking)
- Claude never sees the backtick syntax — only the output

### Execution Order

1. Skill L2 body loaded
2. Shell preprocessing executed and replaced
3. `$ARGUMENTS` substitution performed
4. Skill execution begins

### Environment Variables Available

- `$CLAUDE_SESSION_ID` — current session ID
- `$CLAUDE_PROJECT_DIR` — project root path

### argument-hint Field

Shown in `/` autocomplete menu. Display only — does NOT affect parsing.

### Skill Invocation Methods

1. **User direct**: `/skill-name arg1 arg2` — `$ARGUMENTS` = `arg1 arg2`
2. **Claude auto-invoke**: Skill tool — requires `disable-model-invocation: false`
3. **Lead routing**: Structured context as arguments — use `$ARGUMENTS` for full block

---

## 5. Disambiguation & Budget

### Transformer Routing Mechanics

- Lead (Opus 4.6) uses pure transformer reasoning for skill selection (not keyword matching)
- All auto-loaded L1 descriptions visible every request
- First 50-100 chars receive higher attention weight (community observation)
- No skill priority/weight mechanism exists

### Disambiguation Patterns (Ranked)

| Pattern | Example | Why It Works |
|---------|---------|-------------|
| Unique verb in first 50 chars | "Inventories artifacts" vs "Analyzes patterns" | Different embeddings |
| Explicit object noun | "structural dependencies" vs "runtime behaviors" | Noun specificity |
| Contrastive WHEN conditions | "After codebase complete" vs "After execution logs" | Temporal differentiation |
| Phase tag | [P1·Design] vs [P3·Plan] | Tag + phase = immediate context |
| INPUT_FROM specificity | "from architecture decisions" vs "from task breakdown" | Data flow uniqueness |

### Canonical L1 Structure

```
[Phase·Domain·Role] Unique-verb unique-noun summary.

WHEN: Explicit precondition.
DOMAIN: domain (skill N of M).
INPUT_FROM: source.
OUTPUT_TO: target.

METHODOLOGY: (1) step, (2) step, (3) step, (4) step, (5) step.
OUTPUT_FORMAT: L1 format, L2 format.
```

### Budget Math

- Total budget: `max(context_window × 2%, 16000)` chars (our override: 56000)
- Per-skill recommendation: ≤1024 chars (self-imposed for zero truncation)
- Each new auto-loaded skill: ~300-400 chars
- Skills with `disable-model-invocation: true` excluded

### CC-Native Persistent Storage

| Mechanism | Location | Auto-Load | Persistence |
|-----------|----------|-----------|-------------|
| Agent memory | `.claude/agent-memory/{agent}/` | First 200 lines MEMORY.md | Cross-session |
| Project memory | `~/.claude/projects/{hash}/memory/` | First 200 lines | Cross-session |
| Rules | `.claude/rules/*.md` | Per-path match | Permanent |
| Skill support files | `.claude/skills/{name}/*.md` | On-demand (Read) | Permanent |

---

## 6. Our Usage Pattern

- Pipeline entry skills: `disable-model-invocation: true` + `user-invocable: true`
- Homeostasis skills: `disable-model-invocation: false` (Claude auto-invokes)
- 0 skills use: context, agent, allowed-tools, model, hooks (all routing via Lead)
- 7 skills use: argument-hint
