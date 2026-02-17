# Skill System — Fields, Invocation & Routing

> Verified: 2026-02-17 via claude-code-guide + researcher agent, cross-referenced with code.claude.com

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
- Standard structure: `.claude/skills/{name}/SKILL.md`
- Discovery: `.claude/skills/*/SKILL.md` (one glob level). Monorepo: also discovers from subdirectory `.claude/skills/`
- Max name: 64 chars, lowercase + numbers + hyphens only

---

## 2. Frontmatter Fields (SKILL.md)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | Required (API) / No (CC: defaults to dir name) | directory name | Lowercase, numbers, hyphens. Max 64 chars. Cannot contain "anthropic" or "claude". No XML tags (`<` `>`). Gerund form recommended: `processing-pdfs`, `analyzing-spreadsheets` |
| description | string | Required (API: non-empty) / Recommended (CC: falls back to first paragraph) | none | L1 routing intelligence. Multi-line via YAML `\|`. No XML tags (`<` `>`). Write in third person ("Processes files", not "I can help you") |
| argument-hint | string | no | none | Shown in `/` autocomplete. E.g., `[topic]`, `[file] [format]` |
| user-invocable | boolean | no | true | If false, hidden from `/` menu. Claude can still auto-invoke |
| disable-model-invocation | boolean | no | false | If true, description NOT loaded into context |
| allowed-tools | list | no | all | Tools Claude can use without asking permission when skill is active. EXPERIMENTAL (agentskills.io spec) |
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

### Skill-Agent Bidirectional Relationship

Two inverse patterns for combining skills and agents:
1. **Skills in agent** (`skills` field in agent frontmatter): Agent controls system prompt, skill content loaded as reference. Agent is the primary context.
2. **context:fork in skill** (`context: fork` in skill frontmatter): Skill content becomes the task, agent provides execution environment. Skill is the primary context.

Key: Subagents do NOT inherit skills from parent — must be listed explicitly in agent's `skills` field.

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

## 3.5 Content Guidelines

- Keep SKILL.md body under **500 lines** (optimal performance, not hard limit)
- Body token budget: under **5,000 tokens** recommended
- References should be **one level deep** from SKILL.md (no nested references)
- For reference files >100 lines, include a table of contents at top
- Including "ultrathink" anywhere in skill content enables extended thinking
- Prompt caching: changing skills list in API `container` breaks prompt cache

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

> **Note**: This canonical structure is our custom convention for routing optimization, NOT an official CC requirement. Official guidance only says: "write a clear description that includes keywords users would naturally say."

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

- Total budget: `max(context_window × 2%, 16000)` chars. Override via env var `SLASH_COMMAND_TOOL_CHAR_BUDGET`
- Per-skill recommendation: ≤1024 chars (self-imposed for zero truncation)
- Each new auto-loaded skill: ~300-400 chars
- Skills with `disable-model-invocation: true` excluded

### Skill Troubleshooting (Official)

- Run `/context` to check for excluded skills warnings
- If skill not triggering: check description includes keywords users would naturally say
- If triggering too often: make the description more specific
- If excluded from budget: skill won't be available for auto-invocation (only via /slash-command)

### Permission Control & Discovery

- Permission deny/allow rules: `Skill(name)` exact match, `Skill(name *)` prefix match
- Nested directory discovery: Monorepo support — discovers skills from subdirectory `.claude/skills/`

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
- 0 skills use: context, agent, allowed-tools, model, hooks (all routing via Lead). Note: allowed-tools usage planned for future INFRA redesign
- 7 skills use: argument-hint
- Canonical L1 structure (Phase·Domain·Role, WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO, METHODOLOGY, OUTPUT_FORMAT) is custom convention — not CC native
- Official L1 guidance: "Write a clear description that helps Claude decide when to apply the skill"
- Portable skill format: agentskills.io open standard defines cross-platform skill interchange format

---

## 7. Skills API

- REST API: `/v1/skills` with CRUD + versioning (beta header: `skills-2025-10-02`)
- Container parameter: `container.skills` array (max **8** per API request)
- Upload limit: **8MB** max total
- Pre-built Anthropic skills: pptx, xlsx, docx, pdf (API/claude.ai only, NOT CC)
- Cross-surface isolation: Skills do NOT sync between CC, API, and claude.ai
- Skill priority hierarchy: Enterprise > Personal > Project; plugins namespaced as `plugin-name:skill-name`
